from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentToolRecord:
    id: str
    tenant_key: str
    org_id: str
    tool_code: str
    tool_type_code: str
    input_schema: dict
    output_schema: dict
    endpoint_url: str | None
    mcp_server_url: str | None
    python_source: str | None
    signal_id: str | None
    requires_approval: bool
    is_destructive: bool
    timeout_ms: int
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None
