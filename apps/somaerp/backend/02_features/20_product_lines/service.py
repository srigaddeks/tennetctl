"""Product lines service — orchestrates repo writes + audit emission.

Audit key routing:
  - status changed  -> somaerp.catalog.product_lines.status_changed
  - other field(s)  -> somaerp.catalog.product_lines.updated
  - status + other  -> .status_changed (status dominant)

DELETE guard: reject with 422 DEPENDENCY_VIOLATION if any non-deleted
fct_products reference the line.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somaerp.backend.02_features.20_product_lines.repository")
_errors = import_module("apps.somaerp.backend.01_core.errors")


# ── Categories (read-only, no audit) ─────────────────────────────────────

async def list_categories(conn: Any) -> list[dict]:
    return await _repo.list_categories(conn)


# ── Product lines ────────────────────────────────────────────────────────

async def list_product_lines(
    conn: Any,
    *,
    tenant_id: str,
    category_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_product_lines(
        conn,
        tenant_id=tenant_id,
        category_id=category_id,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_product_line(
    conn: Any, *, tenant_id: str, product_line_id: str,
) -> dict:
    row = await _repo.get_product_line(
        conn, tenant_id=tenant_id, product_line_id=product_line_id,
    )
    if row is None:
        raise _errors.NotFoundError(
            f"Product line {product_line_id} not found.",
        )
    return row


async def create_product_line(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    # Validate category exists (422 if not).
    cat = await _repo.get_category(conn, category_id=data["category_id"])
    if cat is None:
        raise _errors.ValidationError(
            f"Unknown category_id={data['category_id']}.",
            code="INVALID_CATEGORY",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_product_line(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.catalog.product_lines.created",
        scope={
            "user_id": actor_user_id,
            "session_id": session_id,
            "org_id": org_id,
            "workspace_id": tenant_id,
        },
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(row.get("id")),
                "entity_kind": "catalog.product_line",
                "category_id": data["category_id"],
                "slug": data["slug"],
            },
        },
    )
    return row


async def update_product_line(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    product_line_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_product_line(
        conn, tenant_id=tenant_id, product_line_id=product_line_id,
    )
    if existing is None:
        raise _errors.NotFoundError(
            f"Product line {product_line_id} not found.",
        )

    if patch.get("category_id") is not None and patch["category_id"] != existing["category_id"]:
        cat = await _repo.get_category(conn, category_id=patch["category_id"])
        if cat is None:
            raise _errors.ValidationError(
                f"Unknown category_id={patch['category_id']}.",
                code="INVALID_CATEGORY",
            )

    new_status = patch.get("status")
    status_changed = new_status is not None and new_status != existing["status"]

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_product_line(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        product_line_id=product_line_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(
            f"Product line {product_line_id} not found.",
        )

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    event_key = (
        "somaerp.catalog.product_lines.status_changed"
        if status_changed
        else "somaerp.catalog.product_lines.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(product_line_id),
        "entity_kind": "catalog.product_line",
        "changed_fields": changed_fields,
    }
    if status_changed:
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = new_status

    await tennetctl.audit_emit(
        event_key=event_key,
        scope={
            "user_id": actor_user_id,
            "session_id": session_id,
            "org_id": org_id,
            "workspace_id": tenant_id,
        },
        payload={"outcome": "success", "metadata": metadata},
    )
    return row


async def soft_delete_product_line(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    product_line_id: str,
) -> None:
    existing = await _repo.get_product_line(
        conn, tenant_id=tenant_id, product_line_id=product_line_id,
    )
    if existing is None:
        raise _errors.NotFoundError(
            f"Product line {product_line_id} not found.",
        )

    # DELETE guard: no active products may reference the line.
    if await _repo.has_active_products(
        conn, tenant_id=tenant_id, product_line_id=product_line_id,
    ):
        raise _errors.ValidationError(
            f"Product line {product_line_id} has active products; "
            "archive them before deleting the line.",
            code="DEPENDENCY_VIOLATION",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_product_line(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        product_line_id=product_line_id,
    )
    if not ok:
        raise _errors.NotFoundError(
            f"Product line {product_line_id} not found.",
        )

    await tennetctl.audit_emit(
        event_key="somaerp.catalog.product_lines.deleted",
        scope={
            "user_id": actor_user_id,
            "session_id": session_id,
            "org_id": org_id,
            "workspace_id": tenant_id,
        },
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(product_line_id),
                "entity_kind": "catalog.product_line",
            },
        },
    )
