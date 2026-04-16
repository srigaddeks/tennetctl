from __future__ import annotations

import asyncio
import uuid
from importlib import import_module

from .repository import TaskRepository
from .schemas import (
    BulkUpdateTaskRequest,
    BulkUpdateTaskResponse,
    CreateTaskRequest,
    TaskDetailResponse,
    TaskListResponse,
    TaskSummaryResponse,
    TaskTypeSummary,
    UpdateTaskRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.07_tasks.constants")
_access_scope_module = import_module("backend.07_tasks.access_scope")
_auth_constants_module = import_module("backend.03_auth_manage.constants")
_spreadsheet_module = import_module("backend.01_core.spreadsheet")
_engagements_repo_module = import_module("backend.12_engagements.repository")
_engagement_access_module = import_module("backend.03_auth_manage.18_grc_roles.access_check")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuthorizationError = _errors_module.AuthorizationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
TaskAuditEventType = _constants_module.TaskAuditEventType
TASK_STATUS_TRANSITIONS = _constants_module.TASK_STATUS_TRANSITIONS
TASK_TRANSITION_PERMISSION = _constants_module.TASK_TRANSITION_PERMISSION
VALID_SORT_FIELDS = _constants_module.VALID_SORT_FIELDS
is_assignee_portal_mode = _access_scope_module.is_assignee_portal_mode
assert_assignee_task_entity_access = _access_scope_module.assert_assignee_task_entity_access
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
to_csv = _spreadsheet_module.to_csv
to_json = _spreadsheet_module.to_json
to_xlsx = _spreadsheet_module.to_xlsx
to_xlsx_template = _spreadsheet_module.to_xlsx_template
parse_import = _spreadsheet_module.parse_import
make_streaming_response = _spreadsheet_module.make_streaming_response
EngagementRepository = _engagements_repo_module.EngagementRepository
check_engagement_access = _engagement_access_module.check_engagement_access

_CACHE_TTL_TASKS = 300  # 5 minutes

# Event repository for creating task events inline
_events_repo_module = import_module("backend.07_tasks.05_events.repository")
EventRepository = _events_repo_module.EventRepository

_controls_repo_module = import_module("backend.05_grc_library.05_controls.repository")
ControlRepository = _controls_repo_module.ControlRepository

_risks_repo_module = import_module("backend.06_risk_registry.02_risks.repository")
RiskRepository = _risks_repo_module.RiskRepository

_mappings_repo_module = import_module("backend.06_risk_registry.05_control_mappings.repository")
ControlMappingRepository = _mappings_repo_module.ControlMappingRepository


@instrument_class_methods(namespace="tasks.service", logger_name="backend.tasks.instrumentation")
class TaskService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TaskRepository()
        self._engagement_repository = EngagementRepository()
        self._event_repository = EventRepository()
        self._control_repository = ControlRepository()
        self._risk_repository = RiskRepository()
        self._mapping_repository = ControlMappingRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.tasks")

    async def _assert_user_globally_active(self, conn, *, user_id: str) -> None:
        if not await self._engagement_repository.is_user_globally_active(
            conn,
            user_id=user_id,
        ):
            raise AuthorizationError("User account is inactive or suspended.")

    async def _require_task_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str | None,
        workspace_id: str | None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
            scope_workspace_id=workspace_id,
        )

    async def _assert_task_engagement_boundary(
        self,
        conn,
        *,
        user_id: str,
        org_id: str | None,
        entity_type: str | None,
        entity_id: str | None,
    ) -> None:
        if not org_id or not entity_type or not entity_id:
            return
        linked_engagement_ids = await self._repository.list_linked_engagement_ids_for_task_target(
            conn,
            org_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        if not linked_engagement_ids:
            return
        for engagement_id in linked_engagement_ids:
            membership_access = await self._engagement_repository.get_active_membership_access(
                conn,
                engagement_id=engagement_id,
                user_id=user_id,
            )
            if membership_access:
                return
            if await check_engagement_access(
                conn,
                user_id=user_id,
                org_id=org_id,
                engagement_id=engagement_id,
            ):
                return
        raise AuthorizationError(
            "This task is bound to an engagement that the current user cannot access."
        )

    async def _get_task_engagement_lifecycle_role(
        self,
        conn,
        *,
        user_id: str,
        org_id: str | None,
        entity_type: str | None,
        entity_id: str | None,
    ) -> str:
        if not org_id or not entity_type or not entity_id:
            return "non_engagement"
        linked_engagement_ids = await self._repository.list_linked_engagement_ids_for_task_target(
            conn,
            org_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        if not linked_engagement_ids:
            return "non_engagement"

        for engagement_id in linked_engagement_ids:
            membership_access = await self._engagement_repository.get_active_membership_access(
                conn,
                engagement_id=engagement_id,
                user_id=user_id,
            )
            if membership_access:
                if membership_access.get("membership_type_code") == "grc_team":
                    return "elevated"
                return "member"
            if await check_engagement_access(
                conn,
                user_id=user_id,
                org_id=org_id,
                engagement_id=engagement_id,
            ):
                return "elevated"
        return "blocked"

    def _assert_member_task_update_allowed(
        self,
        *,
        role: str,
        user_id: str,
        existing,
        request: UpdateTaskRequest,
    ) -> None:
        if role != "member":
            return

        is_reporter = existing.reporter_user_id == user_id
        is_assignee = existing.assignee_user_id == user_id

        if not is_reporter and not is_assignee:
            raise AuthorizationError("Only the task creator or assignee can update this engagement task.")

        if is_assignee and not is_reporter:
            forbidden_fields = [
                ("priority_code", request.priority_code),
                ("assignee_user_id", request.assignee_user_id),
                ("due_date", request.due_date),
                ("estimated_hours", request.estimated_hours),
                ("title", request.title),
                ("description", request.description),
                ("acceptance_criteria", request.acceptance_criteria),
                ("remediation_plan", request.remediation_plan),
            ]
            changed_forbidden = [field for field, value in forbidden_fields if value is not None]
            if changed_forbidden:
                raise AuthorizationError(
                    "Assignees may only update task progress and completion fields for engagement tasks."
                )
            if request.status_code is not None and request.status_code not in {
                "in_progress",
                "pending_verification",
                "resolved",
            }:
                raise AuthorizationError(
                    "Assignees may only move engagement tasks into progress, review, or resolved states."
                )

        if request.assignee_user_id is not None:
            raise AuthorizationError("Only elevated engagement users can reassign engagement tasks.")

    async def list_tasks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        status_code: str | None = None,
        assignee_user_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        priority_code: str | None = None,
        task_type_code: str | None = None,
        due_date_from: str | None = None,
        due_date_to: str | None = None,
        is_overdue: bool | None = None,
        reporter_user_id: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
        engagement_id: str | None = None,
    ) -> TaskListResponse:
        assignee_mode = is_assignee_portal_mode(portal_mode)
        if not assignee_mode:
            async with self._database_pool.acquire() as conn:
                await self._assert_user_globally_active(conn, user_id=user_id)
                await require_permission(
                    conn, user_id, "tasks.view",
                    scope_org_id=org_id, scope_workspace_id=workspace_id,
                )
        return await self.list_tasks_prevalidated(
            user_id=user_id,
            tenant_key=tenant_key,
            portal_mode=portal_mode,
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

    async def list_tasks_prevalidated(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        status_code: str | None = None,
        assignee_user_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        priority_code: str | None = None,
        task_type_code: str | None = None,
        due_date_from: str | None = None,
        due_date_to: str | None = None,
        is_overdue: bool | None = None,
        reporter_user_id: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
        engagement_id: str | None = None,
    ) -> TaskListResponse:
        assignee_mode = is_assignee_portal_mode(portal_mode)
        accessible_engagement_ids: list[str] | None = None
        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            if not assignee_mode:
                accessible_engagement_ids = await self._engagement_repository.list_accessible_engagement_ids_for_user(
                    conn,
                    user_id=user_id,
                    org_id=org_id,
                )

        scope_assignee_user_id: str | None = user_id if assignee_mode else None
        effective_assignee_filter = assignee_user_id
        if assignee_mode:
            if assignee_user_id is not None and assignee_user_id != user_id:
                return TaskListResponse(items=[], total=0)
            effective_assignee_filter = None

        cache_key = (
            f"tasks:list:{tenant_key}:{workspace_id or 'all'}:"
            f"{engagement_id or 'all'}:"
            f"{portal_mode or 'default'}:{user_id if assignee_mode else 'any'}"
        )
        # Only use cache for unfiltered workspace listing
        has_filters = any([
            status_code, effective_assignee_filter, entity_type, entity_id,
            priority_code, task_type_code, due_date_from, due_date_to,
            is_overdue, reporter_user_id, sort_by, assignee_mode,
        ])
        if not has_filters:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return TaskListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            tasks, total = await self._repository.list_tasks(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
                status_code=status_code,
                assignee_user_id=effective_assignee_filter,
                entity_type=entity_type,
                entity_id=entity_id,
                priority_code=priority_code,
                task_type_code=task_type_code,
                due_date_from=due_date_from,
                due_date_to=due_date_to,
                is_overdue=is_overdue,
                reporter_user_id=reporter_user_id,
                scope_assignee_user_id=scope_assignee_user_id,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
                engagement_id=engagement_id,
                accessible_engagement_ids=accessible_engagement_ids,
            )
        # Batch resolve entity names
        names_map = await self._resolve_entity_names_batch(tasks)
        
        result = TaskListResponse(
            items=[_task_detail_response(t, entity_name=names_map.get(t.id)) for t in tasks],
            total=total,
        )
        if not has_filters:
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_TASKS)
        return result

    async def get_task(
        self,
        *,
        user_id: str,
        task_id: str,
        portal_mode: str | None = None,
    ) -> TaskDetailResponse:
        assignee_mode = is_assignee_portal_mode(portal_mode)
        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            if not assignee_mode:
                existing = await self._repository.get_task_by_id(conn, task_id)
                if existing is None:
                    raise NotFoundError(f"Task '{task_id}' not found")
                await self._require_task_permission(
                    conn,
                    user_id=user_id,
                    permission_code="tasks.view",
                    org_id=existing.org_id,
                    workspace_id=existing.workspace_id,
                )
                await self._assert_task_engagement_boundary(
                    conn,
                    user_id=user_id,
                    org_id=existing.org_id,
                    entity_type=existing.entity_type,
                    entity_id=existing.entity_id,
                )

        cache_key = f"task:{task_id}:{portal_mode or 'default'}:{user_id if assignee_mode else 'any'}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return TaskDetailResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            task = await self._repository.get_task_detail(
                conn,
                task_id,
                scope_assignee_user_id=user_id if assignee_mode else None,
            )
        if task is None:
            raise NotFoundError(f"Task '{task_id}' not found")
        
        # Resolve entity name
        entity_name = await self._resolve_entity_name(task.entity_type, task.entity_id)
        
        result = _task_detail_response(task, entity_name=entity_name)
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_TASKS)
        return result

    async def _resolve_entity_name(self, entity_type: str | None, entity_id: str | None) -> str | None:
        if not entity_type or not entity_id:
            return None
        
        try:
            async with self._database_pool.acquire() as conn:
                if entity_type == "control":
                    ctrl = await self._control_repository.get_control_by_id(conn, entity_id)
                    return ctrl.name if ctrl else None
                elif entity_type == "risk":
                    risk = await self._risk_repository.get_risk_detail(conn, entity_id)
                    return risk.title if risk else None
                elif entity_type == "framework":
                    # Potentially add framework name resolution here if needed
                    pass
        except Exception:
            # Fallback for name resolution errors to avoid breaking the core task fetch
            pass
        return None

    async def _resolve_entity_names_batch(self, tasks: list[TaskDetailRecord]) -> dict[str, str]:
        if not tasks:
            return {}
            
        control_ids = [t.entity_id for t in tasks if t.entity_type == "control" and t.entity_id]
        risk_ids = [t.entity_id for t in tasks if t.entity_type == "risk" and t.entity_id]
        
        entity_id_to_name = {}
        async with self._database_pool.acquire() as conn:
            if control_ids:
                rows = await conn.fetch(
                    'SELECT id::text, name FROM "05_grc_library"."41_vw_control_detail" WHERE id = ANY($1::uuid[])',
                    control_ids
                )
                for r in rows:
                    entity_id_to_name[r["id"]] = r["name"]
                    
            if risk_ids:
                rows = await conn.fetch(
                    'SELECT id::text, title FROM "14_risk_registry"."40_vw_risk_detail" WHERE id = ANY($1::uuid[])',
                    risk_ids
                )
                for r in rows:
                    entity_id_to_name[r["id"]] = r["title"]
        
        # Map task ID to resolved name
        task_id_to_name = {}
        for t in tasks:
            if t.entity_id in entity_id_to_name:
                task_id_to_name[t.id] = entity_id_to_name[t.entity_id]
        return task_id_to_name

    async def list_task_controls(
        self,
        *,
        user_id: str,
        task_id: str,
    ) -> list[any]:
        # Avoiding circular dependency by using localized imports if needed, 
        # but here we already have repo access.
        async with self._database_pool.acquire() as conn:
            task = await self._repository.get_task_detail(conn, task_id)
            if not task:
                raise NotFoundError(f"Task '{task_id}' not found")
            
            control_ids = []
            if task.entity_type == "control" and task.entity_id:
                control_ids.append(task.entity_id)
            elif task.entity_type == "risk" and task.entity_id:
                mappings = await self._mapping_repository.list_control_mappings(conn, task.entity_id)
                control_ids = [m.control_id for m in mappings]
            
            if not control_ids:
                return []
            
            controls = []
            for cid in control_ids:
                ctrl = await self._control_repository.get_control_by_id(conn, cid)
                if ctrl:
                    # Map to a dictionary matching ControlResponse
                    controls.append(ctrl)
            return controls

    async def get_task_summary(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        engagement_id: str | None = None,
    ) -> TaskSummaryResponse:
        assignee_mode = is_assignee_portal_mode(portal_mode)
        accessible_engagement_ids: list[str] | None = None
        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            if not assignee_mode:
                await require_permission(
                    conn, user_id, "tasks.view",
                    scope_org_id=org_id, scope_workspace_id=workspace_id,
                )
                accessible_engagement_ids = await self._engagement_repository.list_accessible_engagement_ids_for_user(
                    conn,
                    user_id=user_id,
                    org_id=org_id,
                )

        cache_key = (
            f"tasks:summary:{tenant_key}:{org_id or 'all'}:{workspace_id or 'all'}:"
            f"{engagement_id or 'all'}:"
            f"{portal_mode or 'default'}:{user_id if assignee_mode else 'any'}"
        )
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return TaskSummaryResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            summary = await self._repository.get_task_summary(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
                scope_assignee_user_id=user_id if assignee_mode else None,
                engagement_id=engagement_id,
                accessible_engagement_ids=accessible_engagement_ids,
            )
        result = TaskSummaryResponse(
            open_count=summary["open_count"],
            in_progress_count=summary["in_progress_count"],
            pending_verification_count=summary["pending_verification_count"],
            resolved_count=summary["resolved_count"],
            cancelled_count=summary["cancelled_count"],
            overdue_count=summary["overdue_count"],
            resolved_this_week_count=summary.get("resolved_this_week_count", 0),
            by_type=[
                TaskTypeSummary(
                    task_type_code=t["task_type_code"],
                    task_type_name=t["task_type_name"],
                    count=t["count"],
                )
                for t in summary["by_type"]
            ],
        )
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_TASKS)
        return result

    async def create_task(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreateTaskRequest,
        portal_mode: str | None = None,
    ) -> TaskDetailResponse:
        if is_assignee_portal_mode(portal_mode):
            raise AuthorizationError("Assignee portal sessions cannot create tasks.")
        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.create",
                org_id=request.org_id,
                workspace_id=request.workspace_id,
            )
            await self._assert_task_engagement_boundary(
                conn,
                user_id=user_id,
                org_id=request.org_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
            )
        return await self.create_task_prevalidated(
            user_id=user_id,
            tenant_key=tenant_key,
            request=request,
            portal_mode=portal_mode,
        )

    async def create_task_prevalidated(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreateTaskRequest,
        portal_mode: str | None = None,
    ) -> TaskDetailResponse:
        if is_assignee_portal_mode(portal_mode):
            raise AuthorizationError("Assignee portal sessions cannot create tasks.")
        now = utc_now_sql()
        task_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            await self._repository.create_task(
                conn,
                task_id=task_id,
                tenant_key=tenant_key,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
                task_type_code=request.task_type_code,
                priority_code=request.priority_code,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                assignee_user_id=request.assignee_user_id,
                reporter_user_id=user_id,
                due_date=request.due_date,
                start_date=request.start_date,
                estimated_hours=request.estimated_hours,
                created_by=user_id,
                now=now,
            )
            # Set EAV properties
            await self._repository.set_task_property(
                conn,
                prop_id=str(uuid.uuid4()),
                task_id=task_id,
                property_key="title",
                property_value=request.title,
                actor_id=user_id,
                now=now,
            )
            if request.description is not None:
                await self._repository.set_task_property(
                    conn,
                    prop_id=str(uuid.uuid4()),
                    task_id=task_id,
                    property_key="description",
                    property_value=request.description,
                    actor_id=user_id,
                    now=now,
                )
            if request.acceptance_criteria is not None:
                await self._repository.set_task_property(
                    conn,
                    prop_id=str(uuid.uuid4()),
                    task_id=task_id,
                    property_key="acceptance_criteria",
                    property_value=request.acceptance_criteria,
                    actor_id=user_id,
                    now=now,
                )
            if request.remediation_plan is not None:
                await self._repository.set_task_property(
                    conn,
                    prop_id=str(uuid.uuid4()),
                    task_id=task_id,
                    property_key="remediation_plan",
                    property_value=request.remediation_plan,
                    actor_id=user_id,
                    now=now,
                )
            # Create initial 'created' event
            await self._event_repository.create_event(
                conn,
                event_id=str(uuid.uuid4()),
                task_id=task_id,
                event_type="created",
                old_value=None,
                new_value=None,
                comment=None,
                actor_id=user_id,
                now=now,
            )
            # Audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="task",
                    entity_id=task_id,
                    event_type=TaskAuditEventType.TASK_CREATED.value,
                    event_category=AuditEventCategory.TASK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "title": request.title,
                        "task_type_code": request.task_type_code,
                        "priority_code": request.priority_code,
                        "org_id": request.org_id,
                        "workspace_id": request.workspace_id,
                    },
                ),
            )
        await self._cache.delete_pattern(f"tasks:list:{tenant_key}:*")
        await self._cache.delete_pattern(f"tasks:summary:{tenant_key}:*")

        # Return full detail view
        async with self._database_pool.acquire() as conn:
            detail = await self._repository.get_task_detail(conn, task_id)
        return _task_detail_response(detail)

    async def update_task(
        self,
        *,
        user_id: str,
        task_id: str,
        request: UpdateTaskRequest,
        portal_mode: str | None = None,
    ) -> TaskDetailResponse:
        if is_assignee_portal_mode(portal_mode):
            raise AuthorizationError("Assignee portal sessions cannot update tasks.")
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            existing = await self._repository.get_task_by_id(conn, task_id)
            if existing is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            lifecycle_role = await self._get_task_engagement_lifecycle_role(
                conn,
                user_id=user_id,
                org_id=existing.org_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.update",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )
            await self._assert_task_engagement_boundary(
                conn,
                user_id=user_id,
                org_id=existing.org_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            if lifecycle_role == "blocked":
                raise AuthorizationError(
                    "This task is bound to an engagement that the current user cannot access."
                )
            self._assert_member_task_update_allowed(
                role=lifecycle_role,
                user_id=user_id,
                existing=existing,
                request=request,
            )

            # Validate status transition
            if request.status_code is not None and request.status_code != existing.status_code:
                allowed = TASK_STATUS_TRANSITIONS.get(existing.status_code, [])
                if request.status_code not in allowed:
                    raise ValidationError(
                        f"Cannot transition task from '{existing.status_code}' to '{request.status_code}'"
                    )
                # Check role-gated permission for this specific transition
                required_perm = TASK_TRANSITION_PERMISSION.get(
                    (existing.status_code, request.status_code)
                )
                if required_perm and lifecycle_role != "member":
                    await require_permission(
                        conn,
                        user_id,
                        required_perm,
                        org_id=existing.org_id,
                        workspace_id=existing.workspace_id,
                    )

            # Validate resolution
            if request.status_code in ("resolved",):
                # Resolution requires resolution_notes
                if not request.resolution_notes:
                    raise ValidationError("Resolution notes are required when resolving a task")

            # Determine completed_at
            completed_at = None
            if request.status_code is not None:
                is_terminal = await self._repository.is_terminal_status(conn, request.status_code)
                if is_terminal:
                    completed_at = now

            # Track changes for events
            old_assignee = existing.assignee_user_id
            old_start_date = existing.start_date

            task = await self._repository.update_task(
                conn,
                task_id,
                priority_code=request.priority_code,
                status_code=request.status_code,
                assignee_user_id=request.assignee_user_id,
                due_date=request.due_date,
                start_date=request.start_date,
                estimated_hours=request.estimated_hours,
                actual_hours=request.actual_hours,
                completed_at=completed_at,
                updated_by=user_id,
                now=now,
            )
            if task is None:
                raise NotFoundError(f"Task '{task_id}' not found")

            # Update EAV properties
            if request.title is not None:
                await self._repository.set_task_property(
                    conn, prop_id=str(uuid.uuid4()), task_id=task_id,
                    property_key="title", property_value=request.title,
                    actor_id=user_id, now=now,
                )
            if request.description is not None:
                await self._repository.set_task_property(
                    conn, prop_id=str(uuid.uuid4()), task_id=task_id,
                    property_key="description", property_value=request.description,
                    actor_id=user_id, now=now,
                )
            if request.acceptance_criteria is not None:
                await self._repository.set_task_property(
                    conn, prop_id=str(uuid.uuid4()), task_id=task_id,
                    property_key="acceptance_criteria", property_value=request.acceptance_criteria,
                    actor_id=user_id, now=now,
                )
            if request.resolution_notes is not None:
                await self._repository.set_task_property(
                    conn, prop_id=str(uuid.uuid4()), task_id=task_id,
                    property_key="resolution_notes", property_value=request.resolution_notes,
                    actor_id=user_id, now=now,
                )
            if request.remediation_plan is not None:
                await self._repository.set_task_property(
                    conn, prop_id=str(uuid.uuid4()), task_id=task_id,
                    property_key="remediation_plan", property_value=request.remediation_plan,
                    actor_id=user_id, now=now,
                )

            # Create task events for tracked changes
            if request.status_code is not None and request.status_code != existing.status_code:
                await self._event_repository.create_event(
                    conn, event_id=str(uuid.uuid4()), task_id=task_id,
                    event_type="status_changed",
                    old_value=existing.status_code, new_value=request.status_code,
                    comment=None, actor_id=user_id, now=now,
                )
            if request.priority_code is not None and request.priority_code != existing.priority_code:
                await self._event_repository.create_event(
                    conn, event_id=str(uuid.uuid4()), task_id=task_id,
                    event_type="priority_changed",
                    old_value=existing.priority_code, new_value=request.priority_code,
                    comment=None, actor_id=user_id, now=now,
                )
            if request.assignee_user_id is not None and request.assignee_user_id != old_assignee:
                await self._event_repository.create_event(
                    conn, event_id=str(uuid.uuid4()), task_id=task_id,
                    event_type="reassigned",
                    old_value=old_assignee, new_value=request.assignee_user_id,
                    comment=None, actor_id=user_id, now=now,
                )
            if request.due_date is not None and request.due_date != existing.due_date:
                await self._event_repository.create_event(
                    conn, event_id=str(uuid.uuid4()), task_id=task_id,
                    event_type="due_date_changed",
                    old_value=existing.due_date, new_value=request.due_date,
                    comment=None, actor_id=user_id, now=now,
                )
            if request.start_date is not None and request.start_date != old_start_date:
                await self._event_repository.create_event(
                    conn, event_id=str(uuid.uuid4()), task_id=task_id,
                    event_type="start_date_changed",
                    old_value=old_start_date, new_value=request.start_date,
                    comment=None, actor_id=user_id, now=now,
                )

            # Audit
            audit_type = TaskAuditEventType.TASK_STATUS_CHANGED if request.status_code else TaskAuditEventType.TASK_UPDATED
            _base_url = (
                getattr(self._settings, "notification_tracking_base_url", "") or
                getattr(self._settings, "platform_base_url", "") or ""
            ).rstrip("/")
            _task_url = f"{_base_url}/tasks/{task_id}" if _base_url else f"/tasks/{task_id}"
            # Fetch task title for notification template (lightweight property lookup)
            _task_title = await conn.fetchval(
                """SELECT property_value FROM "08_tasks"."20_dtl_task_properties"
<<<<<<< HEAD
                   WHERE task_id = $1::uuid AND property_key = 'title' AND is_deleted = FALSE
=======
                   WHERE task_id = $1::uuid AND property_key = 'title'
>>>>>>> 1a112f033d8de616bfb53285cd3a8d5ad243fa84
                   LIMIT 1""",
                task_id,
            ) or ""
            _status_audit_entry = AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=existing.tenant_key,
                entity_type="task",
                entity_id=task_id,
                event_type=audit_type.value,
                event_category=AuditEventCategory.TASK.value,
                occurred_at=now,
                actor_id=user_id,
                actor_type="user",
                properties={
                    k: str(v) for k, v in request.model_dump(exclude_none=True).items()
                } | {
                    "task.title": _task_title,
                    "task.status.previous": existing.status_code or "",
                    "task.status.new": request.status_code or existing.status_code or "",
                    "task.url": _task_url,
                },
            )
            await self._audit_writer.write_entry(conn, _status_audit_entry)

        await self._cache.delete_pattern(f"task:{task_id}:*")
        await self._cache.delete_pattern(f"tasks:list:{existing.tenant_key}:*")
        await self._cache.delete_pattern(f"tasks:summary:{existing.tenant_key}:*")

        # Re-fetch detail view (needed for title in notifications and full response)
        async with self._database_pool.acquire() as conn:
            detail = await self._repository.get_task_detail(conn, task_id)

        # Notify task participants when status changes (fire and forget, best-effort)
        if request.status_code and request.status_code != existing.status_code and self._settings.notification_enabled:
            _dispatcher_module = import_module(
                "backend.04_notifications.02_dispatcher.dispatcher"
            )
            NotificationDispatcher = _dispatcher_module.NotificationDispatcher
            _dispatcher = NotificationDispatcher(
                database_pool=self._database_pool,
                settings=self._settings,
            )
            _recipients = {existing.assignee_user_id, existing.reporter_user_id} - {user_id, None}
            for _recipient_id in _recipients:
                asyncio.create_task(
                    _dispatcher.dispatch_direct(
                        _status_audit_entry,
                        target_user_id=_recipient_id,
                        template_code="task_status_changed_email",
                        notification_type_code="task_status_changed",
                    )
                )

        # Auto-trigger evidence re-evaluation when acceptance criteria changes
        if request.acceptance_criteria is not None:
            asyncio.create_task(
                self._trigger_evidence_check_after_criteria_change(
                    task_id=task_id,
                    tenant_key=existing.tenant_key,
                    org_id=str(existing.org_id) if existing.org_id else "",
                    user_id=user_id,
                )
            )

        return _task_detail_response(detail)

    async def submit_task_for_review(
        self,
        *,
        user_id: str,
        task_id: str,
        portal_mode: str | None = None,
    ) -> TaskDetailResponse:
        now = utc_now_sql()
        assignee_mode = is_assignee_portal_mode(portal_mode)
        allowed_from_states = {"open", "in_progress", "overdue"}
        target_status = "pending_verification"

        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            existing = await self._repository.get_task_by_id(conn, task_id)
            if existing is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            lifecycle_role = await self._get_task_engagement_lifecycle_role(
                conn,
                user_id=user_id,
                org_id=existing.org_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )

            if assignee_mode:
                await assert_assignee_task_entity_access(
                    conn,
                    user_id=user_id,
                    portal_mode=portal_mode,
                    entity_type="task",
                    entity_id=task_id,
                )
            else:
                await self._require_task_permission(
                    conn,
                    user_id=user_id,
                    permission_code="tasks.update",
                    org_id=existing.org_id,
                    workspace_id=existing.workspace_id,
                )
                await self._assert_task_engagement_boundary(
                    conn,
                    user_id=user_id,
                    org_id=existing.org_id,
                    entity_type=existing.entity_type,
                    entity_id=existing.entity_id,
                )
                if lifecycle_role == "member" and user_id not in {
                    existing.reporter_user_id,
                    existing.assignee_user_id,
                }:
                    raise AuthorizationError(
                        "Only the task creator or assignee can submit this engagement task for review."
                    )
                if lifecycle_role == "blocked":
                    raise AuthorizationError(
                        "This task is bound to an engagement that the current user cannot access."
                    )

            if existing.status_code == target_status:
                raise ValidationError("Task is already pending verification.")
            if existing.status_code not in allowed_from_states:
                raise ValidationError(
                    f"Task in status '{existing.status_code}' cannot be submitted for review."
                )

            updated = await self._repository.update_task(
                conn,
                task_id,
                status_code=target_status,
                updated_by=user_id,
                now=now,
            )
            if updated is None:
                raise NotFoundError(f"Task '{task_id}' not found")

            await self._event_repository.create_event(
                conn,
                event_id=str(uuid.uuid4()),
                task_id=task_id,
                event_type="status_changed",
                old_value=existing.status_code,
                new_value=target_status,
                comment="Submitted for review and approval.",
                actor_id=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="task",
                    entity_id=task_id,
                    event_type=TaskAuditEventType.TASK_STATUS_CHANGED.value,
                    event_category=AuditEventCategory.TASK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "old_status": existing.status_code,
                        "new_status": target_status,
                        "source_action": "submit_for_review",
                        "portal_mode": portal_mode or "",
                    },
                ),
            )

        await self._cache.delete_pattern(f"task:{task_id}:*")
        await self._cache.delete_pattern(f"tasks:list:{existing.tenant_key}:*")
        await self._cache.delete_pattern(f"tasks:summary:{existing.tenant_key}:*")

        async with self._database_pool.acquire() as conn:
            detail = await self._repository.get_task_detail(
                conn,
                task_id,
                scope_assignee_user_id=user_id if assignee_mode else None,
            )
        if detail is None:
            raise NotFoundError(f"Task '{task_id}' not found")
        return _task_detail_response(detail)

    async def _trigger_evidence_check_after_criteria_change(
        self,
        *,
        task_id: str,
        tenant_key: str,
        org_id: str,
        user_id: str,
    ) -> None:
        """Fire-and-forget: enqueue evidence check after acceptance criteria changes."""
        try:
            _jh = import_module("backend.20_ai.16_evidence_checker.job_handler")
            async with self._database_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id::text
                    FROM "09_attachments"."01_fct_attachments"
                    WHERE entity_type = 'task' AND entity_id = $1::uuid AND is_deleted = FALSE
                    """,
                    task_id,
                )
            attachment_ids = [r["id"] for r in rows]
            if not attachment_ids:
                return  # No attachments yet — nothing to evaluate
            await _jh.enqueue_evidence_check(
                pool=self._database_pool.pool,
                tenant_key=tenant_key,
                org_id=org_id,
                task_id=task_id,
                triggered_by_attachment_id=None,
                attachment_ids=attachment_ids,
                user_id=user_id,
            )
        except Exception as exc:
            self._logger.warning(
                "evidence_check.criteria_change_trigger_failed: %s", exc,
                extra={"task_id": task_id},
            )

    async def bulk_update_tasks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: BulkUpdateTaskRequest,
        portal_mode: str | None = None,
    ) -> BulkUpdateTaskResponse:
        if is_assignee_portal_mode(portal_mode):
            raise AuthorizationError("Assignee portal sessions cannot bulk-update tasks.")
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            for task_id in request.task_ids:
                task = await self._repository.get_task_by_id(conn, task_id)
                if task is None:
                    raise NotFoundError(f"Task '{task_id}' not found")
                lifecycle_role = await self._get_task_engagement_lifecycle_role(
                    conn,
                    user_id=user_id,
                    org_id=task.org_id,
                    entity_type=task.entity_type,
                    entity_id=task.entity_id,
                )
                await self._require_task_permission(
                    conn,
                    user_id=user_id,
                    permission_code="tasks.update",
                    org_id=task.org_id,
                    workspace_id=task.workspace_id,
                )
                await self._assert_task_engagement_boundary(
                    conn,
                    user_id=user_id,
                    org_id=task.org_id,
                    entity_type=task.entity_type,
                    entity_id=task.entity_id,
                )
                if lifecycle_role == "member":
                    raise AuthorizationError(
                        "Bulk updates for engagement-bound tasks require elevated engagement access."
                    )
                if lifecycle_role == "blocked":
                    raise AuthorizationError(
                        "This task set contains engagement-bound tasks that the current user cannot access."
                    )

        async with self._database_pool.acquire() as conn:
            updated_count = await self._repository.bulk_update_tasks(
                conn,
                task_ids=request.task_ids,
                tenant_key=tenant_key,
                status_code=request.status_code,
                priority_code=request.priority_code,
                assignee_user_id=request.assignee_user_id,
                updated_by=user_id,
                now=now,
            )

        if updated_count > 0:
            await self._cache.delete_pattern(f"tasks:list:{tenant_key}:*")
            await self._cache.delete_pattern(f"tasks:summary:{tenant_key}:*")
            for task_id in request.task_ids:
                await self._cache.delete_pattern(f"task:{task_id}:*")

        return BulkUpdateTaskResponse(updated_count=updated_count)

    async def clone_task(
        self,
        *,
        user_id: str,
        task_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
    ) -> TaskDetailResponse:
        """Clone a task — copies all EAV properties and creates a new task in 'open' status."""
        if is_assignee_portal_mode(portal_mode):
            raise AuthorizationError("Assignee portal sessions cannot clone tasks.")
        now = utc_now_sql()
        new_task_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            existing = await self._repository.get_task_detail(conn, task_id)
            if existing is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            lifecycle_role = await self._get_task_engagement_lifecycle_role(
                conn,
                user_id=user_id,
                org_id=existing.org_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.create",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )
            await self._assert_task_engagement_boundary(
                conn,
                user_id=user_id,
                org_id=existing.org_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            if lifecycle_role == "member" and existing.reporter_user_id != user_id:
                raise AuthorizationError(
                    "Only the task creator or elevated engagement users can clone this engagement task."
                )
            if lifecycle_role == "blocked":
                raise AuthorizationError(
                    "This task is bound to an engagement that the current user cannot access."
                )

            await self._repository.create_task(
                conn,
                task_id=new_task_id,
                tenant_key=existing.tenant_key,
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
                task_type_code=existing.task_type_code,
                priority_code=existing.priority_code,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                assignee_user_id=None,
                reporter_user_id=user_id,
                due_date=None,
                start_date=None,
                estimated_hours=existing.estimated_hours,
                created_by=user_id,
                now=now,
            )
            # Copy EAV properties — prefix title with "Copy of "
            title = f"Copy of {existing.title}" if existing.title else "Copy of task"
            await self._repository.set_task_property(
                conn, prop_id=str(uuid.uuid4()), task_id=new_task_id,
                property_key="title", property_value=title,
                actor_id=user_id, now=now,
            )
            if existing.description:
                await self._repository.set_task_property(
                    conn, prop_id=str(uuid.uuid4()), task_id=new_task_id,
                    property_key="description", property_value=existing.description,
                    actor_id=user_id, now=now,
                )
            if existing.acceptance_criteria:
                await self._repository.set_task_property(
                    conn, prop_id=str(uuid.uuid4()), task_id=new_task_id,
                    property_key="acceptance_criteria", property_value=existing.acceptance_criteria,
                    actor_id=user_id, now=now,
                )
            if existing.remediation_plan:
                await self._repository.set_task_property(
                    conn, prop_id=str(uuid.uuid4()), task_id=new_task_id,
                    property_key="remediation_plan", property_value=existing.remediation_plan,
                    actor_id=user_id, now=now,
                )
            await self._event_repository.create_event(
                conn, event_id=str(uuid.uuid4()), task_id=new_task_id,
                event_type="created", old_value=None, new_value=None,
                comment=f"Cloned from task {task_id}", actor_id=user_id, now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="task",
                    entity_id=new_task_id,
                    event_type=TaskAuditEventType.TASK_CREATED.value,
                    event_category=AuditEventCategory.TASK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"cloned_from": task_id, "title": title},
                ),
            )
        await self._cache.delete_pattern(f"tasks:list:{existing.tenant_key}:*")
        async with self._database_pool.acquire() as conn:
            detail = await self._repository.get_task_detail(conn, new_task_id)
        return _task_detail_response(detail)

    async def delete_task(
        self,
        *,
        user_id: str,
        task_id: str,
        portal_mode: str | None = None,
    ) -> None:
        if is_assignee_portal_mode(portal_mode):
            raise AuthorizationError("Assignee portal sessions cannot delete tasks.")
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            existing = await self._repository.get_task_by_id(conn, task_id)
            if existing is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            lifecycle_role = await self._get_task_engagement_lifecycle_role(
                conn,
                user_id=user_id,
                org_id=existing.org_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.update",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )
            await self._assert_task_engagement_boundary(
                conn,
                user_id=user_id,
                org_id=existing.org_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            if lifecycle_role == "member":
                raise AuthorizationError(
                    "Deleting engagement-bound tasks requires elevated engagement access."
                )
            if lifecycle_role == "blocked":
                raise AuthorizationError(
                    "This task is bound to an engagement that the current user cannot access."
                )
            deleted = await self._repository.soft_delete_task(
                conn, task_id, deleted_by=user_id, now=now
            )
            if not deleted:
                raise NotFoundError(f"Task '{task_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="task",
                    entity_id=task_id,
                    event_type=TaskAuditEventType.TASK_DELETED.value,
                    event_category=AuditEventCategory.TASK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
        await self._cache.delete_pattern(f"task:{task_id}:*")
        await self._cache.delete_pattern(f"tasks:list:{existing.tenant_key}:*")
        await self._cache.delete_pattern(f"tasks:summary:{existing.tenant_key}:*")

    async def export_tasks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        status_code: str | None = None,
        priority_code: str | None = None,
        task_type_code: str | None = None,
        assignee_user_id: str | None = None,
        is_overdue: bool | None = None,
        fmt: str = "csv",
        simplified: bool = False,
    ):
        """Export tasks as CSV, JSON, or XLSX."""
        result = await self.list_tasks(
            user_id=user_id, tenant_key=tenant_key, portal_mode=portal_mode,
            org_id=org_id, workspace_id=workspace_id,
            status_code=status_code, priority_code=priority_code,
            task_type_code=task_type_code, assignee_user_id=assignee_user_id,
            is_overdue=is_overdue, limit=5000, offset=0,
        )
        rows = []
        for task in result.items:
            row = {
                "title": task.title or "",
                "task_type": task.task_type_name or task.task_type_code or "",
                "priority": task.priority_name or task.priority_code or "",
                "status": task.status_name or task.status_code or "",
                "due_date": task.due_date or "",
                "start_date": task.start_date or "",
                "estimated_hours": task.estimated_hours or "",
                "actual_hours": task.actual_hours or "",
                "entity_type": task.entity_type or "",
                "entity_id": task.entity_id or "",
                "description": getattr(task, "description", "") or "",
            }
            if not simplified:
                row["id"] = task.id
                row["assignee_user_id"] = task.assignee_user_id or ""
                row["reporter_user_id"] = task.reporter_user_id or ""
            rows.append(row)

        if simplified:
            columns = ["title", "task_type", "priority", "status", "due_date",
                       "start_date", "estimated_hours", "actual_hours",
                       "entity_type", "entity_id", "description"]
        else:
            columns = ["id", "title", "task_type", "priority", "status",
                       "assignee_user_id", "reporter_user_id",
                       "due_date", "start_date", "estimated_hours", "actual_hours",
                       "entity_type", "entity_id", "description"]

        if fmt == "json":
            data = to_json(rows)
        elif fmt == "xlsx":
            data = to_xlsx(rows, columns, sheet_name="Tasks")
        else:
            data = to_csv(rows, columns)

        return make_streaming_response(data, fmt, "tasks_export")

    async def import_tasks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        org_id: str | None,
        workspace_id: str | None,
        file_bytes: bytes,
        filename: str,
        dry_run: bool = False,
    ):
        """Import tasks from CSV or JSON."""
        if is_assignee_portal_mode(portal_mode):
            raise AuthorizationError("Assignee portal sessions cannot import tasks.")
        from .schemas import ImportTaskError, ImportTasksResult

        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)

        try:
            rows = parse_import(file_bytes, filename)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        created = 0
        errors: list[ImportTaskError] = []

        for row_idx, row in enumerate(rows, start=2):
            title = (row.get("title") or "").strip()
            if not title:
                errors.append(ImportTaskError(row=row_idx, field="title", message="title is required"))
                continue
            try:
                if not dry_run:
                    from .schemas import CreateTaskRequest
                    req = CreateTaskRequest(
                        title=title,
                        task_type_code=row.get("task_type_code") or row.get("task_type") or "general",
                        priority_code=row.get("priority_code") or row.get("priority") or "medium",
                        status_code=row.get("status_code") or row.get("status") or "open",
                        description=row.get("description") or None,
                        due_date=row.get("due_date") or None,
                        start_date=row.get("start_date") or None,
                        estimated_hours=float(row["estimated_hours"]) if row.get("estimated_hours") else None,
                        actual_hours=float(row["actual_hours"]) if row.get("actual_hours") else None,
                        org_id=org_id,
                        workspace_id=workspace_id,
                    )
                    await self.create_task(user_id=user_id, tenant_key=tenant_key, request=req)
                created += 1
            except Exception as exc:
                errors.append(ImportTaskError(row=row_idx, key=title, message=str(exc)))

        return ImportTasksResult(created=created, updated=0, errors=errors, dry_run=dry_run)

    async def get_import_template(self, *, fmt: str = "csv"):
        """Return a downloadable import template for tasks."""
        columns = ["title", "task_type_code", "priority_code", "status_code",
                   "due_date", "start_date", "estimated_hours", "actual_hours",
                   "entity_type", "entity_id", "description"]
        examples = {
            "title": "Review MFA implementation",
            "task_type_code": "general",
            "priority_code": "medium",
            "status_code": "open",
            "due_date": "2026-04-01",
            "start_date": "2026-03-15",
            "estimated_hours": "4",
            "actual_hours": "",
            "entity_type": "control",
            "entity_id": "",
            "description": "Verify MFA is properly configured",
        }
        if fmt == "xlsx":
            data = to_xlsx_template(columns, examples, "Tasks Template")
        else:
            data = to_csv([examples], columns)
        return make_streaming_response(data, fmt, "tasks_import_template")


def _task_detail_response(t, entity_name: str | None = None) -> TaskDetailResponse:
    return TaskDetailResponse(
        id=t.id,
        tenant_key=t.tenant_key,
        org_id=t.org_id,
        workspace_id=t.workspace_id,
        task_type_code=t.task_type_code,
        task_type_name=t.task_type_name,
        priority_code=t.priority_code,
        priority_name=t.priority_name,
        status_code=t.status_code,
        status_name=t.status_name,
        is_terminal=t.is_terminal,
        entity_type=t.entity_type,
        entity_id=t.entity_id,
        assignee_user_id=t.assignee_user_id,
        reporter_user_id=t.reporter_user_id,
        due_date=t.due_date,
        start_date=t.start_date,
        completed_at=t.completed_at,
        estimated_hours=t.estimated_hours,
        actual_hours=t.actual_hours,
        is_active=t.is_active,
        created_at=t.created_at,
        updated_at=t.updated_at,
        title=t.title,
        description=t.description,
        acceptance_criteria=t.acceptance_criteria,
        resolution_notes=t.resolution_notes,
        remediation_plan=t.remediation_plan,
        co_assignee_count=t.co_assignee_count,
        blocker_count=t.blocker_count,
        comment_count=t.comment_count,
        entity_name=entity_name,
    )
