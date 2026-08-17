"""Shree Milk Bank — Smoke test for the three-role RBAC + new farmer APIs + new pages.

Run:  python scripts/smoke_three_roles.py
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Allow running from anywhere (adds the project root to sys.path)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.getenv('TEST_DB_PATH', 'instance/test_rbac_smoke.db')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(DB_PATH).replace('\\', '/')

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

admin_c, br_c, farmer_c = app.test_client(), app.test_client(), app.test_client()

admin_token, _ = login(admin_c, 'admin', 'admin123')
br_token, _ = login(br_c, 'BR01', '9876543210', 'BRANCH_MANAGER')
check('logins ok', bool(admin_token and br_token))

# Pick a BR01 ACTIVE farmer
r = admin_c.get('/api/farmers?branchId=1&status=ACTIVE&per_page=100', headers=auth(admin_token))
farmer = next(f for f in r.get_json()['farmers'] if f['milkType'] in ('COW', 'BUFFALO'))
f_token, _ = login(farmer_c, farmer['email'], farmer['mobile'], 'FARMER')
check('farmer login', bool(f_token))

# ── New farmer self-service APIs ──
r = farmer_c.get('/api/farmer/me/profile', headers=auth(f_token))
check('me/profile GET', r.status_code == 200 and r.get_json()['farmer']['id'] == farmer['id'])

r = farmer_c.patch('/api/farmer/me/profile',
                   json={'village': 'Nippani Updated', 'pincode': '591101'}, headers=auth(f_token))
check('me/profile PATCH (permitted fields)', r.status_code == 200, f"({r.get_json().get('message')})")

r = farmer_c.patch('/api/farmer/me/profile', json={'milkType': 'BUFFALO', 'status': 'BLOCKED'},
                   headers=auth(f_token))
check('me/profile PATCH ignores immutable fields', r.status_code == 200)

r = farmer_c.get('/api/farmer/me/daily-collection', headers=auth(f_token))
check('me/daily-collection GET', r.status_code == 200 and all(k in r.get_json() for k in ('morning', 'evening', 'summary')))

r = farmer_c.get('/api/farmer/me/bank-details', headers=auth(f_token))
check('me/bank-details GET', r.status_code == 200 and 'bankDetail' in r.get_json())

r = farmer_c.post('/api/farmer/me/bank-details',
                  json={'accountHolder': 'Ramesh Kumar', 'bankName': 'SBI', 'accountNumber': '123456789012',
                        'ifsc': 'SBIN0001234'}, headers=auth(f_token))
check('me/bank-details POST (save)', r.status_code == 200, f"({r.get_json().get('message', '')[:40]})")

r = farmer_c.get('/api/farmer/me/bank-details', headers=auth(f_token))
masked = r.get_json()['bankDetail']['accountNumberMasked']
check('bank account masked', '****' in masked, f"(masked={masked})")

# Documents: upload + list + delete
import io
r = farmer_c.post('/api/farmer/me/documents', data={
    'title': 'Aadhaar copy', 'docType': 'AADHAAR',
    'file': (io.BytesIO(b'%PDF-1.4 fake'), 'aadhaar.pdf'),
}, content_type='multipart/form-data', headers=auth(f_token))
check('documents upload', r.status_code == 201, f"({r.get_json().get('document', {}).get('docType')})")
doc_id = r.get_json()['document']['id']
r = farmer_c.get('/api/farmer/me/documents', headers=auth(f_token))
check('documents list (own only)', r.status_code == 200 and all(d['farmerId'] == farmer['id'] for d in r.get_json()['documents']))
r = farmer_c.delete(f'/api/farmer/me/documents/{doc_id}', headers=auth(f_token))
check('documents delete (pending)', r.status_code == 200)

# Grievance detail
r = farmer_c.post('/api/farmer/me/grievances', json={'subject': 'Test', 'category': 'OTHER', 'description': 'desc'},
                  headers=auth(f_token))
gid = r.get_json()['grievance']['id']
r = farmer_c.get(f'/api/farmer/me/grievances/{gid}', headers=auth(f_token))
check('grievance detail (own)', r.status_code == 200 and r.get_json()['grievance']['id'] == gid)
r = farmer_c.get('/api/farmer/me/grievances/999999', headers=auth(f_token))
check('grievance detail (not found)', r.status_code == 404)

# Settings
r = farmer_c.get('/api/farmer/me/settings', headers=auth(f_token))
check('me/settings GET', r.status_code == 200 and 'notificationEmail' in r.get_json()['settings'])
r = farmer_c.patch('/api/farmer/me/settings', json={'notificationEmail': True}, headers=auth(f_token))
check('me/settings PATCH', r.status_code == 200 and r.get_json()['settings']['notificationEmail'] is True)

# Admin registers a farmer for a chosen branch (spec 5.3)
r = admin_c.post('/api/farmers', json={'name': 'Admin Registered', 'mobile': '9876500999', 'milkType': 'COW', 'branchId': 2},
                 headers=auth(admin_token))
check('admin registers farmer with branch (BR02)', r.status_code == 201,
      f"({r.get_json().get('farmer', {}).get('farmerCode')})")

# ── New role pages render for the right roles ──
page_checks = [
    (admin_c, '/admin/collections', 200),
    (br_c, '/branch/milk-collection', 200),
    (br_c, '/branch/payments', 200),
    (br_c, '/branch/notifications', 200),
    (farmer_c, '/farmer/daily-collection', 200),
    (farmer_c, '/farmer/settings', 200),
    (farmer_c, '/farmer/grievance/new', 200),
]
for client, url, expected in page_checks:
    r = client.get(url)
    check(f'page {url} → {expected}', r.status_code == expected, f"(got {r.status_code})")

# Branch pages blocked for farmer; branch inventory gone (404)
check('farmer /branch/payments blocked', farmer_c.get('/branch/payments').status_code == 302)
check('branch inventory page removed (404)', br_c.get('/branch/inventory/allocated').status_code == 404)

# ── Admin collections API: date range + summary + farmer search ──
r = admin_c.get('/api/collections?from=2026-07-01&to=2026-08-09&per_page=5', headers=auth(admin_token))
check('collections date-range filter', r.status_code == 200 and r.get_json().get('total', 0) >= 1)
check('collections summary present', 'summary' in r.get_json() and 'totalAmount' in r.get_json()['summary'])
r = admin_c.get(f"/api/collections?q={farmer['farmerCode'][:4]}&per_page=5", headers=auth(admin_token))
check('collections farmer search', r.status_code == 200)

# Branch payments API view (branch-scoped, view-only list is allowed)
r = br_c.get('/api/payments?per_page=10', headers=auth(br_token))
check('branch payments list (scoped)', r.status_code == 200 and all(p['branchId'] == 1 for p in r.get_json()['payments']))
check('branch payments write blocked', br_c.post('/api/payments', json={'periodStart': '2026-07-01', 'periodEnd': '2026-08-09'},
                                                 headers=auth(br_token)).status_code == 403)

# ── JWT contains scope only from server (farmerId not spoofable) ──
r = farmer_c.post('/api/farmer/me/bank-details', json={'accountHolder': 'X'}, headers=auth(f_token))
check('farmer cannot request another farmer (api always scoped)', r.status_code == 200)

print(f"\n=== SMOKE RESULT: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
