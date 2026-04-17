"""Pydantic schemas for monitoring.saved_queries."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


QueryTarget = Literal["logs", "metrics", "traces"]


class SavedQueryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    target: QueryTarget
    dsl: dict[str, Any]
    shared: bool = False


class SavedQueryUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    dsl: dict[str, Any] | None = None
    shared: bool | None = None
    is_active: bool | None = None


class SavedQueryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    owner_user_id: str
    name: str
    description: str | None = None
    target: QueryTarget
    dsl: dict[str, Any]
    shared: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SavedQueryResponse":
        dsl = row.get("dsl")
        if isinstance(dsl, str):
            import json as _json
            dsl = _json.loads(dsl)
        return cls(
            id=row["id"],
            org_id=row["org_id"],
            owner_user_id=row["owner_user_id"],
            name=row["name"],
            description=row.get("description"),
            target=row["target"],  # type: ignore[arg-type]
            dsl=dsl or {},
            shared=bool(row["shared"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class SavedQueryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SavedQueryResponse]
    total: int
