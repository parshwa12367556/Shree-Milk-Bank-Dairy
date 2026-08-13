import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
DB_PATH = 'instance/test_production_hardening.db'
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(DB_PATH).replace('\\', '/')
os.environ['SECRET_KEY'] = 'test-hardening-secret-key-32chars-long-minimum-ok'
os.environ['JWT_SECRET_KEY'] = 'test-hardening-jwt-secret-key-32chars-long-minimum-ok'
from backend.app import create_app
app = create_app('production')


def login(c, u, p, role=None):
    payload = {'username': u, 'password': p}
    if role:
        payload['role'] = role
    r = c.post('/api/auth/login', json=payload)
    return r.get_json().get('token') if r.status_code == 200 else None


with app.app_context():
    from backend.models import Farmer, User
    e2e = Farmer.query.filter_by(name='E2E Farmer').first()
    print('farmer:', e2e.id if e2e else None, e2e.email if e2e else None)
    uid = User.query.filter_by(farmer_id=e2e.id).first() if e2e else None
    print('user exists:', bool(uid))
c = app.test_client()
t = login(c, 'e2e.farmer@example.com', '9771112222', 'FARMER')
print('login token:', bool(t))
r = c.get('/api/farmer/me', headers={'Authorization': 'Bearer ' + (t or '')})
print('me:', r.status_code, list((r.get_json() or {}).keys()))
print('me farmer keys:', list((r.get_json() or {}).get('farmer', {}).keys())[:8])
print('farmerCode:', (r.get_json() or {}).get('farmer', {}).get('farmerCode'))
r = c.get('/api/farmer/me/collections', headers={'Authorization': 'Bearer ' + (t or '')})
print('cols:', r.status_code, list((r.get_json() or {}).keys()))
cols = (r.get_json() or {}).get('collections', [])
print('n cols:', len(cols), 'first keys:', list(cols[0].keys())[:10] if cols else None)
r = c.get('/api/farmer/me/passbook', headers={'Authorization': 'Bearer ' + (t or '')})
pb = (r.get_json() or {})
print('passbook:', r.status_code, list(pb.keys()))
ents = pb.get('entries', [])
print('n entries:', len(ents), 'first keys:', list(ents[0].keys())[:10] if ents else None)
r = c.get('/api/farmer/me/notifications', headers={'Authorization': 'Bearer ' + (t or '')})
nf = (r.get_json() or {})
print('notifs:', r.status_code, list(nf.keys()))
ns = nf.get('notifications', [])
print('n notifs:', len(ns), 'titles:', [n.get('title') for n in ns[:3]])
r = c.get('/api/farmer/me/payments', headers={'Authorization': 'Bearer ' + (t or '')})
print('payments:', r.status_code, list((r.get_json() or {}).keys()))
