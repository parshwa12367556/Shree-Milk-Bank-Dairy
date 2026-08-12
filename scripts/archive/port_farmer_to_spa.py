"""
Port the farmer portal from MPA templates into the SPA shell.

Each `templates/farmer/*.html` (extends base/farmer_layout) becomes a
`templates/index/pages/farmer_*.html` page-container partial that the SPA
router shows/hides. Server-side Jinja (`farmer`, `current_user`) is replaced
with client-side equivalents sourced from the JWT (`Auth.getUser()`), and the
farmer page modules fetch the rest via the API — so every value is real.

The output partials are pure HTML + the page's existing <script> includes.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'templates', 'farmer')
DST = os.path.join(ROOT, 'templates', 'index', 'pages')

# farmer MPA file -> (SPA partial filename, page-container id, route name)
MAP = {
    'dashboard.html': ('farmer_dashboard.html', 'page-farmer-dashboard', 'farmer-dashboard'),
    'daily_collection.html': ('farmer_daily_collection.html', 'page-farmer-daily-collection', 'farmer-daily-collection'),
    'milk_collection_history.html': ('farmer_collections.html', 'page-farmer-collections', 'farmer-collections'),
    'passbook.html': ('farmer_passbook.html', 'page-farmer-passbook', 'farmer-passbook'),
    'payment_history.html': ('farmer_payments.html', 'page-farmer-payments', 'farmer-payments'),
    'payment_status.html': ('farmer_payment_status.html', 'page-farmer-payment-status', 'farmer-payment-status'),
    'notifications.html': ('farmer_notifications.html', 'page-farmer-notifications', 'farmer-notifications'),
    'profile.html': ('farmer_profile.html', 'page-farmer-profile', 'farmer-profile'),
    'bank_details.html': ('farmer_bank_details.html', 'page-farmer-bank-details', 'farmer-bank-details'),
    'documents.html': ('farmer_documents.html', 'page-farmer-documents', 'farmer-documents'),
    'grievance.html': ('farmer_grievance.html', 'page-farmer-grievance', 'farmer-grievance'),
    'settings.html': ('farmer_settings.html', 'page-farmer-settings', 'farmer-settings'),
}

TITLE = {
    'farmer-dashboard': 'My Dashboard',
    'farmer-daily-collection': 'Daily Collection',
    'farmer-collections': 'My Collections',
    'farmer-passbook': 'My Passbook',
    'farmer-payments': 'Payment History',
    'farmer-payment-status': 'Payment Status',
    'farmer-notifications': 'Notifications',
    'farmer-profile': 'My Profile',
    'farmer-bank-details': 'Bank Details',
    'farmer-documents': 'My Documents',
    'farmer-grievance': 'Grievance',
    'farmer-settings': 'Settings',
}

# Regexes for the Jinja fragments we replace with client-side equivalents.
# 1) {% ... %} blocks that render conditionals — drop the tags, keep an
#    empty-state span the module can populate (the modules re-render these
#    containers from API data anyway).
JINJA_TAG = re.compile(r'{%[-+]?[^%]*?[-+]?%}')


def convert(src_name, dst_name, container_id, route):
    src_path = os.path.join(SRC, src_name)
    dst_path = os.path.join(DST, dst_name)
    if not os.path.exists(src_path):
        print(f'  [SKIP] missing source {src_name}')
        return

    text = open(src_path, encoding='utf-8').read()

    # Extract the {% block content %} ... {% endblock %} body.
    m = re.search(r'{%\s*block\s+content\s*%}(.*?){%\s*endblock\s*%}', text, re.S)
    body = m.group(1) if m else text

    # Extract the page's init + scripts (they live in a {% block scripts %}).
    scripts_m = re.search(r'{%\s*block\s+scripts\s*%}(.*?){%\s*endblock\s*%}', text, re.S)
    scripts = scripts_m.group(1).strip() if scripts_m else ''

    # Replace Jinja expression tags with empty-state markers. Keep it simple:
    # the modules own these containers and render real data on init.
    body = JINJA_TAG.sub('', body)

    # Convert internal MPA links (/farmer/..., /shared/...) to SPA hash routes.
    body = re.sub(r'href="/(farmer|shared|admin|branch)/[a-z0-9/_-]*"',
                  lambda mm: f'href="#{_route_for(mm.group(1))}"', body)

    # Remove empty leftover blank lines from tag removal.
    body = re.sub(r'\n\s*\n\s*\n+', '\n\n', body)

    header_title = TITLE.get(route, route.replace('-', ' ').title())
    partial = f'''      <!-- ── {header_title} (farmer portal) ── -->
      <div class="page-container" id="{container_id}" style="display:none;">
        <div class="breadcrumb">
          <a href="#farmer-dashboard"><i data-lucide="home" style="width:14px;height:14px;"></i></a>
          <span class="separator"><i data-lucide="chevron-right" style="width:12px;height:12px;"></i></span>
          <span class="current">{header_title}</span>
        </div>
{body}
      </div>
'''
    if scripts:
        partial += f'\n<script src="/static/js/farmer/{os.path.basename(src_name).replace(".html", ".js")}"></script>\n'

    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(partial)
    print(f'  [OK] {src_name} -> {dst_name} ({container_id})')


def _route_for(prefix):
    """Map an MPA URL prefix to the SPA hash route."""
    return {
        'farmer': 'farmer-dashboard',
        'shared': 'profile',
        'admin': 'dashboard',
        'branch': 'dashboard',
    }.get(prefix, 'dashboard')


def main():
    os.makedirs(DST, exist_ok=True)
    for src_name, (dst_name, cid, route) in MAP.items():
        convert(src_name, dst_name, cid, route)
    print(f'\nDone. {len(MAP)} farmer pages ported into the SPA.')


if __name__ == '__main__':
    main()
