from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, File, Query, Request, UploadFile, status

from .dependencies import get_framework_service
from .schemas import (
    ApproveWithSelectionRequest,
    BundleImportResult,
    CreateFrameworkRequest,
    FrameworkBundle,
    FrameworkDiff,
    FrameworkListResponse,
    FrameworkResponse,
    ReviewSelectionResponse,
    SubmitForReviewRequest,
    UpdateFrameworkRequest,
)
from .service import FrameworkService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_versions_deps_module = import_module("backend.05_grc_library.03_versions.dependencies")

_grc_access_module = import_module("backend.03_auth_manage.18_grc_roles.access_check")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
get_allowed_framework_template_ids = (
    _grc_access_module.get_allowed_framework_template_ids
)
get_version_service = _versions_deps_module.get_version_service

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-frameworks"])


@router.get("/frameworks", response_model=FrameworkListResponse)
async def list_frameworks(
    request: Request,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
    category: str | None = Query(None),
    framework_type: str | None = Query(None),
    approval_status: str | None = Query(None),
    is_active: bool | None = Query(None),
    is_marketplace_visible: bool | None = Query(None),
    search: str | None = Query(None),
    scope_org_id: str | None = Query(None),
    scope_workspace_id: str | None = Query(None),
    deployed_org_id: str | None = Query(None),
    deployed_workspace_id: str | None = Query(None),
    only_engaged: bool = Query(default=False),
    sort_by: str | None = Query(None),
    sort_dir: str | None = Query(None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> FrameworkListResponse:
    result = await service.list_frameworks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        category=category,
        framework_type=framework_type,
        approval_status=approval_status,
        is_active=is_active,
        is_marketplace_visible=is_marketplace_visible,
        search=search,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
        deployed_org_id=deployed_org_id,
        deployed_workspace_id=deployed_workspace_id,
        only_engaged=only_engaged,
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
            result.items = [f for f in result.items if f.id in allowed_fw]
            result.total = len(result.items)
    elif result.items and not org_id:
        # Safety: if no org_id provided, check if user has a GRC role in any org.
        # If they do, return empty — scoped users must provide org_id.
        # Exception: platform-level users (super admins) bypass this filter.
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
                      AND fp.code = 'frameworks.view'
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


@router.get("/frameworks/{framework_id}/diff", response_model=FrameworkDiff)
async def get_framework_diff(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
) -> FrameworkDiff:
    """Compare live controls vs latest published version snapshot."""
    return await service.get_framework_diff(
        user_id=claims.subject, framework_id=framework_id
    )


@router.get("/frameworks/bundle/export/{framework_id}")
async def export_framework_bundle(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
):
    """Download a framework as a portable JSON bundle (no UUIDs)."""
    return await service.export_bundle(
        user_id=claims.subject, framework_id=framework_id
    )


@router.post(
    "/frameworks/bundle/import",
    response_model=BundleImportResult,
    status_code=status.HTTP_200_OK,
)
async def import_framework_bundle(
    body: FrameworkBundle,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
    scope_org_id: str | None = Query(None),
    scope_workspace_id: str | None = Query(None),
    dry_run: bool = Query(default=False),
) -> BundleImportResult:
    """Import a framework bundle JSON. Pass dry_run=true to preview without committing."""
    return await service.import_bundle(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        bundle=body,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
        dry_run=dry_run,
    )


@router.get("/frameworks/{framework_id}", response_model=FrameworkResponse)
async def get_framework(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
) -> FrameworkResponse:
    return await service.get_framework(
        user_id=claims.subject, framework_id=framework_id
    )


@router.post(
    "/frameworks", response_model=FrameworkResponse, status_code=status.HTTP_201_CREATED
)
async def create_framework(
    body: CreateFrameworkRequest,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
) -> FrameworkResponse:
    return await service.create_framework(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.patch("/frameworks/{framework_id}", response_model=FrameworkResponse)
async def update_framework(
    framework_id: str,
    body: UpdateFrameworkRequest,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
) -> FrameworkResponse:
    return await service.update_framework(
        user_id=claims.subject, framework_id=framework_id, request=body
    )


@router.delete("/frameworks/{framework_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_framework(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_framework(user_id=claims.subject, framework_id=framework_id)


# ── Approval Workflow ─────────────────────────────────────────────────────────


@router.post("/frameworks/{framework_id}/submit", response_model=FrameworkResponse)
async def submit_for_review(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
    request: SubmitForReviewRequest | None = None,
) -> FrameworkResponse:
    """Submit a draft/rejected framework for admin review.

    Optionally specify requirement_ids and/or control_ids to submit only specific items.
    If not provided, all items are submitted (backward compatible).
    """
    return await service.submit_for_review(
        user_id=claims.subject, framework_id=framework_id, request=request
    )


@router.get(
    "/frameworks/{framework_id}/review-selection",
    response_model=ReviewSelectionResponse,
)
async def get_review_selection(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
) -> ReviewSelectionResponse:
    """Get the current review submission details for a framework."""
    return await service.get_review_selection(framework_id=framework_id)


@router.post("/frameworks/{framework_id}/approve", response_model=FrameworkResponse)
async def approve_framework(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
    request: ApproveWithSelectionRequest | None = None,
) -> FrameworkResponse:
    """Approve a pending framework and publish to marketplace."""
    ctrl_ids = request.control_ids if request and request.control_ids else None
    return await service.approve_framework(
        user_id=claims.subject,
        framework_id=framework_id,
        control_ids=ctrl_ids,
    )


@router.get("/frameworks/{framework_id}/review-diff")
async def get_review_diff(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
) -> dict:
    """Get diff between submitted items and previous approved version."""
    return await service.get_review_diff(framework_id=framework_id)


@router.post("/frameworks/{framework_id}/reject", response_model=FrameworkResponse)
async def reject_framework(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
    reason: str | None = Query(None),
) -> FrameworkResponse:
    """Reject a pending framework with optional reason."""
    return await service.reject_framework(
        user_id=claims.subject, framework_id=framework_id, reason=reason
    )


@router.patch("/frameworks/{framework_id}/status", response_model=FrameworkResponse)
async def update_framework_status(
    framework_id: str,
    service: Annotated[FrameworkService, Depends(get_framework_service)],
    claims=Depends(get_current_access_claims),
    status: str = Query(
        ..., description="New status: draft, pending_review, approved, rejected"
    ),
) -> FrameworkResponse:
    """Update framework approval status."""
    return await service.update_framework_status(
        user_id=claims.subject, framework_id=framework_id, new_status=status
    )
