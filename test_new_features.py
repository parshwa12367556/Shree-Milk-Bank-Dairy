"""Test script for all newly implemented features (audit, verification workflow,
procurement module, inventory movements, expenses/P&L, exports, vehicle extras,
bank editing, SMS/email settings)."""
import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

# Fresh database — path is configurable via TEST_DB_PATH so the suite can
# run against a scratch DB while a dev server holds the main smart_dairy.db.
# Default is an ISOLATED test database; the real smart_dairy.db is NEVER
# touched by this suite.
DB_PATH = os.getenv('TEST_DB_PATH', 'smart_dairy_test.db')

# Safety assertion: destructive tests must never point at the production DB.
PROD_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'smart_dairy.db'))
if os.path.abspath(DB_PATH) == PROD_DB_PATH:
    raise RuntimeError(
        "Refusing to run destructive tests against the production database "
        f"({PROD_DB_PATH}). Set TEST_DB_PATH to an isolated test database."
    )

if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except PermissionError:
        raise SystemExit(
            f"Cannot remove test database {DB_PATH}: file is locked by another process. "
            "Close any process holding it and re-run."
        )
    print(f"Removed old database ({DB_PATH})")

# Point the app at the isolated database BEFORE importing the app factory.
os.environ['DATABASE_URL'] = 'sqlite:///' + DB_PATH.replace('\\', '/')

from backend.app import create_app
from backend.app import db as _db

app = create_app()

PASS, FAIL = 0, 0


def check(name, cond, extra=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK  {name} {extra}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {extra}")


def login(client, username, password, branch_id=None):
    r = client.post('/api/auth/login', json={
        'username': username, 'password': password, 'branch_id': branch_id})
    return r.get_json().get('token'), r.get_json()


def auth(token):
    return {'Authorization': f'Bearer {token}'}


with app.app_context():
    from backend.seed import seed_database
    seed_database()
    print("Seeded.\n")

with app.test_client() as c:
    # ── Auth ──
    admin_token, admin_data = login(c, 'admin', 'admin123')
    check('admin login', bool(admin_token))
    br_token, br_data = login(c, 'BR01', '9876543210')
    check('branch login', bool(br_token))

    # ── Audit logging on login ──
    r = c.get('/api/audit', headers=auth(admin_token))
    logs = r.get_json().get('logs', [])
    check('audit: login recorded', any(l['action'] == 'LOGIN_SUCCESS' for l in logs),
          f'({len(logs)} logs)')

    # ── Farmer verification workflow ──
    r = c.get('/api/farmers/stats', headers=auth(admin_token))
    stats = r.get_json()
    check('farmer stats: pending count', stats.get('pendingVerification', 0) >= 1,
          f"(pending={stats.get('pendingVerification')})")

    r = c.get('/api/farmers?status=PENDING_VERIFICATION', headers=auth(admin_token))
    pending = [f for f in r.get_json()['farmers'] if f['status'] == 'PENDING_VERIFICATION']
    check('farmer list: pending filter', len(pending) >= 1, f"({len(pending)})")
    pending_code = pending[0]['farmerCode']

    # Aadhaar search
    r = c.get('/api/farmers?per_page=50', headers=auth(admin_token))
    with_aadhaar = [f for f in r.get_json()['farmers'] if f.get('aadhaar')]
    aadhaar = with_aadhaar[0]['aadhaar'] if with_aadhaar else '000000000000'
    r = c.get(f"/api/farmers?q={aadhaar[:6]}", headers=auth(admin_token))
    check('farmer search: by aadhaar', r.get_json()['total'] >= 1,
          f"(query={aadhaar[:6]} → {r.get_json()['total']})")

    # Verify farmer (admin)
    r = c.post(f'/api/farmers/{pending_code}/verify', headers=auth(admin_token))
    check('verify farmer (admin)', r.status_code == 200, f"({r.get_json().get('message', '')[:40]})")
    r2 = c.post(f'/api/farmers/{pending_code}/verify', headers=auth(admin_token))
    check('verify already-active rejected', r2.status_code == 400)

    # Branch manager CANNOT verify
    r = c.post(f'/api/farmers/BR03011/verify', headers=auth(br_token))
    check('verify blocked for branch manager', r.status_code == 403)

    # Admin CAN create farmers (must choose a branch — spec 5.2/5.3)
    r = c.post('/api/farmers', json={'name': 'X', 'mobile': '9999999999', 'milkType': 'COW'},
               headers=auth(admin_token))
    check('admin needs branch to register farmer', r.status_code == 400)
    r = c.post('/api/farmers', json={'name': 'X', 'mobile': '9999999999', 'milkType': 'COW', 'branchId': 1},
               headers=auth(admin_token))
    check('admin registers farmer with branch', r.status_code == 201,
          f"({r.get_json().get('farmer', {}).get('farmerCode')})")

    # Branch manager registers farmer → PENDING_VERIFICATION
    r = c.post('/api/farmers', json={
        'name': 'New Farmer Test', 'mobile': '9876543211', 'milkType': 'COW',
        'village': 'Nippani', 'aadhaar': '123456789012',
        'accountNumber': '111122223333', 'ifsc': 'SBIN0012345', 'bankName': 'SBI',
    }, headers=auth(br_token))
    body = r.get_json()
    check('branch registers farmer', r.status_code == 201, f"({body.get('farmer', {}).get('farmerCode')})")
    new_code = body['farmer']['farmerCode']
    check('new farmer status pending', body['farmer']['status'] == 'PENDING_VERIFICATION')

    # Bank detail edit (admin)
    r = c.patch(f'/api/farmers/{new_code}', json={'bankName': 'HDFC Bank', 'accountNumber': '9999999999'},
                headers=auth(admin_token))
    check('bank details editable', r.status_code == 200,
          f"(bank={r.get_json().get('farmer', {}).get('bankDetail', {}).get('bankName')})")

    # ── Payments (ACTIVE-only + UTR) ──
    r = c.post('/api/payments', json={
        'periodStart': '2026-07-01', 'periodEnd': '2026-08-03'}, headers=auth(admin_token))
    body = r.get_json()
    check('generate payment sheet', r.status_code == 201, f"({body.get('count')} payments)")
    if body.get('payments'):
        pid = body['payments'][0]['id']
        r = c.patch(f'/api/payments/{pid}', json={'status': 'APPROVED'}, headers=auth(admin_token))
        check('approve payment', r.status_code == 200)
        r = c.patch(f'/api/payments/{pid}', json={'status': 'PAID'}, headers=auth(admin_token))
        paid = r.get_json().get('payment', {})
        check('mark paid + UTR reference', paid.get('status') == 'PAID' and bool(paid.get('reference')),
              f"(ref={paid.get('reference')})")

    # ── Inventory movements ──
    r = c.get('/api/inventory', headers=auth(admin_token))
    items = r.get_json()['items']
    check('inventory list', len(items) >= 1)
    inv_id = items[0]['id']
    r = c.post(f'/api/inventory/{inv_id}/movement', json={'type': 'IN', 'quantity': 100, 'note': 'test'},
               headers=auth(admin_token))
    check('stock IN', r.status_code == 201, f"(stock={r.get_json().get('item', {}).get('stock')})")
    r = c.post(f'/api/inventory/{inv_id}/movement', json={'type': 'ALLOCATE', 'quantity': 10, 'branchId': 1},
               headers=auth(admin_token))
    check('stock ALLOCATE', r.status_code == 201)
    r = c.get('/api/inventory/movements', headers=auth(admin_token))
    check('movement ledger', r.get_json().get('total', 0) >= 2)
    # Branch manager cannot create inventory
    r = c.post('/api/inventory', json={'name': 'x'}, headers=auth(br_token))
    check('inventory create blocked for branch', r.status_code == 403)

    # ── Procurement module ──
    r = c.get('/api/procurement/suppliers', headers=auth(admin_token))
    check('suppliers list', r.get_json().get('suppliers', []) and len(r.get_json()['suppliers']) >= 1)
    r = c.post('/api/procurement/suppliers', json={'name': 'Test Vendor', 'category': 'FEED'},
               headers=auth(admin_token))
    check('create supplier', r.status_code == 201)
    sup_id = r.get_json()['supplier']['id']

    r = c.post('/api/procurement/purchase-orders', json={
        'supplierId': sup_id, 'orderDate': '2026-08-01',
        'items': [{'itemName': 'Test Feed', 'quantity': 100, 'unit': 'kg', 'unitPrice': 50}],
    }, headers=auth(admin_token))
    check('create PO (draft)', r.status_code == 201, f"({r.get_json().get('purchase_order', {}).get('poCode')})")
    po = r.get_json()['purchase_order']
    po_id = po['id']

    r = c.patch(f'/api/procurement/purchase-orders/{po_id}', json={'status': 'PENDING'}, headers=auth(admin_token))
    check('PO submit → PENDING', r.get_json().get('purchase_order', {}).get('status') == 'PENDING')
    r = c.patch(f'/api/procurement/purchase-orders/{po_id}', json={'status': 'APPROVED'}, headers=auth(admin_token))
    check('PO approve', r.get_json().get('purchase_order', {}).get('status') == 'APPROVED')
    r = c.patch(f'/api/procurement/purchase-orders/{po_id}', json={'status': 'RECEIVED'}, headers=auth(admin_token))
    check('PO receive → stock-in', r.get_json().get('purchase_order', {}).get('status') == 'RECEIVED')
    # Test Feed should now exist in inventory with 100 stock
    r = c.get('/api/inventory?q=Test Feed', headers=auth(admin_token))
    feed = [i for i in r.get_json()['items'] if i['name'] == 'Test Feed']
    check('PO items added to inventory', bool(feed) and feed[0]['stock'] == 100,
          f"(stock={feed[0]['stock'] if feed else 0})")

    r = c.post('/api/procurement/vendor-payments', json={'poId': po_id, 'amount': 5000, 'method': 'BANK_TRANSFER'},
               headers=auth(admin_token))
    check('vendor payment', r.status_code == 201)
    r = c.patch(f'/api/procurement/purchase-orders/{po_id}', json={'status': 'COMPLETED'}, headers=auth(admin_token))
    # Full payment auto-completes the PO, so the explicit transition may be a no-op
    check('PO complete after full payment',
          r.status_code == 200 or (r.status_code == 400 and 'COMPLETED' in (r.get_json().get('error') or '')),
          f"(status_code={r.status_code})")
    check('branch blocked from procurement write', c.post('/api/procurement/suppliers', json={'name': 'x'},
                                                          headers=auth(br_token)).status_code == 403)

    # ── Expenses + P&L ──
    r = c.post('/api/expenses', json={'category': 'FEED', 'amount': 2500, 'description': 'test expense',
                                      'expenseDate': '2026-08-01'}, headers=auth(admin_token))
    check('create expense', r.status_code == 201)
    r = c.get('/api/expenses', headers=auth(admin_token))
    check('expense list', r.get_json().get('summary', {}).get('totalAmount', 0) > 0)
    r = c.get('/api/reports?type=expense&from=2026-07-01&to=2026-08-03', headers=auth(admin_token))
    check('expense report', r.get_json().get('summary', {}).get('expenseCount', 0) >= 1)
    r = c.get('/api/reports?type=pnl&from=2026-07-01&to=2026-08-03', headers=auth(admin_token))
    pnl = r.get_json().get('summary', {})
    check('pnl report', 'profit' in pnl and 'revenue' in pnl, f"(rev={pnl.get('revenue')}, costs={pnl.get('totalCosts')})")

    # ── Report CSV export ──
    r = c.get('/api/reports/export?type=collection&from=2026-07-01&to=2026-08-03&format=csv',
              headers=auth(admin_token))
    check('report CSV export', r.status_code == 200 and 'csv' in r.headers.get('Content-Type', ''))
    r = c.get('/api/farmers/export', headers=auth(admin_token))
    check('farmer CSV export', r.status_code == 200 and 'csv' in r.headers.get('Content-Type', ''))

    # ── Dashboard P&L ──
    r = c.get('/api/dashboard', headers=auth(admin_token))
    kpis = r.get_json().get('kpis', {})
    check('dashboard profit kpi', 'profit30d' in kpis, f"(profit30d={kpis.get('profit30d')})")

    # ── Vehicles extras ──
    r = c.post('/api/vehicles', json={
        'vehicleNumber': 'KA-01-TEST-99', 'type': 'TANKER',
        'insuranceNo': 'POL-TEST-1', 'insuranceExpiry': '2027-01-01',
        'lastServiceDate': '2026-07-01', 'nextServiceDate': '2026-10-01', 'gpsStatus': 'ACTIVE',
    }, headers=auth(admin_token))
    v = r.get_json().get('vehicle', {})
    check('vehicle extras saved', r.status_code == 201 and v.get('insuranceNo') == 'POL-TEST-1',
          f"(ins={v.get('insuranceNo')}, gps={v.get('gpsStatus')})")

    # ── Settings SMS/email ──
    r = c.patch('/api/settings', json={'sms_provider': 'MSG91', 'sms_sender_id': 'DAIRY',
                                       'email_smtp_host': 'smtp.gmail.com'}, headers=auth(admin_token))
    s = r.get_json().get('settings', {})
    check('settings sms/email saved', s.get('sms_provider') == 'MSG91' and s.get('email_smtp_host') == 'smtp.gmail.com')

    # ── Audit coverage for new actions ──
    r = c.get('/api/audit', headers=auth(admin_token))
    actions = {l['action'] for l in r.get_json()['logs']}
    check('audit: VERIFY present', 'VERIFY' in actions, f"({sorted(actions)})")
    check('audit: EXPORT present', 'EXPORT' in actions)
    check('audit: PAY present', 'PAY' in actions or 'APPROVE' in actions)

# ═══════════════ Phase 2 round — additional enterprise features ═══════════════

    # ── Farmer verification: reject + resubmit + bank verify ──
    r = c.post('/api/farmers', json={
        'name': 'Reject Test Farmer', 'mobile': '9876500001', 'milkType': 'COW',
        'village': 'Nippani', 'accountNumber': '1122334455', 'ifsc': 'SBIN0011111', 'bankName': 'SBI',
    }, headers=auth(br_token))
    rej_code = r.get_json()['farmer']['farmerCode']
    r = c.post(f'/api/farmers/{rej_code}/verify', json={'action': 'reject', 'reason': 'Aadhaar mismatch'},
               headers=auth(admin_token))
    check('farmer reject with reason', r.status_code == 200 and r.get_json()['farmer']['status'] == 'REJECTED')
    r = c.post(f'/api/farmers/{rej_code}/verify', json={'action': 'reject'}, headers=auth(admin_token))
    check('reject requires reason', r.status_code == 400)
    r = c.post(f'/api/farmers/{rej_code}/resubmit', headers=auth(br_token))
    check('branch resubmits rejected farmer', r.get_json()['farmer']['status'] == 'PENDING_VERIFICATION')
    r = c.post(f'/api/farmers/{rej_code}/resubmit', headers=auth(admin_token))
    check('resubmit blocked for admin', r.status_code == 403)

    # Bank verification
    r = c.post(f'/api/farmers/{new_code}/verify-bank', json={'action': 'verify'}, headers=auth(admin_token))
    check('bank verify', r.status_code == 200)
    r = c.get(f'/api/farmers/{new_code}', headers=auth(admin_token))
    check('bank status VERIFIED', r.get_json()['farmer']['bankDetail'].get('verificationStatus') == 'VERIFIED')

    # Cross-branch isolation: BR02 manager cannot view/edit/resubmit BR01 farmer
    br2_token, _ = login(c, 'BR02', '9123456780')
    check('cross-branch view blocked', c.get(f'/api/farmers/{new_code}', headers=auth(br2_token)).status_code == 403)
    check('cross-branch edit blocked', c.patch(f'/api/farmers/{new_code}', json={'village': 'X'},
                                               headers=auth(br2_token)).status_code == 403)
    check('own-branch edit allowed', c.patch(f'/api/farmers/{rej_code}', json={'village': 'Nippani'},
                                             headers=auth(br_token)).status_code == 200)
    check('milkType null handled', c.post('/api/farmers', json={'name': 'Null Milk', 'mobile': '9876511111',
                                                                'milkType': None}, headers=auth(br_token)).status_code == 400)

    # ── Audit role/branch captured ──
    r = c.get('/api/audit', headers=auth(admin_token))
    logs = r.get_json()['logs']
    admin_login = next((l for l in logs if l['action'] == 'LOGIN_SUCCESS' and l.get('username') == 'admin'), None)
    check('audit: role captured', admin_login and admin_login.get('role') == 'ADMIN')
    br_login = next((l for l in logs if l['action'] == 'LOGIN_SUCCESS' and l.get('username') == 'BR01'), None)
    check('audit: branch role + code captured',
          br_login and br_login.get('role') == 'BRANCH_MANAGER' and br_login.get('branchCode') == 'BR01')

    # ── Supplier GSTIN ──
    r = c.post('/api/procurement/suppliers', json={'name': 'GST Vendor', 'gstin': '27ABCDE1234F1Z5'},
               headers=auth(admin_token))
    check('supplier GSTIN saved', r.get_json()['supplier'].get('gstin') == '27ABCDE1234F1Z5')

    # ── PO receive → GRN + delivery tracking ──
    r = c.post('/api/procurement/purchase-orders', json={
        'supplierId': sup_id, 'orderDate': '2026-08-01',
        'items': [{'itemName': 'GRN Test Item', 'quantity': 20, 'unit': 'nos', 'unitPrice': 10}],
    }, headers=auth(admin_token))
    po2 = r.get_json()['purchase_order']
    for st in ('PENDING', 'APPROVED', 'RECEIVED'):
        r = c.patch(f"/api/procurement/purchase-orders/{po2['id']}", json={'status': st}, headers=auth(admin_token))
    check('PO receive generates GRN', r.get_json()['purchase_order'].get('grnNo', '').startswith('GRN'))
    r = c.patch(f"/api/procurement/purchase-orders/{po2['id']}", json={'deliveryStatus': 'IN_TRANSIT'},
                headers=auth(admin_token))
    check('PO delivery tracking', r.get_json()['purchase_order'].get('deliveryStatus') == 'IN_TRANSIT')

    # ── Inventory allocation ──
    r = c.post(f'/api/inventory/{inv_id}/allocate', json={'branchId': 1, 'quantity': 15},
               headers=auth(admin_token))
    check('allocate to branch', r.status_code == 201)
    r = c.get(f'/api/inventory/{inv_id}/allocations', headers=auth(admin_token))
    check('allocations list', len(r.get_json()['allocations']) >= 1)
    r = c.post(f'/api/inventory/{inv_id}/allocate', json={'branchId': 1, 'quantity': 99999},
               headers=auth(admin_token))
    check('allocate over available blocked', r.status_code == 400)

    # ── New report types + xlsx/pdf export ──
    for rt in ('inventory', 'procurement', 'vehicle', 'employee'):
        r = c.get(f'/api/reports?type={rt}&from=2026-07-01&to=2026-08-03', headers=auth(admin_token))
        check(f'report type {rt}', r.status_code == 200)
    r = c.get('/api/reports/export?type=collection&from=2026-07-01&to=2026-08-03&format=xlsx',
              headers=auth(admin_token))
    check('export xlsx', r.status_code == 200 and 'spreadsheet' in r.headers.get('Content-Type', ''))
    r = c.get('/api/reports/export?type=collection&from=2026-07-01&to=2026-08-03&format=pdf',
              headers=auth(admin_token))
    check('export pdf', r.status_code == 200 and 'pdf' in r.headers.get('Content-Type', ''))

    # ── P&L includes farmer payments ──
    r = c.get('/api/reports?type=pnl&from=2026-07-01&to=2026-08-03', headers=auth(admin_token))
    pnl2 = r.get_json().get('summary', {})
    check('pnl includes farmer payments', 'farmerPayments' in pnl2)

    # ── Vehicle service record ──
    r = c.get('/api/vehicles', headers=auth(admin_token))
    vh = r.get_json()['vehicles'][0]
    r = c.post(f"/api/vehicles/{vh['id']}/service", json={
        'description': 'Oil change', 'cost': 1500, 'odometer': 12000, 'serviceDate': '2026-08-01',
    }, headers=auth(admin_token))
    check('add service record', r.status_code == 201)
    r = c.get(f"/api/vehicles/{vh['id']}/service", headers=auth(admin_token))
    check('service history list', len(r.get_json()['records']) >= 1)

    # ── Employee update + attendance ──
    r = c.get('/api/employees', headers=auth(admin_token))
    emp = r.get_json()['employees'][0]
    r = c.patch(f"/api/employees/{emp['id']}", json={'role': 'ACCOUNTANT', 'salary': 25000}, headers=auth(admin_token))
    check('employee update', r.status_code == 200 and r.get_json()['employee']['role'] == 'ACCOUNTANT')
    r = c.post('/api/employees/attendance', json={'employeeId': emp['id'], 'status': 'PRESENT'},
               headers=auth(admin_token))
    check('mark attendance', r.status_code == 201)
    r = c.get(f"/api/employees/{emp['id']}/attendance", headers=auth(admin_token))
    check('attendance summary', r.get_json().get('summary', {}).get('present', 0) >= 1)

    # ── Notifications auto-created ──
    r = c.get('/api/notifications', headers=auth(admin_token))
    ntypes = {n['type'] for n in r.get_json()['notifications']}
    check('auto notifications (farmer/payment)', 'farmer' in ntypes and 'payment' in ntypes,
          f"({sorted(ntypes)})")

    # ── Backup created + listed ──
    r = c.post('/api/settings/backup', headers=auth(admin_token))
    check('backup created', r.status_code == 200, f"({r.get_json().get('backup', {}).get('filename')})")
    r = c.get('/api/settings/backups', headers=auth(admin_token))
    check('backup list', len(r.get_json()['backups']) >= 1)

    # ── Dashboard analytics ──
    r = c.get('/api/dashboard', headers=auth(admin_token))
    k = r.get_json().get('kpis', {})
    check('dashboard monthly collection', 'monthlyCollection' in k)
    check('dashboard rejected %', 'rejectedPct' in k)
    check('dashboard low stock', 'lowStockCount' in k)

# ═══════════════ Phase 3 — RBAC hardening regression tests ═══════════════

    # ── Procurement: Branch Manager blocked from ALL reads ──
    check('BM blocked: procurement centers', c.get('/api/procurement/centers', headers=auth(br_token)).status_code == 403)
    check('BM blocked: procurement routes', c.get('/api/procurement/routes', headers=auth(br_token)).status_code == 403)
    check('BM blocked: procurement chilling', c.get('/api/procurement/chilling', headers=auth(br_token)).status_code == 403)
    check('BM blocked: suppliers read', c.get('/api/procurement/suppliers', headers=auth(br_token)).status_code == 403)
    check('BM blocked: purchase orders read', c.get('/api/procurement/purchase-orders', headers=auth(br_token)).status_code == 403)
    check('BM blocked: vendor payments read', c.get('/api/procurement/vendor-payments', headers=auth(br_token)).status_code == 403)

    # ── Vehicles: Branch Manager blocked from all writes ──
    check('BM blocked: create vehicle', c.post('/api/vehicles', json={'vehicleNumber': 'KA-99-TEST-00', 'type': 'PICKUP'},
                                               headers=auth(br_token)).status_code == 403)
    vh_list = c.get('/api/vehicles', headers=auth(admin_token)).get_json()['vehicles']
    vh_id = vh_list[0]['id']
    check('BM blocked: update vehicle', c.patch(f'/api/vehicles/{vh_id}', json={'driverName': 'X'},
                                                headers=auth(br_token)).status_code == 403)
    check('BM blocked: delete vehicle', c.delete(f'/api/vehicles/{vh_id}', headers=auth(br_token)).status_code == 403)
    check('BM blocked: add service record', c.post(f'/api/vehicles/{vh_id}/service',
                                                   json={'description': 'x', 'cost': 100},
                                                   headers=auth(br_token)).status_code == 403)

    # ── Employees: Branch Manager blocked from all writes ──
    check('BM blocked: create employee', c.post('/api/employees', json={'name': 'X'},
                                                headers=auth(br_token)).status_code == 403)
    emp_list = c.get('/api/employees', headers=auth(admin_token)).get_json()['employees']
    emp_id = emp_list[0]['id']
    check('BM blocked: update employee', c.patch(f'/api/employees/{emp_id}', json={'salary': 1},
                                                 headers=auth(br_token)).status_code == 403)
    check('BM blocked: mark attendance', c.post('/api/employees/attendance',
                                                json={'employeeId': emp_id, 'status': 'PRESENT'},
                                                headers=auth(br_token)).status_code == 403)

    # ── Reports: Branch Manager scoped to own branch + restricted types ──
    r = c.get('/api/reports?type=collection&from=2026-07-01&to=2026-08-03&branchId=2', headers=auth(br_token))
    coll_branches = {x['branchId'] for x in r.get_json().get('collections', [])}
    check('BM report: own-branch only (branchId=2 ignored)', r.status_code == 200 and coll_branches <= {1},
          f"({coll_branches})")
    for rt in ('pnl', 'branch', 'inventory', 'procurement', 'vehicle', 'employee'):
        check(f'BM blocked: {rt} report', c.get(f'/api/reports?type={rt}&from=2026-07-01&to=2026-08-03',
                                                headers=auth(br_token)).status_code == 403)
    check('BM blocked: export pnl', c.get('/api/reports/export?type=pnl&format=csv',
                                          headers=auth(br_token)).status_code == 403)
    check('BM export: own collection csv', c.get('/api/reports/export?type=collection&format=csv',
                                                 headers=auth(br_token)).status_code == 200)
    # Cross-branch farmer ledger
    all_farmers = c.get('/api/farmers?per_page=100', headers=auth(admin_token)).get_json()['farmers']
    br2_farmer = next((f for f in all_farmers if f['branchId'] == 2), None)
    if br2_farmer:
        check('BM blocked: other-branch farmer ledger',
              c.get(f"/api/reports?type=farmer&farmerId={br2_farmer['id']}&from=2026-07-01&to=2026-08-03",
                    headers=auth(br_token)).status_code == 403)

    # ── List scoping for Branch Manager ──
    r = c.get('/api/vehicles?branchId=2', headers=auth(br_token))
    v = r.get_json()['vehicles']
    check('BM vehicle list: own-branch only', r.status_code == 200 and len(v) >= 1 and all(x['branchId'] == 1 for x in v),
          f"({len(v)} vehicles)")

    r = c.get('/api/employees?branchId=2', headers=auth(br_token))
    e = r.get_json()['employees']
    check('BM employee list: own-branch only', r.status_code == 200 and len(e) >= 1 and all(x['branchId'] == 1 for x in e),
          f"({len(e)} employees)")

    r = c.get('/api/inventory', headers=auth(br_token))
    i = r.get_json()['items']
    check('BM inventory list: own-branch only', r.status_code == 200 and all(x['branchId'] == 1 for x in i),
          f"({len(i)} items)")

    r = c.get('/api/quality', headers=auth(br_token))
    q = r.get_json()
    check('BM quality list: own-branch only', r.status_code == 200 and all(t['branchId'] == 1 for t in q['tests']),
          f"({q['total']} tests)")
    if br2_farmer:
        r = c.get(f"/api/quality?farmerId={br2_farmer['id']}", headers=auth(br_token))
        check('BM quality: other-branch farmer excluded', r.get_json()['total'] == 0)

    r = c.get('/api/rejections', headers=auth(br_token))
    rj = r.get_json()
    check('BM rejections list: own-branch only', r.status_code == 200 and all(x['branchId'] == 1 for x in rj['rejections']),
          f"({rj['total']} rejections)")

    # ── Payments: Branch Manager blocked from ALL payment writes ──
    check('BM blocked: generate payment sheet', c.post('/api/payments',
                                                       json={'periodStart': '2026-07-01', 'periodEnd': '2026-08-03'},
                                                       headers=auth(br_token)).status_code == 403)
    pay_list = c.get('/api/payments', headers=auth(admin_token)).get_json()['payments']
    if pay_list:
        pay_id = pay_list[0]['id']
        check('BM blocked: approve payment', c.patch(f'/api/payments/{pay_id}', json={'status': 'APPROVED'},
                                                     headers=auth(br_token)).status_code == 403)
        check('BM blocked: mark paid', c.patch(f'/api/payments/{pay_id}', json={'status': 'PAID'},
                                               headers=auth(br_token)).status_code == 403)

    # ── Collections: BM forced to own branch (read + write) ──
    new_farmer = next((f for f in all_farmers if f['farmerCode'] == new_code), None)
    if new_farmer and br2_farmer:
        check('BM blocked: collect for other-branch farmer',
              c.post('/api/collections', json={'farmerId': br2_farmer['id'], 'quantity': 20},
                     headers=auth(br_token)).status_code == 403)
    if new_farmer:
        r = c.post('/api/collections', json={'farmerId': new_farmer['id'], 'quantity': 20},
                   headers=auth(br_token))
        check('BM collects own-branch farmer', r.status_code == 201,
              f"(branch={r.get_json().get('collection', {}).get('branchId')})")

    # ── Settings: Branch Manager blocked ──
    check('BM blocked: settings read', c.get('/api/settings', headers=auth(br_token)).status_code == 403)

    # ── Admin unaffected after hardening ──
    check('admin: vehicle create still ok', c.post('/api/vehicles', json={'vehicleNumber': 'KA-55-TEST-77', 'type': 'PICKUP'},
                                                   headers=auth(admin_token)).status_code == 201)
    check('admin: pnl report still ok', c.get('/api/reports?type=pnl&from=2026-07-01&to=2026-08-03',
                                              headers=auth(admin_token)).status_code == 200)

# ═══════════════ Phase 4 — Login hardening (first-login, lockout, OTP reset) ═══════════════

    # ── Role hint validation (login-screen role tabs) ──
    # Common login: the backend detects the role — a role sent by the client
    # is NEVER trusted (it is ignored entirely).
    r = c.post('/api/auth/login', json={'username': 'BR01', 'password': '9876543210', 'role': 'ADMIN'})
    body = r.get_json() or {}
    check('role sent by client is ignored (login succeeds)', r.status_code == 200,
          f'(status={r.status_code})')
    check('role detected from DB (BRANCH_MANAGER, not client role)',
          body.get('user', {}).get('role') == 'BRANCH_MANAGER',
          f"(role={body.get('user', {}).get('role')})")
    check('login response has redirect_url', '/branch/dashboard' == body.get('redirect_url'),
          f"(redirect={body.get('redirect_url')})")
    check('login response has mustChangePassword flag',
          body.get('mustChangePassword') is False)

    # ── Brute-force lockout (BR01) ──
    for _ in range(5):
        c.post('/api/auth/login', json={'username': 'BR01', 'password': 'wrongpass'})
    r = c.post('/api/auth/login', json={'username': 'BR01', 'password': 'wrongpass'})
    check('account locked after 5 failed attempts', r.status_code == 429,
          f"(status={r.status_code})")
    r = c.post('/api/auth/login', json={'username': 'BR01', 'password': '9876543210'})
    check('correct password rejected while locked', r.status_code == 429)

    # Failed logins are audit-logged
    r = c.get('/api/audit', headers=auth(admin_token))
    audit_actions = {l['action'] for l in r.get_json()['logs']}
    check('audit: LOGIN_FAILED recorded', 'LOGIN_FAILED' in audit_actions)
    check('audit: ACCOUNT_LOCKED recorded', 'ACCOUNT_LOCKED' in audit_actions)

    # ── OTP reset (also unlocks the account) ──
    r = c.post('/api/auth/forgot-password', json={'username': 'BR01'})
    otp = r.get_json().get('dev_otp')
    check('forgot-password returns dev OTP', bool(otp), f"(otp={otp})")
    r = c.post('/api/auth/reset-password', json={'login_id': 'BR01MG001', 'otp': '000000', 'new_password': 'Br01newpass9'})
    check('reset rejects wrong OTP', r.status_code == 400)
    r = c.post('/api/auth/reset-password', json={'login_id': 'BR01MG001', 'otp': otp, 'new_password': 'Br01newpass9'})
    check('correct OTP still valid after wrong guess', r.status_code == 200)
    check('reset password via OTP', r.status_code == 200)
    r = c.post('/api/auth/login', json={'login_id': 'BR01MG001', 'password': 'Br01newpass9'})
    check('login with new password works (login_id)', r.status_code == 200)
    r = c.post('/api/auth/login', json={'login_id': 'br01op001', 'password': 'Br01newpass9'})
    check('login_id is case-insensitive', r.status_code == 200)
    r = c.post('/api/auth/login', json={'login_id': 'BR01MG001', 'password': '9876543210'})
    check('old phone password no longer works', r.status_code == 401)

    # ── First-login must-change-password flow (new branch manager) ──
    r = c.post('/api/branches', json={'name': 'Login Test Branch', 'code': 'BR99', 'phone': '9999999999'},
               headers=auth(admin_token))
    check('create branch for login test', r.status_code == 201, f"({r.get_json().get('message', '')[:45]})")
    r = c.post('/api/auth/login', json={'login_id': 'BR99OP001', 'password': '9999999999'})
    br99 = r.get_json()
    check('new manager: first login forces password change',
          r.status_code == 200 and br99.get('mustChangePassword') is True)
    # While must_change_password is set, all non-auth APIs are blocked
    r = c.get('/api/dashboard', headers=auth(br99['token']))
    check('new manager: dashboard blocked until password change (403)', r.status_code == 403)
    r = c.post('/api/auth/change-password', json={'current_password': '9999999999', 'new_password': 'Br99secure9'},
               headers=auth(br99['token']))
    check('change default password', r.status_code == 200)
    r = c.post('/api/auth/login', json={'login_id': 'BR99OP001', 'password': 'Br99secure9'})
    check('new manager: login after change (flag cleared)',
          r.status_code == 200 and r.get_json().get('mustChangePassword') is False)

    # ── Production config must not leak the OTP in the response ──
    os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-prod-mode-checks')
    os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key-for-prod-mode-checks')
    from backend.app import create_app as _create_app
    prod_app = _create_app('production')
    with prod_app.test_client() as pc:
        r = pc.post('/api/auth/forgot-password', json={'username': 'BR99'})
        body = r.get_json()
        check('production: dev_otp not leaked', r.status_code == 200 and 'dev_otp' not in body,
              f"(keys={sorted(body.keys())})")

print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
