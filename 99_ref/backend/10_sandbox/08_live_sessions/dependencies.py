from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.08_live_sessions.service")
LiveSessionService = _service_module.LiveSessionService


def get_live_session_service(request: Request) -> LiveSessionService:
    return LiveSessionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
