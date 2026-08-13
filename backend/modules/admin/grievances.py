"""
Shree Milk Bank — Admin Grievance Management
=============================================
ADMIN-only endpoints for viewing, filtering, and responding to farmer
grievances. A response or status change immediately notifies the farmer
(in-app + email when configured) and is audit-logged.

GET   /api/admin/grievances           — List (filters: branchId, status, q)
GET   /api/admin/grievances/<id>      — Detail
PATCH /api/admin/grievances/<id>      — Respond / update status
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Grievance, Farmer, User
from backend.auth import role_required, get_identity
from backend.audit import log_audit
from backend.notify import notify
from backend.utils import utcnow

grievance_admin_bp = Blueprint('admin_grievances', __name__)

VALID_STATUSES = ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')


@grievance_admin_bp.route('/api/admin/grievances', methods=['GET'])
@jwt_required()
@role_required('ADMIN')
def list_grievances():
    """List all grievances with optional branch / status / search filters."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    branch_id = request.args.get('branchId', type=int)
    status = (request.args.get('status') or '').upper()
    q = (request.args.get('q') or '').strip()

    query = Grievance.query
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if status in VALID_STATUSES:
        query = query.filter_by(status=status)
    if q:
        search = f'%{q}%'
        query = query.join(Farmer, Grievance.farmer_id == Farmer.id).filter(
            db.or_(
                Farmer.farmer_code.ilike(search),
                Farmer.name.ilike(search),
                Grievance.subject.ilike(search),
                Grievance.grievance_code.ilike(search),
            )
        )

    pagination = query.order_by(Grievance.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    # Summary counts
    open_count = Grievance.query.filter_by(status='OPEN').count()
    in_progress = Grievance.query.filter_by(status='IN_PROGRESS').count()
    resolved = Grievance.query.filter_by(status='RESOLVED').count()

    return jsonify({
        'grievances': [g.to_dict() for g in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'summary': {
            'open': open_count,
            'inProgress': in_progress,
            'resolved': resolved,
        },
    })


@grievance_admin_bp.route('/api/admin/grievances/<int:grievance_id>', methods=['GET'])
@jwt_required()
@role_required('ADMIN')
def grievance_detail(grievance_id):
    """Single grievance detail (admin)."""
    grievance = Grievance.query.get(grievance_id)
    if not grievance:
        return jsonify({'error': 'Grievance not found'}), 404
    return jsonify({'grievance': grievance.to_dict()})


@grievance_admin_bp.route('/api/admin/grievances/<int:grievance_id>', methods=['PATCH'])
@jwt_required()
@role_required('ADMIN')
def respond_grievance(grievance_id):
    """Respond to a grievance and/or update its status (ADMIN only).

    body: {'response': '...', 'status': 'IN_PROGRESS'|'RESOLVED'|'CLOSED'}
    The farmer is notified immediately; email delivery is best-effort.
    """
    grievance = Grievance.query.get(grievance_id)
    if not grievance:
        return jsonify({'error': 'Grievance not found'}), 404

    data = request.get_json(silent=True) or {}
    response = (data.get('response') or '').strip()
    new_status = (data.get('status') or '').upper()

    if not response and not new_status:
        return jsonify({'error': 'Provide a response and/or a new status.'}), 400

    if new_status and new_status not in VALID_STATUSES:
        return jsonify({'error': 'Status must be OPEN, IN_PROGRESS, RESOLVED or CLOSED'}), 400

    user = get_identity()
    changes = []
    if response:
        grievance.response = response
        grievance.responded_by = user.get('uid')
        grievance.responded_at = utcnow()
        changes.append('responded')
    if new_status and new_status != grievance.status:
        changes.append(f'status {grievance.status}→{new_status}')
        grievance.status = new_status
        if not grievance.responded_at:
            grievance.responded_by = user.get('uid')
            grievance.responded_at = utcnow()

    log_audit('UPDATE', 'Grievance', grievance.grievance_code,
              detail=f'Grievance {grievance.grievance_code} updated by Admin: {", ".join(changes)}'
                     + (f' — {response[:120]}' if response else ''))

    # Notify the farmer (in-app on their login account + email if configured)
    farmer_acct = User.query.filter_by(
        farmer_id=grievance.farmer_id, role='FARMER').first()
    if farmer_acct:
        notify(
            'grievance', f'Grievance {grievance.grievance_code} Updated',
            f'Your grievance \"{grievance.subject}\" is now {grievance.status.replace("_", " ")}.'
            + (f' Response: {response}' if response else ''),
            link='/farmer/grievance',
            user_id=farmer_acct.id,
            farmer_id=grievance.farmer_id,
            related_type='Grievance',
            related_id=grievance.id,
        )
        try:
            from backend.mailer import send_email, is_email_configured
            if farmer_acct.email and is_email_configured():
                # Escape ALL farmer-controlled text — the subject/response are
                # user input and must never inject HTML into the email body.
                from html import escape as _h
                subject = f'Your grievance {grievance.grievance_code} is now {grievance.status.replace("_", " ")}'
                body = (f'<p>Dear {_h(grievance.farmer.name)},</p>'
                        f'<p>Your grievance "<b>{_h(grievance.subject)}</b>" '
                        f'({_h(grievance.grievance_code)}) is now '
                        f'<b>{grievance.status.replace("_", " ")}</b>.</p>'
                        + (f'<p>Response: {_h(response)}</p>' if response else '')
                        + '<p>— Shree Milk Bank</p>')
                sent, reason = send_email(farmer_acct.email, subject, body)
                if not sent:
                    current_app.logger.info('Grievance email skipped: %s', reason)
        except Exception as exc:  # email must never break the response flow
            current_app.logger.warning('Grievance email failed: %s', exc)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update grievance: {str(e)}'}), 500

    return jsonify({
        'grievance': grievance.to_dict(),
        'message': f'Grievance {grievance.grievance_code} updated.',
    })
