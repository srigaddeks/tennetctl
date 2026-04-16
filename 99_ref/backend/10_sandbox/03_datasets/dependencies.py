from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.03_datasets.service")
DatasetService = _service_module.DatasetService


def get_dataset_service(request: Request) -> DatasetService:
    return DatasetService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
