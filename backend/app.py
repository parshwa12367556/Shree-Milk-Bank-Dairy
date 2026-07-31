"""
Smart Dairy ERP — Flask Application Factory
"""
import os
from flask import Flask, render_template
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

    # Serve the main SPA shell
    @app.route('/')
    def index():
        return render_template('index.html')

    # Catch-all for SPA routes
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404

    return app


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
    """Register all route blueprints with the app."""
    from backend.routes.health_routes import health_bp
    from backend.routes.dashboard_routes import dashboard_bp
    from backend.routes.auth_routes import auth_bp
    from backend.routes.branch_routes import branch_bp
    from backend.routes.farmer_routes import farmer_bp
    from backend.routes.collection_routes import collection_bp
    from backend.routes.payment_routes import payment_bp
    from backend.routes.pricing_routes import pricing_bp
    from backend.routes.quality_routes import quality_bp
    from backend.routes.rejection_routes import rejection_bp
    from backend.routes.procurement_routes import procurement_bp
    from backend.routes.inventory_routes import inventory_bp
    from backend.routes.employee_routes import employee_bp
    from backend.routes.vehicle_routes import vehicle_bp
    from backend.routes.report_routes import report_bp
    from backend.routes.audit_routes import audit_bp
    from backend.routes.settings_routes import settings_bp
    from backend.routes.notification_routes import notification_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(branch_bp)
    app.register_blueprint(farmer_bp)
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
