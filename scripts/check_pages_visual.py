"""Verify branch/farmer/shared/error pages render with expected structural content."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from flask_jwt_extended import create_access_token
from backend.app import create_app

app = create_app()
c = app.test_client()


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


results = []

# ── Branch Manager pages ──
auth('BRANCH_MANAGER', 'BR01', branch_id=1)
results.append(check('/branch/dashboard', ['Branch', 'sidebar-nav'], 'branch dashboard'))
results.append(check('/branch/collection/morning', ['Morning Collection', 'sidebar-nav'], 'morning collection'))
results.append(check('/branch/collection/evening', ['Evening Collection'], 'evening collection'))
results.append(check('/branch/quality/testing', ['Quality Testing'], 'quality testing'))
results.append(check('/branch/quality/rejected', ['Rejected Milk'], 'rejected milk'))
results.append(check('/branch/farmers', ['Farmer List'], 'branch farmers'))
results.append(check('/branch/farmers/register', ['Register', 'Farmer'], 'register farmer'))
results.append(check('/branch/reports/daily', ['Daily Report'], 'daily report'))
results.append(check('/branch/inventory/allocated', ['Allocated Inventory'], 'allocated inventory'))
results.append(check('/branch/profile', ['Branch Profile'], 'branch profile'))

# ── Farmer portal ──
auth('FARMER', 'BR01001', branch_id=1)
results.append(check('/farmer/profile', ['My Profile', 'Farmer Portal'], 'farmer profile'))
results.append(check('/farmer/passbook', ['Passbook'], 'farmer passbook'))
results.append(check('/farmer/milk-history', ['Milk', 'Collection'], 'farmer milk history'))
results.append(check('/farmer/payments', ['Payment History'], 'farmer payments'))
results.append(check('/farmer/bank-details', ['Bank Details'], 'farmer bank'))
results.append(check('/farmer/notifications', ['Notifications'], 'farmer notifications'))

# ── Shared pages ──
auth('SUPER_ADMIN', 'admin')
results.append(check('/shared/profile', ['Profile'], 'shared profile'))
results.append(check('/shared/notifications', ['Notifications'], 'shared notifications'))
results.append(check('/shared/user-guide', ['User Guide', 'Guide'], 'user guide'))
results.append(check('/shared/help', ['Help'], 'help center'))
results.append(check('/shared/faq', ['FAQ'], 'faq'))
results.append(check('/shared/contact-support', ['Contact', 'Support'], 'contact support'))

# ── Error pages ──
r = c.get('/this-page-does-not-exist')
err_html = r.get_data(as_text=True)
results.append(r.status_code == 404 and '404' in err_html)
print(f'  [{"PASS" if r.status_code == 404 and "404" in err_html else "FAIL"}] styled 404 page')

print()
ok = all(results)
print('RESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
