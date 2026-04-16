from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.15_collection_runs.service")
CollectionRunService = _service_module.CollectionRunService


def get_collection_run_service(request: Request) -> CollectionRunService:
    return CollectionRunService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
