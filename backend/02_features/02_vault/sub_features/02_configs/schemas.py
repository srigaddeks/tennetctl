"""
vault.configs — Pydantic v2 API models.

Configs are plaintext, typed, scoped, NOT versioned. Value storage is JSONB; the
declared `value_type` drives validation + UI rendering only.

Scope model matches secrets — see vault.secrets.schemas for the full contract.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_KEY_RE = re.compile(r"^[a-z][a-z0-9._-]{0,127}$")

VaultScope = Literal["global", "org", "workspace"]
ConfigValueType = Literal["boolean", "string", "number", "json"]


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


def _validate_value_matches_type(value: Any, value_type: ConfigValueType) -> Any:
    """Enforce declared type. JSON accepts anything; number accepts int or float."""
    if value_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError("value must be a boolean when value_type='boolean'")
    elif value_type == "string":
        if not isinstance(value, str):
            raise ValueError("value must be a string when value_type='string'")
    elif value_type == "number":
        # bool is a subclass of int in Python — reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("value must be a number when value_type='number'")
    elif value_type == "json":
        # Any JSON-serializable value is fine; asyncpg handles dict/list round-trip.
        pass
    return value


class ConfigCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    value_type: ConfigValueType
    value: Any
    description: str | None = Field(default=None, max_length=500)
    scope: VaultScope = "global"
    org_id: str | None = None
    workspace_id: str | None = None

    @field_validator("key")
    @classmethod
    def _key_shape(cls, v: str) -> str:
        return _validate_key(v)

    @model_validator(mode="after")
    def _shape(self) -> "ConfigCreate":
        _validate_scope_shape(self.scope, self.org_id, self.workspace_id)
        _validate_value_matches_type(self.value, self.value_type)
        return self


class ConfigUpdate(BaseModel):
    """PATCH body. Only `value` + `description` + `is_active` are mutable.
    `value_type` + `scope` + `key` are immutable — change those via delete + recreate."""
    model_config = ConfigDict(extra="forbid")

    value: Any = None
    description: str | None = None
    is_active: bool | None = None


class ConfigMeta(BaseModel):
    """Read shape. Value IS visible for configs (unlike secrets)."""
    model_config = ConfigDict(extra="ignore")

    id: str
    key: str
    value_type: ConfigValueType
    value: Any
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

    @field_validator("value", mode="before")
    @classmethod
    def _unwrap_jsonb(cls, v: Any) -> Any:
        # asyncpg returns JSONB as str by default unless a codec is set.
        # Our pool registers the JSONB codec in 01_core.database (phase 3 plan 03),
        # so v is already a Python value. This validator is a safety net.
        import json
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (TypeError, ValueError):
                return v
        return v

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_timestamp(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v
