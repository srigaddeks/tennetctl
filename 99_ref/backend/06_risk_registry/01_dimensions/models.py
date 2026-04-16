from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskCategoryRecord:
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool


@dataclass(frozen=True)
class RiskTreatmentTypeRecord:
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool


@dataclass(frozen=True)
class RiskLevelRecord:
    code: str
    name: str
    description: str
    score_min: int
    score_max: int
    color_hex: str
    sort_order: int
    is_active: bool
