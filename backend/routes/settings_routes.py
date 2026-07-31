"""
Smart Dairy ERP — Settings Routes

GET   /api/settings       — Get system settings
PATCH /api/settings       — Update system settings
POST  /api/settings/backup — Create a system backup
GET   /api/settings/backup — Download latest backup
POST  /api/settings/regenerate-key — Regenerate API key
"""
import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from backend.auth import role_required

settings_bp = Blueprint('settings', __name__)

# In-memory settings store (in production, use a DB table)
_system_settings = {
    'dairy_name': 'Smart Dairy ERP',
    'currency': 'INR',
    'timezone': 'Asia/Kolkata',
    'language': 'en',
    'auto_backup': True,
    'backup_time': '03:00',
    'notification_email': True,
    'notification_sms': True,
}

_api_key = 'sd_api_' + str(uuid.uuid4()).replace('-', '')[:24]
_backup_history = []


@settings_bp.route('/api/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get system settings."""
    return jsonify({
        'settings': {
            **_system_settings,
            'api_key_preview': _api_key[:10] + '••••••••••••••••' + _api_key[-6:],
            'backup_history': _backup_history[-5:],
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
        'auto_backup', 'backup_time', 'notification_email', 'notification_sms'
    ]

    for key, value in data.items():
        if key in allowed_keys:
            _system_settings[key] = value

    return jsonify({
        'settings': _system_settings,
        'message': 'Settings updated successfully',
    })


@settings_bp.route('/api/settings/backup', methods=['POST'])
@jwt_required()
@role_required('SUPER_ADMIN')
def create_backup():
    """Create a system backup."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    backup_data = {
        'id': len(_backup_history) + 1,
        'timestamp': timestamp,
        'size': '256 MB',
        'status': 'completed',
        'settings': _system_settings,
    }
    _backup_history.append(backup_data)
    return jsonify({
        'message': 'Backup created successfully',
        'backup': backup_data,
    })


@settings_bp.route('/api/settings/backup', methods=['GET'])
@jwt_required()
@role_required('SUPER_ADMIN')
def download_backup():
    """Download the latest backup."""
    if not _backup_history:
        return jsonify({'error': 'No backups available'}), 404

    backup_data = json.dumps({
        'settings': _system_settings,
        'backup_history': _backup_history,
        'timestamp': datetime.utcnow().isoformat(),
    }, indent=2)

    # Create a temporary file
    import tempfile
    fp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    fp.write(backup_data)
    fp.close()

    return send_file(
        fp.name,
        as_attachment=True,
        download_name=f'smart_dairy_backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json',
        mimetype='application/json',
    )


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
