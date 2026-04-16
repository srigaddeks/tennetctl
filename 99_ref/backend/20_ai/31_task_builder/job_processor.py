"""
Job processor bridge for task builder job types.

The job queue worker calls dispatch(job, pool, settings) for:
  - task_builder_preview  → Generate task suggestions (async)
  - task_builder_apply    → Create approved tasks in DB (async)
"""

from __future__ import annotations

from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.task_builder.processor")


async def dispatch(job, pool, settings) -> None:
    """Dispatch entry point called by the job queue worker."""
    from .job_handler import handle_apply_job, handle_preview_job

    _logger.info(
        "task_builder.processor_dispatch",
        extra={"job_id": job.id, "job_type": job.job_type},
    )

    if job.job_type == "task_builder_preview":
        await handle_preview_job(job=job, pool=pool, settings=settings)
    elif job.job_type == "task_builder_apply":
        await handle_apply_job(job=job, pool=pool, settings=settings)
    else:
        raise ValueError(f"task_builder: unknown job_type '{job.job_type}'")
