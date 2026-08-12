"""
Clean up the ported farmer SPA partials:
  1. Remove leftover Jinja {{ ... }} expressions (replace with '—').
  2. Fix <script src> filenames to the real module names in static/js/farmer/.
  3. Remove empty leftover <span class="tag"> blocks from stripped conditionals
     that are not data-driven (they are re-rendered by the modules).
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'templates', 'index', 'pages')

# module name for each partial (actual files in static/js/farmer/)
MODULE = {
    'farmer_dashboard.html': 'dashboard.js',
    'farmer_daily_collection.html': 'daily-collection.js',
    'farmer_collections.html': 'milk-collection.js',
    'farmer_passbook.html': 'passbook.js',
    'farmer_payments.html': 'payments.js',
    'farmer_payment_status.html': 'payments.js',
    'farmer_notifications.html': 'notifications.js',
    'farmer_profile.html': 'profile.js',
    'farmer_bank_details.html': 'bank-details.js',
    'farmer_documents.html': 'documents.js',
    'farmer_grievance.html': 'grievance.js',
    'farmer_settings.html': 'settings.js',
}

JINJA = re.compile(r"\{\{.*?\}\}")

for fname, module in MODULE.items():
    path = os.path.join(DST, fname)
    if not os.path.exists(path):
        print(f'  [SKIP] {fname}')
        continue
    text = open(path, encoding='utf-8').read()
    orig = text

    # Replace Jinja expressions with an em-dash (client module fills real data)
    text = JINJA.sub('—', text)

    # Remove stacked empty tag lines left over from stripped {% if %} blocks
    text = re.sub(r'(\s*<span class="tag tag-[a-z]+">—?</span>\s*){2,}', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Point script src at the real module
    text = re.sub(
        r'<script src="/static/js/farmer/[^"]*\.js"></script>',
        f'<script src="/static/js/farmer/{module}"></script>',
        text,
    )

    if text != orig:
        open(path, 'w', encoding='utf-8').write(text)
        print(f'  [FIX] {fname} (module {module})')
    else:
        print(f'  [OK]  {fname} no changes')

# Report any leftovers
print('\n=== leftover {{ or {% in ported pages ===')
for fn in sorted(os.listdir(DST)):
    if not fn.startswith('farmer_'):
        continue
    t = open(os.path.join(DST, fn), encoding='utf-8').read()
    n = len(re.findall(r"\{\{|\{%", t))
    if n:
        print(f'  {fn}: {n} jinja tags remain')
