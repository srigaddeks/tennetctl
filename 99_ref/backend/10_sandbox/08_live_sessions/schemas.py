from __future__ import annotations

from pydantic import BaseModel, Field


class StartSessionRequest(BaseModel):
    connector_instance_id: str = Field(..., min_length=1)
    signal_ids: list[str] = Field(default_factory=list)
    threat_type_ids: list[str] = Field(default_factory=list)
    duration_minutes: int = Field(default=30, ge=1, le=60)
    workspace_id: str = Field(..., min_length=1)


class AttachSignalRequest(BaseModel):
    signal_id: str = Field(..., min_length=1)


class AttachThreatRequest(BaseModel):
    threat_type_id: str = Field(..., min_length=1)


class SaveDatasetRequest(BaseModel):
    dataset_code: str = Field(
        ..., min_length=3, max_length=100, pattern=r"^[a-z0-9][a-z0-9\-]{1,98}[a-z0-9]$"
    )
    properties: dict[str, str] | None = None


class LiveSessionSignalResponse(BaseModel):
    id: str
    live_session_id: str
    signal_id: str
    signal_code: str | None = None
    signal_name: str | None = None


class LiveSessionThreatResponse(BaseModel):
    id: str
    live_session_id: str
    threat_type_id: str
    threat_code: str | None = None
    threat_name: str | None = None


class LiveSessionResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    connector_instance_id: str
    session_status: str
    duration_minutes: int
    started_at: str | None = None
    expires_at: str | None = None
    paused_at: str | None = None
    completed_at: str | None = None
    data_points_received: int = 0
    bytes_received: int = 0
    signals_executed: int = 0
    threats_evaluated: int = 0
    created_at: str
    created_by: str
    attached_signals: list[LiveSessionSignalResponse] = Field(default_factory=list)
    attached_threats: list[LiveSessionThreatResponse] = Field(default_factory=list)


class LiveSessionListResponse(BaseModel):
    items: list[LiveSessionResponse]
    total: int


class StreamEvent(BaseModel):
    sequence_number: int
    event_type: str
    data: dict
    occurred_at: str


class StreamResponse(BaseModel):
    events: list[StreamEvent] = Field(default_factory=list)
    has_more: bool = False
    next_cursor: int = 0


class SaveDatasetResponse(BaseModel):
    dataset_id: str
    dataset_code: str
    version_number: int
    created_at: str
