"""Shree Milk Bank — Farmer Portal & Role Isolation tests.

Covers:
  - Farmer login (email + mobile)
  - Farmer self-service APIs scoped to the JWT farmer
  - Farmer isolation: cannot view other farmers / branch / admin data
  - Branch isolation: BR01 vs BR02
  - Milk collection → farmer notification flow
  - Duplicate collection prevention (idempotency key)
  - Collection correction (PATCH) + re-notification
  - Page-level URL access control for all three roles
  - Grievance create/list (own only)
  - Admin unaffected by all hardening

Each role uses its own test client so the login cookie never leaks across
requests (the page blueprint resolves the user from the cookie first).

Run:  python test_farmer_portal.py
"""
import os
import sys
from datetime import date as _date

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.getenv('TEST_DB_PATH', 'instance/test_farmer_portal.db')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(DB_PATH).replace('\\', '/')
# Production-mode validation requires secrets — tests supply throwaway ones.
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-prod-mode-checks')
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key-for-prod-mode-checks')

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
    print("Seeded.\n")

# ── Separate clients: one identity per client ──
admin_c = app.test_client()
br_c = app.test_client()
br2_c = app.test_client()
farmer_c = app.test_client()

# ══════════ Logins ══════════
admin_token, _ = login(admin_c, 'admin', 'admin123')
check('admin login', bool(admin_token))
br_token, _ = login(br_c, 'BR01', '9876543210', 'BRANCH_MANAGER')
check('branch BR01 login', bool(br_token))
br2_token, _ = login(br2_c, 'BR02', '9123456780', 'BRANCH_MANAGER')
check('branch BR02 login', bool(br2_token))

# Find a BR01 ACTIVE farmer with a priced milk type (COW/BUFFALO — MIXED
# farmers have no active rate card, so the collection-flow checks need a
# farmer whose rate is known).
r = admin_c.get('/api/farmers?branchId=1&status=ACTIVE&per_page=100', headers=auth(admin_token))
br1_farmers = [f for f in r.get_json()['farmers'] if f['branchId'] == 1]
priced = next(f for f in br1_farmers if f['milkType'] in ('COW', 'BUFFALO'))
farmer = priced
farmer_email = farmer['email']
farmer_mobile = farmer['mobile']
farmer_id = farmer['id']
farmer_code = farmer['farmerCode']
check('seed farmer found', bool(farmer_email and farmer_mobile), f"({farmer_code} {farmer['milkType']})")

f_token, r = login(farmer_c, farmer_email, farmer_mobile, 'FARMER')
check('farmer login (email + mobile)', bool(f_token), f"(status={r.status_code})")

# Another farmer (same branch) for isolation tests
farmer2_id = next(f for f in br1_farmers if f['id'] != farmer_id)['id']

# ══════════ Farmer dashboard API ══════════
r = farmer_c.get('/api/farmer/me', headers=auth(f_token))
me = r.get_json().get('farmer', {})
check('farmer/me: own profile', r.status_code == 200 and me.get('id') == farmer_id
      and me.get('farmerCode') == farmer_code)

r = farmer_c.get('/api/farmer/me/dashboard', headers=auth(f_token))
d = r.get_json()
check('farmer/me/dashboard: 200', r.status_code == 200)
check('farmer/me/dashboard: own farmer', d.get('farmer', {}).get('id') == farmer_id)
check('farmer/me/dashboard: keys', all(k in d for k in ('today', 'totals', 'payment', 'recentCollections', 'notifications')))

# ══════════ Farmer collections (own only) ══════════
r = farmer_c.get('/api/farmer/me/collections?per_page=100', headers=auth(f_token))
colls = r.get_json()
check('farmer collections: 200', r.status_code == 200)
own_ids = {cl['farmerId'] for cl in colls.get('collections', [])}
check('farmer collections: own farmer only', all(fid == farmer_id for fid in own_ids),
      f"({len(colls.get('collections', []))} rows)")

# Tamper attempt: request another farmer's records via query param
r = farmer_c.get(f'/api/farmer/me/collections?farmerId={farmer2_id}&per_page=100', headers=auth(f_token))
tamper_ids = {cl['farmerId'] for cl in r.get_json().get('collections', [])}
check('farmer collections: farmerId param ignored', all(fid == farmer_id for fid in tamper_ids))

# Shift filter
r = farmer_c.get('/api/farmer/me/collections?shift=MORNING', headers=auth(f_token))
shifts = {cl['shift'] for cl in r.get_json().get('collections', [])}
check('farmer collections: shift filter works', all(s == 'MORNING' for s in shifts))

# ══════════ Passbook ══════════
r = farmer_c.get('/api/farmer/me/passbook?per_page=100', headers=auth(f_token))
pb = r.get_json()
check('passbook: 200', r.status_code == 200)
check('passbook: summary present', 'summary' in pb and 'totalQuantity' in pb['summary'])
check('passbook: entries own only', all(e['farmerId'] == farmer_id for e in pb.get('entries', [])))
check('passbook: balance present', all('balance' in e for e in pb.get('entries', [])))

# ══════════ Payments (own only) ══════════
r = farmer_c.get('/api/farmer/me/payments?per_page=100', headers=auth(f_token))
pays = r.get_json()
check('farmer payments: 200', r.status_code == 200)
check('farmer payments: own farmer only', all(p['farmerId'] == farmer_id for p in pays.get('payments', [])))
check('farmer payments: summary', 'summary' in pays)

# ══════════ Notifications (own only) ══════════
r = farmer_c.get('/api/farmer/me/notifications', headers=auth(f_token))
check('farmer notifications: 200', r.status_code == 200 and 'unreadCount' in r.get_json())

# ══════════ Farmer isolation: staff endpoints blocked ══════════
check('farmer blocked: /api/farmers list', farmer_c.get('/api/farmers', headers=auth(f_token)).status_code == 403)
check('farmer blocked: /api/farmers/stats', farmer_c.get('/api/farmers/stats', headers=auth(f_token)).status_code == 403)
check('farmer blocked: /api/farmers/<code>', farmer_c.get(f'/api/farmers/{farmer_code}', headers=auth(f_token)).status_code == 403)
check('farmer blocked: /api/farmers PATCH',
      farmer_c.patch(f'/api/farmers/{farmer_code}', json={'village': 'X'}, headers=auth(f_token)).status_code == 403)
check('farmer blocked: /api/collections', farmer_c.get('/api/collections', headers=auth(f_token)).status_code == 403)
check('farmer blocked: /api/payments', farmer_c.get('/api/payments', headers=auth(f_token)).status_code == 403)
check('farmer blocked: /api/dashboard', farmer_c.get('/api/dashboard', headers=auth(f_token)).status_code == 403)
check('farmer blocked: /api/reports', farmer_c.get('/api/reports?type=collection', headers=auth(f_token)).status_code == 403)
check('farmer blocked: /api/farmers export', farmer_c.get('/api/farmers/export', headers=auth(f_token)).status_code == 403)
check('farmer blocked: collection create', farmer_c.post('/api/collections', json={'farmerId': farmer_id, 'quantity': 10},
                                                         headers=auth(f_token)).status_code == 403)

# ══════════ Page-level URL access control ══════════
anon_c = app.test_client()
r = anon_c.get('/admin/dashboard')
check('anonymous /admin/dashboard → login redirect', r.status_code == 302)
r = farmer_c.get('/admin/dashboard')
check('farmer /admin/dashboard → unauthorized redirect', r.status_code == 302,
      f"(→ {r.headers.get('Location', '')})")
r = farmer_c.get('/branch/dashboard')
check('farmer /branch/dashboard → unauthorized redirect', r.status_code == 302)
r = farmer_c.get('/farmer/dashboard')
check('farmer /farmer/dashboard → 200', r.status_code == 200)
r = br_c.get('/farmer/dashboard')
check('branch user /farmer/dashboard → unauthorized redirect', r.status_code == 302)
r = br_c.get('/admin/dashboard')
check('branch user /admin/dashboard → unauthorized redirect', r.status_code == 302)
r = admin_c.get('/admin/dashboard')
check('admin /admin/dashboard → 200', r.status_code == 200)
r = admin_c.get('/branch/dashboard')
check('admin can preview branch dashboard', r.status_code == 200)
r = admin_c.get('/farmer/dashboard')
check('admin /farmer/dashboard → unauthorized redirect', r.status_code == 302)

# ══════════ Branch isolation (BR01 vs BR02) ══════════
r = br_c.get('/api/farmers?branchId=2', headers=auth(br_token))
check('BR01 farmers list: own branch only', all(f['branchId'] == 1 for f in r.get_json()['farmers']),
      f"({len(r.get_json()['farmers'])} rows)")
r = br2_c.get('/api/farmers?branchId=2', headers=auth(br2_token))
check('BR02 farmers list: own branch only', all(f['branchId'] == 2 for f in r.get_json()['farmers']))

br2_farmer = next(f for f in admin_c.get('/api/farmers?branchId=2&per_page=100', headers=auth(admin_token))
                  .get_json()['farmers'] if f['status'] == 'ACTIVE')
check('BR01 blocked: collect for BR02 farmer',
      br_c.post('/api/collections', json={'farmerId': br2_farmer['id'], 'quantity': 15},
                headers=auth(br_token)).status_code == 403)
check('BR01 blocked: view BR02 farmer', br_c.get(f"/api/farmers/{br2_farmer['farmerCode']}",
                                                 headers=auth(br_token)).status_code == 403)

# ══════════ Milk collection → farmer notification flow ══════════
# Expected price uses the active rate card for the farmer's milk type.
_rates = admin_c.get('/api/pricing', headers=auth(admin_token)).get_json()
_active_rate = next(rr for rr in (_rates.get('rates') or _rates.get('rateMasters') or [])
                    if rr['milkType'] == farmer['milkType'] and rr['status'] == 'ACTIVE')
_expected_rate = round(4.2 * _active_rate['fatRate'] + 8.5 * _active_rate['snfRate'], 2)

before = farmer_c.get('/api/farmer/me/notifications', headers=auth(f_token)).get_json()['unreadCount']
payload = {
    'farmerId': farmer_id, 'quantity': 12.5, 'fat': 4.2, 'snf': 8.5,
    'shift': 'EVENING', 'temperature': 28.4,
    'idempotencyKey': 'test-key-001',
}
r = br_c.post('/api/collections', json=payload, headers=auth(br_token))
coll = r.get_json().get('collection', {})
check('BR01 records collection for own farmer', r.status_code == 201,
      f"(receipt={r.get_json().get('receipt')}, amount={r.get_json().get('amount')})")
check('collection: correct branch', coll.get('branchId') == 1)
check('collection: linked farmer', coll.get('farmerId') == farmer_id)
check('collection: server-computed amount', coll.get('amount') == round(_expected_rate * 12.5, 2),
      f"(rate={coll.get('ratePerLiter')} expected={_expected_rate})")
check('collection: rate per liter matches formula',
      coll.get('ratePerLiter') == _expected_rate)

# Farmer notification created
r = farmer_c.get('/api/farmer/me/notifications', headers=auth(f_token))
titles = [n['title'] for n in r.get_json()['notifications']]
check('farmer notified: "New Milk Collection"', any('New Milk Collection' in t for t in titles),
      f"(unread {before}→{r.get_json()['unreadCount']})")

# Duplicate prevention: same idempotency key → 409
r = br_c.post('/api/collections', json=payload, headers=auth(br_token))
check('duplicate submission rejected (idempotency)', r.status_code == 409,
      f"(status={r.status_code})")
r = farmer_c.get('/api/farmer/me/collections?per_page=100', headers=auth(f_token))
dup = [cl for cl in r.get_json()['collections'] if cl['receiptNo'] == coll['receiptNo']]
check('no duplicate record created', len(dup) == 1)

# Dashboard reflects the new collection
r = farmer_c.get('/api/farmer/me/dashboard', headers=auth(f_token))
latest = (r.get_json().get('recentCollections') or [])[0]
check('dashboard shows new collection', latest and latest['receiptNo'] == coll['receiptNo'])

# ══════════ Collection correction (PATCH) ══════════
r = br_c.patch(f"/api/collections/{coll['id']}", json={'quantity': 12.3, 'reason': 'measurement correction'},
               headers=auth(br_token))
updated = r.get_json().get('collection', {})
check('BR01 corrects collection', r.status_code == 200 and updated['quantity'] == 12.3)
check('correction re-priced server-side', updated['amount'] == round(_expected_rate * 12.3, 2),
      f"(amount={updated.get('amount')})")
check('correction status = CORRECTED', updated['status'] == 'CORRECTED')
# Farmer sees corrected value + update notification
r = farmer_c.get('/api/farmer/me/dashboard', headers=auth(f_token))
latest = (r.get_json().get('recentCollections') or [])[0]
check('farmer sees corrected quantity', latest['quantity'] == 12.3)
r = farmer_c.get('/api/farmer/me/notifications', headers=auth(f_token))
titles = [n['title'] for n in r.get_json()['notifications']]
check('farmer notified: "Collection Updated"', any('Collection Updated' in t for t in titles))
# BR02 cannot correct BR01 collection
check('BR02 blocked: correct BR01 collection',
      br2_c.patch(f"/api/collections/{coll['id']}", json={'quantity': 1},
                  headers=auth(br2_token)).status_code == 403)

# ══════════ Grievance ══════════
r = farmer_c.post('/api/farmer/me/grievances', json={
    'subject': 'Payment not received', 'category': 'PAYMENT',
    'description': 'My payment for last fortnight has not arrived.',
}, headers=auth(f_token))
check('farmer creates grievance', r.status_code == 201, f"({r.get_json().get('grievance', {}).get('grievanceCode')})")
r = farmer_c.get('/api/farmer/me/grievances', headers=auth(f_token))
check('farmer lists own grievances', r.status_code == 200 and len(r.get_json()['grievances']) >= 1)
check('grievance scoped to own farmer', all(g['farmerId'] == farmer_id for g in r.get_json()['grievances']))

# ══════════ Admin unaffected ══════════
r = admin_c.get('/api/dashboard', headers=auth(admin_token))
check('admin dashboard API works', r.status_code == 200 and 'kpis' in r.get_json())
r = admin_c.get('/api/farmers?per_page=5', headers=auth(admin_token))
check('admin sees all farmers', r.status_code == 200 and r.get_json()['total'] >= 10)
r = admin_c.get('/api/branches', headers=auth(admin_token))
check('admin sees all branches', r.status_code == 200 and len(r.get_json()['branches']) >= 5)

_today = _date.today().isoformat()
r = admin_c.get(f'/api/collections?date={_today}', headers=auth(admin_token))
check('admin collection list works', r.status_code == 200)
r = admin_c.get(f'/api/collections?date={_today}&farmerId={farmer_id}', headers=auth(admin_token))
check('admin sees the new collection', any(cl['receiptNo'] == coll['receiptNo'] for cl in r.get_json()['collections']))

# ══════════ Login page renders (no template syntax errors) ══════════
r = anon_c.get('/login')
check('login page renders', r.status_code == 200)

print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
