from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import LiveSessionRecord, LiveSessionSignalRecord, LiveSessionThreatRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods


@instrument_class_methods(
    namespace="sandbox.live_sessions.repository",
    logger_name="backend.sandbox.live_sessions.repository.instrumentation",
)
class LiveSessionRepository:
    async def list_sessions(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        session_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LiveSessionRecord]:
        filters = ["org_id = $1", "is_deleted = FALSE"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"workspace_id = ${idx}")
            values.append(workspace_id)
            idx += 1
        if session_status is not None:
            filters.append(f"session_status = ${idx}")
            values.append(session_status)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, workspace_id,
                   connector_instance_id, session_status,
                   duration_minutes, started_at::text, expires_at::text,
                   paused_at::text, completed_at::text,
                   data_points_received, bytes_received,
                   signals_executed, threats_evaluated,
                   created_at::text, created_by
            FROM {SCHEMA}."28_fct_live_sessions"
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_session(r) for r in rows]

    async def count_sessions(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        session_status: str | None = None,
    ) -> int:
        filters = ["org_id = $1", "is_deleted = FALSE"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"workspace_id = ${idx}")
            values.append(workspace_id)
            idx += 1
        if session_status is not None:
            filters.append(f"session_status = ${idx}")
            values.append(session_status)
            idx += 1

        where_clause = " AND ".join(filters)

        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."28_fct_live_sessions" WHERE {where_clause}',
            *values,
        )
        return row["total"] if row else 0

    async def get_session_by_id(
        self, connection: asyncpg.Connection, session_id: str
    ) -> LiveSessionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_id, workspace_id,
                   connector_instance_id, session_status,
                   duration_minutes, started_at::text, expires_at::text,
                   paused_at::text, completed_at::text,
                   data_points_received, bytes_received,
                   signals_executed, threats_evaluated,
                   created_at::text, created_by
            FROM {SCHEMA}."28_fct_live_sessions"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            session_id,
        )
        return _row_to_session(row) if row else None

    async def create_session(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        connector_instance_id: str,
        session_status: str,
        duration_minutes: int,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."28_fct_live_sessions"
                (id, tenant_key, org_id, workspace_id,
                 connector_instance_id, session_status,
                 duration_minutes, started_at, expires_at,
                 paused_at, completed_at,
                 data_points_received, bytes_received,
                 signals_executed, threats_evaluated,
                 is_deleted, created_at, updated_at, created_by, updated_by)
            VALUES
                ($1, $2, $3, $4,
                 $5, $6,
                 $7, NULL, NULL,
                 NULL, NULL,
                 0, 0,
                 0, 0,
                 FALSE, $8, $9, $10, $11)
            """,
            id,
            tenant_key,
            org_id,
            workspace_id,
            connector_instance_id,
            session_status,
            duration_minutes,
            now,
            now,
            created_by,
            created_by,
        )
        return id

    async def update_session_status(
        self,
        connection: asyncpg.Connection,
        session_id: str,
        new_status: str,
        *,
        now: object,
    ) -> bool:
        # Determine which timestamp column to update based on new_status
        ts_column_map = {
            "active": "started_at",
            "paused": "paused_at",
            "completed": "completed_at",
            "expired": "completed_at",
        }
        ts_column = ts_column_map.get(new_status)

        if ts_column:
            result = await connection.execute(
                f"""
                UPDATE {SCHEMA}."28_fct_live_sessions"
                SET session_status = $1, {ts_column} = $2, updated_at = $3
                WHERE id = $4 AND is_deleted = FALSE
                """,
                new_status,
                now,
                now,
                session_id,
            )
        else:
            result = await connection.execute(
                f"""
                UPDATE {SCHEMA}."28_fct_live_sessions"
                SET session_status = $1, updated_at = $2
                WHERE id = $3 AND is_deleted = FALSE
                """,
                new_status,
                now,
                session_id,
            )
        return result != "UPDATE 0"

    async def set_expires_at(
        self,
        connection: asyncpg.Connection,
        session_id: str,
        expires_at: object,
        *,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."28_fct_live_sessions"
            SET expires_at = $1, updated_at = $2
            WHERE id = $3 AND is_deleted = FALSE
            """,
            expires_at,
            now,
            session_id,
        )
        return result != "UPDATE 0"

    async def increment_stats(
        self,
        connection: asyncpg.Connection,
        session_id: str,
        *,
        data_points: int = 0,
        bytes_count: int = 0,
        signals: int = 0,
        threats: int = 0,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."28_fct_live_sessions"
            SET data_points_received = data_points_received + $1,
                bytes_received = bytes_received + $2,
                signals_executed = signals_executed + $3,
                threats_evaluated = threats_evaluated + $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            data_points,
            bytes_count,
            signals,
            threats,
            session_id,
        )
        return result != "UPDATE 0"

    # --- Attached Signals ---

    async def attach_signal(
        self,
        connection: asyncpg.Connection,
        *,
        live_session_id: str,
        signal_id: str,
        created_by: str,
        now: object,
    ) -> str:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."52_lnk_live_session_signals"
                (id, live_session_id, signal_id, created_at, created_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4)
            RETURNING id::text
            """,
            live_session_id,
            signal_id,
            now,
            created_by,
        )
        return row["id"]

    async def detach_signal(
        self,
        connection: asyncpg.Connection,
        live_session_id: str,
        signal_id: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."52_lnk_live_session_signals"
            WHERE live_session_id = $1 AND signal_id = $2
            """,
            live_session_id,
            signal_id,
        )
        return result != "DELETE 0"

    async def list_attached_signals(
        self,
        connection: asyncpg.Connection,
        session_id: str,
    ) -> list[LiveSessionSignalRecord]:
        rows = await connection.fetch(
            f"""
            SELECT ls.id::text, ls.live_session_id::text, ls.signal_id::text,
                   s.signal_code
            FROM {SCHEMA}."52_lnk_live_session_signals" ls
            LEFT JOIN {SCHEMA}."22_fct_signals" s ON s.id = ls.signal_id
            WHERE ls.live_session_id = $1
            ORDER BY s.signal_code ASC
            """,
            session_id,
        )
        return [
            LiveSessionSignalRecord(
                id=r["id"],
                live_session_id=r["live_session_id"],
                signal_id=r["signal_id"],
                signal_code=r["signal_code"],
                signal_name=None,
            )
            for r in rows
        ]

    # --- Attached Threat Types ---

    async def attach_threat_type(
        self,
        connection: asyncpg.Connection,
        *,
        live_session_id: str,
        threat_type_id: str,
        created_by: str,
        now: object,
    ) -> str:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."53_lnk_live_session_threat_types"
                (id, live_session_id, threat_type_id, created_at, created_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4)
            RETURNING id::text
            """,
            live_session_id,
            threat_type_id,
            now,
            created_by,
        )
        return row["id"]

    async def detach_threat_type(
        self,
        connection: asyncpg.Connection,
        live_session_id: str,
        threat_type_id: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."53_lnk_live_session_threat_types"
            WHERE live_session_id = $1 AND threat_type_id = $2
            """,
            live_session_id,
            threat_type_id,
        )
        return result != "DELETE 0"

    async def list_attached_threats(
        self,
        connection: asyncpg.Connection,
        session_id: str,
    ) -> list[LiveSessionThreatRecord]:
        rows = await connection.fetch(
            f"""
            SELECT lt.id::text, lt.live_session_id::text, lt.threat_type_id::text,
                   t.threat_code
            FROM {SCHEMA}."53_lnk_live_session_threat_types" lt
            LEFT JOIN {SCHEMA}."23_fct_threat_types" t ON t.id = lt.threat_type_id
            WHERE lt.live_session_id = $1
            ORDER BY t.threat_code ASC
            """,
            session_id,
        )
        return [
            LiveSessionThreatRecord(
                id=r["id"],
                live_session_id=r["live_session_id"],
                threat_type_id=r["threat_type_id"],
                threat_code=r["threat_code"],
                threat_name=None,
            )
            for r in rows
        ]

    # --- Active session count ---

    async def count_active_sessions(
        self,
        connection: asyncpg.Connection,
        workspace_id: str,
    ) -> int:
        row = await connection.fetchrow(
            f"""
            SELECT COUNT(*)::int AS total
            FROM {SCHEMA}."28_fct_live_sessions"
            WHERE workspace_id = $1
              AND session_status IN ('starting', 'active', 'paused')
              AND is_deleted = FALSE
            """,
            workspace_id,
        )
        return row["total"] if row else 0


def _row_to_session(r) -> LiveSessionRecord:
    return LiveSessionRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        connector_instance_id=r["connector_instance_id"],
        session_status=r["session_status"],
        duration_minutes=r["duration_minutes"],
        started_at=r["started_at"],
        expires_at=r["expires_at"],
        paused_at=r["paused_at"],
        completed_at=r["completed_at"],
        data_points_received=r["data_points_received"],
        bytes_received=r["bytes_received"],
        signals_executed=r["signals_executed"],
        threats_evaluated=r["threats_evaluated"],
        created_at=r["created_at"],
        created_by=r["created_by"],
    )
