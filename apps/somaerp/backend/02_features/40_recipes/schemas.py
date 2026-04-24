"""Pydantic v2 schemas for recipes + nested ingredients + steps + cost."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RecipeStatus = Literal["draft", "active", "archived"]


# ── Recipe ───────────────────────────────────────────────────────────────

class RecipeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str
    version: int = Field(default=1, ge=1)
    status: RecipeStatus = "draft"
    effective_from: date | None = None
    notes: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class RecipeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int | None = Field(default=None, ge=1)
    status: RecipeStatus | None = None
    effective_from: date | None = None
    notes: str | None = None
    properties: dict[str, Any] | None = None


class RecipeOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    product_id: str
    product_name: str | None = None
    product_slug: str | None = None
    product_category_code: str | None = None
    version: int
    status: RecipeStatus
    effective_from: date | None = None
    notes: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Recipe Ingredients ───────────────────────────────────────────────────

class RecipeIngredientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_material_id: str
    quantity: Decimal = Field(gt=0)
    unit_id: int
    position: int = Field(default=1, ge=1)
    notes: str | None = None


class RecipeIngredientUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_material_id: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_id: int | None = None
    position: int | None = Field(default=None, ge=1)
    notes: str | None = None


class RecipeIngredientOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    recipe_id: str
    raw_material_id: str
    raw_material_name: str | None = None
    raw_material_slug: str | None = None
    raw_material_target_unit_cost: Decimal | None = None
    raw_material_currency_code: str | None = None
    quantity: Decimal
    unit_id: int
    unit_code: str | None = None
    unit_dimension: str | None = None
    position: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Recipe Steps ─────────────────────────────────────────────────────────

class RecipeStepCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_number: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=200)
    duration_min: int | None = Field(default=None, ge=0)
    equipment_notes: str | None = None
    instructions: str | None = None


class RecipeStepUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_number: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    duration_min: int | None = Field(default=None, ge=0)
    equipment_notes: str | None = None
    instructions: str | None = None


class RecipeStepOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    recipe_id: str
    step_number: int
    name: str
    duration_min: int | None = None
    equipment_notes: str | None = None
    instructions: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Cost ─────────────────────────────────────────────────────────────────

class RecipeCostLine(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ingredient_id: str
    raw_material_id: str
    raw_material_name: str | None = None
    quantity: Decimal
    unit_code: str | None = None
    unit_cost: Decimal | None = None
    line_cost: Decimal | None = None
    is_unconvertible: bool = False


class RecipeCostSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    recipe_id: str
    product_name: str | None = None
    total_cost: Decimal
    currency_code: str
    ingredient_count: int
    has_unconvertible_units: bool
    lines: list[RecipeCostLine] = Field(default_factory=list)


# ── Step-Equipment link ──────────────────────────────────────────────────

class StepEquipmentLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    equipment_id: str
