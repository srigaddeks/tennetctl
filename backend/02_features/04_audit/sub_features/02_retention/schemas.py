from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class RetentionPolicyStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class RetentionPolicyCreate(BaseModel):
    org_id: UUID = Field(..., description="Organization for this policy")
    retention_days: int = Field(..., ge=7, le=2555, description="Days to retain audit events (7-7 years)")
    auto_purge_enabled: bool = Field(default=True, description="Enable automatic purge jobs")
    exclude_critical: bool = Field(default=True, description="Never purge critical/security events")


class RetentionPolicyUpdate(BaseModel):
    retention_days: Optional[int] = Field(None, ge=7, le=2555)
    auto_purge_enabled: Optional[bool] = None
    exclude_critical: Optional[bool] = None
    status: Optional[RetentionPolicyStatus] = None


class RetentionPolicyRead(BaseModel):
    policy_id: UUID
    org_id: UUID
    retention_days: int
    auto_purge_enabled: bool
    exclude_critical: bool
    status: RetentionPolicyStatus
    last_purge_at: Optional[datetime]
    next_purge_scheduled_at: Optional[datetime]
    purge_count: int  # Total events purged under this policy
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurgeJobStatus(str, Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PurgeJobRead(BaseModel):
    job_id: UUID
    policy_id: UUID
    status: PurgeJobStatus
    rows_purged: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
