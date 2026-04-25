"""
product_ops.track — Pydantic v2 schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TrackEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str = Field(..., min_length=1, max_length=200)
    distinct_id: str = Field(..., min_length=1, max_length=200)
    session_id: str | None = Field(default=None, max_length=200)
    source: Literal["web", "mobile", "server", "backend", "other"] = "web"
    url: str | None = Field(default=None, max_length=2000)
    properties: dict[str, Any] = Field(default_factory=dict)
    org_id: str | None = None
    workspace_id: str | None = None
    actor_user_id: str | None = None


class TrackEventResponse(BaseModel):
    id: str
    created_at: datetime


class ProductEventRow(BaseModel):
    id: str
    org_id: str
    workspace_id: str | None
    actor_user_id: str | None
    distinct_id: str
    event_name: str
    session_id: str | None
    source: str
    url: str | None
    user_agent: str | None
    ip_addr: str | None
    properties: dict[str, Any]
    created_at: datetime


class ProductEventListResponse(BaseModel):
    items: list[ProductEventRow]
    next_cursor: str | None


class TopEventRow(BaseModel):
    event_name: str
    count: int


class CountsResponse(BaseModel):
    events_today: int
    events_24h: int
    dau: int
    distinct_ids_24h: int
    top_events_24h: list[TopEventRow]
