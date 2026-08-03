"""
Smart Dairy ERP — Utility Functions

Common helper functions used throughout the application.
"""
from datetime import datetime, date


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
