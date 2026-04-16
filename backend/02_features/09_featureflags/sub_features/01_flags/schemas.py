"""
featureflags.flags — Pydantic v2 API models.

Three scope partitions (global / org / application); CHECK + partial unique
indexes enforce on the DB side. Pydantic validates the shape up-front so
callers get a clean 422 instead of a CHECK violation 500.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


FlagScope = Literal["global", "org", "application"]
FlagValueType = Literal["boolean", "string", "number", "json"]
FlagEnvironment = Literal["dev", "staging", "prod", "test"]

_FLAG_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def _validate_flag_key(v: str) -> str:
    if not _FLAG_KEY_RE.match(v):
        raise ValueError(
            f"flag_key {v!r} must match ^[a-z][a-z0-9_]{{1,62}}$ (lowercase_snake_case)"
        )
    return v


class FlagCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: FlagScope
    org_id: str | None = None
    application_id: str | None = None
    flag_key: str
    value_type: FlagValueType
    default_value: Any
    description: str | None = None

    @field_validator("flag_key")
    @classmethod
    def _fk(cls, v: str) -> str:
        return _validate_flag_key(v)

    @model_validator(mode="after")
    def _scope_targets(self) -> "FlagCreate":
        if self.scope == "global":
            if self.org_id is not None or self.application_id is not None:
                raise ValueError(
                    "scope=global requires org_id and application_id to be null"
                )
        elif self.scope == "org":
            if self.org_id is None:
                raise ValueError("scope=org requires org_id")
            if self.application_id is not None:
                raise ValueError(
                    "scope=org requires application_id to be null (use scope=application for app-scoped flags)"
                )
        elif self.scope == "application":
            if self.org_id is None or self.application_id is None:
                raise ValueError(
                    "scope=application requires both org_id and application_id"
                )
        return self


class FlagUpdate(BaseModel):
    """PATCH body — scope/flag_key/value_type/org/app are frozen after create."""
    model_config = ConfigDict(extra="forbid")

    default_value: Any | None = None
    description: str | None = None
    is_active: bool | None = None


class FlagRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    scope: FlagScope
    org_id: str | None = None
    application_id: str | None = None
    flag_key: str
    value_type: FlagValueType
    default_value: Any
    description: str | None = None
    is_active: bool
    is_test: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _ts(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class FlagStateRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    flag_id: str
    environment: FlagEnvironment
    is_enabled: bool
    env_default_value: Any | None = None
    is_test: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _ts(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class FlagStateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_enabled: bool | None = None
    env_default_value: Any | None = None
