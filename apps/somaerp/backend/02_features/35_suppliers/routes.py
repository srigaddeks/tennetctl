"""Supplier routes — /v1/somaerp/supply/{supplier-source-types, suppliers,
suppliers/.../materials} plus nested link routes under /raw-materials/{id}/suppliers.

NOTE: shares /v1/somaerp/supply prefix with 30_raw_materials — FastAPI
allows multiple routers under the same prefix.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.35_suppliers.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.35_suppliers.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp/supply",
    tags=["supply", "suppliers"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Read-only source types ───────────────────────────────────────────────


@router.get("/supplier-source-types")
async def list_source_types(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_source_types(conn)
    data = [
        _schemas.SupplierSourceTypeOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Suppliers ────────────────────────────────────────────────────────────


@router.get("/suppliers")
async def list_suppliers(
    request: Request,
    source_type_id: int | None = Query(default=None),
    location_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_suppliers(
            conn,
            tenant_id=workspace_id,
            source_type_id=source_type_id,
            location_id=location_id,
            status=status,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.SupplierOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/suppliers", status_code=201)
async def create_supplier(request: Request, payload: Any = Body(...)) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.SupplierCreate(**p) for p in payload]
    else:
        items = [_schemas.SupplierCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_supplier(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(mode="python"),
            )
            created.append(
                _schemas.SupplierOut(**row).model_dump(mode="json"),
            )
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/suppliers/{supplier_id}")
async def get_supplier(request: Request, supplier_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_supplier(
            conn, tenant_id=workspace_id, supplier_id=supplier_id,
        )
    return _response.ok(_schemas.SupplierOut(**row).model_dump(mode="json"))


@router.patch("/suppliers/{supplier_id}")
async def patch_supplier(
    request: Request,
    supplier_id: str,
    payload: _schemas.SupplierUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_supplier(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            supplier_id=supplier_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.SupplierOut(**row).model_dump(mode="json"))


@router.delete(
    "/suppliers/{supplier_id}", status_code=204, response_class=Response,
)
async def delete_supplier(request: Request, supplier_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_supplier(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            supplier_id=supplier_id,
        )
    return Response(status_code=204)


@router.get("/suppliers/{supplier_id}/materials")
async def list_materials_for_supplier(
    request: Request, supplier_id: str,
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_material_links_for_supplier(
            conn, tenant_id=workspace_id, supplier_id=supplier_id,
        )
    data = [
        _schemas.SupplierMaterialLinkOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Link routes (nested under /raw-materials/{id}/suppliers) ─────────────


@router.get("/raw-materials/{material_id}/suppliers")
async def list_suppliers_for_material(
    request: Request, material_id: str,
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_supplier_links_for_material(
            conn, tenant_id=workspace_id, material_id=material_id,
        )
    data = [
        _schemas.SupplierMaterialLinkOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post(
    "/raw-materials/{material_id}/suppliers", status_code=201,
)
async def link_supplier(
    request: Request,
    material_id: str,
    payload: _schemas.SupplierMaterialLinkCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_link(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            material_id=material_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.SupplierMaterialLinkOut(**row).model_dump(mode="json"),
    )


@router.patch(
    "/raw-materials/{material_id}/suppliers/{supplier_id}",
)
async def update_link(
    request: Request,
    material_id: str,
    supplier_id: str,
    payload: _schemas.SupplierMaterialLinkUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_link(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            material_id=material_id,
            supplier_id=supplier_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.SupplierMaterialLinkOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/raw-materials/{material_id}/suppliers/{supplier_id}",
    status_code=204,
    response_class=Response,
)
async def delete_link(
    request: Request, material_id: str, supplier_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.delete_link(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            material_id=material_id,
            supplier_id=supplier_id,
        )
    return Response(status_code=204)
