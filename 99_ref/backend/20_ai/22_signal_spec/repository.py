"""
Repository for signal spec sessions.

Reads/writes 20_ai.46_fct_signal_spec_sessions.
"""

from __future__ import annotations

import json
from importlib import import_module

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.signal_spec.repository")

_SESSIONS = '"20_ai"."46_fct_signal_spec_sessions"'

_SESSION_COLS = """
    id::text, tenant_key, user_id::text, org_id::text, workspace_id::text,
    signal_id::text, connector_type_code, source_dataset_id::text,
    status, current_spec, feasibility_result, conversation_history,
    job_id::text, error_message,
    created_at::text, updated_at::text
"""

_MAX_HISTORY = 20


def _row_to_dict(row) -> dict:
    d = dict(row)
    for key in ("current_spec", "feasibility_result", "conversation_history"):
        val = d.get(key)
        if val is None:
            if key == "conversation_history":
                d[key] = []
            continue
        if isinstance(val, str):
            try:
                d[key] = json.loads(val)
            except Exception:
                pass
    return d


class SpecSessionRepository:

    async def create_session(
        self,
        conn: asyncpg.Connection,
        *,
        session_id: str,
        tenant_key: str,
        user_id: str,
        org_id: str | None,
        workspace_id: str | None,
        connector_type_code: str,
        source_dataset_id: str | None,
        now: str,
    ) -> dict:
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_SESSIONS} (
                id, tenant_key, user_id, org_id, workspace_id,
                connector_type_code, source_dataset_id,
                status, conversation_history,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3::uuid, $4::uuid, $5::uuid,
                $6, $7::uuid,
                'drafting', '[]'::jsonb,
                $8, $9
            )
            RETURNING {_SESSION_COLS}
            """,
            session_id, tenant_key, user_id,
            org_id, workspace_id,
            connector_type_code, source_dataset_id,
            now, now,
        )
        return _row_to_dict(row)

    async def get_by_id(
        self, conn: asyncpg.Connection, session_id: str, tenant_key: str
    ) -> dict | None:
        row = await conn.fetchrow(
            f"SELECT {_SESSION_COLS} FROM {_SESSIONS} WHERE id = $1 AND tenant_key = $2",
            session_id, tenant_key,
        )
        return _row_to_dict(row) if row else None

    async def list_sessions(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        rows = await conn.fetch(
            f"""
            SELECT {_SESSION_COLS}
            FROM {_SESSIONS}
            WHERE tenant_key = $1 AND user_id = $2::uuid
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """,
            tenant_key, user_id, limit, offset,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM {_SESSIONS} WHERE tenant_key = $1 AND user_id = $2::uuid",
            tenant_key, user_id,
        )
        return [_row_to_dict(r) for r in rows], total

    async def save_spec(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        spec: dict,
        feasibility_result: dict | None,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET current_spec = $2::jsonb,
                feasibility_result = $3::jsonb,
                status = 'feasible',
                updated_at = $4
            WHERE id = $1
            """,
            session_id,
            json.dumps(spec),
            json.dumps(feasibility_result) if feasibility_result else None,
            now,
        )

    async def save_feasibility(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        feasibility_result: dict,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET feasibility_result = $2::jsonb,
                updated_at = $3
            WHERE id = $1
            """,
            session_id, json.dumps(feasibility_result), now,
        )

    async def append_turn(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        turn: dict,
        now: str,
    ) -> None:
        """Append a conversation turn, keeping only the last _MAX_HISTORY turns."""
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET conversation_history = (
                    SELECT jsonb_agg(elem)
                    FROM (
                        SELECT elem FROM jsonb_array_elements(
                            COALESCE(conversation_history, '[]'::jsonb) || $2::jsonb
                        ) elem
                        ORDER BY ordinality DESC
                        LIMIT {_MAX_HISTORY}
                    ) sub(elem, ordinality) WITH ORDINALITY
                    ORDER BY ordinality ASC
                ),
                updated_at = $3
            WHERE id = $1
            """,
            session_id, json.dumps([turn]), now,
        )

    async def set_job(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        job_id: str,
        status: str,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET job_id = $2::uuid, status = $3, updated_at = $4
            WHERE id = $1
            """,
            session_id, job_id, status, now,
        )

    async def set_signal_id(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        signal_id: str,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET signal_id = $2::uuid, status = 'approved', updated_at = $3
            WHERE id = $1
            """,
            session_id, signal_id, now,
        )

    async def set_status(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        status: str,
        error_message: str | None = None,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET status = $2, error_message = $3, updated_at = $4
            WHERE id = $1
            """,
            session_id, status, error_message, now,
        )
