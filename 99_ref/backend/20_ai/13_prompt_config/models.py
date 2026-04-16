from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplateRecord:
    id: str
    tenant_key: str
    scope_code: str
    agent_type_code: str | None
    feature_code: str | None
    org_id: str | None
    prompt_text: str
    version: int
    is_active: bool
    created_by: str | None
    created_at: str
    updated_at: str
