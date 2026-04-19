"""Pydantic schemas for product_ops.profiles."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ValueType = Literal["text", "jsonb", "smallint"]
TraitSource = Literal["identify", "trait_set", "inferred", "imported"]


class SetTraitsBody(BaseModel):
    """Caller submits a flat dict of trait_code → value. Server resolves
    each trait against dim_attr_defs to determine the right key_* column.

    Example:
      {"email": "alice@x.com", "plan": "pro", "mrr_cents": 4900}
    """
    model_config = ConfigDict(extra="forbid")

    visitor_id: str | None = None
    anonymous_id: str | None = None
    workspace_id: str
    project_key: str | None = None
    traits: dict[str, Any] = Field(default_factory=dict)
    source: TraitSource = "trait_set"


class TraitOut(BaseModel):
    code: str
    label: str
    value_type: ValueType
    value: Any
    source: TraitSource | str
    set_at: datetime


class ProfileOut(BaseModel):
    """Read shape from v_visitor_profiles plus the raw trait list."""
    model_config = ConfigDict(extra="ignore")

    id: str
    anonymous_id: str
    user_id: str | None
    org_id: str
    workspace_id: str
    first_seen: datetime
    last_seen: datetime
    # Pivoted trait columns
    email: str | None
    phone: str | None
    name: str | None
    plan: str | None
    mrr_cents: Any | None
    country: str | None
    company: str | None
    role: str | None
    signup_at: str | None
    last_login_at: str | None
    # First-touch (inherited)
    first_utm_campaign: str | None
    first_referrer: str | None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    # Optional bag of all traits including unrecognized ones
    traits: list[TraitOut] | None = None


class ProfileListResponse(BaseModel):
    items: list[ProfileOut]
    total: int
    limit: int
    offset: int
