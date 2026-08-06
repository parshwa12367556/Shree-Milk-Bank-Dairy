"""
Smart Dairy ERP — Database Seeder

Generates sample data for development and testing.

Usage:
    python run.py --seed

Or from Python:
    from backend.seed import seed_database
    seed_database()
"""
from datetime import date, timedelta, datetime
import random
from backend.app import db
from backend.models import (
    User, Branch, Farmer, BankDetail, RateMaster,
    Collection, Payment, QualityTest, MilkRejection,
    CollectionCenter, CollectionRoute, ChillingCenter,
    InventoryItem, StockMovement, Employee, Vehicle,
    Supplier, PurchaseOrder, PurchaseOrderItem, VendorPayment,
    Expense, Notification, AuditLog,
)
from backend.auth import hash_password
from backend.utils import generate_farmer_email

COMPANY_NAME = 'Shree Milk Bank Dairy'


def seed_database():
    """Seed the database with sample data."""
    print('[SEED] Seeding database...')

    # Clear existing data
    _clear_data()

    # Create seed data (branches FIRST since users reference them)
    _seed_branches()
    _seed_users()
    _seed_farmers()
    _seed_farmer_users()
    _seed_bank_details()
    _seed_rates()
    _seed_collections()
    _seed_payments()
    _seed_quality_tests()
    _seed_rejections()
    _seed_procurement()
    _seed_inventory()
    _seed_employees()
    _seed_vehicles()
    _seed_suppliers_and_orders()
    _seed_expenses()
    _seed_stock_movements()
    _seed_notifications()
    _seed_audit_logs()

    print('[SEED] Database seeded successfully!')
    print('[SEED] Login credentials:')
    print(f'  Head Office: admin / admin123 (SUPER_ADMIN)')
    for b in Branch.query.order_by(Branch.id).all():
        print(f'  Branch {b.code}: {b.code} / {b.phone} (BRANCH_MANAGER)')
    sample = Farmer.query.filter_by(status='ACTIVE').order_by(Farmer.id).first()
    if sample:
        print(f'  Farmer: {sample.email} / {sample.mobile} (FARMER) — sign in with email, password is the mobile number')


def _clear_data():
    """Clear all existing data."""
    models = [
        AuditLog, Notification, VendorPayment, PurchaseOrderItem, PurchaseOrder,
        Supplier, Expense, StockMovement, Vehicle, Employee, InventoryItem,
        CollectionCenter, ChillingCenter, CollectionRoute, MilkRejection,
        QualityTest, Payment, Collection, RateMaster, BankDetail, Farmer,
        Branch, User,
    ]
    for model in models:
        model.query.delete()
    db.session.commit()


def _seed_branches():
    branches = [
        Branch(code='BR01', name='Nippani Branch', manager_name='Vijay Singh',
               phone='9876543210', address='Main Road, Nippani',
               village='Nippani', district='Belagavi', state='Karnataka', status='ACTIVE'),
        Branch(code='BR02', name='Belagavi Branch', manager_name='Ravi Sharma',
               phone='9123456780', address='College Road, Belagavi',
               village='Belagavi', district='Belagavi', state='Karnataka', status='ACTIVE'),
        Branch(code='BR03', name='Chikkodi Branch', manager_name='Amit Verma',
               phone='9234567890', address='Market Road, Chikkodi',
               village='Chikkodi', district='Belagavi', state='Karnataka', status='ACTIVE'),
        Branch(code='BR04', name='Sankeshwar Branch', manager_name='Sanjay Patil',
               phone='9345678901', address='Station Road, Sankeshwar',
               village='Sankeshwar', district='Belagavi', state='Karnataka', status='ACTIVE'),
        Branch(code='BR05', name='Athani Branch', manager_name='Mahesh Desai',
               phone='9456789012', address='Bus Stand Road, Athani',
               village='Athani', district='Belagavi', state='Karnataka', status='ACTIVE'),
    ]
    db.session.add_all(branches)
    db.session.commit()
    print('[SEED] Branches created')


def _seed_users():
    """One login per branch: username = branch code, password = branch phone."""
    branches = Branch.query.order_by(Branch.id).all()
    users = [
        User(username='admin', password_hash=hash_password('admin123'),
             name='Admin User', role='SUPER_ADMIN', phone='9876543000',
             email='admin@dairy.com', status='ACTIVE'),
    ]
    for b in branches:
        users.append(User(
            username=b.code,
            password_hash=hash_password(b.phone),
            name=b.manager_name or f'{b.name} Manager',
            role='BRANCH_MANAGER',
            branch_id=b.id,
            phone=b.phone,
            email=f'manager{b.code.lower()}@dairy.com',
            status='ACTIVE',
        ))
    db.session.add_all(users)
    db.session.commit()
    print('[SEED] Users created')


def _seed_farmers():
    """Farmers with auto-generated IDs: <branch code><3-digit serial> (BR01001...)."""
    first_names = ['Ramesh', 'Dinesh', 'Suresh', 'Mahesh', 'Prakash', 'Ajay',
                   'Sunil', 'Amar', 'Ravi', 'Vikas', 'Rajesh', 'Ganesh',
                   'Vinod', 'Sanjay', 'Mohan', 'Raju', 'Deepak', 'Kailash',
                   'Santosh', 'Nitin', 'Anil', 'Prakash', 'Harish', 'Girish']
    last_names = ['Kumar', 'Verma', 'Patil', 'Sharma', 'Mane', 'Meena', 'Gaikwad',
                  'Deshmukh', 'Yadav', 'Das', 'Joshi', 'Patel', 'Lal', 'Bhai',
                  'Kulkarni', 'Desai', 'Sutar', 'Kamble', 'More', 'Jadhav']

    branches = Branch.query.order_by(Branch.id).all()
    farmers = []
    per_branch = 10

    for b in branches:
        for i in range(1, per_branch + 1):
            mtype = random.choice(['COW', 'BUFFALO', 'MIXED'])
            code = f'{b.code}{i:03d}'
            farmer = Farmer(
                farmer_code=code,
                name=f'{random.choice(first_names)} {random.choice(last_names)}',
                father_name=f'{random.choice(first_names)} {random.choice(last_names)}',
                mobile=f'9{random.randint(200000000, 999999999)}',
                email=generate_farmer_email(code),
                aadhaar=str(random.randint(100000000000, 999999999999)),
                village=b.village,
                taluka=random.choice(['Nippani', 'Chikkodi', 'Athani', 'Kagwad', 'Raybag']),
                district=b.district,
                state=b.state,
                pincode=str(random.randint(591101, 591399)),
                milk_type=mtype,
                cow_count=random.randint(1, 6) if mtype != 'BUFFALO' else 0,
                buffalo_count=random.randint(1, 6) if mtype != 'COW' else 0,
                branch_id=b.id,
                status='ACTIVE',
                joined_at=date.today() - timedelta(days=random.randint(30, 365)),
            )
            farmers.append(farmer)

    # A few blocked / inactive farmers for demo purposes
    farmers.append(Farmer(
        farmer_code=f'BR01{per_branch + 1:03d}', name='Test Blocked', father_name='T Father',
        mobile='9876543299', email=generate_farmer_email(f'BR01{per_branch + 1:03d}'),
        village='Nippani', milk_type='COW',
        cow_count=2, buffalo_count=0, branch_id=1,
        status='BLOCKED', status_reason='Quality violation',
        joined_at=date.today() - timedelta(days=90),
    ))
    farmers.append(Farmer(
        farmer_code=f'BR02{per_branch + 1:03d}', name='Test Inactive', father_name='T Father',
        mobile='9876543298', email=generate_farmer_email(f'BR02{per_branch + 1:03d}'),
        village='Belagavi', milk_type='BUFFALO',
        cow_count=0, buffalo_count=2, branch_id=2,
        status='INACTIVE',
        joined_at=date.today() - timedelta(days=60),
    ))
    farmers.append(Farmer(
        farmer_code=f'BR03{per_branch + 1:03d}', name='Test Pending Verify', father_name='P Father',
        mobile='9876543297', email=generate_farmer_email(f'BR03{per_branch + 1:03d}'),
        village='Chikkodi', milk_type='COW',
        cow_count=3, buffalo_count=0, branch_id=3,
        status='PENDING_VERIFICATION',
        joined_at=date.today() - timedelta(days=5),
    ))

    db.session.add_all(farmers)
    db.session.commit()
    print(f'[SEED] {len(farmers)} Farmers created')


def _seed_farmer_users():
    """Create login accounts for farmers (username = farmer code, password = mobile).

    Only ACTIVE farmers get ACTIVE logins — unverified/blocked farmers stay
    locked out of the portal until Head Office activates them.
    """
    users = []
    for farmer in Farmer.query.order_by(Farmer.id).all():
        users.append(User(
            username=farmer.farmer_code,
            password_hash=hash_password(farmer.mobile or 'farmer@123'),
            name=farmer.name,
            role='FARMER',
            branch_id=farmer.branch_id,
            phone=farmer.mobile,
            email=farmer.email,
            farmer_id=farmer.id,
            status='ACTIVE' if farmer.status == 'ACTIVE' else 'INACTIVE',
        ))
    db.session.add_all(users)
    db.session.commit()
    print(f'[SEED] {len(users)} Farmer login accounts created')


def _seed_bank_details():
    farmers = Farmer.query.all()
    banks = [
        'State Bank of India', 'Bank of Baroda', 'HDFC Bank',
        'ICICI Bank', 'Karnataka Gramin Bank',
    ]
    for farmer in farmers[:12]:
        bank = BankDetail(
            farmer_id=farmer.id,
            account_holder=farmer.name,
            bank_name=random.choice(banks),
            branch_name=f'{farmer.village} Branch',
            account_number=str(random.randint(100000000000, 999999999999)),
            ifsc=f'SBIN0{random.randint(100000, 999999)}',
        )
        db.session.add(bank)
    db.session.commit()
    print('[SEED] Bank details created')


def _seed_rates():
    rates = [
        RateMaster(milk_type='COW', fat_rate=5.00, snf_rate=2.50,
                   effective_from=date(2026, 7, 15), version=2, status='ACTIVE',
                   created_by=1),
        RateMaster(milk_type='BUFFALO', fat_rate=6.50, snf_rate=3.00,
                   effective_from=date(2026, 7, 15), version=2, status='ACTIVE',
                   created_by=1),
        RateMaster(milk_type='COW', fat_rate=4.80, snf_rate=2.40,
                   effective_from=date(2026, 7, 1), effective_to=date(2026, 7, 14),
                   version=1, status='INACTIVE', created_by=1),
        RateMaster(milk_type='BUFFALO', fat_rate=6.30, snf_rate=2.90,
                   effective_from=date(2026, 7, 1), effective_to=date(2026, 7, 14),
                   version=1, status='INACTIVE', created_by=1),
    ]
    db.session.add_all(rates)
    db.session.commit()
    print('[SEED] Rates created')


def _seed_collections():
    farmers = Farmer.query.filter_by(status='ACTIVE').all()
    rate_cow = RateMaster.query.filter_by(milk_type='COW', status='ACTIVE').first()
    rate_buffalo = RateMaster.query.filter_by(milk_type='BUFFALO', status='ACTIVE').first()
    branch_users = {u.branch_id: u.id for u in User.query.filter_by(role='BRANCH_MANAGER').all()}

    collections = []
    seq = 1240

    for day_offset in range(14):
        for farmer in farmers[:random.randint(8, 15)]:
            for shift in ['MORNING', 'EVENING']:
                if random.random() > 0.6:
                    continue
                seq += 1

                qty = round(random.uniform(10, 35), 1)
                fat = round(random.uniform(3.5, 7.0), 1)
                snf = round(random.uniform(8.0, 9.5), 1)
                water = round(random.uniform(1.5, 6.0), 1)

                rate = rate_cow if farmer.milk_type == 'COW' else rate_buffalo
                fat_rate = rate.fat_rate if rate else 5.0
                snf_rate = rate.snf_rate if rate else 2.5
                rate_per_liter = round(fat * fat_rate + snf * snf_rate, 2)
                amount = round(rate_per_liter * qty, 2)

                coll_date = date.today() - timedelta(days=day_offset)
                collection = Collection(
                    receipt_no=f'RC{seq:07d}',
                    farmer_id=farmer.id,
                    branch_id=farmer.branch_id,
                    operator_id=branch_users.get(farmer.branch_id, 1),
                    rate_master_id=rate.id if rate else None,
                    date=coll_date,
                    shift=shift,
                    milk_type=farmer.milk_type,
                    quantity=qty,
                    fat=fat,
                    snf=snf,
                    clr=round(random.uniform(27.0, 29.5), 1),
                    temperature=round(random.uniform(3.0, 6.0), 1),
                    water=water,
                    rate_per_liter=rate_per_liter,
                    amount=amount,
                    status='ACCEPTED',
                )
                collections.append(collection)

    db.session.add_all(collections)
    db.session.commit()
    print(f'[SEED] {len(collections)} Collections created')


def _seed_payments():
    farmers = Farmer.query.filter_by(status='ACTIVE').limit(8).all()
    payments = []

    for farmer in farmers:
        collections = Collection.query.filter(
            Collection.farmer_id == farmer.id,
            Collection.payment_id.is_(None),
        ).limit(random.randint(3, 8)).all()

        if not collections:
            continue

        total_qty = sum(c.quantity for c in collections)
        total_amt = sum(c.amount for c in collections)
        status = random.choice(['PENDING', 'APPROVED', 'PAID'])

        payment = Payment(
            pay_code=f'PAY{100 + len(payments):07d}',
            farmer_id=farmer.id,
            branch_id=farmer.branch_id,
            period_start=date.today() - timedelta(days=15),
            period_end=date.today(),
            total_quantity=total_qty,
            total_amount=total_amt,
            collection_count=len(collections),
            status=status,
            paid_at=datetime.now() if status == 'PAID' else None,
            paid_by=1 if status == 'PAID' else None,  # Head Office (Super Admin)
        )
        db.session.add(payment)
        db.session.flush()

        for c in collections:
            c.payment_id = payment.id

        payments.append(payment)

    db.session.commit()
    print(f'[SEED] {len(payments)} Payments created')


def _seed_quality_tests():
    collections = Collection.query.order_by(Collection.id.desc()).limit(30).all()
    tests = []

    for coll in collections[:20]:
        water = coll.water or random.uniform(2.0, 6.0)
        if water > 8:
            result = 'FAIL'
        elif water > 5:
            result = 'BORDERLINE'
        else:
            result = 'PASS'

        test = QualityTest(
            collection_id=coll.id,
            farmer_id=coll.farmer_id,
            branch_id=coll.branch_id,
            tested_by=coll.operator_id,
            date=coll.date,
            shift=coll.shift,
            fat=coll.fat,
            snf=coll.snf,
            clr=coll.clr,
            temperature=coll.temperature,
            water_content=coll.water,
            overall_result=result,
            result_summary=f'Grade: {result}',
        )
        tests.append(test)

    db.session.add_all(tests)
    db.session.commit()
    print(f'[SEED] {len(tests)} Quality tests created')


def _seed_rejections():
    branch_users = {u.branch_id: u.id for u in User.query.filter_by(role='BRANCH_MANAGER').all()}
    farmers = Farmer.query.order_by(Farmer.id).all()
    rejections = [
        MilkRejection(farmer_id=farmers[0].id, branch_id=farmers[0].branch_id,
                      rejected_by=branch_users.get(farmers[0].branch_id, 1),
                      date=date.today() - timedelta(days=1),
                      shift='MORNING', quantity=30, reason='HIGH_WATER',
                      fat=3.8, water_content=9.2, remark='Water > 8% threshold'),
        MilkRejection(farmer_id=farmers[2].id, branch_id=farmers[2].branch_id,
                      rejected_by=branch_users.get(farmers[2].branch_id, 1),
                      date=date.today() - timedelta(days=2),
                      shift='MORNING', quantity=22, reason='SOUR_MILK',
                      fat=3.5, remark='Failed alcohol test'),
        MilkRejection(farmer_id=farmers[4].id, branch_id=farmers[4].branch_id,
                      rejected_by=branch_users.get(farmers[4].branch_id, 1),
                      date=date.today() - timedelta(days=3),
                      shift='EVENING', quantity=18, reason='LOW_FAT',
                      fat=2.8, remark='Fat below minimum'),
    ]
    db.session.add_all(rejections)
    db.session.commit()
    print(f'[SEED] {len(rejections)} Rejections created')


def _seed_procurement():
    b1 = Branch.query.filter_by(code='BR01').first()
    b2 = Branch.query.filter_by(code='BR02').first()
    centers = [
        CollectionCenter(code='CC-001', name='Nippani Main Center', center_type='MAIN',
                         branch_id=b1.id, manager_name=b1.manager_name, capacity=5000,
                         village='Nippani', district='Belagavi', status='ACTIVE'),
        CollectionCenter(code='CC-002', name='Belagavi Sub Center', center_type='SUB_CENTER',
                         branch_id=b2.id, manager_name=b2.manager_name, capacity=2000,
                         village='Belagavi', district='Belagavi', status='ACTIVE'),
        CollectionCenter(code='CC-003', name='Chikkodi Chilling Point', center_type='CHILLING_POINT',
                         branch_id=b1.id, manager_name='Amit Verma', capacity=3000,
                         village='Chikkodi', district='Belagavi', status='ACTIVE'),
    ]
    db.session.add_all(centers)
    db.session.commit()
    print('[SEED] Collection centers created')


def _seed_inventory():
    items = [
        InventoryItem(code='INV-001', name='Raw Milk', category='Dairy', stock=12450, unit='Liters', min_stock=2000),
        InventoryItem(code='INV-002', name='Pasteurized Milk', category='Dairy', stock=5800, unit='Liters', min_stock=1000),
        InventoryItem(code='INV-003', name='Curd', category='Dairy', stock=850, unit='Liters', min_stock=200),
        InventoryItem(code='INV-004', name='Packaging Material', category='Packaging', stock=12500, unit='Pieces', min_stock=5000),
        InventoryItem(code='INV-005', name='Cleaning Supplies', category='Supplies', stock=45, unit='Boxes', min_stock=10),
        InventoryItem(code='INV-006', name='Starter Culture', category='Ingredients', stock=8, unit='Packs', min_stock=5),
    ]
    db.session.add_all(items)
    db.session.commit()
    print('[SEED] Inventory items created')


def _seed_employees():
    b1 = Branch.query.filter_by(code='BR01').first()
    b2 = Branch.query.filter_by(code='BR02').first()
    employees = [
        Employee(code='EMP-001', name='Anil Sharma', role='Operator', branch_id=b1.id, mobile='9876543101', email='anil@dairy.com', status='ACTIVE'),
        Employee(code='EMP-002', name='Rahul Verma', role='Operator', branch_id=b2.id, mobile='9876543102', email='rahul@dairy.com', status='ACTIVE'),
        Employee(code='EMP-003', name='Priya Patel', role='Accountant', mobile='9876543103', email='priya@dairy.com', status='ACTIVE'),
        Employee(code='EMP-004', name='Vijay Singh', role='Branch Manager', branch_id=b1.id, mobile='9876543104', email='vijay@dairy.com', status='ACTIVE'),
        Employee(code='EMP-005', name='Amit Kumar', role='Driver', branch_id=b1.id, mobile='9876543105', email='amit@dairy.com', status='ACTIVE'),
    ]
    db.session.add_all(employees)
    db.session.commit()
    print('[SEED] Employees created')


def _seed_vehicles():
    b1 = Branch.query.filter_by(code='BR01').first()
    b2 = Branch.query.filter_by(code='BR02').first()
    vehicles = [
        Vehicle(vehicle_number='KA-23-AB-1234', type='TANKER', driver_name='Ramesh Kumar', capacity=3000, branch_id=b1.id, status='ACTIVE',
                insurance_no='POL-2026-112233', insurance_expiry=date(2026, 12, 31), last_service_date=date.today() - timedelta(days=30), next_service_date=date.today() + timedelta(days=60), gps_status='ACTIVE'),
        Vehicle(vehicle_number='KA-22-CD-5678', type='TANKER', driver_name='Suresh Patil', capacity=2500, branch_id=b2.id, status='ACTIVE',
                insurance_no='POL-2026-445566', insurance_expiry=date(2026, 9, 15), last_service_date=date.today() - timedelta(days=15), next_service_date=date.today() + timedelta(days=45), gps_status='ACTIVE'),
        Vehicle(vehicle_number='KA-23-EF-9012', type='PICKUP', driver_name='Mahesh Das', capacity=1000, branch_id=b1.id, status='MAINTENANCE',
                insurance_expiry=date(2026, 3, 1), gps_status='NOT_TRACKED'),
    ]
    db.session.add_all(vehicles)
    db.session.commit()
    print('[SEED] Vehicles created')


def _seed_suppliers_and_orders():
    suppliers = [
        Supplier(code='SUP-001', name='Karnataka Dairy Equipments', contact_person='Ravi Patil',
                 phone='9888800001', email='sales@kde.in', address='Belagavi',
                 category='EQUIPMENT', status='ACTIVE'),
        Supplier(code='SUP-002', name='PackPlus Industries', contact_person='Amit Jain',
                 phone='9888800002', email='amit@packplus.in', address='Pune',
                 category='PACKAGING', status='ACTIVE'),
        Supplier(code='SUP-003', name='AgroFeed Solutions', contact_person='Sunil Kumar',
                 phone='9888800003', email='sunil@agrofeed.in', address='Kolhapur',
                 category='FEED', status='ACTIVE'),
        Supplier(code='SUP-004', name='VetChem Labs', contact_person='Dr. Sneha Rao',
                 phone='9888800004', email='sneha@vetchem.in', address='Hubli',
                 category='CHEMICALS', status='ACTIVE'),
    ]
    db.session.add_all(suppliers)
    db.session.commit()

    b1 = Branch.query.filter_by(code='BR01').first()
    po = PurchaseOrder(
        po_code='PO000001',
        supplier_id=suppliers[0].id,
        branch_id=b1.id,
        order_date=date.today() - timedelta(days=12),
        expected_date=date.today() + timedelta(days=8),
        status='APPROVED',
        total_amount=97500.00,
        paid_amount=97500.00,
        remarks='Milk cans & testing equipment',
        created_by=1,
    )
    db.session.add(po)
    db.session.flush()
    db.session.add_all([
        PurchaseOrderItem(po_id=po.id, item_name='Milk Cans (40L)', quantity=50, unit='nos', unit_price=1400, amount=70000.00),
        PurchaseOrderItem(po_id=po.id, item_name='Lactometer', quantity=25, unit='nos', unit_price=450, amount=11250.00),
        PurchaseOrderItem(po_id=po.id, item_name='Butyrometer', quantity=10, unit='nos', unit_price=1625, amount=16250.00),
    ])
    db.session.add(VendorPayment(
        payment_code='VP000001', po_id=po.id, amount=97500.00,
        payment_date=date.today() - timedelta(days=2), method='BANK_TRANSFER',
        reference='UTR20260701123456', status='COMPLETED', created_by=1,
    ))
    db.session.commit()
    print('[SEED] Suppliers & purchase orders created')


def _seed_expenses():
    b1 = Branch.query.filter_by(code='BR01').first()
    b2 = Branch.query.filter_by(code='BR02').first()
    expenses = [
        Expense(code='EXP000001', branch_id=b1.id, category='FEED',
                description='Animal feed purchase', amount=12500.00,
                expense_date=date.today() - timedelta(days=2), created_by=1),
        Expense(code='EXP000002', branch_id=b2.id, category='TRANSPORT',
                description='Milk tanker fuel', amount=8400.00,
                expense_date=date.today() - timedelta(days=3), created_by=1),
        Expense(code='EXP000003', branch_id=b1.id, category='ELECTRICITY',
                description='Chilling unit electricity bill', amount=5600.00,
                expense_date=date.today() - timedelta(days=5), created_by=1),
        Expense(code='EXP000004', branch_id=None, category='ADMIN',
                description='Head office stationery & admin', amount=3100.00,
                expense_date=date.today() - timedelta(days=6), created_by=1),
    ]
    db.session.add_all(expenses)
    db.session.commit()
    print('[SEED] Expenses created')


def _seed_stock_movements():
    raw_milk = InventoryItem.query.filter_by(code='INV-001').first()
    packaging = InventoryItem.query.filter_by(code='INV-004').first()
    b1 = Branch.query.filter_by(code='BR01').first()
    movements = [
        StockMovement(item_id=raw_milk.id, movement_type='IN', quantity=2500, reference='Collection',
                      note='Morning bulk intake', created_by=1),
        StockMovement(item_id=raw_milk.id, movement_type='ALLOCATE', quantity=800, branch_id=b1.id,
                      reference='ALLOC-101', note='Allocated to BR01', created_by=1),
        StockMovement(item_id=packaging.id, movement_type='OUT', quantity=300, reference='PACK-88',
                      note='Dispatch to packing line', created_by=1),
    ]
    db.session.add_all(movements)
    db.session.commit()
    print('[SEED] Stock movements created')


def _seed_notifications():
    notifications = [
        Notification(type='collection', title='Collection Target Achieved',
                     message='Nippani branch achieved 98% of daily target.', read=False),
        Notification(type='payment', title='Payment Sheet Generated',
                     message='New payment sheet for 24 farmers.', read=False),
        Notification(type='quality', title='Quality Alert',
                     message='5 farmers flagged for quality follow-up.', read=False),
        Notification(type='system', title='Rate Version Updated',
                     message='New rate version effective from 01 Aug 2026.', read=False),
        Notification(type='farmer', title='New Farmer Registered',
                     message='New farmer (BR01011) registered at Nippani branch.', read=True),
    ]
    db.session.add_all(notifications)
    db.session.commit()
    print('[SEED] Notifications created')


def _seed_audit_logs():
    logs = [
        AuditLog(user_id=1, username='Admin User', action='LOGIN', entity='Session', entity_id='admin',
                 detail='User logged in successfully', ip='192.168.1.100'),
        AuditLog(user_id=2, username='BR01', action='CREATE', entity='Collection', entity_id='RC0001245',
                 detail='Recorded milk collection: 25L Cow Milk', ip='192.168.1.101'),
        AuditLog(user_id=1, username='Admin User', action='UPDATE', entity='RateMaster', entity_id='v2.1',
                 detail='Updated rates: Cow Rs 5.00, Buffalo Rs 6.50'),
        AuditLog(user_id=1, username='Admin User', action='APPROVE', entity='Payment', entity_id='PAY0000101',
                 detail='Approved payment of Rs 5,328'),
    ]
    db.session.add_all(logs)
    db.session.commit()
    print('[SEED] Audit logs created')
