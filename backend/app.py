"""
Smart Dairy ERP — Flask Application Factory
"""
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration environment name
    
    Returns:
        Configured Flask application
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
        static_url_path='/static'
    )

    # Load configuration
    from config import config_by_name
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    # Register JWT error handlers
    register_jwt_handlers(jwt)

    # Register all route blueprints
    register_blueprints(app)

    # Create database tables
    with app.app_context():
        from backend import models  # noqa: F401 — ensures models are loaded
        db.create_all()
        run_schema_updates()
        ensure_farmer_accounts()
        run_auto_backup()

    # Serve the main SPA shell
    @app.route('/')
    def index():
        return render_template('index.html')

    # ── Error pages ──────────────────────────────────────────────
    # API calls get JSON errors; browser navigations get styled HTML
    # pages (templates/errors/) consistent with the app design.
    def _is_api_request():
        return request.path.startswith('/api/')

    @app.errorhandler(404)
    def not_found(e):
        if _is_api_request():
            return {'error': 'Not found'}, 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        if _is_api_request():
            return {'error': 'Access denied'}, 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        if _is_api_request():
            return {'error': 'Internal server error'}, 500
        return render_template('errors/500.html'), 500

    return app


def run_auto_backup():
    """
    Automatic daily backup — creates one snapshot per day (tracked by a marker
    file with today's date). Runs at application startup.
    """
    import os
    import shutil
    from datetime import datetime
    from config import Config

    marker = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'backups', '.last_auto_backup')
    today = datetime.utcnow().strftime('%Y-%m-%d')
    if os.path.exists(marker):
        with open(marker, 'r') as f:
            if f.read().strip() == today:
                return  # already backed up today

    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    try:
        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(
                backup_dir, f'auto_backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.db'))
            with open(marker, 'w') as f:
                f.write(today)
            print(f'[BACKUP] Automatic daily backup completed ({today})')
    except Exception as e:
        print(f'[BACKUP] Auto-backup skipped: {e}')


def run_schema_updates():
    """
    Lightweight SQLite migration: add columns added to existing tables.

    db.create_all() only creates NEW tables; columns added to models that
    already have a table are applied here with ALTER TABLE ADD COLUMN.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    existing = {t: {c['name'] for c in inspector.get_columns(t)} for t in inspector.get_table_names()}

    # (table, column, type) — add if missing
    additions = [
        ('farmers', 'verified_by', 'INTEGER'),
        ('farmers', 'verified_at', 'DATETIME'),
        ('vehicles', 'insurance_no', 'VARCHAR(50)'),
        ('vehicles', 'insurance_expiry', 'DATE'),
        ('vehicles', 'next_service_date', 'DATE'),
        ('vehicles', 'gps_status', 'VARCHAR(20)'),
        ('vehicles', 'fitness_expiry', 'DATE'),
        ('vehicles', 'permit_expiry', 'DATE'),
        ('vehicles', 'mileage', 'FLOAT'),
        ('audit_logs', 'role', 'VARCHAR(30)'),
        ('audit_logs', 'branch_code', 'VARCHAR(20)'),
        ('users', 'must_change_password', 'BOOLEAN'),
        ('users', 'failed_attempts', 'INTEGER'),
        ('users', 'locked_until', 'DATETIME'),
        ('users', 'recovery_email', 'VARCHAR(120)'),
        ('users', 'recovery_mobile', 'VARCHAR(15)'),
        ('users', 'farmer_id', 'INTEGER'),
        ('bank_details', 'verification_status', 'VARCHAR(20)'),
        ('bank_details', 'verified_by', 'INTEGER'),
        ('bank_details', 'verified_at', 'DATETIME'),
        ('inventory_items', 'reserved', 'FLOAT'),
        ('inventory_items', 'max_stock', 'FLOAT'),
        ('suppliers', 'gstin', 'VARCHAR(20)'),
        ('purchase_orders', 'delivery_status', 'VARCHAR(20)'),
        ('purchase_orders', 'grn_no', 'VARCHAR(20)'),
        ('collections', 'idempotency_key', 'VARCHAR(64)'),
    ]
    for table, column, col_type in additions:
        if table in existing and column not in existing[table]:
            try:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                db.session.commit()
                print(f'[MIGRATE] Added column {table}.{column}')
            except Exception:
                db.session.rollback()

    # Unique index on collections.idempotency_key — the final database-level
    # guard against duplicate milk collection submissions. SQLite unique
    # indexes allow multiple NULLs, so legacy rows are unaffected.
    try:
        db.session.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_collections_idempotency_key "
            "ON collections (idempotency_key)"))
        db.session.commit()
    except Exception:
        db.session.rollback()


def ensure_farmer_accounts():
    """
    Create login accounts for farmers that don't have one yet.

    Every Farmer gets a User row (role=FARMER) so they can sign in from the
    farmer portal. Username = farmer code, password = registered mobile
    number (same pattern as branch logins: code / phone). The account status
    mirrors the farmer's status, so unverified/blocked farmers stay locked
    out until Head Office activates them.

    Each new account is flushed individually so a single username conflict
    (e.g. a legacy user already using a farmer code) can't roll back the
    whole batch — the conflicting farmer is skipped with a fallback username.

    Farmers sign in with their EMAIL (identifier) + MOBILE (password), so
    farmers without an email on file get a deterministic one generated
    (<farmer code>@dairy.com) and the login account is kept in sync.
    """
    from sqlalchemy.exc import IntegrityError
    from backend.models import Farmer, User
    from backend.auth import hash_password
    from backend.utils import generate_farmer_email

    created = updated = email_filled = 0
    for farmer in Farmer.query.all():
        # Ensure every farmer has an email (their portal login identifier)
        if not farmer.email:
            farmer.email = generate_farmer_email(farmer.farmer_code)
            email_filled += 1
        user = User.query.filter_by(farmer_id=farmer.id).first()
        if not user:
            # Prefer the farmer code; fall back to farmer_<id> if taken by a
            # non-farmer account (keeps the backfill non-fatal per row).
            username = farmer.farmer_code
            if User.query.filter_by(username=username).first():
                username = f'farmer_{farmer.id}'
            user = User(
                username=username,
                password_hash=hash_password(farmer.mobile or 'farmer@123'),
                name=farmer.name,
                role='FARMER',
                branch_id=farmer.branch_id,
                phone=farmer.mobile,
                email=farmer.email,
                farmer_id=farmer.id,
            )
            db.session.add(user)
            try:
                db.session.flush()
                created += 1
            except IntegrityError:
                db.session.rollback()  # only this row — keep going
                continue
        # Keep the login in sync with the farmer's verification status
        desired = 'ACTIVE' if farmer.status == 'ACTIVE' else 'INACTIVE'
        if user.status != desired:
            user.status = desired
            updated += 1
        # Keep the login email in sync with the farmer record
        if user.email != farmer.email:
            user.email = farmer.email
            updated += 1
    if created or updated or email_filled:
        db.session.commit()
        print(f'[FARMER-LOGIN] Created {created}, synced {updated} farmer login account(s)')


def register_jwt_handlers(jwt_instance):
    """Register JWT error handlers."""

    @jwt_instance.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired. Please login again.'}, 401

    @jwt_instance.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token. Please login again.'}, 401

    @jwt_instance.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Authorization token is missing.'}, 401


def register_blueprints(app):
    """Register all route blueprints with the app (organized by role module)."""
    # ── Admin (Head Office) modules ──
    from backend.modules.admin.branches import branch_bp
    from backend.modules.admin.procurement import procurement_bp
    from backend.modules.admin.inventory import inventory_bp
    from backend.modules.admin.vehicles import vehicle_bp
    from backend.modules.admin.employees import employee_bp
    from backend.modules.admin.audit import audit_bp
    from backend.modules.admin.settings import settings_bp
    from backend.modules.admin.pricing import pricing_bp
    from backend.modules.admin.expenses import expense_bp
    from backend.modules.admin.payments import payment_bp

    # ── Branch (Branch Manager) modules ──
    from backend.modules.branch.collection import collection_bp
    from backend.modules.branch.quality import quality_bp
    from backend.modules.branch.rejections import rejection_bp

    # ── Farmer module ──
    from backend.modules.farmer.farmers import farmer_bp
    from backend.modules.farmer.me import farmer_me_bp

    # ── Shared modules (all roles) ──
    from backend.modules.shared.auth import auth_bp
    from backend.modules.shared.dashboard import dashboard_bp
    from backend.modules.shared.reports import report_bp
    from backend.modules.shared.notifications import notification_bp
    from backend.modules.shared.health import health_bp

    # ── Server-rendered pages (multi-page template system) ──
    from backend.modules.pages import pages_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(branch_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(farmer_me_bp)
    app.register_blueprint(collection_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(pricing_bp)
    app.register_blueprint(quality_bp)
    app.register_blueprint(rejection_bp)
    app.register_blueprint(procurement_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(vehicle_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(pages_bp)
