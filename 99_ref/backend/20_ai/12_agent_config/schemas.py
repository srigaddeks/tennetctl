from __future__ import annotations

from pydantic import BaseModel, Field


_VALID_PROVIDER_TYPES = {"openai", "anthropic", "azure_openai", "openai_compatible"}


class CreateAgentConfigRequest(BaseModel):
    agent_type_code: str = Field(..., min_length=1, max_length=50)
    org_id: str | None = None
    provider_base_url: str | None = Field(None, max_length=500)
    api_key: str | None = Field(None, max_length=1000, description="Plaintext — encrypted before storage")
    provider_type: str = Field(default="openai_compatible", max_length=50)
    model_id: str = Field(default="gpt-5.3-chat", max_length=200)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    is_active: bool = True


class UpdateAgentConfigRequest(BaseModel):
    provider_base_url: str | None = Field(None, max_length=500)
    api_key: str | None = Field(None, max_length=1000, description="Plaintext — encrypted before storage. Pass null to keep existing key.")
    provider_type: str | None = Field(None, max_length=50)
    model_id: str | None = Field(None, max_length=200)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=128000)
    is_active: bool | None = None


class AgentConfigResponse(BaseModel):
    id: str
    tenant_key: str
    agent_type_code: str
    org_id: str | None = None
    provider_base_url: str | None = None
    provider_type: str = "openai_compatible"
    has_api_key: bool  # Never return the actual key
    model_id: str
    temperature: float
    max_tokens: int
    is_active: bool
    created_at: str
    updated_at: str


class AgentConfigListResponse(BaseModel):
    items: list[AgentConfigResponse]
    total: int


class ResolvedConfigResponse(BaseModel):
    agent_type_code: str
    provider_type: str = "openai_compatible"
    provider_base_url: str | None = None
    model_id: str
    temperature: float
    max_tokens: int
    is_global: bool
