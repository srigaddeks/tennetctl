"""Subscriptions routes — /v1/somaerp/subscriptions/*.

Endpoints:
  GET    /frequencies
  GET    /plans                           (filter status, frequency_id, q)
  POST   /plans
  GET    /plans/{plan_id}                 (returns {plan, items})
  PATCH  /plans/{plan_id}
  DELETE /plans/{plan_id}
  GET    /plans/{plan_id}/items
  POST   /plans/{plan_id}/items
  PATCH  /plans/{plan_id}/items/{item_id}
  DELETE /plans/{plan_id}/items/{item_id}
  GET    /                                (subscriptions list)
  POST   /
  GET    /{sub_id}
  PATCH  /{sub_id}
  DELETE /{sub_id}
  GET    /{sub_id}/events
"""

from __future__ import annotations

from datetime import date
from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.85_subscriptions.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.85_subscriptions.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/subscriptions",
    tags=["subscriptions"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


def _parse_date(val: str | None) -> date | None:
    if val is None or val == "":
        return None
    try:
        return date.fromisoformat(val)
    except ValueError as e:
        raise _errors.ValidationError(
            f"Invalid ISO date: {val}", code="INVALID_DATE",
        ) from e


# ── Frequencies ────────────────────────────────────────────────────────


@router.get("/frequencies")
async def list_frequencies(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_frequencies(conn)
    data = [
        _schemas.SubscriptionFrequencyOut(**r).model_dump(mode="json")
        for r in rows
    ]
    return _response.ok(data)


# ── Plans ─────────────────────────────────────────────────────────────


@router.get("/plans")
async def list_plans(
    request: Request,
    status: str | None = Query(default=None),
    frequency_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_plans(
            conn,
            tenant_id=workspace_id,
            status=status,
            frequency_id=frequency_id,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [
        _schemas.SubscriptionPlanOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("/plans", status_code=201)
async def create_plan(
    request: Request, payload: _schemas.SubscriptionPlanCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_plan(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(),
        )
    return _response.ok(
        _schemas.SubscriptionPlanOut(**row).model_dump(mode="json"),
    )


@router.get("/plans/{plan_id}")
async def get_plan(request: Request, plan_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        detail = await _service.get_plan_detail(
            conn, tenant_id=workspace_id, plan_id=plan_id,
        )
    plan_out = _schemas.SubscriptionPlanOut(**detail["plan"]).model_dump(
        mode="json",
    )
    items_out = [
        _schemas.SubscriptionPlanItemOut(**i).model_dump(mode="json")
        for i in detail["items"]
    ]
    return _response.ok({"plan": plan_out, "items": items_out})


@router.patch("/plans/{plan_id}")
async def patch_plan(
    request: Request,
    plan_id: str,
    payload: _schemas.SubscriptionPlanUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_plan(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            plan_id=plan_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(
        _schemas.SubscriptionPlanOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/plans/{plan_id}", status_code=204, response_class=Response,
)
async def delete_plan(request: Request, plan_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_plan(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            plan_id=plan_id,
        )
    return Response(status_code=204)


# ── Plan items ───────────────────────────────────────────────────────


@router.get("/plans/{plan_id}/items")
async def list_plan_items(request: Request, plan_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_plan_items(
            conn, tenant_id=workspace_id, plan_id=plan_id,
        )
    data = [
        _schemas.SubscriptionPlanItemOut(**r).model_dump(mode="json")
        for r in rows
    ]
    return _response.ok(data)


@router.post("/plans/{plan_id}/items", status_code=201)
async def add_plan_item(
    request: Request,
    plan_id: str,
    payload: _schemas.SubscriptionPlanItemCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_plan_item(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            plan_id=plan_id,
            data=payload.model_dump(),
        )
    return _response.ok(
        _schemas.SubscriptionPlanItemOut(**row).model_dump(mode="json"),
    )


@router.patch("/plans/{plan_id}/items/{item_id}")
async def patch_plan_item(
    request: Request,
    plan_id: str,
    item_id: str,
    payload: _schemas.SubscriptionPlanItemUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_plan_item(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            plan_id=plan_id,
            item_id=item_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(
        _schemas.SubscriptionPlanItemOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/plans/{plan_id}/items/{item_id}",
    status_code=204,
    response_class=Response,
)
async def delete_plan_item(
    request: Request, plan_id: str, item_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_plan_item(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            plan_id=plan_id,
            item_id=item_id,
        )
    return Response(status_code=204)


# ── Subscriptions ────────────────────────────────────────────────────


@router.get("")
async def list_subscriptions(
    request: Request,
    customer_id: str | None = Query(default=None),
    plan_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_date_from: str | None = Query(default=None),
    start_date_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_subscriptions(
            conn,
            tenant_id=workspace_id,
            customer_id=customer_id,
            plan_id=plan_id,
            status=status,
            start_date_from=_parse_date(start_date_from),
            start_date_to=_parse_date(start_date_to),
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [
        _schemas.SubscriptionOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("", status_code=201)
async def create_subscription(
    request: Request, payload: _schemas.SubscriptionCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_subscription(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.SubscriptionOut(**row).model_dump(mode="json"),
    )


@router.get("/{subscription_id}")
async def get_subscription(
    request: Request, subscription_id: str,
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_subscription(
            conn, tenant_id=workspace_id, subscription_id=subscription_id,
        )
    return _response.ok(
        _schemas.SubscriptionOut(**row).model_dump(mode="json"),
    )


@router.patch("/{subscription_id}")
async def patch_subscription(
    request: Request,
    subscription_id: str,
    payload: _schemas.SubscriptionUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_subscription(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            subscription_id=subscription_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.SubscriptionOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/{subscription_id}", status_code=204, response_class=Response,
)
async def delete_subscription(
    request: Request, subscription_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_subscription(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            subscription_id=subscription_id,
        )
    return Response(status_code=204)


@router.get("/{subscription_id}/events")
async def list_events(
    request: Request, subscription_id: str,
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_subscription_events(
            conn, tenant_id=workspace_id, subscription_id=subscription_id,
        )
    data = [
        _schemas.SubscriptionEventOut(**r).model_dump(mode="json")
        for r in rows
    ]
    return _response.ok(data)
