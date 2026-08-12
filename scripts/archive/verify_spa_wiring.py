#!/usr/bin/env python3
"""Verify the SPA shell wiring: routes -> page containers -> init functions."""
import re
import sys
import urllib.request

BASE = 'http://127.0.0.1:5000'
html = urllib.request.urlopen(BASE + '/', timeout=10).read().decode('utf-8')

# 1. All page containers present
containers = set(re.findall(r'id="(page-[a-z0-9-]+)"', html))
routes = [
    'dashboard', 'login', 'collection', 'farmers', 'farmer-form',
    'farmer-profile', 'farmer-passbook', 'branches', 'payments', 'pricing',
    'quality', 'rejections', 'procurement', 'inventory', 'employees',
    'vehicles', 'expenses', 'reports', 'audit', 'settings', 'notifications',
    'profile', 'help', 'guide',
    'farmer-dashboard', 'farmer-collections', 'farmer-daily', 'my-passbook',
    'farmer-payments', 'farmer-notifications', 'my-profile',
    'farmer-bank-details', 'farmer-documents', 'farmer-grievance',
    'farmer-settings', '404',
]
missing = [r for r in routes if f'page-{r}' not in containers]
print(f'containers found: {len(containers)}')
print('MISSING containers:', missing or 'none')

# 2. All farmer module scripts loaded
scripts = re.findall(r'<script src="(/static/js/[^"]+)"', html)
farmer_modules = [
    'farmer/dashboard.js', 'farmer/milk-collection.js',
    'farmer/daily-collection.js', 'farmer/passbook.js', 'farmer/payments.js',
    'farmer/notifications.js', 'farmer/profile.js', 'farmer/bank-details.js',
    'farmer/documents.js', 'farmer/grievance.js', 'farmer/settings.js',
]
missing_scripts = [m for m in farmer_modules if f'/static/js/{m}' not in scripts]
print('MISSING farmer scripts:', missing_scripts or 'none')
print('total scripts:', len(scripts))

# 3. Init functions referenced by routes exist in the loaded JS bundle
router_js = urllib.request.urlopen(BASE + '/static/js/core/router.js', timeout=10).read().decode('utf-8')
inits = set(re.findall(r"init: '([A-Za-z0-9_]+)'", router_js))
for script in scripts:
    try:
        js = urllib.request.urlopen(BASE + script, timeout=10).read().decode('utf-8')
        for init in list(inits):
            if f'window.{init}' in js:
                inits.discard(init)
    except Exception as e:
        print(f'!! cannot fetch {script}: {e}')
print('ROUTES WITHOUT INIT FUNCTION:', inits or 'none')
print('OK' if not missing and not missing_scripts and not inits else 'ISSUES FOUND')
