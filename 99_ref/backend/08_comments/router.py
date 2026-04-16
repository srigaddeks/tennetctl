from __future__ import annotations

from importlib import import_module

_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

_comments_router_module = import_module("backend.08_comments.01_comments.router")

router = InstrumentedAPIRouter(prefix="/api/v1/cm", tags=["comments"])

router.include_router(_comments_router_module.router)
