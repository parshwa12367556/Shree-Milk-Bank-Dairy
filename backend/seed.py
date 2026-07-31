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
    CollectionCenter, InventoryItem, Employee, Vehicle,
    Notification, AuditLog,
)
from backend.auth import hash_password


def seed_database():
    """Seed the database with sample data."""
    print('[SEED] Seeding database...')

    # Clear existing data
    _clear_data()

    # Create seed data (branches FIRST since users reference them)
    _seed_branches()
    _seed_users()
    _seed_farmers()
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
    _seed_notifications()
    _seed_audit_logs()

    print('[SEED] Database seeded successfully!')
    print('[SEED] Login credentials:')
    print('  admin      / admin123      (SUPER_ADMIN)')
    print('  manager    / manager123    (BRANCH_MANAGER)')
    print('  operator   / operator123   (OPERATOR)')
    print('  accountant / accountant123 (ACCOUNTANT)')


def _clear_data():
    """Clear all existing data."""
    models = [
        AuditLog, Notification, Vehicle, Employee, InventoryItem,
        CollectionCenter, MilkRejection, QualityTest, Payment,
        Collection, RateMaster, BankDetail, Farmer, Branch, User,
    ]
    for model in models:
        model.query.delete()
    db.session.commit()


def _seed_users():
    users = [
        User(username='admin', password_hash=hash_password('admin123'),
             name='Admin User', role='SUPER_ADMIN', phone='9876543000',
             email='admin@dairy.com', status='ACTIVE'),
        User(username='manager', password_hash=hash_password('manager123'),
             name='Vijay Singh', role='BRANCH_MANAGER', branch_id=1,
             phone='9876543001', email='vijay@dairy.com', status='ACTIVE'),
        User(username='operator', password_hash=hash_password('operator123'),
             name='Anil Sharma', role='OPERATOR', branch_id=1,
             phone='9876543002', email='anil@dairy.com', status='ACTIVE'),
        User(username='accountant', password_hash=hash_password('accountant123'),
             name='Priya Patel', role='ACCOUNTANT',
             phone='9876543003', email='priya@dairy.com', status='ACTIVE'),
    ]
    db.session.add_all(users)
    db.session.commit()
    print('[SEED] Users created')


def _seed_branches():
    branches = [
        Branch(code='BR-001', name='Agar Malwa Main', manager_name='Vijay Singh',
               phone='9876543001', address='Main Road, Agar Malwa',
               village='Agar', district='Agar Malwa', state='Madhya Pradesh', status='ACTIVE'),
        Branch(code='BR-002', name='Susner Sub', manager_name='Ravi Sharma',
               phone='9876543004', address='Bus Stand, Susner',
               village='Susner', district='Shajapur', state='Madhya Pradesh', status='ACTIVE'),
        Branch(code='BR-003', name='Kannod Branch', manager_name='Amit Verma',
               phone='9876543005', address='Market Road, Kannod',
               village='Kannod', district='Agar Malwa', state='Madhya Pradesh', status='ACTIVE'),
        Branch(code='BR-004', name='Shajapur Branch', manager_name='Sanjay Patil',
               phone='9876543006', address='Station Road, Shajapur',
               village='Shajapur', district='Shajapur', state='Madhya Pradesh', status='ACTIVE'),
    ]
    db.session.add_all(branches)
    db.session.commit()
    print('[SEED] Branches created')


def _seed_farmers():
    farmer_data = [
        ('C-1042', 'Ramesh Kumar', 'Suresh Kumar', '9876543210', 'Agar', 'COW', 4, 0),
        ('C-1043', 'Dinesh Verma', 'Ramesh Verma', '9876543211', 'Susner', 'COW', 3, 0),
        ('B-0387', 'Suresh Patil', 'Ganesh Patil', '9876543212', 'Kannod', 'BUFFALO', 0, 5),
        ('M-0215', 'Mahesh Sharma', 'Laxmi Sharma', '9876543213', 'Nalkheda', 'MIXED', 3, 4),
        ('C-1089', 'Prakash Mane', 'Shivaji Mane', '9876543214', 'Shajapur', 'COW', 2, 0),
        ('B-0401', 'Ajay Meena', 'Ravi Meena', '9876543215', 'Agar', 'BUFFALO', 0, 4),
        ('C-1098', 'Sunil Gaikwad', 'Dattatray Gaikwad', '9876543216', 'Susner', 'COW', 3, 0),
        ('M-0221', 'Amar Deshmukh', 'Vijay Deshmukh', '9876543217', 'Kannod', 'MIXED', 4, 2),
        ('C-1123', 'Ravi Patil', 'Shankar Patil', '9876543218', 'Agar', 'COW', 2, 0),
        ('B-0425', 'Vikas Yadav', 'Ram Yadav', '9876543219', 'Nalkheda', 'BUFFALO', 0, 3),
        ('C-1150', 'Rajesh Kumar', 'Mohan Kumar', '9876543220', 'Shajapur', 'COW', 5, 0),
        ('B-0440', 'Ganesh Das', 'Hari Das', '9876543221', 'Agar', 'BUFFALO', 0, 6),
        ('M-0235', 'Vinod Sharma', 'Kishan Sharma', '9876543222', 'Susner', 'MIXED', 2, 3),
        ('C-1178', 'Sanjay Patel', 'Ramesh Patel', '9876543223', 'Kannod', 'COW', 4, 0),
        ('B-0458', 'Mohan Lal', 'Shyam Lal', '9876543224', 'Nalkheda', 'BUFFALO', 0, 4),
        ('C-1201', 'Raju Bhai', 'Mangilal', '9876543225', 'Agar', 'COW', 3, 0),
        ('M-0248', 'Deepak Joshi', 'Ravi Joshi', '9876543226', 'Shajapur', 'MIXED', 3, 3),
        ('B-0472', 'Kailash Meena', 'Sohan Meena', '9876543227', 'Susner', 'BUFFALO', 0, 5),
    ]

    farmers = []
    for code, name, father, mobile, village, mtype, cows, buffs in farmer_data:
        branch_id = random.choice([1, 2, 3, 4])
        farmer = Farmer(
            farmer_code=code, name=name, father_name=father,
            mobile=mobile, village=village, milk_type=mtype,
            cow_count=cows, buffalo_count=buffs,
            branch_id=branch_id, status='ACTIVE',
            joined_at=date.today() - timedelta(days=random.randint(30, 365)),
        )
        farmers.append(farmer)

    # Add one blocked and one inactive farmer
    farmers.append(Farmer(
        farmer_code='C-1305', name='Test Blocked', father_name='T Father',
        mobile='9876543299', village='Test', milk_type='COW',
        cow_count=2, buffalo_count=0, branch_id=1,
        status='BLOCKED', status_reason='Quality violation',
        joined_at=date.today() - timedelta(days=90),
    ))
    farmers.append(Farmer(
        farmer_code='B-0500', name='Test Inactive', father_name='T Father',
        mobile='9876543298', village='Test', milk_type='BUFFALO',
        cow_count=0, buffalo_count=2, branch_id=2,
        status='INACTIVE',
        joined_at=date.today() - timedelta(days=60),
    ))

    db.session.add_all(farmers)
    db.session.commit()
    print('[SEED] Farmers created')


def _seed_bank_details():
    farmers = Farmer.query.all()
    banks = [
        'State Bank of India', 'Bank of Baroda', 'HDFC Bank',
        'ICICI Bank', 'Madhya Pradesh Gramin Bank',
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
                    operator_id=random.choice([2, 3]),
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

    for i, farmer in enumerate(farmers):
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
            pay_code=f'PAY{100 + i:07d}',
            farmer_id=farmer.id,
            branch_id=farmer.branch_id,
            period_start=date.today() - timedelta(days=15),
            period_end=date.today(),
            total_quantity=total_qty,
            total_amount=total_amt,
            collection_count=len(collections),
            status=status,
            paid_at=datetime.now() if status == 'PAID' else None,
            paid_by=4 if status == 'PAID' else None,
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
    farmers = Farmer.query.all()
    rejections = [
        MilkRejection(farmer_id=farmers[0].id, branch_id=farmers[0].branch_id,
                      rejected_by=3, date=date.today() - timedelta(days=1),
                      shift='MORNING', quantity=30, reason='HIGH_WATER',
                      fat=3.8, water_content=9.2, remark='Water > 8% threshold'),
        MilkRejection(farmer_id=farmers[2].id, branch_id=farmers[2].branch_id,
                      rejected_by=3, date=date.today() - timedelta(days=2),
                      shift='MORNING', quantity=22, reason='SOUR_MILK',
                      fat=3.5, remark='Failed alcohol test'),
        MilkRejection(farmer_id=farmers[4].id, branch_id=farmers[4].branch_id,
                      rejected_by=3, date=date.today() - timedelta(days=3),
                      shift='EVENING', quantity=18, reason='LOW_FAT',
                      fat=2.8, remark='Fat below minimum'),
    ]
    db.session.add_all(rejections)
    db.session.commit()
    print(f'[SEED] {len(rejections)} Rejections created')


def _seed_procurement():
    centers = [
        CollectionCenter(code='CC-001', name='Agar Main Center', center_type='MAIN',
                         branch_id=1, manager_name='Vijay Singh', capacity=5000,
                         village='Agar', district='Agar Malwa', status='ACTIVE'),
        CollectionCenter(code='CC-002', name='Susner Sub Center', center_type='SUB_CENTER',
                         branch_id=2, manager_name='Ravi Sharma', capacity=2000,
                         village='Susner', district='Shajapur', status='ACTIVE'),
        CollectionCenter(code='CC-003', name='Kannod Chilling Point', center_type='CHILLING_POINT',
                         branch_id=1, manager_name='Amit Verma', capacity=3000,
                         village='Kannod', district='Agar Malwa', status='ACTIVE'),
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
    employees = [
        Employee(code='EMP-001', name='Anil Sharma', role='Operator', branch_id=1, mobile='9876543101', email='anil@dairy.com', status='ACTIVE'),
        Employee(code='EMP-002', name='Rahul Verma', role='Operator', branch_id=2, mobile='9876543102', email='rahul@dairy.com', status='ACTIVE'),
        Employee(code='EMP-003', name='Priya Patel', role='Accountant', mobile='9876543103', email='priya@dairy.com', status='ACTIVE'),
        Employee(code='EMP-004', name='Vijay Singh', role='Branch Manager', branch_id=1, mobile='9876543104', email='vijay@dairy.com', status='ACTIVE'),
        Employee(code='EMP-005', name='Amit Kumar', role='Driver', branch_id=1, mobile='9876543105', email='amit@dairy.com', status='ACTIVE'),
    ]
    db.session.add_all(employees)
    db.session.commit()
    print('[SEED] Employees created')


def _seed_vehicles():
    vehicles = [
        Vehicle(vehicle_number='MP-09-AB-1234', type='TANKER', driver_name='Ramesh Kumar', capacity=3000, branch_id=1, status='ACTIVE'),
        Vehicle(vehicle_number='MP-09-CD-5678', type='TANKER', driver_name='Suresh Patil', capacity=2500, branch_id=2, status='ACTIVE'),
        Vehicle(vehicle_number='MP-09-EF-9012', type='PICKUP', driver_name='Mahesh Das', capacity=1000, branch_id=1, status='MAINTENANCE'),
    ]
    db.session.add_all(vehicles)
    db.session.commit()
    print('[SEED] Vehicles created')


def _seed_notifications():
    notifications = [
        Notification(type='collection', title='Collection Target Achieved',
                     message='Agar Malwa branch achieved 98% of daily target.', read=False),
        Notification(type='payment', title='Payment Sheet Generated',
                     message='New payment sheet for 24 farmers.', read=False),
        Notification(type='quality', title='Quality Alert',
                     message='5 farmers flagged for quality follow-up.', read=False),
        Notification(type='system', title='Rate Version Updated',
                     message='New rate version effective from 01 Aug 2026.', read=False),
        Notification(type='farmer', title='New Farmer Registered',
                     message='Ravi Patil (C-1097) registered at Susner branch.', read=True),
    ]
    db.session.add_all(notifications)
    db.session.commit()
    print('[SEED] Notifications created')


def _seed_audit_logs():
    logs = [
        AuditLog(user_id=1, username='Admin User', action='LOGIN', entity='Session', entity_id='admin',
                 detail='User logged in successfully', ip='192.168.1.100'),
        AuditLog(user_id=3, username='Anil Sharma', action='CREATE', entity='Collection', entity_id='RC0001245',
                 detail='Recorded milk collection: 25L Cow Milk'),
        AuditLog(user_id=1, username='Admin User', action='UPDATE', entity='RateMaster', entity_id='v2.1',
                 detail='Updated rates: Cow Rs 5.00, Buffalo Rs 6.50'),
        AuditLog(user_id=4, username='Priya Patel', action='APPROVE', entity='Payment', entity_id='PAY0000124',
                 detail='Approved payment of Rs 5,328'),
    ]
    db.session.add_all(logs)
    db.session.commit()
    print('[SEED] Audit logs created')
