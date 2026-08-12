"""
Smart Dairy ERP — Production Entry Point (Windows-compatible)

Runs the application under Waitress with FLASK_ENV=production so DEBUG stays
off and the dev login bypass / dev OTP are disabled.

Usage:
    python production.py

Env:
    HOST   (default 0.0.0.0)
    PORT   (default 8000)
    THREADS (default 4)
"""
import os

os.environ.setdefault('FLASK_ENV', 'production')

try:
    from waitress import serve
except ImportError:
    raise SystemExit(
        'waitress is not installed. Run: pip install -r requirements.txt'
    )

from wsgi import app

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    threads = int(os.getenv('THREADS', '4'))
    print(f'Shree Milk Bank Dairy serving on http://{host}:{port} (waitress)')
    serve(app, host=host, port=port, threads=threads)
