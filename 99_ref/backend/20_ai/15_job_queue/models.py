from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobRecord:
    id: str
    tenant_key: str
    user_id: str
    org_id: str | None
    workspace_id: str | None
    agent_type_code: str
    priority_code: str
    status_code: str
    job_type: str
    input_json: dict
    output_json: dict | None
    error_message: str | None
    scheduled_at: str
    started_at: str | None
    completed_at: str | None
    estimated_tokens: int
    actual_tokens: int | None
    max_retries: int
    retry_count: int
    next_retry_at: str | None
    conversation_id: str | None
    agent_run_id: str | None
    batch_id: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class BatchRecord:
    id: str
    tenant_key: str
    user_id: str
    org_id: str | None
    agent_type_code: str
    name: str | None
    description: str | None
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    estimated_tokens: int
    actual_tokens: int
    status_code: str
    scheduled_at: str
    started_at: str | None
    completed_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class RateLimitConfig:
    agent_type_code: str
    max_requests_per_minute: int
    max_tokens_per_minute: int
    max_concurrent_jobs: int
    batch_size: int
    batch_interval_seconds: int
    cooldown_seconds: int
