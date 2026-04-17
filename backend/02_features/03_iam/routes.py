"""
IAM feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'iam' module is enabled
(always on per feature.manifest.yaml). Each sub-feature router owns its prefix
(/v1/orgs, /v1/workspaces, etc.) so this file only composes.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_orgs_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.routes"
)
_ws_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.02_workspaces.routes"
)
_users_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.routes"
)
_memberships_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.routes"
)
_roles_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.routes"
)
_groups_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.05_groups.routes"
)
_applications_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.06_applications.routes"
)
_auth_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.routes"
)
_credentials_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.routes"
)
_sessions_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.routes"
)

router = APIRouter()
router.include_router(_orgs_routes.router)
router.include_router(_ws_routes.router)
router.include_router(_users_routes.router)
router.include_router(_memberships_routes.router)
router.include_router(_roles_routes.router)
router.include_router(_groups_routes.router)
router.include_router(_applications_routes.router)
router.include_router(_credentials_routes.router)
router.include_router(_sessions_routes.router)
router.include_router(_auth_routes.router)
