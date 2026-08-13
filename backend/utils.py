"""
Smart Dairy ERP — Utility Functions

Common helper functions used throughout the application.
"""
import hashlib
import hmac
from datetime import datetime, date, timezone


# ── Timezone-consistent UTC helpers ───────────────────────────────────────
# The whole application uses ONE convention: timezone-aware UTC datetimes.
# (SQLAlchemy stores aware datetimes with a +00:00 suffix; on read they come
# back naive, so `ensure_utc` re-tags them before any Python-side comparison.)

def utcnow():
    """Current UTC datetime, timezone-aware (single app-wide convention)."""
    return datetime.now(timezone.utc)


def ensure_utc(dt):
    """
    Return a datetime as timezone-aware UTC, or None.

    Values loaded from the database come back naive (SQLAlchemy DateTime
    drops tzinfo on read) even though they were stored as UTC — this helper
    re-tags them so aware/naive comparison TypeErrors are impossible.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ── Farmer QR payload helpers ─────────────────────────────────────────────
# The QR payload is a signed opaque farmer identifier — it carries NO private
# data (no Aadhaar/PAN/bank/mobile). Format: FARMER:<code>:<hmac-sha256 hex>
# The signature proves the payload was minted by this server, so a scanned
# QR resolves to the right farmer without enabling impersonation or forgery.

_QR_VERSION = 'v1'


def sign_farmer_qr(farmer_code):
    """
    Build the signed QR payload for a farmer code.

    Returns None when the app's signing secret is unavailable (should not
    happen — SECRET_KEY is always configured).
    """
    from flask import current_app
    secret = current_app.config.get('SECRET_KEY') or ''
    if not secret:
        return None
    body = f'FARMER:{farmer_code}:{_QR_VERSION}'.encode('utf-8')
    sig = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    return f'{body.decode("utf-8")}:{sig}'


def verify_farmer_qr(payload):
    """
    Validate a signed QR payload and return the farmer code, or None.

    Recomputes the HMAC and compares in constant time; a forged or tampered
    payload (wrong code, wrong signature, wrong version) is rejected.
    """
    if not payload or not isinstance(payload, str):
        return None
    parts = payload.split(':')
    if len(parts) != 4 or parts[0] != 'FARMER' or parts[2] != _QR_VERSION:
        return None
    farmer_code, version, sig = parts[1], parts[2], parts[3]
    from flask import current_app
    secret = current_app.config.get('SECRET_KEY') or ''
    if not secret:
        return None
    body = f'FARMER:{farmer_code}:{version}'.encode('utf-8')
    expected = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    return farmer_code


def fmt_inr(n, d=2):
    """
    Format a number as Indian Rupees.
    
    Args:
        n: Number to format
        d: Decimal places
    
    Returns:
        Formatted currency string
    """
    if n is None:
        return '₹0.00'
    return f'₹{n:,.{d}f}'


def fmt_num(n, d=0):
    """
    Format a number with Indian-style commas.
    
    Args:
        n: Number to format
        d: Decimal places
    
    Returns:
        Formatted number string
    """
    if n is None:
        return '0'
    return f'{n:,.{d}f}'


def fmt_date(d):
    """
    Format a date to readable string.
    
    Args:
        d: Date object or ISO string
    
    Returns:
        Formatted date string like "19 Jul 2026"
    """
    if d is None:
        return '-'
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d)
        except (ValueError, TypeError):
            return d
    return d.strftime('%d %b %Y')


def today_iso():
    """
    Get today's date as ISO string.
    
    Returns:
        'YYYY-MM-DD' format
    """
    return date.today().isoformat()


def now_iso():
    """
    Get current datetime as ISO string.
    
    Returns:
        ISO 8601 datetime string
    """
    return datetime.now().isoformat()


def generate_receipt_no(seq):
    """
    Generate a sequential receipt number.
    
    Format: RC + 7-digit zero-padded sequence
    
    Args:
        seq: Sequence number
    
    Returns:
        Receipt number string (e.g., RC0000001)
    """
    return f'RC{seq:07d}'


def generate_farmer_code(branch_code, seq):
    """
    Generate a farmer code based on branch code and per-branch serial.
    
    Format: <branch_code><3-digit zero-padded serial>
    e.g. BR01 + 1 → BR01001, BR01 + 42 → BR01042
    
    Args:
        branch_code: Branch code (e.g., BR01)
        seq: Per-branch serial number (1-999)
    
    Returns:
        Farmer code string (e.g., BR01001)
    """
    seq = max(1, min(int(seq), 999))
    return f'{branch_code}{seq:03d}'


def generate_farmer_email(farmer_code):
    """
    Generate a deterministic email address for a farmer that has no email
    on file. Used so every farmer can sign in with email + phone number.

    Format: <farmer_code lowercased>@dairy.com  (e.g. BR01001 -> br01001@dairy.com)

    Args:
        farmer_code: Farmer code (e.g., BR01001)

    Returns:
        Email address string
    """
    code = (farmer_code or 'farmer').lower().strip()
    return f'{code}@dairy.com'


def generate_pay_code(seq):
    """
    Generate a sequential payment code.
    
    Format: PAY + 7-digit zero-padded sequence
    
    Args:
        seq: Sequence number
    
    Returns:
        Payment code string (e.g., PAY0000001)
    """
    return f'PAY{seq:07d}'


def today_str():
    """Get today's date in 'YYYY-MM-DD' format."""
    return date.today().isoformat()


def parse_date(date_str):
    """
    Parse a date string into a date object.
    
    Args:
        date_str: Date string in ISO format or 'YYYY-MM-DD'
    
    Returns:
        Date object or None
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
