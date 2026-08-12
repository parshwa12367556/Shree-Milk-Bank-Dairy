"""Validate: register farmer (branch) -> verify (head office) -> farmer can log in."""
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


def login_as(role, username, branch_id=None):
    ident = {'uid': 999, 'username': username, 'name': username, 'role': role,
             'branchId': branch_id, 'branchName': 'BR01'}
    with app.app_context():
        tok = create_access_token(identity=json.dumps(ident))
    c.set_cookie('access_token', tok)
    login_as.__last_tok = tok
    return tok


def H():
    return {'Authorization': 'Bearer ' + getattr(login_as, '__last_tok', '')}


# 1) Branch Manager registers a farmer
login_as('BRANCH_OPERATOR', 'BR01', branch_id=1)
r = c.post('/api/farmers', headers=H(), json={
    'name': 'Flow Test Farmer', 'mobile': '9012345678', 'milkType': 'COW'})
body = r.get_json() or {}
code = body.get('farmer', {}).get('farmerCode')
results.append(('register farmer 201', r.status_code == 201, f'{r.status_code} {body.get("error", "")}'))
results.append(('farmer code generated', bool(code), str(code)))

with app.app_context():
    f = Farmer.query.filter_by(farmer_code=code).first()
    u = User.query.filter_by(farmer_id=f.id).first() if f else None
    results.append(('login account auto-created', u is not None, str(u)))
    results.append(('account INACTIVE before verify', u.status == 'INACTIVE' if u else False, u.status if u else 'n/a'))
    phone = u.phone if u else None

# 2) Farmer cannot log in before verification
r = c.post('/api/auth/login', json={'username': code, 'password': phone, 'role': 'FARMER'})
results.append(('login blocked before verify (403)', r.status_code == 403, str(r.status_code)))

# 3) Head Office verifies the farmer
login_as('ADMIN', 'admin')
r = c.post(f'/api/farmers/{code}/verify', headers=H(), json={'action': 'approve'})
results.append(('verify farmer 200', r.status_code == 200, str(r.status_code)))

with app.app_context():
    f = Farmer.query.filter_by(farmer_code=code).first()
    u = User.query.filter_by(farmer_id=f.id).first()
    results.append(('account ACTIVE after verify', u.status == 'ACTIVE' if u else False, u.status if u else 'n/a'))

# 4) Now the farmer can log in with code + mobile
r = c.post('/api/auth/login', json={'username': code, 'password': phone, 'role': 'FARMER'})
results.append(('farmer logs in after verify (200)', r.status_code == 200, f'{r.status_code} {r.get_json().get("error")}'))
c.set_cookie('access_token', r.get_json().get('token') if r.status_code == 200 else '')
r = c.get('/farmer/profile')
results.append(('farmer portal renders 200', r.status_code == 200, str(r.status_code)))

# 4b) New farmer (no email supplied) gets a generated email and can log in with it
with app.app_context():
    f2 = Farmer.query.filter_by(farmer_code=code).first()
    femail = f2.email if f2 else None
results.append(('registered farmer got email', bool(femail), str(femail)))
r = c.post('/api/auth/login', json={'username': femail, 'password': phone, 'role': 'FARMER'})
results.append(('farmer logs in with EMAIL (200)', r.status_code == 200, f'{r.status_code} {r.get_json().get("error")}'))

# 5) Reject flow: reject a farmer -> account stays locked
login_as('BRANCH_OPERATOR', 'BR01', branch_id=1)
r = c.post('/api/farmers', headers=H(), json={'name': 'Reject Flow', 'mobile': '9098765432', 'milkType': 'BUFFALO'})
code2 = r.get_json().get('farmer', {}).get('farmerCode')
login_as('ADMIN', 'admin')
c.post(f'/api/farmers/{code2}/verify', headers=H(), json={'action': 'reject', 'reason': 'Docs mismatch'})
with app.app_context():
    u2 = User.query.filter_by(farmer_id=Farmer.query.filter_by(farmer_code=code2).first().id).first()
    results.append(('rejected farmer account stays INACTIVE', u2.status == 'INACTIVE', u2.status))

print('=== REGISTRATION -> VERIFY -> LOGIN ===')
ok = True
for name, passed, info in results:
    print(f'  [{"PASS" if passed else "FAIL"}] {name}: {info}')
    ok = ok and passed
print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
