"""GRC agent run state — carried through the entire agent loop."""

from __future__ import annotations

from typing import Any, TypedDict

from importlib import import_module as _im
ToolContext = _im("backend.20_ai.05_mcp.dispatcher").ToolContext


class GRCAgentState(TypedDict):
    # Identity
    conversation_id: str
    agent_run_id: str
    user_id: str
    tenant_key: str

    # LLM config
    model_id: str

    # Message history in OpenAI format
    # [{role, content}, ...assistant + tool roles appended as loop runs]
    messages: list[dict]

    # Context injected from the page the user was on
    # {framework_id?, control_id?, risk_id?, task_id?, org_id?, workspace_id?}
    page_context: dict[str, Any]

    # Tool execution context (pool + services)
    tool_context: ToolContext

    # Token budget enforcement
    token_budget: int           # model_context * 0.60
    tokens_consumed: int        # rolling total from tool results

    # Loop guards
    max_iterations: int         # default 6
    iteration: int

    # Terminal flags
    is_complete: bool
    error: str | None

    # LangFuse trace id (set once at run start, stored in DB)
    langfuse_trace_id: str | None

    # Original user message — stored so PageIndex MCP queries can use it
    # even when the current "last message" in the history is a tool result
    user_message: str
