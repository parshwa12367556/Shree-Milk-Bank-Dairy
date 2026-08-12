"""
Smart Dairy ERP — WSGI Entry Point

Serves the Flask application on any WSGI server.

Linux (gunicorn):
    FLASK_ENV=production gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app

Windows (waitress):
    python -c "from waitress import serve; from wsgi import app; serve(app, host='0.0.0.0', port=8000)"
"""
from backend.app import create_app

app = create_app()
