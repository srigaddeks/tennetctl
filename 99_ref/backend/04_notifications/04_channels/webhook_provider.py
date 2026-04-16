from __future__ import annotations

"""Webhook channel provider — sends HMAC-signed HTTP POST to user-configured URLs.

Signature: X-KControl-Signature: sha256=<hex>
Payload:
  {
    "notification_type_code": "...",
    "subject": "...",
    "body": "...",
    "metadata": {...}
  }
"""

import hashlib
import hmac
import json
import logging
from typing import Any

import httpx

from .base import ChannelProvider, DeliveryResult

logger = logging.getLogger(__name__)


class WebhookProvider(ChannelProvider):
    """Delivers notifications to a configurable HTTPS endpoint with HMAC auth."""

    def __init__(
        self,
        *,
        webhook_url: str,
        secret: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._webhook_url = webhook_url
        self._secret = secret
        self._timeout = timeout_seconds

    def _sign(self, body: bytes) -> str:
        return "sha256=" + hmac.new(self._secret.encode(), body, hashlib.sha256).hexdigest()

    async def send(
        self,
        *,
        recipient: str,  # unused for webhooks — URL comes from config
        subject: str | None,
        body_html: str | None = None,
        body_text: str | None = None,
        body_short: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DeliveryResult:
        payload: dict[str, Any] = {
            "subject": subject or "",
            "body": body_short or body_text or "",
            "metadata": metadata or {},
        }
        if metadata and metadata.get("notification_type_code"):
            payload["notification_type_code"] = metadata["notification_type_code"]

        raw = json.dumps(payload, separators=(",", ":")).encode()
        sig = self._sign(raw)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._webhook_url,
                    content=raw,
                    headers={
                        "Content-Type": "application/json",
                        "X-KControl-Signature": sig,
                        "User-Agent": "KControl-Webhook/1.0",
                    },
                    timeout=self._timeout,
                )

            if 200 <= response.status_code < 300:
                return DeliveryResult(
                    success=True,
                    provider_response=str(response.status_code),
                )
            if response.status_code == 410:
                return DeliveryResult(
                    success=False,
                    error_code="webhook_gone",
                    error_message=f"Webhook endpoint returned 410 Gone",
                )
            return DeliveryResult(
                success=False,
                error_code=f"http_{response.status_code}",
                error_message=f"Webhook returned {response.status_code}: {response.text[:200]}",
            )
        except Exception as exc:
            logger.error("Webhook send failed: %s", exc)
            return DeliveryResult(
                success=False,
                error_code="webhook_error",
                error_message=str(exc),
            )

    async def close(self) -> None:
        pass
