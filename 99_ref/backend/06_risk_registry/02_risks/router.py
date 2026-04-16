from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, File, Query, Request, UploadFile, status

from .dependencies import get_risk_service
from .schemas import (
    CompleteReviewRequest,
    CreateRiskGroupAssignmentRequest,
    CreateRiskRequest,
    HeatMapResponse,
    OverdueReviewListResponse,
    ReviewScheduleResponse,
    RiskAppetiteListResponse,
    RiskAppetiteResponse,
    RiskDetailResponse,
    RiskGroupAssignmentListResponse,
    RiskGroupAssignmentResponse,
    RiskListResponse,
    RiskResponse,
    RiskSummaryResponse,
    UpdateRiskRequest,
    UpsertReviewScheduleRequest,
    UpsertRiskAppetiteRequest,
)
from .service import RiskService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_grc_access_module = import_module("backend.03_auth_manage.18_grc_roles.access_check")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
get_allowed_risk_ids = _grc_access_module.get_allowed_risk_ids

router = InstrumentedAPIRouter(tags=["risks"])


@router.get("/risks", response_model=RiskListResponse)
async def list_risks(
    request: Request,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    level: str | None = Query(None),
    search: str | None = Query(None),
    treatment_type: str | None = Query(None),
    control_id: str | None = Query(None),
    sort_by: str | None = Query(None),
    sort_dir: str | None = Query(None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> RiskListResponse:
    result = await service.list_risks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        category=category,
        status=status_filter,
        level=level,
        search=search,
        treatment_type=treatment_type,
        control_id=control_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )
    # Apply GRC access grant filtering — risks linked to controls in allowed frameworks
    if result.items and org_id:
        async with request.app.state.database_pool.acquire() as conn:
            allowed = await get_allowed_risk_ids(
                conn, user_id=str(claims.subject), org_id=org_id,
            )
        if allowed is not None:
            result.items = [r for r in result.items if r.id in allowed]
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
                      AND fp.code = 'risks.view'
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


@router.get("/risks/heat-map", response_model=HeatMapResponse)
async def get_risk_heat_map(
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
) -> HeatMapResponse:
    return await service.get_heat_map(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
    )


@router.get("/risks/summary", response_model=RiskSummaryResponse)
async def get_risk_summary(
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
) -> RiskSummaryResponse:
    return await service.get_risk_summary(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
    )


@router.get("/risks/appetite", response_model=RiskAppetiteListResponse)
async def get_risk_appetite(
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> RiskAppetiteListResponse:
    return await service.get_risk_appetite(user_id=claims.subject, org_id=org_id)


@router.put("/risks/appetite", response_model=RiskAppetiteResponse)
async def upsert_risk_appetite(
    body: UpsertRiskAppetiteRequest,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> RiskAppetiteResponse:
    return await service.upsert_risk_appetite(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.get("/risks/overdue-reviews", response_model=OverdueReviewListResponse)
async def list_overdue_reviews(
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(None),
) -> OverdueReviewListResponse:
    return await service.list_overdue_reviews(
        user_id=claims.subject, tenant_key=claims.tenant_key, org_id=org_id
    )


@router.get("/risks/export")
async def export_risks(
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
    format: str = Query(default="csv"),
    simplified: bool = Query(default=False),
):
    """Export risks as CSV, JSON, or XLSX."""
    return await service.export_risks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        fmt=format,
        simplified=simplified,
    )


@router.post("/risks/import")
async def import_risks(
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
    file: UploadFile = File(...),
    org_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
    dry_run: bool = Query(default=False),
):
    """Import risks from CSV or JSON. Upserts by risk_code."""
    file_bytes = await file.read()
    return await service.import_risks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        file_bytes=file_bytes,
        filename=file.filename or "upload.csv",
        dry_run=dry_run,
    )


@router.get("/risks/import-template")
async def get_risks_import_template(
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
    format: str = Query(default="csv"),
):
    """Download a blank import template for risks."""
    return await service.get_import_template(fmt=format)


@router.get("/risks/{risk_id}", response_model=RiskDetailResponse)
async def get_risk(
    risk_id: str,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> RiskDetailResponse:
    return await service.get_risk(user_id=claims.subject, risk_id=risk_id)


@router.post("/risks", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
async def create_risk(
    body: CreateRiskRequest,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> RiskResponse:
    return await service.create_risk(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.patch("/risks/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: str,
    body: UpdateRiskRequest,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> RiskResponse:
    return await service.update_risk(user_id=claims.subject, risk_id=risk_id, request=body)


@router.delete("/risks/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk(
    risk_id: str,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_risk(user_id=claims.subject, risk_id=risk_id)


# ─── Group Assignment Endpoints ──────────────────────────────────────────


@router.get(
    "/risks/{risk_id}/groups", response_model=RiskGroupAssignmentListResponse
)
async def list_risk_groups(
    risk_id: str,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> RiskGroupAssignmentListResponse:
    return await service.list_risk_groups(user_id=claims.subject, risk_id=risk_id)


@router.post(
    "/risks/{risk_id}/groups",
    response_model=RiskGroupAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_risk_group(
    risk_id: str,
    body: CreateRiskGroupAssignmentRequest,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> RiskGroupAssignmentResponse:
    return await service.assign_risk_group(
        user_id=claims.subject, risk_id=risk_id, request=body
    )


@router.delete(
    "/risks/{risk_id}/groups/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unassign_risk_group(
    risk_id: str,
    assignment_id: str,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.unassign_risk_group(
        user_id=claims.subject, risk_id=risk_id, assignment_id=assignment_id
    )


# ─── Scheduled Review Endpoints ──────────────────────────────────────────


@router.get(
    "/risks/{risk_id}/review-schedule", response_model=ReviewScheduleResponse | None
)
async def get_review_schedule(
    risk_id: str,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> ReviewScheduleResponse | None:
    return await service.get_review_schedule(
        user_id=claims.subject, risk_id=risk_id
    )


@router.put(
    "/risks/{risk_id}/review-schedule", response_model=ReviewScheduleResponse
)
async def upsert_review_schedule(
    risk_id: str,
    body: UpsertReviewScheduleRequest,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> ReviewScheduleResponse:
    return await service.upsert_review_schedule(
        user_id=claims.subject, risk_id=risk_id, request=body
    )


@router.post(
    "/risks/{risk_id}/review-schedule/complete",
    response_model=ReviewScheduleResponse,
)
async def complete_review(
    risk_id: str,
    body: CompleteReviewRequest,
    service: Annotated[RiskService, Depends(get_risk_service)],
    claims=Depends(get_current_access_claims),
) -> ReviewScheduleResponse:
    return await service.complete_review(
        user_id=claims.subject, risk_id=risk_id, request=body
    )
