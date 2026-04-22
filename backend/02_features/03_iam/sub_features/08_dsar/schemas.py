from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class DsarJobType(str, Enum):
    EXPORT = "export"
    DELETE = "delete"


class DsarJobStatus(str, Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DsarExportRequest(BaseModel):
    subject_user_id: UUID = Field(..., description="User whose data is being exported")
    org_id: UUID = Field(..., description="Organization scope")


class DsarDeleteRequest(BaseModel):
    subject_user_id: UUID = Field(..., description="User whose data is being deleted")
    org_id: UUID = Field(..., description="Organization scope")


class DsarJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    job_type: DsarJobType
    actor_user_id: UUID
    subject_user_id: UUID
    org_id: UUID
    status: DsarJobStatus
    row_counts: Optional[dict] = None
    error_message: Optional[str] = None
    result_location: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class DsarExportData(BaseModel):
    """Shape of exported user data (JSON format)"""
    user: dict
    organizations: list[dict]
    workspaces: list[dict]
    workspace_members: list[dict]
    sessions: list[dict]
    audit_events: list[dict]
    notification_subscriptions: list[dict]


class DsarPayloadCreated(BaseModel):
    """Internal-only handoff between service and repository after encrypting a payload.
    Never surfaced on the API — ciphertext must not leak outside the backend.
    """
    payload_id: UUID
    job_id: UUID
    dek_version: int
    byte_size: int
