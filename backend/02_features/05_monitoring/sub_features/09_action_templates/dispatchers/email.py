"""Email dispatcher that routes through Notify SMTP transport."""

from importlib import import_module
from typing import Optional
from . import DeliveryResult

_notify_service = import_module("backend.02_features.06_notify.sub_features.01_transactional.service")


class EmailDispatcher:
    """Dispatches emails via Notify transactional SMTP."""

    async def dispatch(
        self,
        target_address: str,
        rendered_body: str,
        rendered_headers: dict,
        delivery_id: Optional[str] = None,
    ) -> DeliveryResult:
        """
        Dispatch an email via Notify.

        Renders body_template should produce a multipart structure with:
        - {% block subject %} ... {% endblock %}
        - {% block text %} ... {% endblock %}
        - {% block html %} ... {% endblock %} (optional)

        Args:
            target_address: Email address or comma-separated list
            rendered_body: Pre-rendered email body (multipart)
            rendered_headers: Additional email headers
            delivery_id: Optional delivery ID for cross-feature traceability

        Returns:
            DeliveryResult with Notify delivery_id in response_excerpt
        """
        # Parse multipart blocks from rendered_body
        subject = ""
        body_text = ""
        body_html = ""

        # Simple block parser (real impl would use proper Jinja2 block extraction)
        lines = rendered_body.split("\n")
        current_block = None
        for line in lines:
            if "{% block subject %}" in line:
                current_block = "subject"
            elif "{% block text %}" in line:
                current_block = "text"
            elif "{% block html %}" in line:
                current_block = "html"
            elif "{% endblock %}" in line:
                current_block = None
            elif current_block == "subject":
                subject += line + "\n"
            elif current_block == "text":
                body_text += line + "\n"
            elif current_block == "html":
                body_html += line + "\n"

        subject = subject.strip()
        body_text = body_text.strip()
        body_html = body_html.strip() or None

        try:
            # Call Notify service to send transactional email
            notify_delivery_id = await _notify_service.send_transactional_email(
                to_address=target_address,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                headers=rendered_headers,
                metadata={"action_delivery_id": delivery_id} if delivery_id else {},
            )

            return DeliveryResult(
                success=True,
                status_code=200,
                response_excerpt=notify_delivery_id,
            )

        except Exception as e:
            return DeliveryResult(
                success=False,
                error_message=f"Notify error: {str(e)}",
            )
