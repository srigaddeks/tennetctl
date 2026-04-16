"""
Tool dispatcher — routes ctx.tool() calls to registered tools.

Handles tool allowlists, approval gates, timeout enforcement.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger

logger = get_logger("backend.agent_sandbox.tool_dispatcher")


@dataclass(frozen=True)
class ToolCallResult:
    tool_code: str
    output: dict
    duration_ms: int
    error: str | None = None


class ToolDispatcher:
    """Dispatches tool calls to registered tool implementations."""

    def __init__(self, *, bound_tools: list[dict], settings) -> None:
        """
        bound_tools: list of dicts from AgentRepository.list_bound_tools()
            Each has: tool_id, tool_code, tool_type_code, tool_name
        """
        self._tools_by_code = {t["tool_code"]: t for t in bound_tools}
        self._settings = settings
        self._tool_records: dict[str, dict] = {}  # Populated with full records if needed

    def set_tool_records(self, records: dict[str, dict]) -> None:
        """Set full tool records (from DB) for execution."""
        self._tool_records = records

    @property
    def available_tool_codes(self) -> list[str]:
        return list(self._tools_by_code.keys())

    async def dispatch(self, tool_code: str, input_data: dict) -> ToolCallResult:
        """Dispatch a tool call. Returns ToolCallResult."""
        if tool_code not in self._tools_by_code:
            return ToolCallResult(
                tool_code=tool_code,
                output={"error": f"Tool '{tool_code}' not bound to this agent"},
                duration_ms=0,
                error=f"Tool '{tool_code}' not bound to this agent",
            )

        tool_meta = self._tools_by_code[tool_code]
        tool_record = self._tool_records.get(tool_code, {})
        tool_type = tool_meta.get("tool_type_code", "")

        start = time.time()
        try:
            if tool_type == "python_function":
                result = await self._execute_python_tool(tool_record, input_data)
            elif tool_type == "api_endpoint":
                result = await self._execute_api_tool(tool_record, input_data)
            elif tool_type == "sandbox_signal":
                result = await self._execute_signal_tool(tool_record, input_data)
            elif tool_type == "mcp_server":
                result = await self._execute_mcp_tool(tool_record, input_data)
            elif tool_type == "db_query":
                result = await self._execute_db_query_tool(tool_record, input_data)
            else:
                result = {"error": f"Unknown tool type: {tool_type}"}
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.error(f"Tool '{tool_code}' execution failed: {e}")
            return ToolCallResult(
                tool_code=tool_code,
                output={"error": str(e)},
                duration_ms=duration_ms,
                error=str(e),
            )

        duration_ms = int((time.time() - start) * 1000)
        return ToolCallResult(
            tool_code=tool_code,
            output=result if isinstance(result, dict) else {"result": result},
            duration_ms=duration_ms,
        )

    async def _execute_python_tool(self, tool_record: dict, input_data: dict) -> dict:
        """Execute a Python function tool in RestrictedPython sandbox."""
        python_source = tool_record.get("python_source", "")
        if not python_source:
            return {"error": "Tool has no python_source"}

        _engine_module = import_module("backend.10_sandbox.07_execution.engine")
        engine = _engine_module.SignalExecutionEngine(timeout_ms=30000, max_memory_mb=128)

        # Tool source defines: def execute(input: dict) -> dict
        # Append evaluate() shim so SignalExecutionEngine can find it
        wrapped_source = python_source + "\n\ndef evaluate(dataset):\n    return execute(dataset)\n"
        result = await engine.execute(python_source=wrapped_source, dataset=input_data)
        if result.status == "completed" and result.result_code:
            return {
                "result": result.result_code,
                "summary": result.result_summary,
                "details": result.result_details,
            }
        return {"error": result.error_message or "Tool execution failed"}

    async def _execute_api_tool(self, tool_record: dict, input_data: dict) -> dict:
        """Execute an API endpoint tool via HTTP."""
        import httpx

        endpoint_url = tool_record.get("endpoint_url", "")
        if not endpoint_url:
            return {"error": "Tool has no endpoint_url"}

        timeout_ms = tool_record.get("timeout_ms", 30000)
        async with httpx.AsyncClient(timeout=timeout_ms / 1000) as client:
            resp = await client.post(endpoint_url, json=input_data)
            resp.raise_for_status()
            return resp.json()

    async def _execute_signal_tool(self, tool_record: dict, input_data: dict) -> dict:
        """Execute an existing sandbox signal as a tool."""
        signal_id = tool_record.get("signal_id")
        if not signal_id:
            return {"error": "Tool has no signal_id"}
        # Delegate to signal execution
        return {"error": "signal_tool execution not yet implemented", "signal_id": signal_id}

    async def _execute_mcp_tool(self, tool_record: dict, input_data: dict) -> dict:
        """Execute an MCP server tool."""
        mcp_url = tool_record.get("mcp_server_url")
        if not mcp_url:
            return {"error": "Tool has no mcp_server_url"}
        return {"error": "mcp_tool execution not yet implemented", "mcp_server_url": mcp_url}

    async def _execute_db_query_tool(self, tool_record: dict, input_data: dict) -> dict:
        """Execute a read-only database query tool."""
        return {"error": "db_query_tool execution not yet implemented"}
