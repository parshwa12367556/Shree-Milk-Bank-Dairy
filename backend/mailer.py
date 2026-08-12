"""
Shree Milk Bank — Email Sending
================================
Reusable SMTP mailer built entirely on the Python standard library
(smtplib + email.message) — no new dependencies.

The SMTP configuration is read from the system settings store
(backend/modules/admin/settings.py), which the Head Office configures via
Settings → Email Settings. When SMTP is not configured (or email
notifications are disabled), sending is skipped gracefully — the caller's
business transaction is NEVER blocked or broken by email delivery.

Security rules followed here:
  * The recipient address always comes from the database record passed in —
    never from client-supplied input.
  * Failures are caught and logged; send_email returns (False, reason).
"""
import logging
import smtplib
import threading
from email.message import EmailMessage

from flask import render_template

from backend.modules.admin.settings import _system_settings

logger = logging.getLogger(__name__)

DEFAULT_FROM = 'Shree Milk Bank <noreply@shreemilkbank.com>'

# Deliver in a background thread so SMTP latency (up to the 15s timeout)
# never stalls the request that triggered the email (e.g. the branch
# operator's "Save Collection" call). Tests flip this to False for
# deterministic capture.
SEND_ASYNC = True


def get_smtp_config():
    """Return the current SMTP settings dict (possibly unconfigured)."""
    return {
        'host': (_system_settings.get('email_smtp_host') or '').strip(),
        'port': int(_system_settings.get('email_smtp_port') or 587),
        'username': (_system_settings.get('email_smtp_username') or '').strip(),
        'password': (_system_settings.get('email_smtp_password') or '').strip(),
        'from': (_system_settings.get('email_from') or '').strip() or DEFAULT_FROM,
        'enabled': bool(_system_settings.get('notification_email', True)),
    }


def is_email_configured():
    """True when SMTP is configured AND email notifications are enabled."""
    cfg = get_smtp_config()
    return bool(cfg['enabled'] and cfg['host'])


def send_email(to_address, subject, html_body):
    """
    Send an HTML email over SMTP. Never raises.

    Args:
        to_address: recipient email (must come from the database record)
        subject: email subject line
        html_body: rendered HTML body

    Returns:
        (True, None) on success, or (False, reason) when skipped/failed.
    """
    if not to_address or '@' not in to_address:
        return False, 'no valid recipient address'

    cfg = get_smtp_config()
    if not cfg['enabled']:
        return False, 'email notifications are disabled'
    if not cfg['host']:
        return False, 'SMTP not configured (set it in Settings → Email Settings)'

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = cfg['from']
        msg['To'] = to_address
        msg.set_content('Please view this email in an HTML-capable email client.')
        msg.add_alternative(html_body, subtype='html')

        if int(cfg['port']) == 465:
            with smtplib.SMTP_SSL(cfg['host'], cfg['port'], timeout=15) as server:
                if cfg['username']:
                    server.login(cfg['username'], cfg['password'])
                server.send_message(msg)
        else:
            with smtplib.SMTP(cfg['host'], cfg['port'], timeout=15) as server:
                try:
                    server.starttls()
                except smtplib.SMTPNotSupportedError:
                    pass  # plain SMTP (e.g. local test server)
                if cfg['username']:
                    server.login(cfg['username'], cfg['password'])
                server.send_message(msg)

        logger.info('Email sent to %s: %s', to_address, subject)
        return True, None
    except Exception as exc:  # noqa: BLE001 — delivery must never raise
        logger.warning('Email to %s failed (%s): %s', to_address, subject, exc)
        return False, str(exc)


# ── Business email builders ──────────────────────────────────────────────

def _fmt(value, digits=2, suffix=''):
    """Format a number for the email (safe for None)."""
    if value is None:
        return '—'
    try:
        return f'{float(value):.{digits}f}{suffix}'
    except (TypeError, ValueError):
        return '—'


def send_payment_email(payment):
    """
    Send the 'Payment Approved / Paid' email to the farmer's registered
    email (read from the database record — never from the frontend). Called
    only after the payment transition has committed. Best-effort delivery.

    Returns (True, None) on success or (False, reason) when skipped/failed.
    """
    farmer = payment.farmer if payment else None
    to_address = (farmer.email or '').strip() if farmer else ''
    if not to_address:
        return False, 'farmer has no email on file'

    status = (payment.status or 'PENDING').title()
    period = f"{payment.period_start.strftime('%d-%b-%Y')} to {payment.period_end.strftime('%d-%b-%Y')}" \
        if payment.period_start and payment.period_end else '—'

    html = render_template(
        'emails/payment.html',
        farmer_name=farmer.name,
        farmer_code=farmer.farmer_code,
        pay_code=payment.pay_code or '—',
        period=period,
        total_quantity=_fmt(payment.total_quantity, 2, ' Liters'),
        collection_count=payment.collection_count or 0,
        payment_status=status,
        gross_amount=_fmt(payment.gross_amount if payment.gross_amount is not None else payment.total_amount, 2),
        deductions=_fmt(payment.deductions or 0, 2),
        net_amount=_fmt(payment.total_amount, 2),
        reference=payment.reference or '',
    )
    subject = f'Payment {status} - Shree Milk Bank ({payment.pay_code})'
    if SEND_ASYNC:
        threading.Thread(
            target=lambda: send_email(to_address, subject, html),
            daemon=True,
        ).start()
        return True, None
    return send_email(to_address, subject, html)


def send_milk_collection_email(collection):
    """
    Send the 'New Milk Collection Recorded' email to the farmer's registered
    email address (read from the farmer's database record — never from the
    frontend). Called only after the collection transaction has committed.

    Returns (True, None) on success or (False, reason) when skipped/failed.
    """
    farmer = collection.farmer
    to_address = (farmer.email or '').strip() if farmer else ''
    if not to_address:
        return False, 'farmer has no email on file'

    branch = collection.branch
    branch_label = f"Shree Milk Bank - {branch.code}" if branch else 'Shree Milk Bank'

    html = render_template(
        'emails/milk_collection.html',
        farmer_name=farmer.name,
        farmer_code=farmer.farmer_code,
        branch_label=branch_label,
        date_str=collection.date.strftime('%d-%b-%Y') if collection.date else '—',
        time_str=collection.created_at.strftime('%I:%M %p') if collection.created_at else '—',
        shift=(collection.shift or '').title() or '—',
        milk_type=(collection.milk_type or '').title() or '—',
        quantity=_fmt(collection.quantity, 2, ' Liters'),
        fat=_fmt(collection.fat, 1, '%'),
        snf=_fmt(collection.snf, 1, '%'),
        temperature=_fmt(collection.temperature, 1, '°C'),
        water=_fmt(collection.water, 0, '%'),
        rate=_fmt(collection.rate_per_liter, 2),
        amount=_fmt(collection.amount, 2),
        status=(collection.status or '').title() or '—',
        receipt_no=collection.receipt_no or '—',
    )
    subject = 'New Milk Collection Recorded - Shree Milk Bank'
    if SEND_ASYNC:
        # All data (recipient, subject, rendered body) is materialized above,
        # inside the request/app context — the worker thread only performs
        # the SMTP conversation, so no Flask/SQLAlchemy context is needed and
        # the operator's request never waits on the network.
        threading.Thread(
            target=lambda: send_email(to_address, subject, html),
            daemon=True,
        ).start()
        return True, None
    return send_email(to_address, subject, html)
