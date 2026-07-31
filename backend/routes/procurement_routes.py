"""
Smart Dairy ERP — Procurement Routes

Collection Centers, Routes, and Chilling Centers CRUD.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import CollectionCenter, CollectionRoute, ChillingCenter

procurement_bp = Blueprint('procurement', __name__)


# ── Collection Centers ──

@procurement_bp.route('/api/procurement/centers', methods=['GET'])
@jwt_required()
def get_centers():
    centers = CollectionCenter.query.order_by(CollectionCenter.name).all()
    return jsonify({'centers': [c.to_dict() for c in centers]})


@procurement_bp.route('/api/procurement/centers', methods=['POST'])
@jwt_required()
def create_center():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    center = CollectionCenter(
        code=data.get('code'),
        name=data.get('name'),
        center_type=data.get('centerType', 'MAIN'),
        branch_id=data.get('branchId'),
        manager_name=data.get('managerName'),
        phone=data.get('phone'),
        village=data.get('village'),
        district=data.get('district'),
        capacity=data.get('capacity'),
        status=data.get('status', 'ACTIVE'),
    )
    db.session.add(center)
    db.session.commit()
    return jsonify({'center': center.to_dict(), 'message': 'Center created'}), 201


# ── Collection Routes ──

@procurement_bp.route('/api/procurement/routes', methods=['GET'])
@jwt_required()
def get_routes():
    routes = CollectionRoute.query.order_by(CollectionRoute.name).all()
    return jsonify({'routes': [r.to_dict() for r in routes]})


@procurement_bp.route('/api/procurement/routes', methods=['POST'])
@jwt_required()
def create_route():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    route = CollectionRoute(
        code=data.get('code'),
        name=data.get('name'),
        branch_id=data.get('branchId'),
        center_id=data.get('centerId'),
        distance=data.get('distance'),
        driver_name=data.get('driverName'),
        vehicle_number=data.get('vehicleNumber'),
        farmer_count=data.get('farmerCount', 0),
        status=data.get('status', 'ACTIVE'),
    )
    db.session.add(route)
    db.session.commit()
    return jsonify({'route': route.to_dict(), 'message': 'Route created'}), 201


# ── Chilling Centers ──

@procurement_bp.route('/api/procurement/chilling', methods=['GET'])
@jwt_required()
def get_chilling_centers():
    centers = ChillingCenter.query.order_by(ChillingCenter.name).all()
    return jsonify({'chilling_centers': [c.to_dict() for c in centers]})


@procurement_bp.route('/api/procurement/chilling', methods=['POST'])
@jwt_required()
def create_chilling_center():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    center = ChillingCenter(
        code=data.get('code'),
        name=data.get('name'),
        branch_id=data.get('branchId'),
        tank_count=data.get('tankCount', 0),
        total_capacity=data.get('totalCapacity'),
        current_stock=data.get('currentStock', 0),
        temperature=data.get('temperature'),
        has_generator=data.get('hasGenerator', False),
        phone=data.get('phone'),
        incharge_name=data.get('inchargeName'),
        status=data.get('status', 'ACTIVE'),
    )
    db.session.add(center)
    db.session.commit()
    return jsonify({'chillingCenter': center.to_dict(), 'message': 'Chilling center created'}), 201
