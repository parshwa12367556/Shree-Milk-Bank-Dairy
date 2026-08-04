"""
Smart Dairy ERP — Procurement Routes

Collection Centers / Routes / Chilling Centers
Suppliers CRUD
Purchase Orders (DRAFT → PENDING → APPROVED → RECEIVED → COMPLETED / REJECTED)
Vendor Payments

Head Office only (all write endpoints gated to SUPER_ADMIN / HEAD_OFFICE).
"""
from datetime import date, datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import (
    CollectionCenter, CollectionRoute, ChillingCenter,
    Supplier, PurchaseOrder, PurchaseOrderItem, VendorPayment,
    InventoryItem, StockMovement,
)
from backend.auth import role_required, get_identity
from backend.audit import log_audit
from backend.notify import notify

procurement_bp = Blueprint('procurement', __name__)


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


# ════════════════════════════════════════════════════════════
#  Collection Centers / Routes / Chilling Centers
# ════════════════════════════════════════════════════════════

@procurement_bp.route('/api/procurement/centers', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def get_centers():
    centers = CollectionCenter.query.order_by(CollectionCenter.name).all()
    return jsonify({'centers': [c.to_dict() for c in centers]})


@procurement_bp.route('/api/procurement/centers', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
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
    db.session.flush()
    log_audit('CREATE', 'CollectionCenter', center.code, detail=f'Center {center.name} created')
    db.session.commit()
    return jsonify({'center': center.to_dict(), 'message': 'Center created'}), 201


@procurement_bp.route('/api/procurement/routes', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def get_routes():
    routes = CollectionRoute.query.order_by(CollectionRoute.name).all()
    return jsonify({'routes': [r.to_dict() for r in routes]})


@procurement_bp.route('/api/procurement/routes', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
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
    db.session.flush()
    log_audit('CREATE', 'CollectionRoute', route.code, detail=f'Route {route.name} created')
    db.session.commit()
    return jsonify({'route': route.to_dict(), 'message': 'Route created'}), 201


@procurement_bp.route('/api/procurement/chilling', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def get_chilling_centers():
    centers = ChillingCenter.query.order_by(ChillingCenter.name).all()
    return jsonify({'chilling_centers': [c.to_dict() for c in centers]})


@procurement_bp.route('/api/procurement/chilling', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
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
    db.session.flush()
    log_audit('CREATE', 'ChillingCenter', center.code, detail=f'Chilling center {center.name} created')
    db.session.commit()
    return jsonify({'chillingCenter': center.to_dict(), 'message': 'Chilling center created'}), 201


# ════════════════════════════════════════════════════════════
#  Suppliers
# ════════════════════════════════════════════════════════════

@procurement_bp.route('/api/procurement/suppliers', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def get_suppliers():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return jsonify({'suppliers': [s.to_dict() for s in suppliers]})


@procurement_bp.route('/api/procurement/suppliers', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def create_supplier():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Supplier name is required'}), 400

    last = Supplier.query.order_by(Supplier.id.desc()).first()
    seq = (last.id + 1) if last else 1
    supplier = Supplier(
        code=data.get('code') or f'SUP{seq:04d}',
        name=name,
        contact_person=data.get('contactPerson', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        address=data.get('address', ''),
        category=data.get('category', 'OTHER'),
        gstin=data.get('gstin', ''),
        status=data.get('status', 'ACTIVE'),
    )
    db.session.add(supplier)
    db.session.flush()
    log_audit('CREATE', 'Supplier', supplier.code, detail=f'Supplier {supplier.name} added')
    db.session.commit()
    return jsonify({'supplier': supplier.to_dict(), 'message': 'Supplier created'}), 201


@procurement_bp.route('/api/procurement/suppliers/<int:supplier_id>', methods=['PATCH'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def update_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    for field in ['name', 'contact_person', 'phone', 'email', 'address', 'category', 'gstin', 'status']:
        if field in data:
            setattr(supplier, field, data[field])

    log_audit('UPDATE', 'Supplier', supplier.code, detail=f'Supplier {supplier.name} updated')
    db.session.commit()
    return jsonify({'supplier': supplier.to_dict(), 'message': 'Supplier updated successfully'})


@procurement_bp.route('/api/procurement/suppliers/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    code = supplier.code
    db.session.delete(supplier)
    log_audit('DELETE', 'Supplier', code, detail=f'Supplier {code} deleted')
    db.session.commit()
    return jsonify({'message': f'Supplier {code} deleted successfully'})


# ════════════════════════════════════════════════════════════
#  Purchase Orders
# ════════════════════════════════════════════════════════════

@procurement_bp.route('/api/procurement/purchase-orders', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def get_purchase_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '').strip()

    query = PurchaseOrder.query.order_by(PurchaseOrder.id.desc())
    if status:
        query = query.filter_by(status=status.upper())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'purchase_orders': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@procurement_bp.route('/api/procurement/purchase-orders', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def create_purchase_order():
    """Create a purchase order (with line items). Starts as DRAFT."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    supplier_id = data.get('supplierId')
    if not supplier_id:
        return jsonify({'error': 'Supplier is required'}), 400
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify({'error': 'Supplier not found'}), 404

    items = data.get('items') or []
    if not items:
        return jsonify({'error': 'At least one item is required'}), 400

    last = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
    seq = (last.id + 1) if last else 1
    po = PurchaseOrder(
        po_code=f'PO{seq:06d}',
        supplier_id=supplier_id,
        branch_id=data.get('branchId'),
        order_date=_parse_date(data.get('orderDate')) or date.today(),
        expected_date=_parse_date(data.get('expectedDate')),
        status='DRAFT',
        remarks=data.get('remarks', ''),
        created_by=get_identity().get('uid'),
    )
    db.session.add(po)
    db.session.flush()

    total = 0.0
    for it in items:
        qty = float(it.get('quantity') or 0)
        price = float(it.get('unitPrice') or 0)
        amount = round(qty * price, 2)
        total += amount
        db.session.add(PurchaseOrderItem(
            po_id=po.id,
            item_name=it.get('itemName', ''),
            quantity=qty,
            unit=it.get('unit', 'nos'),
            unit_price=price,
            amount=amount,
        ))
    po.total_amount = round(total, 2)

    log_audit('CREATE', 'PurchaseOrder', po.po_code,
              detail=f'PO {po.po_code} created for {supplier.name} (₹{po.total_amount})')
    db.session.commit()
    return jsonify({'purchase_order': po.to_dict(), 'message': f'Purchase order {po.po_code} created'}), 201


@procurement_bp.route('/api/procurement/purchase-orders/<int:po_id>', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def get_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    return jsonify({'purchase_order': po.to_dict()})


@procurement_bp.route('/api/procurement/purchase-orders/<int:po_id>', methods=['PATCH'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def update_purchase_order(po_id):
    """Advance a purchase order through its workflow.

    status transitions:
        DRAFT   → submit → PENDING
        PENDING → approve → APPROVED | reject → REJECTED
        APPROVED→ receive → RECEIVED (items are added to central inventory)
        RECEIVED→ complete → COMPLETED (once vendor payment clears)
    """
    po = PurchaseOrder.query.get_or_404(po_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Delivery tracking can be updated independently of PO status
    if 'deliveryStatus' in data:
        delivery = data['deliveryStatus'].upper()
        valid_delivery = ('PENDING', 'DISPATCHED', 'IN_TRANSIT', 'DELIVERED')
        if delivery not in valid_delivery:
            return jsonify({'error': f'Delivery status must be one of: {valid_delivery}'}), 400
        po.delivery_status = delivery
        log_audit('UPDATE', 'PurchaseOrder', po.po_code, detail=f'PO {po.po_code} delivery → {delivery}')

    new_status = (data.get('status') or '').upper()
    if not new_status:
        db.session.commit()
        return jsonify({'purchase_order': po.to_dict(), 'message': 'Purchase order updated'})

    valid = {'DRAFT', 'PENDING', 'APPROVED', 'RECEIVED', 'COMPLETED', 'REJECTED'}
    if new_status not in valid:
        return jsonify({'error': f'Status must be one of: {", ".join(sorted(valid))}'}), 400

    allowed = {
        'DRAFT': {'PENDING', 'REJECTED'},
        'PENDING': {'APPROVED', 'REJECTED'},
        'APPROVED': {'RECEIVED', 'REJECTED'},
        'RECEIVED': {'COMPLETED', 'APPROVED'},
        'COMPLETED': set(),
        'REJECTED': {'DRAFT'},
    }
    if new_status not in allowed.get(po.status, set()):
        return jsonify({'error': f'Cannot move PO from {po.status} to {new_status}'}), 400

    po.status = new_status

    if new_status == 'RECEIVED':
        # Generate GRN (Goods Receipt Note) number and add items to inventory
        if not po.grn_no:
            last_grn = 0
            for po_row in PurchaseOrder.query.filter(PurchaseOrder.grn_no.isnot(None)).all():
                try:
                    last_grn = max(last_grn, int(po_row.grn_no.replace('GRN', '')))
                except ValueError:
                    pass
            po.grn_no = f'GRN{last_grn + 1:06d}'
        for it in po.items:
            inv = InventoryItem.query.filter_by(name=it.item_name).first()
            if not inv:
                last_inv = InventoryItem.query.order_by(InventoryItem.id.desc()).first()
                inv_seq = (last_inv.id + 1) if last_inv else 1
                inv = InventoryItem(
                    code=f'INV-{inv_seq:04d}',
                    name=it.item_name,
                    category='Procurement',
                    stock=0,
                    unit=it.unit or 'nos',
                    min_stock=0,
                )
                db.session.add(inv)
                db.session.flush()
            inv.stock = (inv.stock or 0) + it.quantity
            db.session.add(StockMovement(
                item_id=inv.id,
                movement_type='IN',
                quantity=it.quantity,
                branch_id=po.branch_id,
                reference=po.po_code,
                note=f'Received via {po.po_code} ({po.grn_no})',
                created_by=get_identity().get('uid'),
            ))

    if new_status == 'COMPLETED' and po.paid_amount < po.total_amount:
        return jsonify({'error': f'PO has unpaid balance of ₹{po.total_amount - po.paid_amount}. Record vendor payment first.'}), 400

    log_audit('UPDATE', 'PurchaseOrder', po.po_code, detail=f'PO {po.po_code} → {new_status}')
    if new_status == 'RECEIVED':
        notify('system', 'Purchase Received',
               f'{po.po_code} received from {po.supplier.name if po.supplier else "supplier"} (GRN: {po.grn_no}). Stock updated.',
               link='procurement')
    db.session.commit()
    return jsonify({'purchase_order': po.to_dict(),
                    'message': f'Purchase order {po.po_code} is now {new_status}' +
                               (f' (GRN: {po.grn_no})' if new_status == 'RECEIVED' and po.grn_no else '')})


# ════════════════════════════════════════════════════════════
#  Vendor Payments
# ════════════════════════════════════════════════════════════

@procurement_bp.route('/api/procurement/vendor-payments', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def get_vendor_payments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    po_id = request.args.get('poId', type=int)

    query = VendorPayment.query.order_by(VendorPayment.id.desc())
    if po_id:
        query = query.filter_by(po_id=po_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'vendor_payments': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@procurement_bp.route('/api/procurement/vendor-payments', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def create_vendor_payment():
    """Record a payment to a supplier against a purchase order."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    po_id = data.get('poId')
    if not po_id:
        return jsonify({'error': 'Purchase order is required'}), 400
    po = PurchaseOrder.query.get(po_id)
    if not po:
        return jsonify({'error': 'Purchase order not found'}), 404

    amount = data.get('amount')
    if amount is None or float(amount) <= 0:
        return jsonify({'error': 'Valid amount is required'}), 400
    amount = float(amount)

    balance = (po.total_amount or 0) - (po.paid_amount or 0)
    if amount > balance:
        return jsonify({'error': f'Amount exceeds outstanding balance of ₹{balance}'}), 400

    last = VendorPayment.query.order_by(VendorPayment.id.desc()).first()
    seq = (last.id + 1) if last else 1

    payment = VendorPayment(
        payment_code=f'VP{seq:06d}',
        po_id=po.id,
        amount=amount,
        payment_date=_parse_date(data.get('paymentDate')) or date.today(),
        method=data.get('method', 'BANK_TRANSFER'),
        reference=data.get('reference', ''),
        status='COMPLETED',
        created_by=get_identity().get('uid'),
    )
    db.session.add(payment)
    po.paid_amount = round((po.paid_amount or 0) + amount, 2)
    if po.paid_amount >= po.total_amount and po.status in ('APPROVED', 'RECEIVED'):
        po.status = 'COMPLETED'

    log_audit('CREATE', 'VendorPayment', payment.payment_code,
              detail=f'Paid ₹{amount} to supplier against {po.po_code}')
    db.session.commit()
    return jsonify({'vendor_payment': payment.to_dict(), 'message': 'Vendor payment recorded'}), 201
