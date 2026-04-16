"""
Job processor bridge for signal generation job type.
The job queue worker calls dispatch(job, pool, settings) for: signal_generate
"""
from __future__ import annotations

from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.10_sandbox.13_signal_agent.processor")


async def dispatch(job, pool, settings) -> None:
    """Dispatch entry point called by the job queue worker."""
    from .job_handler import handle_signal_generate_job

    _logger.info(
        "signal_gen.processor_dispatch",
        extra={"job_id": job.id, "job_type": job.job_type},
    )

    if job.job_type == "signal_generate":
        await handle_signal_generate_job(job=job, pool=pool, settings=settings)
    else:
        raise ValueError(f"signal_agent: unknown job_type '{job.job_type}'")
