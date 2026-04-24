"""Products + variants + tags service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.catalog.products.created                (on POST)
  - somaerp.catalog.products.updated                (fields changed, not status)
  - somaerp.catalog.products.status_changed         (status changed)
  - somaerp.catalog.products.deleted                (on DELETE)
  - somaerp.catalog.product_tags.attached           (one per added tag)
  - somaerp.catalog.product_tags.detached           (one per removed tag)
  - somaerp.catalog.product_variants.created/.updated/.deleted

Tag diff rules:
  - PATCH may include tag_codes; service diffs vs existing.
  - If ONLY tags changed (no non-tag fields), DO NOT emit products.updated.
  - If status changed, emit status_changed instead of updated.

TODO(56-07): DELETE on a product with active recipes must return 422
DEPENDENCY_VIOLATION. fct_recipes does not exist yet; guard lands with 56-07.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somaerp.backend.02_features.25_products.repository")
_pl_repo = import_module(
    "apps.somaerp.backend.02_features.20_product_lines.repository",
)
_errors = import_module("apps.somaerp.backend.01_core.errors")


# ── Tags (read-only) ─────────────────────────────────────────────────────

async def list_tags(conn: Any) -> list[dict]:
    return await _repo.list_tags(conn)


# ── Helpers ──────────────────────────────────────────────────────────────

async def _resolve_tag_codes(
    conn: Any, *, codes: list[str],
) -> dict[str, int]:
    """Resolve codes -> tag_ids; raise 422 if any are unknown."""
    if not codes:
        return {}
    mapping = await _repo.get_tag_ids_by_codes(conn, codes=codes)
    unknown = [c for c in codes if c not in mapping]
    if unknown:
        raise _errors.ValidationError(
            f"Unknown tag_codes: {unknown}.", code="INVALID_TAG_CODE",
        )
    return mapping


def _scope(
    *, actor_user_id: str | None, session_id: str | None,
    org_id: str | None, tenant_id: str,
) -> dict:
    return {
        "user_id": actor_user_id,
        "session_id": session_id,
        "org_id": org_id,
        "workspace_id": tenant_id,
    }


# ── Products ─────────────────────────────────────────────────────────────

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
    return await _repo.list_products(
        conn,
        tenant_id=tenant_id,
        product_line_id=product_line_id,
        tag_code=tag_code,
        status=status,
        currency_code=currency_code,
        q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_product(
    conn: Any, *, tenant_id: str, product_id: str,
) -> dict:
    row = await _repo.get_product(
        conn, tenant_id=tenant_id, product_id=product_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Product {product_id} not found.")
    return row


async def create_product(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    # Validate product_line exists for this tenant.
    if not await _repo.product_line_exists(
        conn, tenant_id=tenant_id, product_line_id=data["product_line_id"],
    ):
        raise _errors.ValidationError(
            f"Product line {data['product_line_id']} not found for this tenant.",
            code="INVALID_PRODUCT_LINE",
        )

    tag_codes = list(data.get("tag_codes") or [])
    tag_map = await _resolve_tag_codes(conn, codes=tag_codes)

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_product(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
        tag_code_to_id=tag_map,
    )

    scope = _scope(
        actor_user_id=actor_user_id,
        session_id=session_id,
        org_id=org_id,
        tenant_id=tenant_id,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.catalog.products.created",
        scope=scope,
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(row.get("id")),
                "entity_kind": "catalog.product",
                "product_line_id": str(data["product_line_id"]),
                "currency_code": data["currency_code"],
                "slug": data["slug"],
            },
        },
    )
    for code in tag_codes:
        await tennetctl.audit_emit(
            event_key="somaerp.catalog.product_tags.attached",
            scope=scope,
            payload={
                "outcome": "success",
                "metadata": {
                    "category": "setup" if is_setup else "operational",
                    "entity_id": str(row.get("id")),
                    "entity_kind": "catalog.product_tag",
                    "product_id": str(row.get("id")),
                    "tag_code": code,
                },
            },
        )
    return row


async def update_product(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    product_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_product(
        conn, tenant_id=tenant_id, product_id=product_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Product {product_id} not found.")

    # If product_line_id is changing, validate it.
    if patch.get("product_line_id") and patch["product_line_id"] != existing["product_line_id"]:
        if not await _repo.product_line_exists(
            conn, tenant_id=tenant_id, product_line_id=patch["product_line_id"],
        ):
            raise _errors.ValidationError(
                f"Product line {patch['product_line_id']} not found for this tenant.",
                code="INVALID_PRODUCT_LINE",
            )

    # Separate tag_codes from field patch.
    new_tag_codes = patch.pop("tag_codes", None)
    tag_map: dict[str, int] = {}
    if new_tag_codes is not None:
        tag_map = await _resolve_tag_codes(conn, codes=list(new_tag_codes))

    new_status = patch.get("status")
    status_changed = new_status is not None and new_status != existing["status"]

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    result = await _repo.update_product(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        product_id=product_id,
        patch=patch,
        new_tag_codes=new_tag_codes,
        tag_code_to_id=tag_map,
    )
    row = result["row"]
    if row is None:
        raise _errors.NotFoundError(f"Product {product_id} not found.")

    scope = _scope(
        actor_user_id=actor_user_id,
        session_id=session_id,
        org_id=org_id,
        tenant_id=tenant_id,
    )

    # Emit field-change event only if non-tag fields changed.
    if result["has_field_change"]:
        changed_fields = sorted([k for k, v in patch.items() if v is not None])
        event_key = (
            "somaerp.catalog.products.status_changed"
            if status_changed
            else "somaerp.catalog.products.updated"
        )
        metadata: dict[str, Any] = {
            "category": "setup" if is_setup else "operational",
            "entity_id": str(product_id),
            "entity_kind": "catalog.product",
            "changed_fields": changed_fields,
        }
        if status_changed:
            metadata["previous_status"] = existing["status"]
            metadata["new_status"] = new_status
        await tennetctl.audit_emit(
            event_key=event_key,
            scope=scope,
            payload={"outcome": "success", "metadata": metadata},
        )

    # Per-tag-change events.
    for code in result["tags_added"]:
        await tennetctl.audit_emit(
            event_key="somaerp.catalog.product_tags.attached",
            scope=scope,
            payload={
                "outcome": "success",
                "metadata": {
                    "category": "setup" if is_setup else "operational",
                    "entity_id": str(product_id),
                    "entity_kind": "catalog.product_tag",
                    "product_id": str(product_id),
                    "tag_code": code,
                },
            },
        )
    for code in result["tags_removed"]:
        await tennetctl.audit_emit(
            event_key="somaerp.catalog.product_tags.detached",
            scope=scope,
            payload={
                "outcome": "success",
                "metadata": {
                    "category": "setup" if is_setup else "operational",
                    "entity_id": str(product_id),
                    "entity_kind": "catalog.product_tag",
                    "product_id": str(product_id),
                    "tag_code": code,
                },
            },
        )

    return row


async def soft_delete_product(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    product_id: str,
) -> None:
    existing = await _repo.get_product(
        conn, tenant_id=tenant_id, product_id=product_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Product {product_id} not found.")

    # TODO(56-07): block delete if any fct_recipes reference this product with
    # status != 'archived'. fct_recipes does not exist yet.

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_product(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        product_id=product_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Product {product_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.catalog.products.deleted",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(product_id),
                "entity_kind": "catalog.product",
                "product_line_id": str(existing.get("product_line_id")),
            },
        },
    )


# ── Product variants ─────────────────────────────────────────────────────

async def list_variants(
    conn: Any,
    *,
    tenant_id: str,
    product_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    # Ensure the product exists for tenant (404 if not).
    prod = await _repo.get_product(
        conn, tenant_id=tenant_id, product_id=product_id,
    )
    if prod is None:
        raise _errors.NotFoundError(f"Product {product_id} not found.")
    return await _repo.list_variants(
        conn,
        tenant_id=tenant_id,
        product_id=product_id,
        include_deleted=include_deleted,
    )


async def get_variant(
    conn: Any, *, tenant_id: str, product_id: str, variant_id: str,
) -> dict:
    row = await _repo.get_variant(
        conn, tenant_id=tenant_id, product_id=product_id,
        variant_id=variant_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")
    return row


async def create_variant(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    product_id: str,
    data: dict,
) -> dict:
    # Cross-tenant guard.
    prod = await _repo.get_product(
        conn, tenant_id=tenant_id, product_id=product_id,
    )
    if prod is None:
        raise _errors.ValidationError(
            f"Product {product_id} not found for this tenant.",
            code="INVALID_PRODUCT",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_variant(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        product_id=product_id,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.catalog.product_variants.created",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(row.get("id")),
                "entity_kind": "catalog.product_variant",
                "product_id": str(product_id),
                "is_default": bool(row.get("is_default")),
            },
        },
    )
    return row


async def update_variant(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    product_id: str,
    variant_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_variant(
        conn, tenant_id=tenant_id, product_id=product_id,
        variant_id=variant_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_variant(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        product_id=product_id,
        variant_id=variant_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    await tennetctl.audit_emit(
        event_key="somaerp.catalog.product_variants.updated",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(variant_id),
                "entity_kind": "catalog.product_variant",
                "product_id": str(product_id),
                "changed_fields": changed_fields,
            },
        },
    )
    return row


async def soft_delete_variant(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    product_id: str,
    variant_id: str,
) -> None:
    existing = await _repo.get_variant(
        conn, tenant_id=tenant_id, product_id=product_id,
        variant_id=variant_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_variant(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        product_id=product_id,
        variant_id=variant_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.catalog.product_variants.deleted",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(variant_id),
                "entity_kind": "catalog.product_variant",
                "product_id": str(product_id),
            },
        },
    )
