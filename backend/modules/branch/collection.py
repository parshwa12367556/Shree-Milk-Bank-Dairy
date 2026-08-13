"""
Shree Milk Bank — Collection Routes

GET   /api/collections          — List collections (filterable by date, shift)
POST  /api/collections          — Record new collection
PATCH /api/collections/<id>     — Correct an existing collection (branch-scoped)
"""
from datetime import date, datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from backend.app import db
from backend.models import Collection, Farmer, User
from backend.auth import can_collect, get_identity, get_branch_scope, reject_farmer
from backend.utils import generate_receipt_no, utcnow
from backend.services.pricing_service import calculate_collection_price
from backend.services import ledger_service
from backend.audit import log_audit
from backend.notify import notify

collection_bp = Blueprint('collections', __name__)

VALID_SHIFTS = ('MORNING', 'EVENING')
VALID_STATUSES = ('RECORDED', 'ACCEPTED', 'VERIFIED', 'REJECTED', 'CORRECTED')


def _farmer_user(farmer_id):
    """Login account (role=FARMER) linked to a farmer record, if any."""
    return User.query.filter_by(farmer_id=farmer_id, role='FARMER').first()


@collection_bp.route('/api/collections', methods=['GET'])
@jwt_required()
def get_collections():
    """List collections with filtering."""
    reject_farmer()  # farmers use /api/farmer/me/collections
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_str = request.args.get('date', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    shift = request.args.get('shift', '')
    milk_type = request.args.get('milkType', '')
    status = request.args.get('status', '')
    farmer_id = request.args.get('farmerId', type=int)
    branch_id = request.args.get('branchId', type=int)
    q = request.args.get('q', '').strip()

    query = Collection.query

    # Farmer search by ID / name (join on farmers, only for the caller's scope)
    if q:
        search = f'%{q}%'
        query = query.join(Farmer, Collection.farmer_id == Farmer.id).filter(
            db.or_(
                Farmer.farmer_code.ilike(search),
                Farmer.name.ilike(search),
                Farmer.mobile.ilike(search),
            )
        )

    # Filter by a single date, or a date range (from/to). No date at all
    # returns every record (used by the admin collections page).
    if date_str:
        try:
            query = query.filter_by(date=datetime.strptime(date_str, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass
    else:
        if date_from:
            try:
                query = query.filter(Collection.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
            except (ValueError, TypeError):
                pass
        if date_to:
            try:
                query = query.filter(Collection.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
            except (ValueError, TypeError):
                pass

    if milk_type:
        query = query.filter_by(milk_type=milk_type.upper())
    if status:
        status = status.upper()
        if status in VALID_STATUSES:
            query = query.filter_by(status=status)

    if shift:
        query = query.filter_by(shift=shift.upper())
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)
    if branch_id:
        query = query.filter_by(branch_id=branch_id)

    # Branch isolation
    user = get_identity()
    user_branch_id = user.get('branchId')
    if user.get('role') not in ('ADMIN',) and user_branch_id:
        query = query.filter_by(branch_id=user_branch_id)

    query = query.order_by(Collection.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Summary of the FILTERED result set (not just the current page)
    summary_rows = query.limit(10000).all()
    summary = {
        'totalQuantity': round(sum((c.quantity or 0) for c in summary_rows), 2),
        'totalAmount': round(sum((c.amount or 0) for c in summary_rows), 2),
        'collectionCount': pagination.total,
    }

    return jsonify({
        'collections': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'summary': summary,
    })


@collection_bp.route('/api/collections', methods=['POST'])
@jwt_required()
@can_collect()
def create_collection():
    """Record a new milk collection.

    The backend is the source of truth for the price: the amount is always
    recomputed server-side from the active rate card — a client-supplied
    amount is never trusted.

    Duplicate prevention: an optional `idempotencyKey` from the client makes
    the save safe to retry. The first submission wins; any later submission
    with the same key is rejected (409) instead of creating a second record.
    The unique `receipt_no` remains the final database-level guard.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    farmer_id = data.get('farmerId')
    quantity = data.get('quantity')

    if not farmer_id:
        return jsonify({'error': 'Farmer ID is required'}), 400
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return jsonify({'error': 'Valid quantity is required'}), 400
    if quantity <= 0:
        return jsonify({'error': 'Valid quantity is required'}), 400

    # Idempotency: reject a duplicate submission with the same key
    idem_key = (data.get('idempotencyKey') or '').strip() or None
    if idem_key:
        existing = Collection.query.filter_by(idempotency_key=idem_key).first()
        if existing:
            return jsonify({
                'error': 'Duplicate submission detected. This collection was already recorded.',
                'collection': existing.to_dict(),
                'receipt': existing.receipt_no,
            }), 409

    farmer = db.session.get(Farmer, farmer_id)
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    # Branch isolation: branch-scoped users can only collect from their own
    # branch's farmers, and the collection is always tagged with their branch.
    forced = get_branch_scope()
    if forced and farmer.branch_id != forced:
        return jsonify({'error': 'Access denied. Farmer belongs to another branch.'}), 403

    # Generate receipt number (retry on the tiny race of a colliding id)
    receipt_no = None
    for _ in range(3):
        last_collection = Collection.query.order_by(Collection.id.desc()).first()
        seq = (last_collection.id + 1) if last_collection else 1
        candidate = generate_receipt_no(seq)
        if not Collection.query.filter_by(receipt_no=candidate).first():
            receipt_no = candidate
            break
    if not receipt_no:
        return jsonify({'error': 'Could not allocate a receipt number. Try again.'}), 409

    fat = data.get('fat')
    if fat is None:
        fat = 4.0 if farmer.milk_type == 'COW' else 6.0
    snf = data.get('snf')
    if snf is None:
        snf = 8.5 if farmer.milk_type == 'COW' else 9.0
    try:
        fat = float(fat)
        snf = float(snf)
    except (TypeError, ValueError):
        return jsonify({'error': 'Fat and SNF must be numbers'}), 400

    # Compute price server-side via the pricing service — the amount is
    # always derived from the ACTIVE rate rule for the collection date.
    # A client-supplied amount/rate is never trusted.
    price = calculate_collection_price(farmer.milk_type, fat, snf, quantity)
    rate = price['rate']

    shift = (data.get('shift') or 'MORNING').upper()
    if shift not in VALID_SHIFTS:
        shift = 'MORNING'

    status = (data.get('status') or 'ACCEPTED').upper()
    if status not in VALID_STATUSES:
        status = 'ACCEPTED'

    user = get_identity()
    now = utcnow()

    # Quality grade derived server-side from the recorded parameters.
    quality_grade = None
    if data.get('water') is not None:
        from backend.pricing import quality_grade as grade_milk
        quality_grade = grade_milk(fat, float(data.get('water')), farmer.milk_type)['label']

    collection = Collection(
        receipt_no=receipt_no,
        farmer_id=farmer_id,
        branch_id=forced or data.get('branchId', farmer.branch_id),
        operator_id=user.get('uid'),
        rate_master_id=rate.id if rate else None,
        date=date.today(),
        collection_time=now.time(),
        shift=shift,
        milk_type=farmer.milk_type,
        quantity=quantity,
        fat=fat,
        snf=snf,
        clr=data.get('clr'),
        temperature=data.get('temperature'),
        water=data.get('water'),
        rate_per_liter=price['rate_per_liter'],
        amount=price['amount'],
        quality_grade=quality_grade,
        remarks=data.get('remarks', ''),
        idempotency_key=idem_key,
        status=status,
    )
    db.session.add(collection)
    db.session.flush()

    # Farmer passbook — same transaction, no drift: an accepted collection
    # immediately credits the farmer's ledger.
    if status in ('ACCEPTED', 'RECORDED', 'VERIFIED'):
        ledger_service.record_milk_earning(collection)

    log_audit('CREATE', 'Collection', receipt_no,
              detail=f'Recorded {quantity}L {farmer.milk_type} milk for {farmer.farmer_code} (₹{price["amount"]})')

    # Notify the farmer — the record appears in their portal immediately.
    # Only send when the farmer has a login account; a user_id=None would
    # create a GLOBAL notification with this farmer's private amounts.
    farmer_acct = _farmer_user(farmer.id)
    if farmer_acct:
        notify(
            'collection', 'New Milk Collection',
            f'{fmt_qty(quantity)} L of {farmer.milk_type.title()} milk recorded — '
            f'Fat {fat}% · SNF {snf}% · Amount ₹{price["amount"]:,.2f} · {shift}',
            link='/farmer/milk-history',
            user_id=farmer_acct.id,
        )
    try:
        db.session.commit()
    except IntegrityError:
        # Duplicate submission raced past the pre-check — the unique
        # idempotency_key index is the final guard.
        db.session.rollback()
        existing = Collection.query.filter_by(idempotency_key=idem_key).first() if idem_key else None
        if existing:
            return jsonify({
                'error': 'Duplicate submission detected. This collection was already recorded.',
                'collection': existing.to_dict(),
                'receipt': existing.receipt_no,
            }), 409
        return jsonify({'error': 'Could not save the collection. A conflicting record exists. Try again.'}), 409

    # Email the farmer the collection details. The recipient address is read
    # from the farmer's database record (farmer.email) — never from the
    # frontend. Delivery is best-effort and never blocks the collection flow.
    try:
        from backend.mailer import send_milk_collection_email
        sent, reason = send_milk_collection_email(collection)
        if not sent:
            current_app.logger.info(
                'Milk collection email to %s skipped: %s',
                (collection.farmer.email if collection.farmer else None), reason)
    except Exception as exc:  # noqa: BLE001 — email must never break collection
        current_app.logger.warning('Milk collection email failed: %s', exc)

    # SMS the farmer when SMS is configured and the farmer opted in.
    # Post-commit + best-effort: a gateway failure never fails the collection.
    try:
        from backend.sms import is_sms_configured, send_sms_async
        if is_sms_configured() and farmer.notification_sms:
            mobile = (farmer.mobile or '').strip()
            if mobile:
                send_sms_async(
                    mobile,
                    f'Shree Milk Bank: {quantity:g}L {farmer.milk_type.title()} milk recorded. '
                    f'Fat {fat}% · SNF {snf}% · Amount ₹{price["amount"]:,.2f} · Receipt {receipt_no}',
                    notification_type='COLLECTION', related_type='Collection',
                    related_id=collection.id)
    except Exception as exc:  # noqa: BLE001 — SMS must never break collection
        current_app.logger.warning('Milk collection SMS failed: %s', exc)

    return jsonify({
        'collection': collection.to_dict(),
        'message': f'Collection recorded. Receipt #{receipt_no}',
        'receipt': receipt_no,
        'amount': price['amount'],
    }), 201


@collection_bp.route('/api/collections/<int:collection_id>', methods=['PATCH'])
@jwt_required()
@can_collect()
def update_collection(collection_id):
    """Correct an existing collection (branch-scoped, audit-logged).

    The farmer's portal picks up the corrected values automatically on its
    next refresh — no duplicate record is created.
    """
    collection = db.session.get(Collection, collection_id)
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404

    # Branch isolation: managers/operators may only correct their own branch
    forced = get_branch_scope()
    if forced and collection.branch_id != forced:
        return jsonify({'error': 'Access denied. Collection belongs to another branch.'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    farmer = collection.farmer
    changes = []

    # Quantity / fat / snf changes are re-priced with the current active rate
    new_qty = data.get('quantity', collection.quantity)
    new_fat = data.get('fat', collection.fat)
    new_snf = data.get('snf', collection.snf)
    try:
        new_qty = float(new_qty)
        new_fat = float(new_fat) if new_fat is not None else collection.fat
        new_snf = float(new_snf) if new_snf is not None else collection.snf
    except (TypeError, ValueError):
        return jsonify({'error': 'Quantity, fat and SNF must be numbers'}), 400
    if new_qty <= 0:
        return jsonify({'error': 'Quantity must be greater than zero'}), 400

    if abs(new_qty - collection.quantity) > 1e-9:
        changes.append(f'quantity {collection.quantity}→{new_qty}')
    if abs(new_fat - (collection.fat or 0)) > 1e-9:
        changes.append(f'fat {collection.fat}→{new_fat}')
    if abs(new_snf - (collection.snf or 0)) > 1e-9:
        changes.append(f'snf {collection.snf}→{new_snf}')

    if changes and (new_fat is None or new_snf is None):
        return jsonify({'error': 'Fat and SNF values are required to re-price the collection.'}), 400

    if changes:
        # Re-price using the pricing service (active rate for the milk type)
        price = calculate_collection_price(
            farmer.milk_type, new_fat, new_snf, new_qty, on_date=collection.date)
        collection.quantity = new_qty
        collection.fat = new_fat
        collection.snf = new_snf
        collection.rate_per_liter = price['rate_per_liter']
        collection.amount = price['amount']

    # Shift / remarks / status corrections
    if 'shift' in data:
        shift = (data.get('shift') or '').upper()
        if shift in VALID_SHIFTS and shift != collection.shift:
            changes.append(f'shift {collection.shift}→{shift}')
            collection.shift = shift
    if 'remarks' in data:
        collection.remarks = data.get('remarks')
    if 'status' in data:
        new_status = (data.get('status') or '').upper()
        if new_status in VALID_STATUSES and new_status != collection.status:
            changes.append(f'status {collection.status}→{new_status}')
            collection.status = new_status

    collection.status = 'CORRECTED' if collection.status == 'ACCEPTED' and changes else collection.status

    reason = (data.get('reason') or '').strip()
    log_audit('UPDATE', 'Collection', collection.receipt_no,
              detail=f'Corrected collection {collection.receipt_no}: '
                     + ('; '.join(changes) if changes else 'details updated')
                     + (f' — reason: {reason}' if reason else ''))

    # Keep the farmer's ledger credit in sync with the corrected amount.
    # record_milk_earning is idempotent per (farmer, Collection, id) — it
    # returns the existing row, which we update with the new amount.
    # A correction to REJECTED reverses the earning (the farmer must not
    # keep passbook credit for milk that was ultimately rejected).
    if changes:
        from backend.services.ledger_service import _recompute_balances, _reject_collection_credit
        if collection.status == 'REJECTED':
            _reject_collection_credit(collection.id)
        elif collection.status in ('ACCEPTED', 'RECORDED', 'VERIFIED', 'CORRECTED'):
            entry = ledger_service.record_milk_earning(collection)
            if entry:
                entry.credit_amount = round(collection.amount or 0, 2)
                db.session.flush()
            _recompute_balances(collection.farmer_id)

    # Notify the farmer that their record was corrected
    farmer_acct = _farmer_user(collection.farmer_id)
    if farmer_acct:
        notify(
            'collection', 'Collection Updated',
            f'Your collection {collection.receipt_no} was updated — '
            f'{fmt_qty(collection.quantity)} L · Fat {collection.fat}% · '
            f'SNF {collection.snf}% · Amount ₹{collection.amount:,.2f}'
            + (f'. Reason: {reason}' if reason else ''),
            link='/farmer/milk-history',
            user_id=farmer_acct.id,
        )
    db.session.commit()

    return jsonify({
        'collection': collection.to_dict(),
        'message': 'Collection updated successfully.',
    })


def fmt_qty(q):
    """Format a quantity, dropping unnecessary trailing zeros."""
    if q is None:
        return '0'
    return f'{q:g}'
