from __future__ import annotations

import uuid
from importlib import import_module

from .repository import TestExecutionRepository
from .schemas import CreateTestExecutionRequest, UpdateTestExecutionRequest, TestExecutionResponse, TestExecutionListResponse

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_tests_repo_module = import_module("backend.05_grc_library.06_tests.repository")
_controls_repo_module = import_module("backend.05_grc_library.05_controls.repository")
_frameworks_repo_module = import_module("backend.05_grc_library.02_frameworks.repository")

NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
instrument_class_methods = _telemetry_module.instrument_class_methods
get_logger = _logging_module.get_logger
TestRepository = _tests_repo_module.TestRepository
ControlRepository = _controls_repo_module.ControlRepository
FrameworkRepository = _frameworks_repo_module.FrameworkRepository


@instrument_class_methods(namespace="grc.test_executions.service", logger_name="backend.grc.test_executions.instrumentation")
class TestExecutionService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TestExecutionRepository()
        self._test_repository = TestRepository()
        self._control_repository = ControlRepository()
        self._framework_repository = FrameworkRepository()
        self._audit_writer = AuditWriter(schema_name="05_grc_library")

    async def _resolve_scope(
        self,
        conn,
        *,
        control_test_id: str | None,
        control_id: str | None,
    ) -> tuple[str | None, str | None]:
        if control_test_id:
            test = await self._test_repository.get_test_by_id(conn, control_test_id)
            if test is None:
                raise NotFoundError(f"Test '{control_test_id}' not found")
            return test.scope_org_id, test.scope_workspace_id
        if control_id:
            control = await self._control_repository.get_control_by_id(conn, control_id)
            if control is None:
                raise NotFoundError(f"Control '{control_id}' not found")
            framework = await self._framework_repository.get_framework_by_id(conn, control.framework_id)
            if framework is None:
                raise NotFoundError(f"Framework '{control.framework_id}' not found")
            return framework.scope_org_id, framework.scope_workspace_id
        return None, None

    async def list_executions(
        self, *, user_id: str,
        control_test_id: str | None = None,
        control_id: str | None = None,
        result_status: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> TestExecutionListResponse:
        async with self._database_pool.acquire() as conn:
            scope_org_id, scope_workspace_id = await self._resolve_scope(
                conn,
                control_test_id=control_test_id,
                control_id=control_id,
            )
            await require_permission(
                conn,
                user_id,
                "controls.view",
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
            items, total = await self._repository.list_executions(
                conn, control_test_id=control_test_id, control_id=control_id,
                result_status=result_status, limit=limit, offset=offset,
            )
        return TestExecutionListResponse(items=[_to_response(r) for r in items], total=total)

    async def get_execution(self, *, user_id: str, execution_id: str) -> TestExecutionResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_execution(conn, execution_id)
            if record is None:
                raise NotFoundError(f"Execution '{execution_id}' not found")
            scope_org_id, scope_workspace_id = await self._resolve_scope(
                conn,
                control_test_id=record.control_test_id,
                control_id=record.control_id,
            )
            await require_permission(
                conn,
                user_id,
                "controls.view",
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
        return _to_response(record)

    async def create_execution(
        self, *, user_id: str, tenant_key: str, request: CreateTestExecutionRequest,
    ) -> TestExecutionResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                scope_org_id, scope_workspace_id = await self._resolve_scope(
                    conn,
                    control_test_id=request.control_test_id,
                    control_id=request.control_id,
                )
                await require_permission(
                    conn,
                    user_id,
                    "controls.update",
                    scope_org_id=scope_org_id,
                    scope_workspace_id=scope_workspace_id,
                )
                record = await self._repository.create_execution(
                    conn,
                    execution_id=str(uuid.uuid4()),
                    control_test_id=request.control_test_id,
                    control_id=request.control_id,
                    tenant_key=tenant_key,
                    result_status=request.result_status,
                    execution_type=request.execution_type,
                    executed_by=user_id,
                    notes=request.notes,
                    evidence_summary=request.evidence_summary,
                    score=request.score,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="test_execution",
                        entity_id=record.id,
                        event_type="test_executed",
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "control_test_id": request.control_test_id,
                            "result_status": request.result_status,
                            "execution_type": request.execution_type,
                        },
                    ),
                )
                # Fetch with JOINs inside the same transaction
                full = await self._repository.get_execution(conn, record.id)
        return _to_response(full or record)

    async def update_execution(
        self, *, user_id: str, execution_id: str, request: UpdateTestExecutionRequest,
    ) -> TestExecutionResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                existing = await self._repository.get_execution(conn, execution_id)
                if existing is None:
                    raise NotFoundError(f"Execution '{execution_id}' not found")
                scope_org_id, scope_workspace_id = await self._resolve_scope(
                    conn,
                    control_test_id=existing.control_test_id,
                    control_id=existing.control_id,
                )
                await require_permission(
                    conn,
                    user_id,
                    "controls.update",
                    scope_org_id=scope_org_id,
                    scope_workspace_id=scope_workspace_id,
                )
                record = await self._repository.update_execution(
                    conn, execution_id,
                    result_status=request.result_status,
                    notes=request.notes,
                    evidence_summary=request.evidence_summary,
                    score=request.score,
                    updated_by=user_id,
                    now=now,
                )
                if record is None:
                    raise NotFoundError(f"Execution '{execution_id}' not found")
        async with self._database_pool.acquire() as conn:
            full = await self._repository.get_execution(conn, record.id)
        return _to_response(full or record)


def _to_response(r) -> TestExecutionResponse:
    return TestExecutionResponse(
        id=r.id,
        control_test_id=r.control_test_id,
        control_id=r.control_id,
        tenant_key=r.tenant_key,
        result_status=r.result_status,
        execution_type=r.execution_type,
        executed_by=r.executed_by,
        executed_at=r.executed_at,
        notes=r.notes,
        evidence_summary=r.evidence_summary,
        score=r.score,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        test_code=r.test_code,
        test_name=r.test_name,
    )
