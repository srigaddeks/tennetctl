"""
Background job queue worker.

Polls 45_fct_job_queue for queued jobs and dispatches them to the
appropriate handler. Uses per-type semaphores + a global semaphore so
heavy jobs (codegen, threat_composer) don't starve lighter ones.

Uses SELECT FOR UPDATE SKIP LOCKED to safely claim jobs in a
multi-replica deployment (HPA-safe).

Started via asyncio.create_task() in the app _lifespan (application.py).
Controlled by settings.ai_job_worker_enabled (default True).
"""

from __future__ import annotations

import asyncio
import json
from importlib import import_module

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.job_queue.worker")

_JOBS = '"20_ai"."45_fct_job_queue"'
_DEFAULT_POLL_INTERVAL_SECONDS = 5
_DEFAULT_GLOBAL_MAX_CONCURRENT = 5

# Default per-type concurrency limits (overridable via AI_JOB_TYPE_CONCURRENCY env var)
_DEFAULT_TYPE_CONCURRENCY: dict[str, int] = {
    "signal_test_dataset_gen": 2,
    "signal_codegen": 2,
    "signal_generate": 2,
    "threat_composer": 1,
    "library_builder": 1,
    "evidence_check": 2,
    "generate_report": 2,
    "framework_build": 1,
    "framework_apply_changes": 1,
    "framework_gap_analysis": 1,
    "framework_hierarchy": 1,
    "framework_controls": 1,
    "framework_enhance_diff": 1,
    "risk_advisor_bulk_link": 1,
    "test_linker_bulk_link": 1,
    "task_builder_preview": 2,
    "task_builder_apply": 1,
}

_ALL_JOB_TYPES = list(_DEFAULT_TYPE_CONCURRENCY.keys())


async def _claim_next_job(conn: asyncpg.Connection, eligible_types: list[str]) -> dict | None:
    """Atomically claim the next queued job whose type has capacity. Returns None if empty."""
    if not eligible_types:
        return None
    row = await conn.fetchrow(
        f"""
        UPDATE {_JOBS}
        SET status_code = 'running', started_at = NOW(), updated_at = NOW()
        WHERE id = (
            SELECT id FROM {_JOBS}
            WHERE status_code = 'queued'
              AND job_type = ANY($1::text[])
              AND scheduled_at <= NOW()
            ORDER BY
              CASE priority_code WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
              created_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id::text, tenant_key, user_id::text, org_id::text,
                  workspace_id::text, agent_type_code, priority_code, status_code,
                  job_type, input_json, output_json, error_message,
                  scheduled_at::text, started_at::text, completed_at::text,
                  estimated_tokens, actual_tokens, max_retries, retry_count,
                  next_retry_at::text, conversation_id::text, agent_run_id::text,
                  batch_id::text, created_at::text, updated_at::text
        """,
        eligible_types,
    )
    return dict(row) if row else None


async def _mark_job_failed(conn: asyncpg.Connection, job_id: str, error: str) -> None:
    await conn.execute(
        f"""
        UPDATE {_JOBS}
        SET status_code = 'failed', error_message = $2,
            completed_at = NOW(), updated_at = NOW()
        WHERE id = $1
        """,
        job_id, error[:2000],
    )


async def _mark_job_completed(conn: asyncpg.Connection, job_id: str) -> None:
    await conn.execute(
        f"""
        UPDATE {_JOBS}
        SET status_code = 'completed',
            error_message = NULL,
            completed_at = NOW(),
            updated_at = NOW()
        WHERE id = $1
        """,
        job_id,
    )


class _FakeJobRecord:
    """Minimal duck-type for job.id / job.job_type / job.input_json."""

    def __init__(self, row: dict) -> None:
        self.id = row["id"]
        self.job_type = row["job_type"]
        self.tenant_key = row.get("tenant_key", "")
        self.org_id = row.get("org_id")
        self.workspace_id = row.get("workspace_id")
        self.user_id = row.get("user_id")
        raw = row.get("input_json", {})
        self.input_json = raw if isinstance(raw, dict) else json.loads(raw)
        self.agent_type_code = row.get("agent_type_code", "")
        self.retry_count = row.get("retry_count", 0)
        self.max_retries = row.get("max_retries", 2)


async def _process_one(job_row: dict, pool: asyncpg.Pool, settings) -> None:
    """Run a single job, updating the outer job row on completion/failure."""
    job = _FakeJobRecord(job_row)
    _logger.info(
        "job_worker.processing",
        extra={"job_id": job.id, "job_type": job.job_type},
    )

    # Root LangFuse trace for the entire job lifecycle
    _tracer_mod = import_module("backend.20_ai.14_llm_providers.langfuse_tracer")
    tracer = _tracer_mod.LangFuseTracer.from_settings(settings)
    root_trace = tracer.trace(
        name=f"job.{job.job_type}",
        job_id=job.id,
        user_id=str(job.user_id) if job.user_id else None,
        metadata={
            "job_type": job.job_type,
            "org_id": str(job.org_id) if job.org_id else None,
            "workspace_id": str(job.workspace_id) if job.workspace_id else None,
            "tenant_key": job.tenant_key,
            "retry_count": job.retry_count,
        },
        tags=["job_queue", job.job_type],
    )

    try:
        if job.job_type == "evidence_check":
            _proc = import_module("backend.20_ai.16_evidence_checker.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type == "generate_report":
            _proc = import_module("backend.20_ai.20_reports.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type in ("framework_build", "framework_apply_changes", "framework_gap_analysis",
                                "framework_hierarchy", "framework_controls", "framework_enhance_diff"):
            _proc = import_module("backend.20_ai.21_framework_builder.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type == "signal_generate":
            _proc = import_module("backend.10_sandbox.13_signal_agent.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type == "signal_test_dataset_gen":
            _proc = import_module("backend.20_ai.23_test_dataset_gen.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type == "signal_codegen":
            _proc = import_module("backend.20_ai.24_signal_codegen.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type == "threat_composer":
            _proc = import_module("backend.20_ai.25_threat_composer.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type == "library_builder":
            _proc = import_module("backend.20_ai.26_library_builder.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type == "risk_advisor_bulk_link":
            _proc = import_module("backend.20_ai.29_risk_advisor.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type == "test_linker_bulk_link":
            _proc = import_module("backend.20_ai.30_test_linker.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        elif job.job_type in ("task_builder_preview", "task_builder_apply"):
            _proc = import_module("backend.20_ai.31_task_builder.job_processor")
            await _proc.dispatch(job=job, pool=pool, settings=settings)
        else:
            raise ValueError(f"Unknown job_type: {job.job_type}")

        async with pool.acquire() as conn:
            await _mark_job_completed(conn, job.id)
        tracer.event(root_trace, name="job_completed",
                     metadata={"job_type": job.job_type, "job_id": job.id})
        tracer.flush()
        _logger.info("job_worker.completed", extra={"job_id": job.id})

    except Exception as exc:
        _logger.exception("job_worker.failed: %s", exc)
        tracer.event(root_trace, name="job_failed", level="ERROR",
                     metadata={"error": str(exc)[:500], "job_type": job.job_type})
        tracer.flush()
        async with pool.acquire() as conn:
            await _mark_job_failed(conn, job.id, str(exc))


class JobQueueWorker:
    """Polls the job queue and dispatches jobs with per-type + global concurrency limits."""

    def __init__(self, *, pool, settings) -> None:
        # Accept either a raw asyncpg.Pool or the DatabasePool wrapper.
        # Job handlers expect a raw asyncpg.Pool (acquire() → PoolAcquireContext),
        # so unwrap the DatabasePool wrapper if needed.
        self._pool = getattr(pool, "pool", pool)
        self._settings = settings
        self._poll_interval = getattr(settings, "ai_job_worker_poll_interval_seconds", _DEFAULT_POLL_INTERVAL_SECONDS)

        # Build per-type semaphores from settings or defaults
        type_concurrency = _DEFAULT_TYPE_CONCURRENCY.copy()
        raw_override = getattr(settings, "ai_job_type_concurrency", "") or ""
        if raw_override.strip():
            try:
                overrides = json.loads(raw_override)
                type_concurrency.update(overrides)
            except Exception:
                _logger.warning("job_queue_worker.invalid_type_concurrency: %s", raw_override[:200])

        self._type_sems: dict[str, asyncio.Semaphore] = {
            job_type: asyncio.Semaphore(limit)
            for job_type, limit in type_concurrency.items()
        }

        global_max = getattr(settings, "ai_job_global_max_concurrent", _DEFAULT_GLOBAL_MAX_CONCURRENT)
        self._global_sem = asyncio.Semaphore(global_max)
        self._global_max = global_max

        _logger.info(
            "job_queue_worker.init",
            extra={"global_max": global_max, "type_limits": {k: v._value for k, v in self._type_sems.items()}},
        )

    def _eligible_types(self) -> list[str]:
        """Return job types whose per-type semaphore still has capacity."""
        return [jt for jt, sem in self._type_sems.items() if sem._value > 0]

    async def recover_stuck_jobs(self) -> None:
        """Reset jobs stuck in 'running' state from a previous server crash/reload.
        Also permanently fails any job that has been queued or running for over 5 hours."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                UPDATE {_JOBS}
                SET status_code = 'queued', started_at = NULL, updated_at = NOW()
                WHERE status_code = 'running'
                  AND updated_at < NOW() - INTERVAL '2 minutes'
                RETURNING id
                """
            )
            if rows:
                _logger.warning("job_queue_worker.recovered_stuck_jobs", extra={"count": len(rows)})

            # Hard-fail jobs stuck for > 5 hours (queued or running) — covers LLM hangs
            timed_out = await conn.fetch(
                f"""
                UPDATE {_JOBS}
                SET status_code = 'failed',
                    error_message = 'Job timeout: exceeded 5 hour limit',
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE status_code IN ('queued', 'running')
                  AND created_at < NOW() - INTERVAL '5 hours'
                RETURNING id
                """
            )
            if timed_out:
                timed_out_ids = [r["id"] for r in timed_out]
                _logger.warning(
                    "job_queue_worker.timed_out_jobs",
                    extra={"count": len(timed_out_ids), "job_ids": [str(i) for i in timed_out_ids]},
                )
                # Also mark the associated builder sessions as failed
                await conn.execute(
                    """
                    UPDATE "20_ai"."60_fct_builder_sessions"
                    SET status = 'failed',
                        error_message = 'Build job timed out after 5 hours. Please retry.',
                        updated_at = NOW()
                    WHERE job_id = ANY($1::uuid[])
                      AND status NOT IN ('complete', 'failed')
                    """,
                    timed_out_ids,
                )

            await conn.execute(
                """
                UPDATE "20_ai"."50_fct_reports"
                SET status_code = 'queued', error_message = NULL,
                    content_markdown = NULL, word_count = NULL, token_count = NULL,
                    updated_at = NOW()
                WHERE status_code IN ('collecting', 'analyzing', 'writing', 'formatting')
                  AND updated_at < NOW() - INTERVAL '2 minutes'
                """
            )

    async def run_loop(self) -> None:
        _logger.info(
            "job_queue_worker.started",
            extra={"poll_interval_s": self._poll_interval, "global_max": self._global_max},
        )
        ticks = 0
        while True:
            try:
                await self._tick()
                ticks += 1
                # Periodically recover stuck jobs (every ~2 minutes = 24 ticks at 5s poll)
                if ticks % 24 == 0:
                    await self.recover_stuck_jobs()
            except asyncio.CancelledError:
                _logger.info("job_queue_worker.stopped")
                return
            except Exception as exc:
                _logger.warning("job_queue_worker.tick_error: %s", exc)
            await asyncio.sleep(self._poll_interval)

    async def _tick(self) -> None:
        """Claim and dispatch up to global_max jobs per tick, respecting per-type limits."""
        if self._global_sem._value <= 0:
            return
        eligible = self._eligible_types()
        if not eligible:
            return
        for _ in range(self._global_max):
            if self._global_sem._value <= 0:
                break
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    job_row = await _claim_next_job(conn, eligible)
            if not job_row:
                break  # Queue empty for eligible types — stop polling
            task = asyncio.create_task(self._run_with_sems(job_row))
            task.add_done_callback(
                lambda t: _logger.error(
                    "job_worker.task_exception: %s", t.exception()
                ) if not t.cancelled() and t.exception() else None
            )
            # Recalculate eligible only if a type-specific sem may have changed
            eligible = self._eligible_types()
            if not eligible:
                break

    async def _run_with_sems(self, job_row: dict) -> None:
        job_id = job_row.get("id", "?")
        job_type = job_row.get("job_type", "")
        _logger.info("job_worker.task_started", extra={"job_id": job_id, "job_type": job_type})
        type_sem = self._type_sems.get(job_type, self._global_sem)
        _logger.info("job_worker.acquiring_sems", extra={"job_id": job_id, "global_sem_value": self._global_sem._value})
        async with self._global_sem:
            async with type_sem:
                await _process_one(job_row, self._pool, self._settings)
