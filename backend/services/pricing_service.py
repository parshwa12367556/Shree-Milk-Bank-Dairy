"""
Smart Dairy ERP — Pricing Service
=================================
Single source of truth for milk pricing.

Rules enforced here:
  * Only the ADMIN creates/activates/deactivates rate rules (handled in the
    admin route module). This service is read-only for pricing rules.
  * BRANCH_OPERATOR collections use the CURRENTLY ACTIVE rate for the milk
    type on the collection date (effective_from <= date <= effective_to).
  * FARMER views are derived from the stored rate/amount on their
    collections — historical collections keep their original applied rate
    and are NEVER recalculated when rates change.
"""
from datetime import date as _date
from backend.app import db
from backend.models import RateMaster
from backend.pricing import compute_price

# Fallback rates used only when NO rate rule exists at all for a milk type
# (a brand-new installation before the admin has configured pricing).
FALLBACK_RATES = {'COW': (5.0, 2.5), 'BUFFALO': (6.5, 3.0), 'MIXED': (5.0, 2.5)}


def get_active_rate(milk_type, on_date=None):
    """
    Return the ACTIVE rate rule that applies on `on_date` (default today).

    Matching priority:
      1. status='ACTIVE' AND effective_from <= on_date
         AND (effective_to IS NULL OR effective_to >= on_date)
      2. latest ACTIVE rule regardless of date window (lenient fallback so a
         collection can never fail purely because a window is missing)

    Returns a RateMaster instance or None.
    """
    if on_date is None:
        on_date = _date.today()
    milk_type = (milk_type or 'COW').upper()

    # Exact window match first
    rule = RateMaster.query.filter(
        RateMaster.milk_type == milk_type,
        RateMaster.status == 'ACTIVE',
        RateMaster.effective_from <= on_date,
        db.or_(RateMaster.effective_to.is_(None), RateMaster.effective_to >= on_date),
    ).order_by(RateMaster.effective_from.desc(), RateMaster.version.desc()).first()

    if not rule:
        # Lenient fallback: newest ACTIVE rule for the milk type
        rule = RateMaster.query.filter_by(milk_type=milk_type, status='ACTIVE') \
            .order_by(RateMaster.version.desc()).first()
    return rule


def calculate_collection_price(milk_type, fat, snf, quantity, on_date=None):
    """
    Compute rate-per-liter and total amount for a milk collection.

    The backend is the source of truth: rate/amount are ALWAYS derived here
    from the active rate rule — a client-supplied amount is never trusted.

    Returns:
        {
          'rate': RateMaster | None,
          'fat_rate': float, 'snf_rate': float,
          'rate_per_liter': float, 'amount': float,
        }
    """
    rule = get_active_rate(milk_type, on_date)

    if rule:
        fat_rate = rule.fat_rate
        snf_rate = rule.snf_rate
    else:
        fat_rate, snf_rate = FALLBACK_RATES.get((milk_type or 'COW').upper(), (5.0, 2.5))

    try:
        fat = float(fat)
        snf = float(snf)
        quantity = float(quantity)
    except (TypeError, ValueError):
        fat, snf, quantity = 0.0, 0.0, 0.0

    price = compute_price(fat, snf, quantity, fat_rate, snf_rate)
    return {
        'rate': rule,
        'fat_rate': fat_rate,
        'snf_rate': snf_rate,
        'rate_per_liter': price['rate_per_liter'],
        'amount': price['amount'],
    }
