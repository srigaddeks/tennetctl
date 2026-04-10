"""kbio signal catalog schemas."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class SignalDefResponse(BaseModel):
    code: str
    name: str
    description: str
    category: str
    signal_type: str
    default_config: dict[str, Any]
    severity: int
    tags: list[str]


class SignalListResponse(BaseModel):
    items: list[SignalDefResponse]
    total: int
    limit: int
    offset: int
