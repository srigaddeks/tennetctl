from __future__ import annotations

from datetime import datetime
from importlib import import_module
from uuid import uuid4

import asyncpg

from .models import CampaignRecord

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_SELECT_COLS = """
    id, tenant_key, code, name, description, campaign_type, status,
    default_scope, default_role, default_org_id::text, default_workspace_id::text,
    default_expires_hours, starts_at, ends_at,
    invite_count, accepted_count, notes,
    created_at, updated_at, created_by::text
"""


@instrument_class_methods(namespace="invite_campaigns.repository", logger_name="backend.invite_campaigns.repository.instrumentation")
class CampaignRepository:

    async def create_campaign(
        self,
        connection: asyncpg.Connection,
        *,
        code: str,
        name: str,
        description: str,
        campaign_type: str,
        default_scope: str,
        default_role: str | None,
        default_org_id: str | None,
        default_workspace_id: str | None,
        default_expires_hours: int,
        starts_at: datetime | None,
        ends_at: datetime | None,
        notes: str | None,
        tenant_key: str,
        created_by: str,
        now: datetime,
    ) -> CampaignRecord:
        campaign_id = str(uuid4())
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."45_fct_invite_campaigns" (
                id, tenant_key, code, name, description, campaign_type, status,
                default_scope, default_role, default_org_id, default_workspace_id,
                default_expires_hours, starts_at, ends_at,
                invite_count, accepted_count, notes,
                created_at, updated_at, created_by, updated_by
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, 'active',
                $7, $8, $9::uuid, $10::uuid,
                $11, $12, $13,
                0, 0, $14,
                $15, $16, $17::uuid, $18::uuid
            )
            RETURNING {_SELECT_COLS}
            """,
            campaign_id, tenant_key, code, name, description, campaign_type,
            default_scope, default_role, default_org_id, default_workspace_id,
            default_expires_hours, starts_at, ends_at,
            notes,
            now, now, created_by, created_by,
        )
        return _row_to_campaign(row)  # type: ignore[arg-type]

    async def get_by_id(
        self, connection: asyncpg.Connection, campaign_id: str
    ) -> CampaignRecord | None:
        row = await connection.fetchrow(
            f"SELECT {_SELECT_COLS} FROM {SCHEMA}.\"45_fct_invite_campaigns\" WHERE id = $1",
            campaign_id,
        )
        return _row_to_campaign(row) if row else None

    async def get_by_code(
        self, connection: asyncpg.Connection, code: str, tenant_key: str
    ) -> CampaignRecord | None:
        row = await connection.fetchrow(
            f"SELECT {_SELECT_COLS} FROM {SCHEMA}.\"45_fct_invite_campaigns\" WHERE code = $1 AND tenant_key = $2",
            code, tenant_key,
        )
        return _row_to_campaign(row) if row else None

    async def list_campaigns(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        status: str | None = None,
        campaign_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CampaignRecord], int]:
        conditions = ["tenant_key = $1"]
        params: list[object] = [tenant_key]
        idx = 2
        if status:
            conditions.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        if campaign_type:
            conditions.append(f"campaign_type = ${idx}")
            params.append(campaign_type)
            idx += 1

        where = " AND ".join(conditions)
        rows = await connection.fetch(
            f"""
            SELECT {_SELECT_COLS}
            FROM {SCHEMA}."45_fct_invite_campaigns"
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params, limit, offset,
        )
        total_row = await connection.fetchrow(
            f'SELECT COUNT(*) FROM {SCHEMA}."45_fct_invite_campaigns" WHERE {where}',
            *params,
        )
        return [_row_to_campaign(r) for r in rows], int(total_row["count"])

    async def update_campaign(
        self,
        connection: asyncpg.Connection,
        *,
        campaign_id: str,
        name: str | None,
        description: str | None,
        status: str | None,
        default_role: str | None,
        default_expires_hours: int | None,
        starts_at: datetime | None,
        ends_at: datetime | None,
        notes: str | None,
        updated_by: str,
        now: datetime,
    ) -> CampaignRecord | None:
        sets = ["updated_at = $1", "updated_by = $2::uuid"]
        params: list[object] = [now, updated_by]
        idx = 3

        def _add(col: str, val: object, cast: str = "") -> None:
            nonlocal idx
            sets.append(f"{col} = ${idx}{cast}")
            params.append(val)
            idx += 1

        if name is not None:       _add("name", name)
        if description is not None: _add("description", description)
        if status is not None:     _add("status", status)
        if default_role is not None: _add("default_role", default_role)
        if default_expires_hours is not None: _add("default_expires_hours", default_expires_hours)
        if starts_at is not None:  _add("starts_at", starts_at)
        if ends_at is not None:    _add("ends_at", ends_at)
        if notes is not None:      _add("notes", notes)

        params.append(campaign_id)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."45_fct_invite_campaigns"
            SET {", ".join(sets)}
            WHERE id = ${idx}
            RETURNING {_SELECT_COLS}
            """,
            *params,
        )
        return _row_to_campaign(row) if row else None

    async def increment_invite_count(
        self, connection: asyncpg.Connection, campaign_id: str, delta: int = 1
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."45_fct_invite_campaigns"
            SET invite_count = invite_count + $1, updated_at = NOW()
            WHERE id = $2
            """,
            delta, campaign_id,
        )

    async def increment_accepted_count(
        self, connection: asyncpg.Connection, campaign_id: str, delta: int = 1
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."45_fct_invite_campaigns"
            SET accepted_count = accepted_count + $1, updated_at = NOW()
            WHERE id = $2
            """,
            delta, campaign_id,
        )


def _row_to_campaign(row: asyncpg.Record) -> CampaignRecord:
    return CampaignRecord(
        id=str(row["id"]),
        tenant_key=row["tenant_key"],
        code=row["code"],
        name=row["name"],
        description=row["description"],
        campaign_type=row["campaign_type"],
        status=row["status"],
        default_scope=row["default_scope"],
        default_role=row["default_role"],
        default_org_id=row["default_org_id"],
        default_workspace_id=row["default_workspace_id"],
        default_expires_hours=row["default_expires_hours"],
        starts_at=row["starts_at"],
        ends_at=row["ends_at"],
        invite_count=row["invite_count"],
        accepted_count=row["accepted_count"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        created_by=row["created_by"],
    )
