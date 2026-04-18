"""iam.saml_sso — asyncpg repository. Reads v_saml_providers, writes 31_fct_saml_providers."""

from __future__ import annotations

from typing import Any


async def get_by_org(conn: Any, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        'SELECT * FROM "03_iam"."v_saml_providers" WHERE org_id = $1 ORDER BY created_at',
        org_id,
    )
    return [dict(r) for r in rows]


async def get_by_org_slug(conn: Any, org_slug: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "03_iam"."v_saml_providers" WHERE org_slug = $1 AND enabled = TRUE',
        org_slug,
    )
    return dict(row) if row else None


async def get_by_id(conn: Any, provider_id: str, org_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "03_iam"."v_saml_providers" WHERE id = $1 AND org_id = $2',
        provider_id, org_id,
    )
    return dict(row) if row else None


async def create(conn: Any, *, org_id: str, id: str, data: Any) -> dict:
    await conn.execute(
        'INSERT INTO "03_iam"."31_fct_saml_providers" '
        '(id, org_id, idp_entity_id, sso_url, x509_cert, sp_entity_id, enabled) '
        'VALUES ($1, $2, $3, $4, $5, $6, $7)',
        id, org_id,
        data.idp_entity_id, data.sso_url, data.x509_cert, data.sp_entity_id, data.enabled,
    )
    row = await conn.fetchrow(
        'SELECT * FROM "03_iam"."v_saml_providers" WHERE id = $1', id
    )
    return dict(row)


async def soft_delete(conn: Any, *, provider_id: str, org_id: str) -> None:
    await conn.execute(
        'UPDATE "03_iam"."31_fct_saml_providers" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND org_id = $2 AND deleted_at IS NULL',
        provider_id, org_id,
    )
