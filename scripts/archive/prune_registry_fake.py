#!/usr/bin/env python3
"""Remove fake dashboard sub-page entries from scripts/page_registry_admin.py."""
import re

FAKE_ROUTES = [
    '/admin/analytics',
    '/admin/company-statistics',
    '/admin/branch-comparison',
    '/admin/revenue-dashboard',
    '/admin/profit-loss-dashboard',
]

path = 'scripts/page_registry_admin.py'
with open(path, encoding='utf-8') as fh:
    src = fh.read()

for route in FAKE_ROUTES:
    marker = f"dict(route='{route}',"
    start = src.find(marker)
    if start == -1:
        print(f'{route}: not found')
        continue
    # Include the leading newline so we don't leave a blank line.
    if start > 0 and src[start - 1] == '\n':
        start -= 1
    # The block ends at the next top-level "    dict(" or the end of the list.
    nxt = src.find('\n    dict(', start + 10)
    end = nxt if nxt != -1 else len(src)
    # Trim a trailing blank line left between blocks.
    removed = src[start:end]
    src = src[:start] + src[end:]
    print(f'{route}: removed {len(removed)} chars')

with open(path, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(src)

left = [r for r in FAKE_ROUTES if f"route='{r}'" in src]
print('STILL PRESENT:', left or 'none')
