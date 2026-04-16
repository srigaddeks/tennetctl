from __future__ import annotations

import uuid
import datetime
from importlib import import_module

from .models import JobRecord, BatchRecord
from .repository import JobQueueRepository
from .schemas import (
    BatchResponse,
    CreateBatchRequest,
    EnqueueJobRequest,
    JobListResponse,
    JobResponse,
    QueueDepthResponse,
    RateLimitStatusResponse,
    UpdateRateLimitRequest,
)

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_constants_module = import_module("backend.20_ai.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ForbiddenError = _errors_module.AuthorizationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AIAuditEventType = _constants_module.AIAuditEventType
require_permission = _perm_check_module.require_permission


def _job_to_response(r: JobRecord) -> JobResponse:
    return JobResponse(
        id=r.id, tenant_key=r.tenant_key, user_id=r.user_id, org_id=r.org_id,
        agent_type_code=r.agent_type_code, priority_code=r.priority_code,
        status_code=r.status_code, job_type=r.job_type, input_json=r.input_json,
        output_json=r.output_json, error_message=r.error_message,
        scheduled_at=r.scheduled_at, started_at=r.started_at, completed_at=r.completed_at,
        estimated_tokens=r.estimated_tokens, actual_tokens=r.actual_tokens,
        retry_count=r.retry_count, max_retries=r.max_retries,
        batch_id=r.batch_id, conversation_id=r.conversation_id,
        created_at=r.created_at, updated_at=r.updated_at,
    )


@instrument_class_methods(
    namespace="ai.job_queue.service",
    logger_name="backend.ai.job_queue.instrumentation",
)
class JobQueueService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = JobQueueRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.job_queue")

    async def enqueue_job(
        self,
        *,
        caller_id: str,
        tenant_key: str,
        org_id: str | None,
        workspace_id: str | None,
        request: EnqueueJobRequest,
    ) -> JobResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.execute")
            record = await self._repository.enqueue_job(
                conn,
                tenant_key=tenant_key, user_id=caller_id,
                org_id=org_id, workspace_id=workspace_id,
                agent_type_code=request.agent_type_code,
                priority_code=request.priority_code,
                job_type=request.job_type, input_json=request.input_json,
                estimated_tokens=request.estimated_tokens,
                scheduled_at=request.scheduled_at,
                max_retries=request.max_retries,
                conversation_id=request.conversation_id,
                batch_id=request.batch_id,
            )
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()), tenant_key=tenant_key,
                entity_type="job", entity_id=record.id,
                event_type=AIAuditEventType.JOB_QUEUED, event_category="ai",
                actor_id=caller_id, actor_type="user",
                properties={"agent_type_code": request.agent_type_code, "job_type": request.job_type},
                occurred_at=datetime.datetime.utcnow(),
            ))
        return _job_to_response(record)

    async def create_batch(
        self,
        *,
        caller_id: str,
        tenant_key: str,
        org_id: str | None,
        workspace_id: str | None,
        request: CreateBatchRequest,
    ) -> tuple[BatchResponse, list[JobResponse]]:
        """Create a batch and enqueue all its jobs atomically."""
        total_estimated = sum(j.estimated_tokens for j in request.jobs)

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.execute")
            async with conn.transaction():
                batch = await self._repository.create_batch(
                    conn, tenant_key=tenant_key, user_id=caller_id,
                    org_id=org_id, agent_type_code=request.agent_type_code,
                    name=request.name, description=request.description,
                    total_jobs=len(request.jobs), estimated_tokens=total_estimated,
                    scheduled_at=request.scheduled_at,
                )
                jobs: list[JobResponse] = []
                for job_req in request.jobs:
                    job_req_with_batch = job_req.model_copy(update={"batch_id": batch.id})
                    record = await self._repository.enqueue_job(
                        conn, tenant_key=tenant_key, user_id=caller_id,
                        org_id=org_id, workspace_id=workspace_id,
                        agent_type_code=request.agent_type_code,
                        priority_code=job_req.priority_code,
                        job_type=job_req.job_type, input_json=job_req.input_json,
                        estimated_tokens=job_req.estimated_tokens,
                        scheduled_at=request.scheduled_at,
                        max_retries=job_req.max_retries,
                        conversation_id=job_req.conversation_id,
                        batch_id=batch.id,
                    )
                    jobs.append(_job_to_response(record))
                await self._audit_writer.write_entry(conn, AuditEntry(
                    id=str(uuid.uuid4()), tenant_key=tenant_key,
                    entity_type="batch", entity_id=batch.id,
                    event_type=AIAuditEventType.BATCH_CREATED, event_category="ai",
                    actor_id=caller_id, actor_type="user",
                    properties={"agent_type_code": request.agent_type_code, "total_jobs": str(len(request.jobs))},
                    occurred_at=datetime.datetime.utcnow(),
                ))

        batch_resp = BatchResponse(
            id=batch.id, tenant_key=batch.tenant_key, user_id=batch.user_id,
            agent_type_code=batch.agent_type_code, name=batch.name,
            description=batch.description, total_jobs=batch.total_jobs,
            completed_jobs=batch.completed_jobs, failed_jobs=batch.failed_jobs,
            pending_jobs=batch.total_jobs,
            estimated_tokens=batch.estimated_tokens, actual_tokens=batch.actual_tokens,
            status_code=batch.status_code, scheduled_at=batch.scheduled_at,
            started_at=batch.started_at, completed_at=batch.completed_at,
            completion_pct=0.0, created_at=batch.created_at,
        )
        return batch_resp, jobs

    async def get_job(self, *, job_id: str, tenant_key: str, caller_id: str) -> JobResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_job(conn, job_id=job_id, tenant_key=tenant_key)
        if not record:
            raise NotFoundError(f"Job {job_id} not found")
        if record.user_id != caller_id:
            async with self._database_pool.acquire() as conn:
                await require_permission(conn, caller_id, "ai_copilot.admin")
        return _job_to_response(record)

    async def list_jobs(
        self,
        *,
        caller_id: str,
        tenant_key: str,
        user_id: str | None = None,
        agent_type_code: str | None = None,
        status_code: str | None = None,
        batch_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> JobListResponse:
        # Admin can filter across users; regular user sees only their own
        target_user = user_id
        async with self._database_pool.acquire() as conn:
            if user_id and user_id != caller_id:
                await require_permission(conn, caller_id, "ai_copilot.admin")
                target_user = user_id
            records = await self._repository.list_jobs(
                conn, tenant_key=tenant_key, user_id=target_user,
                agent_type_code=agent_type_code, status_code=status_code,
                batch_id=batch_id, limit=limit, offset=offset,
            )
        return JobListResponse(items=[_job_to_response(r) for r in records], total=len(records))

    async def cancel_job(self, *, job_id: str, tenant_key: str, caller_id: str) -> None:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_job(conn, job_id=job_id, tenant_key=tenant_key)
            if not record:
                raise NotFoundError(f"Job {job_id} not found")
            if record.user_id != caller_id:
                await require_permission(conn, caller_id, "ai_copilot.admin")
            cancelled = await self._repository.cancel_job(conn, job_id=job_id, tenant_key=tenant_key)
            if cancelled:
                await self._audit_writer.write_entry(conn, AuditEntry(
                    id=str(uuid.uuid4()), tenant_key=tenant_key,
                    entity_type="job", entity_id=job_id,
                    event_type=AIAuditEventType.JOB_CANCELLED, event_category="ai",
                    actor_id=caller_id, actor_type="user",
                    properties={"agent_type_code": record.agent_type_code},
                    occurred_at=datetime.datetime.utcnow(),
                ))

    async def get_batch_progress(
        self, *, batch_id: str, tenant_key: str, caller_id: str
    ) -> BatchResponse:
        async with self._database_pool.acquire() as conn:
            data = await self._repository.get_batch_progress(conn, batch_id=batch_id, tenant_key=tenant_key)
        if not data:
            raise NotFoundError(f"Batch {batch_id} not found")
        if data.get("user_id") != caller_id:
            async with self._database_pool.acquire() as conn:
                await require_permission(conn, caller_id, "ai_copilot.admin")
        return BatchResponse(
            id=data["id"], tenant_key=data["tenant_key"], user_id=data["user_id"],
            agent_type_code=data["agent_type_code"], name=data.get("name"),
            description=data.get("description"),
            total_jobs=data["total_jobs"], completed_jobs=data["completed_jobs"],
            failed_jobs=data["failed_jobs"], pending_jobs=data.get("pending_jobs", 0),
            estimated_tokens=data["estimated_tokens"], actual_tokens=data["actual_tokens"],
            status_code=data["status_code"], scheduled_at=data["scheduled_at"],
            started_at=data.get("started_at"), completed_at=data.get("completed_at"),
            completion_pct=data.get("completion_pct", 0.0),
            created_at=data["created_at"],
        )

    async def get_queue_depth(
        self, *, caller_id: str, tenant_key: str
    ) -> list[QueueDepthResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.admin")
            rows = await self._repository.get_queue_depth(conn, tenant_key=tenant_key)
        return [QueueDepthResponse(
            agent_type_code=r["agent_type_code"],
            agent_type_name=r.get("agent_type_name"),
            status_code=r["status_code"],
            priority_code=r["priority_code"],
            job_count=r["job_count"],
            estimated_tokens=r["estimated_tokens"],
            oldest_job_at=r.get("oldest_job_at"),
        ) for r in rows]

    async def get_rate_limit_status(
        self, *, caller_id: str, tenant_key: str
    ) -> list[RateLimitStatusResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.admin")
            rows = await self._repository.get_rate_limit_status(conn, tenant_key=tenant_key)
        return [RateLimitStatusResponse(**r) for r in rows]

    async def update_rate_limit(
        self,
        *,
        caller_id: str,
        tenant_key: str,
        agent_type_code: str,
        org_id: str | None,
        request: UpdateRateLimitRequest,
    ) -> None:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.admin")
            await self._repository.update_rate_limit_config(
                conn, agent_type_code=agent_type_code, org_id=org_id,
                tenant_key=tenant_key,
                max_requests_per_minute=request.max_requests_per_minute,
                max_tokens_per_minute=request.max_tokens_per_minute,
                max_concurrent_jobs=request.max_concurrent_jobs,
                batch_size=request.batch_size,
                batch_interval_seconds=request.batch_interval_seconds,
                cooldown_seconds=request.cooldown_seconds,
            )
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()), tenant_key=tenant_key,
                entity_type="rate_limit_config", entity_id=agent_type_code,
                event_type=AIAuditEventType.RATE_LIMIT_CONFIG_UPDATED, event_category="ai",
                actor_id=caller_id, actor_type="user",
                properties={"agent_type_code": agent_type_code, "org_id": org_id or "global"},
                occurred_at=datetime.datetime.utcnow(),
            ))
