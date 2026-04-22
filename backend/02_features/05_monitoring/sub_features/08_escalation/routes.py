"""Routes for monitoring.escalation — CRUD + ack endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from importlib import import_module

from . import service, repository, schemas

_resp = import_module("backend.01_core.response")
_errors = import_module("backend.01_core.errors")
_db = import_module("backend.01_core.database")
_auth = import_module("backend.02_features.03_iam.auth")
_audit = import_module("backend.02_features.04_audit.service")
_core_id = import_module("backend.01_core.id")
_oncall = import_module("backend.02_features.05_monitoring.sub_features.08_escalation.oncall")

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring.escalation"])


# ─ Escalation Policies ──────────────────────────────────────────────────

@router.get("/escalation-policies", status_code=200)
async def list_escalation_policies(
    is_active: bool | None = None,
    offset: int = 0,
    limit: int = 50,
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """List escalation policies for org."""
    try:
        policies, total = await repository.list_escalation_policies(
            conn, current_org_id, is_active=is_active, offset=offset, limit=limit
        )
        return _resp.success_list_response(
            [schemas.EscalationPolicyResponse.from_row(p).model_dump() for p in policies],
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalation-policies", status_code=201)
async def create_escalation_policy(
    req: schemas.EscalationPolicyCreateRequest,
    current_user_id: str = Depends(_auth.require_user),
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """Create escalation policy."""
    try:
        policy = await service.create_escalation_policy(conn, current_org_id, current_user_id, req)
        return _resp.success_response(schemas.EscalationPolicyResponse.from_row(policy).model_dump())
    except _errors.AppError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escalation-policies/{policy_id}", status_code=200)
async def get_escalation_policy(
    policy_id: str,
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """Get escalation policy by ID."""
    try:
        policy = await repository.get_escalation_policy(conn, policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        if policy["org_id"] != current_org_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN"})
        return _resp.success_response(schemas.EscalationPolicyResponse.from_row(policy).model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/escalation-policies/{policy_id}", status_code=200)
async def update_escalation_policy(
    policy_id: str,
    req: schemas.EscalationPolicyUpdateRequest,
    current_user_id: str = Depends(_auth.require_user),
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """Update escalation policy."""
    try:
        policy = await service.update_escalation_policy(
            conn, current_org_id, current_user_id, policy_id, req
        )
        return _resp.success_response(schemas.EscalationPolicyResponse.from_row(policy).model_dump())
    except _errors.AppError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/escalation-policies/{policy_id}", status_code=204)
async def delete_escalation_policy(
    policy_id: str,
    current_user_id: str = Depends(_auth.require_user),
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> None:
    """Delete escalation policy."""
    try:
        await service.delete_escalation_policy(conn, current_org_id, current_user_id, policy_id)
    except _errors.AppError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─ On-Call Schedules ────────────────────────────────────────────────────

@router.get("/oncall-schedules", status_code=200)
async def list_oncall_schedules(
    offset: int = 0,
    limit: int = 50,
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """List on-call schedules for org."""
    try:
        schedules, total = await repository.list_oncall_schedules(
            conn, current_org_id, offset=offset, limit=limit
        )
        return _resp.success_list_response(
            [schemas.OncallScheduleResponse.from_row(s).model_dump() for s in schedules],
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oncall-schedules", status_code=201)
async def create_oncall_schedule(
    req: schemas.OncallScheduleCreateRequest,
    current_user_id: str = Depends(_auth.require_user),
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """Create on-call schedule."""
    try:
        schedule = await service.create_oncall_schedule(conn, current_org_id, current_user_id, req)
        return _resp.success_response(schemas.OncallScheduleResponse.from_row(schedule).model_dump())
    except _errors.AppError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oncall-schedules/{schedule_id}", status_code=200)
async def get_oncall_schedule(
    schedule_id: str,
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """Get on-call schedule by ID."""
    try:
        schedule = await repository.get_oncall_schedule(conn, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        if schedule["org_id"] != current_org_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN"})
        return _resp.success_response(schemas.OncallScheduleResponse.from_row(schedule).model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/oncall-schedules/{schedule_id}", status_code=200)
async def update_oncall_schedule(
    schedule_id: str,
    req: schemas.OncallScheduleUpdateRequest,
    current_user_id: str = Depends(_auth.require_user),
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """Update on-call schedule."""
    try:
        schedule = await service.update_oncall_schedule(
            conn, current_org_id, current_user_id, schedule_id, req
        )
        return _resp.success_response(schemas.OncallScheduleResponse.from_row(schedule).model_dump())
    except _errors.AppError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/oncall-schedules/{schedule_id}", status_code=204)
async def delete_oncall_schedule(
    schedule_id: str,
    current_user_id: str = Depends(_auth.require_user),
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> None:
    """Delete on-call schedule."""
    try:
        await service.delete_oncall_schedule(conn, current_org_id, current_user_id, schedule_id)
    except _errors.AppError as e:
        raise HTTPException(status_code=e.status, detail={"code": e.code, "message": e.message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oncall-schedules/{schedule_id}/whoami", status_code=200)
async def oncall_whoami(
    schedule_id: str,
    current_user_id: str = Depends(_auth.require_user),
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """Get current on-call user for schedule."""
    try:
        schedule = await repository.get_oncall_schedule(conn, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        if schedule["org_id"] != current_org_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN"})

        members = schedule.get("members") or []
        now = _core_id.now_utc()
        oncall_user_id = _oncall.resolve_oncall(schedule, members, now)

        if not oncall_user_id:
            raise HTTPException(status_code=400, detail={"code": "NO_ONCALL"})

        # Fetch user details
        user = await conn.fetchrow(
            'SELECT id, email FROM "03_iam"."10_fct_users" WHERE id = $1',
            oncall_user_id,
        )
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND"})

        on_until = _oncall.next_handover(schedule, members, now)

        return _resp.success_response({
            "user_id": user["id"],
            "user_email": user["email"],
            "on_until": on_until.isoformat(),
            "schedule_id": schedule_id,
            "schedule_name": schedule["name"],
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─ Alert Acknowledgment ─────────────────────────────────────────────────
# PATCH /v1/monitoring/alerts/{alert_id} with body {"ack": true, "note": "..."}
# is the canonical way to acknowledge an alert (per PATCH-handles-state-changes).
# The path identifies the alert; the body describes the state transition.

@router.patch("/alerts/{alert_id}", status_code=200)
async def ack_alert(
    alert_id: str,
    req: schemas.AlertAckRequest,
    current_user_id: str = Depends(_auth.require_user),
    current_org_id: str = Depends(_auth.require_org),
    conn: Any = Depends(_db.get_connection),
) -> dict[str, Any]:
    """Acknowledge an alert, short-circuiting escalation.

    Body: `{"ack": true, "note": "..."}`. Only ack=true is supported today;
    un-ack is intentionally not modelled since `evt_` rows are append-only.
    """
    try:
        if not getattr(req, "ack", True):
            raise HTTPException(
                status_code=422,
                detail={"code": "UNSUPPORTED_OPERATION", "message": "only ack=true is supported"},
            )
        # Fetch alert
        alert = await conn.fetchrow(
            '''SELECT * FROM "05_monitoring"."60_evt_monitoring_alert_events"
               WHERE id = $1 AND org_id = $2''',
            alert_id, current_org_id,
        )
        if not alert:
            raise HTTPException(status_code=404, detail={"code": "ALERT_NOT_FOUND"})

        # Fetch escalation state if exists
        esc_state = await repository.get_escalation_state(conn, alert_id)
        if esc_state:
            now = _core_id.now_utc()
            await repository.update_escalation_state(
                conn,
                alert_id,
                ack_user_id=current_user_id,
                ack_at=now,
            )

        # Emit audit
        await _audit.emit_audit_event(
            conn,
            org_id=current_org_id,
            actor_id=current_user_id,
            category="monitoring.alert.ack",
            object_type="alert_event",
            object_id=alert_id,
            changes={"acked": True, "note": req.note or ""},
        )

        return _resp.success_response({
            "alert_id": alert_id,
            "acked_by": current_user_id,
            "acked_at": _core_id.now_utc().isoformat(),
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
