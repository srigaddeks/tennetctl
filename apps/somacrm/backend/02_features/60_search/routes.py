"""Global search across contacts, organizations, leads, deals."""
from __future__ import annotations
from importlib import import_module
from fastapi import APIRouter, Query, Request

_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")

SCHEMA = '"12_somacrm"'
router = APIRouter(prefix="/v1/somacrm/search", tags=["search"])


@router.get("")
async def global_search(
    request: Request,
    q: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required.")

    pool = request.app.state.pool
    pattern = f"%{q}%"

    async with pool.acquire() as conn:
        # Search contacts
        contacts = await conn.fetch(
            f"""SELECT id, 'contact' AS entity_type,
                CONCAT_WS(' ', first_name, last_name) AS title,
                email AS subtitle
            FROM {SCHEMA}.fct_contacts
            WHERE tenant_id = $1 AND deleted_at IS NULL
              AND (first_name ILIKE $2 OR last_name ILIKE $2 OR email ILIKE $2 OR phone ILIKE $2)
            LIMIT $3""",
            ws, pattern, limit // 4 + 5,
        )
        # Search organizations
        orgs = await conn.fetch(
            f"""SELECT id, 'organization' AS entity_type,
                name AS title, email AS subtitle
            FROM {SCHEMA}.fct_organizations
            WHERE tenant_id = $1 AND deleted_at IS NULL
              AND (name ILIKE $2 OR email ILIKE $2)
            LIMIT $3""",
            ws, pattern, limit // 4 + 5,
        )
        # Search leads
        leads = await conn.fetch(
            f"""SELECT id, 'lead' AS entity_type,
                title, email AS subtitle
            FROM {SCHEMA}.fct_leads
            WHERE tenant_id = $1 AND deleted_at IS NULL
              AND (title ILIKE $2 OR email ILIKE $2 OR first_name ILIKE $2 OR last_name ILIKE $2)
            LIMIT $3""",
            ws, pattern, limit // 4 + 5,
        )
        # Search deals
        deals = await conn.fetch(
            f"""SELECT id, 'deal' AS entity_type,
                title, NULL AS subtitle
            FROM {SCHEMA}.fct_deals
            WHERE tenant_id = $1 AND deleted_at IS NULL
              AND title ILIKE $2
            LIMIT $3""",
            ws, pattern, limit // 4 + 5,
        )

    results = (
        [dict(r) for r in contacts]
        + [dict(r) for r in orgs]
        + [dict(r) for r in leads]
        + [dict(r) for r in deals]
    )
    results = results[:limit]
    return _response.ok({"results": results, "total": len(results), "query": q})
