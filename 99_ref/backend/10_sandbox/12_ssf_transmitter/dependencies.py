from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.12_ssf_transmitter.service")
SSFTransmitterService = _service_module.SSFTransmitterService


def get_ssf_transmitter_service(request: Request) -> SSFTransmitterService:
    return SSFTransmitterService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
