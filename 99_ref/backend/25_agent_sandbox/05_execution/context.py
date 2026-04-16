"""
AgentContext — the controlled ctx object users interact with.

Every ctx.llm() call goes through the platform's LLM provider.
Every ctx.tool() call goes through the platform's tool dispatcher.
State, emit, ask_human, and memory are all platform-controlled.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

_logging_module = import_module("backend.01_core.logging_utils")
_sse_module = import_module("backend.25_agent_sandbox.07_streaming.events")
get_logger = _logging_module.get_logger

logger = get_logger("backend.agent_sandbox.context")


@dataclass
class LLMCallRecord:
    model_id: str | None
    system_prompt: str
    user_prompt: str
    response_text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    duration_ms: int


@dataclass
class ToolCallRecord:
    tool_code: str
    tool_type_code: str
    input_json: dict
    output_json: dict
    duration_ms: int
    error: str | None
    approval_status: str | None


@dataclass
class StepRecord:
    step_index: int
    node_name: str
    step_type: str
    input_json: dict | None
    output_json: dict | None
    transition: str | None
    tokens_used: int
    cost_usd: float
    duration_ms: int
    error_message: str | None
    started_at: float
    completed_at: float | None
    llm_calls: list[LLMCallRecord] = field(default_factory=list)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)


class HumanInputRequired(Exception):
    """Raised when ctx.ask_human() is called — pauses execution."""
    def __init__(self, question: str) -> None:
        self.question = question
        super().__init__(question)


class AgentContext:
    """The controlled ctx object provided to user-defined agent handlers.

    All LLM calls, tool calls, and state mutations go through this object,
    giving the platform full control over budget, tracing, and approval.
    """

    def __init__(
        self,
        *,
        budget_enforcer,
        tool_dispatcher,
        llm_config: dict,
        tracer=None,
        trace=None,
        sse_callback=None,
        current_node: str = "",
    ) -> None:
        from .budget_enforcer import BudgetEnforcer
        from .tool_dispatcher import ToolDispatcher

        self._budget: BudgetEnforcer = budget_enforcer
        self._tools: ToolDispatcher = tool_dispatcher
        self._llm_config = llm_config  # {provider_url, api_key, model}
        self._tracer = tracer
        self._trace = trace
        self._sse_callback = sse_callback
        self._current_node = current_node

        # Public state
        self.state: dict[str, Any] = {}
        self.memory: dict[str, Any] = {}

        # Execution records
        self._steps: list[StepRecord] = []
        self._current_step: StepRecord | None = None
        self._output_messages: list[dict] = []

    @property
    def steps(self) -> list[StepRecord]:
        return self._steps

    @property
    def output_messages(self) -> list[dict]:
        return self._output_messages

    def _set_current_node(self, node_name: str) -> None:
        self._current_node = node_name

    def _start_step(self, step_index: int, node_name: str, step_type: str) -> StepRecord:
        step = StepRecord(
            step_index=step_index,
            node_name=node_name,
            step_type=step_type,
            input_json=None,
            output_json=None,
            transition=None,
            tokens_used=0,
            cost_usd=0.0,
            duration_ms=0,
            error_message=None,
            started_at=time.time(),
            completed_at=None,
        )
        self._current_step = step
        self._steps.append(step)
        return step

    def _end_step(self, transition: str | None = None, error: str | None = None) -> None:
        if self._current_step:
            self._current_step.completed_at = time.time()
            self._current_step.duration_ms = int(
                (self._current_step.completed_at - self._current_step.started_at) * 1000
            )
            self._current_step.transition = transition
            self._current_step.error_message = error

    # ── LLM ───────────────────────────────────────────────────

    def llm(self, system: str, user: str, *, temperature: float | None = None, max_tokens: int = 4000) -> str:
        """Make an LLM call. Synchronous from the handler's perspective.

        Internally runs async via the event loop.
        """
        self._budget.check_before_llm()

        # Emit SSE
        if self._sse_callback:
            self._sse_callback(_sse_module.llm_call_start(self._current_node, system))

        start = time.time()

        # Run the async LLM call synchronously for the handler
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._async_llm(system, user, temperature=temperature, max_tokens=max_tokens))

        duration_ms = int((time.time() - start) * 1000)

        # Estimate tokens (rough: 1 token ≈ 4 chars)
        input_tokens = (len(system) + len(user)) // 4
        output_tokens = len(result) // 4
        total_tokens = input_tokens + output_tokens
        # Estimate cost (rough: $0.01 per 1K tokens for mid-tier model)
        cost_usd = total_tokens * 0.00001

        self._budget.record_llm_call(total_tokens, cost_usd)

        # Record
        llm_record = LLMCallRecord(
            model_id=self._llm_config.get("model"),
            system_prompt=system,
            user_prompt=user,
            response_text=result,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
        )
        if self._current_step:
            self._current_step.llm_calls.append(llm_record)
            self._current_step.tokens_used += total_tokens
            self._current_step.cost_usd += cost_usd

        # Emit SSE
        if self._sse_callback:
            self._sse_callback(_sse_module.llm_call_complete(self._current_node, total_tokens, duration_ms))

        return result

    async def _async_llm(self, system: str, user: str, *, temperature: float | None, max_tokens: int) -> str:
        """Internal async LLM call using platform's LLM utilities."""
        _llm_utils = import_module("backend.20_ai._llm_utils")
        llm_complete = _llm_utils.llm_complete

        return await llm_complete(
            provider_url=self._llm_config["provider_url"],
            api_key=self._llm_config["api_key"],
            model=self._llm_config["model"],
            system=system,
            user=user,
            max_tokens=max_tokens,
            temperature=temperature or self._llm_config.get("temperature", 0.3),
            tracer=self._tracer,
            trace=self._trace,
            generation_name=f"agent.{self._current_node}.llm",
        )

    # ── Tools ─────────────────────────────────────────────────

    def tool(self, tool_code: str, input_data: dict | None = None) -> dict:
        """Call a registered tool. Synchronous from the handler's perspective."""
        self._budget.check_before_tool()

        if self._sse_callback:
            self._sse_callback(_sse_module.tool_call_start(self._current_node, tool_code))

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._tools.dispatch(tool_code, input_data or {}))

        self._budget.record_tool_call()

        tool_record = ToolCallRecord(
            tool_code=result.tool_code,
            tool_type_code=self._tools._tools_by_code.get(tool_code, {}).get("tool_type_code", ""),
            input_json=input_data or {},
            output_json=result.output,
            duration_ms=result.duration_ms,
            error=result.error,
            approval_status=None,
        )
        if self._current_step:
            self._current_step.tool_calls.append(tool_record)

        if self._sse_callback:
            self._sse_callback(_sse_module.tool_call_result(self._current_node, tool_code, result.duration_ms))

        return result.output

    # ── State & Output ────────────────────────────────────────

    def emit(self, event_type: str, data: dict | None = None) -> None:
        """Emit an event to the UI via SSE."""
        self._output_messages.append({"type": event_type, "data": data or {}})
        if self._sse_callback:
            self._sse_callback(_sse_module.SSEEvent(event=f"agent.{event_type}", data=data or {}))

    def ask_human(self, question: str) -> str:
        """Pause execution and wait for human input.

        Raises HumanInputRequired — the engine catches this,
        saves checkpoint, sets status to awaiting_approval.
        """
        raise HumanInputRequired(question)

    def checkpoint(self) -> None:
        """Save a state checkpoint. The engine persists this to DB."""
        # No-op during execution; the engine reads ctx.state after each node
        pass
