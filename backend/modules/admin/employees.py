"""
Smart Dairy ERP — Employee Routes

GET    /api/employees              — List employees
POST   /api/employees              — Add employee
PATCH  /api/employees/<id>         — Update employee
DELETE /api/employees/<id>         — Delete employee
GET    /api/employees/attendance   — List attendance (filterable)
POST   /api/employees/attendance   — Mark attendance
GET    /api/employees/<id>/attendance — Attendance for one employee
"""
from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Employee, EmployeeAttendance
from backend.audit import log_audit
from backend.auth import get_identity, get_branch_scope, role_required

employee_bp = Blueprint('employees', __name__)

VALID_ATTENDANCE = ('PRESENT', 'ABSENT', 'LEAVE', 'HALF_DAY')


@employee_bp.route('/api/employees', methods=['GET'])
@jwt_required()
def get_employees():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    branch_id = request.args.get('branchId', type=int)

    query = Employee.query.order_by(Employee.name)
    # Branch isolation: Branch Managers are forced to their own branch
    # (any client-supplied branchId is ignored); global roles may filter.
    forced = get_branch_scope()
    if forced:
        query = query.filter_by(branch_id=forced)
    elif branch_id:
        query = query.filter_by(branch_id=branch_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    employees = pagination.items

    return jsonify({
        'employees': [e.to_dict() for e in employees],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'summary': {
            'total': pagination.total,
            'active': sum(1 for e in employees if e.status == 'ACTIVE'),
            'totalSalary': round(sum(e.salary or 0 for e in employees), 2),
        },
    })


@employee_bp.route('/api/employees', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def create_employee():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Employee name is required'}), 400

    last = Employee.query.order_by(Employee.id.desc()).first()
    seq = (last.id + 1) if last else 1
    employee = Employee(
        code=data.get('code') or f'EMP-{seq:04d}',
        name=name,
        role=data.get('role') or 'OPERATOR',
        branch_id=data.get('branchId') or data.get('branch_id'),
        mobile=data.get('mobile'),
        email=data.get('email'),
        address=data.get('address'),
        salary=data.get('salary'),
        status=data.get('status', 'ACTIVE'),
        joined_at=date.today(),
    )
    db.session.add(employee)
    db.session.flush()
    log_audit('CREATE', 'Employee', employee.code, detail=f'Employee {employee.name} added')
    db.session.commit()
    return jsonify({'employee': employee.to_dict(), 'message': 'Employee created'}), 201


@employee_bp.route('/api/employees/<int:employee_id>', methods=['PATCH'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def update_employee(employee_id):
    """Update employee details (role assignment, salary, status, etc.)."""
    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    field_map = {
        'name': 'name', 'role': 'role', 'mobile': 'mobile', 'email': 'email',
        'address': 'address', 'salary': 'salary', 'status': 'status',
        'branchId': 'branch_id',
    }
    for key, attr in field_map.items():
        if key in data:
            setattr(employee, attr, data[key])

    log_audit('UPDATE', 'Employee', employee.code, detail=f'Employee {employee.name} updated')
    db.session.commit()
    return jsonify({'employee': employee.to_dict(), 'message': 'Employee updated successfully'})


@employee_bp.route('/api/employees/<int:employee_id>', methods=['DELETE'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    code = employee.code
    db.session.delete(employee)
    log_audit('DELETE', 'Employee', code, detail=f'Employee {code} deleted')
    db.session.commit()
    return jsonify({'message': f'Employee {code} deleted successfully'})


# ── Attendance ──

@employee_bp.route('/api/employees/attendance', methods=['GET'])
@jwt_required()
def get_attendance():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_str = request.args.get('date', '')
    employee_id = request.args.get('employeeId', type=int)

    query = EmployeeAttendance.query.order_by(EmployeeAttendance.date.desc())
    if date_str:
        try:
            query = query.filter_by(date=date.fromisoformat(date_str[:10]))
        except ValueError:
            pass
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    # Branch isolation: Branch Managers only see attendance of own-branch employees
    forced = get_branch_scope()
    if forced:
        query = query.join(Employee, EmployeeAttendance.employee_id == Employee.id) \
                     .filter(Employee.branch_id == forced)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'attendance': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@employee_bp.route('/api/employees/<int:employee_id>/attendance', methods=['GET'])
@jwt_required()
def employee_attendance(employee_id):
    """Attendance for a single employee (last 60 days)."""
    employee = Employee.query.get_or_404(employee_id)
    # Branch isolation: Branch Managers can only view own-branch employees
    forced = get_branch_scope()
    if forced and employee.branch_id != forced:
        return jsonify({'error': 'Access denied. Employee belongs to another branch.'}), 403
    records = EmployeeAttendance.query.filter_by(employee_id=employee.id) \
        .order_by(EmployeeAttendance.date.desc()).limit(60).all()
    present = sum(1 for r in records if r.status == 'PRESENT')
    absent = sum(1 for r in records if r.status == 'ABSENT')
    leave = sum(1 for r in records if r.status == 'LEAVE')
    return jsonify({
        'employee': employee.to_dict(),
        'records': [r.to_dict() for r in records],
        'summary': {'present': present, 'absent': absent, 'leave': leave},
    })


@employee_bp.route('/api/employees/attendance', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def mark_attendance():
    """Mark daily attendance for an employee (upserts by employee+date)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    employee_id = data.get('employeeId')
    status = (data.get('status') or '').upper()
    if not employee_id:
        return jsonify({'error': 'Employee is required'}), 400
    if status not in VALID_ATTENDANCE:
        return jsonify({'error': f'Status must be one of: {VALID_ATTENDANCE}'}), 400
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    att_date = date.today()
    if data.get('date'):
        try:
            att_date = date.fromisoformat(data['date'][:10])
        except ValueError:
            pass

    record = EmployeeAttendance.query.filter_by(employee_id=employee_id, date=att_date).first()
    if record:
        record.status = status
        record.shift = data.get('shift', record.shift)
        record.notes = data.get('notes', record.notes)
        created = False
    else:
        record = EmployeeAttendance(
            employee_id=employee_id, date=att_date, status=status,
            shift=data.get('shift', ''), notes=data.get('notes', ''),
            created_by=get_identity().get('uid'),
        )
        db.session.add(record)
        created = True

    log_audit('CREATE' if created else 'UPDATE', 'EmployeeAttendance', employee.code,
              detail=f'{employee.name} marked {status} on {att_date}')
    db.session.commit()
    return jsonify({'attendance': record.to_dict(), 'message': f'{employee.name} marked {status}'}), 201
