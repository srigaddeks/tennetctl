from __future__ import annotations

import json
import uuid
from importlib import import_module

from .evaluator import TestEvaluator

_database_module = import_module("backend.01_core.database")
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

SCHEMA = '"25_agent_sandbox"'


@instrument_class_methods(namespace="agent_sandbox.test_runner.service", logger_name="backend.agent_sandbox.test_runner.instrumentation")
class TestRunnerService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._evaluator = TestEvaluator()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.agent_sandbox.test_runner")

    async def run_scenario(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        scenario_id: str,
        agent_id: str | None = None,
    ) -> dict:
        """Execute all test cases in a scenario against an agent."""
        # Load scenario
        _scenario_repo = import_module("backend.25_agent_sandbox.04_test_scenarios.repository")
        repo = _scenario_repo.TestScenarioRepository()

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.execute")
            scenario = await repo.get_scenario_by_id(conn, scenario_id)
            if scenario is None:
                raise NotFoundError(f"Scenario '{scenario_id}' not found")

            target_agent_id = agent_id or scenario.agent_id
            if not target_agent_id:
                raise NotFoundError("No agent_id specified and scenario has no default agent")

            cases = await repo.list_test_cases(conn, scenario_id)

        if not cases:
            return {"scenario_id": scenario_id, "total_cases": 0, "passed": 0, "failed": 0, "results": []}

        # Execute each case
        _exec_service_module = import_module("backend.25_agent_sandbox.05_execution.service")
        exec_service = _exec_service_module.AgentExecutionService(
            settings=self._settings,
            database_pool=self._database_pool,
            cache=self._cache,
        )

        now = utc_now_sql()
        test_run_id = str(uuid.uuid4())
        case_results = []
        total_tokens = 0
        total_cost = 0.0
        total_duration = 0

        for case in cases:
            # Execute agent for this case
            try:
                run_response = await exec_service.execute_agent(
                    user_id=user_id,
                    tenant_key=tenant_key,
                    org_id=org_id,
                    agent_id=target_agent_id,
                    input_messages=case.input_messages,
                    initial_context=case.initial_context,
                )
                run_result = {
                    "status": run_response.execution_status_code,
                    "output_messages": [],  # Would need to load from DB
                    "final_state": {},
                    "tokens_used": run_response.tokens_used,
                    "tool_calls_made": run_response.tool_calls_made,
                    "cost_usd": run_response.cost_usd,
                    "iterations_used": run_response.iterations_used,
                    "execution_time_ms": run_response.execution_time_ms or 0,
                }
            except Exception as e:
                run_result = {"status": "failed", "error": str(e)}

            # Evaluate
            eval_result = await self._evaluator.evaluate(
                evaluation_method_code=case.evaluation_method_code,
                expected_behavior=case.expected_behavior,
                evaluation_config=case.evaluation_config,
                run_result=run_result,
            )

            case_results.append({
                "case_id": case.id,
                "case_index": case.case_index,
                "passed": eval_result.passed,
                "score": eval_result.score,
                "reason": eval_result.reason,
                "evaluation_output": eval_result.evaluation_output,
                "execution_time_ms": run_result.get("execution_time_ms", 0),
            })
            total_tokens += run_result.get("tokens_used", 0)
            total_cost += run_result.get("cost_usd", 0.0)
            total_duration += run_result.get("execution_time_ms", 0)

        passed = sum(1 for r in case_results if r["passed"])
        failed = len(case_results) - passed
        pass_rate = passed / len(case_results) if case_results else 0.0

        # Persist test run result
        async with self._database_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {SCHEMA}."74_trx_test_run_results"
                    (id, tenant_key, org_id, scenario_id, agent_id,
                     total_cases, passed, failed, errored, pass_rate,
                     total_tokens, total_cost_usd, total_duration_ms,
                     created_at, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """,
                test_run_id, tenant_key, org_id, scenario_id, target_agent_id,
                len(case_results), passed, failed, 0, pass_rate,
                total_tokens, total_cost, total_duration,
                now, user_id,
            )

            # Persist per-case results
            for cr in case_results:
                await conn.execute(
                    f"""
                    INSERT INTO {SCHEMA}."75_dtl_test_case_results"
                        (id, test_run_id, test_case_id, passed, score, reason,
                         evaluation_output, execution_time_ms, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, NOW())
                    """,
                    str(uuid.uuid4()), test_run_id, cr["case_id"],
                    cr["passed"], cr["score"], cr["reason"],
                    json.dumps(cr.get("evaluation_output")) if cr.get("evaluation_output") else None,
                    cr["execution_time_ms"],
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()), tenant_key=tenant_key,
                    entity_type="test_scenario", entity_id=scenario_id,
                    event_type="executed",
                    event_category=AgentSandboxAuditEventType.TEST_SCENARIO_EXECUTED,
                    actor_id=user_id, occurred_at=now,
                    properties={
                        "test_run_id": test_run_id,
                        "pass_rate": str(pass_rate),
                        "total_cases": str(len(case_results)),
                    },
                ),
            )

        return {
            "test_run_id": test_run_id,
            "scenario_id": scenario_id,
            "agent_id": target_agent_id,
            "total_cases": len(case_results),
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "total_duration_ms": total_duration,
            "results": case_results,
        }

    async def list_test_results(
        self, *, user_id: str, org_id: str, limit: int = 50, offset: int = 0,
    ) -> dict:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            count_row = await conn.fetchrow(
                f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."82_vw_test_run_summary" WHERE org_id = $1',
                org_id,
            )
            total = count_row["total"] if count_row else 0
            rows = await conn.fetch(
                f"""
                SELECT id, tenant_key, org_id, scenario_id, agent_id,
                       total_cases, passed, failed, errored, pass_rate::float,
                       total_tokens, total_cost_usd::float, total_duration_ms,
                       created_at::text, created_by, scenario_name, agent_name
                FROM {SCHEMA}."82_vw_test_run_summary"
                WHERE org_id = $1
                ORDER BY created_at DESC
                LIMIT {limit} OFFSET {offset}
                """,
                org_id,
            )
        return {"items": [dict(r) for r in rows], "total": total}
