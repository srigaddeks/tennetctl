"""Tests for Slack dispatcher."""

import pytest
import json
from unittest.mock import AsyncMock, patch
from backend.02_features.05_monitoring.sub_features.09_action_templates.dispatchers.slack import (
    SlackDispatcher,
)


@pytest.mark.asyncio
class TestSlackDispatcher:
    """Test Slack webhook dispatch."""

    async def test_slack_success_response(self):
        """Test successful Slack webhook delivery."""
        dispatcher = SlackDispatcher()
        body = json.dumps({"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "*Alert*"}}]})

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "ok"
            mock_post.return_value = mock_response

            result = await dispatcher.dispatch(
                target_url="https://hooks.slack.com/services/T/B/X",
                rendered_body=body,
                rendered_headers={},
                severity="critical",
            )

            assert result.success is True

    async def test_slack_failure_response(self):
        """Test Slack webhook failure handling."""
        dispatcher = SlackDispatcher()
        body = json.dumps({"blocks": []})

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "no_text"  # Slack returns "ok" only on success
            mock_post.return_value = mock_response

            result = await dispatcher.dispatch(
                target_url="https://hooks.slack.com/services/T/B/X",
                rendered_body=body,
                rendered_headers={},
            )

            assert result.success is False
            assert "no_text" in result.error_message

    async def test_slack_color_injection_info(self):
        """Test color injection for info severity."""
        dispatcher = SlackDispatcher()

        # Verify color for info severity
        expected_color = dispatcher.SEVERITY_COLORS["info"]
        assert expected_color == "#36a64f"

    async def test_slack_color_injection_critical(self):
        """Test color injection for critical severity."""
        dispatcher = SlackDispatcher()

        expected_color = dispatcher.SEVERITY_COLORS["critical"]
        assert expected_color == "#7a0000"

    async def test_slack_no_signing_header(self):
        """Test that Slack dispatch does not add signing headers."""
        dispatcher = SlackDispatcher()
        body = json.dumps({"blocks": []})

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "ok"
            mock_post.return_value = mock_response

            await dispatcher.dispatch(
                target_url="https://hooks.slack.com/services/T/B/X",
                rendered_body=body,
                rendered_headers={},
            )

            call_args = mock_post.call_args
            headers = call_args.kwargs.get("headers", {})
            # Should NOT have signature header (unlike webhook)
            assert "X-Tennet-Signature" not in headers

    async def test_slack_invalid_json_body(self):
        """Test handling of invalid JSON in rendered body."""
        dispatcher = SlackDispatcher()

        result = await dispatcher.dispatch(
            target_url="https://hooks.slack.com/services/T/B/X",
            rendered_body='not-json',
            rendered_headers={},
        )

        assert result.success is False
        assert "Invalid JSON" in result.error_message
