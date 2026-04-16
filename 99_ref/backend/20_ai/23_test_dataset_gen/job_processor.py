"""Job processor for signal_test_dataset_gen jobs."""

from __future__ import annotations

from importlib import import_module


async def dispatch(job, pool, settings) -> None:
    _handler = import_module("backend.20_ai.23_test_dataset_gen.job_handler")
    await _handler.handle_test_dataset_gen_job(job=job, pool=pool, settings=settings)
