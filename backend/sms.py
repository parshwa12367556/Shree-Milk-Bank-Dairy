"""
Shree Milk Bank — SMS Delivery
==============================
Reusable SMS sender with a pluggable provider abstraction, mirroring the
mailer's "never break the business transaction" contract.

Configuration is read from the system settings store (Settings → SMS) or
environment variables. Supported provider adapters:

  * `generic-http` — POST JSON to SMS_API_URL with
    {api_key, sender_id, mobile, message}. Maps to any HTTP gateway
    (MSG91 / Twilio / TextLocal-style APIs) via the URL + key fields.

No provider is hardcoded and no API keys are shipped in the codebase — the
admin enters them in Settings, exactly like the SMTP credentials.

Every attempt is recorded in the `notification_logs` table AFTER the caller's
transaction commits (the caller is responsible for calling `send_sms` only
post-commit; the delivery itself never raises).
"""
import json
import logging
import threading
import urllib.error
import urllib.request
import urllib.parse

from backend.modules.admin.settings import _system_settings
from backend.models import NotificationLog
from backend.app import db

logger = logging.getLogger(__name__)

# Deliver in a background thread so gateway latency never stalls the request
# that triggered the SMS. Tests flip this to False for deterministic capture.
SEND_ASYNC = True


def get_sms_config():
    """Return the current SMS settings dict (possibly unconfigured)."""
    return {
        'provider': (_system_settings.get('sms_provider') or '').strip(),
        'sender_id': (_system_settings.get('sms_sender_id') or '').strip(),
        'api_key': (_system_settings.get('sms_api_key') or '').strip(),
        'api_url': (_system_settings.get('sms_api_url') or '').strip(),
        'enabled': bool(_system_settings.get('notification_sms', True)),
    }


def is_sms_configured():
    """True when a provider is configured AND SMS notifications are enabled."""
    cfg = get_sms_config()
    return bool(cfg['enabled'] and cfg['provider'] and cfg['api_url'])


def _http_post_json(url, payload, timeout=10):
    """POST JSON to an HTTP endpoint. Returns (status_code, text)."""
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode('utf-8', 'replace')


def _deliver(cfg, recipient, message):
    """
    Perform the actual gateway call for the configured provider.

    Returns (True, None, response_id) or (False, error, None).
    """
    provider = (cfg['provider'] or '').lower()
    if provider in ('msg91', 'twilio', 'textlocal', 'generic', 'generic-http'):
        # Generic HTTP gateway: POST JSON to the configured URL.
        url = cfg['api_url']
        payload = {
            'api_key': cfg['api_key'],
            'sender_id': cfg['sender_id'],
            'mobile': recipient,
            'message': message,
        }
        try:
            status, text = _http_post_json(url, payload)
            response_id = None
            try:
                parsed = json.loads(text)
                response_id = parsed.get('id') or parsed.get('message_id') \
                    or parsed.get('request_id')
                if isinstance(parsed, dict) and (parsed.get('error')
                                                 or parsed.get('type') == 'error'):
                    return False, text[:300], None
            except (ValueError, TypeError):
                pass
            if 200 <= status < 300:
                return True, None, response_id
            return False, f'HTTP {status}', None
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return False, str(exc), None
    return False, f'Unknown SMS provider: {cfg["provider"] or "not set"}', None


def send_sms(recipient, message, notification_type='GENERAL',
             related_type=None, related_id=None):
    """
    Send an SMS. Never raises; records every attempt in notification_logs.

    Args:
        recipient: mobile number (must come from the database record)
        message: SMS body (OTP values are hashed before this call — the
                 plaintext OTP is deliberately NOT part of any log entry)
        notification_type: e.g. OTP, COLLECTION, PAYMENT, ALERT
        related_type / related_id: link back to the originating record

    Returns:
        (True, None) on success, (False, reason) when skipped/failed.
    """
    if not recipient:
        _log('SMS', recipient or '—', notification_type, 'SKIPPED', None, None,
             'no valid recipient number', related_type, related_id)
        return False, 'no valid recipient number'

    cfg = get_sms_config()
    if not cfg['enabled']:
        _log('SMS', recipient, notification_type, 'SKIPPED', cfg['provider'], None,
             'SMS notifications are disabled', related_type, related_id)
        return False, 'SMS notifications are disabled'
    if not cfg['provider'] or not cfg['api_url']:
        _log('SMS', recipient, notification_type, 'SKIPPED', cfg['provider'], None,
             'SMS provider not configured (Settings → SMS)', related_type, related_id)
        return False, 'SMS provider not configured (Settings → SMS)'

    ok, error, response_id = _deliver(cfg, recipient, message)
    status = 'SENT' if ok else 'FAILED'
    _log('SMS', recipient, notification_type, status, cfg['provider'],
         response_id, error, related_type, related_id)
    if ok:
        logger.info('SMS sent to %s (%s)', recipient, notification_type)
    else:
        logger.warning('SMS to %s failed (%s): %s', recipient, notification_type, error)
    return ok, error


def _log(channel, recipient, notif_type, status, provider, response_id, error,
         related_type, related_id):
    """Persist a delivery attempt (best-effort — logging never raises)."""
    try:
        db.session.add(NotificationLog(
            channel=channel,
            recipient=recipient,
            notification_type=notif_type,
            status=status,
            provider=provider,
            provider_response_id=response_id,
            error=(error or '')[:500],
            related_type=related_type,
            related_id=related_id,
        ))
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — delivery logging must never raise
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning('Could not persist SMS delivery log: %s', exc)


def send_sms_async(recipient, message, notification_type='GENERAL',
                   related_type=None, related_id=None):
    """Fire-and-forget SMS (background thread when SEND_ASYNC is True)."""
    if not SEND_ASYNC:
        return send_sms(recipient, message, notification_type,
                        related_type, related_id)
    threading.Thread(
        target=lambda: send_sms(recipient, message, notification_type,
                                related_type, related_id),
        daemon=True,
    ).start()
    return True, None
