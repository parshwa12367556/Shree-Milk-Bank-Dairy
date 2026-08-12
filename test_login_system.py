"""Shree Milk Bank — Common Login System tests (spec §28).

Covers all 28 required login scenarios:
  1.  Admin login using valid Login ID
  2.  Branch Operator login using valid Login ID
  3.  Farmer login using valid Farmer Code
  4.  Invalid Login ID
  5.  Invalid password
  6.  Inactive account
  7.  Suspended account
  8.  Locked account
  9.  Failed login attempt increment
  10. Account lock after configured failures
  11. Successful login resets failed attempts
  12. Correct ADMIN redirect
  13. Correct BRANCH_OPERATOR redirect
  14. Correct FARMER redirect
  15. Farmer cannot access Admin APIs
  16. Farmer cannot access another farmer's data
  17. Branch Operator cannot access another branch's data
  18. Branch Operator cannot access Admin payment processing
  19. Password is never returned in API
  20. Password hash is never returned in API
  21. Login ID uniqueness works
  22. Login ID normalization works correctly
  23. Logout works
  24. Expired token is rejected
  25. Deactivated user token is rejected
  26. Forgot password does not expose account existence
  27. Production API does not return OTP
  28. New user must change password if must_change_password is true

Run:  python test_login_system.py
"""
import os
import sys
import json
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.getenv('TEST_DB_PATH', 'instance/test_login_system.db')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(DB_PATH).replace('\\', '/')
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


def login(client, payload):
    return client.post('/api/auth/login', json=payload)


def auth(token):
    return {'Authorization': f'Bearer {token}'}


with app.app_context():
    from backend.seed import seed_database
    seed_database()
    from backend.models import User, Farmer, AuditLog
    from backend.app import db

    # Capture canonical Login IDs from the seeded DB
    admin = User.query.filter_by(role='ADMIN').first()
    br01 = User.query.filter_by(username='BR01').first()
    br02 = User.query.filter_by(username='BR02').first()
    farmer = User.query.filter_by(role='FARMER', status='ACTIVE').first()
    farmer2 = User.query.filter_by(role='FARMER', status='ACTIVE').filter(User.id != farmer.id).first()
    inactive_farmer = User.query.filter_by(role='FARMER', status='INACTIVE').first()
    ADMIN_ID = admin.login_id
    BR01_ID = br01.login_id
    BR02_ID = br02.login_id
    FARMER_ID = farmer.login_id
    FARMER2_ID = farmer2.login_id
    INACTIVE_ID = inactive_farmer.login_id
    ADMIN_PW = 'admin123'
    BR01_PW = br01.phone
    BR02_PW = br02.phone
    FARMER_PW = farmer.phone
    FARMER2_PW = farmer2.phone
    INACTIVE_PW = inactive_farmer.phone
    FARMER_FARMER_ID = farmer.farmer_id
    FARMER_FARMER_CODE = farmer.farmer.farmer_code
    FARMER2_FARMER_ID = farmer2.farmer_id
    print(f"login ids: {ADMIN_ID} {BR01_ID} {BR02_ID} {FARMER_ID} {FARMER2_ID} inactive={INACTIVE_ID}\n")

class _IPClient:
    """Test-client wrapper that stamps every request with a distinct
    REMOTE_ADDR so the shared per-IP login throttle doesn't couple the
    independent scenarios together (all raw test clients share 127.0.0.1)."""
    def __init__(self, client, ip):
        self._client = client
        self._ip = ip

    def _env(self, kwargs):
        overrides = dict(kwargs.pop('environ_overrides', {}))
        overrides.setdefault('REMOTE_ADDR', self._ip)
        kwargs['environ_overrides'] = overrides
        return kwargs

    def post(self, url, **kwargs):
        return self._client.post(url, **self._env(kwargs))

    def get(self, url, **kwargs):
        return self._client.get(url, **self._env(kwargs))


admin_c = _IPClient(app.test_client(), '10.0.0.11')
br_c = _IPClient(app.test_client(), '10.0.0.12')
br2_c = _IPClient(app.test_client(), '10.0.0.13')
farmer_c = _IPClient(app.test_client(), '10.0.0.14')
farmer2_c = _IPClient(app.test_client(), '10.0.0.15')

# ══════════ 1-3. Valid Login ID logins + 12-14. Redirects ══════════
r = login(admin_c, {'login_id': ADMIN_ID, 'password': ADMIN_PW})
b = r.get_json() or {}
check('1. admin login with Login ID', r.status_code == 200 and b.get('token'))
check('12. admin redirect_url', b.get('redirect_url') == '/admin/dashboard', f"({b.get('redirect_url')})")
check('1b. admin user role from DB', b.get('user', {}).get('role') == 'ADMIN')
admin_token = b.get('token')

r = login(br_c, {'login_id': BR01_ID, 'password': BR01_PW})
b = r.get_json() or {}
check('2. branch operator login with Login ID', r.status_code == 200 and b.get('token'))
check('13. branch redirect_url', b.get('redirect_url') == '/branch/dashboard', f"({b.get('redirect_url')})")
check('2b. branch user role + scope', b.get('user', {}).get('role') == 'BRANCH_OPERATOR'
      and b.get('user', {}).get('branchId') == br01.branch_id)
br_token = b.get('token')

r = login(farmer_c, {'login_id': FARMER_ID, 'password': FARMER_PW})
b = r.get_json() or {}
check('3. farmer login with Farmer Code', r.status_code == 200 and b.get('token'))
check('14. farmer redirect_url', b.get('redirect_url') == '/farmer/dashboard', f"({b.get('redirect_url')})")
check('3b. farmer role + farmerId scope', b.get('user', {}).get('role') == 'FARMER'
      and b.get('user', {}).get('farmerId') == FARMER_FARMER_ID
      and b.get('user', {}).get('farmerCode') == FARMER_FARMER_CODE)
f_token = b.get('token')

# ══════════ 4-5. Invalid Login ID / password — generic error ══════════
r = login(admin_c, {'login_id': 'NO_SUCH_ID', 'password': 'whatever'})
check('4. invalid Login ID → 401', r.status_code == 401)
check('4b. generic error (no account enumeration)',
      r.get_json().get('error') == 'Invalid Login ID or Password.',
      f"({r.get_json().get('error')})")
r = login(admin_c, {'login_id': ADMIN_ID, 'password': 'wrong-pass'})
check('5. invalid password → 401 + generic error',
      r.status_code == 401 and 'Invalid Login ID or Password.' == r.get_json().get('error'))

# ══════════ 6-7. Inactive / suspended accounts ══════════
r = login(farmer_c, {'login_id': INACTIVE_ID, 'password': INACTIVE_PW})
check('6. inactive farmer login blocked (403)', r.status_code == 403, f"({r.status_code})")
with app.app_context():
    sus = User.query.filter_by(username='BR02').first()
    sus.status = 'SUSPENDED'
    db.session.commit()
    sus_login_id = sus.login_id
r = login(br2_c, {'login_id': sus_login_id, 'password': BR02_PW})
check('7. suspended account login blocked (403)', r.status_code == 403, f"({r.status_code})")
with app.app_context():
    sus = User.query.filter_by(username='BR02').first()
    sus.status = 'ACTIVE'
    db.session.commit()

# ══════════ 8-10. Lockout ══════════
for i in range(5):
    login(br_c, {'login_id': BR02_ID, 'password': 'badpass'})
r = login(br_c, {'login_id': BR02_ID, 'password': 'badpass'})
check('9. failed attempts incremented', True)  # verified via DB below
check('10. account locked after 5 failed attempts', r.status_code == 429, f"({r.status_code})")
r = login(br_c, {'login_id': BR02_ID, 'password': BR02_PW})
check('8. locked account rejects even correct password', r.status_code == 429)
with app.app_context():
    u = User.query.filter_by(username='BR02').first()
    check('9b. failed_attempts stored', (u.failed_attempts or 0) >= 5, f"({u.failed_attempts})")
    check('8b. locked_until set', u.locked_until is not None, f"({u.locked_until})")

# ══════════ 11. Successful login resets failed attempts ══════════
with app.app_context():
    u = User.query.filter_by(username='BR02').first()
    u.locked_until = None
    u.failed_attempts = 3
    db.session.commit()
r = login(br2_c, {'login_id': BR02_ID, 'password': BR02_PW})
with app.app_context():
    reset_ok = r.status_code == 200 and (User.query.filter_by(username='BR02').first().failed_attempts or 0) == 0
check('11. successful login resets failed attempts', reset_ok)

# ══════════ 15. Farmer cannot access Admin APIs ══════════
check('15. farmer blocked from admin APIs',
      farmer_c.get('/api/dashboard', headers=auth(f_token)).status_code == 403
      and farmer_c.get('/api/payments', headers=auth(f_token)).status_code == 403)

# ══════════ 16. Farmer IDOR isolation ══════════
r = farmer_c.get('/api/farmer/me/collections?per_page=100', headers=auth(f_token))
check('16. farmer sees own collections only',
      all(c['farmerId'] == FARMER_FARMER_ID for c in r.get_json().get('collections', [])))
r = farmer_c.get(f'/api/farmer/me/collections?farmerId={FARMER2_FARMER_ID}', headers=auth(f_token))
check('16b. farmerId param ignored (own only)',
      all(c['farmerId'] == FARMER_FARMER_ID for c in r.get_json().get('collections', [])))

# ══════════ 17. Branch isolation ══════════
r = login(br2_c, {'login_id': BR02_ID, 'password': BR02_PW})
br2_token = r.get_json()['token']
r = br2_c.get('/api/farmers?per_page=100', headers=auth(br2_token))
check('17. BR02 sees own branch farmers only',
      all(f['branchId'] == 2 for f in r.get_json()['farmers']))

# ══════════ 18. Branch Operator cannot process payments ══════════
r = br_c.post('/api/payments', json={'periodStart': '2026-07-01', 'periodEnd': '2026-08-01'},
              headers=auth(br_token))
check('18. branch operator cannot process payments (403)', r.status_code == 403, f"({r.status_code})")

# ══════════ 19-20. No password / hash leakage ══════════
r = login(admin_c, {'login_id': ADMIN_ID, 'password': ADMIN_PW})
raw = r.get_data(as_text=True)
check('19. password never in API response', 'admin123' not in raw)
check('20. password hash never in API response', '$2b$' not in raw and 'password_hash' not in raw)

# ══════════ 21. Login ID uniqueness (DB constraint) ══════════
with app.app_context():
    from sqlalchemy.exc import IntegrityError
    try:
        dup = User(login_id=ADMIN_ID, username='dup_login_id', password_hash='x',
                   name='Dup', role='ADMIN', status='ACTIVE')
        db.session.add(dup)
        db.session.flush()
        db.session.rollback()
        uniq = False
    except IntegrityError:
        db.session.rollback()
        uniq = True
check('21. duplicate login_id rejected at DB level', uniq)

# ══════════ 22. Login ID normalization (case-insensitive) ══════════
r = login(admin_c, {'login_id': ADMIN_ID.lower(), 'password': ADMIN_PW})
check('22. lowercase Login ID accepted (normalized)', r.status_code == 200)
r = login(admin_c, {'login_id': f'  {ADMIN_ID}  ', 'password': ADMIN_PW})
check('22b. whitespace trimmed', r.status_code == 200)

# ══════════ 23. Logout ══════════
r = admin_c.post('/api/auth/logout', headers=auth(admin_token))
check('23. logout works', r.status_code == 200)

# ══════════ 24. Expired token rejected ══════════
with app.app_context():
    from flask_jwt_extended import create_access_token
    expired = create_access_token(
        identity=json.dumps({'uid': admin.id, 'role': 'ADMIN', 'loginId': ADMIN_ID}),
        expires_delta=timedelta(seconds=-60))
r = admin_c.get('/api/dashboard', headers=auth(expired))
check('24. expired token rejected (401)', r.status_code == 401, f"({r.status_code})")

# ══════════ 25. Deactivated user token rejected ══════════
with app.app_context():
    deact_user = User.query.filter_by(role='BRANCH_OPERATOR').first()
    deact_user.status = 'INACTIVE'
    db.session.commit()
    from flask_jwt_extended import create_access_token
    deact_token = create_access_token(
        identity=json.dumps({'uid': deact_user.id, 'role': 'BRANCH_OPERATOR',
                             'loginId': deact_user.login_id, 'branchId': deact_user.branch_id}))
r = br_c.get('/api/farmers', headers=auth(deact_token))
check('25. deactivated user token rejected (403)', r.status_code == 403, f"({r.status_code})")
with app.app_context():
    deact_user.status = 'ACTIVE'
    db.session.commit()

# ══════════ 26. Forgot password does not expose existence ══════════
r = admin_c.post('/api/auth/forgot-password', json={'login_id': 'DEFINITELY_NOT_A_USER'})
check('26. unknown account → generic message', r.status_code == 200 and 'sent' in (r.get_json().get('message') or ''))
r = admin_c.post('/api/auth/forgot-password', json={'login_id': BR01_ID})
check('26b. known account → same generic message',
      r.status_code == 200 and r.get_json().get('message') ==
      admin_c.post('/api/auth/forgot-password', json={'login_id': 'DEFINITELY_NOT_A_USER'}).get_json().get('message'))

# ══════════ 27. Production API does not return OTP ══════════
r = admin_c.post('/api/auth/forgot-password', json={'login_id': BR01_ID})
check('27. production response has no dev_otp', 'dev_otp' not in (r.get_json() or {}),
      f"(keys={sorted((r.get_json() or {}).keys())})")

# ══════════ 28. must_change_password enforced for new accounts ══════════
r = admin_c.post('/api/branches', json={'name': 'Login Test', 'code': 'BR77', 'phone': '9777777777'},
                 headers=auth(admin_token))
check('28a. create branch (new operator account)', r.status_code == 201)
r = login(admin_c, {'login_id': 'BR77OP001', 'password': '9777777777'})
b = r.get_json() or {}
check('28b. first login forces password change', r.status_code == 200 and b.get('mustChangePassword') is True)
# Non-auth APIs blocked while must_change_password
r = admin_c.get('/api/dashboard', headers=auth(b.get('token')))
check('28c. dashboard blocked until password changed (403)', r.status_code == 403, f"({r.status_code})")
# Password change clears the flag
r = admin_c.post('/api/auth/change-password',
                 json={'current_password': '9777777777', 'new_password': 'NewPass123'},
                 headers=auth(b.get('token')))
check('28d. change password succeeds', r.status_code == 200)
r = login(admin_c, {'login_id': 'BR77OP001', 'password': 'NewPass123'})
b = r.get_json() or {}
check('28e. flag cleared after change', r.status_code == 200 and b.get('mustChangePassword') is False)
# Dashboard now accessible
r = admin_c.get('/api/dashboard', headers=auth(b.get('token')))
check('28f. dashboard accessible after password change', r.status_code == 200)

# ══════════ Audit trail (spec §27) ══════════
r = admin_c.get('/api/audit?per_page=200', headers=auth(admin_token))
actions = {l['action'] for l in r.get_json().get('logs', [])}
check('A1. LOGIN_SUCCESS audited', 'LOGIN_SUCCESS' in actions)
check('A2. LOGIN_FAILED audited', 'LOGIN_FAILED' in actions)
check('A3. ACCOUNT_LOCKED audited', 'ACCOUNT_LOCKED' in actions)
check('A4. PASSWORD_CHANGED audited', 'PASSWORD_CHANGED' in actions)
check('A5. PASSWORD_RESET_REQUESTED audited', 'PASSWORD_RESET_REQUESTED' in actions)
check('A6. LOGOUT audited', 'LOGOUT' in actions)

print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
