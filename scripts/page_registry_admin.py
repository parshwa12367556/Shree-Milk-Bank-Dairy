"""
Smart Dairy ERP — Admin page registry for the template generator.

Each entry:
  route    — URL path (also used by the backend pages blueprint)
  file     — template file under templates/
  layout   — 'admin' | 'branch' | 'farmer' | 'shared'
  title    — page title
  subtitle — page subtitle
  icon     — lucide icon name
  section  — sidebar section name (active_section)
  page     — sidebar page key (active_page)
  type     — 'dashboard' | 'list' | 'form' | 'profile' | 'report' | 'settings' | 'audit' | 'simple'
  cols     — table column headers (list pages)
  kpis     — list of (id, label, value, icon, color)
  actions  — list of header action buttons
  sections — form sections: (title, [(label, name, type, required, placeholder)])
  tabs     — profile tabs
"""

ADMIN_PAGES = [
    # ── Dashboard ────────────────────────────────────────────────
    dict(route='/admin/dashboard', file='admin/dashboard/dashboard.html', layout='admin',
         title='Dashboard', subtitle="Welcome back! Here's what's happening today.",
         icon='layout-dashboard', section='dashboard', page='dashboard', type='dashboard',
         kpis=[
             ('kpi-collection', 'Today Collection', '1,240 L', 'milk', 'green'),
             ('kpi-revenue', 'Revenue', '₹4,82,300', 'indian-rupee', 'gold'),
             ('kpi-farmers', 'Active Farmers', '1,247', 'users', 'blue'),
             ('kpi-pending', 'Pending Payments', '₹1,24,500', 'clock', 'amber'),
             ('kpi-fat', 'Avg Fat', '4.2%', 'droplets', 'purple'),
             ('kpi-profit', 'Profit (30d)', '₹1,18,900', 'trending-up', 'cyan'),
         ],
         actions=[('Refresh', 'refresh-cw', 'primary'), ('New Collection', 'plus', 'secondary')]),

    dict(route='/admin/analytics', file='admin/dashboard/analytics.html', layout='admin',
         title='Analytics', subtitle='Deep-dive analytics across all branches and products.',
         icon='chart-line', section='dashboard', page='analytics', type='dashboard',
         kpis=[
             ('anl-collection', 'Total Collection (30d)', '86,430 L', 'milk', 'green'),
             ('anl-revenue', 'Gross Revenue', '₹48.2L', 'indian-rupee', 'gold'),
             ('anl-avg-fat', 'Average Fat', '4.18%', 'droplets', 'purple'),
             ('anl-growth', 'YoY Growth', '+12.5%', 'trending-up', 'cyan'),
         ],
         actions=[('Export', 'download', 'secondary'), ('Refresh', 'refresh-cw', 'primary')]),

    dict(route='/admin/company-statistics', file='admin/dashboard/company_statistics.html', layout='admin',
         title='Company Statistics', subtitle='Overall company-wide performance indicators.',
         icon='building-2', section='dashboard', page='company_statistics', type='dashboard',
         kpis=[
             ('st-branches', 'Branches', '12', 'building-2', 'blue'),
             ('st-farmers', 'Registered Farmers', '8,432', 'users', 'green'),
             ('st-employees', 'Employees', '96', 'briefcase', 'purple'),
             ('st-collection', 'Annual Collection', '1.24 Cr L', 'milk', 'gold'),
             ('st-revenue', 'Annual Revenue', '₹6.8 Cr', 'indian-rupee', 'cyan'),
             ('st-vehicles', 'Fleet Size', '24', 'car', 'teal'),
         ],
         actions=[('Refresh', 'refresh-cw', 'primary')]),

    dict(route='/admin/branch-comparison', file='admin/dashboard/branch_comparison.html', layout='admin',
         title='Branch Comparison', subtitle='Compare performance across branches side-by-side.',
         icon='git-compare', section='dashboard', page='branch_comparison', type='report',
         cols=['Branch', 'Farmers', 'Collection', 'Revenue', 'Avg Fat', 'Efficiency'],
         actions=[('Export', 'download', 'secondary'), ('Compare', 'git-compare', 'primary')]),

    dict(route='/admin/revenue-dashboard', file='admin/dashboard/revenue_dashboard.html', layout='admin',
         title='Revenue Dashboard', subtitle='Revenue streams, trends and forecasts.',
         icon='indian-rupee', section='dashboard', page='revenue_dashboard', type='dashboard',
         kpis=[
             ('rev-total', 'Total Revenue', '₹48.2L', 'indian-rupee', 'gold'),
             ('rev-milk', 'Milk Sales', '₹38.6L', 'milk', 'green'),
             ('rev-products', 'Product Sales', '₹7.1L', 'package', 'blue'),
             ('rev-other', 'Other Income', '₹2.5L', 'coins', 'purple'),
         ],
         actions=[('Export', 'download', 'secondary'), ('Refresh', 'refresh-cw', 'primary')]),

    dict(route='/admin/profit-loss-dashboard', file='admin/dashboard/profit_loss_dashboard.html', layout='admin',
         title='Profit & Loss Dashboard', subtitle='Profitability analysis for the current period.',
         icon='trending-up', section='dashboard', page='profit_loss_dashboard', type='report',
         cols=['Month', 'Revenue', 'Expenses', 'Profit', 'Margin'],
         actions=[('Export', 'download', 'secondary')]),

    dict(route='/admin/notifications', file='admin/dashboard/notifications.html', layout='admin',
         title='Notifications', subtitle='System-wide alerts and announcements.',
         icon='bell', section='dashboard', page='notifications', type='simple',
         actions=[('Mark All Read', 'check-check', 'secondary')]),

    # ── Branch Management ────────────────────────────────────────
    dict(route='/admin/branches', file='admin/branch_management/branch_list.html', layout='admin',
         title='Branch List', subtitle='Manage all registered branches.',
         icon='building-2', section='branches', page='branch_list', type='list',
         cols=['Code', 'Branch Name', 'City', 'Manager', 'Farmers', 'Collection', 'Status'],
         actions=[('Add Branch', 'plus', 'primary')]),

    dict(route='/admin/branches/create', file='admin/branch_management/create_branch.html', layout='admin',
         title='Create Branch', subtitle='Register a new branch.',
         icon='plus-circle', section='branches', page='branch_list', type='form',
         sections=[
             ('Branch Details', [
                 ('Branch Code', 'code', 'text', True, 'e.g. BR06'),
                 ('Branch Name', 'name', 'text', True, 'Enter branch name'),
                 ('Branch Type', 'branch_type', 'select', True, 'Main / Sub'),
                 ('Phone Number', 'phone', 'tel', True, '10-digit mobile'),
                 ('Email', 'email', 'email', False, 'branch@dairy.com'),
                 ('Registration Date', 'reg_date', 'date', False, ''),
             ]),
             ('Address', [
                 ('Address', 'address', 'textarea', False, 'Full address'),
                 ('City', 'city', 'text', True, 'City'),
                 ('District', 'district', 'text', False, 'District'),
                 ('State', 'state', 'text', False, 'State'),
                 ('Pincode', 'pincode', 'text', False, 'Pincode'),
             ]),
             ('Operating Details', [
                 ('Opening Time', 'open_time', 'time', False, ''),
                 ('Closing Time', 'close_time', 'time', False, ''),
                 ('Collection Capacity (L)', 'capacity', 'number', False, '0'),
                 ('Status', 'status', 'select', True, 'Active / Inactive'),
             ]),
         ]),

    dict(route='/admin/branches/edit', file='admin/branch_management/edit_branch.html', layout='admin',
         title='Edit Branch', subtitle='Update branch information.',
         icon='edit-3', section='branches', page='branch_list', type='form',
         sections=[
             ('Branch Details', [
                 ('Branch Code', 'code', 'text', True, 'e.g. BR06'),
                 ('Branch Name', 'name', 'text', True, 'Enter branch name'),
                 ('Phone Number', 'phone', 'tel', True, '10-digit mobile'),
                 ('Email', 'email', 'email', False, 'branch@dairy.com'),
             ]),
             ('Address', [
                 ('Address', 'address', 'textarea', False, 'Full address'),
                 ('City', 'city', 'text', True, 'City'),
                 ('District', 'district', 'text', False, 'District'),
                 ('State', 'state', 'text', False, 'State'),
                 ('Pincode', 'pincode', 'text', False, 'Pincode'),
             ]),
             ('Operating Details', [
                 ('Opening Time', 'open_time', 'time', False, ''),
                 ('Closing Time', 'close_time', 'time', False, ''),
                 ('Status', 'status', 'select', True, 'Active / Inactive'),
             ]),
         ]),

    dict(route='/admin/branches/details', file='admin/branch_management/branch_details.html', layout='admin',
         title='Branch Details', subtitle='Complete profile of the selected branch.',
         icon='info', section='branches', page='branch_list', type='profile',
         tabs=['Overview', 'Farmers', 'Collections', 'Activity']),

    dict(route='/admin/branches/assign-manager', file='admin/branch_management/assign_branch_manager.html', layout='admin',
         title='Assign Branch Manager', subtitle='Assign or change the manager for a branch.',
         icon='user-cog', section='branches', page='branch_list', type='form',
         sections=[
             ('Manager Assignment', [
                 ('Branch', 'branch', 'select', True, 'Select Branch'),
                 ('Current Manager', 'current_manager', 'text', False, 'Read-only'),
                 ('New Manager', 'manager', 'select', True, 'Select Employee'),
                 ('Manager Phone', 'manager_phone', 'tel', False, '10-digit mobile'),
                 ('Assignment Date', 'assign_date', 'date', False, ''),
                 ('Remarks', 'remarks', 'textarea', False, 'Optional remarks'),
             ]),
         ]),

    dict(route='/admin/branches/reset-password', file='admin/branch_management/reset_branch_password.html', layout='admin',
         title='Reset Branch Password', subtitle='Reset the login password of a branch manager.',
         icon='key', section='branches', page='branch_list', type='form',
         sections=[
             ('Password Reset', [
                 ('Branch Manager', 'manager', 'select', True, 'Select Manager'),
                 ('Branch', 'branch', 'select', False, 'Select Branch'),
                 ('New Password', 'password', 'password', True, 'Minimum 6 characters'),
                 ('Confirm Password', 'confirm', 'password', True, 'Repeat password'),
                 ('Send SMS Notification', 'notify', 'checkbox', False, ''),
             ]),
         ]),

    dict(route='/admin/branches/activity', file='admin/branch_management/branch_activity.html', layout='admin',
         title='Branch Activity', subtitle='Recent activity across all branches.',
         icon='activity', section='branches', page='branch_list', type='audit',
         cols=['Time', 'Branch', 'User', 'Action', 'Detail']),

    # ── Farmer Management ────────────────────────────────────────
    dict(route='/admin/farmers', file='admin/farmer_management/farmer_list.html', layout='admin',
         title='Farmer List', subtitle='Manage all registered farmers across branches.',
         icon='users', section='farmers', page='farmer_list', type='list',
         cols=['Code', 'Farmer Name', 'Mobile', 'Village', 'Type', 'Quantity', 'Status'],
         actions=[('Register Farmer', 'user-plus', 'primary')]),

    dict(route='/admin/farmers/profile', file='admin/farmer_management/farmer_profile.html', layout='admin',
         title='Farmer Profile', subtitle='Complete profile and history of the farmer.',
         icon='user', section='farmers', page='farmer_list', type='profile',
         tabs=['Overview', 'Milk History', 'Payments', 'Documents', 'Activity']),

    dict(route='/admin/farmers/verification', file='admin/farmer_management/farmer_verification.html', layout='admin',
         title='Farmer Verification', subtitle='Approve or reject farmer registrations.',
         icon='badge-check', section='farmers', page='farmer_list', type='list',
         cols=['Code', 'Farmer Name', 'Mobile', 'Aadhaar', 'Submitted', 'Status'],
         actions=[('Verify All', 'check-check', 'secondary')]),

    dict(route='/admin/bank-verification', file='admin/farmer_management/bank_verification.html', layout='admin',
         title='Bank Verification', subtitle='Verify farmer bank account details before payments.',
         icon='landmark', section='farmers', page='farmer_list', type='list',
         cols=['Farmer', 'Account Holder', 'Bank', 'IFSC', 'Account No', 'Status']),

    dict(route='/admin/farmers/documents', file='admin/farmer_management/farmer_documents.html', layout='admin',
         title='Farmer Documents', subtitle='Review documents submitted by farmers.',
         icon='file-text', section='farmers', page='farmer_list', type='list',
         cols=['Farmer', 'Document', 'Type', 'Submitted', 'Size', 'Status']),

    dict(route='/admin/farmers/payment-history', file='admin/farmer_management/payment_history.html', layout='admin',
         title='Farmer Payment History', subtitle='Payment records for all farmers.',
         icon='wallet', section='farmers', page='farmer_list', type='list',
         cols=['Pay Code', 'Farmer', 'Period', 'Amount', 'Method', 'Status']),

    dict(route='/admin/farmers/milk-history', file='admin/farmer_management/milk_history.html', layout='admin',
         title='Farmer Milk History', subtitle='Milk collection records for all farmers.',
         icon='milk', section='farmers', page='farmer_list', type='list',
         cols=['Receipt', 'Farmer', 'Date', 'Qty', 'Fat', 'SNF', 'Rate', 'Amount']),

    dict(route='/admin/farmers/block', file='admin/farmer_management/block_farmer.html', layout='admin',
         title='Block Farmer', subtitle='Temporarily block a farmer from collections and payments.',
         icon='ban', section='farmers', page='farmer_list', type='form',
         sections=[
             ('Block Farmer', [
                 ('Farmer', 'farmer', 'select', True, 'Select Farmer'),
                 ('Reason', 'reason', 'select', True, 'Adulteration / Non-compliance / Other'),
                 ('Duration', 'duration', 'select', True, '7 days / 30 days / Permanent'),
                 ('Details', 'details', 'textarea', False, 'Describe the reason'),
                 ('Notify Farmer', 'notify', 'checkbox', False, ''),
             ]),
         ]),

    dict(route='/admin/farmers/activity', file='admin/farmer_management/farmer_activity.html', layout='admin',
         title='Farmer Activity', subtitle='Audit trail of farmer-related actions.',
         icon='activity', section='farmers', page='farmer_list', type='audit',
         cols=['Time', 'Farmer', 'User', 'Action', 'Detail']),

    # ── Payments ─────────────────────────────────────────────────
    dict(route='/admin/payments/dashboard', file='admin/payments/payment_dashboard.html', layout='admin',
         title='Payment Dashboard', subtitle='Overview of the farmer payment pipeline.',
         icon='wallet', section='payments', page='payment_dashboard', type='dashboard',
         kpis=[
             ('pay-pending', 'Pending Amount', '₹1,24,500', 'clock', 'amber'),
             ('pay-approved', 'Approved', '₹2,18,000', 'check-circle', 'blue'),
             ('pay-paid', 'Paid (This Month)', '₹18.6L', 'check-check', 'green'),
             ('pay-failed', 'Failed', '₹12,400', 'x-circle', 'red'),
         ],
         actions=[('New Payment Sheet', 'plus', 'primary')]),

    dict(route='/admin/payments/sheet', file='admin/payments/payment_sheet.html', layout='admin',
         title='Payment Sheet', subtitle='Generate a payment sheet for a collection period.',
         icon='table', section='payments', page='payment_dashboard', type='list',
         cols=['Select', 'Farmer', 'Days', 'Quantity', 'Amount', 'Deductions', 'Net Payable'],
         actions=[('Generate Sheet', 'file-plus', 'primary')]),

    dict(route='/admin/payments/pending', file='admin/payments/pending_payments.html', layout='admin',
         title='Pending Payments', subtitle='Payments awaiting approval.',
         icon='clock', section='payments', page='payment_dashboard', type='list',
         cols=['Pay Code', 'Farmer', 'Period', 'Amount', 'Created', 'Status'],
         actions=[('Approve Selected', 'check-check', 'primary')]),

    dict(route='/admin/payments/approved', file='admin/payments/approved_payments.html', layout='admin',
         title='Approved Payments', subtitle='Approved payments ready for disbursal.',
         icon='check-circle', section='payments', page='payment_dashboard', type='list',
         cols=['Pay Code', 'Farmer', 'Period', 'Amount', 'Approved By', 'Status'],
         actions=[('Process Payment', 'banknote', 'primary')]),

    dict(route='/admin/payments/paid', file='admin/payments/paid_payments.html', layout='admin',
         title='Paid Payments', subtitle='Payments successfully disbursed.',
         icon='check-check', section='payments', page='payment_dashboard', type='list',
         cols=['Pay Code', 'Farmer', 'Period', 'Amount', 'Method', 'Paid On'],
         actions=[('Export', 'download', 'secondary')]),

    dict(route='/admin/payments/failed', file='admin/payments/failed_payments.html', layout='admin',
         title='Failed Payments', subtitle='Payments that failed during disbursal.',
         icon='x-circle', section='payments', page='payment_dashboard', type='list',
         cols=['Pay Code', 'Farmer', 'Amount', 'Method', 'Error', 'Retry'],
         actions=[('Retry All', 'refresh-cw', 'secondary')]),

    dict(route='/admin/payments/history', file='admin/payments/payment_history.html', layout='admin',
         title='Payment History', subtitle='Complete history of all farmer payments.',
         icon='history', section='payments', page='payment_dashboard', type='list',
         cols=['Pay Code', 'Farmer', 'Period', 'Amount', 'Status', 'Date']),

    dict(route='/admin/payments/bank-transfer', file='admin/payments/bank_transfer.html', layout='admin',
         title='Bank Transfer', subtitle='Manual bank transfer details for payments.',
         icon='landmark', section='payments', page='payment_dashboard', type='form',
         sections=[
             ('Transfer Details', [
                 ('Payment Batch', 'batch', 'select', True, 'Select Payment Batch'),
                 ('Bank Account', 'account', 'select', True, 'Company Bank Account'),
                 ('Beneficiary Count', 'count', 'number', False, ''),
                 ('Total Amount', 'amount', 'number', True, '₹'),
                 ('Reference / UTR', 'utr', 'text', False, 'Bank reference number'),
                 ('Transfer Date', 'transfer_date', 'date', False, ''),
                 ('Remarks', 'remarks', 'textarea', False, 'Optional remarks'),
             ]),
         ]),

    dict(route='/admin/payments/reports', file='admin/payments/payment_reports.html', layout='admin',
         title='Payment Reports', subtitle='Reports on payments, deductions and disbursals.',
         icon='file-bar-chart', section='payments', page='payment_dashboard', type='report',
         cols=['Month', 'Payments', 'Amount', 'Deductions', 'Disbursed', 'Failed']),

    # ── Procurement ──────────────────────────────────────────────
    dict(route='/admin/procurement/dashboard', file='admin/procurement/procurement_dashboard.html', layout='admin',
         title='Procurement Dashboard', subtitle='Suppliers, purchase orders and deliveries.',
         icon='truck', section='procurement', page='procurement_dashboard', type='dashboard',
         kpis=[
             ('pro-suppliers', 'Suppliers', '34', 'factory', 'blue'),
             ('pro-orders', 'Open Orders', '18', 'file-text', 'gold'),
             ('pro-value', 'Order Value', '₹6.4L', 'indian-rupee', 'green'),
             ('pro-deliveries', 'Pending Deliveries', '7', 'truck', 'purple'),
         ],
         actions=[('Create PO', 'file-plus', 'primary')]),

    dict(route='/admin/suppliers', file='admin/procurement/supplier_list.html', layout='admin',
         title='Supplier List', subtitle='Manage procurement suppliers.',
         icon='factory', section='procurement', page='procurement_dashboard', type='list',
         cols=['Code', 'Supplier', 'Category', 'Contact', 'City', 'Status'],
         actions=[('Add Supplier', 'plus', 'primary')]),

    dict(route='/admin/suppliers/profile', file='admin/procurement/supplier_profile.html', layout='admin',
         title='Supplier Profile', subtitle='Complete supplier details and history.',
         icon='factory', section='procurement', page='procurement_dashboard', type='profile',
         tabs=['Overview', 'Purchase Orders', 'Deliveries', 'Payments']),

    dict(route='/admin/suppliers/create', file='admin/procurement/create_supplier.html', layout='admin',
         title='Create Supplier', subtitle='Register a new supplier.',
         icon='plus-circle', section='procurement', page='procurement_dashboard', type='form',
         sections=[
             ('Supplier Details', [
                 ('Supplier Name', 'name', 'text', True, 'Company / individual name'),
                 ('Category', 'category', 'select', True, 'Feed / Equipment / Services / Other'),
                 ('GSTIN', 'gstin', 'text', False, 'GST number'),
                 ('Contact Person', 'contact', 'text', False, ''),
                 ('Phone', 'phone', 'tel', True, '10-digit mobile'),
                 ('Email', 'email', 'email', False, ''),
                 ('City', 'city', 'text', False, ''),
                 ('Address', 'address', 'textarea', False, ''),
             ]),
             ('Bank Details', [
                 ('Account Holder', 'account_holder', 'text', False, ''),
                 ('Bank Name', 'bank_name', 'text', False, ''),
                 ('Account Number', 'account_number', 'text', False, ''),
                 ('IFSC', 'ifsc', 'text', False, ''),
                 ('UPI', 'upi', 'text', False, ''),
             ]),
         ]),

    dict(route='/admin/purchase-orders', file='admin/procurement/purchase_orders.html', layout='admin',
         title='Purchase Orders', subtitle='All purchase orders and their status.',
         icon='file-text', section='procurement', page='procurement_dashboard', type='list',
         cols=['PO No', 'Supplier', 'Items', 'Amount', 'Ordered', 'Delivery Status'],
         actions=[('Create PO', 'file-plus', 'primary')]),

    dict(route='/admin/purchase-orders/create', file='admin/procurement/create_purchase_order.html', layout='admin',
         title='Create Purchase Order', subtitle='Create a new purchase order.',
         icon='file-plus', section='procurement', page='procurement_dashboard', type='form',
         sections=[
             ('Order Details', [
                 ('Supplier', 'supplier', 'select', True, 'Select Supplier'),
                 ('Branch', 'branch', 'select', False, 'Select Branch'),
                 ('Order Date', 'order_date', 'date', False, ''),
                 ('Expected Delivery', 'expected_date', 'date', False, ''),
                 ('Priority', 'priority', 'select', False, 'Normal / High / Urgent'),
                 ('Payment Terms', 'terms', 'select', False, 'Advance / Credit 15d / Credit 30d'),
                 ('Remarks', 'remarks', 'textarea', False, ''),
             ]),
             ('Items', []),
         ]),

    dict(route='/admin/grn', file='admin/procurement/goods_receipt_note.html', layout='admin',
         title='Goods Receipt Notes', subtitle='Record and verify received goods.',
         icon='clipboard-check', section='procurement', page='procurement_dashboard', type='list',
         cols=['GRN No', 'PO No', 'Supplier', 'Items', 'Received On', 'Verified']),

    dict(route='/admin/delivery-tracking', file='admin/procurement/delivery_tracking.html', layout='admin',
         title='Delivery Tracking', subtitle='Track incoming deliveries in real time.',
         icon='map-pin', section='procurement', page='procurement_dashboard', type='list',
         cols=['PO No', 'Supplier', 'Vehicle', 'Route', 'ETA', 'Status']),

    dict(route='/admin/vendor-payments', file='admin/procurement/vendor_payments.html', layout='admin',
         title='Vendor Payments', subtitle='Payments made to suppliers.',
         icon='banknote', section='procurement', page='procurement_dashboard', type='list',
         cols=['Payment No', 'Supplier', 'PO Ref', 'Amount', 'Method', 'Status']),

    dict(route='/admin/procurement/reports', file='admin/procurement/procurement_reports.html', layout='admin',
         title='Procurement Reports', subtitle='Procurement spend and performance reports.',
         icon='file-bar-chart', section='procurement', page='procurement_dashboard', type='report',
         cols=['Month', 'Orders', 'Value', 'Deliveries', 'Vendor Payments']),

    # ── Inventory ────────────────────────────────────────────────
    dict(route='/admin/inventory/dashboard', file='admin/inventory/inventory_dashboard.html', layout='admin',
         title='Inventory Dashboard', subtitle='Stock levels, movements and alerts.',
         icon='package', section='inventory', page='inventory_dashboard', type='dashboard',
         kpis=[
             ('inv-items', 'Items', '142', 'boxes', 'blue'),
             ('inv-stock', 'Stock Value', '₹8.2L', 'indian-rupee', 'green'),
             ('inv-low', 'Low Stock Items', '12', 'alert-triangle', 'amber'),
             ('inv-movements', 'Movements Today', '38', 'shuffle', 'purple'),
         ],
         actions=[('Add Item', 'plus', 'primary'), ('Stock In', 'arrow-down-circle', 'secondary')]),

    dict(route='/admin/warehouse', file='admin/inventory/warehouse.html', layout='admin',
         title='Warehouse', subtitle='Manage warehouses and storage locations.',
         icon='warehouse', section='inventory', page='inventory_dashboard', type='list',
         cols=['Code', 'Warehouse', 'Location', 'Capacity', 'Utilization', 'Status'],
         actions=[('Add Warehouse', 'plus', 'primary')]),

    dict(route='/admin/items', file='admin/inventory/item_list.html', layout='admin',
         title='Item List', subtitle='All inventory items and stock levels.',
         icon='boxes', section='inventory', page='inventory_dashboard', type='list',
         cols=['Code', 'Item', 'Category', 'Unit', 'Stock', 'Rate', 'Status'],
         actions=[('Add Item', 'plus', 'primary')]),

    dict(route='/admin/items/create', file='admin/inventory/create_item.html', layout='admin',
         title='Create Item', subtitle='Add a new inventory item.',
         icon='plus-circle', section='inventory', page='inventory_dashboard', type='form',
         sections=[
             ('Item Details', [
                 ('Item Code', 'code', 'text', True, 'e.g. ITM-143'),
                 ('Item Name', 'name', 'text', True, 'Enter item name'),
                 ('Category', 'category', 'select', True, 'Feed / Packaging / Equipment / Stationery'),
                 ('Unit', 'unit', 'select', True, 'kg / L / pcs / box'),
                 ('Opening Stock', 'opening_stock', 'number', False, '0'),
                 ('Unit Rate', 'rate', 'number', False, '₹'),
                 ('Min Stock Level', 'min_stock', 'number', False, '0'),
                 ('Max Stock Level', 'max_stock', 'number', False, '0'),
                 ('Description', 'description', 'textarea', False, ''),
             ]),
         ]),

    dict(route='/admin/items/edit', file='admin/inventory/edit_item.html', layout='admin',
         title='Edit Item', subtitle='Update inventory item information.',
         icon='edit-3', section='inventory', page='inventory_dashboard', type='form',
         sections=[
             ('Item Details', [
                 ('Item Code', 'code', 'text', True, 'e.g. ITM-143'),
                 ('Item Name', 'name', 'text', True, 'Enter item name'),
                 ('Category', 'category', 'select', True, 'Feed / Packaging / Equipment / Stationery'),
                 ('Unit', 'unit', 'select', True, 'kg / L / pcs / box'),
                 ('Unit Rate', 'rate', 'number', False, '₹'),
                 ('Min Stock Level', 'min_stock', 'number', False, '0'),
                 ('Max Stock Level', 'max_stock', 'number', False, '0'),
             ]),
         ]),

    dict(route='/admin/stock/in', file='admin/inventory/stock_in.html', layout='admin',
         title='Stock In', subtitle='Record incoming stock (purchases, returns).',
         icon='arrow-down-circle', section='inventory', page='inventory_dashboard', type='form',
         sections=[
             ('Stock In', [
                 ('Item', 'item', 'select', True, 'Select Item'),
                 ('Warehouse', 'warehouse', 'select', True, 'Select Warehouse'),
                 ('Quantity', 'quantity', 'number', True, '0'),
                 ('Unit Rate', 'rate', 'number', False, '₹'),
                 ('Reference', 'reference', 'text', False, 'PO / GRN / Invoice no.'),
                 ('Date', 'date', 'date', False, ''),
                 ('Remarks', 'remarks', 'textarea', False, ''),
             ]),
         ]),

    dict(route='/admin/stock/out', file='admin/inventory/stock_out.html', layout='admin',
         title='Stock Out', subtitle='Record outgoing stock (issues, consumption).',
         icon='arrow-up-circle', section='inventory', page='inventory_dashboard', type='form',
         sections=[
             ('Stock Out', [
                 ('Item', 'item', 'select', True, 'Select Item'),
                 ('Warehouse', 'warehouse', 'select', True, 'Select Warehouse'),
                 ('Purpose', 'purpose', 'select', True, 'Branch issue / Consumption / Damage / Other'),
                 ('Quantity', 'quantity', 'number', True, '0'),
                 ('Reference', 'reference', 'text', False, 'Request no. / Batch'),
                 ('Date', 'date', 'date', False, ''),
                 ('Remarks', 'remarks', 'textarea', False, ''),
             ]),
         ]),

    dict(route='/admin/stock/transfer', file='admin/inventory/stock_transfer.html', layout='admin',
         title='Stock Transfer', subtitle='Transfer stock between warehouses and branches.',
         icon='shuffle', section='inventory', page='inventory_dashboard', type='form',
         sections=[
             ('Stock Transfer', [
                 ('Item', 'item', 'select', True, 'Select Item'),
                 ('From', 'from_location', 'select', True, 'From Warehouse / Branch'),
                 ('To', 'to_location', 'select', True, 'To Warehouse / Branch'),
                 ('Quantity', 'quantity', 'number', True, '0'),
                 ('Transfer Date', 'date', 'date', False, ''),
                 ('Remarks', 'remarks', 'textarea', False, ''),
             ]),
         ]),

    dict(route='/admin/stock/allocation', file='admin/inventory/branch_allocation.html', layout='admin',
         title='Branch Allocation', subtitle='Allocate stock to branches.',
         icon='building', section='inventory', page='inventory_dashboard', type='list',
         cols=['Item', 'Branch', 'Allocated', 'Received', 'Pending', 'Date'],
         actions=[('New Allocation', 'plus', 'primary')]),

    dict(route='/admin/inventory/history', file='admin/inventory/inventory_history.html', layout='admin',
         title='Inventory History', subtitle='Complete stock movement history.',
         icon='history', section='inventory', page='inventory_dashboard', type='audit',
         cols=['Date', 'Item', 'Type', 'Qty', 'Reference', 'User']),

    dict(route='/admin/low-stock', file='admin/inventory/low_stock.html', layout='admin',
         title='Low Stock', subtitle='Items below their minimum stock level.',
         icon='alert-triangle', section='inventory', page='inventory_dashboard', type='list',
         cols=['Item', 'Category', 'Stock', 'Min Level', 'Rate', 'Reorder'],
         actions=[('Reorder All', 'refresh-cw', 'secondary')]),

    # ── Vehicles ─────────────────────────────────────────────────
    dict(route='/admin/vehicles/dashboard', file='admin/vehicles/vehicle_dashboard.html', layout='admin',
         title='Vehicle Dashboard', subtitle='Fleet overview, fuel, and maintenance.',
         icon='car', section='vehicles', page='vehicle_dashboard', type='dashboard',
         kpis=[
             ('veh-total', 'Vehicles', '24', 'car', 'blue'),
             ('veh-active', 'Active', '21', 'check-circle', 'green'),
             ('veh-fuel', 'Fuel Cost (Month)', '₹1.8L', 'fuel', 'gold'),
             ('veh-service', 'Due for Service', '4', 'wrench', 'amber'),
         ],
         actions=[('Add Vehicle', 'plus', 'primary')]),

    dict(route='/admin/vehicles', file='admin/vehicles/vehicle_list.html', layout='admin',
         title='Vehicle List', subtitle='All vehicles in the fleet.',
         icon='car-front', section='vehicles', page='vehicle_dashboard', type='list',
         cols=['Reg No', 'Vehicle', 'Type', 'Route', 'Driver', 'Status'],
         actions=[('Add Vehicle', 'plus', 'primary')]),

    dict(route='/admin/vehicles/add', file='admin/vehicles/add_vehicle.html', layout='admin',
         title='Add Vehicle', subtitle='Register a new vehicle in the fleet.',
         icon='plus-circle', section='vehicles', page='vehicle_dashboard', type='form',
         sections=[
             ('Vehicle Details', [
                 ('Registration No', 'reg_no', 'text', True, 'e.g. MP09-AB-1234'),
                 ('Vehicle Name', 'name', 'text', True, 'e.g. Milk Tanker 01'),
                 ('Type', 'vehicle_type', 'select', True, 'Tanker / Truck / Van / Car'),
                 ('Capacity (L)', 'capacity', 'number', False, '0'),
                 ('Chassis No', 'chassis', 'text', False, ''),
                 ('Engine No', 'engine', 'text', False, ''),
                 ('Purchase Date', 'purchase_date', 'date', False, ''),
                 ('Fuel Type', 'fuel_type', 'select', False, 'Diesel / Petrol / CNG / Electric'),
             ]),
             ('Insurance & Fitness', [
                 ('Insurance No', 'insurance_no', 'text', False, ''),
                 ('Insurance Expiry', 'insurance_expiry', 'date', False, ''),
                 ('Fitness Expiry', 'fitness_expiry', 'date', False, ''),
                 ('Permit Expiry', 'permit_expiry', 'date', False, ''),
                 ('GPS Status', 'gps_status', 'select', False, 'Active / Inactive'),
             ]),
         ]),

    dict(route='/admin/vehicles/profile', file='admin/vehicles/vehicle_profile.html', layout='admin',
         title='Vehicle Profile', subtitle='Complete details and history of a vehicle.',
         icon='car', section='vehicles', page='vehicle_dashboard', type='profile',
         tabs=['Overview', 'Fuel Log', 'Maintenance', 'Service History']),

    dict(route='/admin/vehicles/assign', file='admin/vehicles/assign_vehicle.html', layout='admin',
         title='Assign Vehicle', subtitle='Assign a vehicle to a driver and route.',
         icon='user-cog', section='vehicles', page='vehicle_dashboard', type='form',
         sections=[
             ('Assignment', [
                 ('Vehicle', 'vehicle', 'select', True, 'Select Vehicle'),
                 ('Driver', 'driver', 'select', True, 'Select Employee'),
                 ('Route', 'route', 'select', True, 'Select Route'),
                 ('Shift', 'shift', 'select', False, 'Morning / Evening'),
                 ('Assignment Date', 'assign_date', 'date', False, ''),
                 ('Remarks', 'remarks', 'textarea', False, ''),
             ]),
         ]),

    dict(route='/admin/vehicles/maintenance', file='admin/vehicles/maintenance.html', layout='admin',
         title='Maintenance', subtitle='Vehicle maintenance records and schedules.',
         icon='wrench', section='vehicles', page='vehicle_dashboard', type='list',
         cols=['Vehicle', 'Service Type', 'Date', 'Cost', 'Mileage', 'Status'],
         actions=[('Schedule Service', 'plus', 'primary')]),

    dict(route='/admin/vehicles/insurance', file='admin/vehicles/insurance.html', layout='admin',
         title='Insurance', subtitle='Vehicle insurance policies and renewals.',
         icon='shield-check', section='vehicles', page='vehicle_dashboard', type='list',
         cols=['Vehicle', 'Policy No', 'Insurer', 'Expiry', 'Premium', 'Status'],
         actions=[('Add Policy', 'plus', 'primary')]),

    dict(route='/admin/vehicles/fuel', file='admin/vehicles/fuel_log.html', layout='admin',
         title='Fuel Log', subtitle='Fuel consumption and cost tracking.',
         icon='fuel', section='vehicles', page='vehicle_dashboard', type='list',
         cols=['Vehicle', 'Date', 'Qty (L)', 'Rate', 'Cost', 'Mileage', 'Filled By'],
         actions=[('Add Entry', 'plus', 'primary')]),

    dict(route='/admin/vehicles/service-history', file='admin/vehicles/service_history.html', layout='admin',
         title='Service History', subtitle='Complete service history of the fleet.',
         icon='history', section='vehicles', page='vehicle_dashboard', type='audit',
         cols=['Date', 'Vehicle', 'Service', 'Mechanic', 'Cost', 'Next Due']),

    # ── Employees ────────────────────────────────────────────────
    dict(route='/admin/employees/dashboard', file='admin/employees/employee_dashboard.html', layout='admin',
         title='Employee Dashboard', subtitle='Workforce overview, attendance and payroll.',
         icon='briefcase', section='employees', page='employee_dashboard', type='dashboard',
         kpis=[
             ('emp-total', 'Employees', '96', 'users', 'blue'),
             ('emp-present', 'Present Today', '84', 'check-circle', 'green'),
             ('emp-absent', 'Absent Today', '12', 'x-circle', 'red'),
             ('emp-payroll', 'Monthly Payroll', '₹12.4L', 'banknote', 'gold'),
         ],
         actions=[('Add Employee', 'user-plus', 'primary')]),

    dict(route='/admin/employees', file='admin/employees/employee_list.html', layout='admin',
         title='Employee List', subtitle='All employees across the organization.',
         icon='users', section='employees', page='employee_dashboard', type='list',
         cols=['Emp Code', 'Name', 'Role', 'Branch', 'Phone', 'Status'],
         actions=[('Add Employee', 'user-plus', 'primary')]),

    dict(route='/admin/employees/add', file='admin/employees/add_employee.html', layout='admin',
         title='Add Employee', subtitle='Register a new employee.',
         icon='user-plus', section='employees', page='employee_dashboard', type='form',
         sections=[
             ('Personal Information', [
                 ('Employee Name', 'name', 'text', True, 'Full name'),
                 ('Father\'s Name', 'father_name', 'text', False, ''),
                 ('Date of Birth', 'dob', 'date', False, ''),
                 ('Gender', 'gender', 'select', False, 'Male / Female / Other'),
                 ('Mobile', 'mobile', 'tel', True, '10-digit mobile'),
                 ('Email', 'email', 'email', False, ''),
                 ('Aadhaar', 'aadhaar', 'text', False, '12-digit'),
                 ('Address', 'address', 'textarea', False, ''),
             ]),
             ('Employment', [
                 ('Employee Code', 'emp_code', 'text', True, 'e.g. EMP-097'),
                 ('Role', 'role', 'select', True, 'Manager / Operator / Driver / Staff'),
                 ('Branch', 'branch', 'select', True, 'Select Branch'),
                 ('Department', 'department', 'select', False, 'Operations / Quality / Admin / Finance'),
                 ('Joining Date', 'joining_date', 'date', False, ''),
                 ('Salary', 'salary', 'number', False, '₹ / month'),
                 ('Bank Account', 'account_number', 'text', False, ''),
                 ('IFSC', 'ifsc', 'text', False, ''),
             ]),
         ]),

    dict(route='/admin/employees/profile', file='admin/employees/employee_profile.html', layout='admin',
         title='Employee Profile', subtitle='Complete employee record and history.',
         icon='user', section='employees', page='employee_dashboard', type='profile',
         tabs=['Overview', 'Attendance', 'Salary', 'Leave', 'Documents']),

    dict(route='/admin/attendance', file='admin/employees/attendance.html', layout='admin',
         title='Attendance', subtitle='Daily attendance of all employees.',
         icon='calendar-check', section='employees', page='employee_dashboard', type='list',
         cols=['Employee', 'In Time', 'Out Time', 'Shift', 'Hours', 'Status'],
         actions=[('Mark Attendance', 'plus', 'primary')]),

    dict(route='/admin/salary', file='admin/employees/salary.html', layout='admin',
         title='Salary', subtitle='Salary processing and payroll management.',
         icon='banknote', section='employees', page='employee_dashboard', type='list',
         cols=['Employee', 'Basic', 'Allowances', 'Deductions', 'Net Pay', 'Status'],
         actions=[('Generate Payroll', 'file-plus', 'primary')]),

    dict(route='/admin/leave', file='admin/employees/leave_management.html', layout='admin',
         title='Leave Management', subtitle='Employee leave requests and balances.',
         icon='calendar-off', section='employees', page='employee_dashboard', type='list',
         cols=['Employee', 'Type', 'From', 'To', 'Days', 'Status'],
         actions=[('Approve Pending', 'check-check', 'secondary')]),

    dict(route='/admin/roles', file='admin/employees/role_management.html', layout='admin',
         title='Role Management', subtitle='Define roles and permissions for employees.',
         icon='shield', section='employees', page='employee_dashboard', type='settings',
         sections=[
             ('Roles', []),
             ('Permissions', []),
         ]),

    dict(route='/admin/employees/reset-password', file='admin/employees/reset_password.html', layout='admin',
         title='Reset Employee Password', subtitle='Reset the login password of an employee.',
         icon='key', section='employees', page='employee_dashboard', type='form',
         sections=[
             ('Password Reset', [
                 ('Employee', 'employee', 'select', True, 'Select Employee'),
                 ('New Password', 'password', 'password', True, 'Minimum 6 characters'),
                 ('Confirm Password', 'confirm', 'password', True, 'Repeat password'),
             ]),
         ]),

    # ── Reports ──────────────────────────────────────────────────
    dict(route='/admin/reports/dashboard', file='admin/reports/reports_dashboard.html', layout='admin',
         title='Reports Dashboard', subtitle='Generate and download business reports.',
         icon='bar-chart-3', section='reports', page='reports_dashboard', type='report',
         cols=['Report', 'Period', 'Generated', 'Format', 'Size', 'Actions']),

    dict(route='/admin/reports/milk-collection', file='admin/reports/milk_collection_report.html', layout='admin',
         title='Milk Collection Report', subtitle='Milk collection by branch, shift and period.',
         icon='milk', section='reports', page='reports_dashboard', type='report',
         cols=['Date', 'Branch', 'Shift', 'Qty', 'Avg Fat', 'Avg SNF', 'Amount']),

    dict(route='/admin/reports/farmers', file='admin/reports/farmer_report.html', layout='admin',
         title='Farmer Report', subtitle='Farmer registrations and activity report.',
         icon='users', section='reports', page='reports_dashboard', type='report',
         cols=['Farmer', 'Code', 'Branch', 'Registered', 'Total Qty', 'Total Amount']),

    dict(route='/admin/reports/payments', file='admin/reports/payment_report.html', layout='admin',
         title='Payment Report', subtitle='Payments made to farmers by period.',
         icon='wallet', section='reports', page='reports_dashboard', type='report',
         cols=['Period', 'Payments', 'Amount', 'Method', 'Status']),

    dict(route='/admin/reports/inventory', file='admin/reports/inventory_report.html', layout='admin',
         title='Inventory Report', subtitle='Stock levels and movements report.',
         icon='package', section='reports', page='reports_dashboard', type='report',
         cols=['Item', 'Opening', 'In', 'Out', 'Closing', 'Value']),

    dict(route='/admin/reports/procurement', file='admin/reports/procurement_report.html', layout='admin',
         title='Procurement Report', subtitle='Procurement activity and spend report.',
         icon='truck', section='reports', page='reports_dashboard', type='report',
         cols=['Month', 'Orders', 'Value', 'Suppliers', 'Deliveries']),

    dict(route='/admin/reports/employees', file='admin/reports/employee_report.html', layout='admin',
         title='Employee Report', subtitle='Workforce, attendance and payroll report.',
         icon='briefcase', section='reports', page='reports_dashboard', type='report',
         cols=['Department', 'Headcount', 'Present', 'Absent', 'Payroll']),

    dict(route='/admin/reports/vehicles', file='admin/reports/vehicle_report.html', layout='admin',
         title='Vehicle Report', subtitle='Fleet usage, fuel and maintenance report.',
         icon='car', section='reports', page='reports_dashboard', type='report',
         cols=['Vehicle', 'Trips', 'Distance', 'Fuel Cost', 'Service Cost']),

    dict(route='/admin/reports/quality', file='admin/reports/quality_report.html', layout='admin',
         title='Quality Report', subtitle='Milk quality parameters by period.',
         icon='flask-conical', section='reports', page='reports_dashboard', type='report',
         cols=['Date', 'Samples', 'Avg Fat', 'Avg SNF', 'Rejected', 'Rejection %']),

    dict(route='/admin/reports/branches', file='admin/reports/branch_report.html', layout='admin',
         title='Branch Report', subtitle='Branch-wise performance report.',
         icon='building-2', section='reports', page='reports_dashboard', type='report',
         cols=['Branch', 'Farmers', 'Collection', 'Revenue', 'Expenses', 'Profit']),

    dict(route='/admin/reports/profit-loss', file='admin/reports/profit_loss_report.html', layout='admin',
         title='Profit & Loss Report', subtitle='Statement of profit and loss.',
         icon='trending-down', section='reports', page='reports_dashboard', type='report',
         cols=['Item', 'Amount']),

    dict(route='/admin/reports/export', file='admin/reports/export_reports.html', layout='admin',
         title='Export Reports', subtitle='Export business data to Excel, PDF or CSV.',
         icon='download', section='reports', page='reports_dashboard', type='settings',
         sections=[
             ('Export Options', []),
         ]),

    # ── Audit ────────────────────────────────────────────────────
    dict(route='/admin/audit/dashboard', file='admin/audit/audit_dashboard.html', layout='admin',
         title='Audit Dashboard', subtitle='System activity and security monitoring.',
         icon='scroll-text', section='audit', page='audit_dashboard', type='dashboard',
         kpis=[
             ('aud-logins', 'Logins Today', '42', 'log-in', 'blue'),
             ('aud-actions', 'Actions Today', '1,208', 'activity', 'green'),
             ('aud-warnings', 'Security Alerts', '3', 'shield-alert', 'red'),
             ('aud-failures', 'Failed Logins', '8', 'x-circle', 'amber'),
         ],
         actions=[('Export Logs', 'download', 'secondary')]),

    dict(route='/admin/audit/login-logs', file='admin/audit/login_logs.html', layout='admin',
         title='Login Logs', subtitle='All login and logout events.',
         icon='log-in', section='audit', page='audit_dashboard', type='audit',
         cols=['Time', 'User', 'Role', 'Branch', 'IP Address', 'Status']),

    dict(route='/admin/audit/activity-logs', file='admin/audit/activity_logs.html', layout='admin',
         title='Activity Logs', subtitle='All user actions across the system.',
         icon='activity', section='audit', page='audit_dashboard', type='audit',
         cols=['Time', 'User', 'Module', 'Action', 'Detail']),

    dict(route='/admin/audit/payment-logs', file='admin/audit/payment_logs.html', layout='admin',
         title='Payment Logs', subtitle='Audit trail of payment actions.',
         icon='wallet', section='audit', page='audit_dashboard', type='audit',
         cols=['Time', 'User', 'Payment', 'Action', 'Amount', 'Detail']),

    dict(route='/admin/audit/inventory-logs', file='admin/audit/inventory_logs.html', layout='admin',
         title='Inventory Logs', subtitle='Audit trail of inventory movements.',
         icon='package', section='audit', page='audit_dashboard', type='audit',
         cols=['Time', 'User', 'Item', 'Type', 'Qty', 'Detail']),

    dict(route='/admin/audit/branch-logs', file='admin/audit/branch_logs.html', layout='admin',
         title='Branch Logs', subtitle='Actions performed within branches.',
         icon='building-2', section='audit', page='audit_dashboard', type='audit',
         cols=['Time', 'Branch', 'User', 'Action', 'Detail']),

    dict(route='/admin/audit/security-logs', file='admin/audit/security_logs.html', layout='admin',
         title='Security Logs', subtitle='Security events, lockouts and alerts.',
         icon='shield', section='audit', page='audit_dashboard', type='audit',
         cols=['Time', 'User', 'Event', 'Severity', 'IP Address', 'Detail']),

    # ── Settings ─────────────────────────────────────────────────
    dict(route='/admin/settings/company', file='admin/settings/company_profile.html', layout='admin',
         title='Company Profile', subtitle='Company information and branding.',
         icon='building', section='settings', page='settings', type='settings',
         sections=[
             ('Company Information', [
                 ('Company Name', 'company_name', 'text', True, 'Shree Milk Bank Dairy'),
                 ('Tagline', 'tagline', 'text', False, ''),
                 ('Reg Address', 'address', 'textarea', False, ''),
                 ('Phone', 'phone', 'tel', False, ''),
                 ('Email', 'email', 'email', False, ''),
                 ('Website', 'website', 'text', False, ''),
                 ('GSTIN', 'gstin', 'text', False, ''),
                 ('FSSAI License', 'fssai', 'text', False, ''),
                 ('Logo', 'logo', 'file', False, 'Upload logo'),
             ]),
         ]),

    dict(route='/admin/settings/milk-pricing', file='admin/settings/milk_pricing.html', layout='admin',
         title='Milk Pricing', subtitle='Configure fat & SNF based milk rates.',
         icon='dollar-sign', section='settings', page='settings', type='settings',
         sections=[
             ('Rate Configuration', [
                 ('Fat Rate', 'fat_rate', 'number', True, '₹ per fat %'),
                 ('SNF Rate', 'snf_rate', 'number', True, '₹ per SNF %'),
                 ('Rate Effective From', 'effective_from', 'date', False, ''),
                 ('Minimum Rate', 'min_rate', 'number', False, '₹ / L'),
                 ('Cow Milk Rate (Default)', 'cow_rate', 'number', False, '₹ / L'),
                 ('Buffalo Milk Rate (Default)', 'buffalo_rate', 'number', False, '₹ / L'),
             ]),
         ]),

    dict(route='/admin/settings/quality-parameters', file='admin/settings/quality_parameters.html', layout='admin',
         title='Quality Parameters', subtitle='Configure milk quality acceptance criteria.',
         icon='flask-conical', section='settings', page='settings', type='settings',
         sections=[
             ('Quality Parameters', [
                 ('Min Fat %', 'min_fat', 'number', True, '0.0'),
                 ('Max Fat %', 'max_fat', 'number', True, '0.0'),
                 ('Min SNF %', 'min_snf', 'number', True, '0.0'),
                 ('Max SNF %', 'max_snf', 'number', True, '0.0'),
                 ('Min CLR', 'min_clr', 'number', False, '0.0'),
                 ('Max Water %', 'max_water', 'number', False, '0.0'),
                 ('Max Temperature (°C)', 'max_temp', 'number', False, '0.0'),
             ]),
         ]),

    dict(route='/admin/settings/notifications', file='admin/settings/notification_settings.html', layout='admin',
         title='Notification Settings', subtitle='Configure system notifications.',
         icon='bell', section='settings', page='settings', type='settings',
         sections=[
             ('Notification Preferences', [
                 ('Payment Alerts', 'payment_alerts', 'toggle', False, ''),
                 ('Collection Alerts', 'collection_alerts', 'toggle', False, ''),
                 ('Quality Alerts', 'quality_alerts', 'toggle', False, ''),
                 ('Low Stock Alerts', 'stock_alerts', 'toggle', False, ''),
                 ('Farmer Registration', 'farmer_reg', 'toggle', False, ''),
                 ('Security Alerts', 'security_alerts', 'toggle', False, ''),
                 ('Alert Email', 'alert_email', 'email', False, ''),
             ]),
         ]),

    dict(route='/admin/settings/sms', file='admin/settings/sms_settings.html', layout='admin',
         title='SMS Settings', subtitle='Configure SMS gateway for notifications.',
         icon='message-square', section='settings', page='settings', type='settings',
         sections=[
             ('SMS Gateway', [
                 ('SMS Provider', 'sms_provider', 'select', True, 'MSG91 / Twilio / Other'),
                 ('API Key', 'sms_api_key', 'password', False, ''),
                 ('Sender ID', 'sms_sender', 'text', False, ''),
                 ('Default Template', 'sms_template', 'textarea', False, ''),
                 ('Enable SMS', 'sms_enabled', 'toggle', False, ''),
                 ('Test SMS Number', 'test_number', 'tel', False, ''),
             ]),
         ]),

    dict(route='/admin/settings/email', file='admin/settings/email_settings.html', layout='admin',
         title='Email Settings', subtitle='Configure SMTP for email notifications.',
         icon='mail', section='settings', page='settings', type='settings',
         sections=[
             ('SMTP Configuration', [
                 ('SMTP Host', 'smtp_host', 'text', True, 'smtp.example.com'),
                 ('SMTP Port', 'smtp_port', 'number', True, '587'),
                 ('Username', 'smtp_user', 'text', False, ''),
                 ('Password', 'smtp_password', 'password', False, ''),
                 ('From Email', 'from_email', 'email', False, ''),
                 ('Encryption', 'encryption', 'select', False, 'TLS / SSL / None'),
                 ('Enable Email', 'email_enabled', 'toggle', False, ''),
             ]),
         ]),

    dict(route='/admin/settings/backup', file='admin/settings/backup_restore.html', layout='admin',
         title='Backup & Restore', subtitle='Database backup and restore operations.',
         icon='database-backup', section='settings', page='settings', type='settings',
         sections=[
             ('Backup', [
                 ('Auto Backup', 'auto_backup', 'toggle', False, ''),
                 ('Backup Frequency', 'backup_freq', 'select', False, 'Daily / Weekly / Monthly'),
                 ('Keep Last', 'keep_count', 'number', False, '10'),
                 ('Backup Location', 'backup_path', 'text', False, ''),
                 ('Last Backup', 'last_backup', 'text', False, ''),
             ]),
         ]),

    dict(route='/admin/settings/users', file='admin/settings/user_management.html', layout='admin',
         title='User Management', subtitle='Manage system users and their access.',
         icon='user-cog', section='settings', page='settings', type='list',
         cols=['Username', 'Name', 'Role', 'Branch', 'Status', 'Last Login'],
         actions=[('Add User', 'user-plus', 'primary')]),

    dict(route='/admin/settings/security', file='admin/settings/security_settings.html', layout='admin',
         title='Security Settings', subtitle='Password policy and security controls.',
         icon='shield-check', section='settings', page='settings', type='settings',
         sections=[
             ('Password Policy', [
                 ('Min Password Length', 'min_length', 'number', False, '6'),
                 ('Require Special Character', 'special_char', 'toggle', False, ''),
                 ('Require Number', 'require_number', 'toggle', False, ''),
                 ('Force Change on First Login', 'force_change', 'toggle', False, ''),
                 ('Password Expiry (Days)', 'expiry_days', 'number', False, '90'),
                 ('Max Login Attempts', 'max_attempts', 'number', False, '5'),
             ]),
             ('Session', [
                 ('Session Timeout (Minutes)', 'session_timeout', 'number', False, '60'),
                 ('Two-Factor Authentication', 'two_factor', 'toggle', False, ''),
             ]),
         ]),

    dict(route='/admin/settings/system', file='admin/settings/system_configuration.html', layout='admin',
         title='System Configuration', subtitle='Advanced system and application settings.',
         icon='settings', section='settings', page='settings', type='settings',
         sections=[
             ('General', [
                 ('System Name', 'system_name', 'text', True, 'Smart Dairy ERP'),
                 ('Currency', 'currency', 'select', False, 'INR (₹)'),
                 ('Default Language', 'language', 'select', False, 'English / मराठी / हिन्दी'),
                 ('Timezone', 'timezone', 'select', False, 'Asia/Kolkata'),
                 ('Date Format', 'date_format', 'select', False, 'DD-MM-YYYY / MM-DD-YYYY'),
                 ('Maintenance Mode', 'maintenance_mode', 'toggle', False, ''),
                 ('Debug Mode', 'debug_mode', 'toggle', False, ''),
             ]),
         ]),
]
