"""
Shree Milk Bank — Ledger Flow Verification
==========================================
Proves the end-to-end financial chain:
  collection (MILK_EARNING credit) → payment sheet → APPROVED → PAID
  (PAYMENT debit) → running balance → farmer passbook shows both.

Run:  python scripts/check_ledger_flow.py
"""
import os
import sys
from datetime import date, timedelta

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DB_PATH = os.path.join(ROOT, 'instance', 'test_ledger_flow.db')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ['DATABASE_URL'] = 'sqlite:///' + DB_PATH.replace('\\', '/')

from backend.app import create_app  # noqa: E402

app = create_app('production')

PASS, FAIL = 0, 0


def check(name, cond, extra=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  OK  {name} {extra}')
    else:
        FAIL += 1
        print(f'  FAIL {name} {extra}')


c = app.test_client()


def auth(t):
    return {'Authorization': f'Bearer {t}'}


with app.app_context():
    from backend.seed import seed_database
    seed_database()
    from backend.models import FarmerLedgerEntry  # noqa: F401
    from backend.models import Farmer

r = c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
at = r.get_json()['token']
r = c.post('/api/auth/login', json={'username': 'BR01', 'password': '9876543210',
                                    'role': 'BRANCH_MANAGER'})
bt = r.get_json()['token']

# Fresh farmer through the API (proves the whole chain from registration)
r = c.post('/api/farmers', json={'name': 'Ledger Test', 'mobile': '9922222222',
                                 'milkType': 'COW', 'branchId': 1}, headers=auth(at))
code = r.get_json()['farmer']['farmerCode']
r = c.post(f'/api/farmers/{code}/verify', json={'action': 'approve'}, headers=auth(at))
check('register + verify farmer', r.status_code == 200, f'({code})')

with app.app_context():
    fid = Farmer.query.filter_by(farmer_code=code).first().id

# 1. Collection → MILK_EARNING credit
r = c.post('/api/collections', json={'farmerId': fid, 'quantity': 10, 'fat': 4.0,
                                     'snf': 8.5, 'shift': 'MORNING'}, headers=auth(bt))
check('collection recorded', r.status_code == 201)
coll_amount = r.get_json()['amount']

with app.app_context():
    from backend.models import FarmerLedgerEntry
    e = FarmerLedgerEntry.query.filter_by(farmer_id=fid, entry_type='MILK_EARNING').all()
    check('ledger: MILK_EARNING credit row', len(e) == 1 and e[0].credit_amount == coll_amount,
          f'(credit {e[0].credit_amount if e else None})')

# 2. Payment sheet → APPROVED → PAID → PAYMENT debit
r = c.post('/api/payments', json={
    'periodStart': (date.today() - timedelta(days=2)).isoformat(),
    'periodEnd': date.today().isoformat(), 'farmerIds': [fid]}, headers=auth(at))
check('payment sheet generated', r.status_code == 201,
      f"({r.get_json().get('message', '')[:60]})")
pid = r.get_json()['payments'][0]['id']

r = c.patch(f'/api/payments/{pid}', json={'status': 'APPROVED'}, headers=auth(at))
check('payment approved', r.status_code == 200)

r = c.patch(f'/api/payments/{pid}', json={'status': 'PAID',
                                          'paymentMethod': 'BANK_TRANSFER'}, headers=auth(at))
check('payment marked PAID', r.status_code == 200,
      f"(method={r.get_json().get('payment', {}).get('paymentMethod')})")

# 3. PAID downgrade must be rejected
r = c.patch(f'/api/payments/{pid}', json={'status': 'APPROVED'}, headers=auth(at))
check('PAID downgrade blocked (400)', r.status_code == 400,
      f"({r.get_json().get('error', '')[:50]})")

with app.app_context():
    from backend.models import FarmerLedgerEntry
    entries = FarmerLedgerEntry.query.filter_by(farmer_id=fid) \
        .order_by(FarmerLedgerEntry.id).all()
    types = [(e.entry_type, e.credit_amount, e.debit_amount, e.running_balance)
             for e in entries]
    check('ledger: both rows present', len(entries) == 2,
          f'({[(t[0], t[1], t[2]) for t in types]})')
    check('ledger: running balance = credit - debit',
          types[-1][3] == round(types[0][1] - types[1][2], 2),
          f'(balance {types[-1][3]})')

# 4. REJECTED correction must reverse the ledger credit
r = c.post('/api/collections', json={'farmerId': fid, 'quantity': 5, 'fat': 4.0,
                                     'snf': 8.5, 'shift': 'EVENING',
                                     'idempotencyKey': 'rej-test-002'}, headers=auth(bt))
rej_coll_id = r.get_json()['collection']['id']
r = c.patch(f'/api/collections/{rej_coll_id}', json={'status': 'REJECTED', 'reason': 'high water'},
             headers=auth(bt))
check('collection corrected to REJECTED', r.status_code == 200)
with app.app_context():
    from backend.models import FarmerLedgerEntry
    rej_entries = FarmerLedgerEntry.query.filter_by(
        farmer_id=fid, source_type='Collection', source_id=rej_coll_id).all()
    check('REJECTED collection has NO ledger credit', len(rej_entries) == 0,
          f'({len(rej_entries)} rows)')

# 5. Farmer passbook reflects both rows
with app.app_context():
    farmer_email = Farmer.query.get(fid).email
    farmer_mobile = Farmer.query.get(fid).mobile
r = c.post('/api/auth/login', json={'login_id': code, 'password': farmer_mobile})
login_body = r.get_json()
ft = login_body['token']
# New farmers must change their temporary password before using the portal
check('farmer first login forces password change', login_body.get('mustChangePassword') is True,
      f"(mustChangePassword={login_body.get('mustChangePassword')})")
r = c.post('/api/auth/change-password',
           json={'current_password': farmer_mobile, 'new_password': 'LedgerFarm9'},
           headers=auth(ft))
check('farmer changes temporary password', r.status_code == 200, str(r.status_code))
r = c.post('/api/auth/login', json={'login_id': code, 'password': 'LedgerFarm9'})
ft = r.get_json()['token']
check('farmer login after password change', bool(ft))
r = c.get('/api/farmer/me/passbook?per_page=50', headers=auth(ft))
pb = r.get_json()
entry_types = [e.get('entryType') for e in pb.get('entries', [])]
check('passbook: shows MILK_EARNING + PAYMENT rows',
      'MILK_EARNING' in entry_types and 'PAYMENT' in entry_types, f'({entry_types})')
check('passbook: pending = credit - debit',
      abs(pb['summary']['pendingAmount'] - round(coll_amount - coll_amount, 2)) < 0.01,
      f"(pending {pb['summary']['pendingAmount']})")

print(f"\n=== LEDGER FLOW: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
