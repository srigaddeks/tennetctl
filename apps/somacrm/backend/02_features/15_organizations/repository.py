"""Organizations repository — raw asyncpg against schema "12_somacrm"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somacrm.backend.01_core.id")

SCHEMA = '"12_somacrm"'
TABLE = f'{SCHEMA}."fct_organizations"'
VIEW = f'{SCHEMA}.v_organizations'


async def list_organizations(
    conn: Any,
    *,
    tenant_id: str,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1", "deleted_at IS NULL"]
    if q:
        params.append(f"%{q}%")
        clauses.append(f"(name ILIKE ${len(params)} OR industry ILIKE ${len(params)})")
    params.extend([limit, offset])
    sql = (
        f"SELECT * FROM {VIEW} "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_organization(conn: Any, *, tenant_id: str, org_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {VIEW} WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        org_id, tenant_id,
    )
    return dict(row) if row else None


async def create_organization(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {TABLE} "
        "(id, tenant_id, name, slug, industry, website, phone, email, "
        " employee_count, annual_revenue, description, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$13)",
        new_id, tenant_id,
        data["name"], data["slug"],
        data.get("industry"), data.get("website"),
        data.get("phone"), data.get("email"),
        data.get("employee_count"), data.get("annual_revenue"),
        data.get("description"),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", new_id)
    return dict(row) if row else {}


async def update_organization(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    org_id: str,
    patch: dict,
) -> dict | None:
    updatable = ("name", "slug", "industry", "website", "phone", "email",
                 "employee_count", "annual_revenue", "description", "properties")
    sets: list[str] = []
    params: list[Any] = []
    for col in updatable:
        if col in patch:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_organization(conn, tenant_id=tenant_id, org_id=org_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(org_id)
    params.append(tenant_id)
    sql = (
        f'UPDATE {TABLE} SET {", ".join(sets)} '
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", org_id)
    return dict(row) if row else None


async def soft_delete_organization(
    conn: Any, *, tenant_id: str, actor_user_id: str, org_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {TABLE} "
        "SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, org_id, tenant_id,
    )
    return result.endswith(" 1")
