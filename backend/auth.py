"""
Smart Dairy ERP — Authentication & Authorization

Provides helper functions for JWT token creation, password hashing,
and role-based access control (RBAC) decorators.
"""
from functools import wraps
import json
import re
from flask import jsonify, abort, make_response, current_app
from flask_jwt_extended import get_jwt_identity as _get_jwt_identity, verify_jwt_in_request
import bcrypt

# ── Canonical roles ────────────────────────────────────────────────────────
# The system uses exactly three roles:
#   ADMIN            — full system scope (no branch restriction)
#   BRANCH_OPERATOR  — strictly restricted to their assigned branch
#   FARMER           — strictly restricted to their own farmer record
# Roles not in BRANCH_SCOPED_ROLES are treated as unrestricted/global.
ALL_ROLES = ('ADMIN', 'BRANCH_OPERATOR', 'FARMER')
ADMIN_ROLES = ('ADMIN',)
BRANCH_SCOPED_ROLES = ('BRANCH_OPERATOR',)


def _deny(message):
    """Abort the request with a JSON 403 response (matches API error contract)."""
    abort(make_response(jsonify({'error': message}), 403))


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


def generate_login_id(role, branch_code=None, farmer_code=None, existing_count=0):
    """
    Generate a unique, human-friendly Login ID for a new user account.

    Formats (spec §3):
      ADMIN           → ADMIN001, ADMIN002, ...
      BRANCH_OPERATOR → {BRANCH_CODE}OP{serial:03d}  (BR01OP001, BR02OP002, ...)
      FARMER          → the farmer's farmer code (BR01001)

    The caller supplies the number of already-existing accounts of the same
    kind so the serial is sequential and collision-free.

    Args:
        role: One of ADMIN / BRANCH_OPERATOR / FARMER
        branch_code: Branch code (required for BRANCH_OPERATOR)
        farmer_code: Farmer code (required for FARMER)
        existing_count: Count of existing accounts of the same kind

    Returns:
        Generated login_id string
    """
    if role == 'ADMIN':
        return f'ADMIN{existing_count + 1:03d}'
    if role == 'BRANCH_OPERATOR':
        if not branch_code:
            raise ValueError('branch_code is required for BRANCH_OPERATOR login ID')
        return f'{branch_code}OP{existing_count + 1:03d}'
    if role == 'FARMER':
        if not farmer_code:
            raise ValueError('farmer_code is required for FARMER login ID')
        return farmer_code
    raise ValueError(f'Unknown role: {role}')


def normalize_login_id(value):
    """
    Normalize a login identifier for lookup: trim, collapse inner spaces,
    and uppercase so Login IDs are case-insensitive (br01001 → BR01001).
    """
    return re.sub(r'\s+', '', (value or '')).strip().upper()


def validate_password_policy(password):
    """
    Validate a new password against the configured password policy.

    Configurable via env (see config.py):
      PASSWORD_MIN_LENGTH      (default 8)
      PASSWORD_REQUIRE_UPPER   (default on)
      PASSWORD_REQUIRE_LOWER   (default on)
      PASSWORD_REQUIRE_DIGIT   (default on)
      PASSWORD_REQUIRE_SPECIAL (default off)

    Args:
        password: Candidate plain-text password

    Returns:
        List of human-readable policy violations (empty = valid)
    """
    cfg = current_app.config
    errors = []
    min_len = cfg.get('PASSWORD_MIN_LENGTH', 8)
    if len(password or '') < min_len:
        errors.append(f'Password must be at least {min_len} characters long')
    if cfg.get('PASSWORD_REQUIRE_UPPER', True) and not re.search(r'[A-Z]', password or ''):
        errors.append('Password must contain at least one uppercase letter')
    if cfg.get('PASSWORD_REQUIRE_LOWER', True) and not re.search(r'[a-z]', password or ''):
        errors.append('Password must contain at least one lowercase letter')
    if cfg.get('PASSWORD_REQUIRE_DIGIT', True) and not re.search(r'\d', password or ''):
        errors.append('Password must contain at least one number')
    if cfg.get('PASSWORD_REQUIRE_SPECIAL', False) and not re.search(r'[^A-Za-z0-9]', password or ''):
        errors.append('Password must contain at least one special character')
    return errors


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
        @role_required('ADMIN')
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
    Allowed roles: ADMIN, BRANCH_OPERATOR
    """
    return role_required('ADMIN', 'BRANCH_OPERATOR')


def can_pay():
    """
    Decorator for payment access.
    Allowed roles: ADMIN only — creating/approving/processing farmer
    payments is exclusively an ADMIN responsibility per the architecture spec.
    """
    return role_required('ADMIN')


def can_manage_rates():
    """
    Decorator for rate management access.
    Allowed roles: ADMIN only
    """
    return role_required('ADMIN')


def is_global_role():
    """
    Decorator for global/head-office access.
    Allowed roles: ADMIN
    """
    return role_required('ADMIN')


def reject_farmer():
    """
    Deny requests from FARMER accounts on shared/staff endpoints.

    Farmers have their own self-service endpoints (/api/farmer/me/*) that are
    scoped to their own record. The shared list endpoints (farmers, collections,
    payments, dashboard, ...) must reject them outright — a farmer must never
    be able to enumerate or view other farmers' / the branch's data, even if
    a branch_id filter would narrow the rows.
    """
    user = get_identity()
    if user and user.get('role') == 'FARMER':
        _deny('Access denied. Farmer accounts can only access their own portal.')


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
    if user.get('role') in ADMIN_ROLES:
        return True
    
    # Branch-specific roles can only access their branch
    return user.get('branchId') == branch_id


def get_branch_scope():
    """
    Return the branch_id a branch-scoped user is restricted to, or None.

    This is the single source of truth for branch-level data isolation and
    fails CLOSED: branch-scoped roles (BRANCH_OPERATOR) are always
    forced to their assigned branch, and if no branch is assigned the request
    is denied (403) instead of silently granting unrestricted access.
    Unrestricted roles (ADMIN) return None.

    Returns:
        branch_id (int) to filter by, or None for unrestricted access
    """
    user = get_identity()
    if not user:
        return None
    if user.get('role') not in BRANCH_SCOPED_ROLES:
        return None
    branch_id = user.get('branchId')
    if not branch_id:
        _deny('No branch assigned to this account. Contact Head Office.')
    return branch_id


def scope_query(query, model):
    """
    Apply branch isolation to a SQLAlchemy query for branch-scoped users.

    Global roles pass through unfiltered; branch-scoped users (e.g. Branch
    Managers) are always restricted to their own branch, regardless of any
    client-supplied filters.

    Usage:
        query = scope_query(Collection.query, Collection)
        # Branch Manager ⇒ Collection.branch_id == <their branch_id>

    Args:
        query: SQLAlchemy query object
        model: Model class exposing a `branch_id` column

    Returns:
        Query filtered to the user's branch (unchanged for global roles)
    """
    branch_id = get_branch_scope()
    if branch_id:
        query = query.filter(getattr(model, 'branch_id') == branch_id)
    return query
