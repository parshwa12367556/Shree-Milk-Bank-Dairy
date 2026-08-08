"""
Smart Dairy ERP — Payment Routes

GET  /api/payments          — List payments (filterable)
POST /api/payments          — Generate payment sheet
PATCH /api/payments/<id>    — Approve/pay payment
"""
from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Payment, Collection, Farmer
from backend.auth import can_pay, get_identity, reject_farmer
from backend.utils import generate_pay_code
from backend.audit import log_audit
from backend.notify import notify

payment_bp = Blueprint('payments', __name__)


@payment_bp.route('/api/payments', methods=['GET'])
@jwt_required()
def get_payments():
    """List payment records."""
    reject_farmer()  # farmers use /api/farmer/me/payments
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    branch_id = request.args.get('branchId', type=int)
    farmer_id = request.args.get('farmerId', type=int)

    query = Payment.query

    if status:
        query = query.filter_by(status=status.upper())
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)

    user = get_identity()
    user_branch_id = user.get('branchId')
    if user.get('role') not in ('SUPER_ADMIN', 'HEAD_OFFICE') and user_branch_id:
        query = query.filter_by(branch_id=user_branch_id)

    query = query.order_by(Payment.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Payment summary (respect user's branch scope)
    summary_query = Payment.query
    if user.get('role') not in ('SUPER_ADMIN', 'HEAD_OFFICE') and user_branch_id:
        summary_query = summary_query.filter_by(branch_id=user_branch_id)

    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    paid_this_month = summary_query.filter(
        Payment.status == 'PAID',
        db.or_(Payment.paid_at.is_(None), Payment.paid_at >= month_start),
    ).all()
    pending = summary_query.filter(
        Payment.status.in_(['PENDING', 'APPROVED']),
    ).all()
    all_payments = summary_query.all()

    total_paid = sum(p.total_amount for p in paid_this_month)
    total_pending = sum(p.total_amount for p in pending)
    total_amount_all = sum(p.total_amount for p in all_payments)
    total_paid_all = sum(p.total_amount for p in all_payments if p.status == 'PAID')
    payment_rate = round(total_paid_all / total_amount_all * 100, 1) if total_amount_all else 0.0

    return jsonify({
        'payments': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'summary': {
            'totalPaid': round(total_paid, 2),
            'totalPending': round(total_pending, 2),
            'paymentRate': payment_rate,
        },
    })


@payment_bp.route('/api/payments', methods=['POST'])
@jwt_required()
@can_pay()
def create_payment():
    """Generate payments from unpaid collections."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    branch_id = data.get('branchId')
    period_start = data.get('periodStart')
    period_end = data.get('periodEnd')
    farmer_ids = data.get('farmerIds', [])

    if not period_start or not period_end:
        return jsonify({'error': 'Period start and end dates are required'}), 400

    # Parse dates
    try:
        start = datetime.strptime(period_start, '%Y-%m-%d').date()
        end = datetime.strptime(period_end, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Get unpaid collections — only from VERIFIED/ACTIVE farmers can receive
    # payments (per the farmer verification workflow).
    query = Collection.query.join(Farmer, Collection.farmer_id == Farmer.id).filter(
        Collection.date.between(start, end),
        Collection.payment_id.is_(None),
        Collection.status == 'ACCEPTED',
        Farmer.status == 'ACTIVE',
    )

    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if farmer_ids:
        query = query.filter(Collection.farmer_id.in_(farmer_ids))

    # Group by farmer
    collections = query.all()
    farmer_groups = {}
    for c in collections:
        farmer_groups.setdefault(c.farmer_id, []).append(c)

    if not farmer_groups:
        return jsonify({'error': 'No unpaid collections found in the specified period'}), 404

    # Get last payment code
    last_pay = Payment.query.order_by(Payment.id.desc()).first()
    seq = (last_pay.id + 1) if last_pay else 1

    user = get_identity()
    created_payments = []

    for farmer_id, farmer_collections in farmer_groups.items():
        pay_code = generate_pay_code(seq)
        seq += 1

        total_qty = sum(c.quantity for c in farmer_collections)
        total_amt = sum(c.amount for c in farmer_collections)

        payment = Payment(
            pay_code=pay_code,
            farmer_id=farmer_id,
            branch_id=branch_id or farmer_collections[0].branch_id,
            period_start=start,
            period_end=end,
            total_quantity=total_qty,
            total_amount=total_amt,
            collection_count=len(farmer_collections),
            status='PENDING',
        )
        db.session.add(payment)
        db.session.flush()

        # Link collections to payment
        for c in farmer_collections:
            c.payment_id = payment.id

        created_payments.append(payment.to_dict())

    log_audit('CREATE', 'Payment', None,
              detail=f'Generated {len(created_payments)} payment(s) for period {start} to {end}')
    db.session.commit()

    return jsonify({
        'payments': created_payments,
        'count': len(created_payments),
        'message': f'Generated {len(created_payments)} payment(s)',
    }), 201


@payment_bp.route('/api/payments/<int:payment_id>', methods=['PATCH'])
@jwt_required()
@can_pay()
def update_payment(payment_id):
    """Approve or mark payment as paid."""
    payment = Payment.query.get_or_404(payment_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    new_status = data.get('status', '').upper()
    if new_status not in ('APPROVED', 'PAID'):
        return jsonify({'error': 'Status must be APPROVED or PAID'}), 400

    payment.status = new_status
    if new_status == 'PAID':
        payment.paid_at = datetime.utcnow()
        payment.paid_by = get_identity().get('uid')
        # Simulated bank transfer: auto-generate a UTR-style reference when
        # the payment is marked paid (real bank API integration can replace
        # this with the actual bank reference later).
        if not payment.reference:
            payment.reference = 'UTR' + datetime.utcnow().strftime('%Y%m%d%H%M%S') + str(payment.id or 0)

    payment.reference = data.get('reference', payment.reference)
    log_audit('PAY' if new_status == 'PAID' else 'APPROVE', 'Payment', payment.pay_code,
              detail=f'Payment {payment.pay_code} {new_status} (₹{payment.total_amount}) ref {payment.reference}')
    if new_status == 'PAID':
        notify('payment', 'Payment Paid',
               f'₹{payment.total_amount} transferred to {payment.farmer.name if payment.farmer else "farmer"} ({payment.pay_code}). Ref: {payment.reference}',
               link='payments')
    elif new_status == 'APPROVED':
        notify('payment', 'Payment Approved',
               f'Payment {payment.pay_code} of ₹{payment.total_amount} approved.',
               link='payments')
    db.session.commit()

    return jsonify({
        'payment': payment.to_dict(),
        'message': f'Payment {payment.pay_code} {new_status}' + (f'. Bank ref: {payment.reference}' if new_status == 'PAID' else ''),
    })
