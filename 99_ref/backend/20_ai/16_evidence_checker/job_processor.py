"""
Job processor bridge for the evidence_check job type.

The existing job queue worker (15_job_queue) will call dispatch(job, pool, settings)
for jobs with job_type='evidence_check'. This module is the single registration
point — add it to the job_queue worker's dispatch table.

Usage (in the job queue worker's dispatch handler):
    from backend.20_ai.16_evidence_checker.job_processor import dispatch as evidence_check_dispatch

    JOB_TYPE_HANDLERS = {
        ...existing...,
        "evidence_check": evidence_check_dispatch,
    }
"""

from __future__ import annotations

from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.evidence_checker.processor")


async def dispatch(job, pool, settings) -> None:
    """
    Dispatch entry point called by the job queue worker for job_type='evidence_check'.

    Delegates to handle_evidence_check_job() which runs the full:
      ingestion → evaluation → report write → SSE events flow.
    """
    from .job_handler import handle_evidence_check_job

    _logger.info(
        "evidence_check.processor_dispatch",
        extra={"job_id": job.id, "job_type": job.job_type},
    )
    await handle_evidence_check_job(job=job, pool=pool, settings=settings)
