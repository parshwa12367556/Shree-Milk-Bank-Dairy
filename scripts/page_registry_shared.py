"""
Smart Dairy ERP — Shared page registry for the template generator.
"""

SHARED_PAGES = [
    dict(route='/shared/profile', file='shared/profile.html', layout='shared',
         title='My Profile', subtitle='Your account information across the system.',
         icon='user-circle', section='profile', page='profile', type='profile',
         tabs=['Profile', 'Preferences', 'Security']),

    dict(route='/shared/notifications', file='shared/notifications.html', layout='shared',
         title='Notifications', subtitle='All system notifications for your account.',
         icon='bell', section='notifications', page='notifications', type='simple',
         actions=[('Mark All Read', 'check-check', 'secondary')]),

    dict(route='/shared/help', file='shared/help.html', layout='shared',
         title='Help Center', subtitle='Get help with using the Smart Dairy ERP.',
         icon='help-circle', section='help', page='help', type='simple'),

    dict(route='/shared/user-guide', file='shared/user_guide.html', layout='shared',
         title='User Guide', subtitle='Complete guide to the Smart Dairy ERP system.',
         icon='book-open', section='user_guide', page='user_guide', type='simple'),

    dict(route='/shared/faq', file='shared/faq.html', layout='shared',
         title='FAQ', subtitle='Frequently asked questions and answers.',
         icon='help-circle', section='faq', page='faq', type='simple'),

    dict(route='/shared/search', file='shared/search.html', layout='shared',
         title='Global Search', subtitle='Search across farmers, receipts, invoices and more.',
         icon='search', section='search', page='search', type='simple'),

    dict(route='/shared/qr-scanner', file='shared/qr_scanner.html', layout='shared',
         title='QR Scanner', subtitle='Scan a farmer QR code to look up their details.',
         icon='scan-line', section='qr_scanner', page='qr_scanner', type='simple'),

    dict(route='/shared/activity-timeline', file='shared/activity_timeline.html', layout='shared',
         title='Activity Timeline', subtitle='Your recent activity across the system.',
         icon='activity', section='activity_timeline', page='activity_timeline', type='audit',
         cols=['Time', 'Module', 'Action', 'Detail']),

    dict(route='/shared/contact-support', file='shared/contact_support.html', layout='shared',
         title='Contact Support', subtitle='Reach out to the support team.',
         icon='headphones', section='contact_support', page='contact_support', type='form',
         sections=[
             ('Contact Form', [
                 ('Subject', 'subject', 'text', True, 'How can we help?'),
                 ('Category', 'category', 'select', True, 'Technical / Billing / Feature / Other'),
                 ('Priority', 'priority', 'select', False, 'Low / Medium / High'),
                 ('Message', 'message', 'textarea', True, 'Describe your issue in detail'),
             ]),
         ]),

    dict(route='/shared/feedback', file='shared/feedback.html', layout='shared',
         title='Feedback', subtitle='Share your feedback to help us improve.',
         icon='message-square', section='feedback', page='feedback', type='form',
         sections=[
             ('Feedback', [
                 ('Rating', 'rating', 'select', True, '1 - Poor / 5 - Excellent'),
                 ('Category', 'category', 'select', False, 'App / Collection / Payments / Support'),
                 ('Feedback', 'feedback', 'textarea', True, 'Your feedback'),
                 ('Would you recommend us?', 'recommend', 'select', False, 'Yes / No / Maybe'),
             ]),
         ]),
]
