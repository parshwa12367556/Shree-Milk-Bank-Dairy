"""
Smart Dairy ERP — SQLAlchemy Database Models

Defines all database tables as ORM models.
"""
from datetime import datetime, date
from backend.app import db


class User(db.Model):
    """System user accounts with role-based access."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='OPERATOR')
    # Roles: SUPER_ADMIN, HEAD_OFFICE, BRANCH_MANAGER, OPERATOR, ACCOUNTANT
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    status = db.Column(db.String(20), default='ACTIVE')
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    branch = db.relationship('Branch', backref='users', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'role': self.role,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'phone': self.phone,
            'email': self.email,
            'status': self.status,
        }


class Branch(db.Model):
    """Dairy branches/collection centers."""
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    manager_name = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    village = db.Column(db.String(100))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    farmers = db.relationship('Farmer', backref='branch', lazy='dynamic')
    collections = db.relationship('Collection', backref='branch', lazy='dynamic')

    def to_dict(self):
        farmer_count = self.farmers.count() if hasattr(self, 'farmers') else 0
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'managerName': self.manager_name,
            'phone': self.phone,
            'address': self.address,
            'village': self.village,
            'district': self.district,
            'state': self.state,
            'status': self.status,
            'farmerCount': farmer_count,
        }


class Farmer(db.Model):
    """Registered milk producers/farmers."""
    __tablename__ = 'farmers'

    id = db.Column(db.Integer, primary_key=True)
    farmer_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    father_name = db.Column(db.String(200))
    mobile = db.Column(db.String(15), nullable=False)
    alt_mobile = db.Column(db.String(15))
    email = db.Column(db.String(120))
    aadhaar = db.Column(db.String(12))
    pan = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    occupation = db.Column(db.String(100))
    education = db.Column(db.String(100))

    # Address
    address = db.Column(db.Text)
    village = db.Column(db.String(100))
    taluka = db.Column(db.String(100))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(6))
    landmark = db.Column(db.String(200))

    # Livestock
    milk_type = db.Column(db.String(20), nullable=False)  # COW, BUFFALO, MIXED
    cow_count = db.Column(db.Integer, default=0)
    buffalo_count = db.Column(db.Integer, default=0)
    breed = db.Column(db.String(100))
    preferred_shift = db.Column(db.String(20))  # MORNING, EVENING

    # Management
    remarks = db.Column(db.Text)
    qr_code = db.Column(db.Text)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE, BLOCKED
    status_reason = db.Column(db.String(200))
    notification_sms = db.Column(db.Boolean, default=True)
    notification_whatsapp = db.Column(db.Boolean, default=False)
    notification_email = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    joined_at = db.Column(db.Date, default=date.today)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bank_detail = db.relationship('BankDetail', uselist=False, backref='farmer')
    collections = db.relationship('Collection', backref='farmer', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'farmerCode': self.farmer_code,
            'name': self.name,
            'fatherName': self.father_name,
            'mobile': self.mobile,
            'altMobile': self.alt_mobile,
            'email': self.email,
            'aadhaar': self.aadhaar,
            'village': self.village,
            'taluka': self.taluka,
            'district': self.district,
            'state': self.state,
            'milkType': self.milk_type,
            'cowCount': self.cow_count,
            'buffaloCount': self.buffalo_count,
            'breed': self.breed,
            'preferredShift': self.preferred_shift,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'status': self.status,
            'joinedAt': self.joined_at.isoformat() if self.joined_at else None,
            'bankDetail': self.bank_detail.to_dict() if self.bank_detail else None,
        }


class BankDetail(db.Model):
    """Farmer bank account details."""
    __tablename__ = 'bank_details'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), unique=True, nullable=False)
    account_holder = db.Column(db.String(200))
    bank_name = db.Column(db.String(200))
    branch_name = db.Column(db.String(200))
    account_number = db.Column(db.String(30))
    ifsc = db.Column(db.String(11))
    upi = db.Column(db.String(100))
    passbook_image = db.Column(db.String(500))

    def to_dict(self):
        return {
            'id': self.id,
            'accountHolder': self.account_holder,
            'bankName': self.bank_name,
            'branchName': self.branch_name,
            'accountNumber': self.account_number,
            'ifsc': self.ifsc,
            'upi': self.upi,
        }


class RateMaster(db.Model):
    """Versioned milk pricing rates."""
    __tablename__ = 'rate_masters'

    id = db.Column(db.Integer, primary_key=True)
    milk_type = db.Column(db.String(20), nullable=False)  # COW, BUFFALO
    fat_rate = db.Column(db.Float, nullable=False)
    snf_rate = db.Column(db.Float, nullable=False)
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)
    version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'milkType': self.milk_type,
            'fatRate': self.fat_rate,
            'snfRate': self.snf_rate,
            'effectiveFrom': self.effective_from.isoformat() if self.effective_from else None,
            'effectiveTo': self.effective_to.isoformat() if self.effective_to else None,
            'version': f'v{self.version}',
            'status': self.status,
        }


class Collection(db.Model):
    """Daily milk collection records (immutable after creation)."""
    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rate_master_id = db.Column(db.Integer, db.ForeignKey('rate_masters.id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)

    date = db.Column(db.Date, nullable=False, default=date.today)
    shift = db.Column(db.String(20), nullable=False)  # MORNING, EVENING
    milk_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float)
    snf = db.Column(db.Float)
    clr = db.Column(db.Float)
    temperature = db.Column(db.Float)
    density = db.Column(db.Float)
    water = db.Column(db.Float)
    rate_per_liter = db.Column(db.Float)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='ACCEPTED')  # ACCEPTED, REJECTED, CORRECTED
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quality_tests = db.relationship('QualityTest', backref='collection', lazy='dynamic')
    rejections = db.relationship('MilkRejection', backref='collection', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'receiptNo': self.receipt_no,
            'farmerId': self.farmer_id,
            'farmerName': self.farmer.name if self.farmer else None,
            'farmerCode': self.farmer.farmer_code if self.farmer else None,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'operatorId': self.operator_id,
            'date': self.date.isoformat() if self.date else None,
            'shift': self.shift,
            'milkType': self.milk_type,
            'quantity': self.quantity,
            'fat': self.fat,
            'snf': self.snf,
            'clr': self.clr,
            'temperature': self.temperature,
            'water': self.water,
            'ratePerLiter': self.rate_per_liter,
            'amount': self.amount,
            'status': self.status,
            'remarks': self.remarks,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class Payment(db.Model):
    """Farmer payment records."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    pay_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    total_quantity = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    collection_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, APPROVED, PAID
    paid_at = db.Column(db.DateTime, nullable=True)
    paid_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reference = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    farmer = db.relationship('Farmer', backref='payments', lazy=True)
    collections = db.relationship('Collection', backref='payment', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'payCode': self.pay_code,
            'farmerId': self.farmer_id,
            'farmerName': self.farmer.name if self.farmer else None,
            'farmerCode': self.farmer.farmer_code if self.farmer else None,
            'branchId': self.branch_id,
            'periodStart': self.period_start.isoformat() if self.period_start else None,
            'periodEnd': self.period_end.isoformat() if self.period_end else None,
            'totalQuantity': self.total_quantity,
            'totalAmount': self.total_amount,
            'collectionCount': self.collection_count,
            'status': self.status,
            'paidAt': self.paid_at.isoformat() if self.paid_at else None,
            'reference': self.reference,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class QualityTest(db.Model):
    """Milk quality test records."""
    __tablename__ = 'quality_tests'

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    tested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    shift = db.Column(db.String(20))

    # Test parameters
    fat = db.Column(db.Float)
    snf = db.Column(db.Float)
    clr = db.Column(db.Float)
    density = db.Column(db.Float)
    protein = db.Column(db.Float)
    lactose = db.Column(db.Float)
    water_content = db.Column(db.Float)
    temperature = db.Column(db.Float)
    acidity = db.Column(db.Float)
    mbrt = db.Column(db.Float)
    alcohol_test = db.Column(db.String(20))  # PASS, FAIL
    freezing_point = db.Column(db.Float)

    # Results
    overall_result = db.Column(db.String(20))  # PASS, BORDERLINE, FAIL
    result_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    farmer = db.relationship('Farmer', backref='quality_tests')

    def to_dict(self):
        return {
            'id': self.id,
            'collectionId': self.collection_id,
            'farmerId': self.farmer_id,
            'farmerName': self.farmer.name if self.farmer else None,
            'branchId': self.branch_id,
            'testedBy': self.tested_by,
            'date': self.date.isoformat() if self.date else None,
            'shift': self.shift,
            'fat': self.fat,
            'snf': self.snf,
            'clr': self.clr,
            'density': self.density,
            'protein': self.protein,
            'lactose': self.lactose,
            'waterContent': self.water_content,
            'temperature': self.temperature,
            'acidity': self.acidity,
            'mbrt': self.mbrt,
            'alcoholTest': self.alcohol_test,
            'freezingPoint': self.freezing_point,
            'overallResult': self.overall_result,
            'resultSummary': self.result_summary,
        }


class MilkRejection(db.Model):
    """Records of rejected milk."""
    __tablename__ = 'milk_rejections'

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'), nullable=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    rejected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    shift = db.Column(db.String(20))
    quantity = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    # Reasons: HIGH_WATER, LOW_FAT, SOUR_MILK, HIGH_TEMP, ADULTERATION, OTHER
    other_reason = db.Column(db.String(200))
    fat = db.Column(db.Float)
    snf = db.Column(db.Float)
    clr = db.Column(db.Float)
    temperature = db.Column(db.Float)
    water_content = db.Column(db.Float)
    remark = db.Column(db.Text)
    photo_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='CONFIRMED')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    farmer = db.relationship('Farmer', backref='milk_rejections')

    def to_dict(self):
        return {
            'id': self.id,
            'collectionId': self.collection_id,
            'farmerId': self.farmer_id,
            'farmerName': self.farmer.name if self.farmer else None,
            'farmerCode': self.farmer.farmer_code if self.farmer else None,
            'branchId': self.branch_id,
            'rejectedBy': self.rejected_by,
            'date': self.date.isoformat() if self.date else None,
            'shift': self.shift,
            'quantity': self.quantity,
            'reason': self.reason,
            'otherReason': self.other_reason,
            'fat': self.fat,
            'waterContent': self.water_content,
            'remark': self.remark,
            'status': self.status,
        }


class CollectionCenter(db.Model):
    """Procurement collection centers."""
    __tablename__ = 'collection_centers'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    center_type = db.Column(db.String(30), nullable=False)
    # MAIN, SUB_CENTER, CHILLING_POINT, MOBILE
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    manager_name = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    village = db.Column(db.String(100))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(6))
    capacity = db.Column(db.Float)
    morning_start = db.Column(db.String(5))
    morning_end = db.Column(db.String(5))
    evening_start = db.Column(db.String(5))
    evening_end = db.Column(db.String(5))
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'centerType': self.center_type,
            'branchId': self.branch_id,
            'managerName': self.manager_name,
            'phone': self.phone,
            'village': self.village,
            'district': self.district,
            'capacity': self.capacity,
            'status': self.status,
        }


class CollectionRoute(db.Model):
    """Milk collection routes."""
    __tablename__ = 'collection_routes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    center_id = db.Column(db.Integer, db.ForeignKey('collection_centers.id'), nullable=True)
    distance = db.Column(db.Float)
    estimated_duration = db.Column(db.String(20))
    driver_name = db.Column(db.String(120))
    vehicle_number = db.Column(db.String(20))
    farmer_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'branchId': self.branch_id,
            'centerId': self.center_id,
            'distance': self.distance,
            'driverName': self.driver_name,
            'vehicleNumber': self.vehicle_number,
            'farmerCount': self.farmer_count,
            'status': self.status,
        }


class ChillingCenter(db.Model):
    """Chilling/cooling centers for milk storage."""
    __tablename__ = 'chilling_centers'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    tank_count = db.Column(db.Integer, default=0)
    total_capacity = db.Column(db.Float)
    current_stock = db.Column(db.Float, default=0)
    temperature = db.Column(db.Float)
    has_generator = db.Column(db.Boolean, default=False)
    generator_capacity = db.Column(db.Float)
    address = db.Column(db.Text)
    phone = db.Column(db.String(15))
    incharge_name = db.Column(db.String(120))
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'branchId': self.branch_id,
            'tankCount': self.tank_count,
            'totalCapacity': self.total_capacity,
            'currentStock': self.current_stock,
            'temperature': self.temperature,
            'hasGenerator': self.has_generator,
            'phone': self.phone,
            'inchargeName': self.incharge_name,
            'status': self.status,
        }


class InventoryItem(db.Model):
    """Inventory/stock items."""
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    stock = db.Column(db.Float, default=0)
    unit = db.Column(db.String(30))
    min_stock = db.Column(db.Float, default=0)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    status = db.Column(db.String(20), default='IN_STOCK')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category,
            'stock': self.stock,
            'unit': self.unit,
            'minStock': self.min_stock,
            'status': 'Low Stock' if self.stock <= self.min_stock else 'In Stock',
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }


class Employee(db.Model):
    """Employee records."""
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    # OPERATOR, ACCOUNTANT, BRANCH_MANAGER, DRIVER, ADMIN
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    branch = db.relationship('Branch', backref='employees', lazy=True)
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    salary = db.Column(db.Float)
    status = db.Column(db.String(20), default='ACTIVE')
    joined_at = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'role': self.role,
            'branchId': self.branch_id,
            'branchName': self.branch.name if hasattr(self, 'branch') and self.branch else None,
            'mobile': self.mobile,
            'email': self.email,
            'status': self.status,
            'joinedAt': self.joined_at.isoformat() if self.joined_at else None,
        }


class Vehicle(db.Model):
    """Vehicle registry."""
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    type = db.Column(db.String(30), nullable=False)  # TANKER, PICKUP, MINI_VAN
    driver_name = db.Column(db.String(120))
    capacity = db.Column(db.Float)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    last_service_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, MAINTENANCE, INACTIVE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicleNumber': self.vehicle_number,
            'type': self.type,
            'driverName': self.driver_name,
            'capacity': self.capacity,
            'branchId': self.branch_id,
            'lastServiceDate': self.last_service_date.isoformat() if self.last_service_date else None,
            'status': self.status,
        }


class AuditLog(db.Model):
    """System audit trail for all CRUD operations."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80))
    action = db.Column(db.String(50), nullable=False)
    # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT
    entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(50))
    field_name = db.Column(db.String(100))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'username': self.username,
            'action': self.action,
            'entity': self.entity,
            'entityId': self.entity_id,
            'detail': self.detail or f'{self.action} on {self.entity} {self.entity_id}',
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    """System notifications for users."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    type = db.Column(db.String(30), nullable=False)
    # payment, collection, quality, system, farmer
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    link = db.Column(db.String(200))
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'read': self.read,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }
