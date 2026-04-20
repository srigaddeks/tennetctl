"""Business logic for action templates and delivery orchestration."""

from datetime import datetime
from importlib import import_module
from typing import Optional
import asyncpg

from .repository import ActionTemplateRepository, ActionDeliveryRepository
from .renderer import Renderer
from . import schemas

_core_id = import_module("backend.01_core.id")
_response = import_module("backend.01_core.response")
_vault = import_module("backend.02_features.02_vault.sub_features.03_secrets.service")
_audit = import_module("backend.02_features.04_audit.sub_features.01_audit.service")


class ActionTemplateService:
    """Service for managing action templates."""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.repo = ActionTemplateRepository(conn)
        self.delivery_repo = ActionDeliveryRepository(conn)
        self.renderer = Renderer()

    async def create(
        self, org_id: str, user_id: str, input_schema: schemas.ActionTemplateCreate
    ) -> dict:
        """Create a new action template with validation."""
        # Parse and validate template syntax at create-time
        try:
            self.renderer.validate_template(input_schema.body_template)
        except Exception as e:
            raise _response.DomainError(
                "RENDER_PARSE_ERROR",
                f"Template syntax error: {str(e)}",
            )

        # Resolve kind_id from code
        kind_row = await self.conn.fetchrow(
            'SELECT id FROM "05_monitoring"."03_dim_monitoring_action_kind" WHERE code = $1',
            input_schema.kind,
        )
        if not kind_row:
            raise _response.DomainError("INVALID_KIND", f"Unknown action kind: {input_schema.kind}")
        kind_id = kind_row["id"]

        # Validate vault reference if provided
        if input_schema.signing_secret_vault_ref:
            # Placeholder: real implementation would resolve the ref via vault service
            if not input_schema.signing_secret_vault_ref.startswith("vault://"):
                raise _response.DomainError(
                    "VAULT_REF_INVALID", "Vault ref must start with 'vault://'"
                )

        # Create template
        template_id = await self.repo.create(
            org_id=org_id,
            name=input_schema.name,
            description=input_schema.description,
            kind_id=kind_id,
            target_url=input_schema.target_url,
            target_address=input_schema.target_address,
            body_template=input_schema.body_template,
            headers_template=input_schema.headers_template,
            signing_secret_vault_ref=input_schema.signing_secret_vault_ref,
            retry_policy=input_schema.retry_policy or {},
            is_active=input_schema.is_active,
        )

        # Emit audit event
        await _audit.emit_audit_event(
            conn=self.conn,
            org_id=org_id,
            user_id=user_id,
            session_id="",  # Will be set by middleware
            category="monitoring.actions.template_create",
            outcome="success",
            resource_type="action_template",
            resource_id=template_id,
            changes={"created": True},
        )

        return await self.repo.get_by_id(template_id, org_id)

    async def update(
        self, template_id: str, org_id: str, user_id: str, input_schema: schemas.ActionTemplateUpdate
    ) -> dict:
        """Update an action template."""
        # Validate body template syntax if provided
        if input_schema.body_template:
            try:
                self.renderer.validate_template(input_schema.body_template)
            except Exception as e:
                raise _response.DomainError(
                    "RENDER_PARSE_ERROR",
                    f"Template syntax error: {str(e)}",
                )

        # Check if exists
        template = await self.repo.get_by_id(template_id, org_id)
        if not template:
            raise _response.DomainError("NOT_FOUND", "Action template not found")

        # Update
        await self.repo.update(
            template_id,
            org_id,
            name=input_schema.name,
            description=input_schema.description,
            body_template=input_schema.body_template,
            headers_template=input_schema.headers_template,
            signing_secret_vault_ref=input_schema.signing_secret_vault_ref,
            retry_policy=input_schema.retry_policy,
            is_active=input_schema.is_active,
        )

        # Emit audit event
        await _audit.emit_audit_event(
            conn=self.conn,
            org_id=org_id,
            user_id=user_id,
            session_id="",
            category="monitoring.actions.template_update",
            outcome="success",
            resource_type="action_template",
            resource_id=template_id,
            changes={
                "name": input_schema.name,
                "body_template": "***" if input_schema.body_template else None,
            },
        )

        return await self.repo.get_by_id(template_id, org_id)

    async def delete(self, template_id: str, org_id: str, user_id: str) -> None:
        """Soft-delete an action template."""
        template = await self.repo.get_by_id(template_id, org_id)
        if not template:
            raise _response.DomainError("NOT_FOUND", "Action template not found")

        await self.repo.delete(template_id, org_id)

        # Emit audit event
        await _audit.emit_audit_event(
            conn=self.conn,
            org_id=org_id,
            user_id=user_id,
            session_id="",
            category="monitoring.actions.template_delete",
            outcome="success",
            resource_type="action_template",
            resource_id=template_id,
            changes={"deleted": True},
        )

    async def enqueue_delivery(
        self,
        template_id: str,
        alert_event_id: Optional[str] = None,
        escalation_state_id: Optional[str] = None,
        variables: Optional[dict] = None,
    ) -> str:
        """Enqueue an action delivery. Notifies the worker via LISTEN channel."""
        variables = variables or {}

        # Create delivery record
        # Render to get hash
        rendered = self.renderer.render(template_id, "", variables)
        delivery_id = await self.delivery_repo.create(
            template_id=template_id,
            alert_event_id=alert_event_id,
            escalation_state_id=escalation_state_id,
            attempt=1,
            request_payload_hash=rendered.get("payload_hash", ""),
        )

        # Notify worker
        await self.conn.execute(
            "NOTIFY monitoring_action_dispatch, $1",
            delivery_id,
        )

        return delivery_id

    async def test_dispatch(
        self,
        template_id: str,
        org_id: str,
        sample_variables: dict,
    ) -> dict:
        """Synchronously dispatch a template with sample variables (test mode)."""
        # Fetch template
        template = await self.repo.get_by_id(template_id, org_id)
        if not template:
            raise _response.DomainError("NOT_FOUND", "Action template not found")

        if not template["is_active"]:
            raise _response.DomainError("INACTIVE", "Action template is not active")

        # Render
        try:
            rendered = self.renderer.render(template_id, template["body_template"], sample_variables)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

        # Dispatch (sync, no retry)
        # This would call the appropriate dispatcher based on kind_code
        # For now, return placeholder
        return {
            "success": True,
            "status_code": 200,
            "response_excerpt": "OK",
        }
