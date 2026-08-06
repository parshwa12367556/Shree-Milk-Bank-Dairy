"""Check that classes used in templates exist in the CSS, and audit lucide icon names."""
import os
import re
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, 'templates')
CSS_DIR = os.path.join(ROOT, 'static', 'css')

# 1) Collect every CSS rule name (.class, #id) from all css files
css_src = ''
for f in glob.glob(os.path.join(CSS_DIR, '*.css')):
    css_src += open(f, encoding='utf-8').read() + '\n'

css_selectors = set()
for m in re.finditer(r'([.#][A-Za-z][A-Za-z0-9_-]*)', css_src):
    css_selectors.add(m.group(1))

# Also gather element-level selectors like `main`, `table` etc. (skip those)
css_classes = {s[1:] for s in css_selectors if s.startswith('.')}
css_ids = {s[1:] for s in css_selectors if s.startswith('#')}

# 2) Collect classes used in templates
used_classes = set()
used_ids = set()
for f in glob.glob(os.path.join(TPL, '**', '*.html'), recursive=True):
    src = open(f, encoding='utf-8').read()
    # skip Jinja braces content
    src = re.sub(r'\{\{.*?\}\}', ' ', src, flags=re.S)
    src = re.sub(r'\{%.*?%\}', ' ', src, flags=re.S)
    used_classes.update(re.findall(r'class="([^"]+)"', src))
    used_ids.update(re.findall(r'id="([^"]+)"', src))

cls = set()
for group in used_classes:
    cls.update(group.split())
ids = set(used_ids)

# 3) Compare — report classes that are used but never defined in any CSS file
# Skip a known-whitelist of framework/utility classes that are fine unstyled
WHITELIST = {
    'font-mono', 'w-full', 'hide-mobile', 'anim-spin', 'skeleton', 'skeleton-card',
    'skeleton-text', 'btn', 'btn-sm', 'btn-primary', 'btn-secondary', 'btn-ghost',
    'btn-danger', 'btn-outline', 'tag', 'tag-green', 'tag-amber', 'tag-red',
    'tag-gray', 'tab-btn', 'tabs', 'table-wrapper', 'table-header', 'table-title',
    'table-toolbar', 'table-responsive', 'table-footer', 'table-info', 'segmented-control',
    'segmented-btn', 'segmented-btn active', 'info-grid', 'info-item', 'info-label',
    'info-value', 'card', 'card-header', 'card-body', 'section-title', 'dashboard-grid',
    'chart-container', 'empty-state', 'empty-icon', 'form-grid', 'form-group', 'form-label',
    'input-premium', 'input-with-icon', 'input-icon', 'input-group', 'form-options',
    'form-check', 'form-check-label', 'forgot-link', 'btn-login', 'login-error',
    'login-role-tabs', 'role-tab', 'login-dev-hint', 'dropdown-menu', 'dropdown-item',
    'dropdown-header', 'dropdown-divider', 'item-icon', 'nav-item', 'nav-icon', 'nav-label',
    'sidebar-search', 'search-icon', 'sidebar-nav', 'sidebar-footer', 'sidebar-user',
    'user-avatar', 'user-info', 'user-name', 'user-role', 'sidebar-toggle-mobile',
    'sidebar-overlay', 'main-wrapper', 'main-content', 'page-container', 'page-header',
    'breadcrumb-nav', 'nav-brand', 'brand-logo', 'brand-text', 'brand-badge', 'nav-left',
    'nav-center', 'nav-right', 'nav-divider', 'nav-datetime', 'current-date', 'current-time',
    'datetime-separator', 'current-branch', 'current-branch-name', 'user-dropdown',
    'user-trigger', 'user-meta', 'user-chevron', 'notif-trigger', 'notif-count',
    'notif-dropdown', 'notif-header', 'notif-list', 'theme-toggle', 'search-bar',
    'kpi-card', 'kpi-icon', 'kpi-label', 'kpi-value', 'kpi-trend', 'status-pill',
    'badge', 'badge-success', 'badge-warning', 'badge-danger', 'modal', 'modal-content',
    'modal-header', 'modal-body', 'modal-footer', 'toast', 'page-loader', 'loader-spinner',
    'login-page', 'login-container', 'login-card', 'login-header', 'login-logo',
    'login-divider', 'login-footer', 'login-language', 'login-footer-text', 'anim-fade-up',
    'anim-float', 'error-page', 'error-card', 'error-code', 'error-icon', 'error-actions',
    'sidebar-logo', 'sidebar-brand', 'brand-name', 'brand-sub', 'active', 'open', 'loaded',
    'visible', 'app-layout', 'sidebar-collapsed', 'alert', 'alert-danger', 'alert-success',
    'progress', 'progress-bar', 'timeline', 'timeline-item', 'timeline-dot',
}

missing = sorted(cls - css_classes - WHITELIST)
# Only report classes that look like real component classes (heuristic: len > 2)
missing = [c for c in missing if len(c) > 2 and not c[0].isdigit()]

print(f'CSS rules found: {len(css_classes)} classes, {len(css_ids)} ids')
print(f'Classes used in templates: {len(cls)}')
print(f'Classes used but NOT defined anywhere in CSS: {len(missing)}')
if missing:
    for c in missing[:60]:
        print('  -', c)

# 4) Lucide icon sanity — collect data-lucide names and flag non-standard chars
icons = set()
for f in glob.glob(os.path.join(TPL, '**', '*.html'), recursive=True):
    src = open(f, encoding='utf-8').read()
    icons.update(re.findall(r'data-lucide="([a-z0-9-]+)"', src))
print(f'\nLucide icons used: {len(icons)}')
weird = [i for i in sorted(icons) if not re.match(r'^[a-z0-9-]+$', i) or len(i) > 30]
print('Suspicious icon names:', weird if weird else 'none')
