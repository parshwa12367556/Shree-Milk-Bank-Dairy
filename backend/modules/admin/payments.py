"""
Smart Dairy ERP — Payment Routes

GET  /api/payments          — List payments (filterable)
POST /api/payments          — Generate payment sheet
PATCH /api/payments/<id>    — Approve/pay payment
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from backend.app import db
from backend.models import Payment, Collection, Farmer, User
from backend.auth import can_pay, get_identity, reject_farmer
from backend.utils import generate_pay_code, utcnow
from backend.audit import log_audit
from backend.notify import notify
from backend.services import payment_service, ledger_service

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
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')

    query = Payment.query

    if status:
        query = query.filter_by(status=status.upper())
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)
    if date_from:
        try:
            query = query.filter(Payment.period_end >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass
    if date_to:
        try:
            query = query.filter(Payment.period_start <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass

    user = get_identity()
    user_branch_id = user.get('branchId')
    if user.get('role') not in ('ADMIN',) and user_branch_id:
        query = query.filter_by(branch_id=user_branch_id)

    query = query.order_by(Payment.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Payment summary (respect user's branch scope)
    summary_query = Payment.query
    if user.get('role') not in ('ADMIN',) and user_branch_id:
        summary_query = summary_query.filter_by(branch_id=user_branch_id)

    now = utcnow()
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

    # Status breakdown for the dashboard KPI cards — real DB sums only.
    total_pending_amount = sum(p.total_amount for p in all_payments if p.status == 'PENDING')
    total_approved_amount = sum(p.total_amount for p in all_payments if p.status == 'APPROVED')
    total_paid_amount = sum(p.total_amount for p in all_payments if p.status == 'PAID')
    total_failed_amount = sum(p.total_amount for p in all_payments if p.status == 'FAILED')

    return jsonify({
        'payments': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'summary': {
            'totalPaid': round(total_paid, 2),
            'totalPending': round(total_pending, 2),
            'paymentRate': payment_rate,
            'totalPendingAmount': round(total_pending_amount, 2),
            'totalApprovedAmount': round(total_approved_amount, 2),
            'totalPaidAmount': round(total_paid_amount, 2),
            'totalFailedAmount': round(total_failed_amount, 2),
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
    skipped = []

    for farmer_id, farmer_collections in farmer_groups.items():
        # Double-payment guard: a farmer who already has a payment covering
        # this period must NOT get a second sheet for the same collections.
        if payment_service.has_overlapping_payment(farmer_id, start, end):
            farmer = Farmer.query.get(farmer_id)
            skipped.append(farmer.farmer_code if farmer else str(farmer_id))
            continue

        pay_code = generate_pay_code(seq)
        seq += 1

        payment = payment_service.create_payment_sheet(
            farmer=Farmer.query.get(farmer_id),
            branch_id=branch_id,
            period_start=start,
            period_end=end,
            collections=farmer_collections,
            pay_code=pay_code,
            created_by=user.get('uid'),
        )
        created_payments.append(payment.to_dict())

    if not created_payments:
        msg = 'No new payments generated.'
        if skipped:
            msg += f' Farmers already covered for this period: {', '.join(skipped)}'
        return jsonify({'error': msg, 'skipped': skipped}), 409

    log_audit('CREATE', 'Payment', None,
              detail=f'Generated {len(created_payments)} payment(s) for period {start} to {end}'
                     + (f'; skipped already-covered: {', '.join(skipped)}' if skipped else ''))
    try:
        db.session.commit()
    except IntegrityError:
        # Raced past the app-level guard — the unique index on
        # (farmer_id, period_start, period_end) is the final backstop.
        db.session.rollback()
        return jsonify({
            'error': 'A payment already exists for one or more farmers in this period. '
                     'Duplicate payments are not allowed.',
            'skipped': skipped,
        }), 409

    message = f'Generated {len(created_payments)} payment(s)'
    if skipped:
        message += f'. Skipped already-covered farmer(s): {', '.join(skipped)}'
    return jsonify({
        'payments': created_payments,
        'count': len(created_payments),
        'skipped': skipped,
        'message': message,
    }), 201


@payment_bp.route('/api/payments/<int:payment_id>', methods=['PATCH'])
@jwt_required()
@can_pay()
def update_payment(payment_id):
    """Approve or mark payment as paid — ADMIN only, transition-guarded."""
    payment = Payment.query.get_or_404(payment_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    new_status = data.get('status', '').upper()
    reference = (data.get('reference') or '').strip() or None
    payment_method = (data.get('paymentMethod') or '').strip() or None

    actor = get_identity().get('uid')
    payment, err = payment_service.finalize_payment(
        payment, new_status, actor, reference=reference, payment_method=payment_method)
    if err:
        return jsonify({'error': err}), 400

    outbound = None
    if new_status == 'PAID':
        notify('payment', 'Payment Paid',
               f'₹{payment.total_amount} transferred to {payment.farmer.name if payment.farmer else "farmer"} ({payment.pay_code}). Ref: {payment.reference}',
               link='payments')
        # Farmer-specific in-app notification (same transaction)
        outbound = _notify_farmer_payment(payment, paid=True)
    elif new_status == 'APPROVED':
        notify('payment', 'Payment Approved',
               f'Payment {payment.pay_code} of ₹{payment.total_amount} approved.',
               link='payments')
        outbound = _notify_farmer_payment(payment, paid=False)

    db.session.commit()

    # Outbound channels (email/SMS) run strictly AFTER the commit — a
    # gateway failure can never roll back or block the payment transition.
    if outbound:
        _dispatch_farmer_payment_outbound(payment, outbound)

    return jsonify({
        'payment': payment.to_dict(),
        'message': f'Payment {payment.pay_code} {new_status}' + (f'. Bank ref: {payment.reference}' if new_status == 'PAID' else ''),
    })


def _notify_farmer_payment(payment, paid=False):
    """In-app notification to the farmer (committed with the payment)."""
    farmer = payment.farmer if payment else None
    if not farmer:
        return None
    acct = User.query.filter_by(farmer_id=farmer.id, role='FARMER').first()
    if not acct:
        return None
    title = 'Payment Received' if paid else 'Payment Approved'
    message = (
        f'₹{payment.total_amount:,.2f} has been credited for period '
        f'{payment.period_start} to {payment.period_end} ({payment.pay_code}).'
        if paid else
        f'Your payment {payment.pay_code} of ₹{payment.total_amount:,.2f} has been approved.'
    )
    notify('payment', title, message, link='/farmer/payment-history',
           user_id=acct.id, farmer_id=farmer.id,
           related_type='Payment', related_id=payment.id)
    return {'farmer': farmer, 'paid': paid}


def _dispatch_farmer_payment_outbound(payment, outbound):
    """Post-commit, best-effort email + SMS for a farmer payment event."""
    farmer = outbound.get('farmer')
    paid = outbound.get('paid')
    if not farmer:
        return
    # Email
    try:
        from backend.mailer import send_payment_email
        sent, reason = send_payment_email(payment)
        if not sent:
            current_app.logger.info('Payment email to %s skipped: %s', farmer.email, reason)
    except Exception as exc:  # email must never break the payment flow
        current_app.logger.warning('Payment email failed: %s', exc)
    # SMS
    try:
        from backend.sms import is_sms_configured, send_sms_async
        if is_sms_configured() and farmer.notification_sms:
            mobile = (farmer.mobile or '').strip()
            if mobile:
                verb = 'credited' if paid else 'approved'
                send_sms_async(
                    mobile,
                    f'Shree Milk Bank: payment {payment.pay_code} of '
                    f'₹{payment.total_amount:,.2f} has been {verb} '
                    f'({payment.period_start} to {payment.period_end}).',
                    notification_type='PAYMENT', related_type='Payment',
                    related_id=payment.id)
    except Exception as exc:  # SMS must never break the payment flow
        current_app.logger.warning('Payment SMS failed: %s', exc)
