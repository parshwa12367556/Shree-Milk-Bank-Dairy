"""Shree Milk Bank — Security & RBAC tests (spec §32).

Proves the 17 required security scenarios:
  1.  ADMIN can access authorized system-wide data
  2.  BRANCH_OPERATOR BR01 cannot access BR02 data
  3.  BRANCH_OPERATOR cannot create collections for another branch
  4.  FARMER A cannot access FARMER B's data
  5.  FARMER cannot modify payment status
  6.  BRANCH_OPERATOR cannot process payments
  7.  BRANCH_OPERATOR cannot modify pricing
  8.  FARMER cannot access Admin APIs
  9.  Invalid JWT is rejected
  10. Expired JWT is rejected
  11. Inactive users cannot log in
  12. Locked users cannot log in
  13. Duplicate farmer account creation is prevented
  14. Duplicate payment is prevented
  15. Collection amount is calculated by backend (client amount never trusted)
  16. Pricing changes do not modify historical collection amounts
  17. Every important action creates an audit log

Also verifies the farmer ledger (passbook source of truth).

Run:  python test_security_rbac.py
"""
import os
import sys
from datetime import date as _date, datetime, timedelta
import json

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.getenv('TEST_DB_PATH', 'instance/test_security_rbac.db')
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except Exception:
        pass
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(DB_PATH).replace('\\', '/')
os.environ.setdefault('SECRET_KEY', 'test-production-secret-key-32chars-long-minimum')
os.environ.setdefault('JWT_SECRET_KEY', 'test-production-jwt-secret-key-32chars-long-minimum')

from backend.app import create_app  # noqa: E402

app = create_app('production')

PASS, FAIL = 0, 0


def check(name, cond, extra=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK  {name} {extra}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {extra}")


def login(client, username, password, role=None):
    payload = {'username': username, 'password': password}
    if role:
        payload['role'] = role
    r = client.post('/api/auth/login', json=payload)
    if r.status_code != 200:
        return None, r
    return r.get_json().get('token'), r


def auth(token):
    return {'Authorization': f'Bearer {token}'}


with app.app_context():
    from backend.seed import seed_database
    seed_database()
    from backend.models import User, Farmer, Collection, Payment, AuditLog, RateMaster
    from backend.app import db
    print("Seeded.\n")

admin_c = app.test_client()
br_c = app.test_client()
br2_c = app.test_client()
farmer_c = app.test_client()
farmer2_c = app.test_client()

admin_token, _ = login(admin_c, 'admin', 'admin123')
check('1a. admin login', bool(admin_token))
br_token, _ = login(br_c, 'BR01', '9876543210', 'BRANCH_OPERATOR')
check('2a. BR01 login', bool(br_token))
br2_token, _ = login(br2_c, 'BR02', '9123456780', 'BRANCH_OPERATOR')
check('2b. BR02 login', bool(br2_token))

# Active BR01 farmer + a second farmer (isolation pair)
with app.app_context():
    br1_farmers = [f for f in Farmer.query.filter_by(branch_id=1).all()
                   if f.status == 'ACTIVE']
    farmer = next(f for f in br1_farmers if f.milk_type in ('COW', 'BUFFALO'))
    farmer2 = next(f for f in br1_farmers if f.id != farmer.id)
    farmer_id, farmer2_id = farmer.id, farmer2.id
    farmer_code = farmer.farmer_code
    f_email, f_mobile = farmer.email, farmer.mobile

f_token, _ = login(farmer_c, f_email, f_mobile, 'FARMER')
check('4a. farmer A login', bool(f_token))
f2_token, _ = login(farmer2_c, farmer2.email, farmer2.mobile, 'FARMER')
check('4b. farmer B login', bool(f2_token))

# ── 1. ADMIN system-wide access ─────────────────────────────────────────
r = admin_c.get('/api/dashboard', headers=auth(admin_token))
check('1b. admin dashboard (system-wide)', r.status_code == 200 and 'kpis' in r.get_json())
r = admin_c.get('/api/farmers?per_page=100', headers=auth(admin_token))
total_all = r.get_json()['total']
check('1c. admin sees ALL farmers across branches', r.status_code == 200 and total_all >= 50,
      f"({total_all})")
r = admin_c.get('/api/branches', headers=auth(admin_token))
check('1d. admin sees all branches', r.status_code == 200 and len(r.get_json()['branches']) >= 5)

# ── 2/3. Branch isolation ───────────────────────────────────────────────
r = br_c.get('/api/farmers?per_page=100', headers=auth(br_token))
check('2c. BR01 farmers list = own branch only',
      all(f['branchId'] == 1 for f in r.get_json()['farmers']))
br2_farmer = None
with app.app_context():
    br2_farmer = next(f for f in Farmer.query.filter_by(branch_id=2).all()
                      if f.status == 'ACTIVE')
r = br_c.get(f"/api/farmers/{br2_farmer.farmer_code}", headers=auth(br_token))
check('2d. BR01 cannot view BR02 farmer', r.status_code == 403)
r = br2_c.get('/api/collections?per_page=100', headers=auth(br2_token))
check('2e. BR02 collections = own branch only',
      all(c['branchId'] == 2 for c in r.get_json()['collections']))
r = br2_c.get('/api/payments?per_page=100', headers=auth(br2_token))
check('2f. BR02 payments = own branch only',
      all(p['branchId'] == 2 for p in r.get_json()['payments']))

# ── 3. Cannot collect for another branch ────────────────────────────────
r = br_c.post('/api/collections', json={'farmerId': br2_farmer.id, 'quantity': 12},
              headers=auth(br_token))
check('3. BR01 blocked: collection for BR02 farmer → 403', r.status_code == 403,
      f"(status={r.status_code})")

# ── 4. Farmer IDOR isolation ────────────────────────────────────────────
r = farmer_c.get('/api/farmer/me/collections?per_page=100', headers=auth(f_token))
check('4c. farmer A collections: own only',
      all(c['farmerId'] == farmer_id for c in r.get_json()['collections']))
r = farmer_c.get(f'/api/farmer/me/collections?farmerId={farmer2_id}', headers=auth(f_token))
check('4d. farmerId query param ignored (own only)',
      all(c['farmerId'] == farmer_id for c in r.get_json()['collections']))
r = farmer_c.get(f'/api/farmer/me/passbook?farmerId={farmer2_id}', headers=auth(f_token))
check('4e. passbook scoped to own farmer',
      all(e['farmerId'] == farmer_id for e in r.get_json()['entries']))
# Cross-token access attempt via shared endpoints
r = farmer_c.get('/api/farmers', headers=auth(f_token))
check('4f. farmer blocked from staff farmer list', r.status_code == 403)
r = farmer_c.get(f'/api/farmers/{farmer2.farmer_code}', headers=auth(f_token))
check('4g. farmer blocked from another farmer detail', r.status_code == 403)

# ── 5. Farmer cannot modify payment status ──────────────────────────────
with app.app_context():
    some_pay = Payment.query.first()
if some_pay:
    r = farmer_c.patch(f"/api/payments/{some_pay.id}", json={'status': 'PAID'},
                       headers=auth(f_token))
    check('5. farmer blocked: modify payment status → 403', r.status_code == 403,
          f"(status={r.status_code})")
else:
    check('5. farmer blocked: modify payment status → 403', False, '(no payment row)')

# ── 6. Branch operator cannot process payments ──────────────────────────
r = br_c.post('/api/payments', json={
    'periodStart': (_date.today() - timedelta(days=7)).isoformat(),
    'periodEnd': _date.today().isoformat(),
}, headers=auth(br_token))
check('6. BR01 blocked: generate payment → 403', r.status_code == 403)
with app.app_context():
    pend = Payment.query.filter_by(status='PENDING').first()
if pend:
    r = br_c.patch(f"/api/payments/{pend.id}", json={'status': 'PAID'},
                   headers=auth(br_token))
    check('6b. BR01 blocked: approve/paid payment → 403', r.status_code == 403)

# ── 7. Branch operator cannot modify pricing ────────────────────────────
r = br_c.post('/api/pricing', json={'milkType': 'COW', 'fatRate': 9, 'snfRate': 9,
                                    'effectiveFrom': _date.today().isoformat()},
              headers=auth(br_token))
check('7. BR01 blocked: create pricing → 403', r.status_code == 403)

# ── 8. Farmer cannot access Admin APIs ──────────────────────────────────
for path in ('/api/dashboard', '/api/collections', '/api/payments',
             '/api/pricing', '/api/branches', '/api/reports?type=collection',
             '/api/audit', '/api/settings', '/api/admin/grievances'):
    r = farmer_c.get(path, headers=auth(f_token))
    check(f'8. farmer blocked: {path.split("?")[0]} → 403', r.status_code == 403,
          f"(status={r.status_code})")

# ── 9. Invalid JWT rejected ─────────────────────────────────────────────
r = farmer_c.get('/api/farmer/me', headers={'Authorization': 'Bearer not.a.valid.jwt'})
check('9. invalid JWT → 401', r.status_code == 401, f"(status={r.status_code})")

# ── 10. Expired JWT rejected ────────────────────────────────────────────
with app.app_context():
    from flask_jwt_extended import create_access_token
    from backend.auth import hash_password  # noqa: F401 (ensure auth importable)
    user = User.query.filter_by(role='FARMER', farmer_id=farmer_id).first()
    expired_token = create_access_token(
        identity=json.dumps({'uid': user.id, 'role': 'FARMER',
                             'branchId': user.branch_id, 'farmerId': user.farmer_id}),
        expires_delta=timedelta(seconds=-60))
r = farmer_c.get('/api/farmer/me', headers=auth(expired_token))
check('10. expired JWT → 401', r.status_code == 401, f"(status={r.status_code})")

# ── 11. Inactive user cannot log in ─────────────────────────────────────
with app.app_context():
    inact_farmer = next(f for f in Farmer.query.all() if f.status != 'ACTIVE')
    inact_email = inact_farmer.email
    inact_mobile = inact_farmer.mobile
t, r = login(farmer_c, inact_email, inact_mobile, 'FARMER')
check('11. inactive farmer cannot log in', t is None and r.status_code == 403,
      f"(status={r.status_code})")

# ── 12. Locked user cannot log in ───────────────────────────────────────
with app.app_context():
    lock_user = User.query.filter_by(role='BRANCH_OPERATOR').first()
    lock_user.failed_attempts = 6
    lock_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    lock_username = lock_user.username
    lock_phone = lock_user.phone
    db.session.commit()
t, r = login(br_c, lock_username, lock_phone, 'BRANCH_OPERATOR')
check('12. locked user cannot log in', t is None and r.status_code == 429,
      f"(status={r.status_code})")
# unlock for later tests
with app.app_context():
    lock_user = User.query.filter_by(role='BRANCH_OPERATOR').first()
    lock_user.locked_until = None
    lock_user.failed_attempts = 0
    db.session.commit()

# ── 13. Duplicate farmer account prevented (unique farmer_code) ─────────
with app.app_context():
    from sqlalchemy.exc import IntegrityError
    try:
        dup = Farmer(farmer_code=farmer_code, name='Dup', mobile='9999999999',
                     milk_type='COW', branch_id=1, status='ACTIVE')
        db.session.add(dup)
        db.session.flush()
        db.session.rollback()
        dup_prevented = False
    except IntegrityError:
        db.session.rollback()
        dup_prevented = True
check('13. duplicate farmer_code rejected at DB level', dup_prevented)

# ── 14. Duplicate payment prevented ─────────────────────────────────────
# Use a FRESH farmer (no seed payments) so the first generation succeeds.
# Created through the API (also proves the farmer-creation audit trail).
r = admin_c.post('/api/farmers', json={'name': 'Payment Test Farmer', 'mobile': '9911111111',
                                        'milkType': 'COW', 'branchId': 1},
                  headers=auth(admin_token))
fresh_body = r.get_json().get('farmer', {})
fresh_code = fresh_body.get('farmerCode')
check('14a-1. admin registers a new farmer', r.status_code == 201, f"({fresh_code})")
r = admin_c.post(f'/api/farmers/{fresh_code}/verify', json={'action': 'approve'},
                  headers=auth(admin_token))
check('14a-2. admin verifies the new farmer', r.status_code == 200)
with app.app_context():
    fresh_id = Farmer.query.filter_by(farmer_code=fresh_code).first().id
period_start = (_date.today() - timedelta(days=3)).isoformat()
period_end = _date.today().isoformat()
r = br_c.post('/api/collections', json={'farmerId': fresh_id, 'quantity': 8, 'fat': 4.0, 'snf': 8.5,
                                        'shift': 'MORNING'}, headers=auth(br_token))
check('14a0. seed collection for fresh farmer', r.status_code == 201)
r = admin_c.post('/api/payments', json={
    'periodStart': period_start, 'periodEnd': period_end,
    'farmerIds': [fresh_id],
}, headers=auth(admin_token))
first_body = r.get_json()
check('14a. first payment generation', r.status_code == 201,
      f"(count={first_body.get('count')}, message={first_body.get('message', '')[:80]})")
r = admin_c.post('/api/payments', json={
    'periodStart': period_start, 'periodEnd': period_end,
    'farmerIds': [fresh_id],
}, headers=auth(admin_token))
check('14b. duplicate payment for same period rejected',
      r.status_code in (404, 409), f"(status={r.status_code}, {r.get_json().get('error', '')[:80]})")
with app.app_context():
    dup_pays = Payment.query.filter_by(farmer_id=fresh_id,
                                       period_start=datetime.strptime(period_start, '%Y-%m-%d').date()).count()
    check('14c. no second payment created', dup_pays <= 1, f"({dup_pays})")

# ── 15. Collection amount computed by backend ───────────────────────────
with app.app_context():
    rates = RateMaster.query.filter_by(milk_type=farmer.milk_type, status='ACTIVE').all()
    active_rate = rates[0]
    expected_rate = round(4.2 * active_rate.fat_rate + 8.5 * active_rate.snf_rate, 2)
r = br_c.post('/api/collections', json={
    'farmerId': farmer_id, 'quantity': 10.0, 'fat': 4.2, 'snf': 8.5,
    'shift': 'MORNING', 'amount': 1.0,  # client lies — must be ignored
    'ratePerLiter': 1.0,  # client lies — must be ignored
    'idempotencyKey': 'sec-test-001',
}, headers=auth(br_token))
coll = r.get_json().get('collection', {})
check('15a. collection accepted', r.status_code == 201)
check('15b. server-computed rate (client rate ignored)',
      coll.get('ratePerLiter') == expected_rate,
      f"(got {coll.get('ratePerLiter')}, expected {expected_rate})")
check('15c. server-computed amount (client amount ignored)',
      coll.get('amount') == round(expected_rate * 10.0, 2),
      f"(got {coll.get('amount')}, expected {round(expected_rate * 10.0, 2)})")
check('15d. collection carries quality grade', 'qualityGrade' in coll)

# ── 16. Pricing changes do NOT alter historical collections ─────────────
with app.app_context():
    hist = db.session.get(Collection, coll['id'])
    hist_amount = hist.amount
    hist_rate = hist.rate_per_liter
r = admin_c.post('/api/pricing', json={'milkType': farmer.milk_type, 'fatRate': 99, 'snfRate': 99,
                                       'effectiveFrom': _date.today().isoformat()},
                 headers=auth(admin_token))
check('16a. admin creates new rate', r.status_code == 201)
with app.app_context():
    hist2 = db.session.get(Collection, coll['id'])
    check('16b. historical amount unchanged after pricing change',
          hist2.amount == hist_amount and hist2.rate_per_liter == hist_rate,
          f"(amount {hist2.amount}=={hist_amount}, rate {hist2.rate_per_liter}=={hist_rate})")

# ── 17. Important actions create audit logs ─────────────────────────────
r = admin_c.get('/api/audit?per_page=200', headers=auth(admin_token))
entities = [a['entity'] for a in r.get_json().get('logs', [])]
check('17a. audit log contains Collection action', any(e == 'Collection' for e in entities))
check('17b. audit log contains Payment action', any(e == 'Payment' for e in entities))
check('17c. audit log contains RateMaster action', any(e == 'RateMaster' for e in entities))
check('17d. audit log contains Farmer action', any(e == 'Farmer' for e in entities))

# ── Bonus: farmer ledger drives the passbook ────────────────────────────
r = farmer_c.get('/api/farmer/me/passbook?per_page=100', headers=auth(f_token))
pb = r.get_json()
check('L1. passbook returns entries', pb.get('total', 0) > 0, f"({pb.get('total')} entries)")
check('L2. passbook entries are ledger-backed (entryType present)',
      all('entryType' in e for e in pb.get('entries', [])))
with app.app_context():
    from backend.models import FarmerLedgerEntry
    led = FarmerLedgerEntry.query.filter_by(farmer_id=farmer_id).count()
    check('L3. ledger rows exist for farmer', led > 0, f"({led})")

# ── Bonus: admin grievance management ───────────────────────────────────
r = admin_c.get('/api/admin/grievances', headers=auth(admin_token))
check('G1. admin lists grievances', r.status_code == 200 and 'summary' in r.get_json())
r = br_c.get('/api/admin/grievances', headers=auth(br_token))
check('G2. branch operator blocked from admin grievances → 403', r.status_code == 403)

print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
