"""
vault.secrets — Pydantic v2 API models.

SecretCreate / SecretRotate drive the write surface. SecretMeta is the flat read
shape returned everywhere except the single plaintext-read endpoint. SecretValue
is ONLY returned by the internal admin endpoint GET /v1/vault/{key}; list
responses never carry it.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_KEY_RE = re.compile(r"^[a-z][a-z0-9._-]{0,127}$")


def _validate_key(v: str) -> str:
    if not _KEY_RE.match(v):
        raise ValueError(
            "key must match ^[a-z][a-z0-9._-]{0,127}$ "
            "(lowercase, starts with letter, dots/dashes/underscores allowed)"
        )
    return v


class SecretCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    value: str = Field(min_length=1, max_length=65536)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("key")
    @classmethod
    def _key_shape(cls, v: str) -> str:
        return _validate_key(v)


class SecretRotate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1, max_length=65536)
    description: str | None = Field(default=None, max_length=500)


class SecretMeta(BaseModel):
    """Flat read shape. Metadata only — never carries plaintext or ciphertext bytes."""
    model_config = ConfigDict(extra="ignore")

    key: str
    version: int
    description: str | None = None
    is_active: bool
    is_test: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_timestamp(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class SecretValue(BaseModel):
    """Returned only by GET /v1/vault/{key}. Never from list."""
    model_config = ConfigDict(extra="forbid")

    key: str
    version: int
    value: str
