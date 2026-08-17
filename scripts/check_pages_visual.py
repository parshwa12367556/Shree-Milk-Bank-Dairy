"""
Verify role-gated routes serve the SPA shell with the correct role gate.

The SPA (templates/index.html) is the single canonical frontend: every
role-gated deep link serves the shell, so checks validate:
  1. the route returns 200 and renders the SPA shell, and
  2. the expected SPA page container is present in the shell.
Role-mismatch requests must be redirected to /unauthorized.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from flask_jwt_extended import create_access_token
from backend.app import create_app

app = create_app()
c = app.test_client()

SPA_MARKER = 'Shree Milk Bank'


def auth(role, username, branch_id=None):
    ident = {'uid': 9, 'username': username, 'name': 'Tester', 'role': role,
             'branchId': branch_id, 'branchName': 'Nippani Branch'}
    with app.app_context():
        tok = create_access_token(identity=json.dumps(ident))
    c.set_cookie('access_token', tok)


def check(path, must_contain, label):
    r = c.get(path)
    html = r.get_data(as_text=True)
    ok = r.status_code == 200 and all(m in html for m in must_contain)
    missing = [m for m in must_contain if m not in html] if r.status_code == 200 else ['<page error>']
    print(f'  [{"PASS" if ok else "FAIL"}] {label} ({path}) {r.status_code}' + (f' missing={missing}' if not ok else ''))
    return ok


def gated(path, label):
    """Verify the route is 302-redirected when the user lacks the role."""
    r = c.get(path)
    ok = r.status_code == 302 and '/unauthorized' in r.headers.get('Location', '')
    print(f'  [{"PASS" if ok else "FAIL"}] {label} ({path}) {r.status_code} -> {r.headers.get("Location", "-")}')
    return ok


results = []

# ── Branch Operator pages → SPA shell with branch containers ──
auth('BRANCH_MANAGER', 'BR01', branch_id=1)
results.append(check('/branch/dashboard', [SPA_MARKER, 'id="page-dashboard"'], 'branch dashboard'))
results.append(check('/branch/collection/morning', [SPA_MARKER, 'id="page-collection"'], 'morning collection'))
results.append(check('/branch/collection/evening', [SPA_MARKER, 'id="page-collection"'], 'evening collection'))
results.append(check('/branch/milk-collection', [SPA_MARKER, 'id="page-collection"'], 'milk collection'))
results.append(check('/branch/quality/testing', [SPA_MARKER, 'id="page-quality"'], 'quality testing'))
results.append(check('/branch/quality/rejected', [SPA_MARKER, 'id="page-rejections"'], 'rejected milk'))
results.append(check('/branch/farmers', [SPA_MARKER, 'id="page-farmers"'], 'branch farmers'))
results.append(check('/branch/farmers/register', [SPA_MARKER, 'id="page-farmer-form"'], 'register farmer'))
results.append(check('/branch/reports/daily', [SPA_MARKER, 'id="page-reports"'], 'daily report'))
results.append(check('/branch/payments', [SPA_MARKER, 'id="page-payments"'], 'branch payments (view only)'))
results.append(check('/branch/profile', [SPA_MARKER, 'id="page-profile"'], 'branch profile'))

# Branch operator must NOT reach admin-only routes
results.append(gated('/admin/branches', 'branch blocked from admin branches'))

# ── Farmer pages → SPA shell with farmer portal containers ──
auth('FARMER', 'BR01001', branch_id=1)
results.append(check('/farmer/dashboard', [SPA_MARKER, 'id="page-farmer-dashboard"'], 'farmer dashboard'))
results.append(check('/farmer/profile', [SPA_MARKER, 'id="page-my-profile"'], 'farmer profile'))
results.append(check('/farmer/passbook', [SPA_MARKER, 'id="page-my-passbook"'], 'farmer passbook'))
results.append(check('/farmer/milk-history', [SPA_MARKER, 'id="page-farmer-collections"'], 'farmer milk history'))
results.append(check('/farmer/payments', [SPA_MARKER, 'id="page-farmer-payments"'], 'farmer payments'))
results.append(check('/farmer/bank-details', [SPA_MARKER, 'id="page-farmer-bank-details"'], 'farmer bank'))
results.append(check('/farmer/notifications', [SPA_MARKER, 'id="page-farmer-notifications"'], 'farmer notifications'))
results.append(check('/farmer/grievance', [SPA_MARKER, 'id="page-farmer-grievance"'], 'farmer grievance'))
results.append(check('/farmer/daily-collection', [SPA_MARKER, 'id="page-farmer-daily"'], 'farmer daily collection'))
results.append(check('/farmer/settings', [SPA_MARKER, 'id="page-farmer-settings"'], 'farmer settings'))
results.append(check('/farmer/grievance/1', [SPA_MARKER], 'farmer grievance detail'))

# Farmer must NOT reach admin/branch routes
results.append(gated('/admin/dashboard', 'farmer blocked from admin'))
results.append(gated('/branch/dashboard', 'farmer blocked from branch'))

# ── Admin pages → SPA shell ──
auth('ADMIN', 'admin')
results.append(check('/admin/dashboard', [SPA_MARKER, 'id="page-dashboard"'], 'admin dashboard'))
results.append(check('/admin/farmers', [SPA_MARKER, 'id="page-farmers"'], 'admin farmers'))
results.append(check('/admin/branches', [SPA_MARKER, 'id="page-branches"'], 'admin branches'))
results.append(check('/admin/collections', [SPA_MARKER, 'id="page-collection"'], 'admin collections'))
results.append(check('/admin/payments/dashboard', [SPA_MARKER, 'id="page-payments"'], 'admin payments'))
results.append(check('/admin/settings/company', [SPA_MARKER, 'id="page-settings"'], 'admin settings'))

# ── Shared pages ──
results.append(check('/shared/profile', [SPA_MARKER, 'id="page-profile"'], 'shared profile'))
results.append(check('/shared/notifications', [SPA_MARKER, 'id="page-notifications"'], 'shared notifications'))
results.append(check('/shared/user-guide', [SPA_MARKER, 'id="page-guide"'], 'user guide'))
results.append(check('/shared/help', [SPA_MARKER, 'id="page-help"'], 'help center'))

# ── Removed fake dashboard sub-pages are gone ──
auth('ADMIN', 'admin')
r = c.get('/admin/analytics')
print(f'  [{"PASS" if r.status_code == 404 else "FAIL"}] fake analytics page removed ({r.status_code})')
results.append(r.status_code == 404)

# ── Error pages ──
r = c.get('/this-page-does-not-exist')
err_html = r.get_data(as_text=True)
results.append(r.status_code == 404 and '404' in err_html)
print(f'  [{"PASS" if r.status_code == 404 and "404" in err_html else "FAIL"}] styled 404 page')

# ── Unauthenticated → redirect to login ──
c.set_cookie('access_token', '')
r = c.get('/admin/dashboard')
ok = r.status_code == 302 and '/login' in r.headers.get('Location', '')
results.append(ok)
print(f'  [{"PASS" if ok else "FAIL"}] unauthenticated redirected to login ({r.status_code} -> {r.headers.get("Location", "-")})')

print()
ok = all(results)
print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
sys.exit(0 if ok else 1)
