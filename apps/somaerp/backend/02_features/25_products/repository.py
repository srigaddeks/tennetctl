"""Products + variants + tags repository — raw asyncpg against "11_somaerp".

Notes:
- create_product inserts fct_products + lnk_product_tags rows in one tx.
- update_product diffs tag_codes (caller passes replacement set) and returns
  `tags_added` / `tags_removed` / `has_field_change` so the service layer can
  emit one audit event per tag change.
- create_variant and update_variant atomically clear any prior default variant
  when is_default=True toggles on, inside the same tx.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Tags (read-only) ─────────────────────────────────────────────────────

async def list_tags(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_product_tags "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def get_tag_ids_by_codes(
    conn: Any, *, codes: list[str],
) -> dict[str, int]:
    """Return {code: id} for all supplied codes that exist (non-deprecated)."""
    if not codes:
        return {}
    rows = await conn.fetch(
        f"SELECT id, code FROM {SCHEMA}.dim_product_tags "
        "WHERE code = ANY($1::text[]) AND deprecated_at IS NULL",
        list(codes),
    )
    return {r["code"]: r["id"] for r in rows}


# ── Products CRUD ────────────────────────────────────────────────────────

async def list_products(
    conn: Any,
    *,
    tenant_id: str,
    product_line_id: str | None = None,
    tag_code: str | None = None,
    status: str | None = None,
    currency_code: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if product_line_id is not None:
        params.append(product_line_id)
        clauses.append(f"product_line_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if currency_code is not None:
        params.append(currency_code)
        clauses.append(f"currency_code = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"name ILIKE ${len(params)}")
    if tag_code:
        # tag_code may be comma-separated; any match.
        codes = [c.strip() for c in tag_code.split(",") if c.strip()]
        if codes:
            params.append(codes)
            clauses.append(f"tag_codes && ${len(params)}::text[]")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_products "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_product(
    conn: Any, *, tenant_id: str, product_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_products "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_id, tenant_id,
    )
    return dict(row) if row else None


async def product_line_exists(
    conn: Any, *, tenant_id: str, product_line_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_product_lines "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_line_id, tenant_id,
    )
    return row is not None


async def create_product(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
    tag_code_to_id: dict[str, int],
) -> dict:
    """Atomic: insert fct_products row + lnk_product_tags rows in one tx."""
    new_id = _id.uuid7()
    async with conn.transaction():
        await conn.execute(
            f"INSERT INTO {SCHEMA}.fct_products "
            "(id, tenant_id, product_line_id, name, slug, description, "
            " target_benefit, default_serving_size_ml, default_shelf_life_hours, "
            " target_cogs_amount, default_selling_price, currency_code, "
            " status, properties, created_by, updated_by) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$15)",
            new_id,
            tenant_id,
            data["product_line_id"],
            data["name"],
            data["slug"],
            data.get("description"),
            data.get("target_benefit"),
            data.get("default_serving_size_ml"),
            data.get("default_shelf_life_hours"),
            data.get("target_cogs_amount"),
            data.get("default_selling_price"),
            data["currency_code"],
            data.get("status") or "active",
            data.get("properties") or {},
            actor_user_id,
        )
        for _code, tag_id in tag_code_to_id.items():
            await conn.execute(
                f"INSERT INTO {SCHEMA}.lnk_product_tags "
                "(tenant_id, product_id, tag_id, created_by) "
                "VALUES ($1, $2, $3, $4)",
                tenant_id, new_id, tag_id, actor_user_id,
            )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_products WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_PRODUCT_UPDATABLE_COLUMNS = (
    "product_line_id",
    "name",
    "slug",
    "description",
    "target_benefit",
    "default_serving_size_ml",
    "default_shelf_life_hours",
    "target_cogs_amount",
    "default_selling_price",
    "currency_code",
    "status",
    "properties",
)


async def update_product(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    product_id: str,
    patch: dict,
    new_tag_codes: list[str] | None,
    tag_code_to_id: dict[str, int],
) -> dict[str, Any]:
    """Atomic: update fct_products fields + diff tag links.

    Returns dict with keys:
      row                -> refreshed v_products row (or None)
      has_field_change   -> bool (any non-tag field updated)
      tags_added         -> list[str] (codes newly attached)
      tags_removed       -> list[str] (codes detached)
    """
    async with conn.transaction():
        # ── Field update ────────────────────────────────────────────
        sets: list[str] = []
        params: list[Any] = []
        for col in _PRODUCT_UPDATABLE_COLUMNS:
            if col in patch and patch[col] is not None:
                params.append(patch[col])
                sets.append(f"{col} = ${len(params)}")
        has_field_change = bool(sets)
        if sets:
            params.append(actor_user_id)
            sets.append(f"updated_by = ${len(params)}")
            sets.append("updated_at = CURRENT_TIMESTAMP")
            params.append(product_id)
            params.append(tenant_id)
            sql = (
                f"UPDATE {SCHEMA}.fct_products SET {', '.join(sets)} "
                f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
                "AND deleted_at IS NULL"
            )
            result = await conn.execute(sql, *params)
            if not result.endswith(" 1"):
                return {
                    "row": None,
                    "has_field_change": False,
                    "tags_added": [],
                    "tags_removed": [],
                }

        # ── Tag diff ────────────────────────────────────────────────
        tags_added: list[str] = []
        tags_removed: list[str] = []
        if new_tag_codes is not None:
            current_rows = await conn.fetch(
                f"SELECT t.code FROM {SCHEMA}.lnk_product_tags lt "
                f"JOIN {SCHEMA}.dim_product_tags t ON t.id = lt.tag_id "
                "WHERE lt.product_id = $1 AND lt.tenant_id = $2",
                product_id, tenant_id,
            )
            current = {r["code"] for r in current_rows}
            new_set = set(new_tag_codes)
            added = sorted(new_set - current)
            removed = sorted(current - new_set)
            for code in added:
                tag_id = tag_code_to_id.get(code)
                if tag_id is None:
                    continue
                await conn.execute(
                    f"INSERT INTO {SCHEMA}.lnk_product_tags "
                    "(tenant_id, product_id, tag_id, created_by) "
                    "VALUES ($1, $2, $3, $4) "
                    "ON CONFLICT DO NOTHING",
                    tenant_id, product_id, tag_id, actor_user_id,
                )
                tags_added.append(code)
            for code in removed:
                await conn.execute(
                    f"DELETE FROM {SCHEMA}.lnk_product_tags lt "
                    f"USING {SCHEMA}.dim_product_tags t "
                    "WHERE lt.tenant_id = $1 AND lt.product_id = $2 "
                    "AND lt.tag_id = t.id AND t.code = $3",
                    tenant_id, product_id, code,
                )
                tags_removed.append(code)

    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_products WHERE id = $1", product_id,
    )
    return {
        "row": dict(row) if row else None,
        "has_field_change": has_field_change,
        "tags_added": tags_added,
        "tags_removed": tags_removed,
    }


async def soft_delete_product(
    conn: Any, *, tenant_id: str, actor_user_id: str, product_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_products "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, product_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Product variants ─────────────────────────────────────────────────────

async def list_variants(
    conn: Any,
    *,
    tenant_id: str,
    product_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    clauses = ["tenant_id = $1", "product_id = $2"]
    params: list[Any] = [tenant_id, product_id]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    sql = (
        f"SELECT * FROM {SCHEMA}.v_product_variants "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY is_default DESC, created_at ASC"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_variant(
    conn: Any, *, tenant_id: str, product_id: str, variant_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_product_variants "
        "WHERE id = $1 AND tenant_id = $2 AND product_id = $3 "
        "AND deleted_at IS NULL",
        variant_id, tenant_id, product_id,
    )
    return dict(row) if row else None


async def create_variant(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    product_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    async with conn.transaction():
        if data.get("is_default"):
            # Atomically clear any prior default variant in same tx.
            await conn.execute(
                f"UPDATE {SCHEMA}.fct_product_variants "
                "SET is_default = FALSE, "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = $1 "
                "WHERE tenant_id = $2 AND product_id = $3 "
                "AND is_default = TRUE AND deleted_at IS NULL",
                actor_user_id, tenant_id, product_id,
            )
        await conn.execute(
            f"INSERT INTO {SCHEMA}.fct_product_variants "
            "(id, tenant_id, product_id, name, slug, serving_size_ml, "
            " selling_price, currency_code, is_default, status, properties, "
            " created_by, updated_by) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$12)",
            new_id,
            tenant_id,
            product_id,
            data["name"],
            data["slug"],
            data.get("serving_size_ml"),
            data.get("selling_price"),
            data["currency_code"],
            bool(data.get("is_default")),
            data.get("status") or "active",
            data.get("properties") or {},
            actor_user_id,
        )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_product_variants WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_VARIANT_UPDATABLE_COLUMNS = (
    "name",
    "slug",
    "serving_size_ml",
    "selling_price",
    "currency_code",
    "is_default",
    "status",
    "properties",
)


async def update_variant(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    product_id: str,
    variant_id: str,
    patch: dict,
) -> dict | None:
    async with conn.transaction():
        # If toggling is_default TRUE, first clear the prior default variant
        # (excluding this row) in same tx.
        if patch.get("is_default") is True:
            await conn.execute(
                f"UPDATE {SCHEMA}.fct_product_variants "
                "SET is_default = FALSE, "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = $1 "
                "WHERE tenant_id = $2 AND product_id = $3 "
                "AND is_default = TRUE AND id <> $4 AND deleted_at IS NULL",
                actor_user_id, tenant_id, product_id, variant_id,
            )

        sets: list[str] = []
        params: list[Any] = []
        for col in _VARIANT_UPDATABLE_COLUMNS:
            if col in patch and patch[col] is not None:
                params.append(patch[col])
                sets.append(f"{col} = ${len(params)}")
        if not sets:
            row = await conn.fetchrow(
                f"SELECT * FROM {SCHEMA}.v_product_variants "
                "WHERE id = $1 AND tenant_id = $2 AND product_id = $3 "
                "AND deleted_at IS NULL",
                variant_id, tenant_id, product_id,
            )
            return dict(row) if row else None
        params.append(actor_user_id)
        sets.append(f"updated_by = ${len(params)}")
        sets.append("updated_at = CURRENT_TIMESTAMP")
        params.append(variant_id)
        params.append(tenant_id)
        params.append(product_id)
        sql = (
            f"UPDATE {SCHEMA}.fct_product_variants SET {', '.join(sets)} "
            f"WHERE id = ${len(params) - 2} AND tenant_id = ${len(params) - 1} "
            f"AND product_id = ${len(params)} AND deleted_at IS NULL"
        )
        result = await conn.execute(sql, *params)
        if not result.endswith(" 1"):
            return None
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_product_variants WHERE id = $1", variant_id,
    )
    return dict(row) if row else None


async def soft_delete_variant(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    product_id: str,
    variant_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_product_variants "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND product_id = $4 "
        "AND deleted_at IS NULL",
        actor_user_id, variant_id, tenant_id, product_id,
    )
    return result.endswith(" 1")
