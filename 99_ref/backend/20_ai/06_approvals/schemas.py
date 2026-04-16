from __future__ import annotations
from pydantic import BaseModel, Field

class ApprovalResponse(BaseModel):
    id: str
    tenant_key: str
    requester_id: str
    org_id: str | None = None
    approver_id: str | None = None
    status_code: str
    tool_name: str
    tool_category: str
    entity_type: str | None = None
    operation: str | None = None
    payload_json: dict
    diff_json: dict | None = None
    rejection_reason: str | None = None
    expires_at: str
    approved_at: str | None = None
    executed_at: str | None = None
    created_at: str
    updated_at: str
    is_overdue: bool = False
    execution_result: dict | None = None  # populated after execution, not stored in DB

class ApprovalListResponse(BaseModel):
    items: list[ApprovalResponse]
    total: int

class ApproveRequest(BaseModel):
    pass

class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)
