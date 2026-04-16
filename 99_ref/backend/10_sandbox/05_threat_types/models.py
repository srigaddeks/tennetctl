from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreatTypeRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    threat_code: str
    version_number: int
    severity_code: str
    severity_name: str | None
    expression_tree: dict | None
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None
