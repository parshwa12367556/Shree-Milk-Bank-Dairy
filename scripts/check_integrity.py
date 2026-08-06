"""
Final integrity check — verifies every template is valid Jinja2, every
referenced partial exists, and the manifest matches the files on disk.

Run:
    python scripts/check_integrity.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.chdir(ROOT)

from jinja2 import Environment, FileSystemLoader  # noqa: E402

env = Environment(loader=FileSystemLoader('templates'), autoescape=True)
problems = []

# 1) Parse every template
files = glob.glob('templates/**/*.html', recursive=True)
for f in files:
    name = f.replace('\\', '/').replace('templates/', '')
    try:
        env.parse(open(f, encoding='utf-8').read())
    except Exception as e:
        problems.append(f'JINJA SYNTAX {name}: {e}')

# 2) Verify every referenced partial exists
for f in files:
    name = f.replace('\\', '/').replace('templates/', '')
    src = open(f, encoding='utf-8').read()
    for partial in re.findall(r"(?:extends|include|from)\s+'([^']+)'", src):
        if not os.path.exists(os.path.join('templates', partial)):
            problems.append(f'MISSING PARTIAL {partial} (referenced by {name})')

# 3) Verify manifest routes map to existing files
manifest = json.load(open('backend/pages_manifest.json', encoding='utf-8'))
for route, meta in manifest.items():
    if not os.path.exists(os.path.join('templates', meta['template'])):
        problems.append(f'MISSING TEMPLATE {meta["template"]} (route {route})')

# 4) Verify specific wired pages have their expected table IDs and that
#    the page_init block is filled (it renders the <body data-page-init> attr
#    via base.html).
wired = {
    'admin/branch_management/branch_list.html': ('branches-table', 'initBranches'),
    'admin/payments/payment_dashboard.html': ('payments-table', 'initPayments'),
    'admin/inventory/inventory_dashboard.html': ('inventory-table', 'initInventory'),
    'admin/employees/employee_dashboard.html': ('employees-table', 'initEmployees'),
    'admin/vehicles/vehicle_dashboard.html': ('vehicles-table', 'initVehicles'),
    'admin/audit/audit_dashboard.html': ('audit-table', 'initAudit'),
    'branch/quality/quality_testing.html': ('quality-table', 'initQuality'),
    'branch/quality/rejected_milk.html': ('rejections-table', 'initRejections'),
    'branch/collection/morning_collection.html': ('collections-table', 'initCollection'),
    'admin/dashboard/dashboard.html': (None, 'initDashboard'),
    'branch/dashboard/dashboard.html': (None, 'initDashboard'),
}
for tpl, (tid, init) in wired.items():
    src = open(os.path.join('templates', tpl), encoding='utf-8').read()
    if tid and f'id="{tid}"' not in src:
        problems.append(f'MISSING TABLE ID {tid} in {tpl}')
    if f'{{% block page_init %}}{init}{{% endblock %}}' not in src:
        problems.append(f'MISSING page_init block {init} in {tpl}')

print(f'Templates parsed: {len(files)}')
print(f'Manifest routes:  {len(manifest)}')
if problems:
    print(f'\nPROBLEMS ({len(problems)}):')
    for p in problems:
        print(f'  - {p}')
    sys.exit(1)
print('\nAll integrity checks passed.')
