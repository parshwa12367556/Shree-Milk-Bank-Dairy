"""
Smart Dairy ERP — Branch Routes

GET    /api/branches                      — List active branches (public for login)
POST   /api/branches                      — Create branch + auto-create branch login (SUPER_ADMIN, HEAD_OFFICE)
PATCH  /api/branches/<id>                 — Update branch (syncs branch login)
POST   /api/branches/<id>/reset-password  — Reset branch login password to branch phone
DELETE /api/branches/<id>                 — Delete branch
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Branch, User
from backend.auth import role_required, hash_password
from backend.audit import log_audit

branch_bp = Blueprint('branches', __name__)


@branch_bp.route('/api/branches', methods=['GET'])
def get_branches():
    """List all active branches. Public (used in login dropdown)."""
    branches = Branch.query.filter_by(status='ACTIVE').order_by(Branch.name).all()
    return jsonify({
        'branches': [b.to_dict() for b in branches]
    })


@branch_bp.route('/api/branches', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def create_branch():
    """Create a new branch."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Branch name is required'}), 400

    code = data.get('code', '').strip()
    if not code:
        return jsonify({'error': 'Branch code is required'}), 400

    # Phone doubles as the branch login password, so it is mandatory
    phone = data.get('phone', '').strip()
    if not phone:
        return jsonify({'error': 'Branch phone number is required (it is used as the branch login password)'}), 400

    if Branch.query.filter_by(code=code).first():
        return jsonify({'error': 'Branch code already exists'}), 409

    if User.query.filter_by(username=code).first():
        return jsonify({'error': 'Branch code conflicts with an existing login username. Choose a different code.'}), 409

    branch = Branch(
        code=code,
        name=name,
        manager_name=data.get('managerName', ''),
        phone=phone,
        address=data.get('address', ''),
        village=data.get('village', ''),
        district=data.get('district', ''),
        state=data.get('state', ''),
        status=data.get('status', 'ACTIVE'),
    )
    db.session.add(branch)
    db.session.flush()

    # Auto-create the branch login: username = branch code, password = branch phone
    if not User.query.filter_by(username=code).first():
        branch_user = User(
            username=code,
            password_hash=hash_password(phone),
            name=data.get('managerName', '') or f'{name} Manager',
            role='BRANCH_MANAGER',
            branch_id=branch.id,
            phone=phone,
            status='ACTIVE',
        )
        db.session.add(branch_user)

    log_audit('CREATE', 'Branch', branch.code, detail=f'Branch {branch.name} created (login {code})')
    db.session.commit()
    return jsonify({
        'branch': branch.to_dict(),
        'message': f'Branch created successfully. Branch login: {code} / {phone}'
    }), 201


@branch_bp.route('/api/branches/<int:branch_id>', methods=['PATCH'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def update_branch(branch_id):
    """Update an existing branch (syncs the branch login if code/phone changed)."""
    branch = Branch.query.get_or_404(branch_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    old_code = branch.code
    old_phone = branch.phone

    if 'name' in data:
        branch.name = data['name'].strip()
    if 'code' in data:
        code = data['code'].strip()
        existing = Branch.query.filter_by(code=code).first()
        if existing and existing.id != branch_id:
            return jsonify({'error': 'Branch code already exists'}), 409
        branch.code = code
    if 'managerName' in data:
        branch.manager_name = data['managerName']
    if 'phone' in data:
        branch.phone = data['phone']
    if 'address' in data:
        branch.address = data['address']
    if 'village' in data:
        branch.village = data['village']
    if 'district' in data:
        branch.district = data['district']
    if 'state' in data:
        branch.state = data['state']
    if 'status' in data:
        branch.status = data['status']

    # Keep the branch login in sync: username = code, password = phone
    branch_user = User.query.filter_by(username=old_code).first()
    if branch_user:
        if branch.code != old_code:
            if User.query.filter(User.username == branch.code, User.id != branch_user.id).first():
                return jsonify({'error': 'Branch login username already in use'}), 409
            branch_user.username = branch.code
        if branch.phone and branch.phone != old_phone:
            branch_user.password_hash = hash_password(branch.phone)
            branch_user.phone = branch.phone
        if branch.manager_name:
            branch_user.name = branch.manager_name

    log_audit('UPDATE', 'Branch', branch.code, detail=f'Branch {branch.name} updated')
    db.session.commit()
    return jsonify({'branch': branch.to_dict(), 'message': 'Branch updated successfully'})


@branch_bp.route('/api/branches/<int:branch_id>/reset-password', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def reset_branch_password(branch_id):
    """Reset a branch login password to the branch's phone number."""
    branch = Branch.query.get_or_404(branch_id)
    if not branch.phone:
        return jsonify({'error': 'Branch has no phone number set. Set the phone first.'}), 400

    branch_user = User.query.filter_by(username=branch.code).first()
    if not branch_user:
        branch_user = User(
            username=branch.code,
            password_hash=hash_password(branch.phone),
            name=branch.manager_name or f'{branch.name} Manager',
            role='BRANCH_MANAGER',
            branch_id=branch.id,
            phone=branch.phone,
            status='ACTIVE',
        )
        db.session.add(branch_user)
    else:
        branch_user.password_hash = hash_password(branch.phone)
        branch_user.phone = branch.phone

    log_audit('UPDATE', 'Branch', branch.code, detail=f'Branch login password reset')
    db.session.commit()
    return jsonify({
        'message': f'Password reset successfully. Branch login: {branch.code} / {branch.phone}'
    })


@branch_bp.route('/api/branches/<int:branch_id>', methods=['DELETE'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def delete_branch(branch_id):
    """Delete a branch.

    Soft-deletes by setting status to INACTIVE so the branch disappears
    from all active listings while preserving linked data (farmers,
    collections, users, etc.) that references it.
    """
    branch = Branch.query.get_or_404(branch_id)
    branch.status = 'INACTIVE'
    # Free up the code (DB has a UNIQUE constraint on it) so a new
    # branch can reuse it later; the renamed row is never shown.
    branch.code = f"{branch.code}-DEL-{branch.id}"
    # Deactivate the auto-created branch login so it can no longer sign in
    branch_user = User.query.filter_by(branch_id=branch.id, role='BRANCH_MANAGER').first()
    if branch_user:
        branch_user.status = 'INACTIVE'
    log_audit('DELETE', 'Branch', branch.code, detail=f'Branch {branch.name} deleted')
    db.session.commit()
    return jsonify({'message': f'Branch {branch.name} deleted successfully'})
