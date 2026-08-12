"""
Production cleanup — remove hardcoded KPI values from MPA templates.

Any `.kpi-value` containing a fabricated figure (₹ amounts, "148 / 312",
"286 L", "4.2%", "₹18.6L") is replaced with a skeleton placeholder so the
page can never display invented business data. Real values are set by the
page modules (or show "—" when empty).

Idempotent.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, 'templates')

# Templates known to contain hardcoded KPI values that are NOT overwritten
# by their JS module (checked against static/js/* init functions).
TARGETS = [
    'admin/dashboard/analytics.html',
    'admin/dashboard/company_statistics.html',
    'admin/dashboard/revenue_dashboard.html',
    'admin/employees/employee_dashboard.html',
    'admin/inventory/inventory_dashboard.html',
    'admin/payments/payment_dashboard.html',
    'admin/procurement/procurement_dashboard.html',
    'admin/vehicles/vehicle_dashboard.html',
    'branch/collection/evening_collection.html',
    'branch/collection/morning_collection.html',
    'branch/quality/quality_testing.html',
]

# Fabricated-looking values: ₹ amounts (incl. 12.4L / 18.6L / 6.8Cr), N / N
# counts, "<number> L", "<float>%" — but NOT plain "0", "—", or tag text.
FAKE_RE = re.compile(
    r'(₹\s*[\d,]+\.?\d*[LC]?|\d[\d,]*\s*/\s*\d[\d,]*|>[\s]*\d+\.?\d*\s*L<|'
    r'[+-]?\d+\.\d+\s*%|[>]\s*[\d,]+\.?\d*\s*%<)'
)

SKELETON = '<div class="skeleton skeleton-text" style="height:1.4rem;width:60%;margin-top:0.25rem;"></div>'


def fix_file(rel):
    full = os.path.join(TEMPLATES, rel)
    if not os.path.exists(full):
        print(f'  [SKIP] missing {rel}')
        return
    text = open(full, encoding='utf-8').read()
    if 'kpi-value' not in text:
        print(f'  [SKIP] no kpi cards {rel}')
        return

    orig = text
    # Replace the inner content of every .kpi-value whose text matches FAKE_RE
    def repl(m):
        content = m.group(0)
        if FAKE_RE.search(content):
            return f'<div class="kpi-value">{SKELETON}</div>'
        return content

    new_text = re.sub(r'<div class="kpi-value">([^<]*?)(?:<[^>]*>[^<]*</[^>]*>)*[^<]*?</div>', repl, text)
    if new_text != orig:
        open(full, 'w', encoding='utf-8').write(new_text)
        print(f'  [FIX] {rel}: skeleton-ized hardcoded KPI values')
    else:
        # Fallback: simpler per-line approach
        lines = text.split('\n')
        changed = 0
        for i, line in enumerate(lines):
            if 'kpi-value' in line and FAKE_RE.search(line):
                lines[i] = re.sub(
                    r'<div class="kpi-value">.*?</div>',
                    f'<div class="kpi-value">{SKELETON}</div>',
                    line,
                )
                changed += 1
        if changed:
            open(full, 'w', encoding='utf-8').write('\n'.join(lines))
            print(f'  [FIX] {rel}: skeleton-ized {changed} KPI line(s)')
        else:
            print(f'  [WARN] no fake KPI matched {rel}')


def main():
    for rel in TARGETS:
        fix_file(rel)

    # Report any remaining suspicious values across templates for manual review
    print('\n=== remaining suspicious values (review) ===')
    for root, _, files in os.walk(TEMPLATES):
        for fn in files:
            if not fn.endswith('.html'):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, TEMPLATES).replace('\\', '/')
            for i, line in enumerate(open(p, encoding='utf-8'), 1):
                if FAKE_RE.search(line) and 'kpi-value' in line:
                    print(f'  {rel}:{i}: {line.strip()[:90]}')


if __name__ == '__main__':
    main()
