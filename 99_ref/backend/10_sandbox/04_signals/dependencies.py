from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.04_signals.service")
SignalService = _service_module.SignalService


def get_signal_service(request: Request) -> SignalService:
    return SignalService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
