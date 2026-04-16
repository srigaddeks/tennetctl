"""Job processor for library_builder jobs."""

from __future__ import annotations

from importlib import import_module


async def dispatch(job, pool, settings) -> None:
    _handler = import_module("backend.20_ai.26_library_builder.job_handler")
    await _handler.handle_library_builder_job(job=job, pool=pool, settings=settings)
