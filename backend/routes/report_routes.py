"""
Smart Dairy ERP — Report Routes

GET /api/reports?type=collection&from=&to=&branchId=
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Collection, Farmer, Payment, MilkRejection, QualityTest, Branch

report_bp = Blueprint('reports', __name__)


@report_bp.route('/api/reports', methods=['GET'])
@jwt_required()
def get_report():
    """Generate reports based on type and filters."""
    report_type = request.args.get('type', 'collection')
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')
    branch_id = request.args.get('branchId', type=int)
    farmer_id = request.args.get('farmerId', type=int)

    # Parse dates
    start = None
    end = None
    try:
        if from_date:
            start = datetime.strptime(from_date, '%Y-%m-%d').date()
        if to_date:
            end = datetime.strptime(to_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass

    if not start:
        end = date.today()
        start = end - timedelta(days=30)

    if report_type == 'collection':
        return _collection_report(start, end, branch_id)
    elif report_type == 'payment':
        return _payment_report(start, end, branch_id)
    elif report_type == 'farmer':
        return _farmer_ledger(farmer_id, start, end)
    elif report_type == 'quality':
        return _quality_report(start, end, branch_id)
    elif report_type == 'rejection':
        return _rejection_report(start, end, branch_id)
    elif report_type == 'branch':
        return _branch_report(start, end)
    else:
        return jsonify({'error': 'Invalid report type'}), 400


def _collection_report(start, end, branch_id):
    query = Collection.query.filter(Collection.date.between(start, end))
    if branch_id:
        query = query.filter_by(branch_id=branch_id)

    collections = query.all()

    total_qty = sum(c.quantity for c in collections)
    total_amount = sum(c.amount for c in collections)
    morning = sum(c.quantity for c in collections if c.shift == 'MORNING')
    evening = sum(c.quantity for c in collections if c.shift == 'EVENING')
    avg_fat = sum(c.fat for c in collections if c.fat) / max(len([c for c in collections if c.fat]), 1)
    avg_snf = sum(c.snf for c in collections if c.snf) / max(len([c for c in collections if c.snf]), 1)

    return jsonify({
        'type': 'collection',
        'period': {'from': start.isoformat(), 'to': end.isoformat()},
        'summary': {
            'totalQuantity': round(total_qty, 2),
            'totalAmount': round(total_amount, 2),
            'morningQuantity': round(morning, 2),
            'eveningQuantity': round(evening, 2),
            'collectionCount': len(collections),
            'avgFat': round(avg_fat, 2),
            'avgSnf': round(avg_snf, 2),
        },
        'collections': [c.to_dict() for c in collections[:100]],
    })


def _payment_report(start, end, branch_id):
    query = Payment.query.filter(Payment.created_at.between(
        datetime.combine(start, datetime.min.time()),
        datetime.combine(end, datetime.max.time())
    ))
    if branch_id:
        query = query.filter_by(branch_id=branch_id)

    payments = query.all()
    total_paid = sum(p.total_amount for p in payments if p.status == 'PAID')
    total_pending = sum(p.total_amount for p in payments if p.status in ('PENDING', 'APPROVED'))

    return jsonify({
        'type': 'payment',
        'period': {'from': start.isoformat(), 'to': end.isoformat()},
        'summary': {
            'totalPaid': round(total_paid, 2),
            'totalPending': round(total_pending, 2),
            'paymentCount': len(payments),
        },
        'payments': [p.to_dict() for p in payments[:100]],
    })


def _farmer_ledger(farmer_id, start, end):
    if not farmer_id:
        return jsonify({'error': 'Farmer ID is required for farmer ledger'}), 400

    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    collections = Collection.query.filter(
        Collection.farmer_id == farmer_id,
        Collection.date.between(start, end)
    ).order_by(Collection.date.desc()).all()

    total_qty = sum(c.quantity for c in collections)
    total_amount = sum(c.amount for c in collections)

    return jsonify({
        'type': 'farmer',
        'farmer': farmer.to_dict(),
        'period': {'from': start.isoformat(), 'to': end.isoformat()},
        'summary': {
            'totalQuantity': round(total_qty, 2),
            'totalAmount': round(total_amount, 2),
            'collectionCount': len(collections),
        },
        'collections': [c.to_dict() for c in collections],
    })


def _quality_report(start, end, branch_id):
    query = QualityTest.query.filter(QualityTest.date.between(start, end))
    if branch_id:
        query = query.filter_by(branch_id=branch_id)

    tests = query.all()
    passed = sum(1 for t in tests if t.overall_result == 'PASS')
    borderline = sum(1 for t in tests if t.overall_result == 'BORDERLINE')
    failed = sum(1 for t in tests if t.overall_result == 'FAIL')

    return jsonify({
        'type': 'quality',
        'period': {'from': start.isoformat(), 'to': end.isoformat()},
        'summary': {
            'totalTests': len(tests),
            'passed': passed,
            'borderline': borderline,
            'failed': failed,
            'passRate': round(passed / max(len(tests), 1) * 100, 1),
        },
    })


def _rejection_report(start, end, branch_id):
    query = MilkRejection.query.filter(MilkRejection.date.between(start, end))
    if branch_id:
        query = query.filter_by(branch_id=branch_id)

    rejections = query.all()
    total_qty = sum(r.quantity for r in rejections)

    # Group by reason
    reasons = {}
    for r in rejections:
        reasons[r.reason] = reasons.get(r.reason, 0) + r.quantity

    return jsonify({
        'type': 'rejection',
        'period': {'from': start.isoformat(), 'to': end.isoformat()},
        'summary': {
            'totalQuantity': round(total_qty, 2),
            'totalEvents': len(rejections),
            'byReason': reasons,
        },
    })


def _branch_report(start, end):
    branches = Branch.query.filter_by(status='ACTIVE').all()
    branch_data = []

    for branch in branches:
        collections = Collection.query.filter(
            Collection.branch_id == branch.id,
            Collection.date.between(start, end),
        ).all()

        total_qty = sum(c.quantity for c in collections)
        total_amt = sum(c.amount for c in collections)
        farmer_count = Farmer.query.filter_by(branch_id=branch.id, status='ACTIVE').count()

        branch_data.append({
            'branchId': branch.id,
            'branchName': branch.name,
            'branchCode': branch.code,
            'farmerCount': farmer_count,
            'totalQuantity': round(total_qty, 2),
            'totalAmount': round(total_amt, 2),
            'collectionCount': len(collections),
        })

    return jsonify({
        'type': 'branch',
        'period': {'from': start.isoformat(), 'to': end.isoformat()},
        'branches': branch_data,
    })
