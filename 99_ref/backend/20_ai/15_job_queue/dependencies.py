from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.20_ai.15_job_queue.service")
JobQueueService = _service_module.JobQueueService


def get_job_queue_service(request: Request) -> JobQueueService:
    return JobQueueService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
