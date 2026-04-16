from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import AgentRecord

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

SCHEMA = '"25_agent_sandbox"'


@instrument_class_methods(namespace="agent_sandbox.agents.repository", logger_name="backend.agent_sandbox.agents.repository.instrumentation")
class AgentRepository:
    _AGENT_SORT_COLUMNS = frozenset({"name", "agent_code", "created_at", "updated_at", "version_number"})

    # ── list ──────────────────────────────────────────────────

    async def list_agents(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        agent_status_code: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AgentRecord], int]:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"workspace_id = ${idx}")
            values.append(workspace_id)
            idx += 1
        if agent_status_code is not None:
            filters.append(f"agent_status_code = ${idx}")
            values.append(agent_status_code)
            idx += 1
        if search is not None:
            filters.append(f"(LOWER(name) LIKE ${idx} OR LOWER(agent_code) LIKE ${idx})")
            values.append(f"%{search.lower()}%")
            idx += 1

        where_clause = " AND ".join(filters)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."80_vw_agent_detail" WHERE {where_clause}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        sort_col = sort_by if sort_by in self._AGENT_SORT_COLUMNS else "created_at"
        sort_direction = "DESC" if sort_dir.upper() == "DESC" else "ASC"

        rows = await connection.fetch(
            f"""
            SELECT v.id, v.tenant_key, v.org_id, v.workspace_id, v.agent_code,
                   v.version_number, v.agent_status_code, v.agent_status_name,
                   v.graph_type, v.llm_model_id, v.temperature::float,
                   v.max_iterations, v.max_tokens_budget, v.max_tool_calls,
                   v.max_duration_ms, v.max_cost_usd::float, v.requires_approval,
                   v.python_hash, v.is_active,
                   v.created_at::text, v.updated_at::text,
                   v.name, v.description,
                   gs.property_value AS graph_source
            FROM {SCHEMA}."80_vw_agent_detail" v
            LEFT JOIN {SCHEMA}."40_dtl_agent_properties" gs
                ON gs.agent_id = v.id AND gs.property_key = 'graph_source'
            WHERE {where_clause}
            ORDER BY {sort_col} {sort_direction}, agent_code ASC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_agent(r) for r in rows], total

    # ── single ────────────────────────────────────────────────

    async def get_agent_by_id(
        self, connection: asyncpg.Connection, agent_id: str
    ) -> AgentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT v.id, v.tenant_key, v.org_id, v.workspace_id, v.agent_code,
                   v.version_number, v.agent_status_code, v.agent_status_name,
                   v.graph_type, v.llm_model_id, v.temperature::float,
                   v.max_iterations, v.max_tokens_budget, v.max_tool_calls,
                   v.max_duration_ms, v.max_cost_usd::float, v.requires_approval,
                   v.python_hash, v.is_active,
                   v.created_at::text, v.updated_at::text,
                   v.name, v.description
            FROM {SCHEMA}."80_vw_agent_detail" v
            WHERE v.id = $1
            """,
            agent_id,
        )
        return _row_to_agent(row) if row else None

    # ── properties ────────────────────────────────────────────

    async def get_agent_properties(
        self, connection: asyncpg.Connection, agent_id: str
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."40_dtl_agent_properties"
            WHERE agent_id = $1
            """,
            agent_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    # ── create ────────────────────────────────────────────────

    async def create_agent(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        agent_code: str,
        version_number: int,
        agent_status_code: str,
        graph_type: str,
        llm_model_id: str | None,
        temperature: float,
        max_iterations: int,
        max_tokens_budget: int,
        max_tool_calls: int,
        max_duration_ms: int,
        max_cost_usd: float,
        requires_approval: bool,
        python_hash: str | None,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."20_fct_agents"
                (id, tenant_key, org_id, workspace_id, agent_code,
                 version_number, agent_status_code, graph_type,
                 llm_model_id, temperature,
                 max_iterations, max_tokens_budget, max_tool_calls,
                 max_duration_ms, max_cost_usd, requires_approval,
                 python_hash,
                 is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by,
                 deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8,
                 $9, $10,
                 $11, $12, $13,
                 $14, $15, $16,
                 $17,
                 TRUE, FALSE,
                 $18, $19, $20, $21,
                 NULL, NULL)
            """,
            id, tenant_key, org_id, workspace_id, agent_code,
            version_number, agent_status_code, graph_type,
            llm_model_id, temperature,
            max_iterations, max_tokens_budget, max_tool_calls,
            max_duration_ms, max_cost_usd, requires_approval,
            python_hash,
            now, now, created_by, created_by,
        )
        return id

    # ── versioning ────────────────────────────────────────────

    async def get_next_version(
        self, connection: asyncpg.Connection, org_id: str, agent_code: str
    ) -> int:
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1))",
            f"asb:agent_version:{org_id}:{agent_code}",
        )
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM {SCHEMA}."20_fct_agents"
            WHERE org_id = $1 AND agent_code = $2
            """,
            org_id, agent_code,
        )
        return row["next_version"]

    async def list_versions(
        self, connection: asyncpg.Connection, org_id: str, agent_code: str
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT id, version_number, agent_status_code, python_hash,
                   created_at::text, created_by
            FROM {SCHEMA}."20_fct_agents"
            WHERE org_id = $1 AND agent_code = $2 AND is_deleted = FALSE
            ORDER BY version_number DESC
            """,
            org_id, agent_code,
        )
        return [dict(r) for r in rows]

    # ── properties upsert ─────────────────────────────────────

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        agent_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (agent_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."40_dtl_agent_properties"
                (id, agent_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (agent_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    # ── update status ─────────────────────────────────────────

    async def update_agent_status(
        self,
        connection: asyncpg.Connection,
        agent_id: str,
        new_status: str,
        *,
        updated_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_fct_agents"
            SET agent_status_code = $1, updated_at = $2, updated_by = $3
            WHERE id = $4 AND is_deleted = FALSE
            """,
            new_status, now, updated_by, agent_id,
        )
        return result != "UPDATE 0"

    # ── update structural fields ──────────────────────────────

    async def update_agent_fields(
        self,
        connection: asyncpg.Connection,
        agent_id: str,
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
            set_clauses.append(f"{col} = ${idx}")
            values.append(val)
            idx += 1
        set_clauses.append(f"updated_at = ${idx}")
        values.append(now)
        idx += 1
        set_clauses.append(f"updated_by = ${idx}")
        values.append(updated_by)
        idx += 1
        values.append(agent_id)
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_fct_agents"
            SET {", ".join(set_clauses)}
            WHERE id = ${idx} AND is_deleted = FALSE
            """,
            *values,
        )
        return result != "UPDATE 0"

    # ── soft delete ───────────────────────────────────────────

    async def soft_delete_agent(
        self,
        connection: asyncpg.Connection,
        agent_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_fct_agents"
            SET is_deleted = TRUE, is_active = FALSE,
                deleted_at = $1, deleted_by = $2,
                updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, agent_id,
        )
        return result != "UPDATE 0"

    # ── tool bindings ─────────────────────────────────────────

    async def bind_tool(
        self,
        connection: asyncpg.Connection,
        agent_id: str,
        tool_id: str,
        *,
        sort_order: int = 0,
        created_by: str,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."50_lnk_agent_tool_bindings"
                (id, agent_id, tool_id, sort_order, is_active, created_at, created_by)
            VALUES (gen_random_uuid(), $1, $2, $3, TRUE, NOW(), $4)
            ON CONFLICT (agent_id, tool_id) DO UPDATE
            SET sort_order = EXCLUDED.sort_order, is_active = TRUE
            """,
            agent_id, tool_id, sort_order, created_by,
        )

    async def unbind_tool(
        self,
        connection: asyncpg.Connection,
        agent_id: str,
        tool_id: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."50_lnk_agent_tool_bindings"
            WHERE agent_id = $1 AND tool_id = $2
            """,
            agent_id, tool_id,
        )
        return result != "DELETE 0"

    async def list_bound_tools(
        self,
        connection: asyncpg.Connection,
        agent_id: str,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT b.tool_id, b.sort_order, t.tool_code, t.tool_type_code,
                   tp.property_value AS tool_name
            FROM {SCHEMA}."50_lnk_agent_tool_bindings" b
            JOIN {SCHEMA}."21_fct_agent_tools" t ON t.id = b.tool_id
            LEFT JOIN {SCHEMA}."41_dtl_tool_properties" tp
                ON tp.tool_id = t.id AND tp.property_key = 'name'
            WHERE b.agent_id = $1 AND b.is_active = TRUE AND t.is_deleted = FALSE
            ORDER BY b.sort_order, t.tool_code
            """,
            agent_id,
        )
        return [dict(r) for r in rows]


def _row_to_agent(r) -> AgentRecord:
    return AgentRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        agent_code=r["agent_code"],
        version_number=r["version_number"],
        agent_status_code=r["agent_status_code"],
        agent_status_name=r.get("agent_status_name"),
        graph_type=r["graph_type"],
        llm_model_id=r.get("llm_model_id"),
        temperature=float(r["temperature"]),
        max_iterations=r["max_iterations"],
        max_tokens_budget=r["max_tokens_budget"],
        max_tool_calls=r["max_tool_calls"],
        max_duration_ms=r["max_duration_ms"],
        max_cost_usd=float(r["max_cost_usd"]),
        requires_approval=r["requires_approval"],
        python_hash=r.get("python_hash"),
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r.get("name"),
        description=r.get("description"),
    )
