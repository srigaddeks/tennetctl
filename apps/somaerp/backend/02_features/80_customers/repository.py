"""Customers repository — raw asyncpg against schema "11_somaerp".

Reads v_customers; writes fct_customers (soft-delete). Filters: q (ILIKE
on name/email/phone), status, location_id. Cross-tenant location_id
validation lives here; service calls location_exists before create/update.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Existence checks ────────────────────────────────────────────────────

async def location_exists(
    conn: Any, *, tenant_id: str, location_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_locations "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        location_id, tenant_id,
    )
    return row is not None


# ── Customers CRUD ──────────────────────────────────────────────────────

async def list_customers(
    conn: Any,
    *,
    tenant_id: str,
    status: str | None = None,
    location_id: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if location_id is not None:
        params.append(location_id)
        clauses.append(f"location_id = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        idx = len(params)
        clauses.append(
            f"(name ILIKE ${idx} OR email ILIKE ${idx} OR phone ILIKE ${idx})",
        )
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_customers "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_customer(
    conn: Any, *, tenant_id: str, customer_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_customers "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        customer_id, tenant_id,
    )
    return dict(row) if row else None


async def create_customer(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_customers "
        "(id, tenant_id, location_id, name, slug, email, phone, "
        " address_jsonb, delivery_notes, acquisition_source, status, "
        " lifetime_value, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,0,$12,$13,$13)",
        new_id,
        tenant_id,
        data.get("location_id"),
        data["name"],
        data["slug"],
        data.get("email"),
        data.get("phone"),
        data.get("address_jsonb") or {},
        data.get("delivery_notes"),
        data.get("acquisition_source"),
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_customers WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_CUSTOMER_COLS = (
    "location_id",
    "name",
    "slug",
    "email",
    "phone",
    "address_jsonb",
    "delivery_notes",
    "acquisition_source",
    "status",
    "properties",
    "somacrm_contact_id",
)


async def update_customer(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    customer_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _CUSTOMER_COLS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_customer(
            conn, tenant_id=tenant_id, customer_id=customer_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(customer_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_customers SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_customer(
        conn, tenant_id=tenant_id, customer_id=customer_id,
    )


async def soft_delete_customer(
    conn: Any, *, tenant_id: str, actor_user_id: str, customer_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_customers "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, customer_id, tenant_id,
    )
    return result.endswith(" 1")


async def count_active_subscriptions_for_customer(
    conn: Any, *, tenant_id: str, customer_id: str,
) -> int:
    row = await conn.fetchrow(
        f"SELECT COUNT(*)::INT AS n FROM {SCHEMA}.fct_subscriptions "
        "WHERE tenant_id = $1 AND customer_id = $2 "
        "AND status = 'active' AND deleted_at IS NULL",
        tenant_id, customer_id,
    )
    return int(row["n"]) if row else 0
