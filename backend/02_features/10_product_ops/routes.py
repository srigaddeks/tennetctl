"""
product_ops feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'product_ops' module is enabled.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_events: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.routes"
)
_links: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.02_links.routes"
)
_referrals: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.03_referrals.routes"
)
_profiles: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.04_profiles.routes"
)
_promos: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.05_promos.routes"
)
_partners: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.06_partners.routes"
)
_campaigns: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.07_campaigns.routes"
)
_cohorts: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.08_cohorts.routes"
)
_destinations: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.09_destinations.routes"
)

router = APIRouter()
router.include_router(_events.router)
router.include_router(_links.router)
router.include_router(_referrals.router)
router.include_router(_profiles.router)
router.include_router(_promos.router)
router.include_router(_partners.router)
router.include_router(_campaigns.router)
router.include_router(_cohorts.router)
router.include_router(_destinations.router)
