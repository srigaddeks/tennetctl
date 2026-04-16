from __future__ import annotations
from importlib import import_module
_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
router = InstrumentedAPIRouter(prefix="/api/v1/ai/dimensions", tags=["ai-dimensions"])

@router.get("/agent-types")
async def list_agent_types() -> list[dict]:
    return [{"code": "copilot", "name": "System Copilot"},
            {"code": "supervisor", "name": "Supervisor"},
            {"code": "grc_assistant", "name": "GRC Assistant"},
            {"code": "signal_generator", "name": "Signal Generator"}]
