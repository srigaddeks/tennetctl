"""Product-line routes — /v1/somaerp/catalog/{categories,product-lines}.

Bulk POST supported: body may be a single object or an array.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module("apps.somaerp.backend.02_features.20_product_lines.service")
_schemas = import_module("apps.somaerp.backend.02_features.20_product_lines.schemas")
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp/catalog",
    tags=["catalog", "product_lines"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Categories (read-only) ───────────────────────────────────────────────

@router.get("/categories")
async def list_categories(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_categories(conn)
    validated = [_schemas.ProductCategoryOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(validated)


# ── Product lines ────────────────────────────────────────────────────────

@router.get("/product-lines")
async def list_product_lines(
    request: Request,
    category_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_product_lines(
            conn,
            tenant_id=workspace_id,
            category_id=category_id,
            status=status,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.ProductLineOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/product-lines", status_code=201)
async def create_product_line(
    request: Request,
    payload: Any = Body(...),
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.ProductLineCreate(**p) for p in payload]
    else:
        items = [_schemas.ProductLineCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_product_line(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(mode="python"),
            )
            created.append(
                _schemas.ProductLineOut(**row).model_dump(mode="json"),
            )
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/product-lines/{product_line_id}")
async def get_product_line(request: Request, product_line_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_product_line(
            conn, tenant_id=workspace_id, product_line_id=product_line_id,
        )
    return _response.ok(
        _schemas.ProductLineOut(**row).model_dump(mode="json"),
    )


@router.patch("/product-lines/{product_line_id}")
async def patch_product_line(
    request: Request,
    product_line_id: str,
    payload: _schemas.ProductLineUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_product_line(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            product_line_id=product_line_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.ProductLineOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/product-lines/{product_line_id}",
    status_code=204,
    response_class=Response,
)
async def delete_product_line(
    request: Request, product_line_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_product_line(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            product_line_id=product_line_id,
        )
    return Response(status_code=204)
