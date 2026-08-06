"""
Smart Dairy ERP — Farmer portal page registry for the template generator.
"""

FARMER_PAGES = [
    dict(route='/farmer/profile', file='farmer/profile.html', layout='farmer',
         title='My Profile', subtitle='Your personal and dairy account information.',
         icon='user-circle', section='profile', page='profile', type='profile',
         tabs=['Profile', 'Livestock', 'Bank Details']),

    dict(route='/farmer/passbook', file='farmer/passbook.html', layout='farmer',
         title='Passbook', subtitle='Your milk collections and payments at a glance.',
         icon='book-open', section='passbook', page='passbook', type='report',
         cols=['Date', 'Shift', 'Qty', 'Fat', 'SNF', 'Rate', 'Credit', 'Debit', 'Balance']),

    dict(route='/farmer/milk-history', file='farmer/milk_collection_history.html', layout='farmer',
         title='Milk Collection History', subtitle='All your milk collections.',
         icon='milk', section='milk_history', page='milk_history', type='list',
         cols=['Receipt', 'Date', 'Shift', 'Qty', 'Fat', 'SNF', 'Rate', 'Amount']),

    dict(route='/farmer/payments', file='farmer/payment_history.html', layout='farmer',
         title='Payment History', subtitle='Payments received for your milk supply.',
         icon='wallet', section='payments', page='payments', type='list',
         cols=['Pay Code', 'Period', 'Amount', 'Method', 'Status', 'Paid On']),

    dict(route='/farmer/payment-status', file='farmer/payment_status.html', layout='farmer',
         title='Payment Status', subtitle='Current status of your pending payments.',
         icon='clock', section='payment_status', page='payment_status', type='list',
         cols=['Period', 'Amount', 'Status', 'Expected On', 'Remarks']),

    dict(route='/farmer/bank-details', file='farmer/bank_details.html', layout='farmer',
         title='Bank Details', subtitle='Your bank account information for payments.',
         icon='landmark', section='bank_details', page='bank_details', type='form',
         sections=[
             ('Bank Account', [
                 ('Account Holder Name', 'account_holder', 'text', True, 'As per bank records'),
                 ('Bank Name', 'bank_name', 'text', True, ''),
                 ('Branch Name', 'branch_name', 'text', True, ''),
                 ('Account Number', 'account_number', 'text', True, ''),
                 ('IFSC Code', 'ifsc', 'text', True, ''),
                 ('UPI ID', 'upi', 'text', False, ''),
                 ('Verified', 'verified', 'text', False, 'Pending verification'),
             ]),
         ]),

    dict(route='/farmer/documents', file='farmer/documents.html', layout='farmer',
         title='My Documents', subtitle='Documents submitted for your profile.',
         icon='file-text', section='documents', page='documents', type='list',
         cols=['Document', 'Type', 'Submitted', 'Status', 'Remarks'],
         actions=[('Upload Document', 'upload', 'primary')]),

    dict(route='/farmer/notifications', file='farmer/notifications.html', layout='farmer',
         title='Notifications', subtitle='Messages and alerts from your dairy.',
         icon='bell', section='notifications', page='notifications', type='simple',
         actions=[('Mark All Read', 'check-check', 'secondary')]),

    dict(route='/farmer/grievance', file='farmer/grievance.html', layout='farmer',
         title='Grievance', subtitle='Raise a complaint or request with the dairy.',
         icon='message-square', section='grievance', page='grievance', type='form',
         sections=[
             ('New Grievance', [
                 ('Subject', 'subject', 'text', True, 'Brief subject'),
                 ('Category', 'category', 'select', True, 'Payment / Quality / Collection / Other'),
                 ('Description', 'description', 'textarea', True, 'Describe your issue'),
                 ('Related Receipt', 'receipt', 'text', False, 'Optional receipt number'),
                 ('Attach File', 'attachment', 'file', False, ''),
             ]),
             ('Previous Grievances', []),
         ]),
]
