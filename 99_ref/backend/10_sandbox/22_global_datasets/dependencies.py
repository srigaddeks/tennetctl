from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.22_global_datasets.service")
GlobalDatasetService = _service_module.GlobalDatasetService


def get_global_dataset_service(request: Request) -> GlobalDatasetService:
    return GlobalDatasetService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
