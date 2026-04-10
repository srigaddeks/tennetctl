"""kbio threat type catalog schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ThreatTypeDefResponse(BaseModel):
    code: str
    name: str
    description: str
    category: str
    severity: int
    default_action: str
    conditions: dict[str, Any]
    default_config: dict[str, Any]
    reason_template: str
    tags: list[str]


class ThreatTypeListResponse(BaseModel):
    items: list[ThreatTypeDefResponse]
    total: int
    limit: int
    offset: int
