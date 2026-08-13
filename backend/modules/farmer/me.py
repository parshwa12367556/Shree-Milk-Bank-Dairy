"""
Shree Milk Bank — Farmer Self-Service API
=========================================
Every endpoint in this blueprint is scoped to the *authenticated* farmer.
The farmer_id is always derived from the JWT identity (`farmerId`) — it is
NEVER taken from the query string or request body, so a farmer can never
request another farmer's records by tampering with parameters.

Endpoints
---------
GET    /api/farmer/me                    — Own profile
PATCH  /api/farmer/me/profile            — Update permitted personal fields
GET    /api/farmer/me/dashboard          — Dashboard stats (today, totals, recent)
GET    /api/farmer/me/collections        — Own milk collections (filter/paginate)
GET    /api/farmer/me/daily-collection   — Today's own collection (morning/evening)
GET    /api/farmer/me/passbook           — Own passbook (collections + payments)
GET    /api/farmer/me/payments           — Own payments
GET    /api/farmer/me/bank-details       — Own bank details (account masked)
POST   /api/farmer/me/bank-details       — Save/update own bank details
GET    /api/farmer/me/documents          — Own documents
POST   /api/farmer/me/documents          — Upload a document
DELETE /api/farmer/me/documents/<id>     — Delete an own pending document
GET    /api/farmer/me/notifications      — Own notifications + dairy announcements
PATCH  /api/farmer/me/notifications/read — Mark own notifications as read
GET    /api/farmer/me/grievances         — Own grievances
POST   /api/farmer/me/grievances         — Raise a grievance
GET    /api/farmer/me/grievances/<id>    — Own grievance detail
GET    /api/farmer/me/settings           — Own notification preferences
PATCH  /api/farmer/me/settings           — Update own notification preferences
"""
import os
import uuid
from datetime import date, datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from backend.app import db
from backend.models import (
    Collection, Payment, Notification, Grievance, User, Farmer, BankDetail,
    FarmerDocument,
)
from backend.auth import get_identity
from backend.audit import log_audit
from backend.utils import sign_farmer_qr

farmer_me_bp = Blueprint('farmer_me', __name__)


# ── Helpers ──────────────────────────────────────────────────────────────

def _auth_farmer():
    """
    Resolve the currently authenticated farmer from the JWT.

    Returns (farmer, user) or raises a 401/403 JSON error. The farmer_id is
    taken exclusively from the token — client-supplied ids are ignored.
    """
    from backend.models import Farmer
    identity = get_identity()
    if not identity:
        return None, None, {'error': 'Authentication required.'}, 401
    if identity.get('role') != 'FARMER':
        return None, None, {'error': 'Access denied. Farmer portal only.'}, 403

    farmer_id = identity.get('farmerId')
    if not farmer_id:
        return None, None, {'error': 'Farmer account is not linked to a farmer record.'}, 403

    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return None, None, {'error': 'Farmer record not found.'}, 404

    user = User.query.filter_by(farmer_id=farmer.id, role='FARMER').first()
    return farmer, user, None, None


def _collection_payload(c):
    """Collection row for the farmer portal (own data only)."""
    return {
        'id': c.id,
        'receiptNo': c.receipt_no,
        'farmerId': c.farmer_id,
        'date': c.date.isoformat() if c.date else None,
        'shift': c.shift,
        'milkType': c.milk_type,
        'quantity': c.quantity,
        'fat': c.fat,
        'snf': c.snf,
        'clr': c.clr,
        'temperature': c.temperature,
        'water': c.water,
        'ratePerLiter': c.rate_per_liter,
        'amount': c.amount,
        'status': c.status,
        'createdAt': c.created_at.isoformat() if c.created_at else None,
    }


# ── Profile ──────────────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me', methods=['GET'])
@jwt_required()
def my_profile():
    """Return the authenticated farmer's own profile."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    bank = farmer.bank_detail
    return jsonify({
        'farmer': {
            'id': farmer.id,
            'farmerCode': farmer.farmer_code,
            'name': farmer.name,
            'fatherName': farmer.father_name,
            'mobile': farmer.mobile,
            'email': farmer.email,
            'village': farmer.village,
            'taluka': farmer.taluka,
            'district': farmer.district,
            'state': farmer.state,
            'milkType': farmer.milk_type,
            'cowCount': farmer.cow_count,
            'buffaloCount': farmer.buffalo_count,
            'breed': farmer.breed,
            'preferredShift': farmer.preferred_shift,
            'branchId': farmer.branch_id,
            'branchName': farmer.branch.name if farmer.branch else None,
            'branchCode': farmer.branch.code if farmer.branch else None,
            'status': farmer.status,
            'joinedAt': farmer.joined_at.isoformat() if farmer.joined_at else None,
            'bankDetail': bank.to_dict() if bank else None,
            # Signed QR payload + rendered image for the farmer's own QR card
            # (contains only a signed identifier — no private data).
            'qrPayload': farmer.qr_code or sign_farmer_qr(farmer.farmer_code),
            'qrImage': _my_qr_image(farmer),
        },
    })


def _my_qr_image(farmer):
    """Render the farmer's own QR card image (SVG data URI), or None."""
    try:
        from backend.modules.farmer.farmers import _qr_data_uri
        return _qr_data_uri(farmer.qr_code or sign_farmer_qr(farmer.farmer_code))
    except Exception:
        return None


def _bank_payload(bank):
    """Bank detail row with the account number masked for safe display."""
    if not bank:
        return None
    acc = bank.account_number or ''
    masked = (acc[:4] + '*' * max(len(acc) - 8, 0) + acc[-4:]) if len(acc) > 8 else '***'
    return {
        'id': bank.id,
        'accountHolder': bank.account_holder,
        'bankName': bank.bank_name,
        'branchName': bank.branch_name,
        'accountNumber': bank.account_number,
        'accountNumberMasked': masked,
        'ifsc': bank.ifsc,
        'upi': bank.upi,
        'verificationStatus': bank.verification_status,
    }


@farmer_me_bp.route('/api/farmer/me/profile', methods=['GET'])
@jwt_required()
def my_profile_alias():
    """Alias of GET /api/farmer/me (spec 7.8 — profile API)."""
    return my_profile()


@farmer_me_bp.route('/api/farmer/me/profile', methods=['PATCH'])
@jwt_required()
def update_my_profile():
    """Update permitted personal fields of the authenticated farmer.

    Immutable fields (farmer ID, branch, milk type, status, role) are never
    accepted — they can only be changed by ADMIN / BRANCH_OPERATOR.
    """
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    data = request.get_json(silent=True) or {}
    allowed = {
        'mobile': 'mobile', 'altMobile': 'alt_mobile', 'email': 'email',
        'address': 'address', 'village': 'village', 'taluka': 'taluka',
        'district': 'district', 'state': 'state', 'pincode': 'pincode',
        'landmark': 'landmark',
    }
    changed = []
    for json_key, attr in allowed.items():
        if json_key in data:
            value = (data[json_key] or '').strip() if isinstance(data[json_key], str) else data[json_key]
            if value:
                setattr(farmer, attr, value)
                changed.append(json_key)

    if 'email' in changed:
        farmer.email = farmer.email.strip().lower()
        if user:
            user.email = farmer.email  # farmers sign in with their email

    if changed:
        log_audit('UPDATE', 'Farmer', farmer.farmer_code,
                  detail=f'Farmer updated own profile: {", ".join(changed)}')
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully',
                        'farmer': {
                            'id': farmer.id,
                            'farmerCode': farmer.farmer_code,
                            'name': farmer.name,
                            'mobile': farmer.mobile,
                            'email': farmer.email,
                            'village': farmer.village,
                            'taluka': farmer.taluka,
                            'district': farmer.district,
                            'state': farmer.state,
                        }})
    return jsonify({'message': 'No changes provided'})


# ── Dashboard ────────────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/dashboard', methods=['GET'])
@jwt_required()
def my_dashboard():
    """Aggregated dashboard data for the authenticated farmer."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    today = date.today()
    month_start = today.replace(day=1)

    def _sum_rows(query):
        rows = query.all()
        return rows, sum((r.quantity or 0) for r in rows), sum((r.amount or 0) for r in rows)

    # Today's collections (morning/evening split)
    today_rows, today_qty, today_amount = _sum_rows(
        Collection.query.filter_by(farmer_id=farmer.id, date=today))
    morning_qty = sum((r.quantity or 0) for r in today_rows if r.shift == 'MORNING')
    evening_qty = sum((r.quantity or 0) for r in today_rows if r.shift == 'EVENING')
    morning_amount = sum((r.amount or 0) for r in today_rows if r.shift == 'MORNING')
    evening_amount = sum((r.amount or 0) for r in today_rows if r.shift == 'EVENING')

    # This month + all-time totals
    _, month_qty, month_amount = _sum_rows(
        Collection.query.filter_by(farmer_id=farmer.id).filter(Collection.date >= month_start))
    _, total_qty, total_amount = _sum_rows(Collection.query.filter_by(farmer_id=farmer.id))

    # Payments: pending (current) + paid totals
    payments = Payment.query.filter_by(farmer_id=farmer.id).order_by(Payment.created_at.desc()).all()
    pending_amount = sum(p.total_amount or 0 for p in payments if p.status in ('PENDING', 'APPROVED'))
    paid_amount = sum(p.total_amount or 0 for p in payments if p.status == 'PAID')
    current_payment = next(
        (p for p in payments if p.status in ('PENDING', 'APPROVED')), None)

    # Recent collections (latest 5)
    recent_collections = Collection.query.filter_by(farmer_id=farmer.id) \
        .order_by(Collection.created_at.desc()).limit(5).all()

    # Recent payments (latest 3)
    recent_payments = payments[:3]

    # Unread notifications + recent notifications
    unread_count = 0
    recent_notifications = []
    if user:
        unread_count = Notification.query.filter(
            Notification.user_id == user.id, Notification.read.is_(False)).count()
        recent_notifications = Notification.query.filter(
            db.or_(Notification.user_id == user.id, Notification.user_id.is_(None))
        ).order_by(Notification.created_at.desc()).limit(4).all()

    avg_fat = None
    fats = [c.fat for c in Collection.query.filter_by(farmer_id=farmer.id).all() if c.fat]
    if fats:
        avg_fat = round(sum(fats) / len(fats), 1)

    return jsonify({
        'farmer': {
            'id': farmer.id,
            'farmerCode': farmer.farmer_code,
            'name': farmer.name,
            'mobile': farmer.mobile,
            'milkType': farmer.milk_type,
            'branchName': farmer.branch.name if farmer.branch else None,
            'branchCode': farmer.branch.code if farmer.branch else None,
        },
        'today': {
            'quantity': round(today_qty, 2),
            'amount': round(today_amount, 2),
            'morningQuantity': round(morning_qty, 2),
            'morningAmount': round(morning_amount, 2),
            'eveningQuantity': round(evening_qty, 2),
            'eveningAmount': round(evening_amount, 2),
            'collectionCount': len(today_rows),
        },
        'totals': {
            'monthQuantity': round(month_qty, 2),
            'monthAmount': round(month_amount, 2),
            'totalQuantity': round(total_qty, 2),
            'totalAmount': round(total_amount, 2),
            'collectionCount': Collection.query.filter_by(farmer_id=farmer.id).count(),
            'avgFat': avg_fat,
        },
        'payment': {
            'pendingAmount': round(pending_amount, 2),
            'paidAmount': round(paid_amount, 2),
            'currentPayment': current_payment.to_dict() if current_payment else None,
        },
        'recentCollections': [_collection_payload(c) for c in recent_collections],
        'recentPayments': [p.to_dict() for p in recent_payments],
        'notifications': {
            'unreadCount': unread_count,
            'recent': [n.to_dict() for n in recent_notifications],
        },
    })


# ── Milk collections ─────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/collections', methods=['GET'])
@jwt_required()
def my_collections():
    """The authenticated farmer's own collection records."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    shift = (request.args.get('shift') or '').upper()
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')

    query = Collection.query.filter_by(farmer_id=farmer.id)

    if shift in ('MORNING', 'EVENING'):
        query = query.filter_by(shift=shift)
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

    query = query.order_by(Collection.date.desc(), Collection.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'collections': [_collection_payload(c) for c in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'perPage': per_page,
    })


# ── Passbook ─────────────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/passbook', methods=['GET'])
@jwt_required()
def my_passbook():
    """
    Digital passbook — generated from the real farmer ledger
    (`farmer_ledger_entries`), which is written in the same transaction as
    every collection (credit) and settled payment (debit). No frontend
    computation; the running balance comes straight from the ledger.
    """
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    from backend.models import FarmerLedgerEntry
    from backend.services import ledger_service

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')

    query = FarmerLedgerEntry.query.filter_by(farmer_id=farmer.id)
    if date_from:
        try:
            query = query.filter(FarmerLedgerEntry.entry_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass
    if date_to:
        try:
            query = query.filter(FarmerLedgerEntry.entry_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass

    query = query.order_by(FarmerLedgerEntry.entry_date.desc(),
                           FarmerLedgerEntry.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Enrich ledger rows with collection/payment display data.
    entries = []
    coll_map = {c.id: c for c in Collection.query.filter_by(farmer_id=farmer.id).all()}
    pay_map = {p.id: p for p in Payment.query.filter_by(farmer_id=farmer.id).all()}
    for le in pagination.items:
        base = {
            'id': le.id,
            'farmerId': le.farmer_id,
            'entryType': le.entry_type,
            'date': le.entry_date.isoformat() if le.entry_date else None,
            'description': le.description,
            'credit': le.credit_amount,
            'debit': le.debit_amount,
            'balance': round(le.running_balance or 0, 2),
        }
        if le.source_type == 'Collection' and le.source_id in coll_map:
            c = coll_map[le.source_id]
            base.update({
                'shift': c.shift,
                'milkType': c.milk_type,
                'quantity': c.quantity,
                'fat': c.fat,
                'snf': c.snf,
                'ratePerLiter': c.rate_per_liter,
                'amount': c.amount,
                'receiptNo': c.receipt_no,
                'paymentStatus': c.payment.status if c.payment else None,
                'paymentCode': c.payment.pay_code if c.payment else None,
            })
        elif le.source_type == 'Payment' and le.source_id in pay_map:
            p = pay_map[le.source_id]
            base.update({
                'amount': -(le.debit_amount or 0),  # debit shown as negative
                'paymentStatus': p.status,
                'paymentCode': p.pay_code,
            })
        entries.append(base)

    # Summary from the full ledger (unfiltered). Quantity counts only the
    # collections that actually carry a MILK_EARNING credit (rejected
    # collections have no credit, so they must not inflate the summary).
    all_entries = FarmerLedgerEntry.query.filter_by(farmer_id=farmer.id).all()
    credited_coll_ids = {
        e.source_id for e in all_entries
        if e.source_type == 'Collection' and (e.credit_amount or 0) > 0
    }
    total_qty = sum(
        (c.quantity or 0) for cid, c in coll_map.items() if cid in credited_coll_ids)
    credits = sum((e.credit_amount or 0) for e in all_entries)
    debits = sum((e.debit_amount or 0) for e in all_entries)
    paid_total = sum(
        (p.total_amount or 0) for p in Payment.query.filter_by(
            farmer_id=farmer.id, status='PAID').all())

    return jsonify({
        'entries': entries,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'perPage': per_page,
        'summary': {
            'totalQuantity': round(total_qty, 2),
            'totalAmount': round(credits, 2),
            'paidAmount': round(paid_total, 2),
            'pendingAmount': round(ledger_service.farmer_balance(farmer.id), 2),
        },
    })


# ── Payments ─────────────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/payments', methods=['GET'])
@jwt_required()
def my_payments():
    """The authenticated farmer's own payment history."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status_filter = (request.args.get('status') or '').upper()

    query = Payment.query.filter_by(farmer_id=farmer.id)
    if status_filter in ('PENDING', 'APPROVED', 'PAID'):
        query = query.filter_by(status=status_filter)

    query = query.order_by(Payment.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    pending = Payment.query.filter(
        Payment.farmer_id == farmer.id,
        Payment.status.in_(['PENDING', 'APPROVED']),
    ).all()
    paid = Payment.query.filter(
        Payment.farmer_id == farmer.id, Payment.status == 'PAID').all()

    return jsonify({
        'payments': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'perPage': per_page,
        'summary': {
            'pendingAmount': round(sum((p.total_amount or 0) for p in pending), 2),
            'pendingCount': len(pending),
            'paidAmount': round(sum((p.total_amount or 0) for p in paid), 2),
            'paidCount': len(paid),
        },
    })


# ── Notifications ────────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/notifications', methods=['GET'])
@jwt_required()
def my_notifications():
    """Notifications for the authenticated farmer + dairy-wide announcements."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    limit = min(request.args.get('limit', 30, type=int), 100)
    unread_only = request.args.get('unread', '').lower() == 'true'

    query = Notification.query.order_by(Notification.created_at.desc())
    if user:
        query = query.filter(
            db.or_(Notification.user_id == user.id, Notification.user_id.is_(None)))
    else:
        query = query.filter(Notification.user_id.is_(None))
    if unread_only:
        query = query.filter(Notification.read.is_(False))

    notifications = query.limit(limit).all()
    unread_count = 0
    if user:
        unread_count = Notification.query.filter(
            Notification.user_id == user.id, Notification.read.is_(False)).count()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unreadCount': unread_count,
    })


@farmer_me_bp.route('/api/farmer/me/notifications/read', methods=['PATCH'])
@jwt_required()
def mark_my_notifications_read():
    """Mark the farmer's own notifications as read."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status
    if not user:
        return jsonify({'error': 'No notification account linked.'}), 400

    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if ids:
        Notification.query.filter(
            Notification.user_id == user.id, Notification.id.in_(ids)) \
            .update({Notification.read: True}, synchronize_session=False)
    else:
        Notification.query.filter(
            Notification.user_id == user.id, Notification.read.is_(False)) \
            .update({Notification.read: True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'message': 'Notifications marked as read'})


# ── Grievances ───────────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/grievances', methods=['GET'])
@jwt_required()
def my_grievances():
    """List the authenticated farmer's own grievances."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    grievances = Grievance.query.filter_by(farmer_id=farmer.id) \
        .order_by(Grievance.created_at.desc()).all()
    return jsonify({'grievances': [g.to_dict() for g in grievances]})


@farmer_me_bp.route('/api/farmer/me/grievances', methods=['POST'])
@jwt_required()
def create_grievance():
    """Raise a grievance for the authenticated farmer."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    data = request.get_json(silent=True) or {}
    subject = (data.get('subject') or '').strip()
    category = (data.get('category') or '').strip().upper()
    description = (data.get('description') or '').strip()

    if not subject:
        return jsonify({'error': 'Subject is required'}), 400
    if category not in ('PAYMENT', 'QUALITY', 'COLLECTION', 'OTHER'):
        category = 'OTHER'
    if not description:
        return jsonify({'error': 'Description is required'}), 400

    last = Grievance.query.order_by(Grievance.id.desc()).first()
    seq = (last.id + 1) if last else 1
    grievance = Grievance(
        grievance_code=f'GRV{seq:06d}',
        farmer_id=farmer.id,
        branch_id=farmer.branch_id,
        subject=subject,
        category=category,
        description=description,
        receipt_no=(data.get('receiptNo') or '').strip() or None,
        status='OPEN',
    )
    db.session.add(grievance)
    db.session.flush()
    log_audit('CREATE', 'Grievance', grievance.grievance_code,
              detail=f'{farmer.farmer_code} raised a {category} grievance: {subject}')
    db.session.commit()

    return jsonify({
        'grievance': grievance.to_dict(),
        'message': 'Grievance submitted. The dairy will respond shortly.',
    }), 201


@farmer_me_bp.route('/api/farmer/me/grievances/<int:grievance_id>', methods=['GET'])
@jwt_required()
def my_grievance_detail(grievance_id):
    """A single grievance — only if it belongs to the authenticated farmer."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    grievance = Grievance.query.filter_by(
        id=grievance_id, farmer_id=farmer.id).first()
    if not grievance:
        return jsonify({'error': 'Grievance not found'}), 404
    return jsonify({'grievance': grievance.to_dict()})


# ── Daily collection ─────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/daily-collection', methods=['GET'])
@jwt_required()
def my_daily_collection():
    """Today's own milk collection — morning / evening / summary."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    today = date.today()
    rows = Collection.query.filter_by(farmer_id=farmer.id, date=today) \
        .order_by(Collection.created_at.asc()).all()

    def _shift(shift):
        rows_s = [r for r in rows if r.shift == shift]
        return {
            'quantity': round(sum((r.quantity or 0) for r in rows_s), 2),
            'amount': round(sum((r.amount or 0) for r in rows_s), 2),
            'fat': round(sum((r.fat or 0) for r in rows_s) / len(rows_s), 1) if rows_s else None,
            'snf': round(sum((r.snf or 0) for r in rows_s) / len(rows_s), 1) if rows_s else None,
            'ratePerLiter': (rows_s[0].rate_per_liter if rows_s else None),
            'collections': [_collection_payload(r) for r in rows_s],
        }

    return jsonify({
        'date': today.isoformat(),
        'morning': _shift('MORNING'),
        'evening': _shift('EVENING'),
        'summary': {
            'totalQuantity': round(sum((r.quantity or 0) for r in rows), 2),
            'totalAmount': round(sum((r.amount or 0) for r in rows), 2),
            'collectionCount': len(rows),
        },
    })


# ── Bank details ─────────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/bank-details', methods=['GET'])
@jwt_required()
def my_bank_details():
    """The authenticated farmer's own bank details (masked for display)."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status
    return jsonify({'bankDetail': _bank_payload(farmer.bank_detail)})


@farmer_me_bp.route('/api/farmer/me/bank-details', methods=['POST', 'PATCH'])
@jwt_required()
def save_my_bank_details():
    """Save/update the authenticated farmer's own bank details.

    Saving a change resets verification to PENDING so the ADMIN can
    re-review the new details before any payment transfer.
    """
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    data = request.get_json(silent=True) or {}
    bank = farmer.bank_detail
    if not bank:
        bank = BankDetail(farmer_id=farmer.id)
        db.session.add(bank)

    for json_key, attr in [
        ('accountHolder', 'account_holder'), ('bankName', 'bank_name'),
        ('branchName', 'branch_name'), ('accountNumber', 'account_number'),
        ('ifsc', 'ifsc'), ('upi', 'upi'),
    ]:
        if json_key in data:
            setattr(bank, attr, (data[json_key] or '').strip())

    if not bank.account_holder or not bank.account_number or not bank.ifsc:
        return jsonify({'error': 'Account holder, account number and IFSC are required.'}), 400

    # Any edit invalidates the previous verification.
    bank.verification_status = 'PENDING'
    bank.verified_by = None
    bank.verified_at = None

    log_audit('UPDATE', 'BankDetail', farmer.farmer_code,
              detail=f'{farmer.farmer_code} updated own bank details (awaiting verification)')
    db.session.commit()
    return jsonify({
        'message': 'Bank details saved. Verification status reset to PENDING.',
        'bankDetail': _bank_payload(bank),
    })


# ── Documents ────────────────────────────────────────────────────────────

_DOC_UPLOAD_DIR = os.path.join('static', 'uploads', 'documents')
_MAX_DOC_SIZE = 5 * 1024 * 1024  # 5 MB — enforced server-side too


@farmer_me_bp.route('/api/farmer/me/documents', methods=['GET'])
@jwt_required()
def my_documents():
    """The authenticated farmer's own uploaded documents."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    documents = FarmerDocument.query.filter_by(farmer_id=farmer.id) \
        .order_by(FarmerDocument.created_at.desc()).all()
    return jsonify({'documents': [d.to_dict() for d in documents]})


@farmer_me_bp.route('/api/farmer/me/documents', methods=['POST'])
@jwt_required()
def upload_my_document():
    """Upload a document for the authenticated farmer."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    title = (request.form.get('title') or '').strip()
    doc_type = (request.form.get('docType') or 'OTHER').strip().upper()
    file = request.files.get('file')

    if not title:
        return jsonify({'error': 'Document title is required'}), 400
    if not file or not file.filename:
        return jsonify({'error': 'A file is required'}), 400
    if doc_type not in ('AADHAAR', 'PAN', 'BANK_PASSBOOK', 'PHOTO', 'ADDRESS_PROOF', 'OTHER'):
        doc_type = 'OTHER'

    # Sandbox the filename and store under /static/uploads/documents/<farmer>/.
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.pdf', '.jpg', '.jpeg', '.png', '.webp'):
        return jsonify({'error': 'Only PDF or image files are allowed.'}), 400

    # Enforce the size cap server-side (client-side limits are not security).
    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > _MAX_DOC_SIZE:
        return jsonify({'error': 'File is too large. Maximum size is 5 MB.'}), 400

    rel_dir = os.path.join(_DOC_UPLOAD_DIR, farmer.farmer_code)
    abs_dir = os.path.join(current_app.root_path, '..', rel_dir)
    abs_dir = os.path.abspath(abs_dir)
    os.makedirs(abs_dir, exist_ok=True)

    fname = f'{uuid.uuid4().hex}{ext}'
    file.save(os.path.join(abs_dir, fname))
    file_path = f'/{rel_dir.replace(os.sep, "/")}/{fname}'

    doc = FarmerDocument(
        farmer_id=farmer.id,
        doc_type=doc_type,
        title=title,
        file_path=file_path,
        mime_type=file.mimetype,
        status='PENDING',
    )
    db.session.add(doc)
    db.session.commit()
    log_audit('CREATE', 'FarmerDocument', farmer.farmer_code,
              detail=f'{farmer.farmer_code} uploaded a {doc_type} document: {title}')
    return jsonify({'document': doc.to_dict(),
                    'message': 'Document uploaded. Pending review by the dairy.'}), 201


@farmer_me_bp.route('/api/farmer/me/documents/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_my_document(doc_id):
    """Delete one of the farmer's own documents (pending ones only)."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    doc = FarmerDocument.query.filter_by(id=doc_id, farmer_id=farmer.id).first()
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
    if doc.status not in ('PENDING', 'REJECTED'):
        return jsonify({'error': 'Approved documents cannot be deleted. Contact the dairy.'}), 400

    db.session.delete(doc)
    db.session.commit()
    return jsonify({'message': 'Document removed'})


# ── Settings ─────────────────────────────────────────────────────────────

@farmer_me_bp.route('/api/farmer/me/settings', methods=['GET'])
@jwt_required()
def my_settings():
    """The authenticated farmer's notification preferences."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status
    # WhatsApp is reported as NOT available until a WhatsApp provider is
    # configured — the UI must never show an enabled toggle for it.
    return jsonify({
        'settings': {
            'notificationSms': bool(farmer.notification_sms),
            'notificationWhatsapp': bool(farmer.notification_whatsapp),
            'notificationEmail': bool(farmer.notification_email),
            'email': farmer.email,
            'mobile': farmer.mobile,
        },
        'capabilities': {'whatsapp': False},
    })


@farmer_me_bp.route('/api/farmer/me/settings', methods=['PATCH'])
@jwt_required()
def update_my_settings():
    """Update the authenticated farmer's notification preferences."""
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    data = request.get_json(silent=True) or {}
    for json_key, attr in [
        ('notificationSms', 'notification_sms'),
        ('notificationWhatsapp', 'notification_whatsapp'),
        ('notificationEmail', 'notification_email'),
    ]:
        if json_key in data:
            # No WhatsApp provider is integrated — the toggle is force-disabled
            # server-side so the preference can never be falsely "enabled".
            if attr == 'notification_whatsapp':
                continue
            setattr(farmer, attr, bool(data[json_key]))

    log_audit('UPDATE', 'Farmer', farmer.farmer_code,
              detail=f'{farmer.farmer_code} updated notification preferences')
    db.session.commit()
    return jsonify({'message': 'Settings saved',
                    'settings': {
                        'notificationSms': bool(farmer.notification_sms),
                        'notificationWhatsapp': bool(farmer.notification_whatsapp),
                        'notificationEmail': bool(farmer.notification_email),
                    }})

