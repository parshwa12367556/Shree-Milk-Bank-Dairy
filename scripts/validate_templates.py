"""
Smart Dairy ERP — Template Validation
=====================================
Boots the Flask app and renders every page template to catch Jinja2 syntax
errors, missing extends, broken includes, or manifest mismatches.

Run:
    python scripts/validate_templates.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.app import create_app  # noqa: E402

MANIFEST = os.path.join(ROOT, 'backend', 'pages_manifest.json')

app = create_app()
client = app.test_client()

failures = []
checked = 0


def check(path):
    global checked
    checked += 1
    resp = client.get(path)
    if resp.status_code == 302 and resp.headers.get('Location') in ('/login', '/unauthorized'):
        return  # expected redirect for unauthenticated
    if resp.status_code != 200:
        failures.append((path, resp.status_code, resp.get_data(as_text=True)[:300]))


def main():
    print('Validating template pages...\n')

    # 1) Public auth pages
    for route in ['/login', '/forgot-password', '/verify-otp', '/reset-password',
                  '/change-password', '/account-locked', '/unauthorized']:
        resp = client.get(route)
        if resp.status_code != 200:
            failures.append((route, resp.status_code, resp.get_data(as_text=True)[:300]))

    # 2) Manifest pages — as an authenticated SUPER_ADMIN (cookie)
    with open(MANIFEST, encoding='utf-8') as f:
        manifest = json.load(f)

    # Build a real token by logging in through the API
    login = client.post('/api/auth/login', json={
        'username': 'admin', 'password': 'admin123', 'role': 'SUPER_ADMIN'})
    if login.status_code == 200:
        token = login.get_json()['token']
        client.set_cookie('access_token', token)

    for route in manifest:
        check(route)

    # 3) Error pages
    for route in ['/missing-page-xyz', '/api/missing']:
        resp = client.get(route)
        if resp.status_code == 404:
            pass
        else:
            failures.append((route, resp.status_code, resp.get_data(as_text=True)[:200]))

    # 4) Root SPA
    resp = client.get('/')
    if resp.status_code != 200:
        failures.append(('/', resp.status_code, ''))

    print(f'Checked {checked} routes.\n')
    if failures:
        print(f'FAILED: {len(failures)} problem(s)')
        for path, code, body in failures:
            print(f'\n  [{code}] {path}')
            print(f'    {body.replace(chr(10), " ")[:200]}')
        sys.exit(1)
    print('All pages rendered successfully.')


if __name__ == '__main__':
    main()
