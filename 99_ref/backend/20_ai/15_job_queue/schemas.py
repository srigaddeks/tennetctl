from __future__ import annotations

import json
from typing import Any
from pydantic import BaseModel, Field, field_validator


class EnqueueJobRequest(BaseModel):
    agent_type_code: str = Field(..., min_length=1, max_length=50)
    job_type: str = Field(..., min_length=1, max_length=200)
    input_json: dict = Field(default_factory=dict)
    priority_code: str = Field(default="normal")
    estimated_tokens: int = Field(default=0, ge=0)
    scheduled_at: str | None = None       # ISO datetime; defaults to now
    max_retries: int = Field(default=3, ge=0, le=10)
    conversation_id: str | None = None
    batch_id: str | None = None


class CreateBatchRequest(BaseModel):
    agent_type_code: str = Field(..., min_length=1, max_length=50)
    name: str | None = Field(None, max_length=500)
    description: str | None = None
    jobs: list[EnqueueJobRequest] = Field(..., min_length=1)
    scheduled_at: str | None = None


class JobResponse(BaseModel):
    id: str
    tenant_key: str
    user_id: str
    org_id: str | None = None
    agent_type_code: str
    priority_code: str
    status_code: str
    job_type: str
    input_json: Any  # may arrive as dict or JSON string from asyncpg
    output_json: Any = None  # same

    @field_validator("input_json", "output_json", mode="before")
    @classmethod
    def _coerce_json(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v
    error_message: str | None = None
    scheduled_at: str
    started_at: str | None = None
    completed_at: str | None = None
    estimated_tokens: int
    actual_tokens: int | None = None
    retry_count: int
    max_retries: int
    batch_id: str | None = None
    conversation_id: str | None = None
    created_at: str
    updated_at: str


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int


class BatchResponse(BaseModel):
    id: str
    tenant_key: str
    user_id: str
    agent_type_code: str
    name: str | None = None
    description: str | None = None
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    pending_jobs: int
    estimated_tokens: int
    actual_tokens: int
    status_code: str
    scheduled_at: str
    started_at: str | None = None
    completed_at: str | None = None
    completion_pct: float
    created_at: str


class QueueDepthResponse(BaseModel):
    agent_type_code: str
    agent_type_name: str | None = None
    status_code: str
    priority_code: str
    job_count: int
    estimated_tokens: int
    oldest_job_at: str | None = None


class RateLimitStatusResponse(BaseModel):
    agent_type_code: str
    agent_type_name: str | None = None
    window_start: str
    requests_count: int
    tokens_count: int
    max_requests_per_minute: int | None = None
    max_tokens_per_minute: int | None = None
    max_concurrent_jobs: int | None = None
    request_utilization_pct: float | None = None
    token_utilization_pct: float | None = None
    is_at_limit: bool


class UpdateRateLimitRequest(BaseModel):
    max_requests_per_minute: int | None = Field(None, ge=1)
    max_tokens_per_minute: int | None = Field(None, ge=1)
    max_concurrent_jobs: int | None = Field(None, ge=1)
    batch_size: int | None = Field(None, ge=1)
    batch_interval_seconds: int | None = Field(None, ge=10)
    cooldown_seconds: int | None = Field(None, ge=0)
