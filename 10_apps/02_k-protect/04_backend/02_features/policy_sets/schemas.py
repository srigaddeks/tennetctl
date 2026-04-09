"""kprotect policy_sets schemas — Pydantic v2."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PolicySetMemberItem(BaseModel):
    selection_id: str
    sort_order: int


class PolicySetData(BaseModel):
    id: str
    org_id: str
    code: str
    name: str | None
    description: str | None
    evaluation_mode: str
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    members: list[PolicySetMemberItem]


class PolicySetListData(BaseModel):
    items: list[PolicySetData]
    total: int
    limit: int
    offset: int


class CreatePolicySetRequest(BaseModel):
    org_id: str
    code: str
    name: str
    description: str | None = None
    evaluation_mode: str = "short_circuit"
    is_default: bool = False
    member_selection_ids: list[PolicySetMemberItem] = []


class PatchPolicySetRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    evaluation_mode: str | None = None
    is_default: bool | None = None
    # When provided, the full member list is rewritten
    member_selection_ids: list[PolicySetMemberItem] | None = None
