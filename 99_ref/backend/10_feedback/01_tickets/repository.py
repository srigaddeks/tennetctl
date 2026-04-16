"""SQL repository for the feedback & support ticket domain."""
from __future__ import annotations

import json
from importlib import import_module

import asyncpg

from .models import (
    TicketDetailRecord,
    TicketEventRecord,
    TicketPriorityDimRecord,
    TicketRecord,
    TicketStatusDimRecord,
    TicketTypeDimRecord,
)

FB_SCHEMA = '"10_feedback"'
AUTH_SCHEMA = '"03_auth_manage"'

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(
    namespace="feedback.repository",
    logger_name="backend.feedback.repository.instrumentation",
)
class TicketRepository:

    # ── Dimensions ─────────────────────────────────────────────────────────────

    async def list_ticket_types(self, connection: asyncpg.Connection) -> list[TicketTypeDimRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, icon_name, sort_order, is_active '
            f'FROM {FB_SCHEMA}."01_dim_ticket_types" WHERE is_active = TRUE ORDER BY sort_order'
        )
        return [TicketTypeDimRecord(**dict(r)) for r in rows]

    async def list_ticket_statuses(self, connection: asyncpg.Connection) -> list[TicketStatusDimRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, is_terminal, sort_order '
            f'FROM {FB_SCHEMA}."02_dim_ticket_statuses" ORDER BY sort_order'
        )
        return [TicketStatusDimRecord(**dict(r)) for r in rows]

    async def list_ticket_priorities(self, connection: asyncpg.Connection) -> list[TicketPriorityDimRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, numeric_level, sort_order '
            f'FROM {FB_SCHEMA}."03_dim_ticket_priorities" ORDER BY sort_order'
        )
        return [TicketPriorityDimRecord(**dict(r)) for r in rows]

    async def ticket_type_exists(self, connection: asyncpg.Connection, code: str) -> bool:
        row = await connection.fetchrow(
            f'SELECT 1 FROM {FB_SCHEMA}."01_dim_ticket_types" WHERE code = $1 AND is_active = TRUE',
            code,
        )
        return row is not None

    async def priority_exists(self, connection: asyncpg.Connection, code: str) -> bool:
        row = await connection.fetchrow(
            f'SELECT 1 FROM {FB_SCHEMA}."03_dim_ticket_priorities" WHERE code = $1',
            code,
        )
        return row is not None

    # ── Ticket reads ──────────────────────────────────────────────────────────

    async def get_ticket_raw(
        self, connection: asyncpg.Connection, ticket_id: str
    ) -> TicketRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                id::text, tenant_key, submitted_by::text,
                ticket_type_code, status_code, priority_code,
                org_id::text, workspace_id::text,
                is_deleted, deleted_at::text, deleted_by::text,
                created_at::text, updated_at::text, created_by::text, updated_by::text,
                resolved_at::text, resolved_by::text
            FROM {FB_SCHEMA}."10_fct_tickets"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            ticket_id,
        )
        if not row:
            return None
        return TicketRecord(
            id=row["id"],
            tenant_key=row["tenant_key"],
            submitted_by=row["submitted_by"],
            ticket_type_code=row["ticket_type_code"],
            status_code=row["status_code"],
            priority_code=row["priority_code"],
            org_id=row["org_id"],
            workspace_id=row["workspace_id"],
            is_deleted=row["is_deleted"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolved_at=row["resolved_at"],
            resolved_by=row["resolved_by"],
        )

    async def get_ticket_detail(
        self, connection: asyncpg.Connection, ticket_id: str
    ) -> TicketDetailRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                t.id::text,
                t.tenant_key,
                t.submitted_by::text,
                t.ticket_type_code,
                t.status_code,
                t.priority_code,
                t.org_id::text,
                t.workspace_id::text,
                t.is_deleted,
                t.created_at::text,
                t.updated_at::text,
                t.resolved_at::text,
                t.resolved_by::text,
                -- EAV properties
                MAX(CASE WHEN p.property_key = 'title'               THEN p.property_value END) AS title,
                MAX(CASE WHEN p.property_key = 'description'         THEN p.property_value END) AS description,
                MAX(CASE WHEN p.property_key = 'context_url'         THEN p.property_value END) AS context_url,
                MAX(CASE WHEN p.property_key = 'browser_info'        THEN p.property_value END) AS browser_info,
                MAX(CASE WHEN p.property_key = 'steps_to_reproduce'  THEN p.property_value END) AS steps_to_reproduce,
                MAX(CASE WHEN p.property_key = 'expected_behavior'   THEN p.property_value END) AS expected_behavior,
                MAX(CASE WHEN p.property_key = 'actual_behavior'     THEN p.property_value END) AS actual_behavior,
                MAX(CASE WHEN p.property_key = 'version_info'        THEN p.property_value END) AS version_info,
                MAX(CASE WHEN p.property_key = 'admin_note'          THEN p.property_value END) AS admin_note,
                -- submitter info
                subm_email.property_value    AS submitter_email,
                subm_name.property_value     AS submitter_display_name,
                -- assignments as JSON
                COALESCE(
                    (SELECT json_agg(json_build_object(
                        'assigned_to', a.assigned_to::text,
                        'assigned_by', a.assigned_by::text,
                        'assigned_at', a.assigned_at::text
                    )) FROM {FB_SCHEMA}."20_lnk_ticket_assignments" a
                     WHERE a.ticket_id = t.id AND a.is_active = TRUE),
                    '[]'::json
                ) AS active_assignments
            FROM {FB_SCHEMA}."10_fct_tickets" t
            LEFT JOIN {FB_SCHEMA}."15_dtl_ticket_properties" p ON p.ticket_id = t.id
            LEFT JOIN {AUTH_SCHEMA}."05_dtl_user_properties" subm_email
                ON subm_email.user_id = t.submitted_by AND subm_email.property_key = 'email'
            LEFT JOIN {AUTH_SCHEMA}."05_dtl_user_properties" subm_name
                ON subm_name.user_id = t.submitted_by AND subm_name.property_key = 'display_name'
            WHERE t.id = $1::uuid AND t.is_deleted = FALSE
            GROUP BY t.id, subm_email.property_value, subm_name.property_value
            """,
            ticket_id,
        )
        if not row:
            return None
        return _row_to_ticket_detail(row)

    async def count_tickets(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str | None = None,
        submitted_by: str | None = None,
        status_code: str | None = None,
        ticket_type_code: str | None = None,
        priority_code: str | None = None,
    ) -> int:
        conditions = ["t.is_deleted = FALSE"]
        params: list = []
        idx = 1

        if tenant_key:
            conditions.append(f"t.tenant_key = ${idx}")
            params.append(tenant_key)
            idx += 1
        if submitted_by:
            conditions.append(f"t.submitted_by = ${idx}::uuid")
            params.append(submitted_by)
            idx += 1
        if status_code:
            conditions.append(f"t.status_code = ${idx}")
            params.append(status_code)
            idx += 1
        if ticket_type_code:
            conditions.append(f"t.ticket_type_code = ${idx}")
            params.append(ticket_type_code)
            idx += 1
        if priority_code:
            conditions.append(f"t.priority_code = ${idx}")
            params.append(priority_code)
            idx += 1

        where = " AND ".join(conditions)
        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {FB_SCHEMA}."10_fct_tickets" t WHERE {where}',
            *params,
        )
        return row["total"] if row else 0

    async def list_tickets(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str | None = None,
        submitted_by: str | None = None,
        status_code: str | None = None,
        ticket_type_code: str | None = None,
        priority_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TicketDetailRecord]:
        conditions = ["t.is_deleted = FALSE"]
        params: list = []
        idx = 1

        if tenant_key:
            conditions.append(f"t.tenant_key = ${idx}")
            params.append(tenant_key)
            idx += 1
        if submitted_by:
            conditions.append(f"t.submitted_by = ${idx}::uuid")
            params.append(submitted_by)
            idx += 1
        if status_code:
            conditions.append(f"t.status_code = ${idx}")
            params.append(status_code)
            idx += 1
        if ticket_type_code:
            conditions.append(f"t.ticket_type_code = ${idx}")
            params.append(ticket_type_code)
            idx += 1
        if priority_code:
            conditions.append(f"t.priority_code = ${idx}")
            params.append(priority_code)
            idx += 1

        where = " AND ".join(conditions)
        rows = await connection.fetch(
            f"""
            SELECT
                t.id::text,
                t.tenant_key,
                t.submitted_by::text,
                t.ticket_type_code,
                t.status_code,
                t.priority_code,
                t.org_id::text,
                t.workspace_id::text,
                t.is_deleted,
                t.created_at::text,
                t.updated_at::text,
                t.resolved_at::text,
                t.resolved_by::text,
                MAX(CASE WHEN p.property_key = 'title'               THEN p.property_value END) AS title,
                MAX(CASE WHEN p.property_key = 'description'         THEN p.property_value END) AS description,
                MAX(CASE WHEN p.property_key = 'context_url'         THEN p.property_value END) AS context_url,
                MAX(CASE WHEN p.property_key = 'browser_info'        THEN p.property_value END) AS browser_info,
                MAX(CASE WHEN p.property_key = 'steps_to_reproduce'  THEN p.property_value END) AS steps_to_reproduce,
                MAX(CASE WHEN p.property_key = 'expected_behavior'   THEN p.property_value END) AS expected_behavior,
                MAX(CASE WHEN p.property_key = 'actual_behavior'     THEN p.property_value END) AS actual_behavior,
                MAX(CASE WHEN p.property_key = 'version_info'        THEN p.property_value END) AS version_info,
                MAX(CASE WHEN p.property_key = 'admin_note'          THEN p.property_value END) AS admin_note,
                subm_email.property_value    AS submitter_email,
                subm_name.property_value     AS submitter_display_name,
                COALESCE(
                    (SELECT json_agg(json_build_object(
                        'assigned_to', a.assigned_to::text,
                        'assigned_by', a.assigned_by::text,
                        'assigned_at', a.assigned_at::text
                    )) FROM {FB_SCHEMA}."20_lnk_ticket_assignments" a
                     WHERE a.ticket_id = t.id AND a.is_active = TRUE),
                    '[]'::json
                ) AS active_assignments
            FROM {FB_SCHEMA}."10_fct_tickets" t
            LEFT JOIN {FB_SCHEMA}."15_dtl_ticket_properties" p ON p.ticket_id = t.id
            LEFT JOIN {AUTH_SCHEMA}."05_dtl_user_properties" subm_email
                ON subm_email.user_id = t.submitted_by AND subm_email.property_key = 'email'
            LEFT JOIN {AUTH_SCHEMA}."05_dtl_user_properties" subm_name
                ON subm_name.user_id = t.submitted_by AND subm_name.property_key = 'display_name'
            WHERE {where}
            GROUP BY t.id, subm_email.property_value, subm_name.property_value
            ORDER BY t.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )
        return [_row_to_ticket_detail(r) for r in rows]

    # ── Ticket writes ─────────────────────────────────────────────────────────

    async def create_ticket(
        self,
        connection: asyncpg.Connection,
        *,
        ticket_id: str,
        tenant_key: str,
        submitted_by: str,
        ticket_type_code: str,
        status_code: str,
        priority_code: str,
        org_id: str | None,
        workspace_id: str | None,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {FB_SCHEMA}."10_fct_tickets" (
                id, tenant_key, submitted_by, ticket_type_code,
                status_code, priority_code, org_id, workspace_id,
                created_at, updated_at, created_by, updated_by
            ) VALUES (
                $1::uuid, $2, $3::uuid, $4,
                $5, $6,
                $7::uuid, $8::uuid,
                $9, $10, $11::uuid, $12::uuid
            )
            """,
            ticket_id, tenant_key, submitted_by, ticket_type_code,
            status_code, priority_code,
            org_id, workspace_id,
            now, now, submitted_by, submitted_by,
        )

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        *,
        ticket_id: str,
        properties: dict[str, str],
        is_internal: bool,
        actor_id: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (ticket_id, key, value, is_internal, now, now, actor_id, actor_id)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
                INSERT INTO {FB_SCHEMA}."15_dtl_ticket_properties"
                    (id, ticket_id, property_key, property_value, is_internal,
                     created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1::uuid, $2, $3, $4, $5, $6, $7::uuid, $8::uuid)
                ON CONFLICT (ticket_id, property_key)
                DO UPDATE SET property_value = EXCLUDED.property_value,
                              updated_at = EXCLUDED.updated_at,
                              updated_by = EXCLUDED.updated_by
                """,
            rows,
        )

    async def update_ticket_status(
        self,
        connection: asyncpg.Connection,
        ticket_id: str,
        *,
        status_code: str,
        resolved_at: object | None,
        resolved_by: str | None,
        updated_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {FB_SCHEMA}."10_fct_tickets"
            SET status_code = $1, resolved_at = $2, resolved_by = $3::uuid,
                updated_at = $4, updated_by = $5::uuid
            WHERE id = $6::uuid AND is_deleted = FALSE
            """,
            status_code, resolved_at, resolved_by, now, updated_by, ticket_id,
        )
        return result != "UPDATE 0"

    async def update_ticket_priority(
        self,
        connection: asyncpg.Connection,
        ticket_id: str,
        *,
        priority_code: str,
        updated_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {FB_SCHEMA}."10_fct_tickets"
            SET priority_code = $1, updated_at = $2, updated_by = $3::uuid
            WHERE id = $4::uuid AND is_deleted = FALSE
            """,
            priority_code, now, updated_by, ticket_id,
        )
        return result != "UPDATE 0"

    async def soft_delete_ticket(
        self,
        connection: asyncpg.Connection,
        ticket_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {FB_SCHEMA}."10_fct_tickets"
            SET is_deleted = TRUE, deleted_at = $1, deleted_by = $2::uuid, updated_at = $3
            WHERE id = $4::uuid AND is_deleted = FALSE
            """,
            now, deleted_by, now, ticket_id,
        )
        return result != "UPDATE 0"

    # ── Assignment writes ─────────────────────────────────────────────────────

    async def create_assignment(
        self,
        connection: asyncpg.Connection,
        *,
        ticket_id: str,
        assigned_to: str,
        assigned_by: str,
        note: str | None,
        now: object,
    ) -> None:
        # Deactivate existing active assignment for this user if any
        await connection.execute(
            f"""
            UPDATE {FB_SCHEMA}."20_lnk_ticket_assignments"
            SET is_active = FALSE, unassigned_at = $1, unassigned_by = $2::uuid
            WHERE ticket_id = $3::uuid AND assigned_to = $4::uuid AND is_active = TRUE
            """,
            now, assigned_by, ticket_id, assigned_to,
        )
        await connection.execute(
            f"""
            INSERT INTO {FB_SCHEMA}."20_lnk_ticket_assignments"
                (id, ticket_id, assigned_to, assigned_by, is_active, assigned_at, note)
            VALUES (gen_random_uuid(), $1::uuid, $2::uuid, $3::uuid, TRUE, $4, $5)
            """,
            ticket_id, assigned_to, assigned_by, now, note,
        )

    async def deactivate_assignment(
        self,
        connection: asyncpg.Connection,
        *,
        ticket_id: str,
        assigned_to: str,
        unassigned_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {FB_SCHEMA}."20_lnk_ticket_assignments"
            SET is_active = FALSE, unassigned_at = $1, unassigned_by = $2::uuid
            WHERE ticket_id = $3::uuid AND assigned_to = $4::uuid AND is_active = TRUE
            """,
            now, unassigned_by, ticket_id, assigned_to,
        )
        return result != "UPDATE 0"

    # ── Audit events ──────────────────────────────────────────────────────────

    async def write_event(
        self,
        connection: asyncpg.Connection,
        *,
        event_id: str,
        ticket_id: str,
        tenant_key: str,
        event_type: str,
        actor_id: str,
        old_value: str | None,
        new_value: str | None,
        note: str | None,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {FB_SCHEMA}."30_aud_ticket_events"
                (id, ticket_id, tenant_key, event_type, actor_id,
                 occurred_at, old_value, new_value, note)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $6, $7, $8, $9)
            """,
            event_id, ticket_id, tenant_key, event_type, actor_id,
            now, old_value, new_value, note,
        )

    async def list_events(
        self,
        connection: asyncpg.Connection,
        ticket_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[TicketEventRecord], int]:
        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {FB_SCHEMA}."30_aud_ticket_events" WHERE ticket_id = $1::uuid',
            ticket_id,
        )
        total = count_row["total"] if count_row else 0
        rows = await connection.fetch(
            f"""
            SELECT id::text, ticket_id::text, tenant_key, event_type,
                   actor_id::text, occurred_at::text, old_value, new_value, note
            FROM {FB_SCHEMA}."30_aud_ticket_events"
            WHERE ticket_id = $1::uuid
            ORDER BY occurred_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            ticket_id,
        )
        return [_row_to_event(r) for r in rows], total


# ── Row mappers ───────────────────────────────────────────────────────────────

def _row_to_ticket_detail(r) -> TicketDetailRecord:
    raw_assignments = r["active_assignments"]
    if isinstance(raw_assignments, str):
        assignments = json.loads(raw_assignments) or []
    elif raw_assignments is None:
        assignments = []
    else:
        assignments = list(raw_assignments)

    return TicketDetailRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        submitted_by=r["submitted_by"],
        ticket_type_code=r["ticket_type_code"],
        status_code=r["status_code"],
        priority_code=r["priority_code"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        is_deleted=r["is_deleted"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        resolved_at=r["resolved_at"],
        resolved_by=r["resolved_by"],
        title=r["title"],
        description=r["description"],
        context_url=r["context_url"],
        browser_info=r["browser_info"],
        steps_to_reproduce=r["steps_to_reproduce"],
        expected_behavior=r["expected_behavior"],
        actual_behavior=r["actual_behavior"],
        version_info=r["version_info"],
        admin_note=r["admin_note"],
        submitter_email=r["submitter_email"],
        submitter_display_name=r["submitter_display_name"],
        active_assignments=assignments,
    )


def _row_to_event(r) -> TicketEventRecord:
    return TicketEventRecord(
        id=r["id"],
        ticket_id=r["ticket_id"],
        tenant_key=r["tenant_key"],
        event_type=r["event_type"],
        actor_id=r["actor_id"],
        occurred_at=r["occurred_at"],
        old_value=r["old_value"],
        new_value=r["new_value"],
        note=r["note"],
    )
