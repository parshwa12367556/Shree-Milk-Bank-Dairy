"""
Smart Dairy ERP — Application Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'sd-erp-secret-key-change-in-production-2026')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'sd-jwt-secret-change-in-production-2026')
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours

    # SQLite database
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASEDIR, "smart_dairy.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT config
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_IDENTITY_CLAIM = 'sub'
    JWT_ERROR_MESSAGE_KEY = 'error'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
