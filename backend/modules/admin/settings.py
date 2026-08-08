"""
Shree Milk Bank — Settings Routes

GET   /api/settings       — Get system settings
PATCH /api/settings       — Update system settings
POST  /api/settings/backup — Create a system backup
GET   /api/settings/backup — Download latest backup
POST  /api/settings/regenerate-key — Regenerate API key
"""
import os
import json
import uuid
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from backend.auth import role_required, get_identity
from backend.audit import log_audit
from backend.app import db

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

settings_bp = Blueprint('settings', __name__)

# In-memory settings store (in production, use a DB table)
_system_settings = {
    'dairy_name': 'Shree Milk Bank',
    'currency': 'INR',
    'timezone': 'Asia/Kolkata',
    'language': 'en',
    'auto_backup': True,
    'backup_time': '03:00',
    'notification_email': True,
    'notification_sms': True,

    # SMS gateway configuration (stored; actual sending requires a provider
    # API key, e.g. a national SMS gateway).
    'sms_provider': '',
    'sms_sender_id': '',
    'sms_api_key': '',
    'sms_api_url': '',

    # Email / SMTP configuration (stored; actual sending requires SMTP creds).
    'email_smtp_host': '',
    'email_smtp_port': '587',
    'email_from': '',
    'email_smtp_username': '',
    'email_smtp_password': '',
}

_api_key = 'sd_api_' + str(uuid.uuid4()).replace('-', '')[:24]


def _list_backups():
    """List backup files on disk (newest first)."""
    backups = []
    if not os.path.isdir(BACKUP_DIR):
        return backups
    for name in sorted(os.listdir(BACKUP_DIR), reverse=True):
        path = os.path.join(BACKUP_DIR, name)
        if os.path.isfile(path):
            backups.append({
                'id': name,
                'timestamp': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S'),
                'size': f'{os.path.getsize(path) / 1024:.1f} KB',
                'status': 'completed',
                'filename': name,
            })
    return backups[:20]


@settings_bp.route('/api/settings', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def get_settings():
    """Get system settings."""
    return jsonify({
        'settings': {
            **_system_settings,
            'api_key_preview': _api_key[:10] + '••••••••••••••••' + _api_key[-6:],
            'backup_history': _list_backups()[:5],
        }
    })


@settings_bp.route('/api/settings', methods=['PATCH'])
@jwt_required()
@role_required('SUPER_ADMIN', 'HEAD_OFFICE')
def update_settings():
    """Update system settings."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    allowed_keys = [
        'dairy_name', 'currency', 'timezone', 'language',
        'auto_backup', 'backup_time', 'notification_email', 'notification_sms',
        'sms_provider', 'sms_sender_id', 'sms_api_key', 'sms_api_url',
        'email_smtp_host', 'email_smtp_port', 'email_from',
        'email_smtp_username', 'email_smtp_password',
    ]

    for key, value in data.items():
        if key in allowed_keys:
            _system_settings[key] = value

    log_audit('UPDATE', 'Settings', None,
              detail=f'Settings updated: {list(data.keys())}')
    db.session.commit()

    return jsonify({
        'settings': _system_settings,
        'message': 'Settings updated successfully',
    })


@settings_bp.route('/api/settings/backup', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN')
def create_backup():
    """Create a system backup (snapshot of the SQLite database + settings)."""
    from config import Config
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    backup_data = {
        'id': timestamp,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'completed',
        'settings': _system_settings,
    }

    # Snapshot the SQLite file (if it exists)
    if os.path.exists(db_path):
        backup_file = os.path.join(BACKUP_DIR, f'smart_dairy_backup_{timestamp}.db')
        shutil.copy2(db_path, backup_file)
        backup_data['size'] = f'{os.path.getsize(backup_file) / 1024:.1f} KB'
        backup_data['filename'] = os.path.basename(backup_file)
    else:
        # Fallback: JSON settings backup
        backup_file = os.path.join(BACKUP_DIR, f'smart_dairy_backup_{timestamp}.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({'settings': _system_settings, 'timestamp': timestamp}, f, indent=2)
        backup_data['size'] = f'{os.path.getsize(backup_file) / 1024:.1f} KB'
        backup_data['filename'] = os.path.basename(backup_file)

    log_audit('CREATE', 'Backup', timestamp, detail=f'System backup created: {backup_data.get("filename")}')
    db.session.commit()
    return jsonify({
        'message': 'Backup created successfully',
        'backup': backup_data,
    })


@settings_bp.route('/api/settings/backup', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN')
def download_backup():
    """Download the latest backup file from disk."""
    backups = _list_backups()
    if not backups:
        return jsonify({'error': 'No backups available'}), 404

    latest = backups[0]
    filepath = os.path.join(BACKUP_DIR, latest['filename'])
    if not os.path.exists(filepath):
        return jsonify({'error': 'Backup file not found'}), 404

    return send_file(
        filepath,
        as_attachment=True,
        download_name=latest['filename'],
        mimetype='application/octet-stream',
    )


@settings_bp.route('/api/settings/backups', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN')
def list_backups():
    """List all backup files."""
    return jsonify({'backups': _list_backups()})


@settings_bp.route('/api/settings/restore/<filename>', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN')
def restore_backup(filename):
    """Restore a backup — copies the DB snapshot over the live database.

    NOTE: The server should be restarted after restore for a clean state.
    """
    from config import Config
    if os.path.basename(filename) != filename or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400

    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Backup file not found'}), 404
    if not filename.endswith('.db'):
        return jsonify({'error': 'Only database snapshots (.db) can be restored'}), 400

    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    # Safety copy of the current DB before overwriting
    safety = os.path.join(BACKUP_DIR, 'pre_restore_' + datetime.utcnow().strftime('%Y%m%d_%H%M%S') + '.db')
    if os.path.exists(db_path):
        shutil.copy2(db_path, safety)

    shutil.copy2(filepath, db_path)
    log_audit('UPDATE', 'Backup', filename, detail=f'Database restored from {filename}')
    db.session.commit()
    return jsonify({
        'message': f'Database restored from {filename}. Restart the server to apply cleanly.',
        'safety_copy': os.path.basename(safety),
    })


@settings_bp.route('/api/settings/regenerate-key', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN')
def regenerate_api_key():
    """Regenerate the API key."""
    global _api_key
    _api_key = 'sd_api_' + str(uuid.uuid4()).replace('-', '')[:24]
    return jsonify({
        'message': 'API key regenerated successfully',
        'api_key_preview': _api_key[:10] + '••••••••••••••••' + _api_key[-6:],
    })
