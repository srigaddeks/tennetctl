from __future__ import annotations

import json
import time

import asyncpg
from importlib import import_module

from ..models import VariableQueryRecord

SCHEMA = '"03_notifications"'
AUTH_SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods
get_logger = import_module("backend.01_core.logging_utils").get_logger

_LOGGER = get_logger("backend.notifications.variable_queries.repository")

_QUERY_COLS = """id, tenant_key, code, name, description, sql_template,
                 bind_params::text, result_columns::text, timeout_ms,
                 is_active, is_deleted, is_system,
                 linked_event_type_codes,
                 created_at::text, updated_at::text, created_by"""

# ── Dangerous SQL keywords (standalone, case-insensitive) ─────────────────

_FORBIDDEN_KEYWORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "COPY", "EXECUTE", "CALL",
})


def validate_sql_template(sql: str) -> None:
    """Reject anything that isn't a read-only SELECT.

    Raises ValueError if the SQL contains forbidden keywords,
    doesn't start with SELECT, or contains statement terminators.
    """
    # Reject any semicolons — they allow statement chaining / injection
    if ";" in sql:
        raise ValueError("SQL template must not contain semicolons")

    stripped = sql.strip()
    # Strip leading comments
    while stripped.startswith("--"):
        stripped = stripped.split("\n", 1)[-1].strip()
    while stripped.startswith("/*"):
        end = stripped.find("*/")
        if end == -1:
            break
        stripped = stripped[end + 2:].strip()

    if not stripped.upper().startswith("SELECT"):
        raise ValueError("SQL template must start with SELECT")

    # Tokenize and check for forbidden keywords
    import re
    tokens = re.findall(r"[A-Za-z_]+", stripped.upper())
    for token in tokens:
        if token in _FORBIDDEN_KEYWORDS:
            raise ValueError(f"SQL template contains forbidden keyword: {token}")


@instrument_class_methods(
    namespace="variable_queries.repository",
    logger_name="backend.notifications.variable_queries.repository.instrumentation",
)
class VariableQueryRepository:

    async def list_queries(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
    ) -> tuple[list[VariableQueryRecord], int]:
        total: int = await connection.fetchval(
            f"""SELECT COUNT(*) FROM {SCHEMA}."31_fct_variable_queries"
            WHERE (tenant_key = $1 OR tenant_key = '__system__') AND is_deleted = FALSE""",
            tenant_key,
        )
        rows = await connection.fetch(
            f"""SELECT {_QUERY_COLS} FROM {SCHEMA}."31_fct_variable_queries"
            WHERE (tenant_key = $1 OR tenant_key = '__system__') AND is_deleted = FALSE
            ORDER BY is_system DESC, code""",
            tenant_key,
        )
        return [_row_to_record(r) for r in rows], total

    async def get_by_id(
        self,
        connection: asyncpg.Connection,
        query_id: str,
    ) -> VariableQueryRecord | None:
        row = await connection.fetchrow(
            f"""SELECT {_QUERY_COLS} FROM {SCHEMA}."31_fct_variable_queries"
            WHERE id = $1 AND is_deleted = FALSE""",
            query_id,
        )
        return _row_to_record(row) if row else None

    async def get_by_code(
        self,
        connection: asyncpg.Connection,
        code: str,
        tenant_key: str,
    ) -> VariableQueryRecord | None:
        row = await connection.fetchrow(
            f"""SELECT {_QUERY_COLS} FROM {SCHEMA}."31_fct_variable_queries"
            WHERE code = $1 AND tenant_key = $2 AND is_deleted = FALSE""",
            code, tenant_key,
        )
        return _row_to_record(row) if row else None

    async def create(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        code: str,
        name: str,
        description: str | None,
        sql_template: str,
        bind_params: list[dict],
        result_columns: list[dict],
        timeout_ms: int,
        created_by: str,
        now: str,
    ) -> VariableQueryRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."31_fct_variable_queries"
                (id, tenant_key, code, name, description, sql_template,
                 bind_params, result_columns, timeout_ms, linked_event_type_codes,
                 created_by, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $10, $11, $12, $12)
            RETURNING {_QUERY_COLS}
            """,
            id, tenant_key, code, name, description, sql_template,
            json.dumps(bind_params), json.dumps(result_columns),
            timeout_ms, linked_event_type_codes or [], created_by, now,
        )
        return _row_to_record(row)

    async def update(
        self,
        connection: asyncpg.Connection,
        query_id: str,
        *,
        now: str,
        **fields,
    ) -> VariableQueryRecord | None:
        sets: list[str] = ["updated_at = $2"]
        params: list = [query_id, now]
        idx = 3
        for key, value in fields.items():
            if value is None:
                continue
            if key in ("bind_params", "result_columns"):
                sets.append(f"{key} = ${idx}::jsonb")
                params.append(json.dumps(value))
            elif key == "linked_event_type_codes":
                sets.append(f"{key} = ${idx}")
                params.append(value)  # already a list
            else:
                sets.append(f"{key} = ${idx}")
                params.append(value)
            idx += 1
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."31_fct_variable_queries"
            SET {', '.join(sets)}
            WHERE id = $1 AND is_deleted = FALSE
            RETURNING {_QUERY_COLS}
            """,
            *params,
        )
        return _row_to_record(row) if row else None

    async def soft_delete(
        self,
        connection: asyncpg.Connection,
        query_id: str,
        now: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."31_fct_variable_queries"
            SET is_deleted = TRUE, is_active = FALSE, updated_at = $2
            WHERE id = $1 AND is_deleted = FALSE
            """,
            query_id, now,
        )
        return result.endswith("1")

    # ── Query execution ────────────────────────────────────────────────

    async def execute_query(
        self,
        connection: asyncpg.Connection,
        *,
        sql_template: str,
        ordered_params: list,
        timeout_ms: int,
    ) -> tuple[list[dict[str, str]], int]:
        """Execute a user-defined SELECT in a read-only context with timeout.

        Returns (rows_as_dicts, execution_ms).
        """
        import re as _re

        # Enforce a hard LIMIT 100 cap: wrap in a subquery if no LIMIT present
        _upper = sql_template.upper()
        if "LIMIT" not in _upper:
            safe_sql = f"SELECT * FROM ({sql_template}) _vq_inner LIMIT 100"
        else:
            safe_sql = sql_template

        start = time.monotonic()
        # Use a SAVEPOINT to ensure any side-effects (should be impossible with
        # read-only mode, but belt-and-suspenders) are rolled back cleanly.
        await connection.execute(f"SET LOCAL statement_timeout = '{timeout_ms}'")
        await connection.execute("SET LOCAL default_transaction_read_only = ON")
        await connection.execute("SAVEPOINT vq_exec")
        try:
            rows = await connection.fetch(safe_sql, *ordered_params)
        finally:
            await connection.execute("ROLLBACK TO SAVEPOINT vq_exec")
            await connection.execute("RELEASE SAVEPOINT vq_exec")

        elapsed_ms = int((time.monotonic() - start) * 1000)

        result = []
        for row in rows:
            result.append({k: str(v) if v is not None else "" for k, v in dict(row).items()})
        return result, elapsed_ms

    # ── Variable key sync ──────────────────────────────────────────────

    async def sync_variable_keys(
        self,
        connection: asyncpg.Connection,
        *,
        query_id: str,
        query_code: str,
        result_columns: list[dict],
        now: str,
    ) -> list[str]:
        """Create/update/deactivate variable keys in 08_dim_template_variable_keys.

        Returns the list of generated variable key codes.
        """
        import uuid as _uuid

        # Get existing keys for this query
        existing = await connection.fetch(
            f"""SELECT id, code, resolution_key
            FROM {SCHEMA}."08_dim_template_variable_keys"
            WHERE query_id = $1""",
            query_id,
        )
        existing_by_col = {r["resolution_key"]: r for r in existing}

        generated_codes: list[str] = []
        new_col_names = set()

        for idx, col in enumerate(result_columns):
            col_name = col["name"]
            new_col_names.add(col_name)
            var_code = f"custom.{query_code}.{col_name}"
            generated_codes.append(var_code)

            if col_name in existing_by_col:
                # Update existing
                await connection.execute(
                    f"""
                    UPDATE {SCHEMA}."08_dim_template_variable_keys"
                    SET code = $1, name = $2, description = $3,
                        data_type = $4, example_value = $5,
                        sort_order = $6, updated_at = $7
                    WHERE id = $8
                    """,
                    var_code,
                    f"Custom: {query_code}.{col_name}",
                    f"Custom variable from query '{query_code}'",
                    col.get("data_type", "string"),
                    col.get("default_value"),
                    900 + idx,  # sort after built-in vars
                    now,
                    existing_by_col[col_name]["id"],
                )
            else:
                # Insert new
                await connection.execute(
                    f"""
                    INSERT INTO {SCHEMA}."08_dim_template_variable_keys"
                        (id, code, name, description, data_type, example_value,
                         resolution_source, resolution_key, query_id,
                         sort_order, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, 'custom_query', $7, $8, $9, $10, $10)
                    """,
                    str(_uuid.uuid4()),
                    var_code,
                    f"Custom: {query_code}.{col_name}",
                    f"Custom variable from query '{query_code}'",
                    col.get("data_type", "string"),
                    col.get("default_value"),
                    col_name,      # resolution_key = column name
                    query_id,
                    900 + idx,
                    now,
                )

        # Deactivate keys for removed columns (delete the rows)
        for col_name, row in existing_by_col.items():
            if col_name not in new_col_names:
                await connection.execute(
                    f"""DELETE FROM {SCHEMA}."08_dim_template_variable_keys"
                    WHERE id = $1""",
                    row["id"],
                )

        return generated_codes

    async def deactivate_variable_keys(
        self,
        connection: asyncpg.Connection,
        query_id: str,
    ) -> None:
        """Remove all variable keys for a deleted query."""
        await connection.execute(
            f"""DELETE FROM {SCHEMA}."08_dim_template_variable_keys"
            WHERE query_id = $1""",
            query_id,
        )

    async def get_variable_keys_for_query(
        self,
        connection: asyncpg.Connection,
        query_id: str,
    ) -> list[str]:
        """Get the generated variable key codes for a query."""
        rows = await connection.fetch(
            f"""SELECT code FROM {SCHEMA}."08_dim_template_variable_keys"
            WHERE query_id = $1 ORDER BY sort_order""",
            query_id,
        )
        return [r["code"] for r in rows]

    async def fetch_audit_event_context(
        self,
        connection: asyncpg.Connection,
        event_id: str,
    ) -> dict[str, str]:
        """Fetch audit event properties for preview/test context."""
        rows = await connection.fetch(
            f"""SELECT meta_key, meta_value
            FROM {AUTH_SCHEMA}."41_dtl_audit_event_properties"
            WHERE event_id = $1""",
            event_id,
        )
        return {r["meta_key"]: r["meta_value"] for r in rows}

    # ── Schema metadata ───────────────────────────────────────────────

    async def fetch_schema_metadata(
        self,
        connection: asyncpg.Connection,
        schema_tables: dict[str, list[str]],
    ) -> list[dict]:
        """Fetch column metadata for whitelisted tables."""
        schemas = list(schema_tables.keys())
        tables = [t for ts in schema_tables.values() for t in ts]
        rows = await connection.fetch(
            """SELECT table_schema, table_name, column_name,
                      data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = ANY($1)
              AND table_name = ANY($2)
            ORDER BY table_schema, table_name, ordinal_position""",
            schemas, tables,
        )
        return [dict(r) for r in rows]

    # ── Audit event types ─────────────────────────────────────────────

    async def fetch_audit_event_types(
        self,
        connection: asyncpg.Connection,
    ) -> list[dict]:
        """Get distinct audit event types with counts."""
        rows = await connection.fetch(
            f"""SELECT entity_type, event_type, event_category,
                       COUNT(*)::int AS event_count
            FROM {AUTH_SCHEMA}."40_aud_events"
            GROUP BY entity_type, event_type, event_category
            ORDER BY event_count DESC"""
        )
        return [dict(r) for r in rows]

    async def fetch_audit_event_properties(
        self,
        connection: asyncpg.Connection,
        event_type: str,
    ) -> list[str]:
        """Get distinct meta_keys used for a given event_type."""
        rows = await connection.fetch(
            f"""SELECT DISTINCT ep.meta_key
            FROM {AUTH_SCHEMA}."41_dtl_audit_event_properties" ep
            JOIN {AUTH_SCHEMA}."40_aud_events" ae ON ae.id = ep.event_id
            WHERE ae.event_type = $1
            ORDER BY ep.meta_key""",
            event_type,
        )
        return [r["meta_key"] for r in rows]

    # ── Recent audit events ───────────────────────────────────────────

    async def fetch_recent_audit_events(
        self,
        connection: asyncpg.Connection,
        event_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Fetch recent audit events with their properties."""
        if event_type:
            event_rows = await connection.fetch(
                f"""SELECT id::text, entity_type, entity_id::text,
                           event_type, event_category,
                           actor_id::text, occurred_at::text
                FROM {AUTH_SCHEMA}."40_aud_events"
                WHERE event_type = $1
                ORDER BY occurred_at DESC
                LIMIT $2""",
                event_type, limit,
            )
        else:
            event_rows = await connection.fetch(
                f"""SELECT id::text, entity_type, entity_id::text,
                           event_type, event_category,
                           actor_id::text, occurred_at::text
                FROM {AUTH_SCHEMA}."40_aud_events"
                ORDER BY occurred_at DESC
                LIMIT $1""",
                limit,
            )

        results = []
        for er in event_rows:
            props = await self.fetch_audit_event_context(connection, er["id"])
            results.append({**dict(er), "properties": props})
        return results


def _row_to_record(row: asyncpg.Record) -> VariableQueryRecord:
    return VariableQueryRecord(
        id=str(row["id"]),
        tenant_key=row["tenant_key"],
        code=row["code"],
        name=row["name"],
        description=row["description"],
        sql_template=row["sql_template"],
        bind_params=row["bind_params"],
        result_columns=row["result_columns"],
        timeout_ms=row["timeout_ms"],
        is_active=row["is_active"],
        is_deleted=row["is_deleted"],
        is_system=row["is_system"],
        linked_event_type_codes=list(row["linked_event_type_codes"] or []),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        created_by=str(row["created_by"]) if row["created_by"] else None,
    )
