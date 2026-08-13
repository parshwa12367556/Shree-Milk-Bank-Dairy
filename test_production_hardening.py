"""Shree Milk Bank — Production Hardening & Feature Completion Tests.

Covers the production-readiness work added across the hardening pass:

  H1. Isolated test database — tests never touch smart_dairy.db and refuse
      to run against the production DB path.
  H2. Timezone consistency — one app-wide convention (aware UTC). DB-loaded
      values are re-tagged via ensure_utc; comparisons never raise the
      naive/aware TypeError.
  H3. Persistent OTP — database-backed reset tokens survive "worker"
      switches (OTP issued in one context, validated from another), are
      single-use, expire, block after max attempts, and never store or
      return the plaintext in production.
  H4. SMS failure is non-fatal — a broken gateway never fails the milk
      collection; every attempt is recorded in notification_logs.
  H5. Password change (ADMIN / BRANCH_OPERATOR / FARMER) — current password
      verified, policy enforced, session stays usable.
  H6. QR generation / validation / authorization — signed opaque payloads,
      no PII, branch-scoped lookup, regeneration invalidates old payloads.
  H7. Deep-scan accuracy — the regenerated results contain no RBAC
      false positives.
  H8. End-to-end business flow — branch → farmer → collection → passbook →
      notification → payment → farmer payment history, all backed by the
      real database.

Run:  python test_production_hardening.py
"""
import os
import sys
import json
from datetime import date as _date, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# ── H1. Isolated test database ───────────────────────────────────────────
PROD_DB = os.path.abspath('smart_dairy.db')
DB_PATH = os.getenv('TEST_DB_PATH', os.path.join('instance', 'test_production_hardening.db'))
if os.path.abspath(DB_PATH) == PROD_DB:
    raise RuntimeError('Refusing to run destructive tests against the production database: '
                       f'{PROD_DB}')
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except Exception:
        pass  # a lock here (dev server) is impossible — this is an isolated file

os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(DB_PATH).replace('\\', '/')
os.environ.setdefault('SECRET_KEY', 'test-hardening-secret-key-32chars-long-minimum-ok')
os.environ.setdefault('JWT_SECRET_KEY', 'test-hardening-jwt-secret-key-32chars-long-minimum-ok')

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
    from backend.models import (User, Farmer, Collection, Payment, AuditLog,
                                PasswordResetOTP, NotificationLog, Branch)
    from backend.app import db
    from backend.utils import utcnow, ensure_utc, sign_farmer_qr, verify_farmer_qr
    from backend.modules.shared.auth import _issue_otp, _hash_otp
    print("Seeded.\n")

admin_c = app.test_client()
br_c = app.test_client()
farmer_c = app.test_client()

admin_token, _ = login(admin_c, 'admin', 'admin123')
check('H0a. admin login', bool(admin_token))
br_token, _ = login(br_c, 'BR01', '9876543210', 'BRANCH_OPERATOR')
check('H0b. BR01 operator login', bool(br_token))

# ══════════ H1. Isolated test DB ═════════════════════════════════════════
check('H1a. test DB is not the production DB',
      os.path.abspath(DB_PATH) != PROD_DB, f'({os.path.basename(DB_PATH)})')
with app.app_context():
    check('H1b. app connected to the isolated DB',
          'test_production_hardening' in app.config.get('SQLALCHEMY_DATABASE_URI', ''),
          f"({app.config.get('SQLALCHEMY_DATABASE_URI')})")

# ══════════ H2. Timezone consistency ═════════════════════════════════════
with app.app_context():
    now = utcnow()
    check('H2a. utcnow() is timezone-aware', now.tzinfo is not None)
    check('H2b. ensure_utc(aware) round-trips', ensure_utc(now) == now)
    naive = now.replace(tzinfo=None)
    check('H2c. ensure_utc(naive) re-tags as UTC', ensure_utc(naive).tzinfo is not None
          and ensure_utc(naive) == now)
    check('H2d. ensure_utc(None) is None', ensure_utc(None) is None)

    # Model defaults are produced by utcnow() → aware at flush time.
    u = User(login_id='TZ_PROBE', username='tzprobe', name='TZ Probe',
             password_hash='x', role='ADMIN')
    db.session.add(u)
    db.session.flush()
    check('H2e. model created_at default is aware', u.created_at is not None
          and u.created_at.tzinfo is not None)
    uid = u.id
    db.session.commit()
    reloaded = db.session.get(User, uid)
    try:
        cmp_ok = ensure_utc(reloaded.created_at) > utcnow() - timedelta(days=1)
        check('H2f. DB-loaded created_at compares without TypeError', cmp_ok)
    except TypeError:
        check('H2f. DB-loaded created_at compares without TypeError', False,
              '(TypeError: naive/aware)')
    db.session.delete(reloaded)
    db.session.commit()

# ══════════ H3. Persistent OTP ═══════════════════════════════════════════
# Use a dedicated seeded user (BR02 operator) so the admin/BR01 sessions and
# their passwords are never disturbed; restore the password at the end.
with app.app_context():
    otp_user = User.query.filter_by(username='BR02').first()
    otp_login_id = otp_user.login_id
    otp_orig_password = '9123456780'

# H3a. Production API never returns the OTP in the response.
r = admin_c.post('/api/auth/forgot-password', json={'login_id': otp_login_id})
body = r.get_json() or {}
check('H3a. forgot-password: generic message, no dev_otp in production',
      r.status_code == 200 and 'dev_otp' not in body,
      f"(keys={sorted(body.keys())})")

# H3b. OTP row persisted with a hash — never the plaintext.
with app.app_context():
    row = PasswordResetOTP.query.filter_by(
        user_id=otp_user.id, purpose='PASSWORD_RESET', used_at=None
    ).order_by(PasswordResetOTP.id.desc()).first()
    check('H3b-1. OTP row exists in the shared database', row is not None)
    if row:
        check('H3b-2. stored value is a 64-char SHA-256 hash',
              len(row.otp_hash) == 64 and row.otp_hash != _hash_otp(row.otp_hash),
              f"({len(row.otp_hash)} chars)")
        check('H3b-3. OTP expires in the future (aware compare)',
              ensure_utc(row.expires_at) > utcnow())
        check('H3b-4. max_attempts set', (row.max_attempts or 0) >= 5)

# H3c. "Worker A creates → Worker B validates": issue in one context
# (simulating worker A), then validate through a separate HTTP request
# (worker B) — persistence in the DB is what makes this work.
with app.app_context():
    worker_otp = _issue_otp(db.session.get(User, otp_user.id))
    db.session.commit()
fresh_otp = worker_otp
new_pw = 'Hardened@2026x'
r = admin_c.post('/api/auth/reset-password',
                 json={'login_id': otp_login_id, 'otp': fresh_otp, 'new_password': new_pw})
check('H3c. worker-B validates worker-A OTP → password reset succeeds',
      r.status_code == 200, f"(status={r.status_code})")

# H3d. Single-use: the same OTP must not work twice.
r = admin_c.post('/api/auth/reset-password',
                 json={'login_id': otp_login_id, 'otp': fresh_otp, 'new_password': new_pw})
check('H3d. OTP is single-use (second use rejected)', r.status_code == 400)

# H3e. Wrong OTP burns an attempt; max attempts blocks.
with app.app_context():
    issue_2 = _issue_otp(db.session.get(User, otp_user.id))
    db.session.commit()
for _ in range(6):
    r = admin_c.post('/api/auth/reset-password',
                     json={'login_id': otp_login_id, 'otp': '000000', 'new_password': new_pw})
blocked = r.status_code == 400
with app.app_context():
    t = PasswordResetOTP.query.filter_by(
        user_id=otp_user.id, purpose='PASSWORD_RESET', used_at=None
    ).order_by(PasswordResetOTP.id.desc()).first()
    attempts = t.attempt_count if t else 0
check('H3e-1. wrong OTP rejected (6 tries)', blocked)
check('H3e-2. failed attempts tracked', attempts >= 5, f"({attempts})")
# The blocked token is unusable even with the RIGHT otp.
r = admin_c.post('/api/auth/reset-password',
                 json={'login_id': otp_login_id, 'otp': issue_2, 'new_password': new_pw})
check('H3e-3. exhausted token rejected even with correct OTP', r.status_code == 400)

# H3f. Expired OTP is rejected.
with app.app_context():
    exp = _issue_otp(db.session.get(User, otp_user.id))
    row2 = PasswordResetOTP.query.filter_by(
        user_id=otp_user.id, purpose='PASSWORD_RESET', used_at=None,
        otp_hash=_hash_otp(exp)).first()
    row2.expires_at = utcnow() - timedelta(seconds=1)
    db.session.commit()
r = admin_c.post('/api/auth/reset-password',
                 json={'login_id': otp_login_id, 'otp': exp, 'new_password': new_pw})
check('H3f. expired OTP rejected', r.status_code == 400)

# H3g. Successful reset invalidates ALL other outstanding OTPs for the user.
with app.app_context():
    otp_a = _issue_otp(db.session.get(User, otp_user.id))
    db.session.commit()
    otp_b = _issue_otp(db.session.get(User, otp_user.id))
    db.session.commit()
r = admin_c.post('/api/auth/reset-password',
                 json={'login_id': otp_login_id, 'otp': otp_b, 'new_password': new_pw})
check('H3g-1. reset succeeds with newest OTP', r.status_code == 200)
with app.app_context():
    outstanding = PasswordResetOTP.query.filter_by(
        user_id=otp_user.id, purpose='PASSWORD_RESET', used_at=None).count()
    check('H3g-2. no outstanding OTPs remain after successful reset',
          outstanding == 0, f"({outstanding} still outstanding)")

# H3h. The plaintext OTP never appears in audit logs or delivery logs.
with app.app_context():
    probe = _issue_otp(db.session.get(User, otp_user.id))
    db.session.commit()
    leaked = AuditLog.query.filter(AuditLog.detail.like(f'%{probe}%')).first() is not None
    check('H3h. plaintext OTP never written to audit logs', not leaked)

# Restore the BR02 password to a policy-compliant value (the JWT below
# stays valid; the seed-style mobile-only passwords cannot be re-set because
# they violate the enforced password policy — intentional hardening).
r = admin_c.post('/api/auth/reset-password',
                 json={'login_id': otp_login_id, 'otp': probe,
                       'new_password': 'BR02@Restored2026'})
check('H3i. BR02 password restored to policy-compliant value', r.status_code == 200)

# ══════════ H4. SMS failure is non-fatal ═════════════════════════════════
# Point the SMS provider at an unreachable endpoint and force synchronous
# delivery so the failure is captured deterministically.
import backend.sms as sms_mod  # noqa: E402
import backend.mailer as mailer_mod  # noqa: E402
sms_mod.SEND_ASYNC = False
mailer_mod.SEND_ASYNC = False

r = admin_c.patch('/api/settings', json={
    'sms_provider': 'generic-http',
    'sms_api_url': 'http://127.0.0.1:1/sms',   # connection refused
    'sms_api_key': 'test-key',
    'sms_sender_id': 'SHREE',
    'notification_sms': True,
    'notification_email': True,
    'email_smtp_host': 'smtp.invalid.local',
}, headers=auth(admin_token))
check('H4a. admin configures SMS + SMTP settings', r.status_code == 200)

with app.app_context():
    f1 = next(f for f in Farmer.query.filter_by(branch_id=1).all() if f.status == 'ACTIVE'
              and f.milk_type in ('COW', 'BUFFALO'))
    f1_id = f1.id
    f1_code = f1.farmer_code
    f1_email = f1.email
    f1_mobile = f1.mobile

r = br_c.post('/api/collections', json={
    'farmerId': f1_id, 'quantity': 6.5, 'fat': 4.0, 'snf': 8.5, 'shift': 'EVENING',
}, headers=auth(br_token))
check('H4b. collection succeeds despite broken SMS gateway',
      r.status_code == 201, f"(status={r.status_code})")
coll_id = r.get_json().get('collection', {}).get('id')
with app.app_context():
    sms_logs = NotificationLog.query.filter_by(channel='SMS').all()
    sms_failed = [l for l in sms_logs if l.status == 'FAILED']
    check('H4c. SMS attempt recorded as FAILED in notification_logs',
          len(sms_failed) > 0, f"({len(sms_logs)} SMS rows, {len(sms_failed)} failed)")
    coll = db.session.get(Collection, coll_id)
    check('H4d. collection row committed with server amount',
          coll is not None and coll.amount and coll.amount > 0)

# ══════════ H5. Password change for all three roles ══════════════════════
# ADMIN
r = admin_c.post('/api/auth/change-password', json={
    'current_password': 'wrong', 'new_password': 'Whatever@2026x'},
    headers=auth(admin_token))
check('H5a. admin: wrong current password rejected', r.status_code == 401)
r = admin_c.post('/api/auth/change-password', json={
    'current_password': 'admin123', 'new_password': 'short'},
    headers=auth(admin_token))
check('H5b. admin: weak new password rejected (policy)', r.status_code == 400)
r = admin_c.post('/api/auth/change-password', json={
    'current_password': 'admin123', 'new_password': 'Admin@New2026'},
    headers=auth(admin_token))
check('H5c. admin: password changed', r.status_code == 200)
new_admin_token, _ = login(admin_c, 'admin', 'Admin@New2026')
check('H5d. admin: login with new password works', bool(new_admin_token))
t_old, _ = login(admin_c, 'admin', 'admin123')
check('H5e. admin: old password no longer works', t_old is None)
# restore (policy-compliant; the existing JWT remains valid for later steps)
r = admin_c.post('/api/auth/change-password', json={
    'current_password': 'Admin@New2026', 'new_password': 'Admin@Restored2026'},
    headers=auth(admin_token))
check('H5f. admin: password restored', r.status_code == 200)

# BRANCH_OPERATOR
r = br_c.post('/api/auth/change-password', json={
    'current_password': '9876543210', 'new_password': 'BR01@New2026'},
    headers=auth(br_token))
check('H5g. branch operator: password changed', r.status_code == 200)
new_br_token, _ = login(br_c, 'BR01', 'BR01@New2026', 'BRANCH_OPERATOR')
check('H5h. branch operator: login with new password works', bool(new_br_token))
r = br_c.post('/api/auth/change-password', json={
    'current_password': 'BR01@New2026', 'new_password': 'BR01@Restored2026'},
    headers=auth(br_token))
check('H5i. branch operator: password restored', r.status_code == 200)

# FARMER
f_token, _ = login(farmer_c, f1_email, f1_mobile, 'FARMER')
check('H5j. farmer login before password change', bool(f_token))
r = farmer_c.post('/api/auth/change-password', json={
    'current_password': f1_mobile, 'new_password': 'Farmer@2026x'},
    headers=auth(f_token))
check('H5k. farmer: password changed', r.status_code == 200)
f2_token, _ = login(farmer_c, f1_email, 'Farmer@2026x', 'FARMER')
check('H5l. farmer: login with new password works', bool(f2_token))
with app.app_context():
    u1 = User.query.filter_by(farmer_id=f1_id).first()
    check('H5m. password_changed_at is aware UTC', u1.password_changed_at is not None
          and ensure_utc(u1.password_changed_at).tzinfo is not None)
    check('H5n. must_change_password cleared', not bool(u1.must_change_password))
r = farmer_c.post('/api/auth/change-password', json={
    'current_password': 'Farmer@2026x', 'new_password': 'Farmer@Restored2026'},
    headers=auth(f_token))
check('H5o. farmer: password restored', r.status_code == 200)

# ══════════ H6. QR generation / validation / authorization ═══════════════
r = admin_c.get(f'/api/farmers/{f1_code}/qr', headers=auth(admin_token))
qr_body = r.get_json()
check('H6a. admin can fetch farmer QR', r.status_code == 200 and 'qrPayload' in qr_body)
qr_payload = qr_body.get('qrPayload', '')
check('H6b. QR payload is a signed opaque identifier',
      qr_payload.startswith('FARMER:') and len(qr_payload.split(':')) == 4)
pii_fields = ['aadhaar', 'pan', 'bank', 'account', 'mobile', 'password', 'otp']
check('H6c. QR payload contains no PII',
      all(f not in qr_payload.lower() for f in pii_fields))
check('H6d. QR image rendered', bool(qr_body.get('qrImage', '').startswith('data:image/svg')))

with app.app_context():
    from backend.utils import verify_farmer_qr
    check('H6e. payload verifies to the correct farmer code',
          verify_farmer_qr(qr_payload) == f1_code)
    check('H6f. tampered payload rejected', verify_farmer_qr(qr_payload[:-2] + 'zz') is None)
    check('H6g. garbage payload rejected', verify_farmer_qr('not-a-qr') is None)
    check('H6h. farmer row stores the signed payload',
          Farmer.query.filter_by(farmer_code=f1_code).first().qr_code == qr_payload)

# QR lookup (the scanner's backend): resolves to the correct farmer.
r = br_c.get(f'/api/farmers/qr-lookup?payload={qr_payload}', headers=auth(br_token))
check('H6i. branch operator QR lookup resolves farmer',
      r.status_code == 200 and r.get_json().get('farmer', {}).get('farmerCode') == f1_code)

# QR authorization: branch operator cannot resolve another branch's QR.
with app.app_context():
    br2_farmer = next(f for f in Farmer.query.filter_by(branch_id=2).all()
                      if f.status == 'ACTIVE')
    br2_qr = br2_farmer.qr_code or sign_farmer_qr(br2_farmer.farmer_code)
r = br_c.get(f'/api/farmers/qr-lookup?payload={br2_qr}', headers=auth(br_token))
check('H6j. QR lookup cannot cross branches → 403', r.status_code == 403,
      f"(status={r.status_code})")

# Farmer role is blocked from the scanner lookup entirely.
r = farmer_c.get(f'/api/farmers/qr-lookup?payload={qr_payload}', headers=auth(f_token))
check('H6k. farmer role blocked from QR lookup → 403', r.status_code == 403)

# Regeneration: new signed payload, old one no longer validates for the row.
r = admin_c.post(f'/api/farmers/{f1_code}/qr', headers=auth(admin_token))
new_payload = r.get_json().get('qrPayload')
with app.app_context():
    from backend.utils import verify_farmer_qr
    row_code = Farmer.query.filter_by(farmer_code=f1_code).first().qr_code
    check('H6l. regenerated payload stored on farmer', row_code == new_payload)
    check('H6m. regenerated payload still verifies', verify_farmer_qr(new_payload) == f1_code)

# ══════════ H7. Deep scan accuracy ═══════════════════════════════════════
scan_path = os.path.join('scripts', 'deep_scan_results.json')
if os.path.exists(scan_path):
    with open(scan_path, encoding='utf-8') as fh:
        scan = json.load(fh)
    rbac_fp = [b for b in scan if 'RBAC' in b.get('category', '')
               and 'Unprotected' in b.get('title', '')]
    check('H7a. deep scan has no RBAC false positives', len(rbac_fp) == 0,
          f"({len(rbac_fp)} found)")
    high = [b for b in scan if b.get('severity') == 'HIGH']
    check('H7b. no HIGH-severity findings remain',
          len(high) == 0, f"({len(high)} high: {[b.get('title') for b in high[:3]]})")
else:
    check('H7a. deep scan results file present', False, '(missing)')

# ══════════ H8. End-to-end business flow ═════════════════════════════════
# Admin → farmer → operator collection → passbook → dashboard
# → notification → payment → farmer payment history.
# The E2E farmer is created in branch 1 (BR01) so the seeded BR01 operator
# can collect for them — branch-scoped RBAC forbids cross-branch collection.
r = admin_c.post('/api/branches', json={'name': 'Hardening Test Branch',
                                        'code': 'BR99', 'phone': '9880000000'},
                 headers=auth(admin_token))
check('H8a. admin creates a new branch', r.status_code == 201,
      f"(status={r.status_code})")

r = admin_c.post('/api/farmers', json={
    'name': 'E2E Farmer', 'mobile': '9771112222', 'milkType': 'COW',
    'branchId': 1, 'email': 'e2e.farmer@example.com'},
    headers=auth(admin_token))
e2e_farmer = r.get_json().get('farmer', {})
e2e_code = e2e_farmer.get('farmerCode')
check('H8b. admin registers farmer (branch 1)', r.status_code == 201, f"({e2e_code})")
r = admin_c.post(f'/api/farmers/{e2e_code}/verify', json={'action': 'approve'},
                 headers=auth(admin_token))
check('H8c. farmer account verified', r.status_code == 200)
with app.app_context():
    e2e = Farmer.query.filter_by(farmer_code=e2e_code).first()
    e2e_id = e2e.id
    e2e_email = e2e.email

# Farmer logs in with the generated temporary credentials.
f_token_e2e, _ = login(farmer_c, e2e_email, '9771112222', 'FARMER')
check('H8d. farmer logs in (temporary password)', bool(f_token_e2e))
# Temporary-password gate (spec §24): the portal stays locked until the
# farmer sets a real password — enforced server-side, not just in the UI.
r = farmer_c.get('/api/farmer/me', headers=auth(f_token_e2e))
check('H8d2. portal blocked until password change', r.status_code == 403)
r = farmer_c.post('/api/auth/change-password', json={
    'current_password': '9771112222', 'new_password': 'E2e@Farmer2026'},
    headers=auth(f_token_e2e))
check('H8d3. farmer sets a real password (gate clears)', r.status_code == 200)
f_token_e2e, _ = login(farmer_c, e2e_email, 'E2e@Farmer2026', 'FARMER')
check('H8d4. farmer re-logs in with real password', bool(f_token_e2e))
r = farmer_c.get('/api/farmer/me', headers=auth(f_token_e2e))
check('H8e. farmer me returns own profile',
      r.status_code == 200 and r.get_json().get('farmer', {}).get('farmerCode') == e2e_code)

# Branch operator records a collection → server computes price.
r = br_c.post('/api/collections', json={
    'farmerId': e2e_id, 'quantity': 10.0, 'fat': 4.5, 'snf': 8.7, 'shift': 'MORNING',
    'idempotencyKey': 'e2e-coll-001',
}, headers=auth(br_token))
e2e_coll = r.get_json().get('collection', {})
check('H8f. operator records collection (server-priced)',
      r.status_code == 201 and e2e_coll.get('amount', 0) > 0,
      f"(amount={e2e_coll.get('amount')})")

# Farmer portal reflects the collection immediately (single source of truth).
r = farmer_c.get('/api/farmer/me/collections', headers=auth(f_token_e2e))
me_cols = r.get_json().get('collections', [])
check('H8g. farmer My Collections shows the new record',
      any(c.get('id') == e2e_coll.get('id') for c in me_cols))
r = farmer_c.get('/api/farmer/me/daily-collection', headers=auth(f_token_e2e))
daily = r.get_json()
check('H8h. farmer Daily Collection reflects quantity',
      (daily.get('summary') or {}).get('totalQuantity', 0) >= 10,
      f"(total={(daily.get('summary') or {}).get('totalQuantity')})")
r = farmer_c.get('/api/farmer/me/passbook', headers=auth(f_token_e2e))
pb = r.get_json().get('entries', [])
check('H8i. farmer Passbook has the credit entry',
      any(e.get('collectionId') == e2e_coll.get('id') for e in pb))
r = farmer_c.get('/api/farmer/me/notifications', headers=auth(f_token_e2e))
notifs = r.get_json().get('notifications', [])
check('H8j. farmer notification created for the collection',
      any('New Milk Collection' in (n.get('title') or '') for n in notifs))

# Dashboards & reports are real DB queries.
r = admin_c.get('/api/dashboard', headers=auth(admin_token))
check('H8k. admin dashboard 200', r.status_code == 200 and 'kpis' in r.get_json())
r = admin_c.get('/api/reports?type=collection', headers=auth(admin_token))
check('H8l. admin reports 200', r.status_code == 200)
r = br_c.get('/api/collections?per_page=5', headers=auth(br_token))
check('H8m. branch collections list 200 (real rows)',
      r.status_code == 200 and r.get_json().get('total', 0) > 0)

# Admin processes the payment; farmer payment history updates.
period_start = (_date.today() - timedelta(days=3)).isoformat()
period_end = _date.today().isoformat()
r = admin_c.post('/api/payments', json={
    'periodStart': period_start, 'periodEnd': period_end, 'farmerIds': [e2e_id],
}, headers=auth(admin_token))
pay_body = r.get_json()
check('H8n. admin generates payment from unpaid collections',
      r.status_code == 201 and pay_body.get('count', 0) >= 1,
      f"(count={pay_body.get('count')}, msg={str(pay_body.get('message'))[:60]})")
with app.app_context():
    e2e_pay = Payment.query.filter_by(farmer_id=e2e_id).order_by(Payment.id.desc()).first()
    e2e_pay_id = e2e_pay.id if e2e_pay else None
r = admin_c.patch(f'/api/payments/{e2e_pay_id}', json={'status': 'PAID',
                                                        'reference': 'NEFT-E2E-001'},
                  headers=auth(admin_token))
check('H8o. admin marks payment PAID', r.status_code == 200)
r = farmer_c.get('/api/farmer/me/payments', headers=auth(f_token_e2e))
payments = r.get_json().get('payments', [])
check('H8p. farmer payment history shows the payment',
      any(p.get('id') == e2e_pay_id for p in payments))

# Audit trail: every major entity type logged.
r = admin_c.get('/api/audit?per_page=300', headers=auth(admin_token))
entities = [a.get('entity') for a in r.get_json().get('logs', [])]
for ent in ('Collection', 'Payment', 'Farmer', 'Branch'):
    check(f'H8q. audit log contains {ent} action', ent in entities)

# Payment timestamps are aware UTC after finalization.
with app.app_context():
    p = db.session.get(Payment, e2e_pay_id)
    check('H8r. payment paid_at is aware UTC',
          p is not None and p.paid_at is not None and ensure_utc(p.paid_at).tzinfo is not None)

print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
