from __future__ import annotations

from pydantic import BaseModel, Field


class GuardrailConfigResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str | None = None
    guardrail_type_code: str
    is_enabled: bool
    config_json: dict


class UpsertGuardrailConfigRequest(BaseModel):
    guardrail_type_code: str
    is_enabled: bool = True
    config_json: dict = Field(default_factory=dict)


class GuardrailEventResponse(BaseModel):
    id: str
    agent_run_id: str | None = None
    user_id: str
    tenant_key: str
    guardrail_type_code: str
    direction: str
    action_taken: str
    matched_pattern: str | None = None
    severity: str
    occurred_at: str


class GuardrailEventListResponse(BaseModel):
    items: list[GuardrailEventResponse]
    total: int
