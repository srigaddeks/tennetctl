"""Slack incoming webhook dispatcher."""

from typing import Optional
import json
import httpx

from . import DeliveryResult
from .webhook import WebhookDispatcher


class SlackDispatcher:
    """Dispatches to Slack incoming webhooks with severity-based coloring."""

    # Severity -> Slack color mapping
    SEVERITY_COLORS = {
        "info": "#36a64f",  # Green
        "warn": "#ffae42",  # Orange
        "error": "#e01e5a",  # Red
        "critical": "#7a0000",  # Dark red
    }

    def __init__(self, timeout_seconds: int = 10):
        self.webhook_dispatcher = WebhookDispatcher(timeout_seconds=timeout_seconds)

    async def dispatch(
        self,
        target_url: str,
        rendered_body: str,
        rendered_headers: dict,
        severity: str = "info",
        delivery_id: Optional[str] = None,
    ) -> DeliveryResult:
        """
        Dispatch to a Slack incoming webhook.

        Renders rendered_body as Slack blocks JSON. Injects {{slack_color}} based on severity.

        Args:
            target_url: Slack incoming webhook URL
            rendered_body: Pre-rendered Slack blocks JSON
            rendered_headers: Additional headers (usually empty for Slack)
            severity: Alert severity (info/warn/error/critical) for color injection
            delivery_id: Optional delivery ID for tracking

        Returns:
            DeliveryResult with Slack-specific status handling
        """
        # Parse rendered body as JSON to inject color if needed
        try:
            body_obj = json.loads(rendered_body)
        except json.JSONDecodeError:
            return DeliveryResult(
                success=False,
                error_message="Invalid JSON in rendered body",
            )

        # Inject slack_color if not already present
        if "slack_color" not in body_obj and "attachments" in body_obj:
            for attachment in body_obj.get("attachments", []):
                if "color" not in attachment:
                    attachment["color"] = self.SEVERITY_COLORS.get(severity, "#36a64f")

        # Re-serialize
        rendered_body = json.dumps(body_obj)

        # Use webhook dispatcher (Slack doesn't sign webhooks)
        result = await self.webhook_dispatcher.dispatch(
            target_url=target_url,
            rendered_body=rendered_body,
            rendered_headers=rendered_headers,
            signing_secret=None,  # Slack doesn't use signing
            delivery_id=delivery_id,
        )

        # Slack returns 200 with body "ok" on success
        if result.success and result.response_excerpt == "ok":
            return result

        # Slack-specific failure detection
        if result.status_code == 200 and result.response_excerpt != "ok":
            return DeliveryResult(
                success=False,
                status_code=result.status_code,
                response_excerpt=result.response_excerpt,
                error_message=f"Slack returned: {result.response_excerpt}",
            )

        return result
