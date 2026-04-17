"""Repository for notify.template_variables — raw asyncpg SQL, reads v_notify_template_variables."""

from __future__ import annotations

from typing import Any


async def list_variables(conn: Any, *, template_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT id, template_id, name, var_type, static_value,
               sql_template, param_bindings, description, created_at, updated_at
        FROM "06_notify"."v_notify_template_variables"
        WHERE template_id = $1
        ORDER BY name ASC
        """,
        template_id,
    )
    return [dict(r) for r in rows]


async def get_variable(conn: Any, *, var_id: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, template_id, name, var_type, static_value,
               sql_template, param_bindings, description, created_at, updated_at
        FROM "06_notify"."v_notify_template_variables"
        WHERE id = $1
        """,
        var_id,
    )
    return dict(row) if row else None


async def create_variable(
    conn: Any,
    *,
    var_id: str,
    template_id: str,
    name: str,
    var_type: str,
    static_value: str | None,
    sql_template: str | None,
    param_bindings: dict | None,
    description: str | None,
) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO "06_notify"."13_fct_notify_template_variables"
            (id, template_id, name, var_type, static_value, sql_template, param_bindings, description)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id, template_id, name, var_type, static_value,
                  sql_template, param_bindings, description, created_at, updated_at
        """,
        var_id,
        template_id,
        name,
        var_type,
        static_value,
        sql_template,
        param_bindings,
        description,
    )
    return dict(row)


async def update_variable(
    conn: Any,
    *,
    var_id: str,
    **fields: Any,
) -> dict | None:
    allowed = {"static_value", "sql_template", "param_bindings", "description"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return await get_variable(conn, var_id=var_id)

    set_clauses = [f"{col} = ${i + 2}" for i, col in enumerate(updates)]
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params = [var_id, *updates.values()]

    row = await conn.fetchrow(
        f"""
        UPDATE "06_notify"."13_fct_notify_template_variables"
        SET {', '.join(set_clauses)}
        WHERE id = $1
        RETURNING id, template_id, name, var_type, static_value,
                  sql_template, param_bindings, description, created_at, updated_at
        """,
        *params,
    )
    return dict(row) if row else None


async def delete_variable(conn: Any, *, var_id: str) -> bool:
    result = await conn.execute(
        """
        DELETE FROM "06_notify"."13_fct_notify_template_variables"
        WHERE id = $1
        """,
        var_id,
    )
    return result == "DELETE 1"


async def resolve_variables(
    conn: Any,
    *,
    template_id: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve all registered variables for a template.

    Static variables: return static_value directly.
    Dynamic SQL: execute sql_template with params from context dict,
                 under SET LOCAL statement_timeout='2000' (2-second limit).

    Returns {var_name: resolved_value} for all registered variables.
    Caller's variables dict is merged AFTER this (caller overrides registered).
    """
    rows = await conn.fetch(
        """
        SELECT name, var_type, static_value, sql_template, param_bindings
        FROM "06_notify"."v_notify_template_variables"
        WHERE template_id = $1
        ORDER BY name ASC
        """,
        template_id,
    )

    result: dict[str, Any] = {}
    for row in rows:
        name = row["name"]
        if row["var_type"] == "static":
            result[name] = row["static_value"]
        else:
            # dynamic_sql: build positional args from param_bindings + context
            bindings: dict[str, str] = dict(row["param_bindings"] or {})
            positional_args: list[Any] = []
            for i in range(1, len(bindings) + 1):
                ctx_key = bindings.get(f"${i}")
                positional_args.append(context.get(ctx_key) if ctx_key else None)

            await conn.execute("SET LOCAL statement_timeout = '2000'")
            try:
                dyn_row = await conn.fetchrow(row["sql_template"], *positional_args)
                result[name] = dyn_row[0] if dyn_row else None
            finally:
                # Reset to no timeout so subsequent queries in this tx are unaffected
                await conn.execute("SET LOCAL statement_timeout = '0'")

    return result
