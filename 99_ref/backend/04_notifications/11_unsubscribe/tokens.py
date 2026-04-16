from __future__ import annotations

"""HMAC-SHA256 one-click unsubscribe tokens for email notifications.

Token format (URL-safe base64):
    HMAC-SHA256(secret, f"{user_id}:{category_code}:{expires_at_unix}")
    encoded as: base64url(user_id) . base64url(category_code) . base64url(expires_at) . base64url(hmac)
"""

import base64
import hashlib
import hmac
import time
from typing import Tuple


def _b64(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def _unb64(s: str) -> str:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (padding % 4)).decode()


def generate_token(
    user_id: str,
    category_code: str,
    secret: str,
    ttl_days: int = 30,
) -> str:
    """Return a signed URL-safe token valid for *ttl_days*."""
    expires_at = str(int(time.time()) + ttl_days * 86400)
    payload = f"{user_id}:{category_code}:{expires_at}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return ".".join([_b64(user_id), _b64(category_code), _b64(expires_at), _b64(sig)])


def verify_token(token: str, secret: str) -> Tuple[str, str]:
    """Verify *token* and return (user_id, category_code).

    Raises ValueError if the token is invalid or expired.
    """
    parts = token.split(".")
    if len(parts) != 4:
        raise ValueError("Malformed unsubscribe token")
    try:
        user_id = _unb64(parts[0])
        category_code = _unb64(parts[1])
        expires_at = int(_unb64(parts[2]))
        sig = _unb64(parts[3])
    except Exception as exc:
        raise ValueError("Malformed unsubscribe token") from exc

    if time.time() > expires_at:
        raise ValueError("Unsubscribe token has expired")

    payload = f"{user_id}:{category_code}:{expires_at}"
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Invalid unsubscribe token signature")

    return user_id, category_code
