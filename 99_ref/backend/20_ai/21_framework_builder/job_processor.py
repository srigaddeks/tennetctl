"""
Job processor bridge for framework builder job types.

The job queue worker calls dispatch(job, pool, settings) for:
  - framework_hierarchy      → Phase 1: generate requirement hierarchy (async)
  - framework_controls       → Phase 2: generate controls + risk mappings (async)
  - framework_build          → Phase 3: write approved proposal to DB
  - framework_apply_changes  → Enhance mode: apply accepted changes to DB
  - framework_gap_analysis   → Compute + store gap analysis report
  - framework_enhance_diff   → Enhance mode: stream diff proposals as background job
"""

from __future__ import annotations

from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.framework_builder.processor")


async def dispatch(job, pool, settings) -> None:
    """Dispatch entry point called by the job queue worker."""
    from .job_handler import (
        handle_apply_changes_job,
        handle_controls_job,
        handle_enhance_diff_job,
        handle_framework_build_job,
        handle_gap_analysis_job,
        handle_hierarchy_job,
    )

    _logger.info(
        "framework_builder.processor_dispatch",
        extra={"job_id": job.id, "job_type": job.job_type},
    )

    if job.job_type == "framework_hierarchy":
        await handle_hierarchy_job(job=job, pool=pool, settings=settings)
    elif job.job_type == "framework_controls":
        await handle_controls_job(job=job, pool=pool, settings=settings)
    elif job.job_type == "framework_build":
        await handle_framework_build_job(job=job, pool=pool, settings=settings)
    elif job.job_type == "framework_apply_changes":
        await handle_apply_changes_job(job=job, pool=pool, settings=settings)
    elif job.job_type == "framework_gap_analysis":
        await handle_gap_analysis_job(job=job, pool=pool, settings=settings)
    elif job.job_type == "framework_enhance_diff":
        await handle_enhance_diff_job(job=job, pool=pool, settings=settings)
    else:
        raise ValueError(f"framework_builder: unknown job_type '{job.job_type}'")
