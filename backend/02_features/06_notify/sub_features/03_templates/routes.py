"""Routes for notify.templates."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module(
    "backend.02_features.06_notify.sub_features.03_templates.schemas"
)
_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.03_templates.service"
)

TemplateCreate = _schemas.TemplateCreate
TemplateUpdate = _schemas.TemplateUpdate
TemplateBodiesUpsert = _schemas.TemplateBodiesUpsert
TemplateRow = _schemas.TemplateRow
TestSendRequest = _schemas.TestSendRequest

router = APIRouter(tags=["notify.templates"])


def _build_ctx(request: Request, pool: Any) -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", None) or _core_id.uuid7(),
        audit_category="system",
        extras={"pool": pool},
    )


@router.get("/v1/notify/templates", status_code=200)
async def list_templates_route(request: Request, org_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.list_templates(conn, org_id=org_id)
    data = [TemplateRow(**r).model_dump() for r in items]
    return _response.success({"items": data, "total": len(data)})


@router.post("/v1/notify/templates", status_code=201)
async def create_template_route(request: Request, body: TemplateCreate) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    data = body.model_dump()
    # Convert bodies list to plain dicts for repo
    if data.get("bodies"):
        data["bodies"] = [b.model_dump() if hasattr(b, "model_dump") else b for b in (body.bodies or [])]
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.create_template(conn, pool, ctx2, data=data)
    return _response.success(TemplateRow(**row).model_dump())


@router.get("/v1/notify/templates/{template_id}", status_code=200)
async def get_template_route(request: Request, template_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_template(conn, template_id=template_id)
    if row is None:
        raise _errors.NotFoundError(f"template {template_id!r} not found")
    return _response.success(TemplateRow(**row).model_dump())


@router.patch("/v1/notify/templates/{template_id}", status_code=200)
async def update_template_route(
    request: Request, template_id: str, body: TemplateUpdate
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.update_template(
            conn, pool, ctx2, template_id=template_id,
            data=body.model_dump(exclude_none=True),
        )
    if row is None:
        raise _errors.NotFoundError(f"template {template_id!r} not found")
    return _response.success(TemplateRow(**row).model_dump())


@router.put("/v1/notify/templates/{template_id}/bodies", status_code=200)
async def upsert_bodies_route(
    request: Request, template_id: str, body: TemplateBodiesUpsert
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    bodies = [b.model_dump() for b in body.bodies]
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.upsert_bodies(conn, pool, ctx2, template_id=template_id, bodies=bodies)
    if row is None:
        raise _errors.NotFoundError(f"template {template_id!r} not found")
    return _response.success(TemplateRow(**row).model_dump())


@router.post("/v1/notify/templates/{template_id}/test-send", status_code=200)
async def test_send_route(
    request: Request, template_id: str, body: TestSendRequest
) -> dict:
    pool = request.app.state.pool
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError("NO_VAULT", "Vault not configured — cannot send email.", 503)
    async with pool.acquire() as conn:
        sent_to = await _service.send_test_email(
            conn,
            template_id=template_id,
            to_email=body.to_email,
            context=body.context,
            vault=vault,
        )
    return _response.success({"sent_to": sent_to})


@router.delete("/v1/notify/templates/{template_id}", status_code=204)
async def delete_template_route(request: Request, template_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        deleted = await _service.delete_template(conn, pool, ctx2, template_id=template_id)
    if not deleted:
        raise _errors.NotFoundError(f"template {template_id!r} not found")
