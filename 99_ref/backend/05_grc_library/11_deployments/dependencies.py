from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.11_deployments.service")
DeploymentService = _service_module.DeploymentService


def get_deployment_service(request: Request) -> DeploymentService:
    return DeploymentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
