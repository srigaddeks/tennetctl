from __future__ import annotations

import uuid
from datetime import datetime, timezone
from importlib import import_module

from .compiler import AgentCompiler
from .engine import AgentExecutionEngine
from .repository import AgentRunRepository
from .schemas import (
    AgentRunListResponse,
    AgentRunResponse,
    AgentRunStepResponse,
    CompileCheckResponse,
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
_agent_repo_module = import_module("backend.25_agent_sandbox.02_agents.repository")

DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AgentSandboxAuditEventType = _constants_module.AgentSandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
AgentRepository = _agent_repo_module.AgentRepository

_CACHE_KEY_PREFIX = "asb:runs"
_CACHE_TTL = 60


@instrument_class_methods(namespace="agent_sandbox.execution.service", logger_name="backend.agent_sandbox.execution.instrumentation")
class AgentExecutionService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._run_repository = AgentRunRepository()
        self._agent_repository = AgentRepository()
        self._compiler = AgentCompiler()
        self._engine = AgentExecutionEngine(
            max_concurrent=settings.agent_sandbox_max_concurrent_runs,
        )
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.agent_sandbox.execution")

    # ── compile check ─────────────────────────────────────────

    async def compile_check(self, *, graph_source: str) -> CompileCheckResponse:
        result = self._compiler.compile_graph_source(graph_source)
        return CompileCheckResponse(
            success=result.success,
            errors=result.errors,
            handler_names=result.handler_names,
        )

    # ── execute agent ─────────────────────────────────────────

    async def execute_agent(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        agent_id: str,
        input_messages: list[dict] | None = None,
        initial_context: dict | None = None,
    ) -> AgentRunResponse:
        now = utc_now_sql()
        run_id = str(uuid.uuid4())

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.execute")

            # Load agent
            agent = await self._agent_repository.get_agent_by_id(conn, agent_id)
            if agent is None:
                raise NotFoundError(f"Agent '{agent_id}' not found")

            # Load graph source
            props = await self._agent_repository.get_agent_properties(conn, agent_id)
            graph_source = props.get("graph_source", "")
            if not graph_source:
                raise ValidationError("Agent has no graph_source")

            # Load bound tools
            bound_tools = await self._agent_repository.list_bound_tools(conn, agent_id)

            # Load tool records
            tool_records = {}
            if bound_tools:
                _tool_repo_module = import_module("backend.25_agent_sandbox.03_tools.repository")
                tool_repo = _tool_repo_module.AgentToolRepository()
                for bt in bound_tools:
                    t = await tool_repo.get_tool_by_id(conn, bt["tool_id"])
                    if t:
                        tool_records[t.tool_code] = {
                            "tool_type_code": t.tool_type_code,
                            "python_source": t.python_source,
                            "endpoint_url": t.endpoint_url,
                            "mcp_server_url": t.mcp_server_url,
                            "signal_id": t.signal_id,
                            "timeout_ms": t.timeout_ms,
                        }

            # Create run record
            await self._run_repository.create_run(
                conn,
                id=run_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=agent.workspace_id,
                agent_id=agent_id,
                execution_status_code="running",
                input_messages=input_messages or [],
                initial_context=initial_context or {},
                graph_source_snapshot=graph_source,
                agent_code_snapshot=agent.agent_code,
                version_snapshot=agent.version_number,
                langfuse_trace_id=None,
                job_queue_id=None,
                test_run_id=None,
                created_by=user_id,
                now=now,
            )

        # Resolve LLM config
        llm_config = {
            "provider_url": self._settings.ai_provider_url or "",
            "api_key": self._settings.ai_api_key or "",
            "model": agent.llm_model_id or self._settings.ai_model,
            "temperature": agent.temperature,
        }

        # Audit: run started
        async with self._database_pool.acquire() as conn:
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="agent_run",
                    entity_id=run_id,
                    event_type="started",
                    event_category=AgentSandboxAuditEventType.AGENT_RUN_STARTED,
                    actor_id=user_id,
                    occurred_at=now,
                    properties={"agent_id": agent_id, "agent_code": agent.agent_code},
                ),
            )

        # Execute
        result = await self._engine.execute(
            graph_source=graph_source,
            input_messages=input_messages,
            initial_context=initial_context,
            bound_tools=bound_tools,
            tool_records=tool_records,
            llm_config=llm_config,
            max_iterations=agent.max_iterations,
            max_tokens_budget=agent.max_tokens_budget,
            max_tool_calls=agent.max_tool_calls,
            max_duration_ms=agent.max_duration_ms,
            max_cost_usd=agent.max_cost_usd,
        )

        # Persist results
        completed_at = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._run_repository.update_run_result(
                conn, run_id,
                execution_status_code=result.status,
                output_messages=result.output_messages,
                final_state=result.final_state,
                error_message=result.error_message,
                tokens_used=result.tokens_used,
                tool_calls_made=result.tool_calls_made,
                llm_calls_made=result.llm_calls_made,
                cost_usd=result.cost_usd,
                iterations_used=result.iterations_used,
                execution_time_ms=result.execution_time_ms,
                completed_at=completed_at,
            )

            # Persist steps and their LLM/tool calls
            for step in result.steps:
                step_id = str(uuid.uuid4())
                step_started = datetime.fromtimestamp(step.started_at, tz=timezone.utc)
                step_completed = (
                    datetime.fromtimestamp(step.completed_at, tz=timezone.utc)
                    if step.completed_at else None
                )
                await self._run_repository.insert_step(
                    conn,
                    id=step_id,
                    agent_run_id=run_id,
                    step_index=step.step_index,
                    node_name=step.node_name,
                    step_type=step.step_type,
                    input_json=step.input_json,
                    output_json=step.output_json,
                    transition=step.transition,
                    tokens_used=step.tokens_used,
                    cost_usd=step.cost_usd,
                    duration_ms=step.duration_ms,
                    error_message=step.error_message,
                    started_at=step_started,
                    completed_at=step_completed,
                )
                for llm_call in step.llm_calls:
                    await self._run_repository.insert_llm_call(
                        conn,
                        id=str(uuid.uuid4()),
                        run_step_id=step_id,
                        model_id=llm_call.model_id,
                        system_prompt=llm_call.system_prompt[:10000],
                        user_prompt=llm_call.user_prompt[:10000],
                        response_text=llm_call.response_text[:10000],
                        input_tokens=llm_call.input_tokens,
                        output_tokens=llm_call.output_tokens,
                        total_tokens=llm_call.total_tokens,
                        cost_usd=llm_call.cost_usd,
                        duration_ms=llm_call.duration_ms,
                    )
                for tc in step.tool_calls:
                    await self._run_repository.insert_tool_call(
                        conn,
                        id=str(uuid.uuid4()),
                        run_step_id=step_id,
                        tool_code=tc.tool_code,
                        tool_type_code=tc.tool_type_code,
                        input_json=tc.input_json,
                        output_json=tc.output_json,
                        duration_ms=tc.duration_ms,
                        error_message=tc.error,
                        approval_status=tc.approval_status,
                    )

            # Audit: run completed/failed
            event_type = AgentSandboxAuditEventType.AGENT_RUN_COMPLETED if result.status == "completed" else AgentSandboxAuditEventType.AGENT_RUN_FAILED
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="agent_run",
                    entity_id=run_id,
                    event_type=result.status,
                    event_category=event_type,
                    actor_id=user_id,
                    occurred_at=now,
                    properties={
                        "tokens_used": str(result.tokens_used),
                        "cost_usd": str(result.cost_usd),
                        "iterations_used": str(result.iterations_used),
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        # Return fresh record
        async with self._database_pool.acquire() as conn:
            run_record = await self._run_repository.get_run_by_id(conn, run_id)
        return _run_response(run_record) if run_record else AgentRunResponse(
            id=run_id, tenant_key=tenant_key, org_id=org_id,
            agent_id=agent_id, execution_status_code=result.status,
            created_at=str(now),
        )

    # ── list runs ─────────────────────────────────────────────

    async def list_runs(
        self,
        *,
        user_id: str,
        org_id: str,
        agent_id: str | None = None,
        execution_status_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AgentRunListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            records, total = await self._run_repository.list_runs(
                conn, org_id,
                agent_id=agent_id,
                execution_status_code=execution_status_code,
                limit=limit,
                offset=offset,
            )
        return AgentRunListResponse(
            items=[_run_response(r) for r in records],
            total=total,
        )

    # ── get run ───────────────────────────────────────────────

    async def get_run(self, *, user_id: str, run_id: str) -> AgentRunResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            record = await self._run_repository.get_run_by_id(conn, run_id)
            if record is None:
                raise NotFoundError(f"Run '{run_id}' not found")
        return _run_response(record)

    # ── get run steps ─────────────────────────────────────────

    async def get_run_steps(self, *, user_id: str, run_id: str) -> list[AgentRunStepResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            steps = await self._run_repository.list_steps(conn, run_id)
        return [
            AgentRunStepResponse(
                id=s.id, agent_run_id=s.agent_run_id,
                step_index=s.step_index, node_name=s.node_name,
                step_type=s.step_type, transition=s.transition,
                tokens_used=s.tokens_used, cost_usd=s.cost_usd,
                duration_ms=s.duration_ms, error_message=s.error_message,
                started_at=s.started_at, completed_at=s.completed_at,
            )
            for s in steps
        ]

    # ── cancel run ────────────────────────────────────────────

    async def cancel_run(self, *, user_id: str, tenant_key: str, run_id: str) -> AgentRunResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.execute")
            record = await self._run_repository.get_run_by_id(conn, run_id)
            if record is None:
                raise NotFoundError(f"Run '{run_id}' not found")
            if record.execution_status_code in ("completed", "failed", "timeout", "cancelled"):
                raise ValidationError(f"Run is already in terminal state: {record.execution_status_code}")
            await self._run_repository.update_run_result(
                conn, run_id,
                execution_status_code="cancelled",
                output_messages=None,
                final_state=None,
                error_message="Cancelled by user",
                tokens_used=record.tokens_used,
                tool_calls_made=record.tool_calls_made,
                llm_calls_made=record.llm_calls_made,
                cost_usd=record.cost_usd,
                iterations_used=record.iterations_used,
                execution_time_ms=record.execution_time_ms or 0,
                completed_at=utc_now_sql(),
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="agent_run",
                    entity_id=run_id,
                    event_type="cancelled",
                    event_category=AgentSandboxAuditEventType.AGENT_RUN_CANCELLED,
                    actor_id=user_id,
                    occurred_at=now,
                    properties={},
                ),
            )
            updated = await self._run_repository.get_run_by_id(conn, run_id)
        return _run_response(updated) if updated else _run_response(record)


def _run_response(r) -> AgentRunResponse:
    return AgentRunResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        agent_id=r.agent_id,
        execution_status_code=r.execution_status_code,
        execution_status_name=r.execution_status_name,
        tokens_used=r.tokens_used,
        tool_calls_made=r.tool_calls_made,
        llm_calls_made=r.llm_calls_made,
        cost_usd=r.cost_usd,
        iterations_used=r.iterations_used,
        error_message=r.error_message,
        started_at=r.started_at,
        completed_at=r.completed_at,
        execution_time_ms=r.execution_time_ms,
        langfuse_trace_id=r.langfuse_trace_id,
        test_run_id=r.test_run_id,
        agent_code_snapshot=r.agent_code_snapshot,
        version_snapshot=r.version_snapshot,
        agent_name=r.agent_name,
        created_at=r.created_at,
        created_by=r.created_by,
    )
