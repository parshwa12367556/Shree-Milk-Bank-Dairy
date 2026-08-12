"""
Smart Dairy ERP — Authentication Routes

POST /api/auth/login             — Authenticate user (Login ID + password), return JWT
POST /api/auth/logout            — Logout (client-side token clear)
GET  /api/auth/me                — Get current user session
PATCH /api/auth/profile          — Update user profile
POST /api/auth/change-password   — Change password
POST /api/auth/forgot-password   — Request password reset
POST /api/auth/reset-password    — Verify OTP and set a new password
"""
import hashlib
import json
import random
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_jwt_extended import create_access_token, jwt_required
from backend.app import db
from backend.models import User, Branch
from backend.auth import (check_password, hash_password, get_identity,
                          normalize_login_id, validate_password_policy)
from backend.audit import log_audit

OTP_TTL_SECONDS = 600  # 10 minutes

# Per-IP throttle (in-memory): bursts of login/reset requests from one source
# are rate-limited server-side in addition to the per-account lockout.
_IP_ATTEMPTS = defaultdict(deque)  # ip -> deque[epoch_seconds]


def _ip_throttled(ip):
    """Return True when the IP has exceeded the login rate limit."""
    window = current_app.config.get('LOGIN_RATE_LIMIT_WINDOW', 300)
    limit = current_app.config.get('LOGIN_RATE_LIMIT_MAX', 20)
    now = time.time()
    q = _IP_ATTEMPTS[ip]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False
# In-memory OTP store: username -> {'hash': sha256(otp), 'expires': epoch_seconds}
# Note: single-process only — lost on restart. Replace with a DB table if the
# app is ever run across multiple workers.
OTP_STORE = {}

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate a user by Login ID + password (spec §7/§8).

    The backend is the single source of truth for identity and role:
      * The role is NEVER accepted from the request — it is read from the
        users table after authentication.
      * branch_id / farmer_id are NEVER accepted from the request — they are
        derived from the authenticated user record.
      * The same generic error is returned whether the Login ID or the
        password is wrong (no account enumeration).
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Canonical field is login_id; `username` is accepted as a legacy alias
    # (older clients/tests) and email is kept as a login convenience for
    # farmers. None of these carry authorization weight — the user's role and
    # scope always come from the database row that matches.
    login_id = data.get('login_id') or data.get('username') or ''
    login_id = normalize_login_id(login_id)
    password = data.get('password', '')
    remember_me = bool(data.get('remember_me'))

    if not login_id or not password:
        return jsonify({'error': 'Login ID and password are required'}), 400

    # Per-IP throttle — too many auth requests from one address in a window.
    if _ip_throttled(request.remote_addr or 'unknown'):
        return jsonify({'error': 'Too many attempts. Please try again later.'}), 429

    # Resolve the account — Login ID is the canonical identifier; fall back to
    # the legacy username, then the registered email (case-insensitive) so
    # existing email-based farmer logins keep working.
    user = None
    if login_id:
        user = (User.query.filter(db.func.upper(User.login_id) == login_id).first()
                or User.query.filter(db.func.upper(User.username) == login_id).first())
    if not user:
        user = User.query.filter(User.email.ilike(login_id)).first()

    max_attempts = current_app.config.get('MAX_FAILED_ATTEMPTS', 5)
    lockout_minutes = current_app.config.get('ACCOUNT_LOCKOUT_MINUTES', 30)

    if not user:
        log_audit('LOGIN_FAILED', 'Session', login_id, username=login_id, force=True,
                  detail='Failed login: account not found')
        db.session.commit()
        return jsonify({'error': 'Invalid Login ID or Password.'}), 401

    # Brute-force lockout — reject while locked (safe message, no timing info).
    now = datetime.utcnow()
    if user.locked_until and user.locked_until > now:
        return jsonify({
            'error': 'Your account is temporarily locked. Please try again later or reset your password.'
        }), 429

    # Verify the password hash (never compare plain text, never reveal which
    # of Login ID / password was wrong).
    if not check_password(password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= max_attempts:
            user.locked_until = now + timedelta(minutes=lockout_minutes)
            log_audit('ACCOUNT_LOCKED', 'User', user.login_id, user_id=user.id,
                      username=user.username, role=user.role,
                      branch_code=user.branch.code if user.branch else None, force=True,
                      detail=f'Account locked after {max_attempts} failed attempts')
        else:
            log_audit('LOGIN_FAILED', 'Session', user.login_id, user_id=user.id,
                      username=user.username, role=user.role,
                      branch_code=user.branch.code if user.branch else None, force=True,
                      detail=f'Failed login attempt {user.failed_attempts}/{max_attempts}')
        db.session.commit()
        return jsonify({'error': 'Invalid Login ID or Password.'}), 401

    # Account status gates (is_active + account_status equivalents).
    if user.status != 'ACTIVE':
        return jsonify({'error': 'Your account is currently inactive. Please contact the administrator.'}), 403

    # ── Success ──
    user.last_login_at = datetime.utcnow()
    user.failed_attempts = 0
    user.locked_until = None
    log_audit('LOGIN_SUCCESS', 'Session', user.login_id, user_id=user.id, username=user.username,
              role=user.role, branch_code=user.branch.code if user.branch else None,
              detail=f'User logged in as {user.role}')
    db.session.commit()

    branch_name = user.branch.name if user.branch else None

    # Authenticated scope — the JWT carries ONLY what authorization needs.
    identity = {
        'uid': user.id,
        'loginId': user.login_id,
        'username': user.username,
        'name': user.name,
        'role': user.role,
        'branchId': user.branch_id,
        'branchName': branch_name,
        'branchCode': user.branch.code if user.branch else None,
        'mustChangePassword': bool(user.must_change_password),
    }
    if user.farmer_id:
        identity['farmerId'] = user.farmer_id
        identity['farmerCode'] = user.farmer.farmer_code if user.farmer else None

    # Remember Me → longer secure token lifetime (configurable), otherwise the
    # normal session lifetime. Never store the password client-side.
    if remember_me:
        expires_delta = timedelta(days=current_app.config.get('REMEMBER_ME_EXPIRES_DAYS', 30))
    else:
        expires_delta = None  # JWT_ACCESS_TOKEN_EXPIRES (24h)
    token = create_access_token(identity=json.dumps(identity), expires_delta=expires_delta)

    # httpOnly cookie so server-rendered pages can resolve the current user.
    cookie_max_age = (expires_delta.total_seconds() if expires_delta
                      else 24 * 60 * 60)
    response = jsonify({
        'token': token,
        'user': identity,
        'mustChangePassword': bool(user.must_change_password),
        'redirect_url': {'ADMIN': '/admin/dashboard',
                         'BRANCH_OPERATOR': '/branch/dashboard',
                         'FARMER': '/farmer/dashboard'}.get(user.role, '/dashboard'),
    })
    response.set_cookie(
        'access_token', token,
        max_age=int(cookie_max_age), httponly=True, samesite='Lax',
        secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
    )
    return response


@auth_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout — tokens are stateless; client should clear the token."""
    log_audit('LOGOUT', 'Session', get_identity().get('loginId') or get_identity().get('username'),
              detail='User logged out')
    db.session.commit()
    response = jsonify({'message': 'Logged out successfully'})
    response.delete_cookie('access_token')
    return response


@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    """Get current authenticated user's session info."""
    identity = get_identity()
    return jsonify({'user': identity})


@auth_bp.route('/api/auth/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    """Update current user's profile."""
    identity = get_identity()
    user = User.query.get(identity.get('uid'))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'name' in data:
        user.name = data['name'].strip()
    if 'email' in data:
        user.email = data['email'].strip()
    if 'phone' in data:
        user.phone = data['phone'].strip()

    db.session.commit()

    return jsonify({
        'message': 'Profile updated successfully',
        'user': {
            'uid': user.id,
            'loginId': user.login_id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
        }
    })


@auth_bp.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change current user's password."""
    identity = get_identity()
    user = User.query.get(identity.get('uid'))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if not current_password or not new_password:
        return jsonify({'error': 'Current and new passwords are required'}), 400

    if not check_password(current_password, user.password_hash):
        return jsonify({'error': 'Current password is incorrect'}), 401

    # Enforce the configured password policy (spec §21).
    policy_errors = validate_password_policy(new_password)
    if policy_errors:
        return jsonify({'error': ' '.join(policy_errors)}), 400

    user.password_hash = hash_password(new_password)
    user.password_changed_at = datetime.utcnow()
    # First-login enforcement: once the password is changed, the flag clears.
    user.must_change_password = False
    user.failed_attempts = 0
    user.locked_until = None
    log_audit('PASSWORD_CHANGED', 'User', user.login_id, user_id=user.id,
              username=user.username, detail='Password changed by user')
    db.session.commit()

    return jsonify({'message': 'Password changed successfully'})


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Request a password reset — generates a 6-digit OTP.

    Delivery is not wired yet (SMS/email providers are configuration
    placeholders), so in development the OTP is returned in the response
    (mirrors the previous dev behavior of returning the reset email).
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    identifier = (data.get('login_id') or data.get('email') or data.get('username') or '').strip()
    if not identifier:
        return jsonify({'error': 'Login ID or email is required'}), 400

    # Per-IP throttle — prevents OTP flooding.
    if _ip_throttled(request.remote_addr or 'unknown'):
        return jsonify({'error': 'Too many requests. Please try again later.'}), 429

    # Find user by Login ID, email or legacy username (case-insensitive).
    norm = normalize_login_id(identifier)
    user = (User.query.filter(db.func.upper(User.login_id) == norm).first()
            or User.query.filter(db.func.upper(User.username) == norm).first()
            or User.query.filter(User.email.ilike(identifier)).first())

    if not user:
        # Don't reveal whether the account exists for security
        return jsonify({'message': 'If the account is registered and has a valid email address, password reset instructions have been sent.'})

    otp = f'{random.randint(0, 999999):06d}'
    OTP_STORE[user.login_id] = {
        'hash': hashlib.sha256(otp.encode('utf-8')).hexdigest(),
        'expires': time.time() + OTP_TTL_SECONDS,
        'attempts': 0,
    }
    log_audit('PASSWORD_RESET_REQUESTED', 'PasswordReset', user.login_id,
              user_id=user.id, username=user.username, detail='Password reset OTP requested')
    db.session.commit()

    # Render the reset email and deliver via SMTP when configured.
    try:
        html_body = render_template(
            'emails/password_reset.html',
            name=user.name or user.username,
            username=user.login_id,
            otp=otp,
            expiry_minutes=OTP_TTL_SECONDS // 60,
        )
        from backend.mailer import send_email, is_email_configured
        if user.email and is_email_configured():
            sent, reason = send_email(
                user.email, 'Password Reset OTP - Shree Milk Bank', html_body)
            current_app.logger.info(
                'Password reset email for %s: %s',
                user.login_id, 'sent' if sent else f'skipped ({reason})')
        else:
            current_app.logger.info(
                'Password reset email prepared for %s (%d chars) — SMTP not configured, delivery skipped',
                user.login_id, len(html_body))
    except Exception as exc:  # never break the OTP flow if the template fails
        current_app.logger.warning('Could not render password reset email: %s', exc)

    # DEV: return the OTP in the response until real SMS/email delivery is
    # configured. NEVER returned in production (DEV_LOGIN_ENABLED off).
    is_dev = current_app.config.get('DEV_LOGIN_ENABLED', False)
    response = {'message': 'If the account is registered and has a valid email address, password reset instructions have been sent.'}
    if is_dev:
        response['dev_otp'] = otp
    return jsonify(response)


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Verify the reset OTP and set a new password."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    identifier = (data.get('login_id') or data.get('username') or '').strip()
    otp = str(data.get('otp') or '').strip()
    new_password = data.get('new_password') or ''

    if not identifier or not otp or not new_password:
        return jsonify({'error': 'Login ID, OTP and new password are required'}), 400

    # Resolve the identifier (Login ID, username OR email) to the canonical account
    norm = normalize_login_id(identifier)
    user = (User.query.filter(db.func.upper(User.login_id) == norm).first()
            or User.query.filter(db.func.upper(User.username) == norm).first()
            or User.query.filter(User.email.ilike(identifier)).first())
    if not user:
        return jsonify({'error': 'Account not found.'}), 404

    # OTP is single-use — but a wrong guess does NOT consume it; it only
    # burns an attempt so a single mistake can't DoS the reset flow.
    entry = OTP_STORE.get(user.login_id)
    if not entry or entry['expires'] < time.time():
        OTP_STORE.pop(user.login_id, None)
        return jsonify({'error': 'Invalid or expired OTP. Request a new one.'}), 400
    if hashlib.sha256(otp.encode('utf-8')).hexdigest() != entry['hash']:
        entry['attempts'] = entry.get('attempts', 0) + 1
        if entry['attempts'] >= 5:
            OTP_STORE.pop(user.login_id, None)  # exhausted after repeated failures
        return jsonify({'error': 'Invalid OTP.'}), 400
    OTP_STORE.pop(user.login_id, None)  # consumed on success

    # Enforce the configured password policy (spec §21).
    policy_errors = validate_password_policy(new_password)
    if policy_errors:
        return jsonify({'error': ' '.join(policy_errors)}), 400

    user.password_hash = hash_password(new_password)
    user.password_changed_at = datetime.utcnow()
    user.must_change_password = False
    user.failed_attempts = 0
    user.locked_until = None
    log_audit('PASSWORD_RESET_SUCCESS', 'User', user.login_id, user_id=user.id,
              username=user.username, detail='Password reset via OTP')
    db.session.commit()
    return jsonify({'message': 'Password reset successfully. Please login with your new password.'})
