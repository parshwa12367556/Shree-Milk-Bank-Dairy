"""
Smart Dairy ERP — Development Entry Point

Usage:
    python run.py          # Start development server (FLASK_ENV=development)
    python run.py --seed   # Seed database with sample data first

For production use wsgi.py / production.py (or gunicorn/waitress directly).
"""
import os
import sys

from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    if '--seed' in sys.argv:
        from backend.seed import seed_database
        with app.app_context():
            seed_database()
        print('Database seeded successfully.')

    debug = os.getenv('FLASK_ENV', 'development') != 'production'
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=debug, host=os.getenv('HOST', '127.0.0.1'), port=port)
