"""
Smart Dairy ERP — Milk Rejection Routes

GET  /api/rejections     — List milk rejections
POST /api/rejections     — Record a milk rejection
"""
from datetime import date, datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import MilkRejection, Collection, Farmer
from backend.auth import get_identity, get_branch_scope, scope_query
from backend.audit import log_audit
from backend.notify import notify

rejection_bp = Blueprint('rejections', __name__)


@rejection_bp.route('/api/rejections', methods=['GET'])
@jwt_required()
def get_rejections():
    """List milk rejections."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_str = request.args.get('date', '')
    reason = request.args.get('reason', '')
    farmer_id = request.args.get('farmerId', type=int)

    # Branch isolation: Branch Managers only see rejections of their branch
    query = scope_query(MilkRejection.query, MilkRejection).order_by(MilkRejection.created_at.desc())

    if date_str:
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter_by(date=query_date)
        except (ValueError, TypeError):
            pass

    if reason:
        query = query.filter_by(reason=reason.upper())
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'rejections': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@rejection_bp.route('/api/rejections', methods=['POST'])
@jwt_required()
def create_rejection():
    """Record a milk rejection."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    farmer_id = data.get('farmerId')
    quantity = data.get('quantity')
    reason = data.get('reason', '').upper()

    if not farmer_id:
        return jsonify({'error': 'Farmer ID is required'}), 400
    if not quantity or quantity <= 0:
        return jsonify({'error': 'Valid quantity is required'}), 400
    if reason not in ('HIGH_WATER', 'LOW_FAT', 'SOUR_MILK', 'HIGH_TEMP', 'ADULTERATION', 'OTHER'):
        return jsonify({'error': 'Invalid rejection reason'}), 400

    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    # Branch isolation: Branch Managers can only reject their own branch's farmers
    forced = get_branch_scope()
    if forced and farmer.branch_id != forced:
        return jsonify({'error': 'Access denied. Farmer belongs to another branch.'}), 403

    rejection = MilkRejection(
        collection_id=data.get('collectionId'),
        farmer_id=farmer_id,
        branch_id=forced or data.get('branchId'),
        rejected_by=get_identity().get('uid'),
        date=date.today(),
        shift=data.get('shift', ''),
        quantity=quantity,
        reason=reason,
        other_reason=data.get('otherReason', ''),
        fat=data.get('fat'),
        snf=data.get('snf'),
        clr=data.get('clr'),
        temperature=data.get('temperature'),
        water_content=data.get('waterContent'),
        remark=data.get('remark', ''),
    )
    db.session.add(rejection)
    db.session.flush()
    log_audit('REJECT', 'MilkRejection', rejection.id,
              detail=f'Rejected {quantity}L ({reason}) for farmer #{farmer_id}')
    notify('quality', 'Milk Rejected',
           f'{quantity}L milk rejected ({reason}) for farmer #{farmer_id}.',
           link='rejections')
    db.session.commit()

    # If linked to a collection, update its status
    if data.get('collectionId'):
        collection = Collection.query.get(data['collectionId'])
        if collection:
            collection.status = 'REJECTED'
            log_audit('UPDATE', 'Collection', collection.receipt_no, detail='Collection marked REJECTED')
            db.session.commit()

    return jsonify({
        'rejection': rejection.to_dict(),
        'message': f'Rejection recorded: {quantity}L - {reason}',
    }), 201
