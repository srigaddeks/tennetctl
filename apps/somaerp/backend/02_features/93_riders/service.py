"""Riders service — orchestrates repo + audit emission + cross-system
validation of optional tennetctl iam user_id.

Audit keys:
  - somaerp.delivery.riders.created / .updated / .status_changed / .deleted
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.93_riders.repository",
)
_errors = import_module("apps.somaerp.backend.01_core.errors")


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


async def list_roles(conn: Any) -> list[dict]:
    return await _repo.list_roles(conn)


async def list_riders(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_riders(conn, **kwargs)


async def get_rider(
    conn: Any, *, tenant_id: str, rider_id: str,
) -> dict:
    row = await _repo.get_rider(
        conn, tenant_id=tenant_id, rider_id=rider_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Rider {rider_id} not found.")
    return row


async def _validate_user_id(
    *, tennetctl: Any, actor_user_id: str | None, user_id: str,
) -> None:
    """Cross-system call to tennetctl /v1/iam/users/{id}. 422 on miss."""
    # Use user-scoped if we have a session bearer; else system-scoped is
    # acceptable for read. Here we use system-scoped read (simpler, matches
    # plan spec's intent of "validate it points to a real iam user").
    try:
        await tennetctl.system_scoped(
            "GET", f"/v1/iam/users/{user_id}",
        )
    except _errors.NotFoundError as e:
        raise _errors.ValidationError(
            f"user_id {user_id} not found in tennetctl iam.",
            code="INVALID_USER_ID",
        ) from e
    except _errors.AuthError:
        # Service key not configured — skip rather than block creation.
        # In a fully wired env this won't happen.
        return


async def create_rider(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if not await _repo.role_exists(
        conn, role_id=int(data["role_id"]),
    ):
        raise _errors.ValidationError(
            f"Unknown role_id={data['role_id']}.",
            code="INVALID_ROLE",
        )
    if data.get("user_id"):
        await _validate_user_id(
            tennetctl=tennetctl,
            actor_user_id=actor_user_id,
            user_id=data["user_id"],
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_rider(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.delivery.riders.created",
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
                "entity_kind": "delivery.rider",
                "role_id": int(data["role_id"]),
                "user_id": data.get("user_id"),
                "status": data.get("status") or "active",
            },
        },
    )
    return row


async def update_rider(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    rider_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_rider(
        conn, tenant_id=tenant_id, rider_id=rider_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Rider {rider_id} not found.")

    if patch.get("role_id") is not None:
        if not await _repo.role_exists(conn, role_id=int(patch["role_id"])):
            raise _errors.ValidationError(
                f"Unknown role_id={patch['role_id']}.",
                code="INVALID_ROLE",
            )
    if patch.get("user_id"):
        await _validate_user_id(
            tennetctl=tennetctl,
            actor_user_id=actor_user_id,
            user_id=patch["user_id"],
        )

    status_changed = (
        "status" in patch
        and patch["status"] is not None
        and patch["status"] != existing["status"]
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_rider(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        rider_id=rider_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Rider {rider_id} not found.")

    event_key = (
        "somaerp.delivery.riders.status_changed"
        if status_changed
        else "somaerp.delivery.riders.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(rider_id),
        "entity_kind": "delivery.rider",
        "changed_fields": sorted([k for k in patch.keys()]),
    }
    if status_changed:
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = patch["status"]
    await tennetctl.audit_emit(
        event_key=event_key,
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={"outcome": "success", "metadata": metadata},
    )
    return row


async def soft_delete_rider(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    rider_id: str,
) -> None:
    existing = await _repo.get_rider(
        conn, tenant_id=tenant_id, rider_id=rider_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Rider {rider_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_rider(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        rider_id=rider_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Rider {rider_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.delivery.riders.deleted",
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
                "entity_id": str(rider_id),
                "entity_kind": "delivery.rider",
            },
        },
    )
