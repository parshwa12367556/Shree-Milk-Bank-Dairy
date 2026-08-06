"""
Smart Dairy ERP — Branch page registry for the template generator.
"""

BRANCH_PAGES = [
    # ── Dashboard ────────────────────────────────────────────────
    dict(route='/branch/dashboard', file='branch/dashboard/dashboard.html', layout='branch',
         title='Branch Dashboard', subtitle="Welcome back! Here's what's happening at your branch today.",
         icon='layout-dashboard', section='dashboard', page='dashboard', type='dashboard',
         kpis=[
             ('kpi-collection', 'Today Collection', '486 L', 'milk', 'green'),
             ('kpi-farmers', 'Active Farmers', '312', 'users', 'blue'),
             ('kpi-avg-fat', 'Avg Fat', '4.1%', 'droplets', 'purple'),
             ('kpi-rejected', 'Rejected Today', '3', 'x-circle', 'red'),
             ('kpi-revenue', 'Revenue', '₹1,82,300', 'indian-rupee', 'gold'),
             ('kpi-pending', 'Pending Payments', '₹42,500', 'clock', 'amber'),
         ],
         actions=[('New Collection', 'plus', 'primary'), ('Refresh', 'refresh-cw', 'secondary')]),

    dict(route='/branch/daily-summary', file='branch/dashboard/daily_summary.html', layout='branch',
         title='Daily Summary', subtitle='Complete summary of today\'s operations.',
         icon='clipboard-list', section='dashboard', page='daily_summary', type='report',
         cols=['Shift', 'Farmers', 'Quantity', 'Avg Fat', 'Avg SNF', 'Amount']),

    dict(route='/branch/collection-statistics', file='branch/dashboard/collection_statistics.html', layout='branch',
         title='Collection Statistics', subtitle='Collection trends and statistics for this branch.',
         icon='bar-chart-3', section='dashboard', page='collection_statistics', type='report',
         cols=['Date', 'Morning', 'Evening', 'Total', 'Farmers', 'Avg Fat']),

    dict(route='/branch/recent-activity', file='branch/dashboard/recent_activity.html', layout='branch',
         title='Recent Activity', subtitle='Latest actions performed at this branch.',
         icon='activity', section='dashboard', page='recent_activity', type='audit',
         cols=['Time', 'User', 'Module', 'Action', 'Detail']),

    # ── Farmer ───────────────────────────────────────────────────
    dict(route='/branch/farmers', file='branch/farmer/farmer_list.html', layout='branch',
         title='Farmer List', subtitle='Farmers registered with this branch.',
         icon='users', section='farmers', page='farmer_list', type='list',
         cols=['Code', 'Farmer Name', 'Mobile', 'Village', 'Type', 'Quantity', 'Status'],
         actions=[('Register Farmer', 'user-plus', 'primary')]),

    dict(route='/branch/farmers/register', file='branch/farmer/register_farmer.html', layout='branch',
         title='Register Farmer', subtitle='Add a new farmer to this branch.',
         icon='user-plus', section='farmers', page='farmer_list', type='form',
         sections=[
             ('Personal Information', [
                 ('Farmer Name', 'farmer_name', 'text', True, 'Enter full name'),
                 ("Father's Name", 'father_name', 'text', False, ''),
                 ('Mobile Number', 'mobile', 'tel', True, '10-digit mobile'),
                 ('Alternate Mobile', 'alt_mobile', 'tel', False, ''),
                 ('Email', 'email', 'email', False, ''),
                 ('Aadhaar Number', 'aadhaar', 'text', True, '12-digit Aadhaar'),
                 ('PAN Number', 'pan', 'text', False, ''),
                 ('Date of Birth', 'dob', 'date', False, ''),
             ]),
             ('Address', [
                 ('Address', 'address', 'textarea', False, 'Full address'),
                 ('Village', 'village', 'text', True, 'Village name'),
                 ('Taluka', 'taluka', 'text', False, ''),
                 ('District', 'district', 'text', False, ''),
                 ('State', 'state', 'text', False, ''),
                 ('Pincode', 'pincode', 'text', False, ''),
             ]),
             ('Livestock & Milk', [
                 ('Milk Type', 'milk_type', 'select', True, 'Cow / Buffalo / Mixed'),
                 ('Number of Cows', 'cow_count', 'number', False, '0'),
                 ('Number of Buffaloes', 'buffalo_count', 'number', False, '0'),
                 ('Breed', 'breed', 'text', False, ''),
                 ('Preferred Shift', 'preferred_shift', 'select', False, 'Morning / Evening'),
                 ('QR Code', 'qr_code', 'text', False, 'Auto-generated'),
             ]),
             ('Bank Details', [
                 ('Account Holder Name', 'account_holder', 'text', False, ''),
                 ('Bank Name', 'bank_name', 'text', False, ''),
                 ('Branch Name', 'bank_branch', 'text', False, ''),
                 ('Account Number', 'account_number', 'text', False, ''),
                 ('IFSC Code', 'ifsc', 'text', False, ''),
                 ('UPI ID', 'upi', 'text', False, ''),
             ]),
         ]),

    dict(route='/branch/farmers/edit', file='branch/farmer/edit_farmer.html', layout='branch',
         title='Edit Farmer', subtitle='Update farmer information.',
         icon='edit-3', section='farmers', page='farmer_list', type='form',
         sections=[
             ('Personal Information', [
                 ('Farmer Name', 'farmer_name', 'text', True, 'Enter full name'),
                 ('Mobile Number', 'mobile', 'tel', True, '10-digit mobile'),
                 ('Alternate Mobile', 'alt_mobile', 'tel', False, ''),
                 ('Email', 'email', 'email', False, ''),
                 ('Date of Birth', 'dob', 'date', False, ''),
             ]),
             ('Address', [
                 ('Address', 'address', 'textarea', False, 'Full address'),
                 ('Village', 'village', 'text', True, 'Village name'),
                 ('Taluka', 'taluka', 'text', False, ''),
                 ('District', 'district', 'text', False, ''),
                 ('Pincode', 'pincode', 'text', False, ''),
             ]),
             ('Livestock & Milk', [
                 ('Milk Type', 'milk_type', 'select', True, 'Cow / Buffalo / Mixed'),
                 ('Number of Cows', 'cow_count', 'number', False, '0'),
                 ('Number of Buffaloes', 'buffalo_count', 'number', False, '0'),
                 ('Preferred Shift', 'preferred_shift', 'select', False, 'Morning / Evening'),
             ]),
         ]),

    dict(route='/branch/farmers/profile', file='branch/farmer/farmer_profile.html', layout='branch',
         title='Farmer Profile', subtitle='Complete profile of the farmer.',
         icon='user', section='farmers', page='farmer_list', type='profile',
         tabs=['Overview', 'Milk History', 'Payments', 'Documents']),

    dict(route='/branch/farmers/documents', file='branch/farmer/farmer_documents.html', layout='branch',
         title='Farmer Documents', subtitle='Documents submitted by farmers.',
         icon='file-text', section='farmers', page='farmer_list', type='list',
         cols=['Farmer', 'Document', 'Type', 'Submitted', 'Size', 'Status']),

    dict(route='/branch/farmers/milk-history', file='branch/farmer/milk_history.html', layout='branch',
         title='Milk History', subtitle='Milk collection records of branch farmers.',
         icon='milk', section='farmers', page='farmer_list', type='list',
         cols=['Receipt', 'Farmer', 'Date', 'Qty', 'Fat', 'SNF', 'Rate', 'Amount']),

    dict(route='/branch/farmers/payment-status', file='branch/farmer/payment_status.html', layout='branch',
         title='Payment Status', subtitle='Payment status of branch farmers.',
         icon='wallet', section='farmers', page='farmer_list', type='list',
         cols=['Farmer', 'Period', 'Amount', 'Status', 'Paid On', 'Method']),

    dict(route='/branch/farmers/passbook', file='branch/farmer/passbook.html', layout='branch',
         title='Passbook', subtitle='Farmer passbook with collection and payment entries.',
         icon='book-open', section='farmers', page='farmer_list', type='list',
         cols=['Date', 'Shift', 'Qty', 'Fat', 'SNF', 'Rate', 'Credit', 'Debit', 'Balance']),

    # ── Collection ───────────────────────────────────────────────
    dict(route='/branch/collection/morning', file='branch/collection/morning_collection.html', layout='branch',
         title='Morning Collection', subtitle='Record morning milk collections.',
         icon='sunrise', section='collection', page='morning_collection', type='dashboard',
         kpis=[
             ('col-morning-count', 'Farmers Done', '148 / 312', 'users', 'blue'),
             ('col-morning-qty', 'Quantity Collected', '286 L', 'milk', 'green'),
             ('col-morning-avg', 'Avg Fat', '4.2%', 'droplets', 'purple'),
             ('col-morning-pending', 'Pending Farmers', '164', 'clock', 'amber'),
         ],
         actions=[('Bulk Entry', 'layers', 'secondary')]),

    dict(route='/branch/collection/evening', file='branch/collection/evening_collection.html', layout='branch',
         title='Evening Collection', subtitle='Record evening milk collections.',
         icon='sunset', section='collection', page='morning_collection', type='dashboard',
         kpis=[
             ('col-eve-count', 'Farmers Done', '132 / 312', 'users', 'blue'),
             ('col-eve-qty', 'Quantity Collected', '248 L', 'milk', 'green'),
             ('col-eve-avg', 'Avg Fat', '4.0%', 'droplets', 'purple'),
             ('col-eve-pending', 'Pending Farmers', '180', 'clock', 'amber'),
         ],
         actions=[('Bulk Entry', 'layers', 'secondary')]),

    dict(route='/branch/collection/bulk', file='branch/collection/bulk_collection.html', layout='branch',
         title='Bulk Collection', subtitle='Quick bulk entry for multiple farmers.',
         icon='layers', section='collection', page='morning_collection', type='list',
         cols=['Farmer', 'Shift', 'Qty', 'Fat', 'SNF', 'Rate', 'Amount', 'Status'],
         actions=[('Save All', 'save', 'primary')]),

    dict(route='/branch/collection/history', file='branch/collection/collection_history.html', layout='branch',
         title='Collection History', subtitle='All collections recorded at this branch.',
         icon='history', section='collection', page='morning_collection', type='list',
         cols=['Receipt', 'Farmer', 'Date', 'Shift', 'Qty', 'Rate', 'Amount']),

    dict(route='/branch/collection/receipt', file='branch/collection/receipt.html', layout='branch',
         title='Receipt', subtitle='Collection receipt preview and printing.',
         icon='receipt', section='collection', page='morning_collection', type='simple'),

    # ── Quality ──────────────────────────────────────────────────
    dict(route='/branch/quality/testing', file='branch/quality/quality_testing.html', layout='branch',
         title='Quality Testing', subtitle='Record milk quality test results.',
         icon='test-tube', section='quality', page='quality', type='dashboard',
         kpis=[
             ('qty-tested', 'Tested Today', '96', 'test-tube', 'blue'),
             ('qty-pass', 'Passed', '93', 'check-circle', 'green'),
             ('qty-rejected', 'Rejected', '3', 'x-circle', 'red'),
             ('qty-avg-fat', 'Avg Fat', '4.1%', 'droplets', 'purple'),
         ],
         actions=[('New Test', 'plus', 'primary')]),

    dict(route='/branch/quality/rejected', file='branch/quality/rejected_milk.html', layout='branch',
         title='Rejected Milk', subtitle='Milk lots rejected during quality checks.',
         icon='x-circle', section='quality', page='quality', type='list',
         cols=['Receipt', 'Farmer', 'Date', 'Qty', 'Reason', 'Tested By'],
         actions=[('Export', 'download', 'secondary')]),

    dict(route='/branch/quality/history', file='branch/quality/quality_history.html', layout='branch',
         title='Quality History', subtitle='Historical quality test results.',
         icon='history', section='quality', page='quality', type='list',
         cols=['Date', 'Farmer', 'Fat', 'SNF', 'CLR', 'Result', 'Tested By']),

    dict(route='/branch/quality/lab-reports', file='branch/quality/lab_reports.html', layout='branch',
         title='Lab Reports', subtitle='Laboratory analysis reports.',
         icon='file-text', section='quality', page='quality', type='list',
         cols=['Report No', 'Date', 'Batch', 'Parameters', 'Result', 'Status']),

    # ── Inventory ────────────────────────────────────────────────
    dict(route='/branch/inventory/allocated', file='branch/inventory/allocated_inventory.html', layout='branch',
         title='Allocated Inventory', subtitle='Stock allocated to this branch.',
         icon='boxes', section='inventory', page='inventory', type='list',
         cols=['Item', 'Category', 'Allocated', 'Used', 'Remaining', 'Status']),

    dict(route='/branch/inventory/usage', file='branch/inventory/stock_usage.html', layout='branch',
         title='Stock Usage', subtitle='Record stock consumed at this branch.',
         icon='arrow-up-circle', section='inventory', page='inventory', type='form',
         sections=[
             ('Stock Usage', [
                 ('Item', 'item', 'select', True, 'Select Item'),
                 ('Quantity', 'quantity', 'number', True, '0'),
                 ('Purpose', 'purpose', 'select', True, 'Processing / Sales / Damage / Other'),
                 ('Date', 'date', 'date', False, ''),
                 ('Remarks', 'remarks', 'textarea', False, ''),
             ]),
         ]),

    dict(route='/branch/inventory/request', file='branch/inventory/stock_request.html', layout='branch',
         title='Stock Request', subtitle='Request additional stock from Head Office.',
         icon='send', section='inventory', page='inventory', type='form',
         sections=[
             ('Stock Request', [
                 ('Item', 'item', 'select', True, 'Select Item'),
                 ('Quantity', 'quantity', 'number', True, '0'),
                 ('Priority', 'priority', 'select', False, 'Normal / High / Urgent'),
                 ('Reason', 'reason', 'textarea', False, 'Why is this stock needed?'),
                 ('Required By', 'required_by', 'date', False, ''),
             ]),
         ]),

    dict(route='/branch/inventory/history', file='branch/inventory/inventory_history.html', layout='branch',
         title='Inventory History', subtitle='Stock movement history for this branch.',
         icon='history', section='inventory', page='inventory', type='audit',
         cols=['Date', 'Item', 'Type', 'Qty', 'Reference', 'User']),

    # ── Reports ──────────────────────────────────────────────────
    dict(route='/branch/reports/daily', file='branch/reports/daily_report.html', layout='branch',
         title='Daily Report', subtitle='Daily operational report.',
         icon='calendar', section='reports', page='reports', type='report',
         cols=['Shift', 'Farmers', 'Quantity', 'Amount', 'Rejected', 'Avg Fat']),

    dict(route='/branch/reports/weekly', file='branch/reports/weekly_report.html', layout='branch',
         title='Weekly Report', subtitle='Weekly collection and revenue report.',
         icon='calendar-days', section='reports', page='reports', type='report',
         cols=['Day', 'Morning', 'Evening', 'Total Qty', 'Amount']),

    dict(route='/branch/reports/monthly', file='branch/reports/monthly_report.html', layout='branch',
         title='Monthly Report', subtitle='Monthly collection and revenue report.',
         icon='calendar-range', section='reports', page='reports', type='report',
         cols=['Week', 'Farmers', 'Total Qty', 'Avg Fat', 'Amount']),

    dict(route='/branch/reports/farmers', file='branch/reports/farmer_report.html', layout='branch',
         title='Farmer Report', subtitle='Branch farmer-wise report.',
         icon='users', section='reports', page='reports', type='report',
         cols=['Farmer', 'Code', 'Total Qty', 'Total Amount', 'Avg Fat', 'Payments']),

    dict(route='/branch/reports/collection', file='branch/reports/collection_report.html', layout='branch',
         title='Collection Report', subtitle='Collection report by date range.',
         icon='milk', section='reports', page='reports', type='report',
         cols=['Date', 'Shift', 'Farmers', 'Qty', 'Avg Fat', 'Avg SNF', 'Amount']),

    dict(route='/branch/reports/quality', file='branch/reports/quality_report.html', layout='branch',
         title='Quality Report', subtitle='Quality test results report.',
         icon='flask-conical', section='reports', page='reports', type='report',
         cols=['Date', 'Samples', 'Avg Fat', 'Avg SNF', 'Rejected', 'Rejection %']),

    # ── Profile ──────────────────────────────────────────────────
    dict(route='/branch/profile', file='branch/profile/branch_profile.html', layout='branch',
         title='Branch Profile', subtitle='Your branch\'s profile and operating details.',
         icon='building-2', section='profile', page='profile', type='profile',
         tabs=['Overview', 'Contact', 'Operating Hours', 'Staff']),

    dict(route='/branch/profile/manager', file='branch/profile/manager_profile.html', layout='branch',
         title='Manager Profile', subtitle='Your personal profile information.',
         icon='user-circle', section='profile', page='profile', type='profile',
         tabs=['Profile', 'Change Password']),

    dict(route='/branch/profile/change-password', file='branch/profile/change_password.html', layout='branch',
         title='Change Password', subtitle='Update your account password.',
         icon='key', section='profile', page='profile', type='form',
         sections=[
             ('Change Password', [
                 ('Current Password', 'current', 'password', True, ''),
                 ('New Password', 'new', 'password', True, 'Minimum 6 characters'),
                 ('Confirm New Password', 'confirm', 'password', True, ''),
             ]),
         ]),
]
