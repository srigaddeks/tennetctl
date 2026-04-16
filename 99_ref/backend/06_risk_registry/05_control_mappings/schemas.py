from __future__ import annotations

from pydantic import BaseModel, Field


class CreateControlMappingRequest(BaseModel):
    control_id: str
    link_type: str = Field(default="mitigating", pattern=r"^(mitigating|compensating|related)$")
    notes: str | None = None


class ControlMappingResponse(BaseModel):
    id: str
    risk_id: str
    control_id: str
    link_type: str
    notes: str | None = None
    created_at: str
    created_by: str | None = None
    # Approval
    approval_status: str = "approved"
    approved_by: str | None = None
    approved_at: str | None = None
    rejection_reason: str | None = None
    ai_confidence: float | None = None
    ai_rationale: str | None = None
    # Derived
    control_code: str | None = None
    control_name: str | None = None
    approved_by_name: str | None = None
    risk_code: str | None = None
    risk_title: str | None = None


class ApproveControlMappingRequest(BaseModel):
    notes: str | None = None


class RejectControlMappingRequest(BaseModel):
    rejection_reason: str | None = None


class BulkApproveRequest(BaseModel):
    mapping_ids: list[str]


class BulkRejectRequest(BaseModel):
    mapping_ids: list[str]
    rejection_reason: str | None = None


class PendingMappingsResponse(BaseModel):
    items: list[ControlMappingResponse]
    total: int


class AssignRiskToControlRequest(BaseModel):
    risk_id: str
    link_type: str = Field(default="mitigating", pattern=r"^(mitigating|compensating|related)$")
    notes: str | None = None
