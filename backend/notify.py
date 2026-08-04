"""
Smart Dairy ERP — Automatic Notifications

Creates Notification records for key business events (farmer registered,
verified, payment approved/paid, milk rejected, PO received, low stock,
vehicle service due, etc.).
"""
from backend.app import db
from backend.models import Notification, InventoryItem, Vehicle, Branch, User


def notify(notif_type, title, message, link=None, user_id=None):
    """Create a notification. user_id=None → global notification (all users)."""
    n = Notification(
        user_id=user_id,
        type=notif_type,
        title=title[:200],
        message=message,
        link=link,
        read=False,
    )
    db.session.add(n)
    return n


def notify_low_stock():
    """Alert for inventory items below minimum stock (global)."""
    items = InventoryItem.query.all()
    low = [i for i in items if i.stock is not None and i.stock <= (i.min_stock or 0)]
    for item in low:
        notify('inventory', 'Low Stock Alert',
               f'{item.name} is below minimum stock ({item.stock} {item.unit or ""} left).',
               link='inventory')


def notify_service_due():
    """Alert when a vehicle's next service or insurance is due (global)."""
    from datetime import date, timedelta
    today = date.today()
    soon = today + timedelta(days=14)
    vehicles = Vehicle.query.all()
    for v in vehicles:
        if v.next_service_date and today <= v.next_service_date <= soon:
            notify('vehicle', 'Service Due',
                   f'{v.vehicle_number} service is due on {v.next_service_date}.',
                   link='vehicles')
        if v.insurance_expiry and today <= v.insurance_expiry <= soon:
            notify('vehicle', 'Insurance Expiring',
                   f'{v.vehicle_number} insurance expires on {v.insurance_expiry}.',
                   link='vehicles')
