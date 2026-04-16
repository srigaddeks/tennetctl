"""
Job handler for signal_generate job type.
Resolves LLM config, runs SignalGenerationAgent, writes results back to signal EAV.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from importlib import import_module
from typing import AsyncIterator

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.10_sandbox.13_signal_agent.job_handler")

_JOBS = '"20_ai"."45_fct_job_queue"'
_SIGNAL_PROPS = '"15_sandbox"."45_dtl_signal_properties"'
_SIGNALS = '"15_sandbox"."22_fct_signals"'
_SIGNAL_STATUSES = '"15_sandbox"."04_dim_signal_statuses"'


class _PoolAdapter:
    """Wraps raw asyncpg.Pool to match DatabasePool interface used by services."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn


async def _set_output(conn: asyncpg.Connection, job_id: str, output: dict) -> None:
    await conn.execute(
        f"UPDATE {_JOBS} SET output_json = $2::jsonb, updated_at = NOW() WHERE id = $1",
        job_id,
        json.dumps(output),
    )


async def _upsert_signal_prop(
    conn: asyncpg.Connection, signal_id: str, key: str, value: str
) -> None:
    await conn.execute(
        f"""
        INSERT INTO {_SIGNAL_PROPS}
            (id, signal_id, property_key, property_value, created_at, updated_at,
             created_by, updated_by)
        VALUES (gen_random_uuid(), $1, $2, $3, NOW(), NOW(), 'system', 'system')
        ON CONFLICT (signal_id, property_key)
        DO UPDATE SET property_value = EXCLUDED.property_value, updated_at = NOW()
        """,
        signal_id,
        key,
        value,
    )


async def _update_signal_status(
    conn: asyncpg.Connection, signal_id: str, status_code: str
) -> None:
    await conn.execute(
        f"UPDATE {_SIGNALS} SET status_code = $2, updated_at = NOW() WHERE id = $1",
        signal_id,
        status_code,
    )


async def handle_signal_generate_job(job, pool, settings) -> None:
    """
    Execute signal generation job:
    1. Build state from job.input_json
    2. Resolve LLM config via AgentConfigResolver
    3. Instantiate SignalGenerationAgent
    4. Run agent
    5. Write: python_source, signal_args_schema, ssf_mapping, name/description EAV
    6. Update signal status → validated (or draft on failure)
    """
    input_data: dict = job.input_json or {}
    signal_id: str | None = input_data.get("signal_id")
    connector_type: str = input_data.get("connector_type", "")
    prompt: str = input_data.get("prompt", "")
    sample_dataset: dict | None = input_data.get("sample_dataset")
    configurable_args: dict = input_data.get("configurable_args") or {}
    org_id: str | None = input_data.get("org_id")

    _logger.info(
        "signal_gen.job_start",
        extra={"job_id": job.id, "signal_id": signal_id, "connector": connector_type},
    )

    # Resolve LLM config
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    _signal_llm_mod = import_module("backend.10_sandbox.13_signal_agent.llm_config")
    AgentConfigResolver = _resolver_mod.AgentConfigResolver
    AgentConfigRepository = _config_repo_mod.AgentConfigRepository
    get_effective_signal_generation_llm_config = (
        _signal_llm_mod.get_effective_signal_generation_llm_config
    )
    resolver = AgentConfigResolver(
        repository=AgentConfigRepository(),
        database_pool=pool,
        settings=settings,
    )
    llm_config = await resolver.resolve(
        agent_type_code="signal_generate",
        org_id=org_id,
    )
    llm_config = get_effective_signal_generation_llm_config(
        llm_config=llm_config,
        settings=settings,
    )

    # Build dataset schema from sample
    _tools_mod = import_module("backend.10_sandbox.13_signal_agent.tools")
    _engine_mod = import_module("backend.10_sandbox.07_execution.engine")
    AgentTools = _tools_mod.AgentTools
    SignalExecutionEngine = _engine_mod.SignalExecutionEngine

    engine = SignalExecutionEngine(
        timeout_ms=getattr(settings, "sandbox_execution_timeout_ms", 10000),
        max_memory_mb=getattr(settings, "sandbox_execution_max_memory_mb", 256),
    )
    tools = AgentTools(execution_engine=engine)

    dataset_schema = {}
    if sample_dataset:
        dataset_schema = tools.infer_dataset_schema(sample_dataset)

    # Build agent state
    from .state import SignalGenState
    state: SignalGenState = {
        "prompt": prompt,
        "connector_type": connector_type,
        "dataset_schema": dataset_schema,
        "sample_dataset": sample_dataset,
        "signal_id": signal_id,
        "configurable_args": configurable_args,
        "max_iterations": 10,
        "fix_history": [],
        "iteration": 0,
        "iterations_used": 0,
        "is_complete": False,
        "error": None,
    }

    # Run agent
    from .agent import SignalGenerationAgent
    agent = SignalGenerationAgent(llm_config=llm_config, settings=settings, tools=tools)
    state = await agent.run(state)

    # Write results back
    async with pool.acquire() as conn:
        async with conn.transaction():
            if signal_id:
                # Write python_source EAV
                if state.get("final_code"):
                    await _upsert_signal_prop(conn, signal_id, "python_source", state["final_code"])

                # Write signal_args_schema EAV
                args_schema = state.get("signal_args_schema")
                if args_schema is not None:
                    await _upsert_signal_prop(
                        conn, signal_id, "signal_args_schema", json.dumps(args_schema)
                    )

                # Write ssf_mapping EAV
                ssf = state.get("ssf_mapping")
                if ssf:
                    await _upsert_signal_prop(
                        conn, signal_id, "signal_ssf_mapping", json.dumps(ssf)
                    )

                # Write name/description suggestions as EAV (if not already set)
                if state.get("signal_name_suggestion"):
                    await _upsert_signal_prop(
                        conn, signal_id, "ai_name_suggestion", state["signal_name_suggestion"]
                    )
                if state.get("signal_description_suggestion"):
                    await _upsert_signal_prop(
                        conn, signal_id, "ai_description_suggestion", state["signal_description_suggestion"]
                    )

                # Write codegen_iterations
                await _upsert_signal_prop(
                    conn, signal_id, "codegen_iterations", str(state.get("iterations_used", 0))
                )

                # Update signal status
                if state.get("is_complete") and state.get("final_code"):
                    await _update_signal_status(conn, signal_id, "validated")
                elif state.get("error"):
                    await _upsert_signal_prop(
                        conn, signal_id, "codegen_failure_reason", state["error"]
                    )
                    await _update_signal_status(conn, signal_id, "draft")

            # Write job output
            await _set_output(conn, job.id, {
                "is_complete": state.get("is_complete", False),
                "iterations_used": state.get("iterations_used", 0),
                "signal_name_suggestion": state.get("signal_name_suggestion"),
                "signal_description_suggestion": state.get("signal_description_suggestion"),
                "has_args_schema": bool(state.get("signal_args_schema")),
                "error": state.get("error"),
            })

    _logger.info(
        "signal_gen.job_complete",
        extra={
            "job_id": job.id,
            "signal_id": signal_id,
            "is_complete": state.get("is_complete"),
            "iterations_used": state.get("iterations_used"),
        },
    )
