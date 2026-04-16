"""
Agent execution engine — walks the graph, executes handlers, records steps.

This is the core orchestrator that:
1. Compiles the graph source
2. Builds AgentContext
3. Walks nodes calling handlers
4. Records every step, LLM call, and tool call
5. Enforces budget limits
6. Emits SSE events
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from importlib import import_module

from .budget_enforcer import BudgetEnforcer, BudgetExceededError
from .compiler import AgentCompiler
from .context import AgentContext, HumanInputRequired
from .tool_dispatcher import ToolDispatcher

_logging_module = import_module("backend.01_core.logging_utils")
_sse_module = import_module("backend.25_agent_sandbox.07_streaming.events")
get_logger = _logging_module.get_logger

logger = get_logger("backend.agent_sandbox.engine")


@dataclass(frozen=True)
class AgentExecutionResult:
    status: str  # completed, failed, timeout, budget_exceeded, awaiting_approval, cancelled
    output_messages: list[dict] = field(default_factory=list)
    final_state: dict = field(default_factory=dict)
    error_message: str | None = None
    tokens_used: int = 0
    tool_calls_made: int = 0
    llm_calls_made: int = 0
    cost_usd: float = 0.0
    iterations_used: int = 0
    execution_time_ms: int = 0
    steps: list = field(default_factory=list)
    human_question: str | None = None  # Set when status=awaiting_approval


class AgentExecutionEngine:
    """Executes an agent graph with full observability and budget enforcement."""

    def __init__(self, *, max_concurrent: int = 5) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._compiler = AgentCompiler()

    async def execute(
        self,
        *,
        graph_source: str,
        input_messages: list[dict] | None = None,
        initial_context: dict | None = None,
        bound_tools: list[dict] | None = None,
        tool_records: dict[str, dict] | None = None,
        llm_config: dict,
        max_iterations: int = 20,
        max_tokens_budget: int = 50000,
        max_tool_calls: int = 100,
        max_duration_ms: int = 300000,
        max_cost_usd: float = 1.0,
        tracer=None,
        trace=None,
        sse_callback=None,
    ) -> AgentExecutionResult:
        """Execute an agent graph.

        Args:
            graph_source: Python source code defining build_graph(ctx) and handlers
            input_messages: Initial messages to seed ctx.state["input"]
            initial_context: Additional context to seed ctx.state
            bound_tools: Tool bindings from DB
            tool_records: Full tool records for execution
            llm_config: {provider_url, api_key, model, temperature}
            max_*: Budget limits
            tracer: LangFuse tracer (optional)
            trace: LangFuse trace (optional)
            sse_callback: Callable(SSEEvent) for real-time streaming
        """
        async with self._semaphore:
            return await self._execute_inner(
                graph_source=graph_source,
                input_messages=input_messages or [],
                initial_context=initial_context or {},
                bound_tools=bound_tools or [],
                tool_records=tool_records or {},
                llm_config=llm_config,
                max_iterations=max_iterations,
                max_tokens_budget=max_tokens_budget,
                max_tool_calls=max_tool_calls,
                max_duration_ms=max_duration_ms,
                max_cost_usd=max_cost_usd,
                tracer=tracer,
                trace=trace,
                sse_callback=sse_callback,
            )

    async def _execute_inner(
        self,
        *,
        graph_source: str,
        input_messages: list[dict],
        initial_context: dict,
        bound_tools: list[dict],
        tool_records: dict[str, dict],
        llm_config: dict,
        max_iterations: int,
        max_tokens_budget: int,
        max_tool_calls: int,
        max_duration_ms: int,
        max_cost_usd: float,
        tracer,
        trace,
        sse_callback,
    ) -> AgentExecutionResult:
        start_time = time.time()

        # 1. Create budget enforcer
        budget = BudgetEnforcer(
            max_tokens_budget=max_tokens_budget,
            max_tool_calls=max_tool_calls,
            max_iterations=max_iterations,
            max_duration_ms=max_duration_ms,
            max_cost_usd=max_cost_usd,
        )

        # 2. Create tool dispatcher
        dispatcher = ToolDispatcher(bound_tools=bound_tools, settings=None)
        dispatcher.set_tool_records(tool_records)

        # 3. Create agent context
        ctx = AgentContext(
            budget_enforcer=budget,
            tool_dispatcher=dispatcher,
            llm_config=llm_config,
            tracer=tracer,
            trace=trace,
            sse_callback=sse_callback,
        )

        # Seed state
        ctx.state["input"] = input_messages
        ctx.state.update(initial_context)

        # 4. Compile and build graph
        try:
            graph = self._compiler.build_graph_runtime(graph_source, ctx)
        except Exception as e:
            return AgentExecutionResult(
                status="failed",
                error_message=f"Graph compilation failed: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # 5. Walk the graph
        current_node = graph.entry_point
        step_index = 0

        try:
            while current_node != "__end__":
                budget.check_before_iteration()
                budget.record_iteration()

                node_def = graph.nodes[current_node]
                handler = node_def["handler"]
                transitions = node_def.get("transitions", {})

                # SSE: node entered
                if sse_callback:
                    sse_callback(_sse_module.node_entered(current_node, step_index))

                # Start step
                ctx._set_current_node(current_node)
                step = ctx._start_step(step_index, current_node, "handler")

                # Execute handler
                try:
                    if asyncio.iscoroutinefunction(handler):
                        transition_label = await handler(ctx)
                    else:
                        transition_label = await asyncio.to_thread(handler, ctx)
                except HumanInputRequired as e:
                    ctx._end_step(error=f"awaiting_human: {e.question}")
                    return AgentExecutionResult(
                        status="awaiting_approval",
                        output_messages=ctx.output_messages,
                        final_state=ctx.state,
                        human_question=e.question,
                        tokens_used=budget.state.tokens_used,
                        tool_calls_made=budget.state.tool_calls_made,
                        llm_calls_made=budget.state.llm_calls_made,
                        cost_usd=budget.state.cost_usd,
                        iterations_used=budget.state.iterations_used,
                        execution_time_ms=int((time.time() - start_time) * 1000),
                        steps=ctx.steps,
                    )

                ctx._end_step(transition=str(transition_label))

                # Resolve transition
                if transition_label is None:
                    # No explicit transition — end
                    current_node = "__end__"
                elif str(transition_label) in transitions:
                    next_node = transitions[str(transition_label)]
                    # SSE: node completed
                    if sse_callback:
                        sse_callback(_sse_module.node_completed(current_node, str(transition_label), next_node))
                    current_node = next_node
                else:
                    # Unknown transition label — treat as end
                    if sse_callback:
                        sse_callback(_sse_module.node_completed(current_node, str(transition_label), None))
                    current_node = "__end__"

                step_index += 1

                # Budget SSE update
                if sse_callback:
                    sse_callback(_sse_module.budget_update(
                        budget.state.tokens_used,
                        budget.state.cost_usd,
                        budget.pct_tokens(),
                        budget.pct_cost(),
                    ))

        except BudgetExceededError as e:
            ctx._end_step(error=str(e))
            execution_time_ms = int((time.time() - start_time) * 1000)
            if sse_callback:
                sse_callback(_sse_module.run_failed("budget_exceeded", str(e)))
            return AgentExecutionResult(
                status="failed",
                error_message=str(e),
                output_messages=ctx.output_messages,
                final_state=ctx.state,
                tokens_used=budget.state.tokens_used,
                tool_calls_made=budget.state.tool_calls_made,
                llm_calls_made=budget.state.llm_calls_made,
                cost_usd=budget.state.cost_usd,
                iterations_used=budget.state.iterations_used,
                execution_time_ms=execution_time_ms,
                steps=ctx.steps,
            )
        except Exception as e:
            ctx._end_step(error=str(e))
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Agent execution failed at node '{current_node}': {e}")
            if sse_callback:
                sse_callback(_sse_module.run_failed("failed", str(e)))
            return AgentExecutionResult(
                status="failed",
                error_message=str(e),
                output_messages=ctx.output_messages,
                final_state=ctx.state,
                tokens_used=budget.state.tokens_used,
                tool_calls_made=budget.state.tool_calls_made,
                llm_calls_made=budget.state.llm_calls_made,
                cost_usd=budget.state.cost_usd,
                iterations_used=budget.state.iterations_used,
                execution_time_ms=execution_time_ms,
                steps=ctx.steps,
            )

        # 6. Success
        execution_time_ms = int((time.time() - start_time) * 1000)
        if sse_callback:
            sse_callback(_sse_module.run_completed("completed", budget.state.tokens_used, budget.state.cost_usd))

        return AgentExecutionResult(
            status="completed",
            output_messages=ctx.output_messages,
            final_state=ctx.state,
            tokens_used=budget.state.tokens_used,
            tool_calls_made=budget.state.tool_calls_made,
            llm_calls_made=budget.state.llm_calls_made,
            cost_usd=budget.state.cost_usd,
            iterations_used=budget.state.iterations_used,
            execution_time_ms=execution_time_ms,
            steps=ctx.steps,
        )
