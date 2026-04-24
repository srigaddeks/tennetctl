"""Deals repository — raw asyncpg against schema "12_somacrm"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somacrm.backend.01_core.id")

SCHEMA = '"12_somacrm"'
TABLE = f'{SCHEMA}."fct_deals"'
VIEW = f'{SCHEMA}.v_deals'


async def list_deals(
    conn: Any,
    *,
    tenant_id: str,
    status: str | None = None,
    stage_id: str | None = None,
    contact_id: str | None = None,
    organization_id: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1", "deleted_at IS NULL"]
    if status:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if stage_id:
        params.append(stage_id)
        clauses.append(f"stage_id = ${len(params)}")
    if contact_id:
        params.append(contact_id)
        clauses.append(f"contact_id = ${len(params)}")
    if organization_id:
        params.append(organization_id)
        clauses.append(f"organization_id = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"title ILIKE ${len(params)}")
    params.extend([limit, offset])
    sql = (
        f"SELECT * FROM {VIEW} "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_deal(conn: Any, *, tenant_id: str, deal_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {VIEW} WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        deal_id, tenant_id,
    )
    return dict(row) if row else None


async def create_deal(conn: Any, *, tenant_id: str, actor_user_id: str, data: dict) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {TABLE} "
        "(id, tenant_id, title, contact_id, organization_id, stage_id, status_id, "
        " value, currency, expected_close_date, actual_close_date, probability_pct, "
        " assigned_to, description, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$16)",
        new_id, tenant_id,
        data["title"],
        data.get("contact_id"), data.get("organization_id"), data.get("stage_id"),
        data.get("status_id", 1),
        data.get("value"), data.get("currency", "INR"),
        data.get("expected_close_date"), data.get("actual_close_date"),
        data.get("probability_pct"),
        data.get("assigned_to"), data.get("description"),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", new_id)
    return dict(row) if row else {}


async def update_deal(
    conn: Any, *, tenant_id: str, actor_user_id: str, deal_id: str, patch: dict,
) -> dict | None:
    updatable = (
        "title", "contact_id", "organization_id", "stage_id", "status_id",
        "value", "currency", "expected_close_date", "actual_close_date",
        "probability_pct", "assigned_to", "description", "properties",
    )
    sets: list[str] = []
    params: list[Any] = []
    for col in updatable:
        if col in patch:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_deal(conn, tenant_id=tenant_id, deal_id=deal_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(deal_id)
    params.append(tenant_id)
    sql = (
        f'UPDATE {TABLE} SET {", ".join(sets)} '
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", deal_id)
    return dict(row) if row else None


async def soft_delete_deal(
    conn: Any, *, tenant_id: str, actor_user_id: str, deal_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {TABLE} "
        "SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, deal_id, tenant_id,
    )
    return result.endswith(" 1")
