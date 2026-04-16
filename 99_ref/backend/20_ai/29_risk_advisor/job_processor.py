from __future__ import annotations


async def dispatch(job, pool, settings) -> None:
    if job.job_type == "risk_advisor_bulk_link":
        from .job_handler import handle_bulk_link_job
        await handle_bulk_link_job(job=job, pool=pool, settings=settings)
    else:
        raise ValueError(f"risk_advisor: unknown job_type '{job.job_type}'")
