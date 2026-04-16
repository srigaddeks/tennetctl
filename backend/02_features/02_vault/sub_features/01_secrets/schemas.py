"""
vault.secrets — Pydantic v2 API models.

Scope model (ADR-028, plan 07-03):
  - scope='global'    → org_id None, workspace_id None
  - scope='org'       → org_id set, workspace_id None
  - scope='workspace' → org_id set, workspace_id set

The `SecretValue` schema was removed — v0.3 dropped the plaintext HTTP view.
Reveal-once is the only path that carries plaintext, and it holds the value in
a client-side ref after POST/rotate (never re-fetched from the server).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_KEY_RE = re.compile(r"^[a-z][a-z0-9._-]{0,127}$")

VaultScope = Literal["global", "org", "workspace"]


def _validate_key(v: str) -> str:
    if not _KEY_RE.match(v):
        raise ValueError(
            "key must match ^[a-z][a-z0-9._-]{0,127}$ "
            "(lowercase, starts with letter, dots/dashes/underscores allowed)"
        )
    return v


def _validate_scope_shape(
    scope: VaultScope, org_id: str | None, workspace_id: str | None
) -> None:
    if scope == "global":
        if org_id is not None or workspace_id is not None:
            raise ValueError("scope='global' requires org_id=null and workspace_id=null")
    elif scope == "org":
        if not org_id or workspace_id is not None:
            raise ValueError("scope='org' requires org_id set and workspace_id=null")
    elif scope == "workspace":
        if not org_id or not workspace_id:
            raise ValueError("scope='workspace' requires both org_id and workspace_id")


class SecretCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    value: str = Field(min_length=1, max_length=65536)
    description: str | None = Field(default=None, max_length=500)
    scope: VaultScope = "global"
    org_id: str | None = None
    workspace_id: str | None = None

    @field_validator("key")
    @classmethod
    def _key_shape(cls, v: str) -> str:
        return _validate_key(v)

    @model_validator(mode="after")
    def _scope_shape(self) -> "SecretCreate":
        _validate_scope_shape(self.scope, self.org_id, self.workspace_id)
        return self


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
    scope: VaultScope
    org_id: str | None = None
    workspace_id: str | None = None
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
