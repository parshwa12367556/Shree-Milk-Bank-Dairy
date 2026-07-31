"""
Smart Dairy ERP — Branch Routes

GET    /api/branches              — List active branches (public for login)
POST   /api/branches              — Create branch (SUPER_ADMIN, HEAD_OFFICE)
PATCH  /api/branches/<id>         — Update branch
DELETE /api/branches/<id>         — Delete branch
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Branch
from backend.auth import role_required

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

    if Branch.query.filter_by(code=code).first():
        return jsonify({'error': 'Branch code already exists'}), 409

    branch = Branch(
        code=code,
        name=name,
        manager_name=data.get('managerName', ''),
        phone=data.get('phone', ''),
        address=data.get('address', ''),
        village=data.get('village', ''),
        district=data.get('district', ''),
        state=data.get('state', ''),
        status=data.get('status', 'ACTIVE'),
    )
    db.session.add(branch)
    db.session.commit()
    return jsonify({'branch': branch.to_dict(), 'message': 'Branch created successfully'}), 201


@branch_bp.route('/api/branches/<int:branch_id>', methods=['PATCH'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def update_branch(branch_id):
    """Update an existing branch."""
    branch = Branch.query.get_or_404(branch_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

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

    db.session.commit()
    return jsonify({'branch': branch.to_dict(), 'message': 'Branch updated successfully'})


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
    db.session.commit()
    return jsonify({'message': f'Branch {branch.name} deleted successfully'})
