#!/usr/bin/env python3
"""Remove the fake dashboard sub-pages (pure static shells with dummy charts)
from pages_manifest.json and delete their template files."""
import json
import os

MANIFEST = 'backend/pages_manifest.json'
FAKE_ROUTES = {
    '/admin/analytics': 'admin/dashboard/analytics.html',
    '/admin/company-statistics': 'admin/dashboard/company_statistics.html',
    '/admin/branch-comparison': 'admin/dashboard/branch_comparison.html',
    '/admin/revenue-dashboard': 'admin/dashboard/revenue_dashboard.html',
    '/admin/profit-loss-dashboard': 'admin/dashboard/profit_loss_dashboard.html',
}

with open(MANIFEST, encoding='utf-8') as fh:
    manifest = json.load(fh)

removed = []
for route in list(FAKE_ROUTES):
    if route in manifest:
        del manifest[route]
        removed.append(route)

with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(manifest, fh, indent=2, ensure_ascii=False)
    fh.write('\n')

print('Removed from manifest:', removed or 'none')

for route, tpl in FAKE_ROUTES.items():
    path = os.path.join('templates', tpl)
    if os.path.exists(path):
        os.remove(path)
        print(f'[del] {path}')

print(f'Manifest now has {len(manifest)} routes.')
