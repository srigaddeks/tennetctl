"""Raw materials routes — /v1/somaerp/supply/{raw-material-categories,
units-of-measure, raw-materials, raw-materials/.../variants}.

Bulk POST supported on /raw-materials (body may be a single object or array).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.30_raw_materials.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.30_raw_materials.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp/supply",
    tags=["supply", "raw_materials"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Read-only dims ───────────────────────────────────────────────────────


@router.get("/raw-material-categories")
async def list_categories(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_categories(conn)
    data = [
        _schemas.RawMaterialCategoryOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.get("/units-of-measure")
async def list_units(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_units(conn)
    data = [_schemas.UnitOfMeasureOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


# ── Raw materials ────────────────────────────────────────────────────────


@router.get("/raw-materials")
async def list_materials(
    request: Request,
    category_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    requires_lot_tracking: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_materials(
            conn,
            tenant_id=workspace_id,
            category_id=category_id,
            status=status,
            q=q,
            requires_lot_tracking=requires_lot_tracking,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.RawMaterialOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/raw-materials", status_code=201)
async def create_material(request: Request, payload: Any = Body(...)) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.RawMaterialCreate(**p) for p in payload]
    else:
        items = [_schemas.RawMaterialCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_material(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(mode="python"),
            )
            created.append(
                _schemas.RawMaterialOut(**row).model_dump(mode="json"),
            )
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/raw-materials/{material_id}")
async def get_material(request: Request, material_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_material(
            conn, tenant_id=workspace_id, material_id=material_id,
        )
    return _response.ok(_schemas.RawMaterialOut(**row).model_dump(mode="json"))


@router.patch("/raw-materials/{material_id}")
async def patch_material(
    request: Request,
    material_id: str,
    payload: _schemas.RawMaterialUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_material(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            material_id=material_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.RawMaterialOut(**row).model_dump(mode="json"))


@router.delete(
    "/raw-materials/{material_id}", status_code=204, response_class=Response,
)
async def delete_material(request: Request, material_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_material(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            material_id=material_id,
        )
    return Response(status_code=204)


# ── Raw material variants (nested) ───────────────────────────────────────


@router.get("/raw-materials/{material_id}/variants")
async def list_variants(
    request: Request,
    material_id: str,
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_variants(
            conn,
            tenant_id=workspace_id,
            material_id=material_id,
            include_deleted=include_deleted,
        )
    data = [
        _schemas.RawMaterialVariantOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("/raw-materials/{material_id}/variants", status_code=201)
async def create_variant(
    request: Request,
    material_id: str,
    payload: _schemas.RawMaterialVariantCreate,
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
            material_id=material_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.RawMaterialVariantOut(**row).model_dump(mode="json"),
    )


@router.get("/raw-materials/{material_id}/variants/{variant_id}")
async def get_variant(
    request: Request, material_id: str, variant_id: str,
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_variant(
            conn,
            tenant_id=workspace_id,
            material_id=material_id,
            variant_id=variant_id,
        )
    return _response.ok(
        _schemas.RawMaterialVariantOut(**row).model_dump(mode="json"),
    )


@router.patch("/raw-materials/{material_id}/variants/{variant_id}")
async def patch_variant(
    request: Request,
    material_id: str,
    variant_id: str,
    payload: _schemas.RawMaterialVariantUpdate,
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
            material_id=material_id,
            variant_id=variant_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.RawMaterialVariantOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/raw-materials/{material_id}/variants/{variant_id}",
    status_code=204,
    response_class=Response,
)
async def delete_variant(
    request: Request, material_id: str, variant_id: str,
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
            material_id=material_id,
            variant_id=variant_id,
        )
    return Response(status_code=204)
