from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SSFStreamRecord:
    id: str
    tenant_key: str
    org_id: str
    stream_description: str | None
    receiver_url: str | None
    delivery_method: str
    events_requested: str  # JSON array stored as text
    events_delivered: int
    stream_status: str
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SSFStreamSubjectRecord:
    id: str
    stream_id: str
    subject_type: str
    subject_format: str
    subject_id_data: str  # JSON stored as text
    created_at: str


@dataclass(frozen=True)
class SSFOutboxRecord:
    id: str
    stream_id: str
    set_jwt: str
    jti: str
    acknowledged: bool
    created_at: str
    acknowledged_at: str | None


@dataclass(frozen=True)
class SSFDeliveryLogRecord:
    id: str
    stream_id: str
    jti: str
    delivery_method: str
    http_status: int | None
    error_message: str | None
    delivered_at: str
