"""
Vault feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'vault' module is enabled.
Each sub-feature router owns its prefix (/v1/vault).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_secrets_routes: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.routes"
)

router = APIRouter()
router.include_router(_secrets_routes.router)
