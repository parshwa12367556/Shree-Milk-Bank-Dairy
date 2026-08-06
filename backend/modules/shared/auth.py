"""
Smart Dairy ERP — Authentication Routes

POST /api/auth/login             — Authenticate user, return JWT
POST /api/auth/logout            — Logout (client-side token clear)
GET  /api/auth/me                — Get current user session
PATCH /api/auth/profile          — Update user profile
POST /api/auth/change-password   — Change password
POST /api/auth/forgot-password   — Request password reset
"""
import hashlib
import json
import random
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_jwt_extended import create_access_token, jwt_required
from backend.app import db
from backend.models import User, Branch
from backend.auth import check_password, hash_password, get_identity
from backend.audit import log_audit

# TEMPORARY DEV: permanent credentials (admin / admin123) — see DEV_LOGIN_ENABLED
# in config.py. Remove this bypass before any production release.
PERMANENT_ADMIN_USERNAME = 'admin'
PERMANENT_ADMIN_PASSWORD = 'admin123'

# ── Login hardening ──
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 30
OTP_TTL_SECONDS = 600  # 10 minutes
# In-memory OTP store: username -> {'hash': sha256(otp), 'expires': epoch_seconds}
# Note: single-process only — lost on restart. Replace with a DB table if the
# app is ever run across multiple workers.
OTP_STORE = {}

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')
    branch_id = data.get('branch_id')
    role_hint = (data.get('role') or '').strip().upper()

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    # TEMPORARY DEV BYPASS (see DEV_LOGIN_ENABLED in config.py) — while enabled,
    # the permanent credentials (admin / admin123) always work, regardless of
    # the stored password hash or DB state. The admin user is created on the
    # fly if missing, and force-set to an ACTIVE SUPER_ADMIN.
    dev_login = current_app.config.get('DEV_LOGIN_ENABLED', False)
    if dev_login and username == PERMANENT_ADMIN_USERNAME and password == PERMANENT_ADMIN_PASSWORD:
        if not user:
            user = User(
                username=PERMANENT_ADMIN_USERNAME,
                password_hash=hash_password(PERMANENT_ADMIN_PASSWORD),
                name='Admin User',
                role='SUPER_ADMIN',
                email='admin@dairy.com',
                status='ACTIVE',
            )
            db.session.add(user)
        if user.role != 'SUPER_ADMIN':
            user.role = 'SUPER_ADMIN'
        if user.status != 'ACTIVE':
            user.status = 'ACTIVE'
        db.session.commit()
    else:
        if not user:
            log_audit('LOGIN_FAILED', 'Session', username, username=username, force=True,
                      detail='Failed login: account not found')
            db.session.commit()
            return jsonify({'error': 'Invalid username or password'}), 401

        # Role hint (from the login-screen role tabs) — reject a mismatch.
        if role_hint and user.role != role_hint:
            log_audit('LOGIN_FAILED', 'Session', username, user_id=user.id, username=username,
                      role=user.role, branch_code=user.branch.code if user.branch else None, force=True,
                      detail=f'Failed login: role mismatch (expected {role_hint})')
            db.session.commit()
            return jsonify({'error': 'Invalid username or password'}), 401

        # Brute-force lockout — reject while locked.
        now = datetime.utcnow()
        if user.locked_until and user.locked_until > now:
            return jsonify({
                'error': f'Too many failed attempts. Account is locked. Try again after {LOCKOUT_MINUTES} minutes.'
            }), 429

        if not check_password(password, user.password_hash):
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                log_audit('LOCK', 'User', user.username, user_id=user.id, username=user.username,
                          role=user.role, branch_code=user.branch.code if user.branch else None, force=True,
                          detail=f'Account locked after {MAX_FAILED_ATTEMPTS} failed attempts')
            else:
                log_audit('LOGIN_FAILED', 'Session', user.username, user_id=user.id, username=user.username,
                          role=user.role, branch_code=user.branch.code if user.branch else None, force=True,
                          detail=f'Failed login attempt {user.failed_attempts}/{MAX_FAILED_ATTEMPTS}')
            db.session.commit()
            return jsonify({'error': 'Invalid username or password'}), 401

        if user.status != 'ACTIVE':
            return jsonify({'error': 'Account is inactive. Contact administrator.'}), 403

    # Success — update last login and reset failed-attempt counters.
    user.last_login_at = datetime.utcnow()
    if user.failed_attempts:
        user.failed_attempts = 0
    user.locked_until = None
    log_audit('LOGIN', 'Session', user.username, user_id=user.id, username=user.username,
              role=user.role, branch_code=user.branch.code if user.branch else None,
              detail=f'User logged in as {user.role}')
    db.session.commit()

    # Branch display resolution:
    # - Branch-scoped users (operator/manager) always use their assigned branch.
    # - Global roles (super admin / head office / accountant) may pick a branch
    #   on the login screen; use it so the branch name is visible in the UI.
    #   (branchId stays as the user's assigned branch so data scoping is unchanged.)
    selected_branch = Branch.query.get(branch_id) if branch_id else None
    branch_name = user.branch.name if user.branch else (selected_branch.name if selected_branch else None)

    identity = {
        'uid': user.id,
        'username': user.username,
        'name': user.name,
        'role': user.role,
        'branchId': user.branch_id,
        'branchName': branch_name,
        'branchCode': user.branch.code if user.branch else None,
        'mustChangePassword': bool(user.must_change_password),
    }

    token = create_access_token(identity=json.dumps(identity))

    return jsonify({
        'token': token,
        'user': identity,
        'mustChangePassword': bool(user.must_change_password),
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout — tokens are stateless; client should clear the token."""
    log_audit('LOGOUT', 'Session', get_identity().get('username'),
              detail='User logged out')
    db.session.commit()
    return jsonify({'message': 'Logged out successfully'})


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

    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400

    user.password_hash = hash_password(new_password)
    # First-login enforcement: once the password is changed, the flag clears.
    user.must_change_password = False
    user.failed_attempts = 0
    user.locked_until = None
    log_audit('UPDATE', 'User', user.username, detail='Password changed',
              user_id=user.id, username=user.username)
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

    email_or_username = data.get('email', '').strip() or data.get('username', '').strip()
    if not email_or_username:
        return jsonify({'error': 'Email or username is required'}), 400

    # Find user by email or username
    user = User.query.filter(
        db.or_(User.email == email_or_username, User.username == email_or_username)
    ).first()

    if not user:
        # Don't reveal whether the account exists for security
        return jsonify({'message': 'If the account exists, an OTP has been sent.'})

    otp = f'{random.randint(0, 999999):06d}'
    OTP_STORE[user.username] = {
        'hash': hashlib.sha256(otp.encode('utf-8')).hexdigest(),
        'expires': time.time() + OTP_TTL_SECONDS,
        'attempts': 0,
    }
    log_audit('REQUEST', 'PasswordReset', user.username, user_id=user.id, username=user.username,
              detail='Password reset OTP requested')
    db.session.commit()

    # Render the reset email. Real delivery is not wired yet (SMTP/MSG91 are
    # config placeholders — see backend/notify.py), so in dev the OTP is
    # returned below and the rendered body is only logged. When a mailer is
    # added, send `html_body` to user.email here.
    try:
        html_body = render_template(
            'emails/password_reset.html',
            name=user.name or user.username,
            username=user.username,
            otp=otp,
            expiry_minutes=OTP_TTL_SECONDS // 60,
        )
        current_app.logger.info(
            'Password reset email prepared for %s (%d chars) — delivery not wired yet',
            user.username, len(html_body))
    except Exception as exc:  # never break the OTP flow if the template fails
        current_app.logger.warning('Could not render password reset email: %s', exc)

    # DEV: return the OTP in the response until real SMS/email delivery is
    # configured. NEVER returned in production (DEV_LOGIN_ENABLED off).
    is_dev = current_app.config.get('DEV_LOGIN_ENABLED', False)
    response = {'message': 'If the account exists, an OTP has been sent.'}
    if is_dev:
        response['dev_otp'] = otp
    return jsonify(response)


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Verify the reset OTP and set a new password."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    identifier = (data.get('username') or '').strip()
    otp = str(data.get('otp') or '').strip()
    new_password = data.get('new_password') or ''

    if not identifier or not otp or not new_password:
        return jsonify({'error': 'Username, OTP and new password are required'}), 400
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400

    # Resolve the identifier (username OR email) to the canonical username
    user = User.query.filter(
        db.or_(User.username == identifier, User.email == identifier)
    ).first()
    if not user:
        return jsonify({'error': 'Account not found.'}), 404

    # OTP is single-use — but a wrong guess does NOT consume it; it only
    # burns an attempt so a single mistake can't DoS the reset flow.
    entry = OTP_STORE.get(user.username)
    if not entry or entry['expires'] < time.time():
        OTP_STORE.pop(user.username, None)
        return jsonify({'error': 'Invalid or expired OTP. Request a new one.'}), 400
    if hashlib.sha256(otp.encode('utf-8')).hexdigest() != entry['hash']:
        entry['attempts'] = entry.get('attempts', 0) + 1
        if entry['attempts'] >= 5:
            OTP_STORE.pop(user.username, None)  # exhausted after repeated failures
        return jsonify({'error': 'Invalid OTP.'}), 400
    OTP_STORE.pop(user.username, None)  # consumed on success

    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    user.failed_attempts = 0
    user.locked_until = None
    log_audit('UPDATE', 'User', user.username, user_id=user.id, username=user.username,
              detail='Password reset via OTP')
    db.session.commit()
    return jsonify({'message': 'Password reset successfully. Please login with your new password.'})
