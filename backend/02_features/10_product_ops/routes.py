"""
product_ops feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'product_ops' module is enabled.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_track: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_track.routes"
)

router = APIRouter()
router.include_router(_track.router)
