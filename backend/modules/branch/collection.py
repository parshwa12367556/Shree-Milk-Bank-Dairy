"""
Smart Dairy ERP — Collection Routes

GET  /api/collections  — List collections (filterable by date, shift)
POST /api/collections  — Record new collection
"""
from datetime import date, datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Collection, Farmer, RateMaster
from backend.auth import can_collect, get_identity, get_branch_scope
from backend.utils import generate_receipt_no
from backend.pricing import compute_price
from backend.audit import log_audit

collection_bp = Blueprint('collections', __name__)


@collection_bp.route('/api/collections', methods=['GET'])
@jwt_required()
def get_collections():
    """List collections with filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_str = request.args.get('date', date.today().isoformat())
    shift = request.args.get('shift', '')
    farmer_id = request.args.get('farmerId', type=int)
    branch_id = request.args.get('branchId', type=int)

    query = Collection.query

    # Filter by date
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        query = query.filter_by(date=query_date)
    except (ValueError, TypeError):
        pass

    if shift:
        query = query.filter_by(shift=shift.upper())
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)
    if branch_id:
        query = query.filter_by(branch_id=branch_id)

    # Branch isolation
    user = get_identity()
    user_branch_id = user.get('branchId')
    if user.get('role') not in ('SUPER_ADMIN', 'HEAD_OFFICE') and user_branch_id:
        query = query.filter_by(branch_id=user_branch_id)

    query = query.order_by(Collection.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'collections': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@collection_bp.route('/api/collections', methods=['POST'])
@jwt_required()
@can_collect()
def create_collection():
    """Record a new milk collection."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    farmer_id = data.get('farmerId')
    quantity = data.get('quantity')

    if not farmer_id:
        return jsonify({'error': 'Farmer ID is required'}), 400
    if not quantity or quantity <= 0:
        return jsonify({'error': 'Valid quantity is required'}), 400

    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    # Branch isolation: branch-scoped users can only collect from their own
    # branch's farmers, and the collection is always tagged with their branch.
    forced = get_branch_scope()
    if forced and farmer.branch_id != forced:
        return jsonify({'error': 'Access denied. Farmer belongs to another branch.'}), 403

    # Generate receipt number
    last_collection = Collection.query.order_by(Collection.id.desc()).first()
    seq = (last_collection.id + 1) if last_collection else 1
    receipt_no = generate_receipt_no(seq)

    # Get current active rate
    rate = RateMaster.query.filter_by(
        milk_type=farmer.milk_type, status='ACTIVE'
    ).first()

    fat = data.get('fat', farmer.milk_type == 'COW' and 4.0 or 6.0)
    snf = data.get('snf', farmer.milk_type == 'COW' and 8.5 or 9.0)

    # Compute price
    fat_rate = rate.fat_rate if rate else 5.0
    snf_rate = rate.snf_rate if rate else 2.5
    price = compute_price(fat, snf, quantity, fat_rate, snf_rate)

    shift = data.get('shift', 'MORNING').upper()
    if shift not in ('MORNING', 'EVENING'):
        shift = 'MORNING'

    user = get_identity()

    collection = Collection(
        receipt_no=receipt_no,
        farmer_id=farmer_id,
        branch_id=forced or data.get('branchId', farmer.branch_id),
        operator_id=user.get('uid'),
        rate_master_id=rate.id if rate else None,
        date=date.today(),
        shift=shift,
        milk_type=farmer.milk_type,
        quantity=quantity,
        fat=fat,
        snf=snf,
        clr=data.get('clr'),
        temperature=data.get('temperature'),
        water=data.get('water'),
        rate_per_liter=price['rate_per_liter'],
        amount=price['amount'],
        remarks=data.get('remarks', ''),
    )
    db.session.add(collection)
    db.session.flush()
    log_audit('CREATE', 'Collection', receipt_no,
              detail=f'Recorded {quantity}L {farmer.milk_type} milk for {farmer.farmer_code} (₹{price["amount"]})')
    db.session.commit()

    return jsonify({
        'collection': collection.to_dict(),
        'message': f'Collection recorded. Receipt #{receipt_no}',
        'receipt': receipt_no,
        'amount': price['amount'],
    }), 201
