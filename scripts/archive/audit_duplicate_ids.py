#!/usr/bin/env python3
"""Audit duplicate DOM ids across SPA page partials."""
import os
import re
from collections import defaultdict

pages_dir = 'templates/index/pages'
by_id = defaultdict(list)

for fname in sorted(os.listdir(pages_dir)):
    if not fname.endswith('.html'):
        continue
    path = os.path.join(pages_dir, fname)
    with open(path, encoding='utf-8') as fh:
        content = fh.read()
    for m in re.finditer(r'id="([a-z0-9-]+)"', content):
        by_id[m.group(1)].append(fname)

print('=== DUPLICATE IDs (appear in >1 page partial) ===')
for cid, files in sorted(by_id.items()):
    if len(files) > 1:
        farmer = [f for f in files if f.startswith('farmer_') or f.startswith('my_')]
        other = [f for f in files if not (f.startswith('farmer_') or f.startswith('my_'))]
        tag = ' <-- FARMER COLLISION' if farmer and other else ''
        print(f'{cid:35s} {", ".join(files)}{tag}')
