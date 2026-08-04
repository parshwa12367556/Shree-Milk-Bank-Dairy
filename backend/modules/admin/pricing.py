"""
Smart Dairy ERP — Pricing / Rate Engine Routes

GET  /api/pricing     — List rate versions
POST /api/pricing     — Create new rate (SUPER_ADMIN, HEAD_OFFICE)
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import RateMaster
from backend.auth import can_manage_rates, get_identity

pricing_bp = Blueprint('pricing', __name__)


@pricing_bp.route('/api/pricing', methods=['GET'])
@jwt_required()
def get_pricing():
    """List all rate versions, current and historical."""
    milk_type = request.args.get('milkType', '')
    status = request.args.get('status', '')

    query = RateMaster.query.order_by(RateMaster.created_at.desc())

    if milk_type:
        query = query.filter_by(milk_type=milk_type.upper())
    if status:
        query = query.filter_by(status=status.upper())

    rates = query.all()
    cow_rate = RateMaster.query.filter_by(milk_type='COW', status='ACTIVE').first()
    buff_rate = RateMaster.query.filter_by(milk_type='BUFFALO', status='ACTIVE').first()

    return jsonify({
        'rates': [r.to_dict() for r in rates],
        'current': {
            'cow': cow_rate.to_dict() if cow_rate else None,
            'buffalo': buff_rate.to_dict() if buff_rate else None,
        }
    })


@pricing_bp.route('/api/pricing', methods=['POST'])
@jwt_required()
@can_manage_rates()
def create_pricing():
    """Create a new rate version. Deactivates previous active rate."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    milk_type = data.get('milkType', '').upper()
    if milk_type not in ('COW', 'BUFFALO'):
        return jsonify({'error': 'Milk type must be COW or BUFFALO'}), 400

    fat_rate = data.get('fatRate')
    snf_rate = data.get('snfRate')
    effective_from = data.get('effectiveFrom')

    if not fat_rate or fat_rate <= 0:
        return jsonify({'error': 'Valid fat rate is required'}), 400
    if not snf_rate or snf_rate <= 0:
        return jsonify({'error': 'Valid SNF rate is required'}), 400

    # Parse effective date
    try:
        eff_date = datetime.strptime(effective_from, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Effective from date is required (YYYY-MM-DD)'}), 400

    # Deactivate current active rate for this milk type
    current = RateMaster.query.filter_by(milk_type=milk_type, status='ACTIVE').first()
    if current:
        current.status = 'INACTIVE'
        current.effective_to = eff_date

    # Get next version number
    max_version = db.session.query(db.func.max(RateMaster.version))\
        .filter_by(milk_type=milk_type).scalar() or 0

    rate = RateMaster(
        milk_type=milk_type,
        fat_rate=fat_rate,
        snf_rate=snf_rate,
        effective_from=eff_date,
        version=max_version + 1,
        status='ACTIVE',
        created_by=get_identity().get('uid'),
    )
    db.session.add(rate)
    db.session.commit()

    return jsonify({
        'rate': rate.to_dict(),
        'message': f'New {milk_type} rate v{rate.version} created successfully',
    }), 201
