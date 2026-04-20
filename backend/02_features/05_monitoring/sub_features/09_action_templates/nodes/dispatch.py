"""Dispatch node — effect kind, performs delivery with retry orchestration."""

from importlib import import_module
from typing import Optional
import asyncpg

from ..repository import ActionTemplateRepository, ActionDeliveryRepository
from ..dispatchers.webhook import WebhookDispatcher
from ..dispatchers.slack import SlackDispatcher
from ..dispatchers.email import EmailDispatcher

_core_db = import_module("backend.01_core.database")


class DispatchNode:
    """
    Dispatch an action delivery.

    Input schema:
        {
            "delivery_id": str (UUID),
            "template_id": str (UUID),
            "rendered_body": str,
            "rendered_headers": dict,
            "signing_secret": str (optional)
        }

    Output schema:
        {
            "success": bool,
            "status_code": int (optional),
            "error_message": str (optional)
        }

    Transaction: own (acquires connection from pool)
    """

    async def handle(self, input_data: dict, pool: asyncpg.Pool = None) -> dict:
        """Dispatch an action and update delivery record."""
        delivery_id = input_data.get("delivery_id")
        template_id = input_data.get("template_id")
        rendered_body = input_data.get("rendered_body", "")
        rendered_headers = input_data.get("rendered_headers", {})
        signing_secret = input_data.get("signing_secret")

        if not delivery_id or not template_id:
            raise ValueError("delivery_id and template_id are required")

        # Acquire connection for this transaction
        if pool is None:
            pool = _core_db.get_pool()
        conn = await pool.acquire()

        try:
            repo = ActionTemplateRepository(conn)
            delivery_repo = ActionDeliveryRepository(conn)

            # Fetch template
            # (Note: we don't have org_id context here; assume delivery is scoped correctly)
            template_row = await conn.fetchrow(
                'SELECT * FROM "05_monitoring"."14_fct_monitoring_action_templates" WHERE id = $1',
                template_id,
            )
            if not template_row:
                raise ValueError(f"Template {template_id} not found")

            # Fetch kind
            kind_row = await conn.fetchrow(
                'SELECT code FROM "05_monitoring"."03_dim_monitoring_action_kind" WHERE id = $1',
                template_row["kind_id"],
            )
            if not kind_row:
                raise ValueError(f"Kind not found for template")

            kind_code = kind_row["code"]

            # Dispatch based on kind
            result = None
            if kind_code == "webhook":
                dispatcher = WebhookDispatcher()
                result = await dispatcher.dispatch(
                    target_url=template_row["target_url"],
                    rendered_body=rendered_body,
                    rendered_headers=rendered_headers,
                    signing_secret=signing_secret,
                    delivery_id=delivery_id,
                )
            elif kind_code == "slack":
                dispatcher = SlackDispatcher()
                # Extract severity from template labels or variables
                result = await dispatcher.dispatch(
                    target_url=template_row["target_url"],
                    rendered_body=rendered_body,
                    rendered_headers=rendered_headers,
                    severity="info",  # TODO: extract from context
                    delivery_id=delivery_id,
                )
            elif kind_code == "email":
                dispatcher = EmailDispatcher()
                result = await dispatcher.dispatch(
                    target_address=template_row["target_address"],
                    rendered_body=rendered_body,
                    rendered_headers=rendered_headers,
                    delivery_id=delivery_id,
                )
            else:
                raise ValueError(f"Unsupported kind: {kind_code}")

            # Update delivery record
            if result:
                await delivery_repo.update_delivery(
                    delivery_id=delivery_id,
                    status_code=result.status_code,
                    response_excerpt=result.response_excerpt,
                    error_excerpt=result.error_message,
                    succeeded=result.success,
                )

            return {
                "success": result.success if result else False,
                "status_code": result.status_code if result else None,
                "error_message": result.error_message if result else "Unknown error",
            }

        finally:
            await pool.release(conn)
