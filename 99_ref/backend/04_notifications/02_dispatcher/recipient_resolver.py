from __future__ import annotations

import json
from importlib import import_module

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_audit_module = import_module("backend.01_core.audit")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
AuditEntry = _audit_module.AuditEntry

AUTH_SCHEMA = '"03_auth_manage"'

_LOGGER = get_logger("backend.notifications.recipient_resolver")


@instrument_class_methods(
    namespace="notifications.recipient_resolver",
    logger_name="backend.notifications.recipient_resolver.instrumentation",
)
class RecipientResolver:
    """Resolves notification recipients based on strategy."""

    async def resolve(
        self,
        connection: asyncpg.Connection,
        *,
        strategy: str,
        audit_entry: AuditEntry,
        filter_json: str | None = None,
    ) -> list[str]:
        """Returns list of user_id strings."""
        if strategy == "actor":
            return [audit_entry.actor_id] if audit_entry.actor_id else []
        elif strategy == "entity_owner":
            return await self._resolve_entity_owner(connection, audit_entry)
        elif strategy == "org_members":
            return await self._resolve_org_members(connection, audit_entry)
        elif strategy == "workspace_members":
            return await self._resolve_workspace_members(connection, audit_entry)
        elif strategy == "all_users":
            return await self._resolve_all_users(connection, audit_entry.tenant_key)
        elif strategy == "specific_users":
            return self._resolve_specific_users(filter_json)

        _LOGGER.warning(
            "unknown_recipient_strategy",
            extra={"action": "resolve", "outcome": "skipped", "strategy": strategy},
        )
        return []

    async def _resolve_entity_owner(
        self,
        connection: asyncpg.Connection,
        audit_entry: AuditEntry,
    ) -> list[str]:
        entity_type = audit_entry.entity_type
        entity_id = audit_entry.entity_id

        if entity_type == "org":
            row = await connection.fetchrow(
                f"""
                SELECT user_id FROM {AUTH_SCHEMA}."31_lnk_org_memberships"
                WHERE org_id = $1
                  AND membership_type = 'owner'
                  AND is_active = TRUE AND is_deleted = FALSE
                LIMIT 1
                """,
                entity_id,
            )
            return [row["user_id"]] if row else []

        if entity_type == "workspace":
            row = await connection.fetchrow(
                f"""
                SELECT user_id FROM {AUTH_SCHEMA}."36_lnk_workspace_memberships"
                WHERE workspace_id = $1
                  AND membership_type = 'owner'
                  AND is_active = TRUE AND is_deleted = FALSE
                LIMIT 1
                """,
                entity_id,
            )
            return [row["user_id"]] if row else []

        # Fall back: try org ownership from audit event properties
        org_id = audit_entry.properties.get("org_id")
        if org_id:
            row = await connection.fetchrow(
                f"""
                SELECT user_id FROM {AUTH_SCHEMA}."31_lnk_org_memberships"
                WHERE org_id = $1
                  AND membership_type = 'owner'
                  AND is_active = TRUE AND is_deleted = FALSE
                LIMIT 1
                """,
                org_id,
            )
            return [row["user_id"]] if row else []

        return []

    async def _resolve_org_members(
        self,
        connection: asyncpg.Connection,
        audit_entry: AuditEntry,
    ) -> list[str]:
        org_id = audit_entry.properties.get("org_id") or (
            audit_entry.entity_id if audit_entry.entity_type == "org" else None
        )
        if not org_id:
            _LOGGER.warning(
                "org_members_no_org_id",
                extra={
                    "action": "resolve_org_members",
                    "outcome": "skipped",
                    "audit_entry_id": audit_entry.id,
                },
            )
            return []

        rows = await connection.fetch(
            f"""
            SELECT user_id FROM {AUTH_SCHEMA}."31_lnk_org_memberships"
            WHERE org_id = $1
              AND is_active = TRUE AND is_deleted = FALSE
            """,
            org_id,
        )
        return [r["user_id"] for r in rows]

    async def _resolve_workspace_members(
        self,
        connection: asyncpg.Connection,
        audit_entry: AuditEntry,
    ) -> list[str]:
        workspace_id = audit_entry.properties.get("workspace_id") or (
            audit_entry.entity_id if audit_entry.entity_type == "workspace" else None
        )
        if not workspace_id:
            _LOGGER.warning(
                "workspace_members_no_workspace_id",
                extra={
                    "action": "resolve_workspace_members",
                    "outcome": "skipped",
                    "audit_entry_id": audit_entry.id,
                },
            )
            return []

        rows = await connection.fetch(
            f"""
            SELECT user_id FROM {AUTH_SCHEMA}."36_lnk_workspace_memberships"
            WHERE workspace_id = $1
              AND is_active = TRUE AND is_deleted = FALSE
            """,
            workspace_id,
        )
        return [r["user_id"] for r in rows]

    async def _resolve_all_users(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
    ) -> list[str]:
        rows = await connection.fetch(
            f"""
            SELECT id FROM {AUTH_SCHEMA}."03_fct_users"
            WHERE tenant_key = $1
              AND is_active = TRUE AND is_deleted = FALSE
            """,
            tenant_key,
        )
        return [r["id"] for r in rows]

    @staticmethod
    def _resolve_specific_users(filter_json: str | None) -> list[str]:
        if not filter_json:
            return []
        try:
            data = json.loads(filter_json)
            user_ids = data.get("user_ids", [])
            if isinstance(user_ids, list):
                return [uid for uid in user_ids if isinstance(uid, str)]
        except (json.JSONDecodeError, AttributeError):
            pass
        return []
