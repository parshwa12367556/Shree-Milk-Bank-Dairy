#!/usr/bin/env python3
"""SPA consolidation: resolve farmer-portal ID collisions and restore admin views.

1. Restore admin-side farmer_profile.html (git HEAD, minus blank chart canvases).
2. Rebuild admin-side farmer_passbook.html with a real passbook table.
3. Convert ported farmer portal pages into my_profile.html / my_passbook.html
   with unique containers and mp-* ids (no collisions with admin/shared pages).
4. Rename remaining colliding ids in farmer_*.html (fm-* prefixes).
5. Strip per-page <script src> tags (modules load centrally from _scripts.html).
6. Delete the redundant farmer_payment_status.html.
"""
import os
import re
import subprocess

PAGES = 'templates/index/pages'


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def write(p, content):
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(content)
    print(f'[ok] {p}')


def git_show(path):
    return subprocess.check_output(
        ['git', 'show', f'HEAD:{path}'], cwd='.', text=True
    ).replace('\r\n', '\n')


def strip_page_scripts(content):
    """Remove trailing <script src=...></script> blocks from page partials."""
    return re.sub(r'\s*<script src="[^"]*"></script>', '', content)


# ── 1. Restore admin-side Farmer Profile page ──
admin_profile = git_show(f'{PAGES}/farmer_profile.html')
# Remove the blank chart canvases (no data source -> no fake charts).
admin_profile = re.sub(
    r'\s*<!-- Charts -->.*?<div class="dashboard-grid">.*?</div>\s*</div>\s*</div>',
    '',
    admin_profile,
    flags=re.DOTALL,
)
# Give the passbook table a uniquely-id'd tbody the module can fill.
admin_profile = admin_profile.replace(
    '<tbody></tbody>',
    '<tbody id="profile-passbook-body"></tbody>',
)
write(f'{PAGES}/farmer_profile.html', admin_profile)

# ── 2. Rebuild admin-side Farmer Passbook page ──
admin_passbook = '''      <!-- ── Farmer Passbook (admin view) ── -->
      <div class="page-container" id="page-farmer-passbook" style="display:none;">
        <div class="breadcrumb">
          <a href="#dashboard">Dashboard</a>
          <span class="separator"><i data-lucide="chevron-right" style="width:12px;height:12px;"></i></span>
          <a href="#farmers">Farmers</a>
          <span class="separator"><i data-lucide="chevron-right" style="width:12px;height:12px;"></i></span>
          <span class="current">Passbook</span>
        </div>
        <div class="page-header">
          <div>
            <h2>Farmer Passbook</h2>
            <p class="subtitle">Complete collection & payment history</p>
          </div>
          <div class="page-actions">
            <button class="btn btn-secondary" data-action="print-passbook"><i data-lucide="printer" style="width:16px;height:16px;"></i> Print</button>
            <button class="btn btn-secondary" data-action="export-pdf"><i data-lucide="download" style="width:16px;height:16px;"></i> PDF</button>
          </div>
        </div>
        <div class="card" style="padding:var(--space-6);margin-bottom:var(--space-4);">
          <p id="passbook-header-text" style="color:var(--ink-muted);">Passbook for <strong>Farmer Name (Code)</strong></p>
        </div>
        <div class="table-wrapper">
          <div class="table-header">
            <div class="table-title">Collection History</div>
            <div class="table-toolbar">
              <button class="btn btn-sm btn-ghost" onclick="Table.exportCSV('passbook-table', 'passbook.csv')"><i data-lucide="download" style="width:16px;height:16px;"></i> Export</button>
            </div>
          </div>
          <div class="table-responsive">
            <table class="table-premium" id="passbook-table" style="width:100%;">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Receipt</th>
                  <th>Shift</th>
                  <th>Qty</th>
                  <th>Fat</th>
                  <th>SNF</th>
                  <th>Rate</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody id="passbook-body">
                <tr><td colspan="8" class="text-center" style="padding:var(--space-4);color:var(--ink-muted);font-size:var(--text-sm);">Loading passbook…</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
'''
write(f'{PAGES}/farmer_passbook.html', admin_passbook)

# ── 3. Convert ported pages to my_profile / my_passbook ──
my_profile = read(f'{PAGES}/farmer_profile.html')
my_profile = my_profile.replace('id="page-farmer-profile"', 'id="page-my-profile"')
my_profile = strip_page_scripts(my_profile)
write(f'{PAGES}/my_profile.html', my_profile)

my_passbook = read(f'{PAGES}/farmer_passbook.html')
my_passbook = strip_page_scripts(my_passbook)
# Container + unique ids (mp-*) so they never clash with admin passbook page.
renames = {
    'id="page-farmer-passbook"': 'id="page-my-passbook"',
    'id="filter-from"': 'id="mp-filter-from"',
    'id="filter-to"': 'id="mp-filter-to"',
    'id="passbook-total"': 'id="mp-passbook-total"',
    'id="passbook-table"': 'id="mp-passbook-table"',
    'id="passbook-body"': 'id="mp-passbook-body"',
    'id="passbook-pager-info"': 'id="mp-passbook-pager-info"',
    'id="passbook-prev"': 'id="mp-passbook-prev"',
    'id="passbook-next"': 'id="mp-passbook-next"',
    'pageFarmerPassbook': 'pageMyPassbook',
}
for old, new in renames.items():
    my_passbook = my_passbook.replace(old, new)
write(f'{PAGES}/my_passbook.html', my_passbook)

# ── 4. Rename colliding ids in the remaining ported pages ──
id_renames = {
    'farmer_dashboard.html': {'id="kpi-pending"': 'id="fm-kpi-pending"'},
    'farmer_collections.html': {'id="collections-table"': 'id="fm-collections-table"'},
    'farmer_notifications.html': {
        'id="notifications-list"': 'id="fm-notifications-list"',
        'id="notif-unread-tag"': 'id="fm-notif-unread-tag"',
    },
    'farmer_payments.html': {'id="payments-table"': 'id="fm-payments-table"'},
}
for fname, mapping in id_renames.items():
    path = os.path.join(PAGES, fname)
    content = read(path)
    for old, new in mapping.items():
        content = content.replace(old, new)
    content = strip_page_scripts(content)
    write(path, content)

# ── 5. Strip script tags from all remaining ported farmer pages ──
for fname in os.listdir(PAGES):
    if not fname.startswith('farmer_') or not fname.endswith('.html'):
        continue
    path = os.path.join(PAGES, fname)
    content = read(path)
    stripped = strip_page_scripts(content)
    if stripped != content:
        write(path, stripped)

# ── 6. Delete redundant payment status page ──
ps = os.path.join(PAGES, 'farmer_payment_status.html')
if os.path.exists(ps):
    os.remove(ps)
    print('[del] templates/index/pages/farmer_payment_status.html')

print('done.')
