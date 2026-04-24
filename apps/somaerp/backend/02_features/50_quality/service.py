"""Quality service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.quality.checkpoints.created / .updated / .status_changed / .deleted
  - somaerp.quality.checks.recorded (evt_* is append-only — `.recorded`
    communicates the immutability of the event row)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.50_quality.repository",
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


# ── Lookups ─────────────────────────────────────────────────────────────


async def list_check_types(conn: Any) -> list[dict]:
    return await _repo.list_check_types(conn)


async def list_stages(conn: Any) -> list[dict]:
    return await _repo.list_stages(conn)


async def list_outcomes(conn: Any) -> list[dict]:
    return await _repo.list_outcomes(conn)


# ── Scope-ref validation helper ────────────────────────────────────────


async def _validate_scope_ref(
    conn: Any, *, tenant_id: str, scope_kind: str, scope_ref_id: str | None,
) -> None:
    if scope_kind == "universal":
        if scope_ref_id is not None:
            raise _errors.ValidationError(
                "scope_ref_id must be null when scope_kind='universal'.",
                code="INVALID_SCOPE_REF",
            )
        return
    if scope_ref_id is None:
        raise _errors.ValidationError(
            f"scope_ref_id is required when scope_kind='{scope_kind}'.",
            code="INVALID_SCOPE_REF",
        )
    if scope_kind == "recipe_step":
        ok = await _repo.recipe_step_exists_for_tenant(
            conn, tenant_id=tenant_id, step_id=scope_ref_id,
        )
    elif scope_kind == "raw_material":
        ok = await _repo.raw_material_exists_for_tenant(
            conn, tenant_id=tenant_id, raw_material_id=scope_ref_id,
        )
    elif scope_kind == "kitchen":
        ok = await _repo.kitchen_exists_for_tenant(
            conn, tenant_id=tenant_id, kitchen_id=scope_ref_id,
        )
    elif scope_kind == "product":
        ok = await _repo.product_exists_for_tenant(
            conn, tenant_id=tenant_id, product_id=scope_ref_id,
        )
    else:
        raise _errors.ValidationError(
            f"Unknown scope_kind={scope_kind}.",
            code="INVALID_SCOPE_KIND",
        )
    if not ok:
        raise _errors.ValidationError(
            f"scope_ref_id={scope_ref_id} not found for scope_kind={scope_kind}.",
            code="INVALID_SCOPE_REF",
        )


# ── Checkpoints ─────────────────────────────────────────────────────────


async def list_checkpoints(
    conn: Any,
    *,
    tenant_id: str,
    scope_kind: str | None = None,
    scope_ref_id: str | None = None,
    stage_id: int | None = None,
    check_type_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_checkpoints(
        conn,
        tenant_id=tenant_id,
        scope_kind=scope_kind,
        scope_ref_id=scope_ref_id,
        stage_id=stage_id,
        check_type_id=check_type_id,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_checkpoint(
    conn: Any, *, tenant_id: str, checkpoint_id: str,
) -> dict:
    row = await _repo.get_checkpoint(
        conn, tenant_id=tenant_id, checkpoint_id=checkpoint_id,
    )
    if row is None:
        raise _errors.NotFoundError(
            f"Checkpoint {checkpoint_id} not found.",
        )
    return row


async def create_checkpoint(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if not await _repo.stage_exists(conn, stage_id=int(data["stage_id"])):
        raise _errors.ValidationError(
            f"Unknown stage_id={data['stage_id']}.",
            code="INVALID_STAGE",
        )
    if not await _repo.check_type_exists(
        conn, check_type_id=int(data["check_type_id"]),
    ):
        raise _errors.ValidationError(
            f"Unknown check_type_id={data['check_type_id']}.",
            code="INVALID_CHECK_TYPE",
        )
    await _validate_scope_ref(
        conn,
        tenant_id=tenant_id,
        scope_kind=data["scope_kind"],
        scope_ref_id=data.get("scope_ref_id"),
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_checkpoint(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.quality.checkpoints.created",
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
                "entity_kind": "quality.checkpoint",
                "stage_code": row.get("stage_code"),
                "check_type_code": row.get("check_type_code"),
                "scope_kind": data["scope_kind"],
            },
        },
    )
    return row


async def update_checkpoint(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    checkpoint_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_checkpoint(
        conn, tenant_id=tenant_id, checkpoint_id=checkpoint_id,
    )
    if existing is None:
        raise _errors.NotFoundError(
            f"Checkpoint {checkpoint_id} not found.",
        )

    if patch.get("stage_id") is not None:
        if not await _repo.stage_exists(conn, stage_id=int(patch["stage_id"])):
            raise _errors.ValidationError(
                f"Unknown stage_id={patch['stage_id']}.",
                code="INVALID_STAGE",
            )
    if patch.get("check_type_id") is not None:
        if not await _repo.check_type_exists(
            conn, check_type_id=int(patch["check_type_id"]),
        ):
            raise _errors.ValidationError(
                f"Unknown check_type_id={patch['check_type_id']}.",
                code="INVALID_CHECK_TYPE",
            )

    # If scope_kind or scope_ref_id changes, revalidate.
    new_scope_kind = patch.get("scope_kind") or existing["scope_kind"]
    new_scope_ref_id = patch["scope_ref_id"] if "scope_ref_id" in patch else existing.get("scope_ref_id")
    if (
        patch.get("scope_kind") is not None
        or "scope_ref_id" in patch
    ):
        await _validate_scope_ref(
            conn,
            tenant_id=tenant_id,
            scope_kind=new_scope_kind,
            scope_ref_id=new_scope_ref_id,
        )

    new_status = patch.get("status")
    status_changed = new_status is not None and new_status != existing["status"]

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_checkpoint(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        checkpoint_id=checkpoint_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(
            f"Checkpoint {checkpoint_id} not found.",
        )

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    event_key = (
        "somaerp.quality.checkpoints.status_changed"
        if status_changed
        else "somaerp.quality.checkpoints.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(checkpoint_id),
        "entity_kind": "quality.checkpoint",
        "changed_fields": changed_fields,
    }
    if status_changed:
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = new_status

    if changed_fields:
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


async def soft_delete_checkpoint(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    checkpoint_id: str,
) -> None:
    existing = await _repo.get_checkpoint(
        conn, tenant_id=tenant_id, checkpoint_id=checkpoint_id,
    )
    if existing is None:
        raise _errors.NotFoundError(
            f"Checkpoint {checkpoint_id} not found.",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_checkpoint(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        checkpoint_id=checkpoint_id,
    )
    if not ok:
        raise _errors.NotFoundError(
            f"Checkpoint {checkpoint_id} not found.",
        )

    await tennetctl.audit_emit(
        event_key="somaerp.quality.checkpoints.deleted",
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
                "entity_id": str(checkpoint_id),
                "entity_kind": "quality.checkpoint",
            },
        },
    )


# ── Checks (append-only) ────────────────────────────────────────────────


async def list_checks(
    conn: Any,
    *,
    tenant_id: str,
    checkpoint_id: str | None = None,
    batch_id: str | None = None,
    outcome_id: int | None = None,
    kitchen_id: str | None = None,
    raw_material_lot: str | None = None,
    performed_by_user_id: str | None = None,
    ts_after: Any = None,
    ts_before: Any = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    return await _repo.list_checks(
        conn,
        tenant_id=tenant_id,
        checkpoint_id=checkpoint_id,
        batch_id=batch_id,
        outcome_id=outcome_id,
        kitchen_id=kitchen_id,
        raw_material_lot=raw_material_lot,
        performed_by_user_id=performed_by_user_id,
        ts_after=ts_after,
        ts_before=ts_before,
        limit=limit,
        offset=offset,
    )


async def get_check(
    conn: Any, *, tenant_id: str, check_id: str,
) -> dict:
    row = await _repo.get_check(
        conn, tenant_id=tenant_id, check_id=check_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Check {check_id} not found.")
    return row


async def create_check(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if actor_user_id is None:
        raise _errors.AuthError(
            "Recording a QC check requires an authenticated user.",
        )

    checkpoint = await _repo.get_checkpoint(
        conn, tenant_id=tenant_id, checkpoint_id=data["checkpoint_id"],
    )
    if checkpoint is None:
        raise _errors.ValidationError(
            f"Checkpoint {data['checkpoint_id']} not found for this tenant.",
            code="INVALID_CHECKPOINT",
        )

    if not await _repo.outcome_exists(
        conn, outcome_id=int(data["outcome_id"]),
    ):
        raise _errors.ValidationError(
            f"Unknown outcome_id={data['outcome_id']}.",
            code="INVALID_OUTCOME",
        )

    if data.get("kitchen_id") is not None:
        ok = await _repo.kitchen_exists_for_tenant(
            conn, tenant_id=tenant_id, kitchen_id=data["kitchen_id"],
        )
        if not ok:
            raise _errors.ValidationError(
                f"Kitchen {data['kitchen_id']} not found for this tenant.",
                code="INVALID_KITCHEN",
            )

    row = await _repo.create_check(
        conn,
        tenant_id=tenant_id,
        performed_by_user_id=actor_user_id,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.quality.checks.recorded",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "operational",
                "entity_id": str(row.get("id")),
                "entity_kind": "quality.check",
                "checkpoint_id": str(data["checkpoint_id"]),
                "outcome_code": row.get("outcome_code"),
                "stage_code": row.get("stage_code"),
                "check_type_code": row.get("check_type_code"),
                "batch_id": str(data["batch_id"]) if data.get("batch_id") else None,
                "raw_material_lot": data.get("raw_material_lot"),
            },
        },
    )
    return row
