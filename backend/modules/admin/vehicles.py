"""
Smart Dairy ERP — Vehicle Routes
"""
from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Vehicle, VehicleServiceRecord
from backend.audit import log_audit
from backend.auth import get_identity, get_branch_scope, role_required


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None

vehicle_bp = Blueprint('vehicles', __name__)


@vehicle_bp.route('/api/vehicles', methods=['GET'])
@jwt_required()
def get_vehicles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    branch_id = request.args.get('branchId', type=int)

    query = Vehicle.query.order_by(Vehicle.vehicle_number)
    # Branch isolation: Branch Managers are forced to their own branch
    # (any client-supplied branchId is ignored); global roles may filter.
    forced = get_branch_scope()
    if forced:
        query = query.filter_by(branch_id=forced)
    elif branch_id:
        query = query.filter_by(branch_id=branch_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'vehicles': [v.to_dict() for v in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@vehicle_bp.route('/api/vehicles', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def create_vehicle():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    vehicle = Vehicle(
        vehicle_number=data.get('vehicleNumber'),
        type=data.get('type'),
        driver_name=data.get('driverName'),
        capacity=data.get('capacity'),
        branch_id=data.get('branchId'),
        status=data.get('status', 'ACTIVE'),
        insurance_no=data.get('insuranceNo'),
        insurance_expiry=_parse_date(data.get('insuranceExpiry')),
        fitness_expiry=_parse_date(data.get('fitnessExpiry')),
        permit_expiry=_parse_date(data.get('permitExpiry')),
        mileage=data.get('mileage'),
        last_service_date=_parse_date(data.get('lastServiceDate')),
        next_service_date=_parse_date(data.get('nextServiceDate')),
        gps_status=data.get('gpsStatus', 'NOT_TRACKED'),
    )
    db.session.add(vehicle)
    db.session.flush()
    log_audit('CREATE', 'Vehicle', vehicle.vehicle_number, detail=f'Vehicle {vehicle.vehicle_number} added')
    db.session.commit()
    return jsonify({'vehicle': vehicle.to_dict(), 'message': 'Vehicle created'}), 201


@vehicle_bp.route('/api/vehicles/<int:vehicle_id>', methods=['PATCH'])
@jwt_required()
@role_required('ADMIN')
def update_vehicle(vehicle_id):
    """Update a vehicle's details."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Update only provided fields
    if 'vehicleNumber' in data:
        vehicle.vehicle_number = data['vehicleNumber']
    if 'type' in data:
        vehicle.type = data['type']
    if 'driverName' in data:
        vehicle.driver_name = data['driverName']
    if 'capacity' in data:
        vehicle.capacity = data['capacity']
    if 'branchId' in data:
        vehicle.branch_id = data['branchId']
    if 'status' in data:
        vehicle.status = data['status']
    if 'insuranceNo' in data:
        vehicle.insurance_no = data['insuranceNo']
    if 'insuranceExpiry' in data:
        vehicle.insurance_expiry = _parse_date(data['insuranceExpiry'])
    if 'fitnessExpiry' in data:
        vehicle.fitness_expiry = _parse_date(data['fitnessExpiry'])
    if 'permitExpiry' in data:
        vehicle.permit_expiry = _parse_date(data['permitExpiry'])
    if 'mileage' in data:
        vehicle.mileage = data['mileage']
    if 'lastServiceDate' in data:
        vehicle.last_service_date = _parse_date(data['lastServiceDate'])
    if 'nextServiceDate' in data:
        vehicle.next_service_date = _parse_date(data['nextServiceDate'])
    if 'gpsStatus' in data:
        vehicle.gps_status = data['gpsStatus']

    log_audit('UPDATE', 'Vehicle', vehicle.vehicle_number, detail=f'Vehicle {vehicle.vehicle_number} updated')
    db.session.commit()
    return jsonify({'vehicle': vehicle.to_dict(), 'message': 'Vehicle updated successfully'})


@vehicle_bp.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
@jwt_required()
@role_required('ADMIN')
def delete_vehicle(vehicle_id):
    """Delete a vehicle."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    number = vehicle.vehicle_number
    db.session.delete(vehicle)
    log_audit('DELETE', 'Vehicle', number, detail=f'Vehicle {number} deleted')
    db.session.commit()
    return jsonify({'message': f'Vehicle {number} deleted successfully'})


# ── Service history ──

@vehicle_bp.route('/api/vehicles/<int:vehicle_id>/service', methods=['GET'])
@jwt_required()
def get_service_history(vehicle_id):
    """List service records for a vehicle."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    # Branch isolation: Branch Managers can only view vehicles of their branch
    forced = get_branch_scope()
    if forced and vehicle.branch_id != forced:
        return jsonify({'error': 'Access denied. Vehicle belongs to another branch.'}), 403
    records = VehicleServiceRecord.query.filter_by(vehicle_id=vehicle.id) \
        .order_by(VehicleServiceRecord.service_date.desc()).all()
    return jsonify({
        'vehicle': vehicle.to_dict(),
        'records': [r.to_dict() for r in records],
    })


@vehicle_bp.route('/api/vehicles/<int:vehicle_id>/service', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def add_service_record(vehicle_id):
    """Add a service record for a vehicle."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    record = VehicleServiceRecord(
        vehicle_id=vehicle.id,
        service_date=_parse_date(data.get('serviceDate')) or date.today(),
        description=data.get('description', ''),
        cost=data.get('cost', 0),
        odometer=data.get('odometer'),
        vendor=data.get('vendor', ''),
        created_by=get_identity().get('uid'),
    )
    db.session.add(record)
    vehicle.last_service_date = record.service_date
    if data.get('nextServiceDate'):
        vehicle.next_service_date = _parse_date(data.get('nextServiceDate'))

    log_audit('CREATE', 'VehicleService', vehicle.vehicle_number,
              detail=f'Service record for {vehicle.vehicle_number}: {record.description}')
    db.session.commit()
    return jsonify({'record': record.to_dict(), 'message': 'Service record added'}), 201
