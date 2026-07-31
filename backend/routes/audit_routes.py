"""
Smart Dairy ERP — Audit Log Routes

GET /api/audit — List audit logs (SUPER_ADMIN only)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import AuditLog
from backend.auth import role_required

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/api/audit', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN')
def get_audit_logs():
    """List audit logs with filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    action = request.args.get('action', '')
    entity = request.args.get('entity', '')
    user_id = request.args.get('userId', type=int)
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')

    query = AuditLog.query.order_by(AuditLog.created_at.desc())

    if action:
        query = query.filter_by(action=action.upper())
    if entity:
        query = query.filter_by(entity=entity)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if from_date:
        try:
            from datetime import datetime
            f = datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= f)
        except (ValueError, TypeError):
            pass
    if to_date:
        try:
            from datetime import datetime
            t = datetime.strptime(to_date, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at <= t)
        except (ValueError, TypeError):
            pass

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'logs': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })
