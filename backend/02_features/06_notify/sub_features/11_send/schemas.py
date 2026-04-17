"""Pydantic schemas for notify.send (transactional API)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class TransactionalSendRequest(BaseModel):
    org_id: str
    template_key: str = Field(..., min_length=1, max_length=64)
    recipient_user_id: str = Field(..., min_length=1, description="User ID or direct email address")
    channel_code: Literal["email", "webpush", "in_app"] = "email"
    variables: dict[str, Any] = Field(default_factory=dict, description="Static variable overrides")
    deep_link: str | None = Field(default=None, description="Canonical URL the recipient lands on when they open the notification")
    send_at: datetime | None = Field(default=None, description="ISO8601 UTC time to release this delivery. Mutually exclusive with delay_seconds.")
    delay_seconds: int | None = Field(default=None, ge=1, le=86400 * 30, description="Defer this many seconds from now. Mutually exclusive with send_at.")

    @model_validator(mode="after")
    def _one_schedule_only(self) -> "TransactionalSendRequest":
        if self.send_at is not None and self.delay_seconds is not None:
            raise ValueError("send_at and delay_seconds are mutually exclusive")
        return self


class TransactionalSendResponse(BaseModel):
    delivery_id: str
