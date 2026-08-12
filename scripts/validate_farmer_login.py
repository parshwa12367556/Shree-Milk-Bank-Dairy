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

# 1d) The role sent by the client is NEVER trusted — the backend detects it
# from the database. Logging in with a farmer email returns the FARMER role.
r = c.post('/api/auth/login', json={
    'username': email, 'password': phone, 'role': 'BRANCH_OPERATOR'})
role_body = r.get_json() or {}
results.append(('client role ignored (login succeeds)', r.status_code == 200, str(r.status_code)))
results.append(('role detected from DB = FARMER',
                role_body.get('user', {}).get('role') == 'FARMER',
                role_body.get('user', {}).get('role')))
token = body.get('token')
ident = body.get('user') or {}
results.append(('identity has farmerCode', bool(ident.get('farmerCode')), ident.get('farmerCode')))
results.append(('identity role FARMER', ident.get('role') == 'FARMER', ident.get('role')))
c.set_cookie('access_token', token)

# 2) Farmer portal pages serve the SPA shell (the farmer's data is rendered
#    client-side from /api/farmer/me — verified below).
r = c.get('/farmer/profile')
html = r.get_data(as_text=True)
results.append(('farmer profile 200', r.status_code == 200, str(r.status_code)))
results.append(('profile serves SPA shell', 'Shree Milk Bank' in html, 'SPA shell'))
results.append(('profile page container present', 'id="page-my-profile"' in html, 'page-my-profile'))
for path in ['/farmer/passbook', '/farmer/milk-history', '/farmer/payments',
             '/farmer/bank-details', '/farmer/notifications']:
    r = c.get(path)
    results.append((f'{path} 200', r.status_code == 200, str(r.status_code)))

# 2b) The self-service API returns the farmer's real identity (client-rendered)
r = c.get('/api/farmer/me', headers={'Authorization': f'Bearer {token}'})
me = r.get_json().get('farmer', {}) if r.status_code == 200 else {}
results.append(('farmer/me 200', r.status_code == 200, str(r.status_code)))
results.append(('farmer/me shows farmer code', me.get('farmerCode') == farmer.farmer_code, me.get('farmerCode')))
results.append(('farmer/me shows farmer name', me.get('name') == farmer.name, me.get('name')))

# 3) RBAC: farmer blocked from admin/branch pages
r = c.get('/admin/branches')
results.append(('farmer blocked from admin (302)', r.status_code == 302, str(r.status_code)))
r = c.get('/branch/dashboard')
results.append(('farmer blocked from branch (302)', r.status_code == 302, str(r.status_code)))

# 4) Wrong password rejected, unknown account rejected (generic error)
r = c.post('/api/auth/login', json={
    'username': email, 'password': 'wrongpass'})
results.append(('wrong password rejected 401', r.status_code == 401, str(r.status_code)))
r = c.post('/api/auth/login', json={
    'username': 'no.such.farmer@dairy.com', 'password': phone})
results.append(('unknown email rejected 401', r.status_code == 401, str(r.status_code)))

# 5) Admin can still log in; farmer portal pages are FARMER-only (spec 11)
r = c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'ADMIN'})
results.append(('admin login 200', r.status_code == 200, str(r.status_code)))
c.set_cookie('access_token', r.get_json()['token'])
r = c.get('/farmer/profile')
results.append(('admin farmer portal blocked (302)', r.status_code == 302, str(r.status_code)))
r = c.get('/admin/dashboard')
results.append(('admin dashboard 200', r.status_code == 200, str(r.status_code)))

print('=== FARMER LOGIN VALIDATION ===')
ok = True
for name, passed, info in results:
    print(f'  [{"PASS" if passed else "FAIL"}] {name}: {info}')
    ok = ok and passed
print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
