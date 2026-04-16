from __future__ import annotations

import json
import asyncpg
from importlib import import_module

from .models import AgentToolRecord

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

SCHEMA = '"25_agent_sandbox"'


@instrument_class_methods(namespace="agent_sandbox.tools.repository", logger_name="backend.agent_sandbox.tools.repository.instrumentation")
class AgentToolRepository:
    _TOOL_SORT_COLUMNS = frozenset({"name", "tool_code", "created_at", "updated_at", "tool_type_code"})

    # ── list ──────────────────────────────────────────────────

    async def list_tools(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        tool_type_code: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AgentToolRecord], int]:
        filters = ["t.org_id = $1", "t.is_deleted = FALSE"]
        values: list[object] = [org_id]
        idx = 2

        if tool_type_code is not None:
            filters.append(f"t.tool_type_code = ${idx}")
            values.append(tool_type_code)
            idx += 1
        if search is not None:
            filters.append(f"(LOWER(tn.property_value) LIKE ${idx} OR LOWER(t.tool_code) LIKE ${idx})")
            values.append(f"%{search.lower()}%")
            idx += 1

        where_clause = " AND ".join(filters)

        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*)::int AS total
            FROM {SCHEMA}."21_fct_agent_tools" t
            LEFT JOIN {SCHEMA}."41_dtl_tool_properties" tn
                ON tn.tool_id = t.id AND tn.property_key = 'name'
            WHERE {where_clause}
            """,
            *values,
        )
        total = count_row["total"] if count_row else 0

        sort_col = f"t.{sort_by}" if sort_by in self._TOOL_SORT_COLUMNS else "t.created_at"
        if sort_by == "name":
            sort_col = "tn.property_value"
        sort_direction = "DESC" if sort_dir.upper() == "DESC" else "ASC"

        rows = await connection.fetch(
            f"""
            SELECT t.id, t.tenant_key, t.org_id, t.tool_code, t.tool_type_code,
                   t.input_schema, t.output_schema,
                   t.endpoint_url, t.mcp_server_url, t.python_source,
                   t.signal_id, t.requires_approval, t.is_destructive,
                   t.timeout_ms, t.is_active,
                   t.created_at::text, t.updated_at::text,
                   tn.property_value AS name,
                   td.property_value AS description
            FROM {SCHEMA}."21_fct_agent_tools" t
            LEFT JOIN {SCHEMA}."41_dtl_tool_properties" tn
                ON tn.tool_id = t.id AND tn.property_key = 'name'
            LEFT JOIN {SCHEMA}."41_dtl_tool_properties" td
                ON td.tool_id = t.id AND td.property_key = 'description'
            WHERE {where_clause}
            ORDER BY {sort_col} {sort_direction}, t.tool_code ASC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_tool(r) for r in rows], total

    # ── single ────────────────────────────────────────────────

    async def get_tool_by_id(
        self, connection: asyncpg.Connection, tool_id: str
    ) -> AgentToolRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT t.id, t.tenant_key, t.org_id, t.tool_code, t.tool_type_code,
                   t.input_schema, t.output_schema,
                   t.endpoint_url, t.mcp_server_url, t.python_source,
                   t.signal_id, t.requires_approval, t.is_destructive,
                   t.timeout_ms, t.is_active,
                   t.created_at::text, t.updated_at::text,
                   tn.property_value AS name,
                   td.property_value AS description
            FROM {SCHEMA}."21_fct_agent_tools" t
            LEFT JOIN {SCHEMA}."41_dtl_tool_properties" tn
                ON tn.tool_id = t.id AND tn.property_key = 'name'
            LEFT JOIN {SCHEMA}."41_dtl_tool_properties" td
                ON td.tool_id = t.id AND td.property_key = 'description'
            WHERE t.id = $1 AND t.is_deleted = FALSE
            """,
            tool_id,
        )
        return _row_to_tool(row) if row else None

    # ── properties ────────────────────────────────────────────

    async def get_tool_properties(
        self, connection: asyncpg.Connection, tool_id: str
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."41_dtl_tool_properties"
            WHERE tool_id = $1
            """,
            tool_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    # ── create ────────────────────────────────────────────────

    async def create_tool(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        tool_code: str,
        tool_type_code: str,
        input_schema: dict,
        output_schema: dict,
        endpoint_url: str | None,
        mcp_server_url: str | None,
        python_source: str | None,
        signal_id: str | None,
        requires_approval: bool,
        is_destructive: bool,
        timeout_ms: int,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."21_fct_agent_tools"
                (id, tenant_key, org_id, tool_code, tool_type_code,
                 input_schema, output_schema,
                 endpoint_url, mcp_server_url, python_source,
                 signal_id, requires_approval, is_destructive, timeout_ms,
                 is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by,
                 deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6::jsonb, $7::jsonb,
                 $8, $9, $10,
                 $11, $12, $13, $14,
                 TRUE, FALSE,
                 $15, $16, $17, $18,
                 NULL, NULL)
            """,
            id, tenant_key, org_id, tool_code, tool_type_code,
            json.dumps(input_schema), json.dumps(output_schema),
            endpoint_url, mcp_server_url, python_source,
            signal_id, requires_approval, is_destructive, timeout_ms,
            now, now, created_by, created_by,
        )
        return id

    # ── properties upsert ─────────────────────────────────────

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        tool_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (tool_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."41_dtl_tool_properties"
                (id, tool_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (tool_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    # ── update ────────────────────────────────────────────────

    async def update_tool_fields(
        self,
        connection: asyncpg.Connection,
        tool_id: str,
        *,
        updates: dict,
        updated_by: str,
        now: object,
    ) -> bool:
        if not updates:
            return False
        set_clauses = []
        values: list[object] = []
        idx = 1
        for col, val in updates.items():
            if col in ("input_schema", "output_schema"):
                set_clauses.append(f"{col} = ${idx}::jsonb")
                values.append(json.dumps(val))
            else:
                set_clauses.append(f"{col} = ${idx}")
                values.append(val)
            idx += 1
        set_clauses.append(f"updated_at = ${idx}")
        values.append(now)
        idx += 1
        set_clauses.append(f"updated_by = ${idx}")
        values.append(updated_by)
        idx += 1
        values.append(tool_id)
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."21_fct_agent_tools"
            SET {", ".join(set_clauses)}
            WHERE id = ${idx} AND is_deleted = FALSE
            """,
            *values,
        )
        return result != "UPDATE 0"

    # ── soft delete ───────────────────────────────────────────

    async def soft_delete_tool(
        self,
        connection: asyncpg.Connection,
        tool_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."21_fct_agent_tools"
            SET is_deleted = TRUE, is_active = FALSE,
                deleted_at = $1, deleted_by = $2,
                updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, tool_id,
        )
        return result != "UPDATE 0"


def _row_to_tool(r) -> AgentToolRecord:
    input_schema = r["input_schema"]
    if isinstance(input_schema, str):
        input_schema = json.loads(input_schema)
    output_schema = r["output_schema"]
    if isinstance(output_schema, str):
        output_schema = json.loads(output_schema)
    return AgentToolRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        tool_code=r["tool_code"],
        tool_type_code=r["tool_type_code"],
        input_schema=input_schema or {},
        output_schema=output_schema or {},
        endpoint_url=r.get("endpoint_url"),
        mcp_server_url=r.get("mcp_server_url"),
        python_source=r.get("python_source"),
        signal_id=r.get("signal_id"),
        requires_approval=r["requires_approval"],
        is_destructive=r["is_destructive"],
        timeout_ms=r["timeout_ms"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r.get("name"),
        description=r.get("description"),
    )
