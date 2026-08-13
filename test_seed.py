"""Quick verification script for database seeding.

Runs against an ISOLATED scratch database (smart_dairy_test.db by default,
or TEST_DB_PATH) — it NEVER touches the real production/development database
(smart_dairy.db). A safety assertion refuses to run against the production
path, and the database connections are disposed at the end.
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Isolated test database — never the real smart_dairy.db.
DB_PATH = os.getenv('TEST_DB_PATH', 'smart_dairy_test.db')

# Safety assertion: destructive tests must never point at the production DB.
PROD_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'smart_dairy.db'))
TEST_DB_ABS = os.path.abspath(DB_PATH)
if TEST_DB_ABS == PROD_DB_PATH:
    raise RuntimeError(
        "Refusing to run destructive tests against the production database "
        f"({PROD_DB_PATH}). Set TEST_DB_PATH to an isolated test database."
    )

if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except PermissionError:
        raise SystemExit(
            f"Cannot remove test database {DB_PATH}: file is locked by another process. "
            "Close any process holding it and re-run."
        )
    print(f"Removed old test database ({DB_PATH})")

# Point the app at the isolated database BEFORE importing the app factory.
os.environ['DATABASE_URL'] = 'sqlite:///' + DB_PATH.replace('\\', '/')

sys.path.insert(0, os.path.dirname(__file__))
from backend.app import create_app, db  # noqa: E402

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

# Dispose the engine so the test database file is never left locked on Windows.
with app.app_context():
    db.session.remove()
    db.engine.dispose()
print(f"\nTest database used: {DB_PATH} (isolated — production DB untouched)")
