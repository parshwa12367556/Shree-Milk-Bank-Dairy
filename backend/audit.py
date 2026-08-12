"""
Smart Dairy ERP — Audit Logging Helper

Writes AuditLog entries for every important system action.
Call log_audit(...) from any route; the current JWT identity,
request IP and user-agent are captured automatically.    Usage:
        from backend.audit import log_audit
        log_audit('CREATE', 'Farmer', farmer.farmer_code, detail='Farmer registered')
        log_audit('LOGIN_SUCCESS', 'Session', user.login_id, user_id=user.id, username=user.username)
    """
from flask import request
from backend.app import db
from backend.models import AuditLog


def _safe(value, max_len=1000):
    if value is None:
        return None
    return str(value)[:max_len]


def log_audit(action, entity, entity_id=None, detail=None, field_name=None,
              old_value=None, new_value=None, user_id=None, username=None,
              role=None, branch_code=None, force=False):
    """
    Create an audit log entry.

    Args:
        action: LOGIN_SUCCESS, LOGIN_FAILED, ACCOUNT_LOCKED, LOGOUT, CREATE,
                UPDATE, DELETE, APPROVE, PAY, VERIFY, REJECT, ALLOCATE,
                EXPORT, PASSWORD_CHANGED, PASSWORD_RESET_REQUESTED, ...
        entity: e.g. Farmer, Collection, Payment, Branch, InventoryItem ...
        entity_id: record identifier string
        detail: human-readable description
        field_name / old_value / new_value: optional field-level change info
        user_id / username: explicit actor (for login, where no JWT exists yet)
        force: log even without an authenticated user (e.g. failed login)
    """
    from backend.auth import get_identity

    if not user_id:
        try:
            identity = get_identity()
        except Exception:
            identity = None
        if identity:
            user_id = identity.get('uid')
            username = identity.get('username') or identity.get('name')
            role = role or identity.get('role')
            branch_code = branch_code or identity.get('branchCode')

    if not user_id and not force:
        return  # skip unauthenticated actions

    ip = None
    ua = None
    try:
        ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip() \
            or request.remote_addr
        ua = request.headers.get('User-Agent', '')[:255]
    except RuntimeError:
        pass  # outside request context

    log = AuditLog(
        user_id=user_id,
        username=username,
        role=role,
        branch_code=branch_code,
        action=str(action).upper(),
        entity=entity,
        entity_id=_safe(entity_id, 50),
        field_name=field_name,
        old_value=_safe(old_value),
        new_value=_safe(new_value),
        detail=detail,
        ip=ip,
        user_agent=ua,
    )
    db.session.add(log)
