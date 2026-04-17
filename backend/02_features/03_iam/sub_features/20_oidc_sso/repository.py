"""iam.oidc_sso — asyncpg repository. Reads v_oidc_providers, writes 30_fct_oidc_providers."""

from __future__ import annotations

from typing import Any


async def get_by_org(conn: Any, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        'SELECT * FROM "03_iam"."v_oidc_providers" WHERE org_id = $1 ORDER BY created_at',
        org_id,
    )
    return [dict(r) for r in rows]


async def get_by_org_slug(conn: Any, org_slug: str, provider_slug: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "03_iam"."v_oidc_providers" '
        'WHERE org_slug = $1 AND slug = $2 AND enabled = TRUE',
        org_slug, provider_slug,
    )
    return dict(row) if row else None


async def get_by_id(conn: Any, provider_id: str, org_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "03_iam"."v_oidc_providers" WHERE id = $1 AND org_id = $2',
        provider_id, org_id,
    )
    return dict(row) if row else None


async def create(conn: Any, *, org_id: str, id: str, data: Any) -> dict:
    row = await conn.fetchrow(
        'INSERT INTO "03_iam"."30_fct_oidc_providers" '
        '(id, org_id, slug, issuer, client_id, client_secret_vault_key, scopes, claim_mapping) '
        'VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *',
        id, org_id,
        data.slug, data.issuer, data.client_id, data.client_secret_vault_key,
        data.scopes, dict(data.claim_mapping),
    )
    return dict(row)


async def soft_delete(conn: Any, *, provider_id: str, org_id: str) -> None:
    await conn.execute(
        'UPDATE "03_iam"."30_fct_oidc_providers" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND org_id = $2 AND deleted_at IS NULL',
        provider_id, org_id,
    )
