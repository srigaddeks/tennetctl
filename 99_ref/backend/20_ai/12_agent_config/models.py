from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfigRecord:
    id: str
    tenant_key: str
    agent_type_code: str
    org_id: str | None
    provider_base_url: str | None
    provider_type: str
    model_id: str
    temperature: float
    max_tokens: int
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ResolvedLLMConfig:
    """Resolved LLM config ready to use with get_provider()."""
    agent_type_code: str
    provider_type: str            # "openai" | "anthropic" | "azure_openai" | "openai_compatible"
    provider_base_url: str | None
    api_key: str | None
    model_id: str
    temperature: float
    max_tokens: int
    is_global: bool  # True if org had no override
