"""Contacts repository — raw asyncpg against schema "12_somacrm".

Reads query v_contacts; writes go to fct_contacts. All functions take
a `conn` (asyncpg.Connection); pool handling is routes-only.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somacrm.backend.01_core.id")

SCHEMA = '"12_somacrm"'
TABLE = f'{SCHEMA}."fct_contacts"'
VIEW = f'{SCHEMA}.v_contacts'


async def list_contacts(
    conn: Any,
    *,
    tenant_id: str,
    q: str | None = None,
    status: str | None = None,
    organization_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1", "deleted_at IS NULL"]
    if q:
        params.append(f"%{q}%")
        clauses.append(
            f"(first_name ILIKE ${len(params)} OR last_name ILIKE ${len(params)} "
            f"OR email ILIKE ${len(params)} OR company_name ILIKE ${len(params)})"
        )
    if status:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if organization_id:
        params.append(organization_id)
        clauses.append(f"organization_id = ${len(params)}")
    params.extend([limit, offset])
    sql = (
        f"SELECT * FROM {VIEW} "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_contact(conn: Any, *, tenant_id: str, contact_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {VIEW} WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        contact_id, tenant_id,
    )
    return dict(row) if row else None


async def create_contact(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {TABLE} "
        "(id, tenant_id, organization_id, first_name, last_name, email, phone, mobile, "
        " job_title, company_name, website, linkedin_url, twitter_handle, lead_source, "
        " status_id, somaerp_customer_id, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$18)",
        new_id, tenant_id,
        data.get("organization_id"),
        data["first_name"],
        data.get("last_name"),
        data.get("email"),
        data.get("phone"),
        data.get("mobile"),
        data.get("job_title"),
        data.get("company_name"),
        data.get("website"),
        data.get("linkedin_url"),
        data.get("twitter_handle"),
        data.get("lead_source"),
        data.get("status_id", 1),
        data.get("somaerp_customer_id"),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", new_id)
    return dict(row) if row else {}


async def update_contact(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    contact_id: str,
    patch: dict,
) -> dict | None:
    updatable = (
        "first_name", "last_name", "email", "phone", "mobile", "job_title",
        "company_name", "website", "linkedin_url", "twitter_handle",
        "lead_source", "organization_id", "status_id", "properties",
        "somaerp_customer_id",
    )
    sets: list[str] = []
    params: list[Any] = []
    for col in updatable:
        if col in patch:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_contact(conn, tenant_id=tenant_id, contact_id=contact_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(contact_id)
    params.append(tenant_id)
    sql = (
        f'UPDATE {TABLE} SET {", ".join(sets)} '
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", contact_id)
    return dict(row) if row else None


async def soft_delete_contact(
    conn: Any, *, tenant_id: str, actor_user_id: str, contact_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {TABLE} "
        "SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, contact_id, tenant_id,
    )
    return result.endswith(" 1")


async def get_contact_timeline(
    conn: Any,
    *,
    tenant_id: str,
    contact_id: str,
    limit: int = 200,
) -> list[dict]:
    """Unified reverse-chronological timeline for a contact.

    Aggregates across three sources:
    - Activities linked directly to this contact
    - Activities linked to any deal or lead belonging to this contact
    - Notes linked directly to this contact or their deals/leads
    """
    rows = await conn.fetch(
        f"""
        WITH contact_deals AS (
            SELECT id, title AS deal_title
            FROM {SCHEMA}.fct_deals
            WHERE contact_id = $2 AND tenant_id = $1 AND deleted_at IS NULL
        ),
        contact_leads AS (
            SELECT id, title AS lead_title
            FROM {SCHEMA}.fct_leads
            WHERE contact_id = $2 AND tenant_id = $1 AND deleted_at IS NULL
        ),
        -- Activities: contact + all their deals + all their leads
        activity_rows AS (
            SELECT
                a.id,
                'activity' AS item_type,
                COALESCE(a.due_at, a.created_at) AS event_at,
                a.title,
                a.description AS body,
                at2.code AS activity_type,
                at2.label AS activity_type_label,
                at2.icon AS activity_type_icon,
                ast.code AS status,
                a.entity_type,
                a.entity_id,
                cd.deal_title,
                cl.lead_title,
                a.completed_at,
                a.duration_minutes,
                a.created_at,
                a.created_by,
                NULL::boolean AS is_pinned
            FROM {SCHEMA}.fct_activities a
            JOIN {SCHEMA}.dim_activity_types at2 ON at2.id = a.activity_type_id
            JOIN {SCHEMA}.dim_activity_statuses ast ON ast.id = a.status_id
            LEFT JOIN contact_deals cd ON a.entity_type = 'deal' AND a.entity_id = cd.id
            LEFT JOIN contact_leads cl ON a.entity_type = 'lead' AND a.entity_id = cl.id
            WHERE a.tenant_id = $1
              AND a.deleted_at IS NULL
              AND (
                  (a.entity_type = 'contact' AND a.entity_id = $2)
                  OR (a.entity_type = 'deal'    AND a.entity_id IN (SELECT id FROM contact_deals))
                  OR (a.entity_type = 'lead'    AND a.entity_id IN (SELECT id FROM contact_leads))
              )
        ),
        -- Notes: contact + all their deals + all their leads
        note_rows AS (
            SELECT
                n.id,
                'note' AS item_type,
                n.created_at AS event_at,
                NULL AS title,
                n.content AS body,
                NULL AS activity_type,
                NULL AS activity_type_label,
                NULL AS activity_type_icon,
                NULL AS status,
                n.entity_type,
                n.entity_id,
                cd.deal_title,
                cl.lead_title,
                NULL::timestamp AS completed_at,
                NULL::int AS duration_minutes,
                n.created_at,
                n.created_by,
                n.is_pinned
            FROM {SCHEMA}.fct_notes n
            LEFT JOIN contact_deals cd ON n.entity_type = 'deal' AND n.entity_id = cd.id
            LEFT JOIN contact_leads cl ON n.entity_type = 'lead' AND n.entity_id = cl.id
            WHERE n.tenant_id = $1
              AND n.deleted_at IS NULL
              AND (
                  (n.entity_type = 'contact' AND n.entity_id = $2)
                  OR (n.entity_type = 'deal'    AND n.entity_id IN (SELECT id FROM contact_deals))
                  OR (n.entity_type = 'lead'    AND n.entity_id IN (SELECT id FROM contact_leads))
              )
        )
        SELECT * FROM activity_rows
        UNION ALL
        SELECT * FROM note_rows
        ORDER BY event_at DESC NULLS LAST
        LIMIT $3
        """,
        tenant_id, contact_id, limit,
    )
    return [dict(r) for r in rows]
