"""IAM applications repository — raw SQL for application CRUD, product links, tokens, and resolve-access.

All attr_def_ids are resolved dynamically from 07_dim_attr_defs by code.
No hardcoded IDENTITY values anywhere in this file.

10_fct_applications has code and name as identity columns (exception for catalog
lookup performance). All extended attrs (description, slug, icon_url,
redirect_uris, owner_user_id) live in 20_dtl_attrs.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Application reads
# ---------------------------------------------------------------------------

async def list_applications(
    conn: object,
    *,
    limit: int = 50,
    offset: int = 0,
    category_id: int | None = None,
) -> tuple[list[dict], int]:
    """Return (page, total) from v_applications."""
    conditions: list[str] = ["is_deleted = FALSE"]
    params: list = [limit, offset]

    if category_id is not None:
        params.append(category_id)
        conditions.append(f"category_id = ${len(params)}")

    where = "WHERE " + " AND ".join(conditions)

    rows = await conn.fetch(  # type: ignore[union-attr]
        f"""
        SELECT id, code, name, category_id, category_code, category_label,
               is_active, is_test, is_deleted,
               description, slug, icon_url, redirect_uris, owner_user_id,
               linked_product_count, active_token_count,
               created_by, updated_by, created_at, updated_at
          FROM "03_iam".v_applications
          {where}
         ORDER BY created_at DESC
         LIMIT $1 OFFSET $2
        """,
        *params,
    )

    count_conditions: list[str] = ["is_deleted = FALSE"]
    count_params: list = []
    if category_id is not None:
        count_params.append(category_id)
        count_conditions.append(f"category_id = ${len(count_params)}")
    count_where = "WHERE " + " AND ".join(count_conditions)

    total = await conn.fetchval(  # type: ignore[union-attr]
        f'SELECT COUNT(*) FROM "03_iam".v_applications {count_where}',
        *count_params,
    )
    return [dict(r) for r in rows], int(total)


async def get_application(conn: object, application_id: str) -> dict | None:
    """Return a single application from v_applications or None."""
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, code, name, category_id, category_code, category_label,
               is_active, is_test, is_deleted,
               description, slug, icon_url, redirect_uris, owner_user_id,
               linked_product_count, active_token_count,
               created_by, updated_by, created_at, updated_at
          FROM "03_iam".v_applications
         WHERE id = $1
        """,
        application_id,
    )
    return dict(row) if row else None


async def get_application_by_code(conn: object, code: str) -> dict | None:
    """Return a single application by code from v_applications or None."""
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, code, name, category_id, category_code, category_label,
               is_active, is_test, is_deleted,
               description, slug, icon_url, redirect_uris, owner_user_id,
               linked_product_count, active_token_count,
               created_by, updated_by, created_at, updated_at
          FROM "03_iam".v_applications
         WHERE code = $1
        """,
        code,
    )
    return dict(row) if row else None


async def check_code_exists(conn: object, code: str) -> bool:
    """Check if an application code already exists (non-deleted)."""
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT 1 FROM "03_iam"."10_fct_applications"
         WHERE code = $1 AND deleted_at IS NULL
        """,
        code,
    )
    return row is not None


async def check_category_type(
    conn: object, category_id: int, expected_type: str = "application"
) -> bool:
    """Check that the category_id belongs to the expected category_type."""
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id FROM "03_iam"."06_dim_categories"
         WHERE id = $1 AND category_type = $2
        """,
        category_id,
        expected_type,
    )
    return row is not None


# ---------------------------------------------------------------------------
# Application writes
# ---------------------------------------------------------------------------

async def insert_application(
    conn: object,
    *,
    application_id: str,
    code: str,
    name: str,
    category_id: int,
    actor_id: str,
) -> None:
    """Insert the application fact row."""
    await conn.execute(  # type: ignore[union-attr]
        """
        INSERT INTO "03_iam"."10_fct_applications"
            (id, code, name, category_id, created_by, updated_by,
             created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        application_id,
        code,
        name,
        category_id,
        actor_id,
    )


async def upsert_application_attr(
    conn: object,
    *,
    id: str,
    entity_type_id: int,
    entity_id: str,
    attr_def_id: int,
    value: object,
    value_column: str,
) -> None:
    """Upsert one EAV attribute row for an application.

    value_column must be one of: key_text, key_jsonb, key_smallint.
    The chosen column is set; the other two are set to NULL.
    """
    allowed = {"key_text", "key_jsonb", "key_smallint"}
    if value_column not in allowed:
        raise ValueError(f"value_column must be one of {allowed}, got {value_column!r}")

    key_text = value if value_column == "key_text" else None
    key_jsonb = value if value_column == "key_jsonb" else None
    key_smallint = value if value_column == "key_smallint" else None

    await conn.execute(  # type: ignore[union-attr]
        """
        INSERT INTO "03_iam"."20_dtl_attrs"
            (id, entity_type_id, entity_id, attr_def_id,
             key_text, key_jsonb, key_smallint, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (entity_id, attr_def_id)
        DO UPDATE SET key_text    = EXCLUDED.key_text,
                      key_jsonb   = EXCLUDED.key_jsonb,
                      key_smallint = EXCLUDED.key_smallint,
                      updated_at  = CURRENT_TIMESTAMP
        """,
        id,
        entity_type_id,
        entity_id,
        attr_def_id,
        key_text,
        key_jsonb,
        key_smallint,
    )


async def update_application_meta(
    conn: object,
    application_id: str,
    *,
    actor_id: str,
    name: str | None = None,
    is_active: bool | None = None,
) -> None:
    """Update fct row columns: name, is_active, updated_by/at."""
    sets = ["updated_by = $2", "updated_at = CURRENT_TIMESTAMP"]
    params: list = [application_id, actor_id]

    if name is not None:
        params.append(name)
        sets.append(f"name = ${len(params)}")

    if is_active is not None:
        params.append(is_active)
        sets.append(f"is_active = ${len(params)}")

    await conn.execute(  # type: ignore[union-attr]
        f"""
        UPDATE "03_iam"."10_fct_applications"
           SET {", ".join(sets)}
         WHERE id = $1
        """,
        *params,
    )


async def soft_delete_application(
    conn: object, application_id: str, *, actor_id: str
) -> None:
    """Soft-delete an application."""
    await conn.execute(  # type: ignore[union-attr]
        """
        UPDATE "03_iam"."10_fct_applications"
           SET deleted_at  = CURRENT_TIMESTAMP,
               is_active   = FALSE,
               updated_by  = $2,
               updated_at  = CURRENT_TIMESTAMP
         WHERE id = $1
        """,
        application_id,
        actor_id,
    )


# ---------------------------------------------------------------------------
# Product link reads
# ---------------------------------------------------------------------------

async def list_linked_products(
    conn: object,
    application_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return (page, total) of active product links for an application."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT p.id, p.code, p.name, p.category_id, p.category_code, p.category_label,
               p.is_sellable, p.is_active, p.is_deleted,
               p.description, p.slug, p.status, p.pricing_tier, p.owner_user_id,
               p.created_by, p.updated_by, p.created_at, p.updated_at,
               lnk.linked_at, lnk.linked_by
          FROM "03_iam"."40_lnk_application_products" lnk
          JOIN "03_iam".v_products p ON p.id = lnk.product_id
         WHERE lnk.application_id = $3
           AND lnk.is_active = TRUE
           AND p.is_deleted = FALSE
         ORDER BY lnk.linked_at DESC
         LIMIT $1 OFFSET $2
        """,
        limit,
        offset,
        application_id,
    )
    total = await conn.fetchval(  # type: ignore[union-attr]
        """
        SELECT COUNT(*)
          FROM "03_iam"."40_lnk_application_products" lnk
          JOIN "03_iam".v_products p ON p.id = lnk.product_id
         WHERE lnk.application_id = $1
           AND lnk.is_active = TRUE
           AND p.is_deleted = FALSE
        """,
        application_id,
    )
    return [dict(r) for r in rows], int(total)


async def get_link(
    conn: object, application_id: str, product_id: str
) -> dict | None:
    """Return an active application-product link row or None."""
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, application_id, product_id, linked_at, linked_by, is_active
          FROM "03_iam"."40_lnk_application_products"
         WHERE application_id = $1 AND product_id = $2 AND is_active = TRUE
        """,
        application_id,
        product_id,
    )
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Product link writes
# ---------------------------------------------------------------------------

async def insert_link(
    conn: object,
    *,
    link_id: str,
    application_id: str,
    product_id: str,
    actor_id: str,
) -> dict:
    """Insert an application-product link. Returns the inserted row."""
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        INSERT INTO "03_iam"."40_lnk_application_products"
            (id, application_id, product_id, linked_by, is_active, linked_at)
        VALUES ($1, $2, $3, $4, TRUE, CURRENT_TIMESTAMP)
        RETURNING id, application_id, product_id, linked_at, linked_by, is_active
        """,
        link_id,
        application_id,
        product_id,
        actor_id,
    )
    return dict(row)  # type: ignore[arg-type]


async def deactivate_link(
    conn: object, application_id: str, product_id: str
) -> bool:
    """Deactivate an application-product link. Returns True if a row was updated."""
    result = await conn.execute(  # type: ignore[union-attr]
        """
        UPDATE "03_iam"."40_lnk_application_products"
           SET is_active = FALSE
         WHERE application_id = $1 AND product_id = $2 AND is_active = TRUE
        """,
        application_id,
        product_id,
    )
    return result != "UPDATE 0"


async def list_active_product_ids_for_application(
    conn: object, application_id: str
) -> list[str]:
    """Return all active product_ids linked to an application."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT product_id
          FROM "03_iam"."40_lnk_application_products"
         WHERE application_id = $1 AND is_active = TRUE
        """,
        application_id,
    )
    return [r["product_id"] for r in rows]


# ---------------------------------------------------------------------------
# Token reads
# ---------------------------------------------------------------------------

async def list_tokens(conn: object, application_id: str) -> list[dict]:
    """Return all non-deleted tokens for an application (no raw hash)."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT id, application_id, application_code, application_name,
               name, token_prefix, is_active, expires_at, last_used_at,
               is_deleted, created_by, created_at
          FROM "03_iam".v_application_tokens
         WHERE application_id = $1 AND is_deleted = FALSE
         ORDER BY created_at DESC
        """,
        application_id,
    )
    return [dict(r) for r in rows]


async def get_token_by_id(
    conn: object, application_id: str, token_id: str
) -> dict | None:
    """Return a token from the safe view by id and application_id."""
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, application_id, application_code, application_name,
               name, token_prefix, is_active, expires_at, last_used_at,
               is_deleted, created_by, created_at
          FROM "03_iam".v_application_tokens
         WHERE id = $1 AND application_id = $2
        """,
        token_id,
        application_id,
    )
    return dict(row) if row else None


async def get_active_token_by_prefix(
    conn: object, application_id: str, token_prefix: str
) -> dict | None:
    """Return the raw fct row (includes token_hash) for hash verification.

    Must query the raw table — not the view — because the view intentionally
    omits token_hash.
    """
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, application_id, token_hash, is_active, expires_at
          FROM "03_iam"."10_fct_application_tokens"
         WHERE application_id = $1
           AND token_prefix = $2
           AND is_active = TRUE
           AND deleted_at IS NULL
        """,
        application_id,
        token_prefix,
    )
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Token writes
# ---------------------------------------------------------------------------

async def insert_token(
    conn: object,
    *,
    token_id: str,
    application_id: str,
    name: str,
    token_prefix: str,
    token_hash: str,
    expires_at: object,
    actor_id: str,
) -> None:
    """Insert a new application token (immutable — no updated_by/at)."""
    await conn.execute(  # type: ignore[union-attr]
        """
        INSERT INTO "03_iam"."10_fct_application_tokens"
            (id, application_id, name, token_prefix, token_hash,
             is_active, expires_at, created_by, created_at)
        VALUES ($1, $2, $3, $4, $5, TRUE, $6, $7, CURRENT_TIMESTAMP)
        """,
        token_id,
        application_id,
        name,
        token_prefix,
        token_hash,
        expires_at,
        actor_id,
    )


async def soft_delete_token(
    conn: object, application_id: str, token_id: str
) -> bool:
    """Soft-delete a token and set is_active=FALSE. Returns True if updated."""
    result = await conn.execute(  # type: ignore[union-attr]
        """
        UPDATE "03_iam"."10_fct_application_tokens"
           SET deleted_at = CURRENT_TIMESTAMP,
               is_active  = FALSE
         WHERE id = $1
           AND application_id = $2
           AND deleted_at IS NULL
        """,
        token_id,
        application_id,
    )
    return result != "UPDATE 0"


async def touch_token_last_used(conn: object, token_id: str) -> None:
    """Best-effort update of last_used_at for a token."""
    await conn.execute(  # type: ignore[union-attr]
        """
        UPDATE "03_iam"."10_fct_application_tokens"
           SET last_used_at = CURRENT_TIMESTAMP
         WHERE id = $1
        """,
        token_id,
    )


# ---------------------------------------------------------------------------
# Resolve-access support helpers
# ---------------------------------------------------------------------------

async def get_user_basic(conn: object, user_id: str) -> dict | None:
    """Return id, username, email for a user or None."""
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, username, email, is_active, is_deleted
          FROM "03_iam".v_users
         WHERE id = $1
        """,
        user_id,
    )
    return dict(row) if row else None


async def list_user_role_codes_by_tier(
    conn: object,
    *,
    user_id: str,
    org_id: str | None,
    workspace_id: str | None,
) -> dict:
    """Return {platform: [codes], org: [codes], workspace: [codes]} for a user."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT 'platform' AS tier, r.code
          FROM "03_iam"."40_lnk_user_platform_roles" upr
          JOIN "03_iam"."10_fct_platform_roles" r ON r.id = upr.platform_role_id
         WHERE upr.user_id = $1
           AND upr.is_active = TRUE
           AND r.is_active = TRUE

        UNION ALL

        SELECT 'org' AS tier, r.code
          FROM "03_iam"."40_lnk_user_org_roles" uor
          JOIN "03_iam"."10_fct_org_roles" r ON r.id = uor.org_role_id
         WHERE uor.user_id = $1
           AND ($2::text IS NULL OR uor.org_id = $2)
           AND uor.is_active = TRUE
           AND r.is_active = TRUE

        UNION ALL

        SELECT 'workspace' AS tier, r.code
          FROM "03_iam"."40_lnk_user_workspace_roles" uwr
          JOIN "03_iam"."10_fct_workspace_roles" r ON r.id = uwr.workspace_role_id
         WHERE uwr.user_id = $1
           AND ($3::text IS NULL OR uwr.workspace_id = $3)
           AND uwr.is_active = TRUE
           AND r.is_active = TRUE
        """,
        user_id,
        org_id,
        workspace_id,
    )
    result: dict = {"platform": [], "org": [], "workspace": []}
    for row in rows:
        tier = row["tier"]
        if tier in result:
            result[tier].append(row["code"])
    return result


async def list_user_groups_for_org(
    conn: object, *, user_id: str, org_id: str
) -> list[dict]:
    """Return groups the user belongs to within an org."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT g.id, g.org_id, g.name, g.slug, g.description
          FROM "03_iam".v_groups g
          JOIN "03_iam"."40_lnk_group_members" m
            ON m.group_id = g.id AND m.is_active = TRUE
         WHERE m.user_id = $1
           AND g.org_id = $2
           AND g.is_deleted = FALSE
        """,
        user_id,
        org_id,
    )
    return [dict(r) for r in rows]


async def list_products_by_ids(conn: object, product_ids: list[str]) -> list[dict]:
    """Return products matching the given ids (non-deleted only)."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT id, code, name, category_id, category_code, category_label,
               is_sellable, is_active, is_deleted,
               description, slug, status, pricing_tier, owner_user_id,
               created_by, updated_by, created_at, updated_at
          FROM "03_iam".v_products
         WHERE id = ANY($1) AND is_deleted = FALSE
        """,
        product_ids,
    )
    return [dict(r) for r in rows]


async def list_features_for_products(
    conn: object, product_ids: list[str]
) -> list[dict]:
    """Return active, non-deleted features for the given product ids."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT id, product_id, code, name, scope_code, category_code, is_active, is_deleted
          FROM "03_iam".v_features
         WHERE product_id = ANY($1)
           AND is_deleted = FALSE
           AND is_active = TRUE
        """,
        product_ids,
    )
    return [dict(r) for r in rows]


async def list_flags_for_products(
    conn: object, product_ids: list[str]
) -> list[dict]:
    """Return non-deleted flags for the given product ids."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT id, code, name, product_id, feature_id, scope_code,
               flag_type, default_value, is_active, is_deleted
          FROM "03_iam".v_feature_flags
         WHERE product_id = ANY($1)
           AND is_deleted = FALSE
        """,
        product_ids,
    )
    return [dict(r) for r in rows]
