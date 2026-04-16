"""Job processor for signal_codegen jobs."""

from __future__ import annotations

from importlib import import_module


async def dispatch(job, pool, settings) -> None:
    _handler = import_module("backend.20_ai.24_signal_codegen.job_handler")
    await _handler.handle_signal_codegen_job(job=job, pool=pool, settings=settings)
