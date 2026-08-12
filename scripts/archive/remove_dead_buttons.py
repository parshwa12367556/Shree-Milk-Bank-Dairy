"""
Production cleanup — remove all "not wired yet" header buttons.

For each template with a dead button, either:
  * wire it to a real server-rendered route that exists (link), or
  * drop the button entirely when the action has no page (feature absent).

Keeps the icon + label and styling; only the onclick/toast wiring changes.
Idempotent: safe to run repeatedly.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, 'templates')

# template path -> action. 'href' means the button becomes a real link;
# 'remove' means the dead button is deleted.
MAP = {
    # ── Admin: branches ──
    'admin/branch_management/branch_list.html': ('/admin/branches/create', 'plus', 'Add Branch'),
    # ── Admin: employees ──
    'admin/employees/employee_list.html': ('/admin/employees/add', 'user-plus', 'Add Employee'),
    'admin/employees/employee_dashboard.html': ('/admin/employees/add', 'user-plus', 'Add Employee'),
    'admin/employees/attendance.html': ('/admin/employees/add', 'user-plus', 'Add Employee'),
    # salary / leave-management have no create page -> remove buttons
    'admin/employees/salary.html': None,
    'admin/employees/leave_management.html': None,
    # ── Admin: farmers ──
    'admin/farmer_management/farmer_list.html': ('/admin/farmers/register', 'user-plus', 'Register Farmer'),
    # verification has no dedicated page -> remove
    'admin/farmer_management/farmer_verification.html': None,
    # ── Admin: inventory ──
    'admin/inventory/inventory_dashboard.html': ('/admin/items/create', 'plus', 'Add Item'),
    'admin/inventory/item_list.html': ('/admin/items/create', 'plus', 'Add Item'),
    'admin/inventory/warehouse.html': ('/admin/items/create', 'plus', 'Add Item'),
    'admin/inventory/branch_allocation.html': ('/admin/inventory/dashboard', 'layers', 'Allocate Stock'),
    'admin/inventory/low_stock.html': ('/admin/items/create', 'plus', 'Add Item'),
    # ── Admin: payments ──
    'admin/payments/payment_dashboard.html': ('/admin/payments/sheet', 'plus', 'New Payment Sheet'),
    'admin/payments/payment_sheet.html': ('/admin/payments/sheet', 'file-plus', 'New Payment Sheet'),
    'admin/payments/pending_payments.html': ('/admin/payments/sheet', 'plus', 'New Payment Sheet'),
    'admin/payments/approved_payments.html': ('/admin/payments/sheet', 'banknote', 'New Payment Sheet'),
    'admin/payments/paid_payments.html': ('/admin/reports/payments', 'download', 'Export Report'),
    'admin/payments/failed_payments.html': ('/admin/reports/payments', 'download', 'Export Report'),
    # ── Admin: procurement ──
    'admin/procurement/procurement_dashboard.html': ('/admin/purchase-orders/create', 'plus', 'New Purchase Order'),
    'admin/procurement/purchase_orders.html': ('/admin/purchase-orders/create', 'plus', 'New Purchase Order'),
    'admin/procurement/supplier_list.html': ('/admin/procurement/suppliers', 'plus', 'Add Supplier'),
    # ── Admin: vehicles ──
    'admin/vehicles/vehicle_dashboard.html': ('/admin/vehicles/add', 'plus', 'Add Vehicle'),
    'admin/vehicles/vehicle_list.html': ('/admin/vehicles/add', 'plus', 'Add Vehicle'),
    'admin/vehicles/maintenance.html': ('/admin/vehicles/dashboard', 'wrench', 'Maintenance'),
    'admin/vehicles/fuel_log.html': ('/admin/vehicles/dashboard', 'fuel', 'Fuel Log'),
    'admin/vehicles/insurance.html': ('/admin/vehicles/dashboard', 'shield-check', 'Insurance'),
    # ── Admin: audit ──
    'admin/audit/audit_dashboard.html': ('/admin/audit/activity-logs', 'download', 'Export Logs'),
    # ── Admin: settings ──
    'admin/settings/user_management.html': ('/admin/settings/users', 'user-plus', 'Manage Users'),
    # ── Admin: dashboard sub-pages (no create actions) → remove dead buttons ──
    'admin/dashboard/analytics.html': None,
    'admin/dashboard/branch_comparison.html': None,
    'admin/dashboard/company_statistics.html': None,
    'admin/dashboard/notifications.html': None,
    'admin/dashboard/profit_loss_dashboard.html': None,
    'admin/dashboard/revenue_dashboard.html': None,
    # ── Branch ──
    'branch/collection/morning_collection.html': ('/branch/collection/morning', 'layers', 'Bulk Entry'),
    'branch/collection/evening_collection.html': ('/branch/collection/evening', 'layers', 'Bulk Entry'),
    'branch/collection/bulk_collection.html': ('/branch/collection/morning', 'list', 'Morning Collection'),
    'branch/farmer/farmer_list.html': ('/branch/farmers/register', 'user-plus', 'Register Farmer'),
    'branch/quality/quality_testing.html': ('/branch/quality/testing', 'plus', 'New Test'),
    'branch/quality/rejected_milk.html': ('/branch/quality/rejected', 'plus', 'Record Rejection'),
    # ── Shared ──
    'shared/notifications.html': None,
}

DEAD_RE = re.compile(
    r'\s*<button class="btn (btn-[a-z-]+)" onclick="window\.Modal && Modal\.toast\([^)]*\)">'
    r'\s*<i data-lucide="([^"]+)"[^>]*></i>\s*\n\s*([^<\n]+?)\s*\n\s*</button>',
    re.MULTILINE,
)


def fix_template(rel_path, action):
    full = os.path.join(TEMPLATES, rel_path)
    if not os.path.exists(full):
        print(f'  [SKIP] missing: {rel_path}')
        return False
    with open(full, encoding='utf-8') as f:
        text = f.read()
    if 'not wired yet' not in text:
        print(f'  [SKIP] no dead button: {rel_path}')
        return False

    def repl(m):
        icon = m.group(2)
        label = m.group(3).strip()
        if action is None:
            return ''
        href, _, _ = action
        return (f'\n            <a class="btn {m.group(1)}" href="{href}">'
                f'<i data-lucide="{icon}" style="width:16px;height:16px;"></i>'
                f' {label}</a>')

    new_text, n = DEAD_RE.subn(repl, text)
    if n == 0:
        # Fallback: some buttons have a different label layout — strip by toast marker
        print(f'  [WARN] pattern not matched: {rel_path}')
        return False
    with open(full, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print(f'  [FIX] {rel_path}: replaced {n} dead button(s)')
    return True


def main():
    fixed = 0
    for rel, action in sorted(MAP.items()):
        if fix_template(rel, action):
            fixed += 1
    print(f'\nDone: {fixed} templates cleaned.')


if __name__ == '__main__':
    main()
