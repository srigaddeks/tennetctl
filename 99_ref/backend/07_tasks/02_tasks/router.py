from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, File, Query, Request, UploadFile, status

from .dependencies import get_task_service
from .schemas import (
    BulkUpdateTaskRequest,
    BulkUpdateTaskResponse,
    CreateTaskRequest,
    TaskDetailResponse,
    TaskListResponse,
    TaskSummaryResponse,
    UpdateTaskRequest,
)
from .service import TaskService

_control_schemas_module = import_module("backend.05_grc_library.05_controls.schemas")
ControlResponse = _control_schemas_module.ControlResponse

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_grc_access_module = import_module("backend.03_auth_manage.18_grc_roles.access_check")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
get_allowed_control_ids = _grc_access_module.get_allowed_control_ids

router = InstrumentedAPIRouter(tags=["tasks"])


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    request: Request,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
    status_code: str | None = Query(default=None),
    assignee_user_id: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    priority_code: str | None = Query(default=None),
    task_type_code: str | None = Query(default=None),
    due_date_from: str | None = Query(default=None),
    due_date_to: str | None = Query(default=None),
    is_overdue: bool | None = Query(default=None),
    reporter_user_id: str | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    engagement_id: str | None = Query(default=None),
) -> TaskListResponse:
    result = await service.list_tasks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        portal_mode=claims.portal_mode,
        org_id=org_id,
        workspace_id=workspace_id,
        status_code=status_code,
        assignee_user_id=assignee_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        priority_code=priority_code,
        task_type_code=task_type_code,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        is_overdue=is_overdue,
        reporter_user_id=reporter_user_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
        engagement_id=engagement_id,
    )
    # Apply GRC access grant filtering — tasks linked to controls in allowed frameworks
    if result.items and org_id:
        async with request.app.state.database_pool.acquire() as conn:
            allowed_controls = await get_allowed_control_ids(
                conn, user_id=str(claims.subject), org_id=org_id,
            )
        if allowed_controls is not None:
            result.items = [
                t for t in result.items
                if t.entity_type != "control" or (t.entity_id and t.entity_id in allowed_controls)
            ]
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
                      AND fp.code = 'tasks.view'
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


# NOTE: /tasks/summary, /tasks/export, /tasks/bulk-update MUST be before
# /tasks/{task_id} to avoid FastAPI routing shadowing.

@router.get("/tasks/summary", response_model=TaskSummaryResponse)
async def get_task_summary(
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
    engagement_id: str | None = Query(default=None),
) -> TaskSummaryResponse:
    return await service.get_task_summary(
        user_id=claims.subject, tenant_key=claims.tenant_key, portal_mode=claims.portal_mode,
        org_id=org_id, workspace_id=workspace_id, engagement_id=engagement_id,
    )


@router.get("/tasks/export")
async def export_tasks(
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
    status_code: str | None = Query(default=None),
    priority_code: str | None = Query(default=None),
    task_type_code: str | None = Query(default=None),
    assignee_user_id: str | None = Query(default=None),
    is_overdue: bool | None = Query(default=None),
    format: str = Query(default="csv"),
    simplified: bool = Query(default=False),
):
    """Export tasks as CSV, JSON, or XLSX."""
    return await service.export_tasks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        portal_mode=claims.portal_mode,
        org_id=org_id,
        workspace_id=workspace_id,
        status_code=status_code,
        priority_code=priority_code,
        task_type_code=task_type_code,
        assignee_user_id=assignee_user_id,
        is_overdue=is_overdue,
        fmt=format,
        simplified=simplified,
    )


@router.post("/tasks/import")
async def import_tasks(
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
    file: UploadFile = File(...),
    org_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
    dry_run: bool = Query(default=False),
):
    """Import tasks from CSV or JSON."""
    file_bytes = await file.read()
    return await service.import_tasks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        portal_mode=claims.portal_mode,
        org_id=org_id,
        workspace_id=workspace_id,
        file_bytes=file_bytes,
        filename=file.filename or "upload.csv",
        dry_run=dry_run,
    )


@router.get("/tasks/import-template")
async def get_tasks_import_template(
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
    format: str = Query(default="csv"),
):
    """Download a blank import template for tasks."""
    return await service.get_import_template(fmt=format)


@router.post("/tasks/bulk-update", response_model=BulkUpdateTaskResponse)
async def bulk_update_tasks(
    body: BulkUpdateTaskRequest,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
) -> BulkUpdateTaskResponse:
    return await service.bulk_update_tasks(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body, portal_mode=claims.portal_mode
    )


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
) -> TaskDetailResponse:
    return await service.get_task(user_id=claims.subject, task_id=task_id, portal_mode=claims.portal_mode)


@router.get("/tasks/{task_id}/controls", response_model=list[ControlResponse])
async def list_task_controls(
    task_id: str,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
) -> list[ControlResponse]:
    """List controls associated with a task (directly or via a risk)."""
    return await service.list_task_controls(user_id=claims.subject, task_id=task_id)


@router.post("/tasks", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: CreateTaskRequest,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
) -> TaskDetailResponse:
    return await service.create_task(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body, portal_mode=claims.portal_mode
    )


@router.patch("/tasks/{task_id}", response_model=TaskDetailResponse)
async def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
) -> TaskDetailResponse:
    return await service.update_task(
        user_id=claims.subject, task_id=task_id, request=body, portal_mode=claims.portal_mode
    )


@router.post("/tasks/{task_id}/submit-for-review", response_model=TaskDetailResponse)
async def submit_task_for_review(
    task_id: str,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
) -> TaskDetailResponse:
    return await service.submit_task_for_review(
        user_id=claims.subject,
        task_id=task_id,
        portal_mode=claims.portal_mode,
    )


@router.post("/tasks/{task_id}/clone", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
async def clone_task(
    task_id: str,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
) -> TaskDetailResponse:
    return await service.clone_task(
        user_id=claims.subject, task_id=task_id, tenant_key=claims.tenant_key, portal_mode=claims.portal_mode
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    service: Annotated[TaskService, Depends(get_task_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_task(user_id=claims.subject, task_id=task_id, portal_mode=claims.portal_mode)
