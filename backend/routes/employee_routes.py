"""
Smart Dairy ERP — Employee Routes
"""
from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Employee

employee_bp = Blueprint('employees', __name__)


@employee_bp.route('/api/employees', methods=['GET'])
@jwt_required()
def get_employees():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    branch_id = request.args.get('branchId', type=int)

    query = Employee.query.order_by(Employee.name)
    if branch_id:
        query = query.filter_by(branch_id=branch_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'employees': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@employee_bp.route('/api/employees', methods=['POST'])
@jwt_required()
def create_employee():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    employee = Employee(
        code=data.get('code'),
        name=data.get('name'),
        role=data.get('role'),
        branch_id=data.get('branchId'),
        mobile=data.get('mobile'),
        email=data.get('email'),
        address=data.get('address'),
        salary=data.get('salary'),
        status=data.get('status', 'ACTIVE'),
        joined_at=date.today(),
    )
    db.session.add(employee)
    db.session.commit()
    return jsonify({'employee': employee.to_dict(), 'message': 'Employee created'}), 201
