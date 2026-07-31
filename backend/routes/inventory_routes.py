"""
Smart Dairy ERP — Inventory Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import InventoryItem

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/api/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = InventoryItem.query.order_by(InventoryItem.name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [i.to_dict() for i in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@inventory_bp.route('/api/inventory', methods=['POST'])
@jwt_required()
def create_inventory():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    item = InventoryItem(
        code=data.get('code'),
        name=data.get('name'),
        category=data.get('category'),
        stock=data.get('stock', 0),
        unit=data.get('unit'),
        min_stock=data.get('minStock', 0),
        branch_id=data.get('branchId'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'message': 'Item created'}), 201
