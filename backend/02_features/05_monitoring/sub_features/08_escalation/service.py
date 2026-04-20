"""Service layer for monitoring.escalation — business logic + audit."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from importlib import import_module

from . import repository
from . import oncall as oncall_module
from . import schemas

_errors = import_module("backend.01_core.errors")
_audit = import_module("backend.02_features.04_audit.service")
_core_id = import_module("backend.01_core.id")
_iam_repo = import_module("backend.02_features.03_iam.repository")


async def create_escalation_policy(
    conn: Any,
    org_id: str,
    user_id: str,
    req: schemas.EscalationPolicyCreateRequest,
) -> dict[str, Any]:
    """Create escalation policy with audit."""
    # Check for existing policy name in org
    existing = await conn.fetchrow(
        '''SELECT id FROM "05_monitoring"."10_fct_monitoring_escalation_policies"
           WHERE org_id = $1 AND name = $2 AND deleted_at IS NULL''',
        org_id, req.name,
    )
    if existing:
        raise _errors.AppError(
            "POLICY_NAME_EXISTS",
            f"Escalation policy '{req.name}' already exists in this org.",
            409,
        )

    # Convert steps to repo format
    steps_data = []
    for step in req.steps:
        step_dict = {
            "kind": step.kind,
            "target_ref": step.target_ref or {},
            "wait_seconds": step.wait_seconds,
            "priority": step.priority,
        }
        steps_data.append(step_dict)

    # Create policy
    policy = await repository.create_escalation_policy(
        conn,
        org_id=org_id,
        name=req.name,
        description=req.description,
        steps=steps_data,
        user_id=user_id,
    )

    # Audit
    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.escalation.policy_create",
        object_type="escalation_policy",
        object_id=policy["id"],
        changes={"name": req.name, "steps_count": len(steps_data)},
    )

    return policy


async def update_escalation_policy(
    conn: Any,
    org_id: str,
    user_id: str,
    policy_id: str,
    req: schemas.EscalationPolicyUpdateRequest,
) -> dict[str, Any]:
    """Update escalation policy with audit."""
    # Fetch existing
    policy = await repository.get_escalation_policy(conn, policy_id)
    if not policy:
        raise _errors.AppError("NOT_FOUND", f"Escalation policy '{policy_id}' not found.", 404)
    if policy["org_id"] != org_id:
        raise _errors.AppError("FORBIDDEN", "Cannot access policy from another org.", 403)

    # Check name uniqueness if changing
    if req.name and req.name != policy["name"]:
        existing = await conn.fetchrow(
            '''SELECT id FROM "05_monitoring"."10_fct_monitoring_escalation_policies"
               WHERE org_id = $1 AND name = $2 AND deleted_at IS NULL AND id <> $3''',
            org_id, req.name, policy_id,
        )
        if existing:
            raise _errors.AppError(
                "POLICY_NAME_EXISTS",
                f"Escalation policy '{req.name}' already exists in this org.",
                409,
            )

    # Convert steps if provided
    steps_data = None
    if req.steps:
        steps_data = []
        for step in req.steps:
            step_dict = {
                "kind": step.kind,
                "target_ref": step.target_ref or {},
                "wait_seconds": step.wait_seconds,
                "priority": step.priority,
            }
            steps_data.append(step_dict)

    # Update policy
    updated = await repository.update_escalation_policy(
        conn,
        policy_id=policy_id,
        name=req.name,
        description=req.description,
        is_active=req.is_active,
        steps=steps_data,
        user_id=user_id,
    )

    # Audit
    changes = {}
    if req.name:
        changes["name"] = req.name
    if req.description is not None:
        changes["description"] = req.description
    if req.is_active is not None:
        changes["is_active"] = req.is_active
    if steps_data:
        changes["steps_count"] = len(steps_data)

    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.escalation.policy_update",
        object_type="escalation_policy",
        object_id=policy_id,
        changes=changes,
    )

    return updated


async def delete_escalation_policy(
    conn: Any,
    org_id: str,
    user_id: str,
    policy_id: str,
) -> None:
    """Delete escalation policy with guard against in-use policies."""
    # Fetch existing
    policy = await repository.get_escalation_policy(conn, policy_id)
    if not policy:
        raise _errors.AppError("NOT_FOUND", f"Escalation policy '{policy_id}' not found.", 404)
    if policy["org_id"] != org_id:
        raise _errors.AppError("FORBIDDEN", "Cannot access policy from another org.", 403)

    # Check if in use
    in_use = await repository.is_policy_in_use(conn, policy_id)
    if in_use:
        raise _errors.AppError(
            "IN_USE",
            "Cannot delete escalation policy referenced by active alert rules.",
            409,
        )

    # Soft delete
    await repository.soft_delete_escalation_policy(conn, policy_id)

    # Audit
    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.escalation.policy_delete",
        object_type="escalation_policy",
        object_id=policy_id,
        changes={"deleted": True},
    )


# ── On-call Schedules ───────────────────────────────────────────────────

async def create_oncall_schedule(
    conn: Any,
    org_id: str,
    user_id: str,
    req: schemas.OncallScheduleCreateRequest,
) -> dict[str, Any]:
    """Create on-call schedule with audit."""
    # Check for existing schedule name in org
    existing = await conn.fetchrow(
        '''SELECT id FROM "05_monitoring"."10_fct_monitoring_oncall_schedules"
           WHERE org_id = $1 AND name = $2 AND deleted_at IS NULL''',
        org_id, req.name,
    )
    if existing:
        raise _errors.AppError(
            "SCHEDULE_NAME_EXISTS",
            f"On-call schedule '{req.name}' already exists in this org.",
            409,
        )

    # Validate all members exist
    for member_id in req.members:
        user = await _iam_repo.get_user(conn, member_id)
        if not user:
            raise _errors.AppError(
                "USER_NOT_FOUND",
                f"User '{member_id}' not found.",
                404,
            )

    # Create schedule
    schedule = await repository.create_oncall_schedule(
        conn,
        org_id=org_id,
        name=req.name,
        description=req.description,
        timezone=req.timezone,
        rotation_period_seconds=req.rotation_period_seconds,
        rotation_start=req.rotation_start,
        member_ids=req.members,
        user_id=user_id,
    )

    # Audit
    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.oncall.schedule_create",
        object_type="oncall_schedule",
        object_id=schedule["id"],
        changes={"name": req.name, "member_count": len(req.members)},
    )

    return schedule


async def update_oncall_schedule(
    conn: Any,
    org_id: str,
    user_id: str,
    schedule_id: str,
    req: schemas.OncallScheduleUpdateRequest,
) -> dict[str, Any]:
    """Update on-call schedule with audit."""
    # Fetch existing
    schedule = await repository.get_oncall_schedule(conn, schedule_id)
    if not schedule:
        raise _errors.AppError("NOT_FOUND", f"On-call schedule '{schedule_id}' not found.", 404)
    if schedule["org_id"] != org_id:
        raise _errors.AppError("FORBIDDEN", "Cannot access schedule from another org.", 403)

    # Check name uniqueness if changing
    if req.name and req.name != schedule["name"]:
        existing = await conn.fetchrow(
            '''SELECT id FROM "05_monitoring"."10_fct_monitoring_oncall_schedules"
               WHERE org_id = $1 AND name = $2 AND deleted_at IS NULL AND id <> $3''',
            org_id, req.name, schedule_id,
        )
        if existing:
            raise _errors.AppError(
                "SCHEDULE_NAME_EXISTS",
                f"On-call schedule '{req.name}' already exists in this org.",
                409,
            )

    # Validate members if provided
    if req.members:
        for member_id in req.members:
            user = await _iam_repo.get_user(conn, member_id)
            if not user:
                raise _errors.AppError(
                    "USER_NOT_FOUND",
                    f"User '{member_id}' not found.",
                    404,
                )

    # Update schedule
    updated = await repository.update_oncall_schedule(
        conn,
        schedule_id=schedule_id,
        name=req.name,
        description=req.description,
        timezone=req.timezone,
        rotation_period_seconds=req.rotation_period_seconds,
        rotation_start=req.rotation_start,
        member_ids=req.members,
        user_id=user_id,
    )

    # Audit
    changes = {}
    if req.name:
        changes["name"] = req.name
    if req.description is not None:
        changes["description"] = req.description
    if req.timezone:
        changes["timezone"] = req.timezone
    if req.rotation_period_seconds:
        changes["rotation_period_seconds"] = req.rotation_period_seconds
    if req.rotation_start:
        changes["rotation_start"] = req.rotation_start.isoformat()
    if req.members:
        changes["member_count"] = len(req.members)

    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.oncall.schedule_update",
        object_type="oncall_schedule",
        object_id=schedule_id,
        changes=changes,
    )

    return updated


async def delete_oncall_schedule(
    conn: Any,
    org_id: str,
    user_id: str,
    schedule_id: str,
) -> None:
    """Delete on-call schedule with audit."""
    # Fetch existing
    schedule = await repository.get_oncall_schedule(conn, schedule_id)
    if not schedule:
        raise _errors.AppError("NOT_FOUND", f"On-call schedule '{schedule_id}' not found.", 404)
    if schedule["org_id"] != org_id:
        raise _errors.AppError("FORBIDDEN", "Cannot access schedule from another org.", 403)

    # Soft delete
    await repository.soft_delete_oncall_schedule(conn, schedule_id)

    # Audit
    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.oncall.schedule_delete",
        object_type="oncall_schedule",
        object_id=schedule_id,
        changes={"deleted": True},
    )


__all__ = [
    "create_escalation_policy",
    "update_escalation_policy",
    "delete_escalation_policy",
    "create_oncall_schedule",
    "update_oncall_schedule",
    "delete_oncall_schedule",
]
