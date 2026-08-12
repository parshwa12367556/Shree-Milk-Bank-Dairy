"""
Smart Dairy ERP — Inventory Routes

GET    /api/inventory                  — List inventory items
GET    /api/inventory/movements        — Stock movement ledger (filterable)
POST   /api/inventory                  — Add item (Head Office)
PATCH  /api/inventory/<id>             — Edit item (Head Office)
DELETE /api/inventory/<id>             — Delete item (Head Office)
POST   /api/inventory/<id>/movement    — Stock IN / OUT / ALLOCATE
GET    /api/inventory/<id>/movements   — Movements for one item
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import InventoryItem, StockMovement, InventoryAllocation, Branch
from backend.auth import role_required, get_identity, get_branch_scope, scope_query
from backend.audit import log_audit
from backend.notify import notify

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/api/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '').strip()
    q = request.args.get('q', '').strip()

    # Branch isolation: Branch Managers only see items allocated to their branch
    query = scope_query(InventoryItem.query, InventoryItem).order_by(InventoryItem.name)
    if category:
        query = query.filter_by(category=category)
    if q:
        search = f'%{q}%'
        query = query.filter(
            db.or_(InventoryItem.name.ilike(search), InventoryItem.code.ilike(search))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Low stock summary (respects user's branch scope)
    items = scope_query(InventoryItem.query, InventoryItem).all()
    low_stock = [i for i in items if i.stock <= i.min_stock]

    return jsonify({
        'items': [i.to_dict() for i in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'summary': {
            'totalItems': len(items),
            'lowStockCount': len(low_stock),
        },
    })


@inventory_bp.route('/api/inventory/movements', methods=['GET'])
@jwt_required()
def get_movements():
    """Stock movement ledger (all items)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    movement_type = request.args.get('type', '').strip()
    item_id = request.args.get('itemId', type=int)
    branch_id = request.args.get('branchId', type=int)

    query = StockMovement.query.order_by(StockMovement.created_at.desc())
    # Branch isolation: Branch Managers are forced to their own branch
    # (any client-supplied branchId is ignored); global roles may filter.
    forced = get_branch_scope()
    if forced:
        query = query.filter_by(branch_id=forced)
    elif branch_id:
        query = query.filter_by(branch_id=branch_id)
    if movement_type:
        query = query.filter_by(movement_type=movement_type.upper())
    if item_id:
        query = query.filter_by(item_id=item_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'movements': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@inventory_bp.route('/api/inventory', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
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
    db.session.flush()
    log_audit('CREATE', 'InventoryItem', item.code, detail=f'Item {item.name} added to inventory')
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'message': 'Item created'}), 201


@inventory_bp.route('/api/inventory/<int:item_id>', methods=['PATCH'])
@jwt_required()
@role_required('ADMIN')
def update_inventory(item_id):
    """Edit item metadata (name, category, unit, min stock)."""
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'name' in data:
        item.name = data['name']
    if 'category' in data:
        item.category = data['category']
    if 'unit' in data:
        item.unit = data['unit']
    if 'minStock' in data:
        item.min_stock = float(data['minStock'])
    if 'maxStock' in data:
        item.max_stock = float(data['maxStock']) if data['maxStock'] else None

    log_audit('UPDATE', 'InventoryItem', item.code, detail=f'Item {item.name} updated')
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'message': 'Item updated successfully'})


@inventory_bp.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@jwt_required()
@role_required('ADMIN')
def delete_inventory(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    code = item.code
    db.session.delete(item)
    log_audit('DELETE', 'InventoryItem', code, detail=f'Item {code} deleted')
    db.session.commit()
    return jsonify({'message': f'Item {code} deleted successfully'})


@inventory_bp.route('/api/inventory/<int:item_id>/movement', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def add_movement(item_id):
    """Stock IN / OUT / ALLOCATE for an item."""
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    movement_type = (data.get('type') or '').upper()
    if movement_type not in ('IN', 'OUT', 'ALLOCATE'):
        return jsonify({'error': 'Movement type must be IN, OUT or ALLOCATE'}), 400

    quantity = data.get('quantity')
    if quantity is None or float(quantity) <= 0:
        return jsonify({'error': 'Valid quantity is required'}), 400
    quantity = float(quantity)

    if movement_type == 'OUT' and item.stock < quantity:
        return jsonify({'error': f'Insufficient stock. Available: {item.stock} {item.unit or ""}'}), 400

    user = get_identity()

    # Apply stock change
    if movement_type == 'IN':
        item.stock = (item.stock or 0) + quantity
    elif movement_type == 'OUT':
        item.stock -= quantity
    elif movement_type == 'ALLOCATE':
        # Allocate stock to a branch (stock quantity unchanged at central).
        branch_id = data.get('branchId')
        if not branch_id:
            return jsonify({'error': 'Branch is required for allocation'}), 400
        item.branch_id = branch_id

    movement = StockMovement(
        item_id=item.id,
        movement_type=movement_type,
        quantity=quantity,
        branch_id=data.get('branchId') if movement_type in ('ALLOCATE',) else None,
        reference=data.get('reference', ''),
        note=data.get('note', ''),
        created_by=user.get('uid'),
    )
    db.session.add(movement)
    db.session.flush()

    log_audit('ALLOCATE' if movement_type == 'ALLOCATE' else movement_type,
              'InventoryItem', item.code,
              detail=f'{movement_type} {quantity} {item.unit or ""} of {item.name}'
                     f"{f' → branch {movement.branch_id}' if movement.branch_id else ''}")
    db.session.commit()

    return jsonify({
        'item': item.to_dict(),
        'movement': movement.to_dict(),
        'message': f'Stock {movement_type.lower()} recorded. New stock: {item.stock}',
    }), 201


@inventory_bp.route('/api/inventory/<int:item_id>/movements', methods=['GET'])
@jwt_required()
def item_movements(item_id):
    """List movements for a single item."""
    item = InventoryItem.query.get_or_404(item_id)
    # Branch isolation: Branch Managers can only inspect items of their branch
    forced = get_branch_scope()
    if forced and item.branch_id != forced:
        return jsonify({'error': 'Access denied. Item is not allocated to your branch.'}), 403
    movements = StockMovement.query.filter_by(item_id=item.id) \
        .order_by(StockMovement.created_at.desc()).limit(50).all()
    return jsonify({
        'item': item.to_dict(),
        'movements': [m.to_dict() for m in movements],
    })


@inventory_bp.route('/api/inventory/<int:item_id>/allocations', methods=['GET'])
@jwt_required()
def get_allocations(item_id):
    """List per-branch allocations for an item."""
    item = InventoryItem.query.get_or_404(item_id)
    # Branch isolation: Branch Managers can only inspect items of their branch
    forced = get_branch_scope()
    if forced and item.branch_id != forced:
        return jsonify({'error': 'Access denied. Item is not allocated to your branch.'}), 403
    allocations = InventoryAllocation.query.filter_by(item_id=item.id).all()
    return jsonify({
        'item': item.to_dict(),
        'allocations': [a.to_dict() for a in allocations],
    })


@inventory_bp.route('/api/inventory/<int:item_id>/allocate', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def allocate_stock(item_id):
    """Allocate a quantity of an item to a branch (central inventory → branch).

    body: {'branchId': 1, 'quantity': 30}
    The item's reserved amount increases; the allocation is tracked per branch.
    """
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    branch_id = data.get('branchId')
    quantity = data.get('quantity')
    if not branch_id:
        return jsonify({'error': 'Branch is required'}), 400
    if quantity is None or float(quantity) <= 0:
        return jsonify({'error': 'Valid quantity is required'}), 400
    quantity = float(quantity)

    branch = Branch.query.get(branch_id)
    if not branch:
        return jsonify({'error': 'Branch not found'}), 404

    available = (item.stock or 0) - (item.reserved or 0)
    if quantity > available:
        return jsonify({'error': f'Only {available} {item.unit or ""} available for allocation.'}), 400

    allocation = InventoryAllocation.query.filter_by(item_id=item.id, branch_id=branch_id).first()
    if allocation:
        allocation.quantity += quantity
    else:
        allocation = InventoryAllocation(
            item_id=item.id, branch_id=branch_id, quantity=quantity,
            created_by=get_identity().get('uid'),
        )
        db.session.add(allocation)

    item.reserved = (item.reserved or 0) + quantity

    movement = StockMovement(
        item_id=item.id,
        movement_type='ALLOCATE',
        quantity=quantity,
        branch_id=branch_id,
        reference=f'ALLOC-{allocation.id or 0}',
        note=f'Allocated to {branch.code}',
        created_by=get_identity().get('uid'),
    )
    db.session.add(movement)
    db.session.flush()
    movement.reference = f'ALLOC-{allocation.id}'

    log_audit('ALLOCATE', 'InventoryItem', item.code,
              detail=f'Allocated {quantity} {item.unit or ""} of {item.name} to {branch.code}')
    notify('inventory', 'Stock Allocated',
           f'{quantity} {item.unit or ""} of {item.name} allocated to {branch.code}.',
           link='inventory')
    db.session.commit()

    return jsonify({
        'item': item.to_dict(),
        'allocation': allocation.to_dict(),
        'message': f'{quantity} {item.unit or ""} of {item.name} allocated to {branch.code}.',
    }), 201


@inventory_bp.route('/api/inventory/<int:item_id>/deallocate', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def deallocate_stock(item_id):
    """Return allocated quantity from a branch back to the central pool."""
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    branch_id = data.get('branchId')
    quantity = data.get('quantity')
    if not branch_id or quantity is None or float(quantity) <= 0:
        return jsonify({'error': 'Branch and valid quantity are required'}), 400
    quantity = float(quantity)

    allocation = InventoryAllocation.query.filter_by(item_id=item.id, branch_id=branch_id).first()
    if not allocation or allocation.quantity < quantity:
        return jsonify({'error': 'Allocation not found or insufficient allocated quantity.'}), 400

    allocation.quantity -= quantity
    item.reserved = max((item.reserved or 0) - quantity, 0)
    if allocation.quantity <= 0:
        db.session.delete(allocation)

    db.session.add(StockMovement(
        item_id=item.id,
        movement_type='ALLOCATE',
        quantity=-quantity,
        branch_id=branch_id,
        reference='DEALLOC',
        note='Returned to central pool',
        created_by=get_identity().get('uid'),
    ))
    log_audit('ALLOCATE', 'InventoryItem', item.code,
              detail=f'Deallocated {quantity} of {item.name} from branch #{branch_id}')
    db.session.commit()

    return jsonify({'item': item.to_dict(), 'message': 'Deallocated successfully.'})
