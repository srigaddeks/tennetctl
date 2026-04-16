from __future__ import annotations

import uuid
from importlib import import_module

from .repository import TestScenarioRepository
from .schemas import (
    AddTestCaseRequest,
    CreateScenarioRequest,
    ScenarioListResponse,
    ScenarioResponse,
    TestCaseResponse,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.25_agent_sandbox.constants")

DatabasePool = _database_module.DatabasePool
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AgentSandboxAuditEventType = _constants_module.AgentSandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_PREFIX = "asb:scenarios"


@instrument_class_methods(namespace="agent_sandbox.test_scenarios.service", logger_name="backend.agent_sandbox.test_scenarios.instrumentation")
class TestScenarioService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TestScenarioRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")

    async def list_scenarios(
        self, *, user_id: str, org_id: str, agent_id: str | None = None,
        limit: int = 100, offset: int = 0,
    ) -> ScenarioListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            records, total = await self._repository.list_scenarios(
                conn, org_id, agent_id=agent_id, limit=limit, offset=offset,
            )
        return ScenarioListResponse(
            items=[_scenario_response(r) for r in records], total=total,
        )

    async def get_scenario(self, *, user_id: str, scenario_id: str) -> ScenarioResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            record = await self._repository.get_scenario_by_id(conn, scenario_id)
            if record is None:
                raise NotFoundError(f"Scenario '{scenario_id}' not found")
            cases = await self._repository.list_test_cases(conn, scenario_id)
        resp = _scenario_response(record)
        resp.test_cases = [
            TestCaseResponse(
                id=c.id, scenario_id=c.scenario_id, case_index=c.case_index,
                input_messages=c.input_messages, initial_context=c.initial_context,
                expected_behavior=c.expected_behavior,
                evaluation_method_code=c.evaluation_method_code,
                evaluation_config=c.evaluation_config,
                is_active=c.is_active, created_at=c.created_at,
            )
            for c in cases
        ]
        return resp

    async def create_scenario(
        self, *, user_id: str, tenant_key: str, org_id: str, request: CreateScenarioRequest,
    ) -> ScenarioResponse:
        now = utc_now_sql()
        scenario_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            async with conn.transaction():
                await self._repository.create_scenario(
                    conn, id=scenario_id, tenant_key=tenant_key, org_id=org_id,
                    workspace_id=request.workspace_id, scenario_code=request.scenario_code,
                    scenario_type_code=request.scenario_type_code, agent_id=request.agent_id,
                    created_by=user_id, now=now,
                )
                if request.properties:
                    await self._repository.upsert_properties(
                        conn, scenario_id, request.properties, created_by=user_id, now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()), tenant_key=tenant_key,
                        entity_type="test_scenario", entity_id=scenario_id,
                        event_type="created",
                        event_category=AgentSandboxAuditEventType.TEST_SCENARIO_CREATED,
                        actor_id=user_id, occurred_at=now,
                        properties={"scenario_code": request.scenario_code},
                    ),
                )
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self.get_scenario(user_id=user_id, scenario_id=scenario_id)

    async def delete_scenario(
        self, *, user_id: str, tenant_key: str, org_id: str, scenario_id: str,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            deleted = await self._repository.soft_delete_scenario(
                conn, scenario_id, deleted_by=user_id, now=now,
            )
            if not deleted:
                raise NotFoundError(f"Scenario '{scenario_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()), tenant_key=tenant_key,
                    entity_type="test_scenario", entity_id=scenario_id,
                    event_type="deleted",
                    event_category=AgentSandboxAuditEventType.TEST_SCENARIO_DELETED,
                    actor_id=user_id, occurred_at=now, properties={},
                ),
            )
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    async def add_test_case(
        self, *, user_id: str, scenario_id: str, request: AddTestCaseRequest,
    ) -> TestCaseResponse:
        now = utc_now_sql()
        case_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            scenario = await self._repository.get_scenario_by_id(conn, scenario_id)
            if scenario is None:
                raise NotFoundError(f"Scenario '{scenario_id}' not found")
            case_index = await self._repository.get_next_case_index(conn, scenario_id)
            await self._repository.add_test_case(
                conn, id=case_id, scenario_id=scenario_id, case_index=case_index,
                input_messages=request.input_messages, initial_context=request.initial_context,
                expected_behavior=request.expected_behavior,
                evaluation_method_code=request.evaluation_method_code,
                evaluation_config=request.evaluation_config,
                created_by=user_id, now=now,
            )
        return TestCaseResponse(
            id=case_id, scenario_id=scenario_id, case_index=case_index,
            input_messages=request.input_messages, initial_context=request.initial_context,
            expected_behavior=request.expected_behavior,
            evaluation_method_code=request.evaluation_method_code,
            evaluation_config=request.evaluation_config,
            is_active=True, created_at=str(now),
        )


def _scenario_response(r) -> ScenarioResponse:
    return ScenarioResponse(
        id=r.id, tenant_key=r.tenant_key, org_id=r.org_id,
        workspace_id=r.workspace_id, scenario_code=r.scenario_code,
        scenario_type_code=r.scenario_type_code, agent_id=r.agent_id,
        is_active=r.is_active, created_at=r.created_at, updated_at=r.updated_at,
        name=r.name, description=r.description,
    )
