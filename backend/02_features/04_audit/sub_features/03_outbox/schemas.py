"""
audit.outbox — Pydantic v2 models for the tail endpoint.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AuditEventRowSlim(BaseModel):
    """Minimal event row returned from the tail endpoint (subset of full AuditEventRow)."""

    outbox_id: int
    id: str
    event_key: str
    event_label: str | None = None
    category_code: str
    actor_user_id: str | None = None
    org_id: str | None = None
    trace_id: str
    outcome: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def _coerce_timestamp(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class AuditTailResponse(BaseModel):
    items: list[AuditEventRowSlim]
    last_outbox_id: int


class AuditOutboxCursorResponse(BaseModel):
    last_outbox_id: int
