from __future__ import annotations
from importlib import import_module
_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
router = InstrumentedAPIRouter(prefix="/api/v1/ai/agents", tags=["ai-agents"])

@router.get("/types")
async def list_agent_types() -> list[dict]:
    return []  # Phase 2: LangGraph agent graph registry

@router.get("/runs")
async def list_agent_runs() -> list[dict]:
    return []  # Phase 2: Agent run tracking
