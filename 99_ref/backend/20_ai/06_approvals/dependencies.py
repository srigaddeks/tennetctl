from __future__ import annotations
from importlib import import_module
from fastapi import Request
_service_module = import_module("backend.20_ai.06_approvals.service")
ApprovalService = _service_module.ApprovalService

def get_approval_service(request: Request) -> ApprovalService:
    return ApprovalService(settings=request.app.state.settings,
        database_pool=request.app.state.database_pool, cache=request.app.state.cache)
