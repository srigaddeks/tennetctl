from __future__ import annotations
from fastapi import APIRouter, Depends, Request, HTTPException
from typing import List, Optional
from importlib import import_module
from uuid import UUID
import asyncpg

from .schemas import (
    EngagementResponse, EngagementCreate, EngagementUpdate,
    AuditorInviteRequest, AuditorInviteResponse,
    AuditAccessTokenResponse, AuditorRequestResponse, AuditorRequestFulfillRequest, AuditorRequestRevokeRequest,
    ControlDetailResponse, ControlVerificationRequest, AuditorDocRequest,
    EngagementTaskCreateRequest,
    EngagementParticipantResponse,
    EngagementAssessmentCreate,
)
from .repository import EngagementRepository
from .service import EngagementService
from .dashboard.router import router as auditor_dashboard_router

_database_module = import_module("backend.01_core.database")
_errors_module = import_module("backend.01_core.errors")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_grc_access_module = import_module("backend.03_auth_manage.18_grc_roles.access_check")
_feature_access_module = import_module("backend.12_engagements.feature_access")
_task_deps_module = import_module("backend.07_tasks.02_tasks.dependencies")
_task_schemas_module = import_module("backend.07_tasks.02_tasks.schemas")
_finding_deps_module = import_module("backend.09_assessments._03_findings.dependencies")
_finding_schemas_module = import_module("backend.09_assessments.schemas")

DatabasePool = _database_module.DatabasePool
AuthorizationError = _errors_module.AuthorizationError
ValidationError = _errors_module.ValidationError
get_logger = _logging_module.get_logger
logger = get_logger("backend.engagements.router")
instrument_class_methods = _telemetry_module.instrument_class_methods
require_permission = _perm_check_module.require_permission
check_engagement_access = _grc_access_module.check_engagement_access
filter_engagement_ids = _grc_access_module.filter_engagement_ids
require_feature_flag_enabled = _feature_access_module.require_feature_flag_enabled
get_task_service = _task_deps_module.get_task_service
TaskService = _task_deps_module.TaskService
TaskListResponse = _task_schemas_module.TaskListResponse
TaskDetailResponse = _task_schemas_module.TaskDetailResponse
get_finding_service = _finding_deps_module.get_finding_service
FindingService = _finding_deps_module.FindingService
CreateFindingRequest = _finding_schemas_module.CreateFindingRequest
FindingListResponse = _finding_schemas_module.FindingListResponse
FindingResponse = _finding_schemas_module.FindingResponse
AssessmentResponse = _finding_schemas_module.AssessmentResponse
UpdateFindingRequest = _finding_schemas_module.UpdateFindingRequest

_assess_deps_module = import_module("backend.09_assessments._02_assessments.dependencies")
get_assessment_service = _assess_deps_module.get_assessment_service
AssessmentService = import_module("backend.09_assessments._02_assessments.service").AssessmentService

_auth_deps = import_module("backend.03_auth_manage.dependencies")
get_current_access_claims = _auth_deps.get_current_access_claims

router = APIRouter(prefix="/api/v1/engagements", tags=["engagements"])


def _get_service() -> EngagementService:
    return EngagementService(EngagementRepository())


async def _require_active_actor(conn, service: EngagementService, user_id: str) -> None:
    if not await service.is_user_globally_active(conn, user_id=str(user_id)):
        raise HTTPException(status_code=403, detail="User account is inactive or suspended")


async def _require_active_membership_if_not_owner(
    conn,
    service: EngagementService,
    *,
    engagement_id: str,
    user_id: str,
    is_owner: bool,
    detail: str,
):
    if is_owner:
        return None
    membership_access = await service.get_active_membership_access(
        conn,
        engagement_id=engagement_id,
        user_id=user_id,
    )
    if not membership_access:
        raise HTTPException(status_code=403, detail=detail)
    return membership_access


# ── Engagements CRUD ────────────────────────────────────────────────────────

@router.get("/", response_model=List[EngagementResponse])
async def list_engagements(
    request: Request,
    org_id: str,
    status_code: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    claims=Depends(get_current_access_claims),
):
    """List engagements filtered by GRC access grants.

    Users with no GRC role or with 'All Frameworks' access see everything.
    Users with specific framework/engagement grants only see those engagements.
    """
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        engagements = await service.list_engagements(
            conn,
            tenant_key=claims.tenant_key,
            org_id=org_id,
            status_code=status_code,
            limit=limit,
            offset=offset,
        )
        # Apply GRC access grant filtering
        if engagements:
            all_ids = [e.id for e in engagements]
            allowed_ids = await filter_engagement_ids(
                conn, user_id=str(claims.subject), org_id=org_id, engagement_ids=all_ids,
            )
            if allowed_ids is not None and set(allowed_ids) != set(all_ids):
                allowed_set = set(allowed_ids)
                engagements = [e for e in engagements if e.id in allowed_set]
        return engagements


@router.get("/my-engagements", response_model=List[EngagementResponse])
async def list_my_engagements(
    request: Request,
    org_id: str | None = None,
    claims=Depends(get_current_access_claims),
):
    """Fetch all engagements accessible to the current user."""
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_portfolio",
            message="The auditor portfolio is not enabled in this environment.",
        )
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_engagement_membership",
            message="Engagement membership access is not enabled in this environment.",
        )
        await _require_active_actor(conn, service, str(claims.subject))
        user_email = await _get_auditor_email(conn, claims)
        
        if not user_email:
             return []
             
        return await service.list_my_engagements(
            conn,
            user_id=str(claims.subject),
            email=user_email,
            org_id=org_id,
        )


@router.post("/", response_model=EngagementResponse, status_code=201)
async def create_engagement(
    request: Request,
    data: EngagementCreate,
    org_id: str,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    try:
        async with request.app.state.database_pool.acquire() as conn:
            await _require_active_actor(conn, service, str(claims.subject))
            return await service.create_engagement(
                conn,
                tenant_key=claims.tenant_key,
                org_id=org_id,
                data=data,
                created_by=str(claims.subject),
            )
    except Exception as e:
        if "unique_violation" in str(e).lower() or "23505" in str(e):
            raise HTTPException(status_code=409, detail="Engagement code already exists in this organization")
        raise


@router.get("/{engagement_id}", response_model=EngagementResponse)
async def get_engagement(
    request: Request,
    engagement_id: str,
    claims=Depends(get_current_access_claims),
):
    """Get a single engagement through internal RBAC, membership, or guest token access."""
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        eff_tenant, _ = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "controls.view",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        return engagement


async def _resolve_engagement_access(conn, service, engagement_id: str, claims, required_internal_perm: str = "controls.view"):
    """Unified access resolver with GRC access grant enforcement.

    Returns (effective_tenant_key, is_owner).
    Checks ownership (claims.tenant_key) + RBAC + GRC access grants for internal users.
    Falls back to active engagement membership, then guest/auditor access via email/token.
    """
    # 1. Attempt internal ownership path
    owner_eng = await service.get_engagement(conn, engagement_id, claims.tenant_key)
    if owner_eng:
        # User is internal to this tenant — check RBAC
        try:
            await require_permission(conn, str(claims.subject), required_internal_perm)
        # Also enforce GRC access grants
            has_access = await check_engagement_access(
                conn, user_id=str(claims.subject), org_id=owner_eng.org_id, engagement_id=engagement_id,
            )
            if has_access:
                return claims.tenant_key, True
        except AuthorizationError:
            pass

    # 2. Attempt active engagement membership path
    membership_access = await service.get_active_membership_access(
        conn,
        engagement_id=engagement_id,
        user_id=str(claims.subject),
    )
    if membership_access:
        return str(membership_access["tenant_key"]), False

    # 3. Attempt auditor guest path
    user_email = await _get_auditor_email(conn, claims)
    guest_tenant = await service.validate_auditor_access_and_get_tenant(conn, engagement_id, user_email)
    if guest_tenant:
        return guest_tenant, False

    # 4. Not found or unauthorised
    raise HTTPException(status_code=404, detail="Engagement not found or access denied")


async def _resolve_engagement_access_v2(
    conn,
    service,
    engagement_id: str,
    claims,
    required_internal_perm: str = "controls.view",
):
    """Resolve engagement access through internal RBAC, membership, or guest token access."""
    await _require_active_actor(conn, service, str(claims.subject))

    owner_eng = await service.get_engagement(conn, engagement_id, claims.tenant_key)
    if owner_eng:
        try:
            await require_permission(conn, str(claims.subject), required_internal_perm)
            has_access = await check_engagement_access(
                conn,
                user_id=str(claims.subject),
                org_id=owner_eng.org_id,
                engagement_id=engagement_id,
            )
            if has_access:
                return claims.tenant_key, True
        except AuthorizationError:
            pass

    membership_access = await service.get_active_membership_access(
        conn,
        engagement_id=engagement_id,
        user_id=str(claims.subject),
    )
    if membership_access:
        return str(membership_access["tenant_key"]), False

    user_email = await _get_auditor_email(conn, claims)
    guest_tenant = await service.validate_auditor_access_and_get_tenant(
        conn,
        engagement_id,
        user_email,
    )
    if guest_tenant:
        return guest_tenant, False

    raise HTTPException(status_code=404, detail="Engagement not found or access denied")


@router.get("/{engagement_id}/controls")
async def list_engagement_controls(
    request: Request,
    engagement_id: str,
    claims=Depends(get_current_access_claims),
):
    """List controls for an engagement.

    External auditors only see evidence marked as auditor-accessible.
    Internal users see all evidence.
    """
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_control_access",
            message="Auditor control access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(conn, service, engagement_id, claims, "controls.view")
        membership_access = await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=engagement_id,
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for auditor control access.",
        )
        return await service.list_engagement_controls(
            conn,
            engagement_id,
            eff_tenant,
            auditor_only=not is_owner,
            viewer_membership_id=membership_access["membership_id"] if membership_access else None,
        )


@router.get("/{engagement_id}/controls/{control_id}/detail", response_model=ControlDetailResponse)
async def get_control_detail(
    request: Request,
    engagement_id: UUID,
    control_id: UUID,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_control_access",
            message="Auditor control access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(conn, service, str(engagement_id), claims, "controls.view")
        membership_access = await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=str(engagement_id),
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for auditor control detail access.",
        )
        return await service.get_control_detail(
            conn,
            str(engagement_id),
            eff_tenant,
            str(control_id),
            auditor_only=not is_owner,
            viewer_membership_id=membership_access["membership_id"] if membership_access else None,
        )


@router.get("/{engagement_id}/tasks", response_model=TaskListResponse)
async def list_engagement_tasks(
    request: Request,
    engagement_id: str,
    task_service: TaskService = Depends(get_task_service),
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_tasks",
            message="Auditor task access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "tasks.view",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=engagement_id,
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for auditor task access.",
        )

    return await task_service.list_tasks_prevalidated(
        user_id=claims.subject,
        tenant_key=eff_tenant,
        portal_mode=claims.portal_mode,
        org_id=engagement.org_id,
        workspace_id=engagement.workspace_id,
        engagement_id=engagement_id,
        limit=100,
        offset=0,
    )


@router.get("/{engagement_id}/participants", response_model=List[EngagementParticipantResponse])
async def list_engagement_participants(
    request: Request,
    engagement_id: str,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_tasks",
            message="Auditor task access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "tasks.view",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=engagement_id,
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for participant lookup.",
        )
        participants = await service.list_active_engagement_participants(
            conn,
            engagement_id=engagement_id,
        )
    return [EngagementParticipantResponse.model_validate(item) for item in participants]


@router.post("/{engagement_id}/tasks", response_model=TaskDetailResponse, status_code=201)
async def create_engagement_task(
    request: Request,
    engagement_id: str,
    data: EngagementTaskCreateRequest,
    task_service: TaskService = Depends(get_task_service),
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_tasks",
            message="Auditor task access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "tasks.create",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=engagement_id,
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for auditor task creation.",
        )
        try:
            task_request = await service.build_engagement_task_request(
                conn,
                engagement=engagement,
                engagement_id=engagement_id,
                task_request=data,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return await task_service.create_task_prevalidated(
        user_id=claims.subject,
        tenant_key=eff_tenant,
        request=task_request,
        portal_mode=claims.portal_mode,
    )


@router.get("/{engagement_id}/assessments", response_model=List[AssessmentResponse])
async def list_engagement_assessments(
    request: Request,
    engagement_id: str,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_findings",
            message="Auditor finding access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "controls.view",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=engagement_id,
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for auditor assessment access.",
        )
        assessments = await service.list_assessments_in_engagement_scope(
            conn,
            engagement_id=engagement_id,
        )
    return [AssessmentResponse.model_validate(item) for item in assessments]


@router.get("/{engagement_id}/findings", response_model=FindingListResponse)
async def list_engagement_findings(
    request: Request,
    engagement_id: str,
    assessment_id: str,
    severity_code: str | None = None,
    status_filter: str | None = None,
    finding_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    finding_service: FindingService = Depends(get_finding_service),
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_findings",
            message="Auditor finding access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "controls.view",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=engagement_id,
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for auditor finding access.",
        )
        try:
            await service.assert_assessment_in_engagement_scope(
                conn,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return await finding_service.list_findings_prevalidated(
        user_id=claims.subject,
        assessment_id=assessment_id,
        severity_code=severity_code,
        status_code=status_filter,
        finding_type=finding_type,
        limit=limit,
        offset=offset,
    )


@router.post("/{engagement_id}/findings", response_model=FindingResponse, status_code=201)
async def create_engagement_finding(
    request: Request,
    engagement_id: str,
    assessment_id: str,
    data: CreateFindingRequest,
    finding_service: FindingService = Depends(get_finding_service),
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_findings",
            message="Auditor finding access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "controls.update",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=engagement_id,
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for auditor finding creation.",
        )
        try:
            await service.assert_assessment_in_engagement_scope(
                conn,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return await finding_service.create_finding_prevalidated(
        user_id=claims.subject,
        assessment_id=assessment_id,
        request=data,
    )


@router.post("/{engagement_id}/assessments", response_model=AssessmentResponse, status_code=201)
async def create_engagement_assessment(
    request: Request,
    engagement_id: str,
    data: EngagementAssessmentCreate,
    assessment_service: AssessmentService = Depends(get_assessment_service),
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_findings",
            message="Auditor finding access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "controls.update",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=engagement_id,
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for auditor assessment creation.",
        )

        return await service.create_engagement_assessment(
            conn,
            engagement_id=engagement_id,
            tenant_key=eff_tenant,
            user_id=str(claims.subject),
            request=data,
            assessment_service=assessment_service,
        )


@router.patch("/{engagement_id}/findings/{finding_id}", response_model=FindingResponse)
async def update_engagement_finding(
    request: Request,
    engagement_id: str,
    finding_id: str,
    data: UpdateFindingRequest,
    finding_service: FindingService = Depends(get_finding_service),
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_findings",
            message="Auditor finding access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "findings.update",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        existing = await finding_service.get_finding(finding_id=finding_id)
        try:
            await service.assert_assessment_in_engagement_scope(
                conn,
                engagement_id=engagement_id,
                assessment_id=existing.assessment_id,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if data.assigned_to:
            is_participant = await service.is_active_engagement_participant_user(
                conn,
                engagement_id=engagement_id,
                user_id=data.assigned_to,
            )
            if not is_participant:
                raise HTTPException(
                    status_code=400,
                    detail="Assigned user must be an active participant in the engagement.",
                )

        if not is_owner:
            membership_access = await _require_active_membership_if_not_owner(
                conn,
                service,
                engagement_id=engagement_id,
                user_id=str(claims.subject),
                is_owner=is_owner,
                detail="Active engagement membership is required for auditor finding updates.",
            )
            is_elevated = membership_access.get("membership_type_code") == "grc_team"
            if not is_elevated:
                if existing.created_by != str(claims.subject):
                    raise HTTPException(
                        status_code=403,
                        detail="Auditors may only update findings they created.",
                    )
                if data.assigned_to is not None:
                    raise HTTPException(
                        status_code=403,
                        detail="Only elevated engagement users can reassign findings.",
                    )
                if data.finding_status_code is not None:
                    raise HTTPException(
                        status_code=403,
                        detail="Only elevated engagement users can change finding lifecycle status.",
                    )

    return await finding_service.update_finding_prevalidated(
        user_id=claims.subject,
        finding_id=finding_id,
        request=data,
    )


@router.delete("/{engagement_id}/findings/{finding_id}", status_code=204)
async def delete_engagement_finding(
    request: Request,
    engagement_id: str,
    finding_id: str,
    finding_service: FindingService = Depends(get_finding_service),
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_findings",
            message="Auditor finding access is not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            engagement_id,
            claims,
            "findings.delete",
        )
        engagement = await service.get_engagement(conn, engagement_id, eff_tenant)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        existing = await finding_service.get_finding(finding_id=finding_id)
        try:
            await service.assert_assessment_in_engagement_scope(
                conn,
                engagement_id=engagement_id,
                assessment_id=existing.assessment_id,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if not is_owner:
            membership_access = await _require_active_membership_if_not_owner(
                conn,
                service,
                engagement_id=engagement_id,
                user_id=str(claims.subject),
                is_owner=is_owner,
                detail="Deleting engagement findings requires elevated engagement access.",
            )
            if membership_access.get("membership_type_code") != "grc_team":
                raise HTTPException(
                    status_code=403,
                    detail="Deleting engagement findings requires elevated engagement access.",
                )

    await finding_service.delete_finding_prevalidated(
        user_id=claims.subject,
        finding_id=finding_id,
    )


@router.post("/{engagement_id}/controls/{control_id}/verify")
async def verify_control(
    request: Request,
    engagement_id: UUID,
    control_id: UUID,
    data: ControlVerificationRequest,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        # Only auditors can verify controls via this path, OR we allow high-level GRC admins? 
        # Typically verifications are auditor-authored.
        user_email = await _get_auditor_email(conn, claims)
        eff_tenant = await service.validate_auditor_access_and_get_tenant(conn, str(engagement_id), user_email)
        if not eff_tenant:
            # Fallback: maybe they possess high internal permissions?
            # We'll stick to auditor tokens for authored verifications for now.
            raise HTTPException(status_code=403, detail="Auditor token required for verification submission")
            
        success = await service.verify_control(
            conn,
            engagement_id=str(engagement_id),
            tenant_key=eff_tenant,
            control_id=str(control_id),
            email=user_email,
            outcome=data.outcome,
            observations=data.observations,
            finding_details=data.finding_details,
        )
        return {"success": success}


@router.post("/{engagement_id}/controls/{control_id}/request-docs")
async def request_more_docs(
    request: Request,
    engagement_id: UUID,
    control_id: UUID,
    data: AuditorDocRequest,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_evidence_requests",
            message="Auditor evidence requests are not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            str(engagement_id),
            claims,
            "controls.view",
        )
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=str(engagement_id),
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for evidence requests.",
        )
        user_email = await _get_auditor_email(conn, claims)
        try:
            request_id = await service.create_auditor_request(
                conn,
                engagement_id=str(engagement_id),
                tenant_key=eff_tenant,
                control_id=str(control_id),
                email=user_email,
                description=data.description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"id": request_id}


@router.post("/{engagement_id}/tasks/{task_id}/request-access")
async def request_task_evidence(
    request: Request,
    engagement_id: UUID,
    task_id: UUID,
    data: AuditorDocRequest,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_evidence_requests",
            message="Auditor evidence requests are not enabled in this environment.",
        )
        eff_tenant, is_owner = await _resolve_engagement_access_v2(
            conn,
            service,
            str(engagement_id),
            claims,
            "controls.view",
        )
        await _require_active_membership_if_not_owner(
            conn,
            service,
            engagement_id=str(engagement_id),
            user_id=str(claims.subject),
            is_owner=is_owner,
            detail="Active engagement membership is required for evidence requests.",
        )
        user_email = await _get_auditor_email(conn, claims)
        try:
            request_id = await service.create_auditor_request(
                conn,
                engagement_id=str(engagement_id),
                tenant_key=eff_tenant,
                control_id=None,
                task_id=str(task_id),
                email=user_email,
                description=data.description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"id": request_id}


async def _get_auditor_email(conn: asyncpg.Connection, claims) -> str:
    """Helper to resolve email from claims (EAV lookup)."""
    if claims.is_api_key:
        # For local dev API testing, use a fallback if needed
        return "admin@test.com"
        
    email = await conn.fetchval(
        'SELECT property_value FROM "03_auth_manage"."05_dtl_user_properties" WHERE user_id = $1 AND property_key = \'email\'',
        UUID(claims.subject)
    )
    if not email:
        raise HTTPException(status_code=404, detail="Auditor email not found")
    return email


@router.patch("/{engagement_id}", response_model=EngagementResponse)
async def update_engagement(
    request: Request,
    engagement_id: str,
    data: EngagementUpdate,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        # Allow update if user has controls.edit permission OR has a GRC role for this engagement
        try:
            await require_permission(conn, str(claims.subject), "controls.edit")
        except Exception:
            # Fallback: check GRC role access
            eng = await service.get_engagement(conn, engagement_id, claims.tenant_key)
            if not eng:
                raise HTTPException(status_code=404, detail="Engagement not found")
            has_access = await check_engagement_access(
                conn, user_id=str(claims.subject), org_id=eng.org_id, engagement_id=engagement_id,
            )
            if not has_access:
                raise HTTPException(status_code=403, detail="Permission required: controls.edit or GRC role")
        try:
            return await service.update_engagement(
                conn, engagement_id, claims.tenant_key, data=data, updated_by=str(claims.subject),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


# ── Auditor Invitation ───────────────────────────────────────────────────────

@router.post("/{engagement_id}/invite-auditor", response_model=AuditorInviteResponse)
async def invite_auditor(
    request: Request,
    engagement_id: str,
    data: AuditorInviteRequest,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        await require_permission(conn, str(claims.subject), "controls.admin")
        existing = await service.get_engagement(conn, engagement_id, claims.tenant_key)
        if not existing:
            raise HTTPException(status_code=404, detail="Engagement not found")

        settings = request.app.state.settings
        platform_base_url = getattr(settings, "platform_base_url", str(request.base_url).rstrip("/"))
        try:
            invite_url, expires_at = await service.invite_auditor(
                conn,
                engagement_id=engagement_id,
                tenant_key=claims.tenant_key,
                email=data.email,
                expires_in_days=data.expires_in_days,
                platform_base_url=platform_base_url,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return AuditorInviteResponse(email=data.email, invite_url=invite_url, expires_at=expires_at)


# ── Access Token Management ─────────────────────────────────────────────────

@router.get("/{engagement_id}/access-tokens", response_model=List[AuditAccessTokenResponse])
async def list_access_tokens(
    request: Request,
    engagement_id: str,
    include_revoked: bool = True,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        await require_permission(conn, str(claims.subject), "controls.view")
        existing = await service.get_engagement(conn, engagement_id, claims.tenant_key)
        if not existing:
            raise HTTPException(status_code=404, detail="Engagement not found")
        return await service.list_access_tokens(conn, engagement_id, claims.tenant_key, include_revoked=include_revoked)


@router.delete("/{engagement_id}/access-tokens/{token_id}", status_code=204)
async def revoke_access_token(
    request: Request,
    engagement_id: str,
    token_id: str,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        await require_permission(conn, str(claims.subject), "controls.admin")
        existing = await service.get_engagement(conn, engagement_id, claims.tenant_key)
        if not existing:
            raise HTTPException(status_code=404, detail="Engagement not found")
        ok = await service.revoke_access_token(conn, token_id, claims.tenant_key, revoked_by=str(claims.subject))
    if not ok:
        raise HTTPException(status_code=404, detail="Token not found or already revoked")


# ── Auditor Request Management ───────────────────────────────────────────────

@router.get("/{engagement_id}/requests", response_model=List[AuditorRequestResponse])
async def list_auditor_requests(
    request: Request,
    engagement_id: str,
    status: Optional[str] = None,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_evidence_requests",
            message="Auditor evidence requests are not enabled in this environment.",
        )
        await require_permission(conn, str(claims.subject), "controls.view")
        existing = await service.get_engagement(conn, engagement_id, claims.tenant_key)
        if not existing:
            raise HTTPException(status_code=404, detail="Engagement not found")
        return await service.list_auditor_requests(conn, engagement_id, claims.tenant_key, status=status)


@router.patch("/{engagement_id}/requests/{request_id}", response_model=AuditorRequestResponse)
async def fulfill_auditor_request(
    request: Request,
    engagement_id: str,
    request_id: str,
    data: AuditorRequestFulfillRequest,
    claims=Depends(get_current_access_claims),
):
    if data.action not in ("fulfill", "dismiss"):
        raise HTTPException(status_code=400, detail="action must be 'fulfill' or 'dismiss'")
    if data.action == "fulfill" and not data.attachment_id:
        raise HTTPException(status_code=400, detail="attachment_id is required when fulfilling an evidence request")
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_evidence_requests",
            message="Auditor evidence requests are not enabled in this environment.",
        )
        await require_permission(conn, str(claims.subject), "controls.edit")
        existing = await service.get_engagement(conn, engagement_id, claims.tenant_key)
        if not existing:
            raise HTTPException(status_code=404, detail="Engagement not found")
        try:
            ok = await service.fulfill_auditor_request(
                conn, request_id, claims.tenant_key,
                action=data.action,
                fulfilled_by=str(claims.subject),
                attachment_ids=data.attachment_ids,
                response_notes=data.response_notes,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not ok:
            raise HTTPException(status_code=404, detail="Request not found, already resolved, or deleted")
        all_requests = await service.list_auditor_requests(conn, engagement_id, claims.tenant_key)
    match = next((r for r in all_requests if r.id == request_id), None)
    if not match:
        raise HTTPException(status_code=500, detail="Failed to fetch updated request")
    return match


@router.post("/{engagement_id}/requests/{request_id}/revoke", response_model=AuditorRequestResponse)
async def revoke_auditor_request_access(
    request: Request,
    engagement_id: str,
    request_id: str,
    data: AuditorRequestRevokeRequest,
    claims=Depends(get_current_access_claims),
):
    service = _get_service()
    async with request.app.state.database_pool.acquire() as conn:
        await _require_active_actor(conn, service, str(claims.subject))
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_evidence_requests",
            message="Auditor evidence requests are not enabled in this environment.",
        )
        await require_permission(conn, str(claims.subject), "controls.edit")
        existing = await service.get_engagement(conn, engagement_id, claims.tenant_key)
        if not existing:
            raise HTTPException(status_code=404, detail="Engagement not found")
        ok = await service.revoke_auditor_request_access(
            conn,
            request_id,
            claims.tenant_key,
            revoked_by=str(claims.subject),
            response_notes=data.response_notes,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Approved evidence access not found or already revoked")
        all_requests = await service.list_auditor_requests(conn, engagement_id, claims.tenant_key)
    match = next((r for r in all_requests if r.id == request_id), None)
    if not match:
        raise HTTPException(status_code=500, detail="Failed to fetch updated request")
    return match
