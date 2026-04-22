"""Repository for notify.template_variables — raw asyncpg SQL, reads v_notify_template_variables."""

from __future__ import annotations

from typing import Any


_VAR_TYPE_ID = {"static": 1, "dynamic_sql": 2}
_DTL_FIELDS = {"name", "static_value", "sql_template", "param_bindings", "description"}


async def list_variables(conn: Any, *, template_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT id, template_id, org_id, name, var_type, static_value,
               sql_template, param_bindings, description, created_at, updated_at
        FROM "06_notify"."v_notify_template_variables"
        WHERE template_id = $1 AND deleted_at IS NULL
        ORDER BY name ASC
        """,
        template_id,
    )
    return [dict(r) for r in rows]


async def get_variable(conn: Any, *, var_id: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, template_id, org_id, name, var_type, static_value,
               sql_template, param_bindings, description, created_at, updated_at
        FROM "06_notify"."v_notify_template_variables"
        WHERE id = $1 AND deleted_at IS NULL
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
    user_id: str,
) -> dict:
    """Insert a variable across both fct (identity + type) and dtl (strings/JSONB).

    Derives org_id from the owning template so callers don't have to plumb it.
    """
    var_type_id = _VAR_TYPE_ID.get(var_type)
    if var_type_id is None:
        raise ValueError(f"unknown var_type {var_type!r}")

    template = await conn.fetchrow(
        'SELECT org_id FROM "06_notify"."12_fct_notify_templates" WHERE id = $1',
        template_id,
    )
    if template is None:
        raise ValueError(f"template {template_id!r} not found")
    org_id = template["org_id"]

    await conn.execute(
        """
        INSERT INTO "06_notify"."13_fct_notify_template_variables"
            (id, template_id, org_id, var_type_id,
             is_active, is_test, created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, $4, TRUE, FALSE, $5, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        var_id, template_id, org_id, var_type_id, user_id,
    )
    await conn.execute(
        """
        INSERT INTO "06_notify"."23_dtl_notify_template_variables"
            (variable_id, template_id, name, static_value, sql_template,
             param_bindings, description, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        var_id, template_id, name, static_value, sql_template,
        param_bindings, description,
    )

    row = await get_variable(conn, var_id=var_id)
    assert row is not None  # just inserted
    return row


async def update_variable(
    conn: Any,
    *,
    var_id: str,
    user_id: str | None = None,
    **fields: Any,
) -> dict | None:
    """Update dtl fields and bump fct audit cols.

    Only dtl fields (static_value, sql_template, param_bindings, description)
    are updatable here — name is immutable post-create to preserve template
    references; var_type is modelled as a new-variable concern.
    """
    updates = {k: v for k, v in fields.items() if k in _DTL_FIELDS and k != "name"}
    if not updates:
        return await get_variable(conn, var_id=var_id)

    set_clauses = [f"{col} = ${i + 2}" for i, col in enumerate(updates)]
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params: list[Any] = [var_id, *updates.values()]

    await conn.execute(
        f"""
        UPDATE "06_notify"."23_dtl_notify_template_variables"
        SET {', '.join(set_clauses)}
        WHERE variable_id = $1
        """,
        *params,
    )

    # Bump fct audit cols so the view's updated_at tracks the edit.
    if user_id is not None:
        await conn.execute(
            """
            UPDATE "06_notify"."13_fct_notify_template_variables"
            SET updated_by = $2, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,
            var_id, user_id,
        )

    return await get_variable(conn, var_id=var_id)


async def delete_variable(conn: Any, *, var_id: str) -> bool:
    """Soft-delete: sets deleted_at on fct; FK cascade will also retire dtl on hard delete."""
    result = await conn.execute(
        """
        UPDATE "06_notify"."13_fct_notify_template_variables"
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1 AND deleted_at IS NULL
        """,
        var_id,
    )
    return result.endswith(" 1")


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
    """
    rows = await conn.fetch(
        """
        SELECT name, var_type, static_value, sql_template, param_bindings
        FROM "06_notify"."v_notify_template_variables"
        WHERE template_id = $1 AND deleted_at IS NULL
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
                await conn.execute("SET LOCAL statement_timeout = '0'")

    return result
