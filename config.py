"""
Smart Dairy ERP — Application Configuration

Environment variables (see .env.example):
    FLASK_ENV            development | production (default: development)
    SECRET_KEY           Flask session key
    JWT_SECRET_KEY       JWT signing key
    DATABASE_URL         SQLAlchemy database URL (default: local SQLite)
    CORS_ORIGINS         Comma-separated allowed cross-origin hosts (optional;
                         same-origin deployments leave this empty)
    SESSION_COOKIE_SECURE   '1' to send the auth cookie over HTTPS only
    DEV_LOGIN_ENABLED       '1' to enable the dev-only admin/admin123 bypass
                            (development builds only — never in production)
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default='0'):
    return os.getenv(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-shree-milk-bank-secure-change-me-32bytes-min')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-shree-milk-bank-secure-key-32bytes-minimum-length-2026')
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours

    # Database (SQLite by default; set DATABASE_URL for PostgreSQL in production)
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASEDIR, "smart_dairy.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # JWT config
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_IDENTITY_CLAIM = 'sub'
    JWT_ERROR_MESSAGE_KEY = 'error'

    # Cross-origin policy — empty means same-origin only (CORS disabled).
    CORS_ORIGINS = [o.strip() for o in os.getenv('CORS_ORIGINS', '').split(',') if o.strip()]

    # Auth cookie: httpOnly + SameSite always; Secure when configured (HTTPS).
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE')

    # Login protection: per-IP throttle + per-account lockout.
    LOGIN_RATE_LIMIT_MAX = int(os.getenv('LOGIN_RATE_LIMIT_MAX', '20'))
    LOGIN_RATE_LIMIT_WINDOW = int(os.getenv('LOGIN_RATE_LIMIT_WINDOW', '300'))  # 5 minutes
    MAX_FAILED_ATTEMPTS = int(os.getenv('MAX_FAILED_ATTEMPTS', '5'))
    ACCOUNT_LOCKOUT_MINUTES = int(os.getenv('ACCOUNT_LOCKOUT_MINUTES', '30'))

    # Remember Me: longer secure token lifetime when the user opts in.
    REMEMBER_ME_EXPIRES_DAYS = int(os.getenv('REMEMBER_ME_EXPIRES_DAYS', '30'))

    # Password policy (enforced on change/reset — never on login verification).
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', '8'))
    PASSWORD_REQUIRE_UPPER = _env_bool('PASSWORD_REQUIRE_UPPER', '1')
    PASSWORD_REQUIRE_LOWER = _env_bool('PASSWORD_REQUIRE_LOWER', '1')
    PASSWORD_REQUIRE_DIGIT = _env_bool('PASSWORD_REQUIRE_DIGIT', '1')
    PASSWORD_REQUIRE_SPECIAL = _env_bool('PASSWORD_REQUIRE_SPECIAL', '0')

    # Dev-only login bypass (admin/admin123) — always off unless explicitly set.
    DEV_LOGIN_ENABLED = _env_bool('DEV_LOGIN_ENABLED')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Convenience for local demos; disable with DEV_LOGIN_ENABLED=0.
    DEV_LOGIN_ENABLED = _env_bool('DEV_LOGIN_ENABLED', '1')


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DEV_LOGIN_ENABLED = False  # the dev bypass is never available in production
    SESSION_COOKIE_SECURE = True  # fail-safe: HTTPS deployments get a Secure cookie


def validate_production():
    """Fail fast when required production secrets are missing.

    Called by create_app() only when FLASK_ENV=production, so development and
    test runs never trip over missing environment variables.
    """
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        raise RuntimeError('SECRET_KEY must be set in production. See .env.example.')
    if len(secret_key) < 32:
        raise RuntimeError('SECRET_KEY must be at least 32 characters long in production for cryptographic safety.')

    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if not jwt_secret:
        raise RuntimeError('JWT_SECRET_KEY must be set in production. See .env.example.')
    if len(jwt_secret) < 32:
        raise RuntimeError('JWT_SECRET_KEY must be at least 32 characters long in production for HMAC SHA256 safety.')

    if os.getenv('DATABASE_URL', '').startswith('sqlite'):
        import warnings
        warnings.warn(
            'DATABASE_URL points at SQLite — use PostgreSQL for production '
            'concurrency and backup reliability.'
        )


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': DevelopmentConfig,
    'default': DevelopmentConfig,
}
