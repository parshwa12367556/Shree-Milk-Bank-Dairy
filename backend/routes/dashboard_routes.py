"""
Smart Dairy ERP — Dashboard Routes

GET /api/dashboard — Aggregated real-time statistics for the dashboard
GET /api/dashboard?days=30 — Longer collection/revenue trends
"""
from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Collection, Farmer, Payment, MilkRejection, Branch
from backend.auth import get_identity

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Return aggregated dashboard data computed from the database."""
    today = date.today()
    days = request.args.get('days', 14, type=int)
    if days not in (14, 30):
        days = 14

    user = get_identity()
    user_branch_id = user.get('branchId')
    scoped = user.get('role') not in ('SUPER_ADMIN', 'HEAD_OFFICE') and user_branch_id

    def _scoped_query(model, *conditions):
        """Apply user branch isolation to a query if the role requires it."""
        query = model.query.filter(*conditions) if conditions else model.query
        if scoped:
            query = query.filter(getattr(model, 'branch_id') == user_branch_id)
        return query

    # ── Today's collections (KPIs) ──
    today_colls = _scoped_query(Collection, Collection.date == today).all()
    today_qty = round(sum(c.quantity or 0 for c in today_colls), 2)
    today_amount = round(sum(c.amount or 0 for c in today_colls), 2)
    today_cow = round(sum(c.quantity or 0 for c in today_colls if c.milk_type == 'COW'), 2)
    today_buffalo = round(sum(c.quantity or 0 for c in today_colls if c.milk_type == 'BUFFALO'), 2)
    today_mixed = round(sum(c.quantity or 0 for c in today_colls if c.milk_type == 'MIXED'), 2)

    fats = [c.fat for c in today_colls if c.fat]
    snfs = [c.snf for c in today_colls if c.snf]
    avg_fat = round(sum(fats) / len(fats), 1) if fats else None
    avg_snf = round(sum(snfs) / len(snfs), 1) if snfs else None

    # ── Farmers, payments, rejections ──
    farmer_query = Farmer.query
    payment_query = Payment.query
    if scoped:
        farmer_query = farmer_query.filter_by(branch_id=user_branch_id)
        payment_query = payment_query.filter_by(branch_id=user_branch_id)

    active_farmers = farmer_query.filter_by(status='ACTIVE').count()
    pending_payments = payment_query.filter(
        Payment.status.in_(['PENDING', 'APPROVED'])
    ).all()
    pending_amount = round(sum(p.total_amount or 0 for p in pending_payments), 2)
    rejected_today = _scoped_query(MilkRejection, MilkRejection.date == today).count()

    # ── Collection progress: today vs 7-day daily average target ──
    week_start = today - timedelta(days=7)
    week_colls = _scoped_query(
        Collection,
        Collection.date >= week_start,
        Collection.date < today,
    ).all()
    week_total = sum(c.quantity or 0 for c in week_colls)
    target = round(week_total / 7 / 10) * 10 if week_total else 0
    progress_pct = round(today_qty / target * 100, 1) if target else 0

    # ── Collection & revenue trends ──
    day_list = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    trend_colls = _scoped_query(
        Collection,
        Collection.date >= day_list[0],
        Collection.date <= today,
    ).all()
    qty_by_day, amt_by_day = {}, {}
    for c in trend_colls:
        key = c.date.isoformat()
        qty_by_day[key] = qty_by_day.get(key, 0) + (c.quantity or 0)
        amt_by_day[key] = amt_by_day.get(key, 0) + (c.amount or 0)

    collection_trend = [round(qty_by_day.get(d.isoformat(), 0), 2) for d in day_list]
    revenue_trend = [round(amt_by_day.get(d.isoformat(), 0), 2) for d in day_list]

    # ── Revenue growth: last 7 days vs previous 7 days ──
    prev_start = today - timedelta(days=14)
    prev_amount = sum(
        c.amount or 0
        for c in _scoped_query(
            Collection,
            Collection.date >= prev_start,
            Collection.date < week_start,
        ).all()
    )
    recent_amount = sum(c.amount or 0 for c in week_colls)
    revenue_growth = round((recent_amount - prev_amount) / prev_amount * 100, 1) \
        if prev_amount else None

    # ── Branch performance (last 30 days) — scoped for branch managers ──
    month_start = today - timedelta(days=30)
    branch_data = []
    branch_query = Branch.query.filter_by(status='ACTIVE').order_by(Branch.name)
    if scoped:
        branch_query = branch_query.filter_by(id=user_branch_id)
    for b in branch_query.all():
        b_colls = Collection.query.filter(
            Collection.branch_id == b.id,
            Collection.date >= month_start,
            Collection.date <= today,
        ).all()
        b_qty = sum(c.quantity or 0 for c in b_colls)
        b_amt = sum(c.amount or 0 for c in b_colls)
        b_farmers = Farmer.query.filter_by(branch_id=b.id, status='ACTIVE').count()
        branch_data.append({
            'code': b.code,
            'name': b.name,
            'farmerCount': b_farmers,
            'collection': round(b_qty, 2),
            'revenue': round(b_amt, 2),
            'efficiency': round(b_amt / b_qty, 2) if b_qty else None,  # ₹ per litre
        })

    # ── Today's entries (most recent first) ──
    recent_entries = sorted(
        today_colls, key=lambda c: c.created_at or c.id, reverse=True
    )[:8]
    today_entries = [{
        'receiptNo': c.receipt_no,
        'farmerName': c.farmer.name if c.farmer else '-',
        'quantity': c.quantity,
        'shift': c.shift,
        'time': c.created_at.strftime('%H:%M') if c.created_at else '',
    } for c in recent_entries]

    # ── Pending payments list ──
    pending_items = [{
        'payCode': p.pay_code,
        'farmerName': p.farmer.name if p.farmer else '-',
        'amount': p.total_amount,
        'status': p.status,
    } for p in sorted(
        pending_payments, key=lambda p: p.created_at or p.id, reverse=True
    )[:5]]

    # ── New farmers (last 7 days) ──
    new_farmers = [{
        'name': f.name,
        'farmerCode': f.farmer_code,
        'joinedAt': f.joined_at.isoformat() if f.joined_at else None,
    } for f in farmer_query.filter(Farmer.joined_at >= week_start)
        .order_by(Farmer.joined_at.desc()).limit(5).all()]

    # ── Top farmers (last 30 days by quantity) ──
    top_query = db.session.query(
        Collection.farmer_id,
        db.func.sum(Collection.quantity).label('qty'),
        db.func.sum(Collection.amount).label('amt'),
    ).filter(
        Collection.date >= month_start,
        Collection.date <= today,
    )
    if scoped:
        top_query = top_query.filter(Collection.branch_id == user_branch_id)
    top_rows = top_query.group_by(Collection.farmer_id) \
        .order_by(db.func.sum(Collection.quantity).desc()).limit(5).all()

    top_farmers = []
    for row in top_rows:
        f = Farmer.query.get(row.farmer_id)
        top_farmers.append({
            'name': f.name if f else '-',
            'farmerCode': f.farmer_code if f else '-',
            'quantity': round(row.qty or 0, 2),
            'amount': round(row.amt or 0, 2),
        })

    # ── System health ──
    db_ok = True
    try:
        with db.engine.connect():
            pass
    except Exception:
        db_ok = False

    return jsonify({
        'kpis': {
            'todayCollection': today_qty,
            'todayCow': today_cow,
            'todayBuffalo': today_buffalo,
            'todayMixed': today_mixed,
            'revenue': today_amount,
            'activeFarmers': active_farmers,
            'avgFat': avg_fat,
            'avgSnf': avg_snf,
            'pendingPayments': pending_amount,
            'rejectedToday': rejected_today,
            'efficiency': progress_pct,
        },
        'collectionProgress': {
            'target': target,
            'collected': today_qty,
            'remaining': round(max(target - today_qty, 0), 2),
            'percent': progress_pct,
        },
        'collectionTrend': {
            'labels': [d.strftime('%d %b') for d in day_list],
            'values': collection_trend,
        },
        'revenueTrend': {
            'labels': [d.strftime('%d %b') for d in day_list],
            'values': revenue_trend,
        },
        'revenueGrowth': revenue_growth,
        'branches': branch_data,
        'todayEntries': today_entries,
        'todayEntryCount': len(today_colls),
        'pendingPayments': pending_items,
        'newFarmers': new_farmers,
        'topFarmers': top_farmers,
        'health': {
            'database': 'Connected' if db_ok else 'Disconnected',
            'api': 'Running',
            'auth': 'Active',
            'storage': 'OK',
        },
    })
