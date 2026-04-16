"""
FormFillAgent — a lightweight, self-contained agentic loop for form filling.

Completely separate from GRCAgent:
  - No DB persistence (ephemeral sessions)
  - Only read tools + grc_propose_form_fields
  - Max 4 iterations (form fill is simple compared to full copilot)
  - Emits the same SSE events as GRCAgent for frontend compatibility
  - Uses the MCP dispatcher for tool execution (same tool handlers, same DB)
"""

from __future__ import annotations

import json
import time
import uuid
from importlib import import_module
from typing import TYPE_CHECKING, AsyncIterator

import asyncpg

if TYPE_CHECKING:
    pass  # type-only imports only

_logging_module = import_module("backend.01_core.logging_utils")
_dispatcher_mod = import_module("backend.20_ai.05_mcp.dispatcher")
_grc_tools_mod = import_module("backend.20_ai.05_mcp.tools.grc_tools")
_factory_mod = import_module("backend.20_ai.14_llm_providers.factory")
_streaming_mod = import_module("backend.20_ai.02_conversations.streaming")
_pageindex_mod = import_module("backend.20_ai.03_memory.pageindex")

_logger = _logging_module.get_logger("backend.ai.form_fill.agent")

MCPToolDispatcher = _dispatcher_mod.MCPToolDispatcher
ToolContext = _dispatcher_mod.ToolContext
GRC_FORM_FILL_TOOL_DEFINITIONS = _grc_tools_mod.GRC_FORM_FILL_TOOL_DEFINITIONS
GRC_TOOL_CATEGORIES = _grc_tools_mod.GRC_TOOL_CATEGORIES
get_provider = _factory_mod.get_provider
sse_event = _streaming_mod.sse_event
sse_form_fill_proposed = _streaming_mod.sse_form_fill_proposed
PageIndexer = _pageindex_mod.PageIndexer
NullPageIndexer = _pageindex_mod.NullPageIndexer
_MCP_TOKEN_THRESHOLD = _pageindex_mod._MCP_TOKEN_THRESHOLD  # noqa: SLF001

# Same eligible tools as GRCAgent
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

_MAX_ITERATIONS = 4
_MAX_TOKENS = 2048


def _input_summary(args: dict) -> str:
    parts = [f"{k}={str(v)[:40]}" for k, v in args.items() if v is not None]
    return ", ".join(parts[:4]) or "(no args)"


def _output_summary(output: dict, error: str | None) -> str:
    if error:
        return f"error: {error[:80]}"
    if "total_count" in output:
        return f"{output.get('returned_count', '?')}/{output['total_count']} rows"
    keys = list(output.keys())[:3]
    return "ok — " + ", ".join(keys)


class FormFillAgent:
    """
    Stateless agentic loop for conversational form filling.
    One instance can serve many concurrent requests.
    """

    def __init__(self, *, config, settings) -> None:
        self._config = config
        self._settings = settings
        self._dispatcher = MCPToolDispatcher()
        self._provider = get_provider(
            provider_type=config.provider_type,
            provider_base_url=config.provider_base_url,
            api_key=config.api_key,
            model_id=config.model_id,
        )
        self._pageindexer = (
            PageIndexer(settings=settings)
            if (
                getattr(settings, "ai_pageindex_enabled", False)
                and getattr(settings, "ai_provider_url", None)
            )
            else NullPageIndexer()
        )

    async def run(
        self,
        *,
        message: str,
        history: list[dict],
        system_prompt: str,
        tool_context: ToolContext,
    ) -> AsyncIterator[str]:
        """Yields SSE strings. No DB writes."""
        message_id = str(uuid.uuid4())
        yield await sse_event("message_start", {"message_id": message_id})

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": message},
        ]

        total_input = 0
        total_output = 0
        iteration = 0

        try:
            while iteration < _MAX_ITERATIONS:
                iteration += 1

                LLMResponse = _factory_mod  # just for type reference below
                response = await self._provider.chat_completion(
                    messages=messages,
                    tools=GRC_FORM_FILL_TOOL_DEFINITIONS,
                    temperature=self._config.temperature,
                    max_tokens=_MAX_TOKENS,
                )
                total_input += response.input_tokens
                total_output += response.output_tokens

                if response.finish_reason == "tool_calls" and response.tool_calls:
                    # Append assistant turn with tool calls
                    messages.append({
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

                    for tc in response.tool_calls:
                        category = GRC_TOOL_CATEGORIES.get(tc.name, "navigation")
                        yield await sse_event("tool_call_start", {
                            "tool_name": tc.name,
                            "tool_category": category,
                            "input_summary": _input_summary(tc.arguments),
                        })

                        t0 = time.monotonic()
                        result = await self._dispatcher.dispatch(tc.name, tc.arguments, tool_context)
                        duration_ms = int((time.monotonic() - t0) * 1000)

                        yield await sse_event("tool_call_result", {
                            "tool_name": tc.name,
                            "is_successful": result.error is None,
                            "output_summary": _output_summary(result.output, result.error),
                        })

                        # Form fill proposed — emit SSE and stop
                        if result.output.get("_form_fill_proposed") and result.error is None:
                            yield await sse_form_fill_proposed(
                                fields=result.output.get("fields", {}),
                                explanation=result.output.get("explanation", ""),
                            )
                            yield await sse_event("message_end", {
                                "usage": {"input_tokens": total_input, "output_tokens": total_output},
                            })
                            return

                        tool_content_str = json.dumps(result.output, default=str)
                        if (
                            tc.name in _PAGEINDEX_MCP_TOOLS
                            and result.error is None
                            and len(tool_content_str) > _MCP_TOKEN_THRESHOLD
                        ):
                            try:
                                pi_summary = await self._pageindexer.retrieve_from_grc_data(
                                    query=message,
                                    tool_name=tc.name,
                                    data=result.output,
                                )
                                if pi_summary:
                                    tool_content_str = (
                                        f"[PageIndex summary of {tc.name} result]\n{pi_summary}"
                                    )
                            except Exception as pi_exc:
                                _logger.debug("PageIndex compression failed (non-fatal): %s", pi_exc)

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": tool_content_str,
                        })

                else:
                    # Text response — stream it as content_delta then done
                    content = response.content or ""
                    if content:
                        yield await sse_event("content_delta", {"delta": content})
                    break

        except Exception as exc:
            _logger.exception("FormFillAgent run failed: %s", exc)
            yield await sse_event("error", {"message": "Agent encountered an error. Please try again."})

        yield await sse_event("message_end", {
            "usage": {"input_tokens": total_input, "output_tokens": total_output},
        })
