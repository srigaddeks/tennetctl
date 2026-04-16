from __future__ import annotations

from pydantic import BaseModel


class RiskCategoryResponse(BaseModel):
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool


class RiskTreatmentTypeResponse(BaseModel):
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool


class RiskLevelResponse(BaseModel):
    code: str
    name: str
    description: str
    score_min: int
    score_max: int
    color_hex: str
    sort_order: int
    is_active: bool
