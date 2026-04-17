"""
iam.auth — Pydantic v2 API models.

Signup + signin accept email + cleartext password (over HTTPS in prod). Cleartext
never propagates further than the credentials service: it is hashed in-memory
and discarded. Passwords have a minimum length but no maximum policy in v1 —
argon2 itself caps server-side cost.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_email(v: str) -> str:
    if not _EMAIL_RE.match(v):
        raise ValueError(f"email {v!r} is not a valid email address")
    return v


class SignupBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    display_name: str
    password: str = Field(min_length=8, max_length=512)

    @field_validator("email")
    @classmethod
    def _email_shape(cls, v: str) -> str:
        return _validate_email(v)


class SigninBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str = Field(min_length=1, max_length=512)

    @field_validator("email")
    @classmethod
    def _email_shape(cls, v: str) -> str:
        return _validate_email(v)


class OAuthCallbackBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    redirect_uri: str = Field(min_length=1)


class SessionMeta(BaseModel):
    """Read shape for a session row exposed to the client."""
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    org_id: str | None = None
    workspace_id: str | None = None
    expires_at: str
    revoked_at: str | None = None
    is_valid: bool

    @field_validator("expires_at", "revoked_at", mode="before")
    @classmethod
    def _coerce_ts(cls, v: object) -> object:
        # asyncpg returns datetime; we want ISO strings on the wire.
        from datetime import datetime
        if v is None:
            return v
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class AuthResponse(BaseModel):
    """Returned by signup / signin / oauth — the token + user + session."""
    model_config = ConfigDict(extra="ignore")

    token: str
    user: dict
    session: SessionMeta


AccountType = Literal["email_password", "google_oauth", "github_oauth"]
