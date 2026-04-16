from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, File, Query, Request, UploadFile, status

from .dependencies import get_control_service
from .schemas import (
    ControlListResponse,
    ControlResponse,
    CreateControlRequest,
    UpdateControlRequest,
)
from .service import ControlService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

_grc_access_module = import_module("backend.03_auth_manage.18_grc_roles.access_check")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
get_allowed_framework_template_ids = (
    _grc_access_module.get_allowed_framework_template_ids
)

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-controls"])


@router.get("/controls", response_model=ControlListResponse)
async def list_all_controls(
    request: Request,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
    search: str | None = Query(default=None),
    framework_id: str | None = Query(default=None),
    scope_org_id: str | None = Query(default=None),
    scope_workspace_id: str | None = Query(default=None),
    deployed_org_id: str | None = Query(default=None),
    deployed_workspace_id: str | None = Query(default=None),
    control_category_code: str | None = Query(default=None),
    criticality_code: str | None = Query(default=None),
    control_type: str | None = Query(default=None),
    automation_potential: str | None = Query(default=None),
    sort_by: str = Query(default="sort_order"),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ControlListResponse:
    result = await service.list_all_controls(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        search=search,
        framework_id=framework_id,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
        deployed_org_id=deployed_org_id,
        deployed_workspace_id=deployed_workspace_id,
        control_category_code=control_category_code,
        criticality_code=criticality_code,
        control_type=control_type,
        automation_potential=automation_potential,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )
    # Apply GRC access grant filtering
    org_id = scope_org_id or deployed_org_id
    if result.items and org_id:
        async with request.app.state.database_pool.acquire() as conn:
            allowed_fw = await get_allowed_framework_template_ids(
                conn,
                user_id=str(claims.subject),
                org_id=org_id,
            )
        if allowed_fw is not None:
            result.items = [c for c in result.items if c.framework_id in allowed_fw]
            result.total = len(result.items)
    elif result.items and not org_id:
        # Platform-level users (super admins) bypass GRC role scoping
        async with request.app.state.database_pool.acquire() as conn:
            has_platform_perm = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM "03_auth_manage"."18_lnk_group_memberships" gm
                    JOIN "03_auth_manage"."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
                    JOIN "03_auth_manage"."20_lnk_role_feature_permissions" rfp ON rfp.role_id = gra.role_id
                    JOIN "03_auth_manage"."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
                    WHERE gm.user_id = $1::UUID
                      AND fp.code = 'controls.view'
                      AND gm.is_active = TRUE AND gm.is_deleted = FALSE
                      AND gra.is_active = TRUE AND gra.is_deleted = FALSE
                      AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
                )
                """,
                str(claims.subject),
            )
            if not has_platform_perm:
                has_role = await conn.fetchval(
                    'SELECT EXISTS(SELECT 1 FROM "03_auth_manage"."47_lnk_grc_role_assignments" WHERE user_id = $1::UUID AND revoked_at IS NULL)',
                    str(claims.subject),
                )
                if has_role:
                    result.items = []
                    result.total = 0
    return result


@router.get("/frameworks/{framework_id}/controls", response_model=ControlListResponse)
async def list_controls(
    framework_id: str,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
    search: str | None = Query(default=None),
    control_category_code: str | None = Query(default=None),
    criticality_code: str | None = Query(default=None),
    control_type: str | None = Query(default=None),
    automation_potential: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    version_id: str | None = Query(default=None),
) -> ControlListResponse:
    return await service.list_controls(
        user_id=claims.subject,
        framework_id=framework_id,
        search=search,
        control_category_code=control_category_code,
        criticality_code=criticality_code,
        control_type=control_type,
        automation_potential=automation_potential,
        limit=limit,
        offset=offset,
        version_id=version_id,
    )


@router.get("/frameworks/{framework_id}/controls/export")
async def export_controls(
    framework_id: str,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
    format: str = Query(default="csv", pattern="^(csv|json|xlsx)$"),
    simplified: bool = Query(default=False),
):
    """Export all controls in a framework."""
    return await service.export_controls(
        user_id=claims.subject,
        framework_id=framework_id,
        fmt=format,
        simplified=simplified,
    )


@router.post("/frameworks/{framework_id}/controls/import")
async def import_controls(
    framework_id: str,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
    file: UploadFile = File(...),
    dry_run: bool = Query(default=False),
):
    """Import controls from CSV or JSON. Upserts by control_code."""
    file_bytes = await file.read()
    return await service.import_controls(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        file_bytes=file_bytes,
        filename=file.filename or "upload.csv",
        dry_run=dry_run,
    )


@router.get("/frameworks/{framework_id}/controls/import-template")
async def get_controls_import_template(
    framework_id: str,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
    format: str = Query(default="csv", pattern="^(csv|xlsx)$"),
):
    """Download a blank import template."""
    return await service.get_import_template(fmt=format)


@router.get(
    "/frameworks/{framework_id}/controls/{control_id}", response_model=ControlResponse
)
async def get_control(
    framework_id: str,
    control_id: str,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
) -> ControlResponse:
    return await service.get_control(
        user_id=claims.subject, framework_id=framework_id, control_id=control_id
    )


@router.post(
    "/frameworks/{framework_id}/controls",
    response_model=ControlResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_control(
    framework_id: str,
    body: CreateControlRequest,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
) -> ControlResponse:
    return await service.create_control(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        request=body,
    )


@router.patch(
    "/frameworks/{framework_id}/controls/{control_id}", response_model=ControlResponse
)
async def update_control(
    framework_id: str,
    control_id: str,
    body: UpdateControlRequest,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
) -> ControlResponse:
    return await service.update_control(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        control_id=control_id,
        request=body,
    )


@router.delete(
    "/frameworks/{framework_id}/controls/{control_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_control(
    framework_id: str,
    control_id: str,
    service: Annotated[ControlService, Depends(get_control_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_control(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        control_id=control_id,
    )
