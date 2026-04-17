"""Pydantic schemas for notify.subscriptions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class SubscriptionCreate(BaseModel):
    org_id: str
    name: str
    event_key_pattern: str
    template_id: str
    channel_id: int
    recipient_mode: str = Field(default="actor", description="actor | users | roles")
    recipient_filter: dict = Field(default_factory=dict, description="{user_ids:[...]} or {role_codes:[...]}")

    @field_validator("recipient_mode")
    @classmethod
    def _valid_mode(cls, v: str) -> str:
        if v not in {"actor", "users", "roles"}:
            raise ValueError("recipient_mode must be one of: actor, users, roles")
        return v

    @field_validator("event_key_pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("event_key_pattern must not be empty")
        # Allow: lowercase letters, digits, underscores, dots, and * for wildcards
        import re
        if not re.match(r'^[a-z_*][a-z0-9_.*]*$', stripped):
            raise ValueError(
                "event_key_pattern must use lowercase letters, digits, underscores, "
                "dots, and '*'. Example: 'iam.users.*' or 'iam.users.created'"
            )
        return stripped


class SubscriptionUpdate(BaseModel):
    name: str | None = None
    event_key_pattern: str | None = None
    template_id: str | None = None
    channel_id: int | None = None
    is_active: bool | None = None

    @field_validator("event_key_pattern")
    @classmethod
    def validate_pattern(cls, v: str | None) -> str | None:
        if v is None:
            return v
        import re
        if not re.match(r'^[a-z_*][a-z0-9_.*]*$', v.strip()):
            raise ValueError("event_key_pattern uses invalid characters")
        return v.strip()


class SubscriptionRow(BaseModel):
    id: str
    org_id: str
    name: str
    event_key_pattern: str
    template_id: str
    channel_id: int
    channel_code: str
    channel_label: str
    recipient_mode: str = "actor"
    recipient_filter: dict = {}
    is_active: bool
    deleted_at: Any = None
    created_by: str
    updated_by: str
    created_at: Any
    updated_at: Any
