"""kprotect decisions schemas — Pydantic v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DecisionData(BaseModel):
    id: str
    org_id: str
    session_id: str | None
    user_hash: str | None
    device_uuid: str | None
    outcome: str | None
    action: str | None
    policy_set_id: str | None
    total_latency_ms: float | None
    kbio_latency_ms: float | None
    policy_latency_ms: float | None
    metadata: dict[str, Any] | None
    created_at: datetime


class DecisionDetailData(BaseModel):
    id: str
    decision_id: str
    policy_selection_id: str | None
    action: str | None
    reason: str | None
    execution_ms: float | None
    error_message: str | None
    created_at: datetime


class DecisionListData(BaseModel):
    items: list[DecisionData]
    total: int
    limit: int
    offset: int
