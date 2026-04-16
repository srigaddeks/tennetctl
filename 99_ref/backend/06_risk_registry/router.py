from __future__ import annotations

from importlib import import_module

_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

_dimensions_router_module = import_module("backend.06_risk_registry.01_dimensions.router")
_risks_router_module = import_module("backend.06_risk_registry.02_risks.router")
_assessments_router_module = import_module("backend.06_risk_registry.03_assessments.router")
_treatment_plans_router_module = import_module("backend.06_risk_registry.04_treatment_plans.router")
_control_mappings_router_module = import_module("backend.06_risk_registry.05_control_mappings.router")
_review_events_router_module = import_module("backend.06_risk_registry.06_review_events.router")
_questionnaires_router_module = import_module("backend.06_risk_registry.07_questionnaires.router")

router = InstrumentedAPIRouter(prefix="/api/v1/rr", tags=["risk-registry"])

router.include_router(_dimensions_router_module.router)
router.include_router(_risks_router_module.router)
router.include_router(_assessments_router_module.router)
router.include_router(_treatment_plans_router_module.router)
router.include_router(_control_mappings_router_module.router)
router.include_router(_review_events_router_module.router)
router.include_router(_questionnaires_router_module.router)
