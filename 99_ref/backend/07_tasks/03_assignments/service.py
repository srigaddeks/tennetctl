from __future__ import annotations

import uuid
from importlib import import_module

from .repository import AssignmentRepository
from .schemas import AddAssignmentRequest, TaskAssignmentResponse

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
_auth_constants_module = import_module("backend.03_auth_manage.constants")
_auth_repo_module = import_module("backend.03_auth_manage.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry

_dispatcher_module = import_module("backend.04_notifications.02_dispatcher.dispatcher")
NotificationDispatcher = _dispatcher_module.NotificationDispatcher
AuditWriter = _audit_module.AuditWriter
TaskAuditEventType = _constants_module.TaskAuditEventType
AccountType = _auth_constants_module.AccountType
AuditEventType = _auth_constants_module.AuditEventType
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
AuthRepository = _auth_repo_module.AuthRepository

_task_repo_module = import_module("backend.07_tasks.02_tasks.repository")
TaskRepository = _task_repo_module.TaskRepository
_events_repo_module = import_module("backend.07_tasks.05_events.repository")
EventRepository = _events_repo_module.EventRepository


@instrument_class_methods(
    namespace="tasks.assignments.service",
    logger_name="backend.tasks.assignments.instrumentation",
)
class AssignmentService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AssignmentRepository()
        self._auth_repository = AuthRepository()
        self._task_repository = TaskRepository()
        self._event_repository = EventRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.tasks.assignments")

    async def list_assignments(
        self, *, user_id: str, task_id: str
    ) -> list[TaskAssignmentResponse]:
        async with self._database_pool.acquire() as conn:
            task = await self._task_repository.get_task_by_id(conn, task_id)
            if task is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            await require_permission(
                conn,
                user_id,
                "tasks.view",
                scope_org_id=task.org_id,
                scope_workspace_id=task.workspace_id,
            )

        async with self._database_pool.acquire() as conn:
            assignments = await self._repository.list_assignments(conn, task_id)
        return [_assignment_response(a) for a in assignments]

    async def add_assignment(
        self, *, user_id: str, task_id: str, request: AddAssignmentRequest
    ) -> TaskAssignmentResponse:
        now = utc_now_sql()
        assignment_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            task_detail = await self._task_repository.get_task_detail(conn, task_id)
            if task_detail is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            await require_permission(
                conn,
                user_id,
                "tasks.assign",
                scope_org_id=task_detail.org_id,
                scope_workspace_id=task_detail.workspace_id,
            )
            target_user_id = request.user_id
            if not target_user_id and request.email:
                target_user_id = await self._resolve_or_create_user_by_email(
                    conn,
                    tenant_key=task_detail.tenant_key,
                    email=str(request.email),
                    actor_user_id=user_id,
                    now=now,
                )
            if not target_user_id:
                raise ValidationError("Either user_id or email must be provided.")
            assignment = await self._repository.add_assignment(
                conn,
                assignment_id=assignment_id,
                task_id=task_id,
                user_id=target_user_id,
                role=request.role,
                assigned_by=user_id,
                now=now,
            )
            # Create task event
            await self._event_repository.create_event(
                conn,
                event_id=str(uuid.uuid4()),
                task_id=task_id,
                event_type="co_assignee_added",
                old_value=None,
                new_value=target_user_id,
                comment=f"Role: {request.role}",
                actor_id=user_id,
                now=now,
            )
            # Build assignee portal URL — task assignment emails link to /assignee/login,
            # not the regular task URL, because recipients authenticate via magic link portal.
            _assignee_base = getattr(self._settings, "magic_link_assignee_frontend_verify_url", "").rstrip("/")
            if not _assignee_base:
                _platform = getattr(self._settings, "platform_base_url", "").rstrip("/")
                _assignee_base = f"{_platform}/assignee/login" if _platform else "/assignee/login"
            _task_url = _assignee_base
            # Create audit entry for notification processing
            audit_entry = AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=task_detail.tenant_key,
                entity_type="task",
                entity_id=task_id,
                event_type="task_assigned",
                event_category="grc",
                occurred_at=now,
                actor_id=user_id,
                actor_type="user",
                properties={
                    "target_user_id": target_user_id,
                    "target_email": str(request.email) if request.email else "",
                    "role": request.role,
                    "task.title": task_detail.title or "",
                    "task.description": task_detail.description or "",
                    "task.priority": task_detail.priority_code or "",
                    "task.due_date": task_detail.due_date or "",
                    "task.url": _task_url,
                },
            )
            await self._audit_writer.write_entry(conn, audit_entry)

            # Dispatch notification for task assignment (fire and forget)
            if self._settings.notification_enabled:
                try:
                    dispatcher = NotificationDispatcher(
                        database_pool=self._database_pool,
                        settings=self._settings,
                    )
                    import asyncio as _asyncio

                    _asyncio.create_task(
                        dispatcher.dispatch_direct(
                            audit_entry,
                            target_user_id=target_user_id,
                            template_code="task_assigned_email",
                            notification_type_code="task_assigned",
                        )
                    )
                except Exception as e:
                    get_logger("backend.07_tasks.03_assignments.service").warning(
                        "notification_dispatch_failed",
                        exc_info=e,
                        extra={
                            "task_id": task_id,
                            "target_user_id": target_user_id,
                        },
                    )
        await self._cache.delete(f"task:{task_id}")
        return _assignment_response(assignment)

    async def _resolve_or_create_user_by_email(
        self,
        connection,
        *,
        tenant_key: str,
        email: str,
        actor_user_id: str,
        now,
    ) -> str:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise ValidationError("Email is required.")

        existing = await self._auth_repository.find_user_by_email_for_magic_link(
            connection,
            tenant_key=tenant_key,
            email=normalized_email,
        )
        if existing is not None:
            if (
                existing.is_deleted
                or not existing.is_active
                or existing.is_disabled
                or existing.is_locked
            ):
                raise ValidationError(
                    f"User '{normalized_email}' is not eligible for assignment."
                )
            await self._auth_repository.ensure_magic_link_account(
                connection,
                user_id=existing.user_id,
                tenant_key=tenant_key,
                now=now,
            )
            return existing.user_id

        new_user_id, _ = await self._auth_repository.create_external_user(
            connection,
            tenant_key=tenant_key,
            now=now,
        )
        await self._auth_repository.create_user_property(
            connection,
            user_id=new_user_id,
            property_key="email",
            property_value=normalized_email,
            created_by=actor_user_id,
            now=now,
        )
        await self._auth_repository.create_user_property(
            connection,
            user_id=new_user_id,
            property_key="email_verified",
            property_value="true",
            created_by=actor_user_id,
            now=now,
        )
        await self._auth_repository.create_user_property(
            connection,
            user_id=new_user_id,
            property_key="user_category_source",
            property_value="task_assignment_email",
            created_by=actor_user_id,
            now=now,
        )
        await self._auth_repository.create_user_account(
            connection,
            user_id=new_user_id,
            tenant_key=tenant_key,
            account_type_code=AccountType.MAGIC_LINK.value,
            is_primary=True,
            created_by=actor_user_id,
            now=now,
        )
        await self._auth_repository.add_user_to_external_collaborators_group(
            connection,
            user_id=new_user_id,
            tenant_key=tenant_key,
            now=now,
        )
        await self._audit_writer.write_entry(
            connection,
            AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="user",
                entity_id=new_user_id,
                event_type=AuditEventType.MAGIC_LINK_EXTERNAL_USER_CREATED.value,
                event_category=AuditEventCategory.AUTH.value,
                occurred_at=now,
                actor_id=actor_user_id,
                actor_type="user",
                properties={
                    "email": normalized_email,
                    "source": "task_assignment",
                    "user_category": "external_collaborator",
                },
            ),
        )
        self._logger.info(
            "task_assignment_external_user_created",
            extra={
                "email": normalized_email,
                "user_id": new_user_id,
                "actor_id": actor_user_id,
            },
        )
        return new_user_id

    async def remove_assignment(
        self, *, user_id: str, task_id: str, assignment_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            task = await self._task_repository.get_task_by_id(conn, task_id)
            if task is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            await require_permission(
                conn,
                user_id,
                "tasks.assign",
                scope_org_id=task.org_id,
                scope_workspace_id=task.workspace_id,
            )
            removed = await self._repository.remove_assignment(
                conn, assignment_id=assignment_id, task_id=task_id
            )
            if not removed:
                raise NotFoundError(
                    f"Assignment '{assignment_id}' not found on task '{task_id}'"
                )
            # Create task event
            await self._event_repository.create_event(
                conn,
                event_id=str(uuid.uuid4()),
                task_id=task_id,
                event_type="co_assignee_removed",
                old_value=assignment_id,
                new_value=None,
                comment=None,
                actor_id=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=task.tenant_key,
                    entity_type="task",
                    entity_id=task_id,
                    event_type=TaskAuditEventType.TASK_ASSIGNMENT_REMOVED.value,
                    event_category=AuditEventCategory.TASK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "assignment_id": assignment_id,
                    },
                ),
            )
        await self._cache.delete(f"task:{task_id}")


def _assignment_response(a) -> TaskAssignmentResponse:
    return TaskAssignmentResponse(
        id=a.id,
        task_id=a.task_id,
        user_id=a.user_id,
        role=a.role,
        assigned_at=a.assigned_at,
        assigned_by=a.assigned_by,
    )
