from __future__ import annotations

from importlib import import_module

_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

_attachments_router_module = import_module("backend.09_attachments.01_attachments.router")

router = InstrumentedAPIRouter(prefix="/api/v1/at", tags=["attachments"])
router.include_router(_attachments_router_module.router)
