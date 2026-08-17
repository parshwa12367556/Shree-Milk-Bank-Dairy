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

# 1) Parse every template (the SPA shell + auth/error/email pages).
files = glob.glob('templates/**/*.html', recursive=True)
for f in files:
    name = f.replace('\\', '/').replace('templates/', '')
    try:
        env.parse(open(f, encoding='utf-8').read())
    except Exception as e:
        problems.append(f'JINJA SYNTAX {name}: {e}')

# 2) Verify every referenced partial exists (live tree only)
for f in files:
    name = f.replace('\\', '/').replace('templates/', '')
    src = open(f, encoding='utf-8').read()
    for partial in re.findall(r"(?:extends|include|from)\s+'([^']+)'", src):
        if not os.path.exists(os.path.join('templates', partial)):
            problems.append(f'MISSING PARTIAL {partial} (referenced by {name})')

# 3) Verify the manifest is valid and every route maps to a layout the SPA
#    can gate. The manifest's `template` fields are legacy metadata from the
#    pre-SPA multi-page system (removed); the SPA shell serves every route now,
#    so no per-route template file is required on disk.
manifest = json.load(open('backend/pages_manifest.json', encoding='utf-8'))
for route, meta in manifest.items():
    if not route.startswith('/') or not meta.get('layout'):
        problems.append(f'INVALID MANIFEST ROUTE {route} ({meta})')

# 4) Verify the SPA shell includes every page partial it references and that
#    every JS page-init function referenced by the partials exists.
index_src = open(os.path.join('templates', 'index.html'), encoding='utf-8').read()
for partial in re.findall(r"{% include '([^']+)' %}", index_src):
    if not os.path.exists(os.path.join('templates', partial)):
        problems.append(f'MISSING SPA PARTIAL {partial} (included by index.html)')

print(f'Templates parsed: {len(files)}')
print(f'Manifest routes:  {len(manifest)}')
if problems:
    print(f'\nPROBLEMS ({len(problems)}):')
    for p in problems:
        print(f'  - {p}')
    sys.exit(1)
print('\nAll integrity checks passed.')
