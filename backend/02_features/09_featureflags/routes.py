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
_permissions: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.02_permissions.routes"
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

router = APIRouter()
router.include_router(_flags.router)
router.include_router(_permissions.router)
router.include_router(_rules.router)
router.include_router(_overrides.router)
router.include_router(_evaluations.router)
