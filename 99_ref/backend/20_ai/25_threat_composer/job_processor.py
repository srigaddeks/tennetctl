"""Job processor for threat_composer jobs."""

from __future__ import annotations

from importlib import import_module


async def dispatch(job, pool, settings) -> None:
    _handler = import_module("backend.20_ai.25_threat_composer.job_handler")
    await _handler.handle_threat_composer_job(job=job, pool=pool, settings=settings)
