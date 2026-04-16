from __future__ import annotations

from pydantic import BaseModel


class DimensionResponse(BaseModel):
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool
