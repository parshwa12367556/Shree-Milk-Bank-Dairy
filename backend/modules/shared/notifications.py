"""
Smart Dairy ERP — Notification Routes

GET   /api/notifications      — List notifications
PATCH /api/notifications      — Mark notifications as read
DELETE /api/notifications     — Delete notifications
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Notification
from backend.auth import get_identity

notification_bp = Blueprint('notifications', __name__)


@notification_bp.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for the current user."""
    limit = request.args.get('limit', 20, type=int)
    notif_type = request.args.get('type', '')
    unread_only = request.args.get('unread', '').lower() == 'true'

    user = get_identity()
    query = Notification.query.order_by(Notification.created_at.desc())

    # Filter by user or global
    query = query.filter(
        db.or_(Notification.user_id == user.get('uid'), Notification.user_id.is_(None))
    )

    if notif_type:
        query = query.filter_by(type=notif_type)
    if unread_only:
        query = query.filter_by(read=False)

    notifications = query.limit(limit).all()

    # Unread count is scoped to THIS user (+ global announcements) — never a
    # whole-database count, which would leak other users' activity volume.
    unread_count = Notification.query.filter(
        db.or_(Notification.user_id == user.get('uid'), Notification.user_id.is_(None)),
        Notification.read == False  # noqa: E712
    ).count()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count,
    })


@notification_bp.route('/api/notifications', methods=['PATCH'])
@jwt_required()
def mark_read():
    """Mark notifications as read."""
    data = request.get_json()
    notification_ids = data.get('ids', []) if data else []

    if notification_ids:
        notifications = Notification.query.filter(Notification.id.in_(notification_ids)).all()
    else:
        # Mark all as read
        user = get_identity()
        notifications = Notification.query.filter(
            db.or_(Notification.user_id == user.get('uid'), Notification.user_id.is_(None)),
            Notification.read == False
        ).all()

    for n in notifications:
        n.read = True

    db.session.commit()
    return jsonify({'message': f'{len(notifications)} notification(s) marked as read'})


@notification_bp.route('/api/notifications', methods=['DELETE'])
@jwt_required()
def delete_notifications():
    """Delete notifications."""
    data = request.get_json()
    notification_ids = data.get('ids', []) if data else []

    if notification_ids:
        Notification.query.filter(Notification.id.in_(notification_ids)).delete()
    else:
        # Delete all read notifications
        user = get_identity()
        Notification.query.filter(
            db.or_(Notification.user_id == user.get('uid'), Notification.user_id.is_(None)),
            Notification.read == True
        ).delete(synchronize_session=False)

    db.session.commit()
    return jsonify({'message': 'Notifications deleted'})
