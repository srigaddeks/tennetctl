"""Locations service — orchestrates repo writes + audit emission.

Pattern per apps/somaerp/03_docs/04_integration/02_audit_emission.md:
every mutation emits exactly one audit event after the repo call succeeds.
Audit emission is best-effort — fail-open per TennetctlClient.audit_emit.

Setup-mode bootstrap (no user_id yet) is allowed: category=setup bypasses
the mandatory actor_user_id enforcement at the tennetctl ingest layer.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somaerp.backend.02_features.10_locations.repository")
_errors = import_module("apps.somaerp.backend.01_core.errors")


# ── Regions (read-only, no audit) ─────────────────────────────────────────

async def list_regions(conn: Any) -> list[dict]:
    return await _repo.list_regions(conn)


# ── Locations ─────────────────────────────────────────────────────────────

async def list_locations(
    conn: Any,
    *,
    tenant_id: str,
    region_id: int | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_locations(
        conn,
        tenant_id=tenant_id,
        region_id=region_id,
        q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_location(
    conn: Any, *, tenant_id: str, location_id: str,
) -> dict:
    row = await _repo.get_location(
        conn, tenant_id=tenant_id, location_id=location_id,
    )
    if row is None:
        # Cross-tenant access returns 404, not 403 (no data leak).
        raise _errors.NotFoundError(f"Location {location_id} not found.")
    return row


async def create_location(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    # Validate region exists (422 if not).
    region = await _repo.get_region(conn, region_id=data["region_id"])
    if region is None:
        raise _errors.ValidationError(
            f"Unknown region_id={data['region_id']}.",
            code="INVALID_REGION",
        )

    # Setup-mode bootstrap: when no user_id is present we stamp a system
    # sentinel and mark the audit category as 'setup' (bypass-approved).
    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_location(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.geography.locations.created",
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
                "entity_kind": "geography.location",
                "region_id": data["region_id"],
                "slug": data["slug"],
            },
        },
    )
    return row


async def update_location(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    location_id: str,
    patch: dict,
) -> dict:
    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_location(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        location_id=location_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Location {location_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.geography.locations.updated",
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
                "entity_id": str(location_id),
                "entity_kind": "geography.location",
                "changed_fields": sorted(
                    [k for k, v in patch.items() if v is not None],
                ),
            },
        },
    )
    return row


async def soft_delete_location(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    location_id: str,
) -> None:
    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_location(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        location_id=location_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Location {location_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.geography.locations.deleted",
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
                "entity_id": str(location_id),
                "entity_kind": "geography.location",
            },
        },
    )
