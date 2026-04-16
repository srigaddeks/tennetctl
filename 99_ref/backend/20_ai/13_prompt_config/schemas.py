from __future__ import annotations

from pydantic import BaseModel, Field


class CreatePromptTemplateRequest(BaseModel):
    scope_code: str = Field(..., description="agent | feature | org")
    agent_type_code: str | None = None
    feature_code: str | None = None
    org_id: str | None = None
    prompt_text: str = Field(..., min_length=1)
    is_active: bool = True


class UpdatePromptTemplateRequest(BaseModel):
    prompt_text: str | None = Field(None, min_length=1)
    is_active: bool | None = None


class PromptTemplateResponse(BaseModel):
    id: str
    tenant_key: str
    scope_code: str
    agent_type_code: str | None = None
    feature_code: str | None = None
    org_id: str | None = None
    prompt_text: str
    version: int
    is_active: bool
    created_by: str | None = None
    created_at: str
    updated_at: str


class PromptTemplateListResponse(BaseModel):
    items: list[PromptTemplateResponse]
    total: int


class PromptPreviewRequest(BaseModel):
    agent_type_code: str
    feature_code: str | None = None
    org_id: str | None = None


class PromptPreviewResponse(BaseModel):
    agent_type_code: str
    feature_code: str | None = None
    org_id: str | None = None
    layers: list[dict]          # [{scope, template_id, prompt_text}]
    composed_prompt: str        # Final assembled prompt
    char_count: int
