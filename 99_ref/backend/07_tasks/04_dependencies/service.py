from __future__ import annotations

import uuid
from importlib import import_module

from .repository import DependencyRepository
from .schemas import AddDependencyRequest, TaskDependencyListResponse, TaskDependencyResponse

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

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
TaskAuditEventType = _constants_module.TaskAuditEventType
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_task_repo_module = import_module("backend.07_tasks.02_tasks.repository")
TaskRepository = _task_repo_module.TaskRepository
_events_repo_module = import_module("backend.07_tasks.05_events.repository")
EventRepository = _events_repo_module.EventRepository


@instrument_class_methods(namespace="tasks.dependencies.service", logger_name="backend.tasks.dependencies.instrumentation")
class DependencyService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = DependencyRepository()
        self._task_repository = TaskRepository()
        self._event_repository = EventRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.tasks.dependencies")

    async def _require_task_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        task,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=task.org_id,
            scope_workspace_id=task.workspace_id,
        )

    async def list_dependencies(
        self, *, user_id: str, task_id: str
    ) -> TaskDependencyListResponse:
        async with self._database_pool.acquire() as conn:
            task = await self._task_repository.get_task_by_id(conn, task_id)
            if task is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.view",
                task=task,
            )

        async with self._database_pool.acquire() as conn:
            blockers = await self._repository.list_blockers(conn, task_id)
            blocked_by = await self._repository.list_blocked_by(conn, task_id)
        return TaskDependencyListResponse(
            blockers=[_dependency_response(d) for d in blockers],
            blocked_by=[_dependency_response(d) for d in blocked_by],
        )

    async def add_dependency(
        self, *, user_id: str, task_id: str, request: AddDependencyRequest
    ) -> TaskDependencyResponse:
        now = utc_now_sql()
        dependency_id = str(uuid.uuid4())
        blocked_task_id = task_id
        blocking_task_id = request.blocking_task_id

        async with self._database_pool.transaction() as conn:
            # Verify both tasks exist
            task = await self._task_repository.get_task_by_id(conn, blocked_task_id)
            if task is None:
                raise NotFoundError(f"Task '{blocked_task_id}' not found")
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.create",
                task=task,
            )
            blocking_task = await self._task_repository.get_task_by_id(conn, blocking_task_id)
            if blocking_task is None:
                raise NotFoundError(f"Blocking task '{blocking_task_id}' not found")

            # Cycle detection
            would_cycle = await self._repository.would_create_cycle(
                conn,
                blocking_task_id=blocking_task_id,
                blocked_task_id=blocked_task_id,
            )
            if would_cycle:
                raise ConflictError(
                    f"Adding dependency would create a cycle: "
                    f"task '{blocking_task_id}' already depends on task '{blocked_task_id}'"
                )

            dependency = await self._repository.add_dependency(
                conn,
                dependency_id=dependency_id,
                blocking_task_id=blocking_task_id,
                blocked_task_id=blocked_task_id,
                created_by=user_id,
                now=now,
            )
            # Create task event
            await self._event_repository.create_event(
                conn,
                event_id=str(uuid.uuid4()),
                task_id=blocked_task_id,
                event_type="dependency_added",
                old_value=None,
                new_value=blocking_task_id,
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
                    entity_id=blocked_task_id,
                    event_type=TaskAuditEventType.TASK_DEPENDENCY_ADDED.value,
                    event_category=AuditEventCategory.TASK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "blocking_task_id": blocking_task_id,
                        "blocked_task_id": blocked_task_id,
                    },
                ),
            )
        await self._cache.delete(f"task:{blocked_task_id}")
        return _dependency_response(dependency)

    async def remove_dependency(
        self, *, user_id: str, task_id: str, dependency_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            task = await self._task_repository.get_task_by_id(conn, task_id)
            if task is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.update",
                task=task,
            )
            removed = await self._repository.remove_dependency(
                conn, dependency_id=dependency_id, task_id=task_id
            )
            if not removed:
                raise NotFoundError(f"Dependency '{dependency_id}' not found for task '{task_id}'")
            # Create task event
            await self._event_repository.create_event(
                conn,
                event_id=str(uuid.uuid4()),
                task_id=task_id,
                event_type="dependency_removed",
                old_value=dependency_id,
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
                    event_type=TaskAuditEventType.TASK_DEPENDENCY_REMOVED.value,
                    event_category=AuditEventCategory.TASK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "dependency_id": dependency_id,
                    },
                ),
            )
        await self._cache.delete(f"task:{task_id}")


def _dependency_response(d) -> TaskDependencyResponse:
    return TaskDependencyResponse(
        id=d.id,
        blocking_task_id=d.blocking_task_id,
        blocked_task_id=d.blocked_task_id,
        created_at=d.created_at,
        created_by=d.created_by,
    )
