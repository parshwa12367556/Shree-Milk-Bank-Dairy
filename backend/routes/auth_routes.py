"""
Smart Dairy ERP — Authentication Routes

POST /api/auth/login             — Authenticate user, return JWT
POST /api/auth/logout            — Logout (client-side token clear)
GET  /api/auth/me                — Get current user session
PATCH /api/auth/profile          — Update user profile
POST /api/auth/change-password   — Change password
POST /api/auth/forgot-password   — Request password reset
"""
import json
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required
from backend.app import db
from backend.models import User, Branch
from backend.auth import check_password, hash_password, get_identity
from backend.audit import log_audit

# TEMPORARY DEV: permanent credentials (admin / admin123) — see DEV_LOGIN_ENABLED
# in config.py. Remove this bypass before any production release.
PERMANENT_ADMIN_USERNAME = 'admin'
PERMANENT_ADMIN_PASSWORD = 'admin123'

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
            return jsonify({'error': 'Invalid username or password'}), 401

        if not check_password(password, user.password_hash):
            return jsonify({'error': 'Invalid username or password'}), 401

        if user.status != 'ACTIVE':
            return jsonify({'error': 'Account is inactive. Contact administrator.'}), 403

    from datetime import datetime
    user.last_login_at = datetime.utcnow()
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
    }

    token = create_access_token(identity=json.dumps(identity))

    return jsonify({
        'token': token,
        'user': identity,
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
    log_audit('UPDATE', 'User', user.username, detail='Password changed',
              user_id=user.id, username=user.username)
    db.session.commit()

    return jsonify({'message': 'Password changed successfully'})


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Request a password reset (email-based)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    email_or_username = data.get('email', '').strip()
    if not email_or_username:
        return jsonify({'error': 'Email or username is required'}), 400

    # Find user by email or username
    user = User.query.filter(
        db.or_(User.email == email_or_username, User.username == email_or_username)
    ).first()

    if not user:
        # Don't reveal whether the account exists for security
        return jsonify({'message': 'If the account exists, a reset link has been sent.'})

    # In production: send email with reset token
    # For now: return the user's email in the response (dev mode)
    return jsonify({
        'message': 'If the account exists, a reset link has been sent.',
        'reset_email': user.email or 'No email on file',
    })
