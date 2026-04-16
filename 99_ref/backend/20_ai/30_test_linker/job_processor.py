from __future__ import annotations


async def dispatch(job, pool, settings) -> None:
    if job.job_type == "test_linker_bulk_link":
        from .job_handler import handle_bulk_link_job

        await handle_bulk_link_job(job=job, pool=pool, settings=settings)
    else:
        raise ValueError(f"test_linker: unknown job_type '{job.job_type}'")
