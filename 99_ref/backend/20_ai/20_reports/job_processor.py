"""
Job processor bridge for the generate_report job type.

The job queue worker calls dispatch(job, pool, settings) for jobs
with job_type='generate_report'.
"""

from __future__ import annotations

from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.reports.processor")


async def dispatch(job, pool, settings) -> None:
    """Dispatch entry point called by the job queue worker."""
    from .job_handler import handle_generate_report_job

    _logger.info(
        "report.processor_dispatch",
        extra={"job_id": job.id, "job_type": job.job_type},
    )
    await handle_generate_report_job(job=job, pool=pool, settings=settings)
