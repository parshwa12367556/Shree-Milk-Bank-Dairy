"""Audit all HTML templates for broken static references and structural issues."""
import os
import re
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, 'templates')
STATIC = os.path.join(ROOT, 'static')

issues = []
html_files = glob.glob(os.path.join(TPL, '**', '*.html'), recursive=True)
print(f'Scanning {len(html_files)} HTML files...')

# 1) Static references that point to missing files
ref_re = re.compile(r'(?:href|src)="(/static/[^"]+)"')
missing_static = {}
for f in html_files:
    src = open(f, encoding='utf-8').read()
    for m in ref_re.finditer(src):
        path = m.group(1)
        local = path.replace('/static/', '', 1)
        full = os.path.join(STATIC, local.replace('/', os.sep))
        if not os.path.exists(full):
            missing_static.setdefault(path, []).append(os.path.relpath(f, TPL))
if missing_static:
    for path, files in missing_static.items():
        issues.append(f'MISSING STATIC {path}  <- {", ".join(sorted(set(files))[:5])}')
else:
    print('  OK: no missing static file references')

# 2) Auth layout uses only auth-related css (login.css + core) — check auth pages render standalone
# 3) Template inheritance: every page extends a base layout that exists
extend_re = re.compile(r"{%\s*extends\s+['\"]([^'\"]+)['\"]")
missing_base = {}
for f in html_files:
    src = open(f, encoding='utf-8').read()
    m = extend_re.search(src)
    if m:
        base = m.group(1)
        if not os.path.exists(os.path.join(TPL, base)):
            missing_base.setdefault(base, []).append(os.path.relpath(f, TPL))
if missing_base:
    for base, files in missing_base.items():
        issues.append(f'MISSING EXTENDS {base}  <- {", ".join(sorted(set(files))[:5])}')
else:
    print('  OK: all extends targets exist')

# 4) Includes that point to missing files
inc_re = re.compile(r"{%\s*include\s+['\"]([^'\"]+)['\"]")
missing_inc = {}
for f in html_files:
    src = open(f, encoding='utf-8').read()
    for m in inc_re.finditer(src):
        inc = m.group(1)
        if not os.path.exists(os.path.join(TPL, inc)):
            missing_inc.setdefault(inc, []).append(os.path.relpath(f, TPL))
if missing_inc:
    for inc, files in missing_inc.items():
        issues.append(f'MISSING INCLUDE {inc}  <- {", ".join(sorted(set(files))[:5])}')
else:
    print('  OK: all includes exist')

# 5) Unclosed tags / unbalanced divs (rough heuristic)
#    Skip templates/index/ — those are intentional SPA fragments split at
#    structural boundaries (e.g. _layout_open.html opens .app-layout that
#    _main_close.html closes); div balance only holds for whole documents.
INDEX_FRAGMENTS = os.path.join(TPL, 'index') + os.sep
for f in html_files:
    if f.startswith(INDEX_FRAGMENTS):
        continue
    src = open(f, encoding='utf-8').read()
    body = re.sub(r'<!--.*?-->', '', src, flags=re.S)
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S)
    opens = len(re.findall(r'<div[\s>]', body))
    closes = len(re.findall(r'</div>', body))
    if opens != closes:
        issues.append(f'UNBALANCED DIVS ({opens} open / {closes} close): {os.path.relpath(f, TPL)}')

# 6) Empty or placeholder-only pages (look for 'skeleton' only content or stray {{ }} )
placeholder_re = re.compile(r'\{\{.*?\}\}')
for f in html_files:
    src = open(f, encoding='utf-8').read()
    # unrendered jinja variables in output
    unrendered = placeholder_re.findall(src)
    bad = [u for u in unrendered if 'current_user' in u or 'farmer.' in u or 'config.' in u or 'breadcrumb(' in u and 'import' not in u]
    if bad:
        issues.append(f'POSSIBLE UNRENDERED VAR {bad[0][:60]} in {os.path.relpath(f, TPL)}')

print()
if issues:
    print(f'=== {len(issues)} ISSUE(S) FOUND ===')
    for i in issues:
        print(' -', i)
else:
    print('=== NO ISSUES FOUND ===')
