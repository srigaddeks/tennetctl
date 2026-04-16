from __future__ import annotations

from importlib import import_module

_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

_dimensions_router_module = import_module("backend.07_tasks.01_dimensions.router")
_tasks_router_module = import_module("backend.07_tasks.02_tasks.router")
_assignments_router_module = import_module("backend.07_tasks.03_assignments.router")
_dependencies_router_module = import_module("backend.07_tasks.04_dependencies.router")
_events_router_module = import_module("backend.07_tasks.05_events.router")

router = InstrumentedAPIRouter(prefix="/api/v1/tk", tags=["tasks"])

router.include_router(_dimensions_router_module.router)
router.include_router(_tasks_router_module.router)
router.include_router(_assignments_router_module.router)
router.include_router(_dependencies_router_module.router)
router.include_router(_events_router_module.router)
