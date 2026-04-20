"""Webhook dispatcher with HMAC-SHA256 signing."""

import hashlib
import hmac
import time
from typing import Optional
import httpx

from . import DeliveryResult


class WebhookDispatcher:
    """Dispatches to HTTP webhooks with optional HMAC-SHA256 signing."""

    SIGNATURE_VERSION = "v1"
    MAX_RESPONSE_SIZE = 4 * 1024  # 4KB

    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    async def dispatch(
        self,
        target_url: str,
        rendered_body: str,
        rendered_headers: dict,
        signing_secret: Optional[str] = None,
        delivery_id: Optional[str] = None,
    ) -> DeliveryResult:
        """
        Dispatch a webhook to target URL.

        Args:
            target_url: HTTP(S) URL to POST to
            rendered_body: Rendered request body
            rendered_headers: Dict of additional headers
            signing_secret: Optional secret for HMAC-SHA256 signing
            delivery_id: Optional delivery ID for tracking header

        Returns:
            DeliveryResult with status and response excerpt
        """
        # Build headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "tennetctl-monitoring/1.0",
        }
        headers.update(rendered_headers or {})

        # Add signature header if secret provided
        if signing_secret:
            timestamp = str(int(time.time()))
            message = f"{timestamp}.{rendered_body}".encode()
            signature = hmac.new(
                signing_secret.encode(),
                message,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Tennet-Signature"] = f"t={timestamp},{self.SIGNATURE_VERSION}={signature}"

        # Add delivery ID header if provided
        if delivery_id:
            headers["X-Tennet-Delivery-Id"] = delivery_id

        # Send POST request
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    target_url,
                    content=rendered_body,
                    headers=headers,
                    follow_redirects=False,
                )

                # Truncate response
                response_text = response.text[: self.MAX_RESPONSE_SIZE]

                # Determine success (2xx) vs retry (5xx, 429) vs permanent failure (4xx non-429)
                if 200 <= response.status_code < 300:
                    return DeliveryResult(
                        success=True,
                        status_code=response.status_code,
                        response_excerpt=response_text,
                    )
                elif response.status_code == 429 or response.status_code >= 500:
                    # Retry these
                    return DeliveryResult(
                        success=False,
                        status_code=response.status_code,
                        response_excerpt=response_text,
                        error_message=f"HTTP {response.status_code} (retryable)",
                    )
                else:
                    # Permanent failure (4xx non-429)
                    return DeliveryResult(
                        success=False,
                        status_code=response.status_code,
                        response_excerpt=response_text,
                        error_message=f"HTTP {response.status_code} (permanent)",
                    )

        except httpx.TimeoutException:
            return DeliveryResult(
                success=False,
                error_message=f"Request timeout after {self.timeout_seconds}s",
            )
        except Exception as e:
            return DeliveryResult(
                success=False,
                error_message=f"Network error: {str(e)}",
            )
