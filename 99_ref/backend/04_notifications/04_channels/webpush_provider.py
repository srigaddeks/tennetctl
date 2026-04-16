from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx
from webpush import WebPush, WebPushSubscription
from webpush.types import WebPushKeys

from .base import ChannelProvider, DeliveryResult

logger = logging.getLogger(__name__)


def _build_wp(private_key_b64: str, public_key_b64: str, subscriber_email: str) -> WebPush:
    """Construct a WebPush instance from base64-encoded PEM private/public keys.

    Both NOTIFICATION_VAPID_PRIVATE_KEY and NOTIFICATION_VAPID_PUBLIC_KEY are
    stored as base64(PEM bytes) as returned by VAPID.generate_keys().
    NOTIFICATION_VAPID_APP_SERVER_KEY is the URL-safe base64 app server key
    used by the frontend (applicationServerKey).
    """
    private_key_pem = base64.b64decode(private_key_b64)
    public_key_pem = base64.b64decode(public_key_b64)
    return WebPush(
        private_key=private_key_pem,
        public_key=public_key_pem,
        subscriber=subscriber_email,
    )


class WebPushProvider(ChannelProvider):
    def __init__(
        self,
        *,
        vapid_private_key: str,
        vapid_public_key: str,
        vapid_claims_email: str,
    ) -> None:
        self._vapid_private_key = vapid_private_key
        self._vapid_public_key = vapid_public_key
        self._vapid_claims_email = vapid_claims_email
        self._wp = _build_wp(vapid_private_key, vapid_public_key, vapid_claims_email)

    async def send(
        self,
        *,
        recipient: str,  # JSON-encoded subscription: {endpoint, keys: {auth, p256dh}}
        subject: str | None,
        body_html: str | None = None,
        body_text: str | None = None,
        body_short: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DeliveryResult:
        try:
            sub_data = json.loads(recipient)
            keys_data = sub_data.get("keys", {})
            subscription = WebPushSubscription(
                endpoint=sub_data["endpoint"],
                keys=WebPushKeys(
                    auth=keys_data["auth"],
                    p256dh=keys_data["p256dh"],
                ),
            )

            payload: dict[str, Any] = {
                "title": subject or "K-Control",
                "body": body_short or body_text or "",
                "icon": (metadata or {}).get("icon", "/icons/icon-192.png"),
                "badge": (metadata or {}).get("badge", "/icons/badge-72.png"),
                "tag": (metadata or {}).get("tag", "kcontrol"),
                "renotify": True,
                "requireInteraction": False,
            }
            url = (metadata or {}).get("url") or (metadata or {}).get("deep_link") or "/"
            payload["data"] = {"url": url}

            message = self._wp.get(
                message=payload,
                subscription=subscription,
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    str(subscription.endpoint),
                    content=message.encrypted,
                    headers=dict(message.headers),
                    timeout=10.0,
                )

            if response.status_code in (200, 201, 202):
                return DeliveryResult(
                    success=True,
                    provider_response=str(response.status_code),
                )
            if response.status_code == 410:
                # Subscription gone — caller should mark it inactive
                return DeliveryResult(
                    success=False,
                    error_code="subscription_gone",
                    error_message=f"Push endpoint returned 410 Gone: {subscription.endpoint}",
                )
            return DeliveryResult(
                success=False,
                error_code=f"http_{response.status_code}",
                error_message=f"Push endpoint returned {response.status_code}: {response.text[:200]}",
            )

        except Exception as exc:
            logger.error("Web push send failed: %s", exc)
            return DeliveryResult(
                success=False,
                error_code="webpush_error",
                error_message=str(exc),
            )

    async def close(self) -> None:
        pass
