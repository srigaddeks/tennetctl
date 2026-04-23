"""Schemas for ideas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IdeaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=10000)
    tags: list[str] = Field(default_factory=list)


class IdeaPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=10000)
    tags: list[str] | None = None


class IdeaOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    org_id: str
    workspace_id: str
    title: str
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_by: str
    created_at: datetime
    updated_at: datetime
