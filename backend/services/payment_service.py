"""
Smart Dairy ERP — Payment Service
=================================
Payment creation / finalization business rules. Only ADMIN ever reaches
these functions (the route decorators enforce the role); the service
enforces the *business* invariants on top:

  * A payment can only move PENDING → APPROVED → PAID (no downgrades,
    no re-marking an already-PAID payment).
  * Marking PAID settles the farmer's outstanding via a ledger debit.
  * Every transition is audit-logged and notified.
"""
from datetime import date as _date
from backend.app import db
from backend.models import Payment
from backend.audit import log_audit
from backend.services import ledger_service
from backend.utils import utcnow

VALID_STATUSES = ('PENDING', 'APPROVED', 'PAID')

# Allowed transitions: current status -> allowed next statuses
_ALLOWED_TRANSITIONS = {
    'PENDING': ('APPROVED', 'PAID'),
    'APPROVED': ('PAID',),
    'PAID': (),
}


def create_payment_sheet(farmer, branch_id, period_start, period_end,
                         collections, pay_code, created_by):
    """
    Build a PENDING payment for one farmer from unpaid collections.
    Caller is responsible for the surrounding transaction + audit log.
    """
    total_qty = sum((c.quantity or 0) for c in collections)
    gross = round(sum((c.amount or 0) for c in collections), 2)
    payment = Payment(
        pay_code=pay_code,
        farmer_id=farmer.id,
        branch_id=branch_id or farmer.branch_id,
        period_start=period_start,
        period_end=period_end,
        total_quantity=round(total_qty, 2),
        gross_amount=gross,
        deductions=0.0,
        total_amount=gross,  # net = gross - deductions (deductions admin-managed)
        collection_count=len(collections),
        status='PENDING',
        created_by=created_by,
    )
    db.session.add(payment)
    db.session.flush()
    for c in collections:
        c.payment_id = payment.id
    return payment


def has_overlapping_payment(farmer_id, period_start, period_end):
    """
    True when the farmer already has a payment whose period overlaps the
    given range (any status). Guards against double-processing the same
    collections for the same period.
    """
    return Payment.query.filter(
        Payment.farmer_id == farmer_id,
        Payment.period_start <= period_end,
        Payment.period_end >= period_start,
    ).first() is not None


def finalize_payment(payment, new_status, user_id, reference=None,
                     payment_method=None):
    """
    Transition a payment's status with business-rule validation.

    Returns (payment, error_message). On error the payment is left untouched.
    """
    new_status = (new_status or '').upper()
    if new_status not in VALID_STATUSES:
        return payment, 'Status must be APPROVED or PAID'

    if payment.status == 'PAID':
        return payment, 'Payment is already PAID and cannot be changed.'

    allowed = _ALLOWED_TRANSITIONS.get(payment.status, ())
    if new_status not in allowed:
        return payment, f'Invalid transition from {payment.status} to {new_status}.'

    old_status = payment.status
    payment.status = new_status

    if new_status == 'PAID':
        payment.paid_at = utcnow()
        payment.processed_by = user_id
        payment.paid_by = user_id
        if payment_method:
            payment.payment_method = payment_method
        if not payment.reference:
            payment.reference = reference or (
                'UTR' + utcnow().strftime('%Y%m%d%H%M%S') + str(payment.id or 0))
        else:
            payment.reference = reference or payment.reference
        # Settle the farmer's outstanding in the same transaction
        ledger_service.record_payment_debit(payment)
    else:
        payment.processed_by = user_id

    action = 'PAY' if new_status == 'PAID' else 'APPROVE'
    log_audit(action, 'Payment', payment.pay_code,
              detail=f'Payment {payment.pay_code} {old_status} → {new_status} '
                     f'(₹{payment.total_amount}) ref {payment.reference}')
    return payment, None
