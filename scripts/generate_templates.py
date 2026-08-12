"""
Smart Dairy ERP — Template Generator
====================================
Generates the multi-page Jinja2 template system under templates/.

Run:
    python scripts/generate_templates.py

The generator is idempotent: re-running it overwrites generated pages but
never touches hand-written files (base/, auth/, errors/).
"""
import json
import os
import sys

# Allow running from anywhere
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from page_registry_admin import ADMIN_PAGES
from page_registry_branch import BRANCH_PAGES
from page_registry_farmer import FARMER_PAGES
from page_registry_shared import SHARED_PAGES

TEMPLATES_DIR = os.path.join(ROOT, 'templates')

LAYOUT = {
    'admin': 'base/admin_layout.html',
    'branch': 'base/branch_layout.html',
    'farmer': 'base/farmer_layout.html',
    'shared': 'base/shared_layout.html',
}

# Page JS init mapping (existing SPA modules that can drive server pages).
# Only modules whose element IDs actually exist on the generated page are
# wired. The table id must match the `#xxx-table` each module queries.
PAGE_JS = {
    'admin/dashboard/dashboard.html': ('initDashboard', 'shared/dashboard.js', None),
    'branch/dashboard/dashboard.html': ('initDashboard', 'shared/dashboard.js', None),
    'admin/branch_management/branch_list.html': ('initBranches', 'admin/branches.js', 'branches-table'),
    'admin/payments/payment_dashboard.html': ('initPayments', 'admin/payments.js', 'payments-table'),
    'admin/inventory/inventory_dashboard.html': ('initInventory', 'admin/inventory.js', 'inventory-table'),
    'admin/employees/employee_dashboard.html': ('initEmployees', 'admin/employees.js', 'employees-table'),
    'admin/vehicles/vehicle_dashboard.html': ('initVehicles', 'admin/vehicles.js', 'vehicles-table'),
    'admin/audit/audit_dashboard.html': ('initAudit', 'admin/audit.js', 'audit-table'),
    'branch/quality/quality_testing.html': ('initQuality', 'branch/quality.js', 'quality-table'),
    'branch/quality/rejected_milk.html': ('initRejections', 'branch/rejections.js', 'rejections-table'),
    'branch/collection/morning_collection.html': ('initCollection', 'branch/collection.js', 'collections-table'),
}

# Generic table id per page (used when no module wiring exists)
TABLE_IDS = {
    'admin/branch_management/create_branch.html': 'branches-table',
    'admin/branch_management/edit_branch.html': 'branches-table',
    'admin/branch_management/branch_activity.html': 'branch-activity-table',
    'admin/farmer_management/farmer_list.html': 'farmers-table',
    'admin/farmer_management/farmer_verification.html': 'verification-table',
    'admin/farmer_management/bank_verification.html': 'bank-verification-table',
    'admin/farmer_management/farmer_documents.html': 'documents-table',
    'admin/farmer_management/payment_history.html': 'payments-table',
    'admin/farmer_management/milk_history.html': 'collections-table',
    'admin/farmer_management/farmer_activity.html': 'farmer-activity-table',
    'admin/payments/payment_sheet.html': 'payment-sheet-table',
    'admin/payments/pending_payments.html': 'payments-table',
    'admin/payments/approved_payments.html': 'payments-table',
    'admin/payments/paid_payments.html': 'payments-table',
    'admin/payments/failed_payments.html': 'payments-table',
    'admin/payments/payment_history.html': 'payments-table',
    'admin/payments/payment_reports.html': 'report-table',
    'admin/procurement/supplier_list.html': 'suppliers-table',
    'admin/procurement/purchase_orders.html': 'purchase-orders-table',
    'admin/procurement/goods_receipt_note.html': 'grn-table',
    'admin/procurement/delivery_tracking.html': 'delivery-table',
    'admin/procurement/vendor_payments.html': 'vendor-payments-table',
    'admin/procurement/procurement_reports.html': 'report-table',
    'admin/inventory/warehouse.html': 'warehouses-table',
    'admin/inventory/item_list.html': 'inventory-table',
    'admin/inventory/branch_allocation.html': 'allocation-table',
    'admin/inventory/inventory_history.html': 'inventory-history-table',
    'admin/inventory/low_stock.html': 'inventory-table',
    'admin/vehicles/vehicle_list.html': 'vehicles-table',
    'admin/vehicles/maintenance.html': 'maintenance-table',
    'admin/vehicles/insurance.html': 'insurance-table',
    'admin/vehicles/fuel_log.html': 'fuel-table',
    'admin/vehicles/service_history.html': 'service-history-table',
    'admin/employees/employee_list.html': 'employees-table',
    'admin/employees/attendance.html': 'attendance-table',
    'admin/employees/salary.html': 'salary-table',
    'admin/employees/leave_management.html': 'leave-table',
    'admin/settings/user_management.html': 'users-table',
    'admin/reports/reports_dashboard.html': 'report-table',
    'branch/farmer/farmer_list.html': 'farmers-table',
    'branch/farmer/farmer_documents.html': 'documents-table',
    'branch/farmer/milk_history.html': 'collections-table',
    'branch/farmer/payment_status.html': 'payments-table',
    'branch/farmer/passbook.html': 'passbook-table',
    'branch/collection/collection_history.html': 'collections-table',
    'branch/collection/bulk_collection.html': 'collections-table',
    'branch/quality/quality_history.html': 'quality-table',
    'branch/quality/lab_reports.html': 'lab-reports-table',
    'branch/inventory/allocated_inventory.html': 'inventory-table',
    'branch/inventory/inventory_history.html': 'inventory-history-table',
    'farmer/passbook.html': 'passbook-table',
    'farmer/milk_collection_history.html': 'collections-table',
    'farmer/payment_history.html': 'payments-table',
    'farmer/payment_status.html': 'payments-table',
    'farmer/documents.html': 'documents-table',
    'shared/activity_timeline.html': 'audit-table',
}


def write(path, content):
    full = os.path.join(TEMPLATES_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f'  + {path}')


# ── Content builders ─────────────────────────────────────────────

def build_kpis(kpis):
    if not kpis:
        return ''
    colors = {'green': 'kpi-green', 'gold': 'kpi-gold', 'blue': 'kpi-blue',
              'purple': 'kpi-purple', 'teal': 'kpi-teal', 'amber': 'kpi-amber',
              'red': 'kpi-red', 'cyan': 'kpi-cyan'}
    rows = []
    for kid, label, value, icon, color in kpis:
        rows.append(f'''
          <div class="kpi-card {colors.get(color, 'kpi-blue')}" id="{kid}">
            <div class="kpi-icon"><i data-lucide="{icon}" style="width:20px;height:20px;"></i></div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
          </div>''')
    return f'''
        <!-- KPI Cards -->
        <div class="kpi-grid">
{''.join(rows)}
        </div>'''


def build_actions(actions):
    if not actions:
        return ''
    btns = []
    for label, icon, variant in actions:
        cls = 'btn btn-primary' if variant == 'primary' else 'btn btn-secondary'
        btns.append(f'''
            <button class="{cls}" onclick="window.Modal && Modal.toast({{title:'Info', message:'This action is not wired yet.', type:'info'}})">
              <i data-lucide="{icon}" style="width:16px;height:16px;"></i>
              {label}
            </button>''')
    return f'''<div class="page-actions">{''.join(btns)}</div>'''


def build_table(cols, table_id=None, sample_rows=True):
    th = '\n                    '.join(f'<th>{c}</th>' for c in cols)
    if sample_rows:
        tds = '\n                  '.join(
            f'<td><span class="skeleton skeleton-text"></span></td>' for _ in cols)
        body = f'''
                  <tbody>
                    <tr>{tds}</tr>
                    <tr>{tds}</tr>
                  </tbody>'''
    else:
        body = '<tbody></tbody>'
    return f'''
        <div class="table-wrapper">
          <div class="table-header">
            <div class="table-title">{cols[0] if cols else 'Records'}</div>
            <div class="table-toolbar">
              <div class="segmented-control">
                <button class="segmented-btn active">All</button>
                <button class="segmented-btn">Recent</button>
              </div>
              <button class="btn btn-sm btn-ghost" title="Export CSV"><i data-lucide="download" style="width:16px;height:16px;"></i></button>
              <button class="btn btn-sm btn-ghost" title="Print"><i data-lucide="printer" style="width:16px;height:16px;"></i></button>
            </div>
          </div>
          <div class="table-responsive">
            <table class="table-premium" id="{table_id or 'data-table'}" style="width:100%;">
              <thead>
                <tr>
                  {th}
                </tr>
              </thead>{body}
            </table>
          </div>
          <div class="table-footer">
            <div class="table-info">Showing 1-10 of 124 entries</div>
            {{% from 'base/pagination.html' import pagination %}}
            {{{{ pagination(1, 13, request.path) }}}}
          </div>
        </div>'''


def build_toolbar(placeholder='Search...'):
    return f'''
        <!-- Toolbar -->
        <div class="toolbar">
          <div class="toolbar-left">
            <div class="search-bar" style="width:280px;">
              <span class="search-icon"><i data-lucide="search"></i></span>
              <input type="text" placeholder="{placeholder}">
            </div>
          </div>
          <div class="toolbar-right">
            <select style="padding:var(--space-1) var(--space-6) var(--space-1) var(--space-2);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--bg-surface);color:var(--ink);font-size:var(--text-sm);">
              <option>All Status</option>
              <option>Active</option>
              <option>Inactive</option>
              <option>Pending</option>
            </select>
            <button class="btn btn-sm btn-ghost" title="Export"><i data-lucide="download" style="width:16px;height:16px;"></i></button>
            <button class="btn btn-sm btn-ghost" title="Print"><i data-lucide="printer" style="width:16px;height:16px;"></i></button>
            <button class="btn btn-sm btn-ghost" title="Refresh"><i data-lucide="refresh-cw" style="width:16px;height:16px;"></i></button>
          </div>
        </div>'''


def build_form_sections(sections, page_key):
    out = []
    for num, (title, fields) in enumerate(sections, start=1):
        if not fields:
            out.append(f'''
              <div class="form-section">
                <h5 class="form-section-title">
                  <span class="section-number">{num}</span>
                  {title}
                </h5>
                <div class="empty-state" style="padding:var(--space-6);">
                  <div class="empty-icon"><i data-lucide="inbox"></i></div>
                  <p style="font-size:var(--text-sm);color:var(--ink-muted);">No items yet. Manage from the list view.</p>
                </div>
              </div>''')
            continue
        grid = []
        for label, name, ftype, required, placeholder in fields:
            req = ' <span class="required">*</span>' if required else ''
            if ftype == 'textarea':
                grid.append(f'''
                  <div class="form-group" style="grid-column:span 2;">
                    <label class="form-label">{label}{req}</label>
                    <textarea class="input-premium" name="{name}" placeholder="{placeholder}" rows="2"></textarea>
                  </div>''')
            elif ftype == 'checkbox':
                grid.append(f'''
                  <div class="form-group" style="grid-column:span 2;">
                    <label class="form-check">
                      <input type="checkbox" name="{name}" checked>
                      <span class="form-check-label">{label}</span>
                    </label>
                  </div>''')
            elif ftype == 'toggle':
                grid.append(f'''
                  <div class="form-group" style="grid-column:span 1;">
                    <label class="form-label">{label}</label>
                    <label class="switch">
                      <input type="checkbox" name="{name}" checked>
                      <span class="switch-slider"></span>
                    </label>
                  </div>''')
            elif ftype == 'select':
                options = placeholder.split('/')
                opts = ''.join(
                    f'<option value="{o.strip().upper()}">{o.strip()}</option>' for o in options)
                grid.append(f'''
                  <div class="form-group">
                    <label class="form-label">{label}{req}</label>
                    <select class="input-premium" name="{name}">
                      <option value="">Select</option>
                      {opts}
                    </select>
                  </div>''')
            else:
                grid.append(f'''
                  <div class="form-group">
                    <label class="form-label">{label}{req}</label>
                    <input type="{ftype}" class="input-premium" name="{name}" placeholder="{placeholder}">
                  </div>''')
        out.append(f'''
              <div class="form-section">
                <h5 class="form-section-title">
                  <span class="section-number">{num}</span>
                  {title}
                </h5>
                <div class="form-grid">
{''.join(grid)}
                </div>
              </div>''')
    return f'''
        <div class="card">
          <div class="card-body">
            <form id="form-{page_key}">
{''.join(out)}
              <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="history.back()">Cancel</button>
                <button type="submit" class="btn btn-primary btn-lg">
                  <i data-lucide="save" style="width:18px;height:18px;"></i>
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>'''


def build_profile_blocks(page, table_id=None):
    tabs = page.get('tabs', ['Overview', 'Activity'])
    tab_btns = '\n'.join(
        f'<button class="tab-btn {"active" if i == 0 else ""}">{t}</button>'
        for i, t in enumerate(tabs))
    return f'''
        <!-- Profile Header -->
        <div class="card" style="padding:var(--space-6);margin-bottom:var(--space-5);">
          <div style="display:flex;align-items:center;gap:var(--space-4);flex-wrap:wrap;">
            <div style="width:72px;height:72px;border-radius:var(--radius-full);background:linear-gradient(135deg,var(--forest-light),var(--forest));display:flex;align-items:center;justify-content:center;font-size:1.6rem;color:white;font-weight:700;flex-shrink:0;">
              {{{{ current_user.name[:2]|upper if current_user and current_user.name else 'PR' }}}}
            </div>
            <div style="flex:1;min-width:220px;">
              <h3 style="margin-bottom:var(--space-1);">{page.get('title', 'Profile')}</h3>
              <p style="color:var(--ink-muted);font-size:var(--text-sm);">ID: <span class="font-mono">—</span> · Status: <span class="tag tag-green">Active</span></p>
            </div>
            <div style="display:flex;gap:var(--space-2);">
              <button class="btn btn-secondary"><i data-lucide="edit-3" style="width:16px;height:16px;"></i> Edit</button>
              <button class="btn btn-primary"><i data-lucide="download" style="width:16px;height:16px;"></i> Export</button>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="tabs" style="margin-bottom:var(--space-5);">
          {tab_btns}
        </div>

        <!-- Overview tab -->
        <div class="card">
          <div class="card-header">
            <h5 class="section-title">Overview</h5>
          </div>
          <div class="card-body">
            <div class="info-grid">
              <div class="info-item"><span class="info-label">Full Name</span><span class="info-value">—</span></div>
              <div class="info-item"><span class="info-label">Mobile</span><span class="info-value">—</span></div>
              <div class="info-item"><span class="info-label">Email</span><span class="info-value">—</span></div>
              <div class="info-item"><span class="info-label">Address</span><span class="info-value">—</span></div>
            </div>
            <div class="skeleton skeleton-text" style="margin-top:var(--space-4);"></div>
            <div class="skeleton skeleton-text"></div>
          </div>
        </div>'''


def build_report_block(page, table_id=None):
    return f'''
        <!-- Report Filters -->
        <div class="card" style="padding:var(--space-5);margin-bottom:var(--space-5);">
          <div class="form-grid" style="grid-template-columns:repeat(auto-fit,minmax(180px,1fr));">
            <div class="form-group">
              <label class="form-label">From Date</label>
              <input type="date" class="input-premium">
            </div>
            <div class="form-group">
              <label class="form-label">To Date</label>
              <input type="date" class="input-premium">
            </div>
            <div class="form-group">
              <label class="form-label">Branch</label>
              <select class="input-premium"><option>All Branches</option></select>
            </div>
            <div class="form-group">
              <label class="form-label">&nbsp;</label>
              <button class="btn btn-primary w-full"><i data-lucide="search" style="width:16px;height:16px;"></i> Generate</button>
            </div>
          </div>
        </div>

        <!-- Report Charts -->
        <div class="dashboard-grid">
          <div class="card">
            <div class="card-header">
              <h5 class="section-title">Summary Chart</h5>
            </div>
            <div class="card-body">
              <div class="chart-container">
                <canvas id="chart-report-1"></canvas>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-header">
              <h5 class="section-title">Trend</h5>
            </div>
            <div class="card-body">
              <div class="chart-container">
                <canvas id="chart-report-2"></canvas>
              </div>
            </div>
          </div>
        </div>

        {build_table(page.get('cols', ['Date', 'Value']), table_id=table_id or 'report-table')}'''


def build_audit_block(page, table_id=None):
    return f'''
        <!-- Filter Tabs -->
        <div class="card" style="padding:var(--space-4);margin-bottom:var(--space-5);">
          <div class="segmented-control">
            <button class="segmented-btn active">All</button>
            <button class="segmented-btn">Today</button>
            <button class="segmented-btn">Last 7 Days</button>
            <button class="segmented-btn">This Month</button>
          </div>
        </div>

        {build_toolbar('Search logs...')}

        {build_table(page.get('cols', ['Time', 'User', 'Action']), table_id=table_id or 'audit-table')}'''


def build_dashboard_block(page, table_id=None):
    kpis = build_kpis(page.get('kpis'))
    charts = f'''
        <div class="dashboard-grid">
          <div class="card">
            <div class="card-header">
              <h5 class="section-title">Trend</h5>
              <div class="segmented-control">
                <button class="segmented-btn active">14 Days</button>
                <button class="segmented-btn">30 Days</button>
              </div>
            </div>
            <div class="card-body">
              <div class="chart-container">
                <canvas id="chart-trend"></canvas>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-header">
              <h5 class="section-title">Breakdown</h5>
            </div>
            <div class="card-body">
              <div class="chart-container">
                <canvas id="chart-breakdown"></canvas>
              </div>
            </div>
          </div>
        </div>'''
    return kpis + charts + f'''
        <div style="height:var(--space-5);"></div>
        {build_table(page.get('cols', ['Date', 'Value']), table_id=table_id or 'recent-table')}'''


def build_simple_block(page, table_id=None):
    return f'''
        <div class="card">
          <div class="card-body" style="text-align:center;padding:var(--space-10);">
            <div class="empty-icon" style="margin:0 auto var(--space-4);"><i data-lucide="{page.get('icon', 'info')}" style="width:48px;height:48px;"></i></div>
            <h4 style="margin-bottom:var(--space-2);">{page.get('title')}</h4>
            <p style="color:var(--ink-muted);max-width:440px;margin:0 auto;">{page.get('subtitle')}</p>
            <div style="margin-top:var(--space-6);display:flex;gap:var(--space-3);justify-content:center;flex-wrap:wrap;">
              <button class="btn btn-primary"><i data-lucide="refresh-cw" style="width:16px;height:16px;"></i> Refresh</button>
              <button class="btn btn-secondary" onclick="history.back()"><i data-lucide="arrow-left" style="width:16px;height:16px;"></i> Go Back</button>
            </div>
          </div>
        </div>'''


def build_list_block(page, table_id=None):
    tid = table_id or TABLE_IDS.get(page.get('file'), 'data-table')
    return build_toolbar() + '\n' + build_table(page.get('cols', ['Name', 'Status']), table_id=tid)


def build_settings_block(page, table_id=None):
    return build_form_sections(page.get('sections', []), page['route'].split('/')[-1])


TYPE_BUILDERS = {
    'dashboard': build_dashboard_block,
    'list': build_list_block,
    'form': lambda p, table_id=None: build_form_sections(p.get('sections', []), p['route'].split('/')[-1]),
    'profile': build_profile_blocks,
    'report': build_report_block,
    'audit': build_audit_block,
    'settings': build_settings_block,
    'simple': build_simple_block,
}


# ── Page assembly ────────────────────────────────────────────────

def root_crumb(layout):
    if layout == 'branch':
        return 'Dashboard', '/branch/dashboard'
    if layout == 'farmer':
        return 'My Profile', '/farmer/profile'
    if layout == 'shared':
        return 'Dashboard', '/admin/dashboard'
    return 'Dashboard', '/admin/dashboard'


def assemble(page, init_name=None, js_file=None, table_id=None):
    layout = LAYOUT[page['layout']]
    root_label, root_url = root_crumb(page['layout'])
    title = page['title']
    subtitle = page.get('subtitle', '')
    section = page.get('section', '')
    page_key = page.get('page', '')
    content = TYPE_BUILDERS.get(page['type'], build_simple_block)(page, table_id=table_id)

    js_scripts = ''
    if js_file:
        js_scripts = f'\n<script src="/static/js/{js_file}"></script>'
    page_init = init_name or ''

    tpl = f"""{{% extends '{layout}' %}}
{{% set active_page = '{page_key}' %}}
{{% set active_section = '{section}' %}}
{{% block page_title %}}{title}{{% endblock %}}
{{% block page_init %}}{page_init}{{% endblock %}}

{{% block page_header %}}
{{% from 'base/breadcrumb.html' import breadcrumb %}}
{{{{ breadcrumb([{{'url': '{root_url}', 'label': '{root_label}'}}, {{'url': '', 'label': '{title}'}}]) }}}}
<div class="page-header">
  <div>
    <h2>{title}</h2>
    <p class="subtitle">{subtitle}</p>
  </div>
  {build_actions(page.get('actions', []))}
</div>
{{% endblock %}}

{{% block content %}}
{content}
{{% endblock %}}

{{% block scripts %}}{js_scripts}
<script>
document.addEventListener('DOMContentLoaded', () => {{
  if (window.Chart && document.getElementById('chart-trend')) {{
    AppCharts.lineChart('chart-trend', ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], [{{label:'Collection', data:[40,55,48,62,58,70,66], borderColor:'#2e7d32', backgroundColor:'rgba(46,125,50,0.12)', fill:true, tension:0.3}}]);
  }}
  if (window.Chart && document.getElementById('chart-breakdown')) {{
    AppCharts.doughnutChart('chart-breakdown', ['Cow','Buffalo','Mixed'], [45,35,20]);
  }}
  if (window.Chart && document.getElementById('chart-report-1')) {{
    AppCharts.barChart('chart-report-1', ['W1','W2','W3','W4'], [{{label:'Value', data:[120,145,132,158]}}]);
  }}
  if (window.Chart && document.getElementById('chart-report-2')) {{
    AppCharts.lineChart('chart-report-2', ['W1','W2','W3','W4'], [{{label:'Trend', data:[90,110,105,128], borderColor:'#d4a043', backgroundColor:'rgba(212,160,67,0.12)', fill:true, tension:0.3}}]);
  }}
}});
</script>
{{% endblock %}}
"""
    return tpl


def main():
    print('Smart Dairy ERP — Template Generator')
    print('=' * 46)
    all_pages = ADMIN_PAGES + BRANCH_PAGES + FARMER_PAGES + SHARED_PAGES
    print(f'Generating {len(all_pages)} pages...\n')

    for page in all_pages:
        init_name = None
        js_file = None
        table_id = None
        js_key = page.get('file')
        if js_key in PAGE_JS:
            init_name, js_file, table_id = PAGE_JS[js_key]
        tpl = assemble(page, init_name=init_name, js_file=js_file, table_id=table_id)
        write(page['file'], tpl)

    # ── Route manifest for the backend pages blueprint ──
    # Hand-written pages (real, data-driven templates that are NOT regenerated
    # from the registries) are merged in afterwards so re-running this script
    # never drops them or overwrites them with skeletons.
    HAND_WRITTEN_ROUTES = {
        '/admin/collections': {'template': 'admin/collections/collections.html', 'layout': 'admin',
                               'title': 'Milk Collections', 'section': 'collections', 'page': 'collections'},
        '/admin/grievances': {'template': 'admin/grievances/grievances.html', 'layout': 'admin',
                              'title': 'Farmer Grievances', 'section': 'grievances', 'page': 'grievances'},
        '/branch/milk-collection': {'template': 'branch/collection/morning_collection.html', 'layout': 'branch',
                                    'title': 'Milk Collection', 'section': 'collection', 'page': 'morning_collection'},
        '/branch/payments': {'template': 'branch/payments/payment_history.html', 'layout': 'branch',
                             'title': 'Payment History', 'section': 'payments', 'page': 'payments'},
        '/branch/notifications': {'template': 'branch/notifications.html', 'layout': 'branch',
                                  'title': 'Notifications', 'section': 'notifications', 'page': 'notifications'},
        '/farmer/daily-collection': {'template': 'farmer/daily_collection.html', 'layout': 'farmer',
                                     'title': 'Daily Collection', 'section': 'collections', 'page': 'daily_collection'},
        '/farmer/settings': {'template': 'farmer/settings.html', 'layout': 'farmer',
                             'title': 'Settings', 'section': 'settings', 'page': 'settings'},
        '/farmer/grievance/new': {'template': 'farmer/grievance.html', 'layout': 'farmer',
                                  'title': 'New Grievance', 'section': 'grievance', 'page': 'grievance'},
    }
    manifest = {}
    for page in all_pages:
        manifest[page['route']] = {
            'template': page['file'],
            'layout': page['layout'],
            'title': page['title'],
            'section': page.get('section', ''),
            'page': page.get('page', ''),
        }
    manifest.update(HAND_WRITTEN_ROUTES)
    manifest_path = os.path.join(ROOT, 'backend', 'pages_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f'\nManifest written: backend/pages_manifest.json ({len(manifest)} routes)')
    print(f'Done. Generated {len(all_pages)} template pages.')


if __name__ == '__main__':
    main()
