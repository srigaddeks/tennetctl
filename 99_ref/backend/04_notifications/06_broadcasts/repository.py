from __future__ import annotations

import asyncpg
from importlib import import_module

from ..models import BroadcastRecord

SCHEMA = '"03_notifications"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_BROADCAST_COLS = """id, tenant_key, title, body_text, body_html, scope,
                   scope_org_id, scope_workspace_id, notification_type_code,
                   priority_code, severity, is_critical, template_code,
                   static_variables::text,
                   scheduled_at::text, sent_at::text,
                   total_recipients, is_active, is_deleted,
                   created_at::text, updated_at::text, created_by"""


@instrument_class_methods(namespace="broadcasts.repository", logger_name="backend.notifications.broadcasts.repository.instrumentation")
class BroadcastRepository:
    async def list_broadcasts(
        self, connection: asyncpg.Connection, tenant_key: str,
        *, limit: int = 50, offset: int = 0,
    ) -> tuple[list[BroadcastRecord], int]:
        total: int = await connection.fetchval(
            f'SELECT COUNT(*) FROM {SCHEMA}."12_fct_broadcasts" WHERE tenant_key = $1 AND is_deleted = FALSE',
            tenant_key,
        )
        rows = await connection.fetch(
            f"""
            SELECT {_BROADCAST_COLS}
            FROM {SCHEMA}."12_fct_broadcasts"
            WHERE tenant_key = $1 AND is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            tenant_key,
        )
        return [_row_to_broadcast(r) for r in rows], total

    async def list_broadcasts_for_org(
        self, connection: asyncpg.Connection, tenant_key: str, org_id: str
    ) -> list[BroadcastRecord]:
        rows = await connection.fetch(
            f"""
            SELECT {_BROADCAST_COLS}
            FROM {SCHEMA}."12_fct_broadcasts"
            WHERE tenant_key = $1 AND scope_org_id = $2 AND is_deleted = FALSE
            ORDER BY created_at DESC
            """,
            tenant_key, org_id,
        )
        return [_row_to_broadcast(r) for r in rows]

    async def get_broadcast_by_id(
        self, connection: asyncpg.Connection, broadcast_id: str
    ) -> BroadcastRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT {_BROADCAST_COLS}
            FROM {SCHEMA}."12_fct_broadcasts"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            broadcast_id,
        )
        return _row_to_broadcast(row) if row else None

    async def create_broadcast(
        self,
        connection: asyncpg.Connection,
        *,
        broadcast_id: str,
        tenant_key: str,
        title: str,
        body_text: str,
        body_html: str | None,
        scope: str,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
        notification_type_code: str,
        priority_code: str,
        severity: str | None,
        is_critical: bool,
        template_code: str | None,
        static_variables: str | None = None,
        scheduled_at: str | None,
        created_by: str,
        now: datetime,
    ) -> BroadcastRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."12_fct_broadcasts"
                (id, tenant_key, title, body_text, body_html, scope,
                 scope_org_id, scope_workspace_id, notification_type_code,
                 priority_code, severity, is_critical, template_code,
                 static_variables,
                 scheduled_at, sent_at, total_recipients,
                 is_active, is_deleted,
                 created_at, updated_at, created_by)
            VALUES ($1, $2, $3, $4, $5, $6,
                    $7, $8, $9,
                    $10, $11, $12, $13,
                    $14::jsonb,
                    $15, NULL, NULL,
                    TRUE, FALSE,
                    $16, $17, $18)
            RETURNING {_BROADCAST_COLS}
            """,
            broadcast_id,
            tenant_key,
            title,
            body_text,
            body_html,
            scope,
            scope_org_id,
            scope_workspace_id,
            notification_type_code,
            priority_code,
            severity,
            is_critical,
            template_code,
            static_variables or "{}",
            scheduled_at,
            now,
            now,
            created_by,
        )
        return _row_to_broadcast(row)

    async def update_broadcast_sent(
        self,
        connection: asyncpg.Connection,
        broadcast_id: str,
        total_recipients: int,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_fct_broadcasts"
            SET sent_at = $1, total_recipients = $2, updated_at = $3
            WHERE id = $4
            """,
            now,
            total_recipients,
            now,
            broadcast_id,
        )

    async def resolve_global_recipients(
        self, connection: asyncpg.Connection, tenant_key: str
    ) -> list[asyncpg.Record]:
        return await connection.fetch(
            """
            SELECT id AS user_id
            FROM "03_auth_manage"."03_fct_users"
            WHERE tenant_key = $1 AND is_active = TRUE AND is_deleted = FALSE
            """,
            tenant_key,
        )

    async def resolve_org_recipients(
        self, connection: asyncpg.Connection, org_id: str
    ) -> list[asyncpg.Record]:
        return await connection.fetch(
            """
            SELECT user_id
            FROM "03_auth_manage"."31_lnk_org_memberships"
            WHERE org_id = $1 AND is_active = TRUE AND is_deleted = FALSE
            """,
            org_id,
        )

    async def resolve_workspace_recipients(
        self, connection: asyncpg.Connection, workspace_id: str
    ) -> list[asyncpg.Record]:
        return await connection.fetch(
            """
            SELECT user_id
            FROM "03_auth_manage"."36_lnk_workspace_memberships"
            WHERE workspace_id = $1 AND is_active = TRUE AND is_deleted = FALSE
            """,
            workspace_id,
        )

    async def resolve_channels_for_type(
        self, connection: asyncpg.Connection, notification_type_code: str
    ) -> list[asyncpg.Record]:
        """Get all available channels for a notification type from the channel-type matrix."""
        return await connection.fetch(
            f"""
            SELECT ct.channel_code, ct.priority_code
            FROM {SCHEMA}."07_dim_notification_channel_types" ct
            JOIN {SCHEMA}."02_dim_notification_channels" ch ON ch.code = ct.channel_code
            WHERE ct.notification_type_code = $1
              AND ct.is_default = TRUE
              AND ch.is_available = TRUE
            """,
            notification_type_code,
        )

    async def resolve_recipient_email(
        self, connection: asyncpg.Connection, user_id: str
    ) -> str | None:
        """Get recipient email from user properties."""
        return await connection.fetchval(
            """
            SELECT property_value FROM "03_auth_manage"."05_dtl_user_properties"
            WHERE user_id = $1 AND property_key = 'email'
            """,
            user_id,
        )

    async def resolve_recipient_push_endpoint(
        self, connection: asyncpg.Connection, user_id: str
    ) -> str | None:
        """Get recipient's active web push endpoint."""
        return await connection.fetchval(
            f"""
            SELECT endpoint FROM {SCHEMA}."13_fct_web_push_subscriptions"
            WHERE user_id = $1 AND is_active = TRUE
            ORDER BY created_at DESC LIMIT 1
            """,
            user_id,
        )

    async def insert_queue_entries(
        self,
        connection: asyncpg.Connection,
        entries: list[tuple],
    ) -> int:
        """Bulk insert notification queue entries. Each tuple contains:
        (id, tenant_key, user_id, notification_type_code, channel_code,
         status_code, priority_code, broadcast_id, rendered_subject,
         rendered_body, recipient_email, recipient_push_endpoint,
         scheduled_at, created_at, updated_at)
        """
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."20_trx_notification_queue"
                (id, tenant_key, user_id, notification_type_code, channel_code,
                 status_code, priority_code, broadcast_id,
                 rendered_subject, rendered_body,
                 recipient_email, recipient_push_endpoint,
                 scheduled_at, attempt_count, max_attempts,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 0, 3, $14, $15)
            """,
            entries,
        )
        return len(entries)


def _row_to_broadcast(r) -> BroadcastRecord:
    import json as _json
    static_vars_raw = r.get("static_variables")
    if isinstance(static_vars_raw, str):
        static_vars = _json.loads(static_vars_raw) if static_vars_raw else {}
    elif isinstance(static_vars_raw, dict):
        static_vars = static_vars_raw
    else:
        static_vars = {}

    return BroadcastRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        title=r["title"],
        body_text=r["body_text"],
        body_html=r["body_html"],
        scope=r["scope"],
        scope_org_id=r["scope_org_id"],
        scope_workspace_id=r["scope_workspace_id"],
        notification_type_code=r["notification_type_code"],
        priority_code=r["priority_code"],
        severity=r["severity"],
        is_critical=r["is_critical"],
        template_code=r["template_code"],
        static_variables=static_vars,
        scheduled_at=r["scheduled_at"],
        sent_at=r["sent_at"],
        total_recipients=r["total_recipients"],
        is_active=r["is_active"],
        is_deleted=r["is_deleted"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )
