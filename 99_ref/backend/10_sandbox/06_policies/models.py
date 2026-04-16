from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    policy_code: str
    version_number: int
    threat_type_id: str
    threat_code: str | None
    actions: list[dict]
    is_enabled: bool
    cooldown_minutes: int
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None


@dataclass(frozen=True)
class PolicyExecutionRecord:
    id: str
    tenant_key: str
    org_id: str
    policy_id: str
    threat_evaluation_id: str | None
    actions_executed: list[dict]
    actions_failed: list[dict]
    created_at: str
    created_by: str
