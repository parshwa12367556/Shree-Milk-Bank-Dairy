"""
Smart Dairy ERP — Health Check Routes

GET /health      — Application + database connectivity (no auth)
GET /api/health  — Same, legacy alias
"""
from datetime import datetime
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


def _check():
    """Probe database connectivity. Returns (status, payload)."""
    db_up = True
    try:
        from backend.app import db
        db.session.execute(db.text('SELECT 1'))
    except Exception as exc:  # noqa: BLE001 — report any connectivity failure
        db_up = False
        print(f'[health] database check failed: {exc}')

    payload = {
        'status': 'ok' if db_up else 'degraded',
        'database': 'up' if db_up else 'down',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
    }
    return (200 if db_up else 503), payload


@health_bp.route('/health', methods=['GET'])
def health():
    code, payload = _check()
    return jsonify(payload), code


@health_bp.route('/api/health', methods=['GET'])
def health_alias():
    code, payload = _check()
    return jsonify(payload), code
