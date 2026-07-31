"""
Smart Dairy ERP — Authentication & Authorization

Provides helper functions for JWT token creation, password hashing,
and role-based access control (RBAC) decorators.
"""
from functools import wraps
import json
from flask import jsonify
from flask_jwt_extended import get_jwt_identity as _get_jwt_identity, verify_jwt_in_request
import bcrypt


def hash_password(password):
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def check_password(password, hashed):
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        hashed: Stored bcrypt hash
    
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def get_identity():
    """
    Get current user identity from JWT, parsing JSON string to dict.
    
    PyJWT 2.x requires the `sub` claim to be a string, so identity
    is stored as a JSON string and parsed back to a dict here.
    
    Returns:
        User identity dict or None
    """
    raw = _get_jwt_identity()
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
    return raw  # fallback for backward compatibility


def role_required(*roles):
    """
    Decorator that restricts access to users with specific roles.
    
    Usage:
        @role_required('SUPER_ADMIN', 'HEAD_OFFICE')
        def protected_route():
            ...
    
    Args:
        *roles: Allowed role names
    
    Returns:
        Decorated function
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            identity = get_identity()
            user_role = identity.get('role')
            
            if user_role not in roles:
                return jsonify({
                    'error': 'Access denied. Insufficient permissions.'
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def can_collect():
    """
    Decorator for collection access.
    Allowed roles: SUPER_ADMIN, BRANCH_MANAGER, OPERATOR
    """
    return role_required('SUPER_ADMIN', 'HEAD_OFFICE', 'BRANCH_MANAGER', 'OPERATOR')


def can_pay():
    """
    Decorator for payment access.
    Allowed roles: SUPER_ADMIN, HEAD_OFFICE, ACCOUNTANT
    """
    return role_required('SUPER_ADMIN', 'HEAD_OFFICE', 'ACCOUNTANT')


def can_manage_rates():
    """
    Decorator for rate management access.
    Allowed roles: SUPER_ADMIN, HEAD_OFFICE
    """
    return role_required('SUPER_ADMIN', 'HEAD_OFFICE')


def is_global_role():
    """
    Decorator for global/head office access.
    Allowed roles: SUPER_ADMIN, HEAD_OFFICE
    """
    return role_required('SUPER_ADMIN', 'HEAD_OFFICE')


def get_current_user():
    """
    Get the current authenticated user's identity.
    
    Returns:
        User identity dict or None
    """
    try:
        return get_identity()
    except Exception:
        return None


def is_branch_accessible(branch_id):
    """
    Check if the current user can access a specific branch.
    Global roles can access all branches; branch-managers/operators
    can only access their assigned branch.
    
    Args:
        branch_id: Branch ID to check
    
    Returns:
        True if accessible, False otherwise
    """
    user = get_current_user()
    if not user:
        return False
    
    # Global roles can access all branches
    if user.get('role') in ('SUPER_ADMIN', 'HEAD_OFFICE'):
        return True
    
    # Branch-specific roles can only access their branch
    return user.get('branchId') == branch_id
