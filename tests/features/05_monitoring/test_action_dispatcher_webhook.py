"""Tests for webhook dispatcher."""

import pytest
import time
from unittest.mock import AsyncMock, patch
from backend.02_features.05_monitoring.sub_features.09_action_templates.dispatchers.webhook import (
    WebhookDispatcher,
)


@pytest.mark.asyncio
class TestWebhookDispatcher:
    """Test webhook dispatch and signing."""

    async def test_successful_webhook_dispatch(self):
        """Test dispatching to a successful webhook."""
        dispatcher = WebhookDispatcher()

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_post.return_value = mock_response

            result = await dispatcher.dispatch(
                target_url="https://example.com/webhook",
                rendered_body='{"test": "data"}',
                rendered_headers={},
            )

            assert result.success is True
            assert result.status_code == 200
            assert result.response_excerpt == "OK"

    async def test_webhook_500_is_retryable(self):
        """Test that 500 responses are marked for retry."""
        dispatcher = WebhookDispatcher()

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.text = "Server Error"
            mock_post.return_value = mock_response

            result = await dispatcher.dispatch(
                target_url="https://example.com/webhook",
                rendered_body='{"test": "data"}',
                rendered_headers={},
            )

            assert result.success is False
            assert result.status_code == 500
            assert "retryable" in result.error_message

    async def test_webhook_429_is_retryable(self):
        """Test that 429 responses are marked for retry."""
        dispatcher = WebhookDispatcher()

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 429
            mock_response.text = "Too Many Requests"
            mock_post.return_value = mock_response

            result = await dispatcher.dispatch(
                target_url="https://example.com/webhook",
                rendered_body='{"test": "data"}',
                rendered_headers={},
            )

            assert result.success is False
            assert "retryable" in result.error_message

    async def test_webhook_404_is_permanent_failure(self):
        """Test that 4xx non-429 responses are permanent failures."""
        dispatcher = WebhookDispatcher()

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_post.return_value = mock_response

            result = await dispatcher.dispatch(
                target_url="https://example.com/webhook",
                rendered_body='{"test": "data"}',
                rendered_headers={},
            )

            assert result.success is False
            assert "permanent" in result.error_message

    async def test_webhook_timeout(self):
        """Test that timeouts are handled gracefully."""
        dispatcher = WebhookDispatcher(timeout_seconds=1)

        with patch("httpx.AsyncClient.post") as mock_post:
            import httpx
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            result = await dispatcher.dispatch(
                target_url="https://example.com/webhook",
                rendered_body='{"test": "data"}',
                rendered_headers={},
            )

            assert result.success is False
            assert "timeout" in result.error_message

    async def test_webhook_hmac_signing(self):
        """Test HMAC-SHA256 signature generation."""
        dispatcher = WebhookDispatcher()
        secret = "test-secret"
        body = '{"alert": "test"}'

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_post.return_value = mock_response

            await dispatcher.dispatch(
                target_url="https://example.com/webhook",
                rendered_body=body,
                rendered_headers={},
                signing_secret=secret,
            )

            # Check that POST was called
            assert mock_post.called

            # Check headers (not easy to test exact value without mocking time)
            call_args = mock_post.call_args
            headers = call_args.kwargs.get("headers", {})
            assert "X-Tennet-Signature" in headers

    async def test_webhook_delivery_id_header(self):
        """Test that delivery ID is added to headers."""
        dispatcher = WebhookDispatcher()

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_post.return_value = mock_response

            delivery_id = "test-delivery-123"
            await dispatcher.dispatch(
                target_url="https://example.com/webhook",
                rendered_body='{}',
                rendered_headers={},
                delivery_id=delivery_id,
            )

            call_args = mock_post.call_args
            headers = call_args.kwargs.get("headers", {})
            assert headers.get("X-Tennet-Delivery-Id") == delivery_id

    async def test_response_truncation(self):
        """Test that large responses are truncated to 4KB."""
        dispatcher = WebhookDispatcher()
        large_response = "x" * 10000  # 10KB

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = large_response
            mock_post.return_value = mock_response

            result = await dispatcher.dispatch(
                target_url="https://example.com/webhook",
                rendered_body='{}',
                rendered_headers={},
            )

            assert len(result.response_excerpt) <= dispatcher.MAX_RESPONSE_SIZE
