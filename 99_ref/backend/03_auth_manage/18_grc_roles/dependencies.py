"""FastAPI dependency injection for GRC role service."""
from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.18_grc_roles.service")
GrcRoleService = _service_module.GrcRoleService


def get_grc_role_service(request: Request) -> GrcRoleService:
    """Create GRC role service with app-level dependencies.

    Args:
        request: FastAPI request object.

    Returns:
        Configured GrcRoleService instance.
    """
    return GrcRoleService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
