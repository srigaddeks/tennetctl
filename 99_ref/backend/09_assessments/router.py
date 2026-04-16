from __future__ import annotations

from importlib import import_module

_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

_types_router_module = import_module("backend.09_assessments._01_assessment_types.router")
_assessments_router_module = import_module("backend.09_assessments._02_assessments.router")
_findings_router_module = import_module("backend.09_assessments._03_findings.router")
_responses_router_module = import_module("backend.09_assessments._04_finding_responses.router")

router = InstrumentedAPIRouter(prefix="/api/v1/as", tags=["assessments"])

router.include_router(_types_router_module.router)
router.include_router(_assessments_router_module.router)
router.include_router(_findings_router_module.router)
router.include_router(_responses_router_module.router)
