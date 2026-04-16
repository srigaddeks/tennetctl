from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from .dependencies import get_test_service
from .schemas import (
    CreateTestRequest,
    TestListResponse,
    TestResponse,
    UpdateTestRequest,
)
from .service import TestService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_grc_access_module = import_module("backend.03_auth_manage.18_grc_roles.access_check")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
get_allowed_test_ids = _grc_access_module.get_allowed_test_ids

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-tests"])


@router.get(
    "/frameworks/{framework_id}/controls/{control_id}/tests",
    response_model=TestListResponse,
)
async def list_control_tests(
    framework_id: str,
    control_id: str,
    service: Annotated[TestService, Depends(get_test_service)],
    claims=Depends(get_current_access_claims),
) -> TestListResponse:
    return await service.list_tests_for_control(
        user_id=claims.subject, control_id=control_id
    )


@router.get(
    "/frameworks/{framework_id}/controls/{control_id}/tests/available",
    response_model=TestListResponse,
)
async def list_available_tests_for_control(
    framework_id: str,
    control_id: str,
    service: Annotated[TestService, Depends(get_test_service)],
    claims=Depends(get_current_access_claims),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> TestListResponse:
    return await service.list_tests_available_for_control(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        control_id=control_id,
        search=search,
        limit=limit,
    )


@router.get("/tests", response_model=TestListResponse)
async def list_tests(
    request: Request,
    service: Annotated[TestService, Depends(get_test_service)],
    claims=Depends(get_current_access_claims),
    search: str | None = Query(default=None),
    test_type_code: str | None = Query(default=None),
    is_platform_managed: bool | None = Query(default=None),
    monitoring_frequency: str | None = Query(default=None),
    scope_org_id: str | None = Query(default=None),
    scope_workspace_id: str | None = Query(default=None),
    sort_by: str = Query(default="name"),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TestListResponse:
    result = await service.list_tests(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        search=search,
        test_type_code=test_type_code,
        is_platform_managed=is_platform_managed,
        monitoring_frequency=monitoring_frequency,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )
    # Apply GRC access grant filtering
    org_id = scope_org_id
    if result.items and org_id:
        async with request.app.state.database_pool.acquire() as conn:
            allowed = await get_allowed_test_ids(
                conn,
                user_id=str(claims.subject),
                org_id=org_id,
            )
        if allowed is not None:
            result.items = [t for t in result.items if t.id in allowed]
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


@router.get("/tests/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: str,
    service: Annotated[TestService, Depends(get_test_service)],
    claims=Depends(get_current_access_claims),
) -> TestResponse:
    return await service.get_test(user_id=claims.subject, test_id=test_id)


@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(
    body: CreateTestRequest,
    service: Annotated[TestService, Depends(get_test_service)],
    claims=Depends(get_current_access_claims),
) -> TestResponse:
    return await service.create_test(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.patch("/tests/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: str,
    body: UpdateTestRequest,
    service: Annotated[TestService, Depends(get_test_service)],
    claims=Depends(get_current_access_claims),
) -> TestResponse:
    return await service.update_test(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        test_id=test_id,
        request=body,
    )


@router.delete("/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test(
    test_id: str,
    service: Annotated[TestService, Depends(get_test_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_test(
        user_id=claims.subject, tenant_key=claims.tenant_key, test_id=test_id
    )
