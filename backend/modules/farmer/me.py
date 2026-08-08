"""
Shree Milk Bank — Farmer Self-Service API
=========================================
Every endpoint in this blueprint is scoped to the *authenticated* farmer.
The farmer_id is always derived from the JWT identity (`farmerId`) — it is
NEVER taken from the query string or request body, so a farmer can never
request another farmer's records by tampering with parameters.

Endpoints
---------
GET   /api/farmer/me                      — Own profile
GET   /api/farmer/me/dashboard            — Dashboard stats (today, totals, recent)
GET   /api/farmer/me/collections          — Own milk collections (filter/paginate)
GET   /api/farmer/me/passbook             — Own passbook (collections + payments)
GET   /api/farmer/me/payments             — Own payments
GET   /api/farmer/me/notifications        — Own notifications + dairy announcements
PATCH /api/farmer/me/notifications/read   — Mark own notifications as read
GET   /api/farmer/me/grievances           — Own grievances
POST  /api/farmer/me/grievances           — Raise a grievance
"""
from datetime import date, datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from backend.app import db
from backend.models import (
    Collection, Payment, Notification, Grievance, User,
)
from backend.auth import get_identity
from backend.audit import log_audit

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
        },
    })


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
    Digital passbook — one row per milk collection, enriched with the
    payment status of the period it belongs to.
    """
    farmer, user, err, status = _auth_farmer()
    if err:
        return jsonify(err), status

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')

    query = Collection.query.filter_by(farmer_id=farmer.id)
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

    # Running balance = cumulative amount of ALL collections up to and
    # including each entry, against the total paid so far.
    all_colls = Collection.query.filter_by(farmer_id=farmer.id) \
        .order_by(Collection.date.asc(), Collection.id.asc()).all()
    running = 0.0
    running_map = {}
    for c in all_colls:
        running += (c.amount or 0)
        running_map[c.id] = round(running, 2)

    entries = []
    for c in pagination.items:
        pay_status = None
        if c.payment:
            pay_status = c.payment.status
        entries.append({
            **_collection_payload(c),
            'paymentStatus': pay_status,
            'paymentCode': c.payment.pay_code if c.payment else None,
            'balance': round(running_map.get(c.id, 0), 2),
        })

    paid_total = sum(
        (p.total_amount or 0) for p in Payment.query.filter_by(farmer_id=farmer.id).all()
        if p.status == 'PAID'
    )
    return jsonify({
        'entries': entries,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'perPage': per_page,
        'summary': {
            'totalQuantity': round(sum((c.quantity or 0) for c in all_colls), 2),
            'totalAmount': round(sum((c.amount or 0) for c in all_colls), 2),
            'paidAmount': round(paid_total, 2),
            'pendingAmount': round(
                sum((c.amount or 0) for c in all_colls) - paid_total, 2),
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
