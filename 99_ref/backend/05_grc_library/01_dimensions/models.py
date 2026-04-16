from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DimensionRecord:
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool
