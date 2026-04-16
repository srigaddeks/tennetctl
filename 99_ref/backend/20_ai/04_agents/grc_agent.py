"""
GRCAgent — token-budget-aware agentic loop for the GRC copilot.

Design invariants:
  - Token budget = model_context * 0.60 (hard stop, not a prompt hint)
  - Max 6 iterations per user turn
  - All tool calls bounded in the dispatcher — agent cannot bypass limits
  - LangFuse traces every LLM call (optional; disabled when settings not configured)
  - Persists assistant message + tool calls to Postgres after completion
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from importlib import import_module
from typing import TYPE_CHECKING, AsyncIterator

import asyncpg

_state_mod = import_module("backend.20_ai.04_agents.state")
_dispatcher_mod = import_module("backend.20_ai.05_mcp.dispatcher")
_grc_tools_mod = import_module("backend.20_ai.05_mcp.tools.grc_tools")
_factory_mod = import_module("backend.20_ai.14_llm_providers.factory")
_provider_mod = import_module("backend.20_ai.14_llm_providers.provider")
_pageindex_mod = import_module("backend.20_ai.03_memory.pageindex")

GRCAgentState = _state_mod.GRCAgentState
MCPToolDispatcher = _dispatcher_mod.MCPToolDispatcher
ToolContext = _dispatcher_mod.ToolContext
GRC_TOOL_CATEGORIES = _grc_tools_mod.GRC_TOOL_CATEGORIES
GRC_TOOL_DEFINITIONS = _grc_tools_mod.GRC_TOOL_DEFINITIONS
GRC_ALL_TOOL_DEFINITIONS = _grc_tools_mod.GRC_ALL_TOOL_DEFINITIONS
get_provider = _factory_mod.get_provider
LLMResponse = _provider_mod.LLMResponse
ToolCallResult = _provider_mod.ToolCallResult
PageIndexer = _pageindex_mod.PageIndexer
NullPageIndexer = _pageindex_mod.NullPageIndexer
_MCP_TOKEN_THRESHOLD = _pageindex_mod._MCP_TOKEN_THRESHOLD  # noqa: SLF001

# Tools that produce raw flat lists and benefit most from PageIndex compression
_PAGEINDEX_MCP_TOOLS = frozenset({
    "grc_list_frameworks",
    "grc_list_requirements",
    "grc_list_controls",
    "grc_list_risks",
    "grc_list_tasks",
    "grc_get_framework_hierarchy",
    "grc_get_control_hierarchy",
    "grc_get_risk_hierarchy",
    "grc_list_tasks_for_entity",
    "grc_framework_health",
    "grc_requirement_gaps",
    "grc_risk_concentration",
    "grc_control_health",
})

if TYPE_CHECKING:
    from typing import Any  # noqa: F401 — keep TYPE_CHECKING block for type checkers

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.agents.grc")

_streaming_module = import_module("backend.20_ai.02_conversations.streaming")
sse_event = _streaming_module.sse_event
sse_tool_call_start = _streaming_module.sse_tool_call_start
sse_tool_call_result = _streaming_module.sse_tool_call_result
sse_navigate = _streaming_module.sse_navigate
sse_navigate_page = _streaming_module.sse_navigate_page
sse_report_queued = _streaming_module.sse_report_queued
sse_form_fill_proposed = _streaming_module.sse_form_fill_proposed

_DEFAULT_MAX_ITERATIONS = 6
_DEFAULT_MAX_TOKENS = 4096
_MODEL_CONTEXT_SIZES: dict[str, int] = {
    "gpt-5.3-chat": 128000,
    "gpt-4o": 128000,
    "gpt-4-turbo": 128000,
    "claude-3-5-sonnet": 200000,
    "claude-opus-4": 200000,
    "default": 128000,
}


def _get_model_context(model_id: str) -> int:
    for prefix, ctx in _MODEL_CONTEXT_SIZES.items():
        if model_id.startswith(prefix):
            return ctx
    return _MODEL_CONTEXT_SIZES["default"]


def _format_page_context_for_prompt(ctx: dict) -> str:
    """
    Converts raw page_context dict into a human-readable system prompt note.
    UUIDs are passed only as tool-call IDs in a separate structured block.
    The prose block only contains human-readable codes and names.
    """
    prose_lines = ["[Current page context]"]
    id_block: dict[str, str] = {}

    # Entity context — most specific first
    if ctx.get("control_id"):
        code = ctx.get("control_code", "")
        name = ctx.get("control_name", "")
        fw = ctx.get("framework_name", "")
        label = f"{code} — {name}" if code and name else code or name or "unknown control"
        fw_part = f" in framework {fw}" if fw else ""
        prose_lines.append(f"  The user is viewing control: {label}{fw_part}")
        id_block["control_id"] = ctx["control_id"]
    elif ctx.get("risk_id"):
        title = ctx.get("risk_title", "unknown risk")
        prose_lines.append(f"  The user is viewing risk: {title}")
        id_block["risk_id"] = ctx["risk_id"]
    elif ctx.get("task_id"):
        title = ctx.get("task_title", "unknown task")
        prose_lines.append(f"  The user is viewing task: {title}")
        id_block["task_id"] = ctx["task_id"]
    elif ctx.get("framework_id"):
        name = ctx.get("framework_name", "unknown framework")
        prose_lines.append(f"  The user is viewing framework: {name}")
        id_block["framework_id"] = ctx["framework_id"]

    # Org/workspace
    org_name = ctx.get("org_name")
    ws_name = ctx.get("workspace_name")
    if org_name or ws_name:
        loc = " / ".join(filter(None, [org_name, ws_name]))
        prose_lines.append(f"  Organization/Workspace: {loc}")

    if len(prose_lines) == 1:
        route = ctx.get("route_pattern") or ctx.get("route", "")
        prose_lines.append(f"  On page: {route}")

    # IDs — separate block for tool parameters only
    if id_block:
        prose_lines.append("  [IDs for tool calls only — never quote these in responses]")
        for k, v in id_block.items():
            prose_lines.append(f"    {k}: {v}")

    prose_lines.append(
        "CRITICAL RULE: In your response, NEVER mention or quote any UUID/ID strings. "
        "Always use human-readable names and codes only (e.g. 'CC6-01', 'SOC 2 Type II'). "
        "If a tool fails, describe what you know from the page context using names — NOT IDs."
    )
    return "\n".join(prose_lines)


def _input_summary(args: dict) -> str:
    """One-line summary of tool input for SSE — never exposes sensitive values."""
    parts = [f"{k}={str(v)[:40]}" for k, v in args.items() if v is not None]
    return ", ".join(parts[:4]) or "(no args)"


def _output_summary(output: dict, error: str | None) -> str:
    if error:
        return f"error: {error[:120]}"
    if "total_count" in output:
        return f"{output.get('returned_count', '?')}/{output['total_count']} rows"
    keys = list(output.keys())[:3]
    return "ok — " + ", ".join(keys)


class GRCAgent:
    """
    Stateless agent: creates a new state dict per run and drives the
    tool-call loop until completion, budget exhaustion, or max iterations.
    """

    def __init__(
        self,
        *,
        pool: asyncpg.Pool,
        config: "ResolvedLLMConfig",
        settings,
        dispatcher: MCPToolDispatcher | None = None,
    ) -> None:
        self._pool = pool
        self._config = config
        self._settings = settings
        self._dispatcher = dispatcher or MCPToolDispatcher()
        self._provider = get_provider(
            provider_type=config.provider_type,
            provider_base_url=config.provider_base_url,
            api_key=config.api_key,
            model_id=config.model_id,
        )
        self._lf_client = self._init_langfuse()
        self._pageindexer = self._init_pageindexer()

    def _init_pageindexer(self):
        """Return a PageIndexer if AI_PAGEINDEX_ENABLED and provider URL set, else NullPageIndexer."""
        if (
            getattr(self._settings, "ai_pageindex_enabled", False)
            and getattr(self._settings, "ai_provider_url", None)
        ):
            return PageIndexer(settings=self._settings)
        return NullPageIndexer()

    # ------------------------------------------------------------------
    # LangFuse
    # ------------------------------------------------------------------

    def _init_langfuse(self):
        if not getattr(self._settings, "ai_langfuse_enabled", False):
            return None
        try:
            from langfuse import Langfuse
            return Langfuse(
                public_key=self._settings.ai_langfuse_public_key,
                secret_key=self._settings.ai_langfuse_secret_key,
                host=self._settings.ai_langfuse_host or "https://cloud.langfuse.com",
            )
        except Exception as exc:
            _logger.warning("LangFuse init failed (non-fatal): %s", exc)
            return None

    def _lf_start_trace(self, state: GRCAgentState):
        if not self._lf_client:
            return None, None
        try:
            trace = self._lf_client.trace(
                name=f"grc_agent/{state['conversation_id']}",
                user_id=state["user_id"],
                metadata={
                    "conversation_id": state["conversation_id"],
                    "agent_run_id": state["agent_run_id"],
                    "model_id": state["model_id"],
                },
            )
            return trace, trace.id
        except Exception:
            return None, None

    def _lf_record_llm_call(self, trace, iteration: int, response: LLMResponse):
        if not trace:
            return
        try:
            trace.generation(
                name=f"llm_call/iter_{iteration}",
                model=response.model_id,
                usage={"input": response.input_tokens, "output": response.output_tokens},
                output=response.content or f"[{len(response.tool_calls)} tool calls]",
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # DB persistence helpers
    # ------------------------------------------------------------------

    async def _create_agent_run(self, conversation_id: str) -> str:
        run_id = str(uuid.uuid4())
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO "20_ai"."24_fct_agent_runs"
                    (id, conversation_id, agent_type_code, status, model_id)
                VALUES ($1::uuid, $2::uuid, 'grc_assistant', 'running', $3)
                """,
                run_id, conversation_id, self._config.model_id,
            )
        return run_id

    async def _complete_agent_run(
        self,
        run_id: str,
        *,
        input_tokens: int,
        output_tokens: int,
        status: str = "completed",
        error_message: str | None = None,
        langfuse_trace_id: str | None = None,
    ) -> None:
        total = input_tokens + output_tokens
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE "20_ai"."24_fct_agent_runs"
                SET status = $1,
                    input_tokens = $2,
                    output_tokens = $3,
                    total_tokens = $4,
                    error_message = $5,
                    langfuse_trace_id = $6,
                    completed_at = NOW()
                WHERE id = $7::uuid
                """,
                status, input_tokens, output_tokens, total,
                error_message, langfuse_trace_id, run_id,
            )

    async def _persist_assistant_message(
        self,
        conversation_id: str,
        content: str | None,
        token_count: int,
    ) -> str:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO "20_ai"."21_fct_messages"
                    (conversation_id, role_code, content, token_count, model_id)
                VALUES ($1::uuid, 'assistant', $2, $3, $4)
                RETURNING id::text
                """,
                conversation_id,
                content or "",
                token_count,
                self._config.model_id,
            )
            await conn.execute(
                'UPDATE "20_ai"."20_fct_conversations" SET updated_at=NOW() WHERE id=$1::uuid',
                conversation_id,
            )
        return row["id"]

    async def _persist_tool_calls(
        self,
        message_id: str,
        run_id: str,
        tool_calls_data: list[dict],
    ) -> None:
        if not tool_calls_data:
            return
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO "20_ai"."22_fct_tool_calls"
                    (message_id, agent_run_id, tool_name, tool_category,
                     input_json, output_json, duration_ms, is_successful, error_message)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9)
                """,
                [
                    (
                        message_id, run_id,
                        tc["tool_name"],
                        GRC_TOOL_CATEGORIES.get(tc["tool_name"], "navigation"),
                        json.dumps(tc["input"]),
                        json.dumps(tc["output"]),
                        tc.get("duration_ms"),
                        tc.get("is_successful", True),
                        tc.get("error"),
                    )
                    for tc in tool_calls_data
                ],
            )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def run(
        self,
        *,
        conversation_id: str,
        user_message: str,
        history: list[dict],
        system_prompt: str,
        tool_context: ToolContext,
        page_context: dict,
    ) -> AsyncIterator[str]:
        """
        Yields SSE strings. Persists assistant message + tool calls to DB on completion.
        """
        run_id = await self._create_agent_run(conversation_id)
        model_id = self._config.model_id
        model_context = _get_model_context(model_id)
        token_budget = int(model_context * 0.60)

        state: GRCAgentState = {
            "conversation_id": conversation_id,
            "agent_run_id": run_id,
            "user_id": tool_context.user_id,
            "tenant_key": tool_context.tenant_key,
            "model_id": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": user_message},
            ],
            "page_context": page_context,
            "tool_context": tool_context,
            "token_budget": token_budget,
            "tokens_consumed": 0,
            "max_iterations": _DEFAULT_MAX_ITERATIONS,
            "iteration": 0,
            "is_complete": False,
            "error": None,
            "langfuse_trace_id": None,
            # Store original user message for PageIndex MCP queries
            "user_message": user_message,
        }

        # Inject page_context so the LLM knows where the user is
        # Format as human-readable text — never expose raw UUIDs to the response
        if page_context:
            ctx_note = _format_page_context_for_prompt(page_context)
            if ctx_note:
                state["messages"][0]["content"] += "\n\n" + ctx_note

        lf_trace, lf_trace_id = self._lf_start_trace(state)
        state["langfuse_trace_id"] = lf_trace_id

        # Start SSE stream
        message_id = str(uuid.uuid4())
        yield await sse_event("message_start", {"message_id": message_id})

        total_input_tokens = 0
        total_output_tokens = 0
        final_content: str | None = None
        tool_calls_log: list[dict] = []

        try:
            async for chunk in self._agent_loop(state, lf_trace):
                if isinstance(chunk, str):
                    # SSE string — pass through to caller
                    yield chunk
                elif isinstance(chunk, dict) and chunk.get("_internal"):
                    # Internal accounting from loop
                    total_input_tokens += chunk.get("input_tokens", 0)
                    total_output_tokens += chunk.get("output_tokens", 0)
                    if chunk.get("content"):
                        final_content = chunk["content"]
                    if chunk.get("tool_calls_log"):
                        tool_calls_log.extend(chunk["tool_calls_log"])

        except Exception as exc:
            _logger.exception("GRCAgent run %s failed: %s", run_id, exc)
            state["error"] = str(exc)
            yield await sse_event("error", {"message": "Agent encountered an error. Please try again."})

        # Persist assistant message
        msg_id = await self._persist_assistant_message(
            conversation_id,
            final_content,
            token_count=total_output_tokens,
        )

        # Persist tool calls
        await self._persist_tool_calls(msg_id, run_id, tool_calls_log)

        # Mark run complete
        await self._complete_agent_run(
            run_id,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            status="failed" if state.get("error") else "completed",
            error_message=state.get("error"),
            langfuse_trace_id=lf_trace_id,
        )

        yield await sse_event("message_end", {
            "usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "tool_calls": len(tool_calls_log),
            },
        })

        # Flush LangFuse async
        if self._lf_client:
            try:
                asyncio.create_task(asyncio.to_thread(self._lf_client.flush))
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Agent loop
    # ------------------------------------------------------------------

    async def _agent_loop(
        self,
        state: GRCAgentState,
        lf_trace,
    ) -> AsyncIterator:
        """
        Core agentic loop. Yields SSE chunks and internal accounting dicts.
        """
        while not state["is_complete"] and state["iteration"] < state["max_iterations"]:
            state["iteration"] += 1

            # Call LLM
            response: LLMResponse = await self._provider.chat_completion(
                messages=state["messages"],
                tools=GRC_ALL_TOOL_DEFINITIONS,
                temperature=self._config.temperature,
                max_tokens=_DEFAULT_MAX_TOKENS,
            )

            # Account tokens
            yield {"_internal": True, "input_tokens": response.input_tokens, "output_tokens": response.output_tokens}
            self._lf_record_llm_call(lf_trace, state["iteration"], response)

            if response.finish_reason == "tool_calls" and response.tool_calls:
                # --- Tool call branch ---

                # Append assistant message with tool calls in OpenAI format
                state["messages"].append({
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                        }
                        for tc in response.tool_calls
                    ],
                })

                iteration_tool_log: list[dict] = []

                for tc in response.tool_calls:
                    # SSE: tool starting
                    category = GRC_TOOL_CATEGORIES.get(tc.name, "navigation")
                    yield await sse_tool_call_start(tc.name, category, _input_summary(tc.arguments))

                    # Execute
                    t0 = time.monotonic()
                    result = await self._dispatcher.dispatch(tc.name, tc.arguments, state["tool_context"])
                    duration_ms = int((time.monotonic() - t0) * 1000)

                    # SSE: tool done
                    yield await sse_tool_call_result(
                        tc.name,
                        result.error is None,
                        _output_summary(result.output, result.error),
                    )

                    # Navigation action — emit navigate event so the frontend can route
                    if result.output.get("_navigate") and result.error is None:
                        yield await sse_navigate(
                            entity_type=result.output["entity_type"],
                            entity_id=result.output["entity_id"],
                            label=result.output.get("label", ""),
                            framework_id=result.output.get("framework_id"),
                        )

                    # Page navigation action — emit navigate_page so the frontend routes to an app page
                    if result.output.get("_navigate_page") and result.error is None:
                        yield await sse_navigate_page(
                            page=result.output["page"],
                            label=result.output.get("label", ""),
                        )

                    # Report queued — emit report_queued so the frontend shows a live ReportCard
                    if result.output.get("_report_queued") and result.error is None:
                        yield await sse_report_queued(
                            report_id=result.output["report_id"],
                            report_type=result.output["report_type"],
                            title=result.output.get("title"),
                            status=result.output.get("status", "queued"),
                        )

                    # Form fill proposed — emit so the frontend can pre-fill a form
                    if result.output.get("_form_fill_proposed") and result.error is None:
                        yield await sse_form_fill_proposed(
                            fields=result.output["fields"],
                            explanation=result.output.get("explanation", ""),
                        )

                    # Write action — emit approval_created so the frontend shows ApprovalCard
                    if result.output.get("_approval") and result.error is None:
                        yield await sse_event("approval_created", {
                            "id": result.output["approval_id"],
                            "tool_name": result.output["tool_name"],
                            "tool_category": "write",
                            "entity_type": result.output.get("entity_type"),
                            "operation": result.output.get("operation"),
                            "payload_json": tc.arguments,
                            "diff_json": {"after": tc.arguments},
                            "status_code": "pending",
                            "label": result.output.get("label", ""),
                        })

                    # PageIndex compression for large MCP results:
                    # If the raw JSON payload is above the threshold and the tool
                    # is in the eligible set, replace the raw JSON with a concise
                    # PageIndex-navigated summary.  Falls back to raw JSON silently.
                    tool_content_str = json.dumps(result.output, default=str)
                    if (
                        tc.name in _PAGEINDEX_MCP_TOOLS
                        and result.error is None
                        and len(tool_content_str) > _MCP_TOKEN_THRESHOLD
                    ):
                        try:
                            user_query = state.get("user_message", "")
                            pi_summary = await self._pageindexer.retrieve_from_grc_data(
                                query=user_query,
                                tool_name=tc.name,
                                data=result.output,
                            )
                            if pi_summary:
                                tool_content_str = (
                                    f"[PageIndex summary of {tc.name} result]\n{pi_summary}"
                                )
                                _logger.debug(
                                    "PageIndex compressed MCP result %s: %d → %d chars",
                                    tc.name,
                                    len(json.dumps(result.output, default=str)),
                                    len(tool_content_str),
                                )
                        except Exception as pi_exc:
                            _logger.debug("PageIndex MCP compression failed (non-fatal): %s", pi_exc)

                    # Append tool result message
                    state["messages"].append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_content_str,
                    })

                    # Budget tracking
                    state["tokens_consumed"] += result.token_estimate
                    iteration_tool_log.append({
                        "tool_name": tc.name,
                        "input": tc.arguments,
                        "output": result.output,
                        "duration_ms": duration_ms,
                        "is_successful": result.error is None,
                        "error": result.error,
                    })

                    if state["tokens_consumed"] >= state["token_budget"]:
                        # Hard budget stop — ask model to synthesize with what it has
                        state["messages"].append({
                            "role": "user",
                            "content": (
                                "[SYSTEM] Token budget reached. Synthesize your answer from the "
                                "information gathered so far. Do not call any more tools."
                            ),
                        })
                        yield {"_internal": True, "tool_calls_log": iteration_tool_log}
                        break  # exit tool loop — one more LLM call will follow

                yield {"_internal": True, "tool_calls_log": iteration_tool_log}

            else:
                # --- Text response branch — final answer ---
                content = response.content or ""
                words = content.split()
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield await sse_event("content_delta", {"delta": chunk})

                yield {"_internal": True, "content": content}
                state["is_complete"] = True

        if not state["is_complete"]:
            # Max iterations hit without text response — ask for final synthesis
            state["messages"].append({
                "role": "user",
                "content": (
                    "[SYSTEM] Maximum tool iterations reached. Please provide your best "
                    "answer based on the information gathered."
                ),
            })
            response = await self._provider.chat_completion(
                messages=state["messages"],
                tools=None,
                temperature=self._config.temperature,
                max_tokens=_DEFAULT_MAX_TOKENS,
            )
            yield {"_internal": True, "input_tokens": response.input_tokens, "output_tokens": response.output_tokens}
            content = response.content or ""
            words = content.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield await sse_event("content_delta", {"delta": chunk})
            yield {"_internal": True, "content": content}
