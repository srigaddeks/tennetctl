from __future__ import annotations

from pydantic import BaseModel, Field


class CreateToolRequest(BaseModel):
    tool_code: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]{2,100}$"
    )
    tool_type_code: str = Field(
        ..., description="One of: mcp_server, api_endpoint, python_function, sandbox_signal, db_query"
    )
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    endpoint_url: str | None = None
    mcp_server_url: str | None = None
    python_source: str | None = None
    signal_id: str | None = None
    requires_approval: bool = False
    is_destructive: bool = False
    timeout_ms: int = Field(default=30000, ge=1000, le=300000)
    properties: dict[str, str] = Field(
        default_factory=dict, description="EAV properties: name, description"
    )


class UpdateToolRequest(BaseModel):
    input_schema: dict | None = None
    output_schema: dict | None = None
    endpoint_url: str | None = None
    mcp_server_url: str | None = None
    python_source: str | None = None
    signal_id: str | None = None
    requires_approval: bool | None = None
    is_destructive: bool | None = None
    timeout_ms: int | None = Field(None, ge=1000, le=300000)
    properties: dict[str, str] | None = None


class ToolResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    tool_code: str
    tool_type_code: str
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    endpoint_url: str | None = None
    mcp_server_url: str | None = None
    python_source: str | None = None
    signal_id: str | None = None
    requires_approval: bool
    is_destructive: bool
    timeout_ms: int
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    properties: dict[str, str] | None = None


class ToolListResponse(BaseModel):
    items: list[ToolResponse]
    total: int
