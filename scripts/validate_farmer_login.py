"""End-to-end validation of the farmer login flow."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from flask_jwt_extended import create_access_token

from backend.app import create_app
from backend.models import User, Farmer

app = create_app()
c = app.test_client()

results = []

with app.app_context():
    # Find a real ACTIVE farmer and their linked login account
    farmer = Farmer.query.filter_by(status='ACTIVE').order_by(Farmer.id).first()
    user = User.query.filter_by(farmer_id=farmer.id).first()
    results.append(('linked user exists', user is not None, f'farmer={farmer.farmer_code}'))
    results.append(('user role FARMER', user.role == 'FARMER', user.role))
    results.append(('user ACTIVE', user.status == 'ACTIVE', user.status))
    results.append(('farmer has email', bool(farmer.email), farmer.email))
    email, phone = farmer.email, user.phone or ''

# 1) Farmer logs in via EMAIL + mobile (role tab = FARMER)
r = c.post('/api/auth/login', json={
    'username': email, 'password': phone, 'role': 'FARMER'})
body = r.get_json() or {}
results.append(('farmer EMAIL login 200', r.status_code == 200, f'status={r.status_code} err={body.get("error")}'))

# 1b) Farmer code still works as a fallback identifier
r = c.post('/api/auth/login', json={
    'username': farmer.farmer_code, 'password': phone, 'role': 'FARMER'})
results.append(('farmer CODE fallback login 200', r.status_code == 200, str(r.status_code)))

# 1c) Email lookup is case-insensitive
r = c.post('/api/auth/login', json={
    'username': email.upper(), 'password': phone, 'role': 'FARMER'})
results.append(('uppercase email login 200', r.status_code == 200, str(r.status_code)))

# 1d) A farmer email never resolves to a non-farmer account
r = c.post('/api/auth/login', json={
    'username': email, 'password': phone, 'role': 'BRANCH_MANAGER'})
results.append(('email as wrong role rejected', r.status_code == 401, str(r.status_code)))
token = body.get('token')
ident = body.get('user') or {}
results.append(('identity has farmerCode', bool(ident.get('farmerCode')), ident.get('farmerCode')))
results.append(('identity role FARMER', ident.get('role') == 'FARMER', ident.get('role')))
c.set_cookie('access_token', token)

# 2) Farmer portal pages render with the farmer's data
r = c.get('/farmer/profile')
html = r.get_data(as_text=True)
results.append(('farmer profile 200', r.status_code == 200, str(r.status_code)))
results.append(('profile shows farmer code', farmer.farmer_code in html, farmer.farmer_code))
results.append(('profile shows farmer name', farmer.name in html, farmer.name))
for path in ['/farmer/passbook', '/farmer/milk-history', '/farmer/payments',
             '/farmer/bank-details', '/farmer/notifications']:
    r = c.get(path)
    results.append((f'{path} 200', r.status_code == 200, str(r.status_code)))

# 3) RBAC: farmer blocked from admin/branch pages
r = c.get('/admin/branches')
results.append(('farmer blocked from admin (302)', r.status_code == 302, str(r.status_code)))
r = c.get('/branch/dashboard')
results.append(('farmer blocked from branch (302)', r.status_code == 302, str(r.status_code)))

# 4) Wrong role hint rejected, wrong password rejected
r = c.post('/api/auth/login', json={
    'username': email, 'password': phone, 'role': 'BRANCH_MANAGER'})
results.append(('role mismatch rejected 401', r.status_code == 401, str(r.status_code)))
r = c.post('/api/auth/login', json={
    'username': email, 'password': 'wrongpass', 'role': 'FARMER'})
results.append(('wrong password rejected 401', r.status_code == 401, str(r.status_code)))
r = c.post('/api/auth/login', json={
    'username': 'no.such.farmer@dairy.com', 'password': phone, 'role': 'FARMER'})
results.append(('unknown email rejected 401', r.status_code == 401, str(r.status_code)))

# 5) Admin can still log in + hit farmer portal (global view)
r = c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'SUPER_ADMIN'})
results.append(('admin login 200', r.status_code == 200, str(r.status_code)))
c.set_cookie('access_token', r.get_json()['token'])
r = c.get('/farmer/profile')
results.append(('admin sees farmer portal 200', r.status_code == 200, str(r.status_code)))

print('=== FARMER LOGIN VALIDATION ===')
ok = True
for name, passed, info in results:
    print(f'  [{"PASS" if passed else "FAIL"}] {name}: {info}')
    ok = ok and passed
print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
