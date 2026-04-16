from __future__ import annotations

import uuid
from importlib import import_module

from .repository import TestRepository
from .schemas import (
    CreateTestRequest,
    TestListResponse,
    TestResponse,
    UpdateTestRequest,
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
_controls_repo_module = import_module("backend.05_grc_library.05_controls.repository")
_frameworks_repo_module = import_module(
    "backend.05_grc_library.02_frameworks.repository"
)

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
ControlRepository = _controls_repo_module.ControlRepository
FrameworkRepository = _frameworks_repo_module.FrameworkRepository


@instrument_class_methods(
    namespace="grc.tests.service", logger_name="backend.grc.tests.instrumentation"
)
class TestService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TestRepository()
        self._control_repository = ControlRepository()
        self._framework_repository = FrameworkRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.tests")

    async def _require_test_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=scope_org_id,
            scope_workspace_id=scope_workspace_id,
        )

    async def list_tests(
        self,
        *,
        user_id: str,
        tenant_key: str,
        search: str | None = None,
        test_type_code: str | None = None,
        is_platform_managed: bool | None = None,
        monitoring_frequency: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        sort_by: str = "name",
        sort_dir: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> TestListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "tests.view",
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
            records, total = await self._repository.list_tests(
                conn,
                tenant_key=tenant_key,
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
        items = [_test_response(r) for r in records]
        return TestListResponse(items=items, total=total)

    async def list_tests_for_control(
        self, *, user_id: str, control_id: str
    ) -> TestListResponse:
        async with self._database_pool.acquire() as conn:
            control = await self._control_repository.get_control_by_id(conn, control_id)
            if control is None:
                raise NotFoundError(f"Control '{control_id}' not found")
            framework = await self._framework_repository.get_framework_by_id(
                conn, control.framework_id
            )
            if framework is None:
                raise NotFoundError(f"Framework '{control.framework_id}' not found")
            await self._require_test_permission(
                conn,
                user_id=user_id,
                permission_code="tests.view",
                scope_org_id=framework.scope_org_id,
                scope_workspace_id=framework.scope_workspace_id,
            )
            records = await self._repository.list_tests_for_control(
                conn, control_id=control_id
            )
        items = [_test_response(r) for r in records]
        return TestListResponse(items=items, total=len(items))

    async def list_tests_available_for_control(
        self,
        *,
        user_id: str,
        tenant_key: str,
        control_id: str,
        search: str | None = None,
        limit: int = 50,
    ) -> TestListResponse:
        async with self._database_pool.acquire() as conn:
            control = await self._control_repository.get_control_by_id(conn, control_id)
            if control is None:
                raise NotFoundError(f"Control '{control_id}' not found")
            framework = await self._framework_repository.get_framework_by_id(
                conn, control.framework_id
            )
            if framework is None:
                raise NotFoundError(f"Framework '{control.framework_id}' not found")
            await self._require_test_permission(
                conn,
                user_id=user_id,
                permission_code="tests.view",
                scope_org_id=framework.scope_org_id,
                scope_workspace_id=framework.scope_workspace_id,
            )
            records = await self._repository.list_tests_available_for_control(
                conn,
                tenant_key=tenant_key,
                control_id=control_id,
                search=search,
                limit=limit,
            )
        items = [_test_response(r) for r in records]
        return TestListResponse(items=items, total=len(items))

    async def get_test(self, *, user_id: str, test_id: str) -> TestResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_test_by_id(conn, test_id)
            if record is None:
                raise NotFoundError(f"Test '{test_id}' not found")
            await self._require_test_permission(
                conn,
                user_id=user_id,
                permission_code="tests.view",
                scope_org_id=record.scope_org_id,
                scope_workspace_id=record.scope_workspace_id,
            )
        return _test_response(record)

    async def create_test(
        self, *, user_id: str, tenant_key: str, request: CreateTestRequest
    ) -> TestResponse:
        now = utc_now_sql()
        test_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await self._require_test_permission(
                    conn,
                    user_id=user_id,
                    permission_code="tests.create",
                    scope_org_id=request.scope_org_id,
                    scope_workspace_id=request.scope_workspace_id,
                )
                await self._repository.create_test(
                    conn,
                    test_id=test_id,
                    tenant_key=tenant_key,
                    test_code=request.test_code,
                    test_type_code=request.test_type_code,
                    integration_type=request.integration_type,
                    monitoring_frequency=request.monitoring_frequency,
                    is_platform_managed=request.is_platform_managed,
                    scope_org_id=request.scope_org_id,
                    scope_workspace_id=request.scope_workspace_id,
                    created_by=user_id,
                    now=now,
                )
                props: dict[str, str] = {}
                if request.name:
                    props["name"] = request.name
                if request.description:
                    props["description"] = request.description
                if request.evaluation_rule:
                    props["evaluation_rule"] = request.evaluation_rule
                if request.signal_type:
                    props["signal_type"] = request.signal_type
                if request.integration_guide:
                    props["integration_guide"] = request.integration_guide
                if request.properties:
                    props.update(request.properties)
                if props:
                    await self._repository.upsert_test_properties(
                        conn,
                        test_id=test_id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="control_test",
                        entity_id=test_id,
                        event_type=FrameworkAuditEventType.TEST_CREATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "test_code": request.test_code,
                            "name": request.name,
                        },
                    ),
                )
                record = await self._repository.get_test_by_id(conn, test_id)
        return _test_response(record)

    async def update_test(
        self, *, user_id: str, tenant_key: str, test_id: str, request: UpdateTestRequest
    ) -> TestResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                existing = await self._repository.get_test_by_id(conn, test_id)
                if existing is None:
                    raise NotFoundError(f"Test '{test_id}' not found")
                await self._require_test_permission(
                    conn,
                    user_id=user_id,
                    permission_code="tests.update",
                    scope_org_id=existing.scope_org_id,
                    scope_workspace_id=existing.scope_workspace_id,
                )
                updated = await self._repository.update_test(
                    conn,
                    test_id,
                    test_type_code=request.test_type_code,
                    integration_type=request.integration_type,
                    monitoring_frequency=request.monitoring_frequency,
                    is_platform_managed=request.is_platform_managed,
                    updated_by=user_id,
                    now=now,
                )
                if not updated:
                    raise NotFoundError(f"Test '{test_id}' not found")
                props: dict[str, str] = {}
                if request.name is not None:
                    props["name"] = request.name
                if request.description is not None:
                    props["description"] = request.description
                if request.evaluation_rule is not None:
                    props["evaluation_rule"] = request.evaluation_rule
                if request.signal_type is not None:
                    props["signal_type"] = request.signal_type
                if request.integration_guide is not None:
                    props["integration_guide"] = request.integration_guide
                if request.properties:
                    props.update(request.properties)
                if props:
                    await self._repository.upsert_test_properties(
                        conn,
                        test_id=test_id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="control_test",
                        entity_id=test_id,
                        event_type=FrameworkAuditEventType.TEST_UPDATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"test_code": request.test_type_code or ""},
                    ),
                )
                record = await self._repository.get_test_by_id(conn, test_id)
        return _test_response(record)

    async def delete_test(self, *, user_id: str, tenant_key: str, test_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                existing = await self._repository.get_test_by_id(conn, test_id)
                if existing is None:
                    raise NotFoundError(f"Test '{test_id}' not found")
                await self._require_test_permission(
                    conn,
                    user_id=user_id,
                    permission_code="tests.delete",
                    scope_org_id=existing.scope_org_id,
                    scope_workspace_id=existing.scope_workspace_id,
                )
                deleted = await self._repository.soft_delete_test(
                    conn,
                    test_id,
                    deleted_by=user_id,
                    now=now,
                )
                if not deleted:
                    raise NotFoundError(f"Test '{test_id}' not found")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="control_test",
                        entity_id=test_id,
                        event_type=FrameworkAuditEventType.TEST_DELETED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={},
                    ),
                )


def _test_response(r) -> TestResponse:
    return TestResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        test_code=r.test_code,
        test_type_code=r.test_type_code,
        test_type_name=r.test_type_name,
        integration_type=r.integration_type,
        monitoring_frequency=r.monitoring_frequency,
        is_platform_managed=r.is_platform_managed,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
        evaluation_rule=r.evaluation_rule,
        signal_type=r.signal_type,
        integration_guide=r.integration_guide,
        mapped_control_count=r.mapped_control_count,
        scope_org_id=r.scope_org_id,
        scope_workspace_id=r.scope_workspace_id,
    )
