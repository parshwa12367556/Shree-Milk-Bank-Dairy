"""
Smart Dairy ERP — Farmer Ledger Service
=======================================
Maintains the `farmer_ledger_entries` table — the real source of truth for
the farmer passbook.

Every milk collection earning (credit) and every settled payment (debit)
writes a ledger row inside the SAME database transaction as the originating
record, so the passbook can never drift from collections/payments.

Entry types:
  MILK_EARNING  — credit, from a Collection (source_type='Collection')
  PAYMENT       — debit,  from a Payment marked PAID (source_type='Payment')
  ADJUSTMENT    — manual credit/debit correction
  DEDUCTION     — manual debit (charges/advances)

The running balance is recomputed after each write: credits increase the
farmer's outstanding, debits reduce it.
"""
from datetime import date as _date
from backend.app import db
from backend.models import FarmerLedgerEntry, Collection, Payment, Farmer


def _recompute_balances(farmer_id):
    """
    Recompute the running balance for every ledger row of a farmer,
    ordered by entry_date then id (stable, deterministic order).
    """
    rows = FarmerLedgerEntry.query.filter_by(farmer_id=farmer_id) \
        .order_by(FarmerLedgerEntry.entry_date.asc(), FarmerLedgerEntry.id.asc()).all()
    running = 0.0
    for row in rows:
        running += (row.credit_amount or 0) - (row.debit_amount or 0)
        if abs(row.running_balance - running) > 0.001:
            row.running_balance = round(running, 2)
    if rows:
        db.session.flush()


def create_entry(farmer_id, branch_id, entry_type, source_type, source_id,
                 entry_date=None, description='', credit=0.0, debit=0.0,
                 recompute=True):
    """
    Create a ledger entry. Idempotent per (farmer, source_type, source_id):
    re-calling with the same source returns the existing row instead of
    duplicating it (safe to call inside retryable transactions).
    """
    if source_type and source_id:
        existing = FarmerLedgerEntry.query.filter_by(
            farmer_id=farmer_id, source_type=source_type, source_id=source_id).first()
        if existing:
            return existing

    entry = FarmerLedgerEntry(
        farmer_id=farmer_id,
        branch_id=branch_id,
        entry_type=entry_type,
        source_type=source_type,
        source_id=source_id,
        entry_date=entry_date or _date.today(),
        description=(description or '')[:255],
        credit_amount=round(float(credit or 0), 2),
        debit_amount=round(float(debit or 0), 2),
        running_balance=0,
    )
    db.session.add(entry)
    db.session.flush()
    if recompute:
        _recompute_balances(farmer_id)
    return entry


# ── Business entry writers ───────────────────────────────────────────────

def record_milk_earning(collection):
    """
    Credit a farmer for an accepted milk collection.

    Called inside the collection creation/correction transaction. The amount
    comes from the collection's already-computed (backend-calculated) amount.
    """
    if not collection or collection.farmer_id is None:
        return None
    return create_entry(
        farmer_id=collection.farmer_id,
        branch_id=collection.branch_id,
        entry_type='MILK_EARNING',
        source_type='Collection',
        source_id=collection.id,
        entry_date=collection.date or _date.today(),
        description=f'Milk collection {collection.receipt_no or ""} · {collection.shift or ""} · {collection.quantity or 0}L'.strip(),
        credit=collection.amount or 0,
    )


def record_payment_debit(payment):
    """
    Debit a farmer when a payment is marked PAID.

    Called inside the payment finalization transaction (ADMIN action only).
    """
    if not payment or payment.farmer_id is None:
        return None
    return create_entry(
        farmer_id=payment.farmer_id,
        branch_id=payment.branch_id,
        entry_type='PAYMENT',
        source_type='Payment',
        source_id=payment.id,
        entry_date=payment.period_end or _date.today(),
        description=f'Payment {payment.pay_code or ""} settled'.strip(),
        debit=payment.total_amount or 0,
    )


# ── Backfill for data created before the ledger existed ─────────────────

def backfill_ledger():
    """
    Idempotently create ledger entries for historical collections and PAID
    payments that predate the ledger table. Runs at application startup so
    existing installations get a complete passbook without manual migration.
    """
    created = 0
    # Accepted collections without a ledger row
    coll_ids = [r[0] for r in db.session.query(Collection.id).all()]
    for cid in coll_ids:
        coll = Collection.query.get(cid)
        if not coll:
            continue
        has = FarmerLedgerEntry.query.filter_by(
            farmer_id=coll.farmer_id, source_type='Collection', source_id=coll.id).first()
        if not has:
            record_milk_earning(coll)
            created += 1

    # PAID payments without a ledger row
    pay_ids = [r[0] for r in db.session.query(Payment.id).filter_by(status='PAID').all()]
    for pid in pay_ids:
        pay = Payment.query.get(pid)
        if not pay:
            continue
        has = FarmerLedgerEntry.query.filter_by(
            farmer_id=pay.farmer_id, source_type='Payment', source_id=pay.id).first()
        if not has:
            record_payment_debit(pay)
            created += 1

    if created:
        db.session.commit()
        print(f'[LEDGER] Backfilled {created} farmer ledger entries')


def farmer_balance(farmer_id):
    """Net outstanding (credits - debits) for a farmer."""
    rows = FarmerLedgerEntry.query.filter_by(farmer_id=farmer_id).all()
    return round(sum((r.credit_amount or 0) for r in rows)
                 - sum((r.debit_amount or 0) for r in rows), 2)


def _reject_collection_credit(collection_id):
    """
    Remove the MILK_EARNING credit for a collection that was corrected to
    REJECTED. The farmer must not keep passbook credit for rejected milk.
    """
    entry = FarmerLedgerEntry.query.filter_by(
        source_type='Collection', source_id=collection_id).first()
    if entry:
        db.session.delete(entry)
        db.session.flush()
        _recompute_balances(entry.farmer_id)
