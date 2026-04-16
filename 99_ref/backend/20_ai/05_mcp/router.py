from __future__ import annotations
from importlib import import_module
GRC_TOOL_DEFINITIONS = import_module("backend.20_ai.05_mcp.tools.grc_tools").GRC_TOOL_DEFINITIONS
_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
router = InstrumentedAPIRouter(prefix="/api/v1/ai/mcp", tags=["ai-mcp"])

@router.get("/tools")
async def list_tools() -> list[dict]:
    return GRC_TOOL_DEFINITIONS
