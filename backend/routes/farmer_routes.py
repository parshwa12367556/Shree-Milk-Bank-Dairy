"""
Smart Dairy ERP — Farmer Routes

GET    /api/farmers          — List farmers (paginated, filterable)
POST   /api/farmers          — Register new farmer
GET    /api/farmers/stats    — Farmer statistics
GET    /api/farmers/<code>   — Farmer detail + bank + stats
PATCH  /api/farmers/<code>   — Update farmer
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Farmer, BankDetail, Collection, Payment
from backend.auth import role_required, get_identity
from backend.utils import generate_farmer_code

farmer_bp = Blueprint('farmers', __name__)


@farmer_bp.route('/api/farmers', methods=['GET'])
@jwt_required()
def get_farmers():
    """List farmers with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    q = request.args.get('q', '').strip()
    branch_id = request.args.get('branchId', type=int)
    milk_type = request.args.get('milk_type', '').strip()
    status = request.args.get('status', '').strip()

    query = Farmer.query

    # Branch filter (respect user's branch)
    user = get_identity()
    user_branch_id = user.get('branchId')
    if user.get('role') not in ('SUPER_ADMIN', 'HEAD_OFFICE') and user_branch_id:
        query = query.filter_by(branch_id=user_branch_id)
    elif branch_id:
        query = query.filter_by(branch_id=branch_id)

    # Search
    if q:
        search = f'%{q}%'
        query = query.filter(
            db.or_(
                Farmer.farmer_code.ilike(search),
                Farmer.name.ilike(search),
                Farmer.mobile.ilike(search),
                Farmer.village.ilike(search),
            )
        )

    # Milk type filter
    if milk_type:
        query = query.filter_by(milk_type=milk_type.upper())

    # Status filter
    if status:
        query = query.filter_by(status=status.upper())

    # Order by most recent
    query = query.order_by(Farmer.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'farmers': [f.to_dict() for f in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page,
    })


@farmer_bp.route('/api/farmers/stats', methods=['GET'])
@jwt_required()
def get_farmer_stats():
    """Get farmer statistics."""
    total = Farmer.query.count()
    active = Farmer.query.filter_by(status='ACTIVE').count()
    cow = Farmer.query.filter_by(milk_type='COW', status='ACTIVE').count()
    buffalo = Farmer.query.filter_by(milk_type='BUFFALO', status='ACTIVE').count()
    mixed = Farmer.query.filter_by(milk_type='MIXED', status='ACTIVE').count()
    inactive = Farmer.query.filter_by(status='INACTIVE').count()
    blocked = Farmer.query.filter_by(status='BLOCKED').count()

    return jsonify({
        'total': total,
        'active': active,
        'cow': cow,
        'buffalo': buffalo,
        'mixed': mixed,
        'inactive': inactive,
        'blocked': blocked,
    })


@farmer_bp.route('/api/farmers', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE', 'BRANCH_MANAGER', 'OPERATOR')
def create_farmer():
    """Register a new farmer."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = data.get('name', '').strip()
    mobile = data.get('mobile', '').strip()
    milk_type = data.get('milkType', '').upper()

    if not name:
        return jsonify({'error': 'Farmer name is required'}), 400
    if not mobile:
        return jsonify({'error': 'Mobile number is required'}), 400
    if milk_type not in ('COW', 'BUFFALO', 'MIXED'):
        return jsonify({'error': 'Valid milk type is required (COW, BUFFALO, MIXED)'}), 400

    # Auto-generate farmer code
    last_farmer = Farmer.query.filter(
        Farmer.farmer_code.like(f'{milk_type[0]}%')
    ).order_by(Farmer.id.desc()).first()

    seq = 1
    if last_farmer:
        try:
            seq = int(last_farmer.farmer_code[1:]) + 1
        except (ValueError, IndexError):
            seq = 1

    farmer_code = generate_farmer_code(milk_type, seq)

    farmer = Farmer(
        farmer_code=farmer_code,
        name=name,
        father_name=data.get('fatherName', ''),
        mobile=mobile,
        alt_mobile=data.get('altMobile', ''),
        email=data.get('email', ''),
        aadhaar=data.get('aadhaar', ''),
        gender=data.get('gender', ''),
        address=data.get('address', ''),
        village=data.get('village', ''),
        taluka=data.get('taluka', ''),
        district=data.get('district', ''),
        state=data.get('state', ''),
        pincode=data.get('pincode', ''),
        milk_type=milk_type,
        cow_count=data.get('cowCount', 0),
        buffalo_count=data.get('buffaloCount', 0),
        breed=data.get('breed', ''),
        preferred_shift=data.get('preferredShift', ''),
        branch_id=data.get('branchId'),
        created_by=get_identity().get('uid'),
    )
    db.session.add(farmer)
    db.session.flush()  # Get farmer ID

    # Create bank detail if provided
    if data.get('accountNumber') or data.get('ifsc'):
        bank = BankDetail(
            farmer_id=farmer.id,
            account_holder=data.get('accountHolder', name),
            bank_name=data.get('bankName', ''),
            branch_name=data.get('bankBranch', ''),
            account_number=data.get('accountNumber', ''),
            ifsc=data.get('ifsc', ''),
            upi=data.get('upi', ''),
        )
        db.session.add(bank)

    db.session.commit()

    return jsonify({
        'farmer': farmer.to_dict(),
        'message': f'Farmer {name} registered successfully with code {farmer_code}'
    }), 201


@farmer_bp.route('/api/farmers/<code>', methods=['GET'])
@jwt_required()
def get_farmer(code):
    """Get detailed farmer information including bank detail and stats."""
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    # Get collection stats
    total_qty = db.session.query(db.func.sum(Collection.quantity))\
        .filter(Collection.farmer_id == farmer.id).scalar() or 0
    total_amount = db.session.query(db.func.sum(Collection.amount))\
        .filter(Collection.farmer_id == farmer.id).scalar() or 0
    collection_count = Collection.query.filter_by(farmer_id=farmer.id).count()

    # Get recent collections (passbook)
    recent_collections = Collection.query\
        .filter_by(farmer_id=farmer.id)\
        .order_by(Collection.created_at.desc())\
        .limit(20).all()

    return jsonify({
        'farmer': farmer.to_dict(),
        'stats': {
            'totalQuantity': total_qty,
            'totalAmount': total_amount,
            'collectionCount': collection_count,
        },
        'recentCollections': [c.to_dict() for c in recent_collections],
    })


@farmer_bp.route('/api/farmers/<code>', methods=['PATCH'])
@jwt_required()
def update_farmer(code):
    """Update farmer information."""
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Map JSON field names to model attributes
    field_map = {
        'name': 'name', 'fatherName': 'father_name', 'mobile': 'mobile',
        'email': 'email', 'village': 'village', 'taluka': 'taluka',
        'district': 'district', 'state': 'state', 'pincode': 'pincode',
        'address': 'address', 'remarks': 'remarks', 'status': 'status',
        'cowCount': 'cow_count', 'buffaloCount': 'buffalo_count',
        'breed': 'breed', 'preferredShift': 'preferred_shift',
    }

    for json_key, model_attr in field_map.items():
        if json_key in data:
            setattr(farmer, model_attr, data[json_key])

    db.session.commit()
    return jsonify({'farmer': farmer.to_dict(), 'message': 'Farmer updated successfully'})
