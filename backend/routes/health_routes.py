"""
Smart Dairy ERP — Health Check Route

GET /api/health — Health check endpoint
"""
from datetime import datetime
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint. No authentication required."""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })
