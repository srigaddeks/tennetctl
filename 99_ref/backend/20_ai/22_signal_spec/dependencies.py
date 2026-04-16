"""FastAPI dependency injection for the Signal Spec module."""

from __future__ import annotations

from importlib import import_module

from fastapi import Request

_database_module = import_module("backend.01_core.database")
_svc_module = import_module("backend.20_ai.22_signal_spec.service")

DatabasePool = _database_module.DatabasePool
SignalSpecService = _svc_module.SignalSpecService


def get_signal_spec_service(request: Request) -> SignalSpecService:
    return SignalSpecService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )
