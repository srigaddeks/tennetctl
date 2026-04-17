"""
audit feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'audit' module is enabled.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_events: Any = import_module(
    "backend.02_features.04_audit.sub_features.01_events.routes"
)
_saved_views: Any = import_module(
    "backend.02_features.04_audit.sub_features.02_saved_views.routes"
)
router = APIRouter()
router.include_router(_events.router)
router.include_router(_saved_views.router)
