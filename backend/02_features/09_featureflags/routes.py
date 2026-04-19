"""
featureflags feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'featureflags' module is enabled.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_flags: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.01_flags.routes"
)
# 02_permissions removed in 23R — old dim_flag_permissions + lnk_role_flag_permissions
# tables were dropped. Replaced by the capabilities surface below.
_capabilities: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.06_capabilities.routes"
)
_rules: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.03_rules.routes"
)
_overrides: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.04_overrides.routes"
)
_evaluations: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.05_evaluations.routes"
)
_apisix: Any = import_module(
    "backend.02_features.09_featureflags.apisix_routes"
)

router = APIRouter()
router.include_router(_flags.router)
router.include_router(_capabilities.router)
router.include_router(_rules.router)
router.include_router(_overrides.router)
router.include_router(_evaluations.router)
router.include_router(_apisix.router)
