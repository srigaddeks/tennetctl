"""Routes for monitoring.escalation — CRUD + ack endpoint.

Uses a top-level ``request: Request`` parameter on every handler and calls
``_auth.require_*`` / acquires the pool inline. Avoids FastAPI's sub-dep
``Request`` quirk that surfaced when these were written with
``Depends(_auth.require_org)`` (it leaked ``request`` as a query param).
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from importlib import import_module

from . import service, repository, schemas

_resp = import_module("backend.01_core.response")
_errors = import_module("backend.01_core.errors")
_auth = import_module("backend.02_features.03_iam.auth")
_audit = import_module("backend.02_features.04_audit.service")
_core_id = import_module("backend.01_core.id")
_oncall = import_module("backend.02_features.05_monitoring.sub_features.08_escalation.oncall")

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring.escalation"])


def _handle_app_error(e: Exception) -> HTTPException:
    """Normalize AppError → HTTPException; wrap everything else as 500."""
    if isinstance(e, _errors.AppError):
        return HTTPException(
            status_code=getattr(e, "status", 500),
            detail={"code": e.code, "message": e.message},
        )
    return HTTPException(status_code=500, detail=str(e))


# ─ Escalation Policies ──────────────────────────────────────────────────

@router.get("/escalation-policies", status_code=200)
async def list_escalation_policies(
    request: Request,
    is_active: bool | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """List escalation policies for org."""
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            policies, total = await repository.list_escalation_policies(
                conn, org_id, is_active=is_active, offset=offset, limit=limit,
            )
        return _resp.success_list_response(
            [schemas.EscalationPolicyResponse.from_row(p).model_dump() for p in policies],
            total=total, limit=limit, offset=offset,
        )
    except Exception as e:
        raise _handle_app_error(e)


@router.post("/escalation-policies", status_code=201)
async def create_escalation_policy(
    request: Request,
    req: schemas.EscalationPolicyCreateRequest,
) -> dict[str, Any]:
    """Create escalation policy."""
    user_id = _auth.require_user(request)
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            policy = await service.create_escalation_policy(conn, org_id, user_id, req)
        return _resp.success_response(schemas.EscalationPolicyResponse.from_row(policy).model_dump())
    except Exception as e:
        raise _handle_app_error(e)


@router.get("/escalation-policies/{policy_id}", status_code=200)
async def get_escalation_policy(request: Request, policy_id: str) -> dict[str, Any]:
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            policy = await repository.get_escalation_policy(conn, policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        if policy["org_id"] != org_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN"})
        return _resp.success_response(schemas.EscalationPolicyResponse.from_row(policy).model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_app_error(e)


@router.patch("/escalation-policies/{policy_id}", status_code=200)
async def update_escalation_policy(
    request: Request,
    policy_id: str,
    req: schemas.EscalationPolicyUpdateRequest,
) -> dict[str, Any]:
    user_id = _auth.require_user(request)
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            policy = await service.update_escalation_policy(
                conn, org_id, user_id, policy_id, req,
            )
        return _resp.success_response(schemas.EscalationPolicyResponse.from_row(policy).model_dump())
    except Exception as e:
        raise _handle_app_error(e)


@router.delete("/escalation-policies/{policy_id}", status_code=204)
async def delete_escalation_policy(request: Request, policy_id: str) -> None:
    user_id = _auth.require_user(request)
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            await service.delete_escalation_policy(conn, org_id, user_id, policy_id)
    except Exception as e:
        raise _handle_app_error(e)


# ─ On-Call Schedules ────────────────────────────────────────────────────

@router.get("/oncall-schedules", status_code=200)
async def list_oncall_schedules(
    request: Request,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            schedules, total = await repository.list_oncall_schedules(
                conn, org_id, offset=offset, limit=limit,
            )
        return _resp.success_list_response(
            [schemas.OncallScheduleResponse.from_row(s).model_dump() for s in schedules],
            total=total, limit=limit, offset=offset,
        )
    except Exception as e:
        raise _handle_app_error(e)


@router.post("/oncall-schedules", status_code=201)
async def create_oncall_schedule(
    request: Request,
    req: schemas.OncallScheduleCreateRequest,
) -> dict[str, Any]:
    user_id = _auth.require_user(request)
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            schedule = await service.create_oncall_schedule(conn, org_id, user_id, req)
        return _resp.success_response(schemas.OncallScheduleResponse.from_row(schedule).model_dump())
    except Exception as e:
        raise _handle_app_error(e)


@router.get("/oncall-schedules/{schedule_id}", status_code=200)
async def get_oncall_schedule(request: Request, schedule_id: str) -> dict[str, Any]:
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            schedule = await repository.get_oncall_schedule(conn, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
        if schedule["org_id"] != org_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN"})
        return _resp.success_response(schemas.OncallScheduleResponse.from_row(schedule).model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_app_error(e)


@router.patch("/oncall-schedules/{schedule_id}", status_code=200)
async def update_oncall_schedule(
    request: Request,
    schedule_id: str,
    req: schemas.OncallScheduleUpdateRequest,
) -> dict[str, Any]:
    user_id = _auth.require_user(request)
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            schedule = await service.update_oncall_schedule(
                conn, org_id, user_id, schedule_id, req,
            )
        return _resp.success_response(schemas.OncallScheduleResponse.from_row(schedule).model_dump())
    except Exception as e:
        raise _handle_app_error(e)


@router.delete("/oncall-schedules/{schedule_id}", status_code=204)
async def delete_oncall_schedule(request: Request, schedule_id: str) -> None:
    user_id = _auth.require_user(request)
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            await service.delete_oncall_schedule(conn, org_id, user_id, schedule_id)
    except Exception as e:
        raise _handle_app_error(e)


@router.get("/oncall-schedules/{schedule_id}/whoami", status_code=200)
async def oncall_whoami(request: Request, schedule_id: str) -> dict[str, Any]:
    _auth.require_user(request)
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            schedule = await repository.get_oncall_schedule(conn, schedule_id)
            if not schedule:
                raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
            if schedule["org_id"] != org_id:
                raise HTTPException(status_code=403, detail={"code": "FORBIDDEN"})

            members = schedule.get("members") or []
            now = _core_id.now_utc()
            oncall_user_id = _oncall.resolve_oncall(schedule, members, now)

            if not oncall_user_id:
                raise HTTPException(status_code=400, detail={"code": "NO_ONCALL"})

            user = await conn.fetchrow(
                'SELECT id FROM "03_iam"."12_fct_users" WHERE id = $1',
                oncall_user_id,
            )
            if not user:
                raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND"})
            email = await conn.fetchval(
                'SELECT email FROM "03_iam".v_users WHERE id = $1',
                oncall_user_id,
            )

        on_until = _oncall.next_handover(schedule, members, now)
        return _resp.success_response({
            "user_id": user["id"],
            "user_email": email,
            "on_until": on_until.isoformat(),
            "schedule_id": schedule_id,
            "schedule_name": schedule["name"],
        })
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_app_error(e)


# ─ Alert Acknowledgment (PATCH /alerts/{id}) ────────────────────────────
# Per the PATCH-handles-all-state-changes rule, the previous
# ``POST /alerts/{id}/ack`` was retired.

@router.patch("/alerts/{alert_id}", status_code=200)
async def ack_alert(
    request: Request,
    alert_id: str,
    req: schemas.AlertAckRequest,
) -> dict[str, Any]:
    """Acknowledge an alert. Body: ``{"ack": true, "note": "..."}``."""
    user_id = _auth.require_user(request)
    org_id = _auth.require_org(request)
    pool = request.app.state.pool
    try:
        if not getattr(req, "ack", True):
            raise HTTPException(
                status_code=422,
                detail={"code": "UNSUPPORTED_OPERATION", "message": "only ack=true is supported"},
            )
        async with pool.acquire() as conn:
            alert = await conn.fetchrow(
                'SELECT * FROM "05_monitoring"."60_evt_monitoring_alert_events" '
                'WHERE id = $1 AND org_id = $2',
                alert_id, org_id,
            )
            if not alert:
                raise HTTPException(status_code=404, detail={"code": "ALERT_NOT_FOUND"})

            esc_state = await repository.get_escalation_state(conn, alert_id)
            if esc_state:
                now = _core_id.now_utc()
                await repository.update_escalation_state(
                    conn, alert_id,
                    ack_user_id=user_id, ack_at=now,
                )

            await _audit.emit_audit_event(
                conn, pool=pool,
                org_id=org_id, actor_id=user_id,
                category="monitoring.alert.ack",
                object_type="alert_event", object_id=alert_id,
                changes={"acked": True, "note": req.note or ""},
            )

        return _resp.success_response({
            "alert_id": alert_id,
            "acked_by": user_id,
            "acked_at": _core_id.now_utc().isoformat(),
        })
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_app_error(e)


__all__ = ["router"]
