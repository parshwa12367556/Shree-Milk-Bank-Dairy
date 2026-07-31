"""Quick verification script for database seeding."""
import os
import sys

# Delete existing db
if os.path.exists('smart_dairy.db'):
    os.remove('smart_dairy.db')
    print("Removed old database")

# Import and seed
sys.path.insert(0, os.path.dirname(__file__))
from backend.app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
    from backend.seed import seed_database
    seed_database()
    
    from backend.models import User, Branch, Farmer, Collection, Payment
    from backend.models import QualityTest, MilkRejection, InventoryItem, Employee, Vehicle
    
    print("\n=== SEED VERIFICATION ===")
    print(f"Users:       {User.query.count()}")
    print(f"Branches:    {Branch.query.count()}")
    print(f"Farmers:     {Farmer.query.count()}")
    print(f"Collections: {Collection.query.count()}")
    print(f"Payments:    {Payment.query.count()}")
    print(f"Quality:     {QualityTest.query.count()}")
    print(f"Rejections:  {MilkRejection.query.count()}")
    print(f"Inventory:   {InventoryItem.query.count()}")
    print(f"Employees:   {Employee.query.count()}")
    print(f"Vehicles:    {Vehicle.query.count()}")
    print("=== ALL OK ===")
