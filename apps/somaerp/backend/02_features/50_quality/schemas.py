"""Pydantic v2 schemas for QC check-types, stages, outcomes, checkpoints, checks."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

QcCheckpointScopeKind = Literal[
    "recipe_step", "raw_material", "kitchen", "product", "universal"
]
QcCheckpointStatus = Literal["active", "paused", "archived"]


# ── Read-only lookups ───────────────────────────────────────────────────


class QcCheckTypeOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


class QcStageOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


class QcOutcomeOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


# ── Checkpoints ─────────────────────────────────────────────────────────


class QcCheckpointCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_id: int
    check_type_id: int
    scope_kind: QcCheckpointScopeKind
    scope_ref_id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    criteria_jsonb: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    status: QcCheckpointStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class QcCheckpointUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage_id: int | None = None
    check_type_id: int | None = None
    scope_kind: QcCheckpointScopeKind | None = None
    scope_ref_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    criteria_jsonb: dict[str, Any] | None = None
    required: bool | None = None
    status: QcCheckpointStatus | None = None
    properties: dict[str, Any] | None = None


class QcCheckpointOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    stage_id: int
    stage_code: str | None = None
    stage_name: str | None = None
    check_type_id: int
    check_type_code: str | None = None
    check_type_name: str | None = None
    scope_kind: QcCheckpointScopeKind
    scope_ref_id: str | None = None
    name: str
    criteria_jsonb: dict[str, Any] = Field(default_factory=dict)
    required: bool
    status: QcCheckpointStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Checks (append-only — no Update schema) ─────────────────────────────


class QcCheckCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkpoint_id: str
    batch_id: str | None = None
    raw_material_lot: str | None = None
    kitchen_id: str | None = None
    outcome_id: int
    measured_value: Decimal | None = None
    measured_unit_id: int | None = None
    notes: str | None = None
    photo_vault_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class QcCheckOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    checkpoint_id: str
    checkpoint_name: str | None = None
    checkpoint_scope_kind: QcCheckpointScopeKind | None = None
    checkpoint_scope_ref_id: str | None = None
    stage_id: int | None = None
    stage_code: str | None = None
    stage_name: str | None = None
    check_type_id: int | None = None
    check_type_code: str | None = None
    check_type_name: str | None = None
    batch_id: str | None = None
    raw_material_lot: str | None = None
    kitchen_id: str | None = None
    kitchen_name: str | None = None
    outcome_id: int
    outcome_code: str | None = None
    outcome_name: str | None = None
    measured_value: Decimal | None = None
    measured_unit_id: int | None = None
    measured_unit_code: str | None = None
    notes: str | None = None
    photo_vault_key: str | None = None
    performed_by_user_id: str
    ts: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
