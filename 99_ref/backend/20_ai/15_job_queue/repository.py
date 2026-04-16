from __future__ import annotations

import asyncpg
from .models import JobRecord, BatchRecord, RateLimitConfig


class JobQueueRepository:
    _SCHEMA = '"20_ai"'
    _JOBS = f'{_SCHEMA}."45_fct_job_queue"'
    _BATCHES = f'{_SCHEMA}."47_fct_job_batches"'
    _RATE_LIMITS = f'{_SCHEMA}."44_fct_agent_rate_limits"'
    _RATE_WINDOWS = f'{_SCHEMA}."46_trx_rate_limit_windows"'
    _VW_QUEUE_DEPTH = f'{_SCHEMA}."65_vw_queue_depth"'
    _VW_RATE_STATUS = f'{_SCHEMA}."66_vw_rate_limit_status"'
    _VW_USER_QUEUE = f'{_SCHEMA}."67_vw_user_job_queue"'
    _VW_BATCH_PROGRESS = f'{_SCHEMA}."68_vw_batch_progress"'
    _VW_PROCESSING = f'{_SCHEMA}."69_vw_queue_processing_order"'

    async def enqueue_job(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str,
        org_id: str | None,
        workspace_id: str | None,
        agent_type_code: str,
        priority_code: str,
        job_type: str,
        input_json: dict,
        estimated_tokens: int,
        scheduled_at: str | None,
        max_retries: int,
        conversation_id: str | None,
        batch_id: str | None,
    ) -> JobRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {self._JOBS}
                (tenant_key, user_id, org_id, workspace_id, agent_type_code,
                 priority_code, job_type, input_json, estimated_tokens,
                 scheduled_at, max_retries, conversation_id, batch_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9,
                    COALESCE($10::TIMESTAMPTZ, NOW()), $11, $12, $13)
            RETURNING id::text, tenant_key, user_id::text, org_id::text,
                      workspace_id::text, agent_type_code, priority_code, status_code,
                      job_type, input_json, output_json, error_message,
                      scheduled_at::text, started_at::text, completed_at::text,
                      estimated_tokens, actual_tokens, max_retries, retry_count,
                      next_retry_at::text, conversation_id::text, agent_run_id::text,
                      batch_id::text, created_at::text, updated_at::text
            """,
            tenant_key, user_id, org_id, workspace_id, agent_type_code,
            priority_code, job_type, input_json, estimated_tokens,
            scheduled_at, max_retries, conversation_id, batch_id,
        )
        return JobRecord(**dict(row))

    async def get_job(
        self,
        connection: asyncpg.Connection,
        *,
        job_id: str,
        tenant_key: str,
    ) -> JobRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, user_id::text, org_id::text,
                   workspace_id::text, agent_type_code, priority_code, status_code,
                   job_type, input_json, output_json, error_message,
                   scheduled_at::text, started_at::text, completed_at::text,
                   estimated_tokens, actual_tokens, max_retries, retry_count,
                   next_retry_at::text, conversation_id::text, agent_run_id::text,
                   batch_id::text, created_at::text, updated_at::text
            FROM {self._JOBS}
            WHERE id = $1 AND tenant_key = $2
            """,
            job_id, tenant_key,
        )
        return JobRecord(**dict(row)) if row else None

    async def list_jobs(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str | None = None,
        agent_type_code: str | None = None,
        status_code: str | None = None,
        batch_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobRecord]:
        conditions = ["tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2
        if user_id:
            conditions.append(f"user_id = ${idx}"); params.append(user_id); idx += 1
        if agent_type_code:
            conditions.append(f"agent_type_code = ${idx}"); params.append(agent_type_code); idx += 1
        if status_code:
            conditions.append(f"status_code = ${idx}"); params.append(status_code); idx += 1
        if batch_id:
            conditions.append(f"batch_id = ${idx}"); params.append(batch_id); idx += 1
        params.extend([limit, offset])
        rows = await connection.fetch(
            f"""
            SELECT id::text, tenant_key, user_id::text, org_id::text,
                   workspace_id::text, agent_type_code, priority_code, status_code,
                   job_type, input_json, output_json, error_message,
                   scheduled_at::text, started_at::text, completed_at::text,
                   estimated_tokens, actual_tokens, max_retries, retry_count,
                   next_retry_at::text, conversation_id::text, agent_run_id::text,
                   batch_id::text, created_at::text, updated_at::text
            FROM {self._JOBS}
            WHERE {" AND ".join(conditions)}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params,
        )
        return [JobRecord(**dict(r)) for r in rows]

    async def update_job_status(
        self,
        connection: asyncpg.Connection,
        *,
        job_id: str,
        status_code: str,
        output_json: dict | None = None,
        error_message: str | None = None,
        actual_tokens: int | None = None,
        agent_run_id: str | None = None,
        next_retry_at: str | None = None,
    ) -> None:
        sets = ["status_code = $2", "updated_at = NOW()"]
        params: list = [job_id, status_code]
        idx = 3
        if status_code == "running":
            sets.append("started_at = NOW()")
        if status_code in ("completed", "failed", "cancelled"):
            sets.append("completed_at = NOW()")
        if output_json is not None:
            sets.append(f"output_json = ${idx}"); params.append(output_json); idx += 1
        if error_message is not None:
            sets.append(f"error_message = ${idx}"); params.append(error_message); idx += 1
        if actual_tokens is not None:
            sets.append(f"actual_tokens = ${idx}"); params.append(actual_tokens); idx += 1
        if agent_run_id is not None:
            sets.append(f"agent_run_id = ${idx}"); params.append(agent_run_id); idx += 1
        if next_retry_at is not None:
            sets.append(f"retry_count = retry_count + 1")
            sets.append(f"next_retry_at = ${idx}"); params.append(next_retry_at); idx += 1
        await connection.execute(
            f"UPDATE {self._JOBS} SET {', '.join(sets)} WHERE id = $1",
            *params,
        )

    async def cancel_job(self, connection: asyncpg.Connection, *, job_id: str, tenant_key: str) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {self._JOBS}
            SET status_code = 'cancelled', updated_at = NOW(), completed_at = NOW()
            WHERE id = $1 AND tenant_key = $2
              AND status_code IN ('queued', 'rate_limited', 'retrying')
            """,
            job_id, tenant_key,
        )
        return result == "UPDATE 1"

    async def create_batch(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str,
        org_id: str | None,
        agent_type_code: str,
        name: str | None,
        description: str | None,
        total_jobs: int,
        estimated_tokens: int,
        scheduled_at: str | None,
    ) -> BatchRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {self._BATCHES}
                (tenant_key, user_id, org_id, agent_type_code, name, description,
                 total_jobs, estimated_tokens, scheduled_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, COALESCE($9::TIMESTAMPTZ, NOW()))
            RETURNING id::text, tenant_key, user_id::text, org_id::text,
                      agent_type_code, name, description, total_jobs, completed_jobs,
                      failed_jobs, estimated_tokens, actual_tokens, status_code,
                      scheduled_at::text, started_at::text, completed_at::text,
                      created_at::text, updated_at::text
            """,
            tenant_key, user_id, org_id, agent_type_code, name, description,
            total_jobs, estimated_tokens, scheduled_at,
        )
        return BatchRecord(**dict(row))

    async def get_batch_progress(
        self,
        connection: asyncpg.Connection,
        *,
        batch_id: str,
        tenant_key: str,
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, user_id::text, org_id::text,
                   agent_type_code, agent_type_name, name, description,
                   total_jobs, completed_jobs, failed_jobs, pending_jobs,
                   estimated_tokens, actual_tokens, status_code,
                   scheduled_at::text, started_at::text, completed_at::text,
                   created_at::text, completion_pct::float, elapsed_seconds
            FROM {self._VW_BATCH_PROGRESS}
            WHERE id = $1 AND tenant_key = $2
            """,
            batch_id, tenant_key,
        )
        return dict(row) if row else None

    async def update_batch_progress(self, connection: asyncpg.Connection, *, batch_id: str) -> None:
        """Recalculate batch counters from job statuses."""
        await connection.execute(
            f"""
            UPDATE {self._BATCHES} b
            SET
                completed_jobs = (SELECT COUNT(*) FROM {self._JOBS} WHERE batch_id = b.id AND status_code = 'completed'),
                failed_jobs    = (SELECT COUNT(*) FROM {self._JOBS} WHERE batch_id = b.id AND status_code = 'failed'),
                actual_tokens  = COALESCE((SELECT SUM(actual_tokens) FROM {self._JOBS} WHERE batch_id = b.id), 0),
                status_code    = CASE
                    WHEN (SELECT COUNT(*) FROM {self._JOBS} WHERE batch_id = b.id AND status_code NOT IN ('completed','failed','cancelled')) = 0
                         THEN 'completed'
                    WHEN (SELECT COUNT(*) FROM {self._JOBS} WHERE batch_id = b.id AND status_code = 'running') > 0
                         THEN 'running'
                    ELSE status_code
                END,
                started_at  = COALESCE(started_at, CASE
                    WHEN (SELECT COUNT(*) FROM {self._JOBS} WHERE batch_id = b.id AND status_code IN ('running','completed','failed')) > 0
                    THEN NOW() END),
                completed_at = CASE
                    WHEN (SELECT COUNT(*) FROM {self._JOBS} WHERE batch_id = b.id AND status_code NOT IN ('completed','failed','cancelled')) = 0
                    THEN NOW() END,
                updated_at = NOW()
            WHERE id = $1
            """,
            batch_id,
        )

    async def get_rate_limit_config(
        self,
        connection: asyncpg.Connection,
        *,
        agent_type_code: str,
        org_id: str | None = None,
    ) -> RateLimitConfig | None:
        row = await connection.fetchrow(
            f"""
            SELECT agent_type_code, max_requests_per_minute, max_tokens_per_minute,
                   max_concurrent_jobs, batch_size, batch_interval_seconds, cooldown_seconds
            FROM {self._RATE_LIMITS}
            WHERE agent_type_code = $1
              AND COALESCE(org_id::text, '') = $2
              AND is_active = TRUE
            """,
            agent_type_code, org_id or "",
        )
        if not row:
            # Fall back to global
            row = await connection.fetchrow(
                f"""
                SELECT agent_type_code, max_requests_per_minute, max_tokens_per_minute,
                       max_concurrent_jobs, batch_size, batch_interval_seconds, cooldown_seconds
                FROM {self._RATE_LIMITS}
                WHERE agent_type_code = $1 AND org_id IS NULL AND is_active = TRUE
                """,
                agent_type_code,
            )
        return RateLimitConfig(**dict(row)) if row else None

    async def get_queue_depth(self, connection: asyncpg.Connection, *, tenant_key: str) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT agent_type_code, agent_type_name, tenant_key, status_code, status_name,
                   priority_code, job_count::int, estimated_tokens::bigint,
                   oldest_job_at::text, newest_job_at::text
            FROM {self._VW_QUEUE_DEPTH}
            WHERE tenant_key = $1
            ORDER BY agent_type_code, status_code, priority_code
            """,
            tenant_key,
        )
        return [dict(r) for r in rows]

    async def get_rate_limit_status(
        self, connection: asyncpg.Connection, *, tenant_key: str
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT tenant_key, org_id::text, agent_type_code, agent_type_name,
                   window_start::text, requests_count::int, tokens_count::bigint,
                   max_requests_per_minute::int, max_tokens_per_minute::bigint,
                   max_concurrent_jobs::int,
                   request_utilization_pct::float, token_utilization_pct::float,
                   is_at_limit
            FROM {self._VW_RATE_STATUS}
            WHERE tenant_key = $1
            ORDER BY agent_type_code, window_start DESC
            """,
            tenant_key,
        )
        return [dict(r) for r in rows]

    async def increment_rate_window(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None,
        agent_type_code: str,
        tokens: int,
    ) -> None:
        """Upsert rate limit sliding window — increment request + token counts for current minute."""
        await connection.execute(
            f"""
            INSERT INTO {self._RATE_WINDOWS}
                (tenant_key, org_id, agent_type_code, window_start, requests_count, tokens_count)
            VALUES ($1, $2, $3, DATE_TRUNC('minute', NOW()), 1, $4)
            ON CONFLICT (tenant_key, COALESCE(org_id::text,''), agent_type_code, window_start)
            DO UPDATE SET
                requests_count = {self._RATE_WINDOWS}.requests_count + 1,
                tokens_count   = {self._RATE_WINDOWS}.tokens_count + EXCLUDED.tokens_count,
                updated_at     = NOW()
            """,
            tenant_key, org_id, agent_type_code, tokens,
        )

    async def update_rate_limit_config(
        self,
        connection: asyncpg.Connection,
        *,
        agent_type_code: str,
        org_id: str | None,
        tenant_key: str,
        max_requests_per_minute: int | None,
        max_tokens_per_minute: int | None,
        max_concurrent_jobs: int | None,
        batch_size: int | None,
        batch_interval_seconds: int | None,
        cooldown_seconds: int | None,
    ) -> None:
        sets = ["updated_at = NOW()"]
        params: list = []
        idx = 1
        if max_requests_per_minute is not None:
            sets.append(f"max_requests_per_minute = ${idx}"); params.append(max_requests_per_minute); idx += 1
        if max_tokens_per_minute is not None:
            sets.append(f"max_tokens_per_minute = ${idx}"); params.append(max_tokens_per_minute); idx += 1
        if max_concurrent_jobs is not None:
            sets.append(f"max_concurrent_jobs = ${idx}"); params.append(max_concurrent_jobs); idx += 1
        if batch_size is not None:
            sets.append(f"batch_size = ${idx}"); params.append(batch_size); idx += 1
        if batch_interval_seconds is not None:
            sets.append(f"batch_interval_seconds = ${idx}"); params.append(batch_interval_seconds); idx += 1
        if cooldown_seconds is not None:
            sets.append(f"cooldown_seconds = ${idx}"); params.append(cooldown_seconds); idx += 1
        params.extend([agent_type_code, org_id or ""])
        await connection.execute(
            f"""
            UPDATE {self._RATE_LIMITS}
            SET {', '.join(sets)}
            WHERE agent_type_code = ${idx} AND COALESCE(org_id::text, '') = ${idx + 1}
            """,
            *params,
        )
