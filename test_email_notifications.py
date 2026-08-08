"""Shree Milk Bank — Email Notification tests.

Covers:
  - Milk collection → email to the farmer's REGISTERED (DB) email address
  - Subject/body content of the collection email
  - Recipient is never a hardcoded / client-supplied address
  - Graceful skip when SMTP is not configured or farmer has no email
  - Password-reset OTP email uses the same mailer

Email transport is replaced with a capture class (no real SMTP needed).

Run:  python test_email_notifications.py
"""
import os
import sys
from unittest.mock import patch

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.getenv('TEST_DB_PATH', 'instance/test_email_notifications.db')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(DB_PATH).replace('\\', '/')

from backend.app import create_app  # noqa: E402

app = create_app('production')

# Deliver synchronously so the capture class below sees messages deterministically.
from backend import mailer  # noqa: E402
mailer.SEND_ASYNC = False

PASS, FAIL = 0, 0


def check(name, cond, extra=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK  {name} {extra}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {extra}")


class FakeSMTP:
    """Captures messages instead of sending them."""
    sent = []

    def __init__(self, *args, **kwargs):
        self.sent_messages = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        return None

    def login(self, user, password):
        return None

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)
        self.sent_messages.append(msg)

    @classmethod
    def reset(cls):
        cls.sent = []


with app.app_context():
    from backend.seed import seed_database
    seed_database()
    print("Seeded.\n")

# SMTP configured for the tests (simulating Settings → Email Settings)
from backend.modules.admin.settings import _system_settings  # noqa: E402

_system_settings['email_smtp_host'] = 'smtp.test.local'
_system_settings['email_smtp_port'] = '587'
_system_settings['email_smtp_username'] = 'dairy'
_system_settings['email_smtp_password'] = 'secret'
_system_settings['email_from'] = 'Shree Milk Bank <noreply@shreemilkbank.com>'
_system_settings['notification_email'] = True


def login(client, username, password, role=None):
    payload = {'username': username, 'password': password}
    if role:
        payload['role'] = role
    r = client.post('/api/auth/login', json=payload)
    return r.get_json().get('token') if r.status_code == 200 else None


admin_c = app.test_client()
br_c = app.test_client()

admin_token = login(admin_c, 'admin', 'admin123')
br_token = login(br_c, 'BR01', '9876543210', 'BRANCH_MANAGER')
check('logins ok', bool(admin_token and br_token))

# Pick a BR01 ACTIVE farmer with a known email
r = admin_c.get('/api/farmers?branchId=1&status=ACTIVE&per_page=100',
                headers={'Authorization': f'Bearer {admin_token}'})
farmer = next(f for f in r.get_json()['farmers'] if f['email'])
farmer_id = farmer['id']
farmer_code = farmer['farmerCode']
farmer_name = farmer['name']
db_email = farmer['email']
check('farmer has DB email', bool(db_email), f"({farmer_code} → {db_email})")

# ══════════ 1. Milk collection → email to the farmer's DB address ══════════
FakeSMTP.reset()
with patch('backend.mailer.smtplib.SMTP', FakeSMTP):
    r = br_c.post('/api/collections', json={
        'farmerId': farmer_id, 'quantity': 12.5, 'fat': 4.2, 'snf': 8.5,
        'shift': 'EVENING', 'temperature': 28.4, 'water': 0,
        'idempotencyKey': 'email-test-001',
    }, headers={'Authorization': f'Bearer {br_token}'})
    check('collection created', r.status_code == 201)

    msgs = FakeSMTP.sent
    check('one email captured', len(msgs) == 1, f"({len(msgs)})")
    if msgs:
        msg = msgs[0]
        check('email To = farmer DB email', msg['To'] == db_email,
              f"(To={msg['To']})")
        check('email NOT hardcoded address', msg['To'] != 'test@fake.com')
        check('email subject', msg['Subject'] == 'New Milk Collection Recorded - Shree Milk Bank',
              f"({msg['Subject']})")
        html = msg.get_payload(1).get_content()
        checks = {
            'greeting': farmer_name in html,
            'farmer id': farmer_code in html,
            'quantity': '12.50 Liters' in html,
            'fat': '4.2%' in html,
            'snf': '8.5%' in html,
            'temperature': '28.4°C' in html,
            'amount': '₹' in html or '&#8377;' in html,
            'status': 'Recorded' in html or 'Accepted' in html,
            'branch label': 'Shree Milk Bank - BR01' in html,
        }
        for name, cond in checks.items():
            check(f'email contains {name}', cond)

# ══════════ 2. Skip when SMTP not configured ══════════
FakeSMTP.reset()
_system_settings['email_smtp_host'] = ''  # unconfigured
with patch('backend.mailer.smtplib.SMTP', FakeSMTP):
    r = br_c.post('/api/collections', json={
        'farmerId': farmer_id, 'quantity': 8, 'idempotencyKey': 'email-test-002',
    }, headers={'Authorization': f'Bearer {br_token}'})
    check('collection still created without SMTP', r.status_code == 201)
    check('no email sent when SMTP unconfigured', len(FakeSMTP.sent) == 0)
_system_settings['email_smtp_host'] = 'smtp.test.local'  # restore

# ══════════ 3. Skip when farmer has no email ══════════
FakeSMTP.reset()
from backend.models import Farmer  # noqa: E402
with app.app_context():
    f = Farmer.query.get(farmer_id)
    orig_email = f.email
    f.email = None
    from backend.app import db as _db
    _db.session.commit()
with patch('backend.mailer.smtplib.SMTP', FakeSMTP):
    r = br_c.post('/api/collections', json={
        'farmerId': farmer_id, 'quantity': 6, 'idempotencyKey': 'email-test-003',
    }, headers={'Authorization': f'Bearer {br_token}'})
    check('collection still created without farmer email', r.status_code == 201)
    check('no email sent when farmer has no email', len(FakeSMTP.sent) == 0)
with app.app_context():
    f = Farmer.query.get(farmer_id)
    f.email = orig_email
    from backend.app import db as _db
    _db.session.commit()

# ══════════ 4. Mailer unit checks ══════════
from backend import mailer  # noqa: E402

FakeSMTP.reset()
with patch('backend.mailer.smtplib.SMTP', FakeSMTP):
    ok, err = mailer.send_email('farmer@example.com', 'Test Subject', '<p>Hello</p>')
    check('send_email returns success', ok is True and err is None)
    msg = FakeSMTP.sent[0]
    check('mailer sets To', msg['To'] == 'farmer@example.com')
    check('mailer sets From', 'Shree Milk Bank' in msg['From'])

FakeSMTP.reset()
ok, err = mailer.send_email('', 'Test', '<p>x</p>')
check('send_email rejects empty recipient', ok is False)

_system_settings['notification_email'] = False
FakeSMTP.reset()
with patch('backend.mailer.smtplib.SMTP', FakeSMTP):
    ok, err = mailer.send_email('farmer@example.com', 'Test', '<p>x</p>')
    check('send_email skips when notifications disabled', ok is False)
_system_settings['notification_email'] = True

# ══════════ 5. Password-reset OTP email uses the mailer ══════════
FakeSMTP.reset()
with app.app_context():
    from backend.models import User as _User
    br01_user = _User.query.filter_by(username='BR01').first()
    br01_email = br01_user.email if br01_user else None
    check('BR01 user has an email in DB', bool(br01_email), f"({br01_email})")
with patch('backend.mailer.smtplib.SMTP', FakeSMTP):
    r = admin_c.post('/api/auth/forgot-password', json={'username': 'BR01'})
    check('forgot-password flow works', r.status_code == 200)
    check('OTP email captured for BR01', bool(br01_email) and any(
        m['To'] == br01_email and 'Password Reset OTP' in m['Subject']
        for m in FakeSMTP.sent))

print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
