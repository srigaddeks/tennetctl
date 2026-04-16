from __future__ import annotations

from pydantic import BaseModel, Field


class CreateStreamRequest(BaseModel):
    delivery_method: str = Field(
        ..., pattern=r"^(push|poll)$", description="Delivery method: push or poll"
    )
    receiver_url: str | None = Field(
        None,
        max_length=2048,
        description="Receiver endpoint URL (required for push delivery)",
    )
    events_requested: list[str] = Field(
        ..., min_length=1, description="List of event URIs to subscribe to"
    )
    description: str | None = Field(None, max_length=500)
    authorization_header: str | None = Field(
        None,
        max_length=2048,
        description="Authorization header value for push delivery",
    )


class UpdateStreamRequest(BaseModel):
    events_requested: list[str] | None = Field(None, min_length=1)
    receiver_url: str | None = Field(None, max_length=2048)
    description: str | None = Field(None, max_length=500)


class UpdateStreamStatusRequest(BaseModel):
    stream_status: str = Field(
        ..., pattern=r"^(enabled|paused|disabled)$"
    )


class AddSubjectRequest(BaseModel):
    subject_type: str = Field(..., min_length=1, max_length=100)
    subject_format: str = Field(..., min_length=1, max_length=100)
    subject_id_data: dict = Field(..., description="Subject identifier data")


class StreamResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    stream_description: str | None = None
    receiver_url: str | None = None
    delivery_method: str
    events_requested: list[str]
    events_delivered: int
    stream_status: str
    is_active: bool
    created_at: str
    updated_at: str


class StreamListResponse(BaseModel):
    items: list[StreamResponse]
    total: int


class SubjectResponse(BaseModel):
    id: str
    stream_id: str
    subject_type: str
    subject_format: str
    subject_id_data: dict
    created_at: str


class PollResponse(BaseModel):
    sets: list[dict] = Field(default_factory=list, description="List of {jti, set_jwt}")
    more_available: bool = False


class VerifyResponse(BaseModel):
    jti: str
    delivered: bool
