from __future__ import annotations

import uuid
from importlib import import_module

from .repository import TestMappingRepository
from .schemas import (
    CreateTestMappingRequest,
    TestMappingListResponse,
    TestMappingResponse,
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
_constants_module = import_module("backend.05_grc_library.constants")
_auto_task_module = import_module("backend.07_tasks._auto_task")
_tests_repo_module = import_module("backend.05_grc_library.06_tests.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
FrameworkAuditEventType = _constants_module.FrameworkAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
auto_create_task = _auto_task_module.auto_create_task
TestRepository = _tests_repo_module.TestRepository


@instrument_class_methods(namespace="grc.test_mappings.service", logger_name="backend.grc.test_mappings.instrumentation")
class TestMappingService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TestMappingRepository()
        self._test_repository = TestRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.test_mappings")

    async def list_mappings(self, *, user_id: str, test_id: str) -> TestMappingListResponse:
        async with self._database_pool.acquire() as conn:
            test = await self._test_repository.get_test_by_id(conn, test_id)
            if test is None:
                raise NotFoundError(f"Test '{test_id}' not found")
            await require_permission(
                conn,
                user_id,
                "tests.view",
                scope_org_id=test.scope_org_id,
                scope_workspace_id=test.scope_workspace_id,
            )
            records = await self._repository.list_mappings(conn, control_test_id=test_id)
        items = [_mapping_response(r) for r in records]
        return TestMappingListResponse(items=items, total=len(items))

    async def create_mapping(
        self, *, user_id: str, tenant_key: str, test_id: str, request: CreateTestMappingRequest
    ) -> TestMappingResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                test = await self._test_repository.get_test_by_id(conn, test_id)
                if test is None:
                    raise NotFoundError(f"Test '{test_id}' not found")
                await require_permission(
                    conn,
                    user_id,
                    "tests.create",
                    scope_org_id=test.scope_org_id,
                    scope_workspace_id=test.scope_workspace_id,
                )
                record = await self._repository.create_mapping(
                    conn,
                    mapping_id=str(uuid.uuid4()),
                    control_test_id=test_id,
                    control_id=request.control_id,
                    is_primary=request.is_primary,
                    sort_order=request.sort_order,
                    created_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="test_mapping",
                        entity_id=record.id,
                        event_type=FrameworkAuditEventType.TEST_MAPPING_CREATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "control_test_id": test_id,
                            "control_id": request.control_id,
                        },
                    ),
                )
                # Auto-create evidence collection task if requested and org context provided
                if request.auto_create_evidence_task and request.org_id and request.workspace_id:
                    control_label = record.control_name or record.control_code or request.control_id
                    await auto_create_task(
                        conn,
                        tenant_key=tenant_key,
                        org_id=request.org_id,
                        workspace_id=request.workspace_id,
                        task_type_code="evidence_collection",
                        priority_code="medium",
                        title=f"Collect evidence for control: {control_label}",
                        description=(
                            f"Evidence collection required for control '{control_label}'. "
                            "Upload supporting documentation and artifacts to satisfy this control test."
                        ),
                        entity_type="control",
                        entity_id=request.control_id,
                        reporter_user_id=user_id,
                    )
        return _mapping_response(record)

    async def delete_mapping(
        self, *, user_id: str, tenant_key: str, test_id: str, mapping_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                test = await self._test_repository.get_test_by_id(conn, test_id)
                if test is None:
                    raise NotFoundError(f"Test '{test_id}' not found")
                await require_permission(
                    conn,
                    user_id,
                    "tests.delete",
                    scope_org_id=test.scope_org_id,
                    scope_workspace_id=test.scope_workspace_id,
                )
                deleted = await self._repository.delete_mapping(conn, mapping_id)
                if not deleted:
                    raise NotFoundError(f"Test mapping '{mapping_id}' not found")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="test_mapping",
                        entity_id=mapping_id,
                        event_type=FrameworkAuditEventType.TEST_MAPPING_DELETED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"control_test_id": test_id},
                    ),
                )
            
            
def _mapping_response(r) -> TestMappingResponse:
    return TestMappingResponse(
        id=r.id,
        control_test_id=r.control_test_id,
        control_id=r.control_id,
        is_primary=r.is_primary,
        sort_order=r.sort_order,
        created_at=r.created_at,
        created_by=r.created_by,
        control_code=r.control_code,
        control_name=r.control_name,
        framework_code=r.framework_code,
    )
