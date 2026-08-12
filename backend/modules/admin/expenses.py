"""
Smart Dairy ERP — Expense Routes

GET    /api/expenses            — List expenses (branch-scoped, filterable)
POST   /api/expenses            — Add expense
PATCH  /api/expenses/<id>       — Update expense (Head Office)
DELETE /api/expenses/<id>       — Delete expense (Head Office)
"""
from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Expense
from backend.auth import role_required, get_identity
from backend.audit import log_audit

expense_bp = Blueprint('expenses', __name__)

VALID_CATEGORIES = [
    'FEED', 'LABOUR', 'TRANSPORT', 'MAINTENANCE',
    'ELECTRICITY', 'ADMIN', 'PROCUREMENT', 'OTHER',
]


@expense_bp.route('/api/expenses', methods=['GET'])
@jwt_required()
def get_expenses():
    """List expenses with filtering (respects user's branch scope)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '').strip()
    branch_id = request.args.get('branchId', type=int)
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')

    query = Expense.query

    user = get_identity()
    user_branch_id = user.get('branchId')
    if user.get('role') not in ('ADMIN',) and user_branch_id:
        query = query.filter_by(branch_id=user_branch_id)
    elif branch_id:
        query = query.filter_by(branch_id=branch_id)

    if category:
        query = query.filter_by(category=category.upper())
    if from_date:
        try:
            query = query.filter(Expense.expense_date >= date.fromisoformat(from_date[:10]))
        except ValueError:
            pass
    if to_date:
        try:
            query = query.filter(Expense.expense_date <= date.fromisoformat(to_date[:10]))
        except ValueError:
            pass

    query = query.order_by(Expense.expense_date.desc(), Expense.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Summary
    scoped = Expense.query
    if user.get('role') not in ('ADMIN',) and user_branch_id:
        scoped = scoped.filter_by(branch_id=user_branch_id)
    all_expenses = scoped.all()
    by_category = {}
    total = 0.0
    for e in all_expenses:
        total += e.amount or 0
        by_category[e.category] = round(by_category.get(e.category, 0) + (e.amount or 0), 2)

    return jsonify({
        'expenses': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'summary': {
            'totalAmount': round(total, 2),
            'byCategory': by_category,
        },
    })


@expense_bp.route('/api/expenses', methods=['POST'])
@jwt_required()
def create_expense():
    """Add a new expense. Branch managers may add expenses to their own branch."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    amount = data.get('amount')
    if amount is None or float(amount) <= 0:
        return jsonify({'error': 'Valid amount is required'}), 400

    category = (data.get('category') or 'OTHER').upper()
    if category not in VALID_CATEGORIES:
        return jsonify({'error': f'Category must be one of: {", ".join(VALID_CATEGORIES)}'}), 400

    user = get_identity()
    branch_id = data.get('branchId')
    if user.get('role') not in ('ADMIN',):
        branch_id = user.get('branchId')  # branch managers: own branch only
        if not branch_id:
            return jsonify({'error': 'No branch assigned to this user. Contact Head Office.'}), 400

    last = Expense.query.order_by(Expense.id.desc()).first()
    seq = (last.id + 1) if last else 1

    expense = Expense(
        code=f'EXP{seq:06d}',
        branch_id=branch_id,
        category=category,
        description=data.get('description', ''),
        amount=float(amount),
        expense_date=date.fromisoformat(data.get('expenseDate', '')[:10]) if data.get('expenseDate') else date.today(),
        created_by=user.get('uid'),
    )
    db.session.add(expense)
    db.session.flush()
    log_audit('CREATE', 'Expense', expense.code,
              detail=f'Added expense of {expense.amount} ({category})')
    db.session.commit()

    return jsonify({'expense': expense.to_dict(), 'message': 'Expense added successfully'}), 201


@expense_bp.route('/api/expenses/<int:expense_id>', methods=['PATCH'])
@jwt_required()
@role_required('ADMIN')
def update_expense(expense_id):
    """Update an expense (Head Office only)."""
    expense = Expense.query.get_or_404(expense_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    old_amount = expense.amount
    if 'amount' in data:
        if float(data['amount']) <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        expense.amount = float(data['amount'])
    if 'category' in data:
        cat = data['category'].upper()
        if cat not in VALID_CATEGORIES:
            return jsonify({'error': f'Invalid category: {cat}'}), 400
        expense.category = cat
    if 'description' in data:
        expense.description = data['description']
    if 'expenseDate' in data:
        try:
            expense.expense_date = date.fromisoformat(data['expenseDate'][:10])
        except ValueError:
            pass
    if 'branchId' in data:
        expense.branch_id = data['branchId']

    log_audit('UPDATE', 'Expense', expense.code,
              detail=f'Updated expense from {old_amount} to {expense.amount}')
    db.session.commit()
    return jsonify({'expense': expense.to_dict(), 'message': 'Expense updated successfully'})


@expense_bp.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
@role_required('ADMIN')
def delete_expense(expense_id):
    """Delete an expense (Head Office only)."""
    expense = Expense.query.get_or_404(expense_id)
    code = expense.code
    db.session.delete(expense)
    log_audit('DELETE', 'Expense', code, detail=f'Deleted expense {code}')
    db.session.commit()
    return jsonify({'message': f'Expense {code} deleted successfully'})
