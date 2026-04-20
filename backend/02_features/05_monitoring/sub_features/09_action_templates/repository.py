"""Database access layer for action templates and deliveries."""

from datetime import datetime, timedelta
from typing import Optional
from importlib import import_module
import asyncpg

_core_id = import_module("backend.01_core.id")


class ActionTemplateRepository:
    """Repository for action templates."""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create(
        self,
        org_id: str,
        name: str,
        description: Optional[str],
        kind_id: int,
        target_url: Optional[str],
        target_address: Optional[str],
        body_template: str,
        headers_template: dict,
        signing_secret_vault_ref: Optional[str],
        retry_policy: dict,
        is_active: bool,
    ) -> str:
        """Create a new action template. Returns template ID."""
        template_id = _core_id.uuid7()
        await self.conn.execute(
            """
            INSERT INTO "05_monitoring"."14_fct_monitoring_action_templates"
            (id, org_id, name, description, kind_id, target_url, target_address,
             body_template, headers_template, signing_secret_vault_ref, retry_policy, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
            template_id,
            org_id,
            name,
            description,
            kind_id,
            target_url,
            target_address,
            body_template,
            headers_template,
            signing_secret_vault_ref,
            retry_policy,
            is_active,
        )
        return template_id

    async def get_by_id(self, template_id: str, org_id: str) -> Optional[dict]:
        """Fetch a single template by ID (org-scoped)."""
        return await self.conn.fetchrow(
            """
            SELECT * FROM "05_monitoring".v_monitoring_action_templates
            WHERE id = $1 AND org_id = $2
            """,
            template_id,
            org_id,
        )

    async def list_by_org(
        self, org_id: str, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> list:
        """List templates for an org with optional active filter."""
        query = """
            SELECT * FROM "05_monitoring".v_monitoring_action_templates
            WHERE org_id = $1
        """
        params = [org_id]
        if is_active is not None:
            query += " AND is_active = $2"
            params.append(is_active)
        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(
            len(params) + 2
        )
        params.extend([limit, skip])
        return await self.conn.fetch(query, *params)

    async def update(
        self,
        template_id: str,
        org_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        body_template: Optional[str] = None,
        headers_template: Optional[dict] = None,
        signing_secret_vault_ref: Optional[str] = None,
        retry_policy: Optional[dict] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """Update a template (org-scoped). Returns True if updated."""
        updates = []
        params = [template_id, org_id]
        param_idx = 3

        if name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(name)
            param_idx += 1
        if description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(description)
            param_idx += 1
        if body_template is not None:
            updates.append(f"body_template = ${param_idx}")
            params.append(body_template)
            param_idx += 1
        if headers_template is not None:
            updates.append(f"headers_template = ${param_idx}")
            params.append(headers_template)
            param_idx += 1
        if signing_secret_vault_ref is not None:
            updates.append(f"signing_secret_vault_ref = ${param_idx}")
            params.append(signing_secret_vault_ref)
            param_idx += 1
        if retry_policy is not None:
            updates.append(f"retry_policy = ${param_idx}")
            params.append(retry_policy)
            param_idx += 1
        if is_active is not None:
            updates.append(f"is_active = ${param_idx}")
            params.append(is_active)
            param_idx += 1

        if not updates:
            return False

        updates.append(f"updated_at = CURRENT_TIMESTAMP")
        query = (
            f"UPDATE \"05_monitoring\".\"14_fct_monitoring_action_templates\" "
            f"SET {', '.join(updates)} "
            f"WHERE id = $1 AND org_id = $2"
        )
        result = await self.conn.execute(query, *params)
        return result != "UPDATE 0"

    async def delete(self, template_id: str, org_id: str) -> bool:
        """Soft-delete a template."""
        result = await self.conn.execute(
            """
            UPDATE "05_monitoring"."14_fct_monitoring_action_templates"
            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND org_id = $2 AND deleted_at IS NULL
            """,
            template_id,
            org_id,
        )
        return result != "UPDATE 0"


class ActionDeliveryRepository:
    """Repository for action deliveries."""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create(
        self,
        template_id: str,
        alert_event_id: Optional[str],
        escalation_state_id: Optional[str],
        attempt: int,
        request_payload_hash: str,
    ) -> str:
        """Create a new delivery record. Returns delivery ID."""
        delivery_id = _core_id.uuid7()
        await self.conn.execute(
            """
            INSERT INTO "05_monitoring"."65_evt_monitoring_action_deliveries"
            (id, template_id, alert_event_id, escalation_state_id, attempt, request_payload_hash)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            delivery_id,
            template_id,
            alert_event_id,
            escalation_state_id,
            attempt,
            request_payload_hash,
        )
        return delivery_id

    async def update_delivery(
        self,
        delivery_id: str,
        status_code: Optional[int] = None,
        response_excerpt: Optional[str] = None,
        error_excerpt: Optional[str] = None,
        succeeded: bool = False,
    ) -> None:
        """Update delivery outcome."""
        await self.conn.execute(
            """
            UPDATE "05_monitoring"."65_evt_monitoring_action_deliveries"
            SET status_code = COALESCE($2, status_code),
                response_excerpt = COALESCE($3, response_excerpt),
                error_excerpt = COALESCE($4, error_excerpt),
                completed_at = CURRENT_TIMESTAMP,
                succeeded_at = CASE WHEN $5 THEN CURRENT_TIMESTAMP ELSE succeeded_at END
            WHERE id = $1
            """,
            delivery_id,
            status_code,
            response_excerpt,
            error_excerpt,
            succeeded,
        )

    async def get_by_id(self, delivery_id: str) -> Optional[dict]:
        """Fetch a single delivery by ID."""
        return await self.conn.fetchrow(
            """
            SELECT * FROM "05_monitoring".v_monitoring_action_deliveries
            WHERE id = $1
            """,
            delivery_id,
        )

    async def list_by_template(
        self, template_id: str, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> list:
        """List deliveries for a template with optional status filter."""
        query = """
            SELECT * FROM "05_monitoring".v_monitoring_action_deliveries
            WHERE template_id = $1
        """
        params = [template_id]
        if status:
            query += f" AND status = $2"
            params.append(status)
        query += f" ORDER BY started_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, skip])
        return await self.conn.fetch(query, *params)

    async def find_pending_retries(self, template_id: Optional[str] = None) -> list:
        """Find deliveries pending retry (succeeded IS NULL and completed IS NULL)."""
        if template_id:
            return await self.conn.fetch(
                """
                SELECT * FROM "05_monitoring".v_monitoring_action_deliveries
                WHERE template_id = $1
                  AND succeeded_at IS NULL
                  AND completed_at IS NULL
                ORDER BY started_at ASC
                """,
                template_id,
            )
        return await self.conn.fetch(
            """
            SELECT * FROM "05_monitoring".v_monitoring_action_deliveries
            WHERE succeeded_at IS NULL
              AND completed_at IS NULL
            ORDER BY started_at ASC
            """
        )
