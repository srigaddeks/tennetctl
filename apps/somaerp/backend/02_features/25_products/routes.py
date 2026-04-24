"""Product routes — /v1/somaerp/catalog/{tags,products,products/.../variants}."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module("apps.somaerp.backend.02_features.25_products.service")
_schemas = import_module("apps.somaerp.backend.02_features.25_products.schemas")
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp/catalog",
    tags=["catalog", "products"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Tags (read-only) ─────────────────────────────────────────────────────

@router.get("/tags")
async def list_tags(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_tags(conn)
    validated = [_schemas.ProductTagOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(validated)


# ── Products ─────────────────────────────────────────────────────────────

@router.get("/products")
async def list_products(
    request: Request,
    product_line_id: str | None = Query(default=None),
    tag_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    currency_code: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_products(
            conn,
            tenant_id=workspace_id,
            product_line_id=product_line_id,
            tag_code=tag_code,
            status=status,
            currency_code=currency_code,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.ProductOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/products", status_code=201)
async def create_product(
    request: Request,
    payload: Any = Body(...),
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.ProductCreate(**p) for p in payload]
    else:
        items = [_schemas.ProductCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_product(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(mode="python"),
            )
            created.append(
                _schemas.ProductOut(**row).model_dump(mode="json"),
            )
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/products/{product_id}")
async def get_product(request: Request, product_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_product(
            conn, tenant_id=workspace_id, product_id=product_id,
        )
    return _response.ok(_schemas.ProductOut(**row).model_dump(mode="json"))


@router.patch("/products/{product_id}")
async def patch_product(
    request: Request,
    product_id: str,
    payload: _schemas.ProductUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_product(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            product_id=product_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.ProductOut(**row).model_dump(mode="json"))


@router.delete(
    "/products/{product_id}",
    status_code=204,
    response_class=Response,
)
async def delete_product(request: Request, product_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_product(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            product_id=product_id,
        )
    return Response(status_code=204)


# ── Product variants (nested under a product) ────────────────────────────

@router.get("/products/{product_id}/variants")
async def list_variants(
    request: Request,
    product_id: str,
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_variants(
            conn,
            tenant_id=workspace_id,
            product_id=product_id,
            include_deleted=include_deleted,
        )
    data = [_schemas.ProductVariantOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/products/{product_id}/variants", status_code=201)
async def create_variant(
    request: Request,
    product_id: str,
    payload: _schemas.ProductVariantCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_variant(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            product_id=product_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.ProductVariantOut(**row).model_dump(mode="json"),
    )


@router.get("/products/{product_id}/variants/{variant_id}")
async def get_variant(
    request: Request, product_id: str, variant_id: str,
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_variant(
            conn,
            tenant_id=workspace_id,
            product_id=product_id,
            variant_id=variant_id,
        )
    return _response.ok(
        _schemas.ProductVariantOut(**row).model_dump(mode="json"),
    )


@router.patch("/products/{product_id}/variants/{variant_id}")
async def patch_variant(
    request: Request,
    product_id: str,
    variant_id: str,
    payload: _schemas.ProductVariantUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_variant(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            product_id=product_id,
            variant_id=variant_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.ProductVariantOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/products/{product_id}/variants/{variant_id}",
    status_code=204,
    response_class=Response,
)
async def delete_variant(
    request: Request, product_id: str, variant_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_variant(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            product_id=product_id,
            variant_id=variant_id,
        )
    return Response(status_code=204)
