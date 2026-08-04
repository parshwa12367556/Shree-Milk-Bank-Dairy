"""Test script for all newly implemented features (audit, verification workflow,
procurement module, inventory movements, expenses/P&L, exports, vehicle extras,
bank editing, SMS/email settings)."""
import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

# Fresh database
if os.path.exists('smart_dairy.db'):
    os.remove('smart_dairy.db')
    print("Removed old database")

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
    check('audit: login recorded', any(l['action'] == 'LOGIN' for l in logs),
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

    # Admin cannot create farmers
    r = c.post('/api/farmers', json={'name': 'X', 'mobile': '9999999999', 'milkType': 'COW'},
               headers=auth(admin_token))
    check('admin cannot register farmer', r.status_code == 403)

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
    admin_login = next((l for l in logs if l['action'] == 'LOGIN' and l.get('username') == 'admin'), None)
    check('audit: role captured', admin_login and admin_login.get('role') == 'SUPER_ADMIN')
    br_login = next((l for l in logs if l['action'] == 'LOGIN' and l.get('username') == 'BR01'), None)
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

print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
