"""monitoring feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'monitoring' module is
enabled. Plan 13-02 (metrics) and 13-03 (logs + traces OTLP) each add their
own sub-feature routers here.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_logs: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.routes"
)
_traces: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.03_traces.routes"
)

router = APIRouter()
router.include_router(_logs.router)
router.include_router(_traces.router)

_metrics: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.routes"
)
router.include_router(_metrics.router)

_saved_queries: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.04_saved_queries.routes"
)
router.include_router(_saved_queries.router)

_admin: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.04_saved_queries.admin_routes"
)
router.include_router(_admin.router)

_dashboards: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.routes"
)
router.include_router(_dashboards.router)

_synthetic: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.routes"
)
router.include_router(_synthetic.router)

_alerts: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.routes"
)
router.include_router(_alerts.router)

_escalation: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.08_escalation.routes"
)
router.include_router(_escalation.router)

_action_templates: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.09_action_templates.routes"
)
router.include_router(_action_templates.router)

_incidents: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.10_incidents.routes"
)
router.include_router(_incidents.router)

_slo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.routes"
)
router.include_router(_slo.router)

_dashboard_sharing: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.routes"
)
router.include_router(_dashboard_sharing.router)
