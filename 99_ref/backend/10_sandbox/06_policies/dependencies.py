from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.06_policies.service")
PolicyService = _service_module.PolicyService


def get_policy_service(request: Request) -> PolicyService:
    return PolicyService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
