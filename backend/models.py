"""
Smart Dairy ERP — SQLAlchemy Database Models

Defines all database tables as ORM models.
"""
from datetime import datetime, date, timezone

def utcnow():
    return datetime.now(timezone.utc)
from backend.app import db


class _DeclarativeModel(db.Model):
    """Shared declarative base for all ORM models.

    SQLAlchemy generates each model's ``__init__`` dynamically from its
    columns; static type checkers (Pyrefly/Pyright) cannot see that dynamic
    constructor and treat the class as accepting only ``object.__init__`` —
    producing false "Unexpected keyword argument" errors on every
    ``Model(**kwargs)`` call. Declaring an explicit ``**kwargs`` constructor
    here keeps runtime behavior identical (SQLAlchemy still rejects unknown
    columns at runtime) while making the column-keyword pattern visible to
    type checkers project-wide.
    """
    __abstract__ = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class User(_DeclarativeModel):
    """System user accounts with role-based access."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    # Canonical login identifier (ADMIN001, BR01OP001, BR01001...). Unique
    # per account — this is what users type on the common login screen.
    login_id = db.Column(db.String(80), unique=True, nullable=False, index=True)
    # Legacy username kept for backward compatibility (branch code, farmer
    # code, 'admin') — login_id is the canonical identifier.
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='BRANCH_OPERATOR')
    # Roles: ADMIN, BRANCH_OPERATOR, FARMER
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True, index=True)
    # Farmers get a login account linked to their Farmer record (role=FARMER).
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=True, index=True)
    phone = db.Column(db.String(15), index=True)
    email = db.Column(db.String(120), index=True)
    status = db.Column(db.String(20), default='ACTIVE', index=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    # Login hardening (first-login enforcement + brute-force protection)
    must_change_password = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    recovery_email = db.Column(db.String(120))
    recovery_mobile = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    branch = db.relationship('Branch', backref='users', lazy=True)
    # Farmer has multiple FKs to users (verified_by, created_by) — pin the
    # relationship to farmer_id explicitly and force the backref to be a
    # single object (otherwise SQLAlchemy infers a one-to-many collection).
    farmer = db.relationship('Farmer', backref=db.backref('user_account', uselist=False),
                             uselist=False, lazy=True, foreign_keys=[farmer_id])

    def to_dict(self):
        return {
            'id': self.id,
            'loginId': self.login_id,
            'username': self.username,
            'name': self.name,
            'role': self.role,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'farmerId': self.farmer_id,
            'farmerCode': self.farmer.farmer_code if self.farmer else None,
            'phone': self.phone,
            'email': self.email,
            'status': self.status,
            'mustChangePassword': bool(self.must_change_password),
            'lastLoginAt': self.last_login_at.isoformat() if self.last_login_at else None,
        }


class Branch(_DeclarativeModel):
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
    created_at = db.Column(db.DateTime, default=utcnow)

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


class Farmer(_DeclarativeModel):
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
    status = db.Column(db.String(20), default='PENDING_VERIFICATION')
    # ACTIVE, PENDING_VERIFICATION, INACTIVE, BLOCKED
    status_reason = db.Column(db.String(200))
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    notification_sms = db.Column(db.Boolean, default=True)
    notification_whatsapp = db.Column(db.Boolean, default=False)
    notification_email = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    joined_at = db.Column(db.Date, default=date.today)

    created_at = db.Column(db.DateTime, default=utcnow)

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


class FarmerLedgerEntry(_DeclarativeModel):
    """
    Farmer passbook / ledger — one row per financial transaction.

    Every milk earning (credit) and every settled payment (debit) writes a
    ledger row, so the farmer passbook is generated from real transactions
    instead of being computed ad-hoc on the frontend.

    entry_type: MILK_EARNING, PAYMENT, ADJUSTMENT, DEDUCTION
    source_type / source_id: link back to the originating record
        (Collection → collection id, Payment → payment id)
    """
    __tablename__ = 'farmer_ledger_entries'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False, index=True)
    entry_type = db.Column(db.String(30), nullable=False)  # MILK_EARNING, PAYMENT, ADJUSTMENT, DEDUCTION
    source_type = db.Column(db.String(30))                 # Collection, Payment, Manual
    source_id = db.Column(db.Integer)
    entry_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    description = db.Column(db.String(255))
    credit_amount = db.Column(db.Float, default=0)   # milk earnings (amount payable to farmer)
    debit_amount = db.Column(db.Float, default=0)    # payments settled to the farmer
    running_balance = db.Column(db.Float, default=0) # credits - debits up to this row
    created_at = db.Column(db.DateTime, default=utcnow)

    farmer = db.relationship('Farmer', backref=db.backref('ledger_entries', lazy='dynamic'),
                             lazy=True)
    branch = db.relationship('Branch', lazy=True)

    # A source record must never produce two ledger rows (idempotent writes).
    __table_args__ = (
        db.UniqueConstraint('farmer_id', 'source_type', 'source_id',
                            name='uq_ledger_farmer_source'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'farmerId': self.farmer_id,
            'branchId': self.branch_id,
            'entryType': self.entry_type,
            'sourceType': self.source_type,
            'sourceId': self.source_id,
            'date': self.entry_date.isoformat() if self.entry_date else None,
            'description': self.description,
            'credit': self.credit_amount,
            'debit': self.debit_amount,
            'balance': self.running_balance,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class BankDetail(_DeclarativeModel):
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
    # Bank verification by Head Office (PENDING / VERIFIED / REJECTED)
    verification_status = db.Column(db.String(20), default='PENDING')
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'accountHolder': self.account_holder,
            'bankName': self.bank_name,
            'branchName': self.branch_name,
            'accountNumber': self.account_number,
            'ifsc': self.ifsc,
            'upi': self.upi,
            'verificationStatus': self.verification_status,
        }


class RateMaster(_DeclarativeModel):
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
    created_at = db.Column(db.DateTime, default=utcnow)

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


class Collection(_DeclarativeModel):
    """Daily milk collection records (immutable after creation)."""
    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False, index=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rate_master_id = db.Column(db.Integer, db.ForeignKey('rate_masters.id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)

    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    collection_time = db.Column(db.Time, nullable=True)
    shift = db.Column(db.String(20), nullable=False, index=True)  # MORNING, EVENING
    milk_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    # Idempotency key — lets the operator retry a save safely (duplicate
    # submissions with the same key are rejected instead of double-recorded).
    idempotency_key = db.Column(db.String(64), nullable=True, index=True)
    fat = db.Column(db.Float)
    snf = db.Column(db.Float)
    clr = db.Column(db.Float)
    temperature = db.Column(db.Float)
    density = db.Column(db.Float)
    water = db.Column(db.Float)
    rate_per_liter = db.Column(db.Float)
    amount = db.Column(db.Float)
    quality_grade = db.Column(db.String(20))  # PASS, BORDERLINE, REJECTED
    status = db.Column(db.String(20), default='ACCEPTED', index=True)  # ACCEPTED, REJECTED, CORRECTED
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

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
            'qualityGrade': self.quality_grade,
            'collectionTime': self.collection_time.isoformat() if self.collection_time else None,
            'status': self.status,
            'remarks': self.remarks,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class Payment(_DeclarativeModel):
    """Farmer payment records."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    pay_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False, index=True)
    period_start = db.Column(db.Date, nullable=False, index=True)
    period_end = db.Column(db.Date, nullable=False, index=True)
    total_quantity = db.Column(db.Float, default=0)
    gross_amount = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)  # net amount (gross - deductions)
    collection_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='PENDING', index=True)  # PENDING, APPROVED, PAID
    payment_method = db.Column(db.String(30), default='BANK_TRANSFER')
    paid_at = db.Column(db.DateTime, nullable=True)
    paid_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reference = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

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
            'grossAmount': self.gross_amount,
            'deductions': self.deductions,
            'totalAmount': self.total_amount,
            'netAmount': self.total_amount,
            'collectionCount': self.collection_count,
            'status': self.status,
            'paymentMethod': self.payment_method,
            'paidAt': self.paid_at.isoformat() if self.paid_at else None,
            'reference': self.reference,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class QualityTest(_DeclarativeModel):
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
    created_at = db.Column(db.DateTime, default=utcnow)

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


class MilkRejection(_DeclarativeModel):
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
    created_at = db.Column(db.DateTime, default=utcnow)

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


class CollectionCenter(_DeclarativeModel):
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
    created_at = db.Column(db.DateTime, default=utcnow)

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


class CollectionRoute(_DeclarativeModel):
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
    created_at = db.Column(db.DateTime, default=utcnow)

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


class ChillingCenter(_DeclarativeModel):
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
    created_at = db.Column(db.DateTime, default=utcnow)

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


class InventoryItem(_DeclarativeModel):
    """Inventory/stock items."""
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    stock = db.Column(db.Float, default=0)
    unit = db.Column(db.String(30))
    min_stock = db.Column(db.Float, default=0)
    max_stock = db.Column(db.Float, nullable=True)
    reserved = db.Column(db.Float, default=0)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    branch = db.relationship('Branch', backref='inventory_items', lazy=True)
    status = db.Column(db.String(20), default='IN_STOCK')
    updated_at = db.Column(db.DateTime, default=utcnow)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        reserved = self.reserved or 0
        available = max((self.stock or 0) - reserved, 0)
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category,
            'stock': self.stock,
            'available': round(available, 2),
            'reserved': round(reserved, 2),
            'unit': self.unit,
            'minStock': self.min_stock,
            'maxStock': self.max_stock,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'status': 'Low Stock' if self.stock <= self.min_stock else 'In Stock',
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }


class Employee(_DeclarativeModel):
    """Employee records."""
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    # HR role labels only (Operator, Accountant, Driver, ...) — independent of
    # the auth roles (ADMIN / BRANCH_OPERATOR / FARMER) used for login access.
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    branch = db.relationship('Branch', backref='employees', lazy=True)
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    salary = db.Column(db.Float)
    status = db.Column(db.String(20), default='ACTIVE')
    joined_at = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=utcnow)

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


class Vehicle(_DeclarativeModel):
    """Vehicle registry."""
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    type = db.Column(db.String(30), nullable=False)  # TANKER, PICKUP, MINI_VAN
    driver_name = db.Column(db.String(120))
    capacity = db.Column(db.Float)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    branch = db.relationship('Branch', backref='vehicles', lazy=True)
    last_service_date = db.Column(db.Date)
    # Vehicle extras (insurance / maintenance / tracking)
    insurance_no = db.Column(db.String(50))
    insurance_expiry = db.Column(db.Date)
    fitness_expiry = db.Column(db.Date)
    permit_expiry = db.Column(db.Date)
    mileage = db.Column(db.Float, default=0)  # odometer (km)
    next_service_date = db.Column(db.Date)
    gps_status = db.Column(db.String(20), default='NOT_TRACKED')  # ACTIVE, NOT_TRACKED, OFFLINE
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, MAINTENANCE, INACTIVE
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicleNumber': self.vehicle_number,
            'type': self.type,
            'driverName': self.driver_name,
            'capacity': self.capacity,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'lastServiceDate': self.last_service_date.isoformat() if self.last_service_date else None,
            'insuranceNo': self.insurance_no,
            'insuranceExpiry': self.insurance_expiry.isoformat() if self.insurance_expiry else None,
            'fitnessExpiry': self.fitness_expiry.isoformat() if self.fitness_expiry else None,
            'permitExpiry': self.permit_expiry.isoformat() if self.permit_expiry else None,
            'mileage': self.mileage,
            'nextServiceDate': self.next_service_date.isoformat() if self.next_service_date else None,
            'gpsStatus': self.gps_status,
            'status': self.status,
        }


class AuditLog(_DeclarativeModel):
    """System audit trail for all CRUD operations."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80))
    role = db.Column(db.String(30))
    branch_code = db.Column(db.String(20))
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
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'username': self.username,
            'role': self.role,
            'branchCode': self.branch_code,
            'action': self.action,
            'entity': self.entity,
            'entityId': self.entity_id,
            'detail': self.detail or f'{self.action} on {self.entity} {self.entity_id}',
            'ip': self.ip,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class Notification(_DeclarativeModel):
    """System notifications for users."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=True)
    type = db.Column(db.String(30), nullable=False)
    # payment, collection, quality, system, farmer, grievance
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    link = db.Column(db.String(200))
    related_type = db.Column(db.String(30))  # Collection, Payment, Grievance, ...
    related_id = db.Column(db.Integer)
    read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'farmerId': self.farmer_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'relatedType': self.related_type,
            'relatedId': self.related_id,
            'read': self.read,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'readAt': self.read_at.isoformat() if self.read_at else None,
        }


class Supplier(_DeclarativeModel):
    """Procurement suppliers/vendors."""
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    category = db.Column(db.String(50), default='OTHER')
    # EQUIPMENT, PACKAGING, CHEMICALS, FEED, DAIRY, OTHER
    gstin = db.Column(db.String(20))
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'contactPerson': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'category': self.category,
            'gstin': self.gstin,
            'status': self.status,
        }


class PurchaseOrder(_DeclarativeModel):
    """Purchase orders raised against suppliers."""
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    po_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    expected_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='DRAFT')
    # DRAFT, PENDING, APPROVED, RECEIVED, COMPLETED, REJECTED
    delivery_status = db.Column(db.String(20), default='PENDING')
    # PENDING, DISPATCHED, IN_TRANSIT, DELIVERED
    grn_no = db.Column(db.String(20))
    total_amount = db.Column(db.Float, default=0)
    paid_amount = db.Column(db.Float, default=0)
    remarks = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    supplier = db.relationship('Supplier', backref='purchase_orders', lazy=True)
    branch = db.relationship('Branch', backref='purchase_orders', lazy=True)
    items = db.relationship('PurchaseOrderItem', backref='po', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'poCode': self.po_code,
            'supplierId': self.supplier_id,
            'supplierName': self.supplier.name if self.supplier else None,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'orderDate': self.order_date.isoformat() if self.order_date else None,
            'expectedDate': self.expected_date.isoformat() if self.expected_date else None,
            'status': self.status,
            'deliveryStatus': self.delivery_status,
            'grnNo': self.grn_no,
            'totalAmount': self.total_amount,
            'paidAmount': self.paid_amount,
            'balance': round((self.total_amount or 0) - (self.paid_amount or 0), 2),
            'remarks': self.remarks,
            'items': [i.to_dict() for i in self.items],
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class PurchaseOrderItem(_DeclarativeModel):
    """Line items on a purchase order."""
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)
    unit = db.Column(db.String(20), default='nos')
    unit_price = db.Column(db.Float, default=0)
    amount = db.Column(db.Float, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'poId': self.po_id,
            'itemName': self.item_name,
            'quantity': self.quantity,
            'unit': self.unit,
            'unitPrice': self.unit_price,
            'amount': self.amount,
        }


class VendorPayment(_DeclarativeModel):
    """Payments made to suppliers against purchase orders."""
    __tablename__ = 'vendor_payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    method = db.Column(db.String(30), default='BANK_TRANSFER')
    # BANK_TRANSFER, CASH, CHEQUE, UPI
    reference = db.Column(db.String(100))
    status = db.Column(db.String(20), default='COMPLETED')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    po = db.relationship('PurchaseOrder', backref='vendor_payments', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'paymentCode': self.payment_code,
            'poId': self.po_id,
            'poCode': self.po.po_code if self.po else None,
            'supplierName': self.po.supplier.name if self.po and self.po.supplier else None,
            'amount': self.amount,
            'paymentDate': self.payment_date.isoformat() if self.payment_date else None,
            'method': self.method,
            'reference': self.reference,
            'status': self.status,
        }


class StockMovement(_DeclarativeModel):
    """Inventory stock in/out/allocate ledger entries."""
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # IN, OUT, ALLOCATE
    quantity = db.Column(db.Float, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    reference = db.Column(db.String(100))
    note = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    item = db.relationship('InventoryItem', backref='movements', lazy=True)
    branch = db.relationship('Branch', backref='stock_movements', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'itemId': self.item_id,
            'itemName': self.item.name if self.item else None,
            'movementType': self.movement_type,
            'quantity': self.quantity,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'reference': self.reference,
            'note': self.note,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class InventoryAllocation(_DeclarativeModel):
    """Per-branch allocation of a central inventory item."""
    __tablename__ = 'inventory_allocations'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    item = db.relationship('InventoryItem', backref='allocations', lazy=True)
    branch = db.relationship('Branch', backref='inventory_allocations', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'itemId': self.item_id,
            'itemName': self.item.name if self.item else None,
            'branchId': self.branch_id,
            'branchCode': self.branch.code if self.branch else None,
            'branchName': self.branch.name if self.branch else None,
            'quantity': self.quantity,
        }


class VehicleServiceRecord(_DeclarativeModel):
    """Service/maintenance history for vehicles."""
    __tablename__ = 'vehicle_service_records'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    service_date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(255))
    cost = db.Column(db.Float, default=0)
    odometer = db.Column(db.Float, nullable=True)
    vendor = db.Column(db.String(120))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    vehicle = db.relationship('Vehicle', backref='service_records', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicleId': self.vehicle_id,
            'vehicleNumber': self.vehicle.vehicle_number if self.vehicle else None,
            'serviceDate': self.service_date.isoformat() if self.service_date else None,
            'description': self.description,
            'cost': self.cost,
            'odometer': self.odometer,
            'vendor': self.vendor,
        }


class EmployeeAttendance(_DeclarativeModel):
    """Daily employee attendance records."""
    __tablename__ = 'employee_attendance'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False)  # PRESENT, ABSENT, LEAVE, HALF_DAY
    shift = db.Column(db.String(20))
    notes = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    employee = db.relationship('Employee', backref='attendance', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'employeeId': self.employee_id,
            'employeeName': self.employee.name if self.employee else None,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'shift': self.shift,
            'notes': self.notes,
        }


class FarmerDocument(_DeclarativeModel):
    """Documents submitted by a farmer (identity, address, bank, other)."""
    __tablename__ = 'farmer_documents'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    doc_type = db.Column(db.String(30), nullable=False, default='OTHER')
    # AADHAAR, PAN, BANK_PASSBOOK, PHOTO, ADDRESS_PROOF, OTHER
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500))
    mime_type = db.Column(db.String(100))
    status = db.Column(db.String(20), default='PENDING')  # PENDING, APPROVED, REJECTED
    remarks = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utcnow)

    farmer = db.relationship('Farmer', backref='documents')

    def to_dict(self):
        return {
            'id': self.id,
            'farmerId': self.farmer_id,
            'docType': self.doc_type,
            'title': self.title,
            'filePath': self.file_path,
            'status': self.status,
            'remarks': self.remarks,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class Grievance(_DeclarativeModel):
    """Farmer complaints/requests raised through the farmer portal."""
    __tablename__ = 'grievances'

    id = db.Column(db.Integer, primary_key=True)
    grievance_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    # PAYMENT, QUALITY, COLLECTION, OTHER
    description = db.Column(db.Text)
    receipt_no = db.Column(db.String(20))
    attachment = db.Column(db.String(500))
    status = db.Column(db.String(20), default='OPEN')
    # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    response = db.Column(db.Text)
    responded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    farmer = db.relationship('Farmer', backref='grievances', lazy=True)
    branch = db.relationship('Branch', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'grievanceCode': self.grievance_code,
            'farmerId': self.farmer_id,
            'farmerCode': self.farmer.farmer_code if self.farmer else None,
            'farmerName': self.farmer.name if self.farmer else None,
            'branchId': self.branch_id,
            'subject': self.subject,
            'category': self.category,
            'description': self.description,
            'receiptNo': self.receipt_no,
            'status': self.status,
            'response': self.response,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'respondedAt': self.responded_at.isoformat() if self.responded_at else None,
        }


class Expense(_DeclarativeModel):
    """Operational expenses for profit/loss accounting."""
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    # FEED, LABOUR, TRANSPORT, MAINTENANCE, ELECTRICITY, ADMIN, PROCUREMENT, OTHER
    description = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    branch = db.relationship('Branch', backref='expenses', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'branchId': self.branch_id,
            'branchName': self.branch.name if self.branch else None,
            'category': self.category,
            'description': self.description,
            'amount': self.amount,
            'expenseDate': self.expense_date.isoformat() if self.expense_date else None,
        }


class PasswordResetOTP(_DeclarativeModel):
    """
    Persistent password-reset OTP tokens (database-backed).

    Replaces the in-memory OTP_STORE so tokens survive application restarts
    and work correctly across multiple workers (gunicorn -w 4): the OTP is
    created on one worker and validated from any other, because it lives in
    the shared database — never in process memory.

    Only a SHA-256 hash of the OTP is stored — never the plaintext value.
    A token is single-use (used_at) and expires after OTP_TTL_SECONDS.
    """
    __tablename__ = 'password_reset_otps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    otp_hash = db.Column(db.String(64), nullable=False)      # sha256 hex digest
    purpose = db.Column(db.String(30), default='PASSWORD_RESET', index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempt_count = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=5)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    user = db.relationship('User', backref=db.backref('reset_otps', lazy='dynamic'))

    def is_expired(self):
        from backend.utils import ensure_utc
        return ensure_utc(self.expires_at) < utcnow() if self.expires_at else True

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'purpose': self.purpose,
            'expiresAt': self.expires_at.isoformat() if self.expires_at else None,
            'attemptCount': self.attempt_count,
            'maxAttempts': self.max_attempts,
            'usedAt': self.used_at.isoformat() if self.used_at else None,
        }


class NotificationLog(_DeclarativeModel):
    """
    Delivery log for every outbound notification attempt (email / SMS /
    WhatsApp). Written AFTER the business transaction commits, so a failed
    provider never rolls back the collection/payment it accompanies.

    Records provider, recipient, notification type, outcome, provider
    response id (when available) and error — for auditability and retries.
    Sensitive payloads (OTP values, passwords) are never stored here.
    """
    __tablename__ = 'notification_logs'

    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(20), nullable=False)   # EMAIL, SMS, WHATSAPP
    recipient = db.Column(db.String(120), nullable=False)
    notification_type = db.Column(db.String(50), default='GENERAL')
    status = db.Column(db.String(20), default='SENT')    # SENT, SKIPPED, FAILED
    provider = db.Column(db.String(50))
    provider_response_id = db.Column(db.String(120))
    error = db.Column(db.String(500))
    related_type = db.Column(db.String(30))              # Collection, Payment, ...
    related_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'channel': self.channel,
            'recipient': self.recipient,
            'notificationType': self.notification_type,
            'status': self.status,
            'provider': self.provider,
            'providerResponseId': self.provider_response_id,
            'error': self.error,
            'relatedType': self.related_type,
            'relatedId': self.related_id,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }
