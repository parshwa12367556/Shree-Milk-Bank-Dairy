#!/usr/bin/env python3
"""Verify security hardening. Run scenarios as separate subprocesses because
config values are read from the environment at import time.

Usage: python scripts/verify_security_hardening.py [scenario]
"""
import os
import sys
import json

os.environ['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
os.environ.setdefault('DEV_LOGIN_ENABLED', '1')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app import create_app  # noqa: E402

app = create_app()
c = app.test_client()
scenario = sys.argv[1] if len(sys.argv) > 1 else ''

if scenario == 'production-no-secrets':
    # SECRET_KEY must be missing in this subprocess → create_app raises.
    print('scenario=production-no-secrets: app already imported — this should not run')
    sys.exit(2)

if scenario == 'production-bypass-off':
    check = []
    ok = True
    try:
        r = c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'ADMIN'})
        bypass = app.config.get('DEV_LOGIN_ENABLED')
        check.append(('DEV_LOGIN_ENABLED is False in production', bypass is False, str(bypass)))
        check.append(('dev bypass auto-creation is off (config gate)', bypass is False, ''))
        r = c.post('/api/auth/forgot-password', json={'username': 'admin'})
        body = r.get_json() or {}
        check.append(('production: dev_otp not leaked', 'dev_otp' not in body, f"keys={sorted(body.keys())}"))
        for name, cond, info in check:
            print(f'  [{"PASS" if cond else "FAIL"}] {name}: {info}')
            ok = ok and cond
    except RuntimeError as exc:
        print(f'  FAIL production config: {exc}')
        ok = False
    print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
    sys.exit(0 if ok else 1)

if scenario == 'bypass-does-not-activate-inactive-admin':
    # The bypass must NOT auto-activate a deliberately INACTIVE admin.
    from backend.models import User
    from backend.auth import hash_password
    with app.app_context():
        u = User.query.filter_by(username='admin').first()
        if not u:
            print('FAIL: no admin user in DB')
            sys.exit(1)
        u.status = 'INACTIVE'
        u.password_hash = hash_password('totally-different-password')
        from backend.app import db
        db.session.commit()
    r = c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'ADMIN'})
    ok = r.status_code == 401
    print(f'  [{"PASS" if ok else "FAIL"}] dev bypass does not activate inactive admin: status={r.status_code}')
    print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
    sys.exit(0 if ok else 1)

if scenario == 'rate-limit':
    codes = set()
    for _ in range(25):
        r = c.post('/api/auth/login', json={'username': 'nope', 'password': 'nope'})
        codes.add(r.status_code)
    ok = 429 in codes
    print(f'  [{"PASS" if ok else "FAIL"}] rate limit returns 429 after burst: {codes}')
    print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
    sys.exit(0 if ok else 1)

if scenario == 'secure-cookie':
    r = c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'ADMIN'})
    ok = 'Secure' in r.headers.get('Set-Cookie', '')
    print(f'  [{"PASS" if ok else "FAIL"}] cookie flagged Secure: {r.headers.get("Set-Cookie", "")[:60]}')
    print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
    sys.exit(0 if ok else 1)

if scenario == 'health':
    r = c.get('/health')
    body = r.get_json() or {}
    ok = r.status_code == 200 and body.get('database') == 'up'
    print(f'  [{"PASS" if ok else "FAIL"}] /health db up: {r.status_code} {body.get("database")}')
    r = c.get('/api/health')
    ok = ok and r.status_code == 200
    print(f'  [{"PASS" if ok else "FAIL"}] /api/health alias: {r.status_code}')
    print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
    sys.exit(0 if ok else 1)

print('unknown scenario')
sys.exit(2)
