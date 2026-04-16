from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ApprovalRecord:
    id: str
    tenant_key: str
    requester_id: str
    org_id: str | None
    approver_id: str | None
    status_code: str
    tool_name: str
    tool_category: str
    entity_type: str | None
    operation: str | None
    payload_json: dict
    diff_json: dict | None
    rejection_reason: str | None
    expires_at: str
    approved_at: str | None
    executed_at: str | None
    created_at: str
    updated_at: str
