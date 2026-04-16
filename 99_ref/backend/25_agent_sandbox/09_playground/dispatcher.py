"""
Playground dispatcher — routes playground requests to the actual agent implementations.

Each agent has a dispatch function that:
1. Validates inputs
2. Calls the real agent
3. Yields SSE events for streaming agents or returns results for batch agents
"""
from __future__ import annotations

import json
import time
import uuid
from importlib import import_module
from typing import AsyncIterator

_logging_module = import_module("backend.01_core.logging_utils")
_time_module = import_module("backend.01_core.time_utils")
_catalog_module = import_module("backend.25_agent_sandbox.08_registry.catalog")

get_logger = _logging_module.get_logger
utc_now_sql = _time_module.utc_now_sql
get_agent_by_code = _catalog_module.get_agent_by_code

logger = get_logger("backend.agent_sandbox.playground")


async def dispatch_playground_run(
    *,
    agent_code: str,
    inputs: dict,
    user_id: str,
    tenant_key: str,
    org_id: str,
    workspace_id: str | None = None,
    settings,
    database_pool,
) -> AsyncIterator[str]:
    """Dispatch a playground run and yield SSE events.

    For streaming agents: proxies the SSE stream directly.
    For batch agents: wraps in SSE start/progress/complete events.
    For request_response agents: wraps response in SSE.
    """
    entry = get_agent_by_code(agent_code)
    if entry is None:
        yield _sse("error", {"message": f"Agent '{agent_code}' not found in registry"})
        return

    run_id = str(uuid.uuid4())
    start_time = time.time()

    yield _sse("run_started", {
        "run_id": run_id,
        "agent_code": agent_code,
        "agent_name": entry.name,
        "execution_mode": entry.execution_mode,
    })

    try:
        if agent_code == "grc_copilot":
            async for event in _run_grc_copilot(inputs, user_id, org_id, workspace_id, settings, database_pool):
                yield event

        elif agent_code == "signal_spec":
            async for event in _run_signal_spec(inputs, settings, database_pool):
                yield event

        elif agent_code == "text_enhancer":
            async for event in _run_text_enhancer(inputs, user_id, org_id, settings, database_pool):
                yield event

        elif agent_code == "dataset_agent":
            async for event in _run_dataset_agent(inputs, user_id, org_id, settings, database_pool):
                yield event

        elif agent_code == "framework_builder":
            async for event in _run_framework_builder(inputs, user_id, org_id, settings, database_pool):
                yield event

        elif agent_code in ("report_generator", "signal_codegen", "signal_generator",
                            "test_dataset_gen", "threat_composer", "library_builder",
                            "evidence_checker"):
            async for event in _run_batch_agent(agent_code, inputs, user_id, tenant_key, org_id, workspace_id, settings, database_pool):
                yield event

        elif agent_code == "form_fill":
            async for event in _run_form_fill(inputs, user_id, org_id, workspace_id, settings, database_pool):
                yield event

        elif agent_code == "signal_codegen_agent":
            async for event in _run_signal_codegen_agent(agent_code, inputs, user_id, tenant_key, org_id, workspace_id, settings, database_pool):
                yield event

        else:
            yield _sse("error", {"message": f"Playground dispatch not implemented for '{agent_code}'"})
            return

    except Exception as e:
        logger.error(f"Playground run failed for {agent_code}: {e}", exc_info=True)
        yield _sse("error", {"message": str(e)})

    duration_ms = int((time.time() - start_time) * 1000)
    yield _sse("run_completed", {"run_id": run_id, "duration_ms": duration_ms})


# ═══════════════════════════════════════════════════════════════════════════════
# Agent-specific dispatch functions
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_grc_copilot(inputs: dict, user_id: str, org_id: str, workspace_id: str | None, settings, database_pool) -> AsyncIterator[str]:
    """Dispatch to GRC Copilot agent — proxies SSE stream."""
    message = inputs.get("message", "")
    if not message:
        yield _sse("error", {"message": "Input 'message' is required"})
        return

    _conv_service_module = import_module("backend.20_ai.02_conversations.service")
    service = _conv_service_module.ConversationService(settings=settings, database_pool=database_pool)

    yield _sse("agent_streaming", {"status": "started", "agent": "grc_copilot"})

    collected_text = []
    async for chunk in service.stream_conversation(
        user_id=user_id,
        tenant_key="default",
        org_id=org_id,
        workspace_id=workspace_id or "",
        user_message=message,
        conversation_id=inputs.get("conversation_id"),
        page_context=inputs.get("page_context"),
    ):
        # Pass through SSE chunks, also collect for trace
        if chunk.startswith("data: "):
            try:
                data = json.loads(chunk[6:])
                event_type = data.get("type", "chunk")
                yield _sse(f"agent.{event_type}", data)
                if event_type in ("content", "chunk"):
                    collected_text.append(data.get("content", data.get("text", "")))
            except json.JSONDecodeError:
                yield _sse("agent.chunk", {"text": chunk[6:]})
        else:
            yield _sse("agent.raw", {"text": chunk})

    yield _sse("agent_result", {"full_response": "".join(collected_text)})


async def _run_signal_spec(inputs: dict, settings, database_pool) -> AsyncIterator[str]:
    """Dispatch to Signal Spec Agent."""
    prompt = inputs.get("prompt", "")
    if not prompt:
        yield _sse("error", {"message": "Input 'prompt' is required"})
        return

    _agent_module = import_module("backend.20_ai.22_signal_spec.agent")
    _config_module = import_module("backend.20_ai.12_agent_config.resolver")

    resolver = _config_module.AgentConfigResolver(settings=settings, database_pool=database_pool)
    llm_config = await resolver.resolve("signal_spec")
    agent = _agent_module.SignalSpecAgent(llm_config=llm_config, settings=settings)

    yield _sse("agent_streaming", {"status": "started", "agent": "signal_spec"})

    async for chunk in agent.stream_generate(
        prompt=prompt,
        connector_type_code=inputs.get("connector_type_code", "github"),
        rich_schema=inputs.get("rich_schema"),
        dataset_records=inputs.get("dataset_records"),
        record_names=inputs.get("record_names"),
    ):
        try:
            data = json.loads(chunk.replace("data: ", "")) if chunk.startswith("data: ") else {"text": chunk}
            yield _sse("agent.spec_event", data)
        except json.JSONDecodeError:
            yield _sse("agent.chunk", {"text": chunk})

    yield _sse("agent_result", {"status": "complete"})


async def _run_text_enhancer(inputs: dict, user_id: str, org_id: str, settings, database_pool) -> AsyncIterator[str]:
    """Dispatch to Text Enhancer."""
    _service_module = import_module("backend.20_ai.17_text_enhancer.service")
    service = _service_module.TextEnhancerService(settings=settings, database_pool=database_pool)

    entity_type = inputs.get("entity_type", "control")
    field_name = inputs.get("field_name", "description")
    current_value = inputs.get("current_value", "")

    if not current_value:
        yield _sse("error", {"message": "Input 'current_value' is required"})
        return

    yield _sse("agent_streaming", {"status": "started", "agent": "text_enhancer"})

    collected = []
    async for chunk in service.enhance_field(
        entity_type=entity_type,
        entity_display_name=inputs.get("entity_display_name", ""),
        field_name=field_name,
        current_value=current_value,
        context=inputs.get("context"),
    ):
        collected.append(chunk)
        yield _sse("agent.chunk", {"text": chunk})

    yield _sse("agent_result", {"enhanced_text": "".join(collected)})


async def _run_dataset_agent(inputs: dict, user_id: str, org_id: str, settings, database_pool) -> AsyncIterator[str]:
    """Dispatch to Dataset Agent (request/response)."""
    _service_module = import_module("backend.20_ai.27_dataset_agent.service")
    service = _service_module.DatasetAgentService(settings=settings, database_pool=database_pool)

    operation = inputs.get("operation", "explain_record")
    records = inputs.get("records", [])

    yield _sse("agent_processing", {"status": "started", "agent": "dataset_agent", "operation": operation})

    if operation == "explain_record" and records:
        result = await service.explain_record(
            record_data=records[0] if isinstance(records, list) else records,
            asset_type_hint=inputs.get("asset_type_hint", ""),
            connector_type=inputs.get("connector_type", ""),
        )
    elif operation == "explain_dataset":
        result = await service.explain_dataset(
            records=records,
            asset_type_hint=inputs.get("asset_type_hint", ""),
        )
    elif operation == "compose_test_data":
        result = await service.compose_test_data(
            schema=inputs.get("schema", {}),
            num_records=int(inputs.get("num_records", 5)),
            constraints=inputs.get("constraints", {}),
        )
    else:
        result = {"error": f"Unknown operation: {operation}"}

    yield _sse("agent_result", {"operation": operation, "result": result})


async def _run_framework_builder(inputs: dict, user_id: str, org_id: str, settings, database_pool) -> AsyncIterator[str]:
    """Dispatch to Framework Builder Agent (streaming phases)."""
    _agent_module = import_module("backend.20_ai.21_framework_builder.agent")
    _config_module = import_module("backend.20_ai.12_agent_config.resolver")

    resolver = _config_module.AgentConfigResolver(settings=settings, database_pool=database_pool)
    llm_config = await resolver.resolve("framework_builder")
    agent = _agent_module.FrameworkBuilderAgent(llm_config=llm_config, settings=settings)

    documents = inputs.get("documents", "")
    user_message = inputs.get("user_message", "")

    yield _sse("agent_streaming", {"status": "started", "agent": "framework_builder"})

    async for chunk in agent.stream_hierarchy(
        documents=documents,
        user_message=user_message,
        session_id=str(uuid.uuid4()),
    ):
        try:
            data = json.loads(chunk.replace("data: ", "")) if chunk.startswith("data: ") else {"text": chunk}
            yield _sse("agent.framework_event", data)
        except json.JSONDecodeError:
            yield _sse("agent.chunk", {"text": chunk})

    yield _sse("agent_result", {"status": "phase1_complete"})


async def _run_form_fill(inputs: dict, user_id: str, org_id: str, workspace_id: str | None, settings, database_pool) -> AsyncIterator[str]:
    """Dispatch to Form Fill Agent."""
    yield _sse("agent_processing", {"status": "started", "agent": "form_fill"})
    yield _sse("agent_result", {"status": "form_fill playground coming soon — use the GRC copilot playground with form context"})


async def _run_signal_codegen_agent(
    agent_code: str,
    inputs: dict,
    user_id: str,
    tenant_key: str,
    org_id: str,
    workspace_id: str | None,
    settings,
    database_pool,
) -> AsyncIterator[str]:
    """Run the signal codegen agent — loads graph from DB, executes with SSE streaming."""
    connector_id = inputs.get("connector_id", "")
    signal_intent = inputs.get("signal_intent", "")
    asset_type = inputs.get("asset_type", "github_repo")

    if not connector_id or not signal_intent:
        yield _sse("error", {"message": "connector_id and signal_intent are required"})
        return

    _agent_repo_module = import_module("backend.25_agent_sandbox.02_agents.repository")
    _tool_repo_module = import_module("backend.25_agent_sandbox.03_tools.repository")
    _engine_module = import_module("backend.25_agent_sandbox.05_execution.engine")

    agent_repo = _agent_repo_module.AgentRepository()
    tool_repo = _tool_repo_module.AgentToolRepository()
    exec_engine = _engine_module.AgentExecutionEngine()

    async with database_pool.acquire() as conn:
        # Load agent from DB
        agents, _ = await agent_repo.list_agents(conn, org_id)
        agent_record = next((a for a in agents if a.agent_code == agent_code), None)

        if agent_record is None:
            yield _sse("error", {"message": f"Agent '{agent_code}' not found in DB for org '{org_id}'. Seed the agent first."})
            return

        # Load graph_source
        props = await agent_repo.get_agent_properties(conn, agent_record.id)
        graph_source = props.get("graph_source", "")
        if not graph_source:
            yield _sse("error", {"message": "Agent has no graph_source property"})
            return

        # Load bound tools
        bound_tools = await agent_repo.list_bound_tools(conn, agent_record.id)

        # Load full tool records (python_source, endpoint_url, etc.)
        tool_records: dict[str, dict] = {}
        for bt in bound_tools:
            tool = await tool_repo.get_tool_by_id(conn, bt["tool_id"])
            if tool:
                # Load tool properties
                tool_props = await tool_repo.get_tool_properties(conn, tool.id)
                tool_records[bt["tool_code"]] = {
                    "tool_code": tool.tool_code,
                    "tool_type_code": tool.tool_type_code,
                    "python_source": tool_props.get("python_source") or tool.python_source or "",
                    "endpoint_url": tool_props.get("endpoint_url") or tool.endpoint_url or "",
                    "timeout_ms": tool.timeout_ms,
                }

    # Build LLM config
    llm_config = {
        "provider_url": settings.sandbox_ai_provider_url or "",
        "api_key": settings.sandbox_ai_api_key or "",
        "model": settings.sandbox_ai_model or "gpt-4o",
        "temperature": 0.2,
    }

    # SSE event buffer
    sse_events: list[str] = []

    def sse_callback(event) -> None:
        data = event if isinstance(event, dict) else (event.__dict__ if hasattr(event, "__dict__") else {"event": str(event)})
        sse_events.append(_sse("agent.node_event", data))

    yield _sse("agent_streaming", {"status": "started", "agent": agent_code})

    # Execute agent
    result = await exec_engine.execute(
        graph_source=graph_source,
        initial_context={
            "connector_id": connector_id,
            "signal_intent": signal_intent,
            "asset_type": asset_type,
            "org_id": org_id,
            "workspace_id": workspace_id or "",
        },
        bound_tools=bound_tools,
        tool_records=tool_records,
        llm_config=llm_config,
        max_iterations=agent_record.max_iterations,
        max_tokens_budget=agent_record.max_tokens_budget,
        max_tool_calls=agent_record.max_tool_calls,
        max_duration_ms=agent_record.max_duration_ms,
        max_cost_usd=agent_record.max_cost_usd,
        sse_callback=sse_callback,
    )

    # Flush buffered SSE events
    for evt in sse_events:
        yield evt

    yield _sse("agent_result", {
        "status": result.status,
        "signal_id": result.final_state.get("signal_id"),
        "signal_code": result.final_state.get("signal_code"),
        "python_source": result.final_state.get("python_source"),
        "test_accuracy": result.final_state.get("test_accuracy"),
        "live_accuracy": result.final_state.get("live_accuracy"),
        "tokens_used": result.tokens_used,
        "cost_usd": result.cost_usd,
        "iterations": result.iterations_used,
        "error": result.error_message,
    })


async def _run_batch_agent(agent_code: str, inputs: dict, user_id: str, tenant_key: str, org_id: str, workspace_id: str | None, settings, database_pool) -> AsyncIterator[str]:
    """Dispatch a batch agent by enqueuing a job and tracking it."""
    yield _sse("agent_processing", {
        "status": "batch_agent",
        "agent": agent_code,
        "message": f"Batch agent '{agent_code}' runs via job queue. Use the Sandbox Runs page to monitor execution.",
    })

    # For now, show the agent's inputs and explain how to use it
    entry = get_agent_by_code(agent_code)
    yield _sse("agent_result", {
        "status": "info",
        "message": f"To run {entry.name}, enqueue a '{agent_code}' job via the appropriate domain page (Signals, Reports, etc.). The job will be picked up by the background worker.",
        "inputs_provided": inputs,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _sse(event: str, data: dict) -> str:
    """Format an SSE event string."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
