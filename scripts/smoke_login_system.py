"""Temporary smoke test for the common login system (deleted after verification)."""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB = 'instance/test_login_smoke.db'
if os.path.exists(DB):
    os.remove(DB)
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(DB).replace('\\', '/')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-prod-mode-checks')
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key-for-prod-mode-checks')

from backend.app import create_app  # noqa: E402

app = create_app('production')
with app.app_context():
    from backend.seed import seed_database
    seed_database()
    from backend.models import User
    print('admin login_id:', User.query.filter_by(role='ADMIN').first().login_id)
    for u in User.query.filter_by(role='BRANCH_MANAGER').limit(2):
        print('branch login_id:', u.login_id, u.username)
    f = User.query.filter_by(role='FARMER').first()
    FARMER_MOBILE = f.phone
    print('farmer login_id:', f.login_id, '| status:', f.status, '| mobile:', FARMER_MOBILE)

c = app.test_client()
r = c.post('/api/auth/login', json={'login_id': 'ADMIN001', 'password': 'admin123'})
print('admin ADMIN001:', r.status_code, '| redirect:', r.get_json().get('redirect_url'),
      '| role:', r.get_json().get('user', {}).get('role'))
r = c.post('/api/auth/login', json={'login_id': 'BR01OP001', 'password': '9876543210', 'remember_me': True})
print('branch BR01OP001:', r.status_code, '| redirect:', r.get_json().get('redirect_url'),
      '| role:', r.get_json().get('user', {}).get('role'))
r = c.post('/api/auth/login', json={'username': 'BR01', 'password': '9876543210', 'role': 'ADMIN'})
print('branch legacy username + client role ignored:', r.status_code,
      '| role:', r.get_json().get('user', {}).get('role'))
r = c.post('/api/auth/login', json={'login_id': 'BR01001', 'password': FARMER_MOBILE})
print('farmer BR01001:', r.status_code, '| redirect:', r.get_json().get('redirect_url'),
      '| role:', r.get_json().get('user', {}).get('role'), '| farmerCode:', r.get_json().get('user', {}).get('farmerCode'))
r = c.post('/api/auth/login', json={'login_id': 'BR01001', 'password': 'nope'})
print('wrong password:', r.status_code, '| err:', r.get_json().get('error'))
r = c.post('/api/auth/login', json={'login_id': 'NOPE99', 'password': 'x'})
print('unknown:', r.status_code, '| err:', r.get_json().get('error'))
r = c.post('/api/auth/login', json={'login_id': 'br01001', 'password': FARMER_MOBILE})
print('lowercase login_id:', r.status_code)
r = c.post('/api/auth/login', json={'login_id': 'ADMIN001', 'password': 'admin123'})
body = r.get_json()
print('password leaked?', 'admin123' in str(body))

# Lockout test (fresh branch user to avoid polluting)
r = c.post('/api/auth/login', json={'login_id': 'BR02OP001', 'password': 'wrong1'})
r = c.post('/api/auth/login', json={'login_id': 'BR02OP001', 'password': 'wrong2'})
r = c.post('/api/auth/login', json={'login_id': 'BR02OP001', 'password': 'wrong3'})
r = c.post('/api/auth/login', json={'login_id': 'BR02OP001', 'password': 'wrong4'})
r = c.post('/api/auth/login', json={'login_id': 'BR02OP001', 'password': 'wrong5'})
r = c.post('/api/auth/login', json={'login_id': 'BR02OP001', 'password': '9123456780'})
print('locked account (after 5 fails):', r.status_code, '| err:', r.get_json().get('error'))
