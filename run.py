"""
Smart Dairy ERP — Application Entry Point

Usage:
    python run.py          # Start development server
    python run.py --seed   # Seed database with sample data
"""
import sys
from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    if '--seed' in sys.argv:
        from backend.seed import seed_database
        with app.app_context():
            seed_database()
        print('Database seeded successfully.')
    
    app.run(debug=True, port=5000)
