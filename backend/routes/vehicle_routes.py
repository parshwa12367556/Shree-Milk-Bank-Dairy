"""
Smart Dairy ERP — Vehicle Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Vehicle

vehicle_bp = Blueprint('vehicles', __name__)


@vehicle_bp.route('/api/vehicles', methods=['GET'])
@jwt_required()
def get_vehicles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    branch_id = request.args.get('branchId', type=int)

    query = Vehicle.query.order_by(Vehicle.vehicle_number)
    if branch_id:
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
    )
    db.session.add(vehicle)
    db.session.commit()
    return jsonify({'vehicle': vehicle.to_dict(), 'message': 'Vehicle created'}), 201


@vehicle_bp.route('/api/vehicles/<int:vehicle_id>', methods=['PATCH'])
@jwt_required()
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

    db.session.commit()
    return jsonify({'vehicle': vehicle.to_dict(), 'message': 'Vehicle updated successfully'})


@vehicle_bp.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_vehicle(vehicle_id):
    """Delete a vehicle."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({'message': f'Vehicle {vehicle.vehicle_number} deleted successfully'})
