from __future__ import annotations

from pydantic import BaseModel, Field


class CreateGlobalRiskRequest(BaseModel):
    risk_code: str = Field(..., min_length=1, max_length=100, pattern=r"^[A-Z0-9][A-Z0-9_\-]{0,98}[A-Z0-9]$")
    risk_category_code: str = Field(..., min_length=1, max_length=50)
    risk_level_code: str | None = None
    inherent_likelihood: int | None = Field(None, ge=1, le=5)
    inherent_impact: int | None = Field(None, ge=1, le=5)
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    short_description: str | None = None
    mitigation_guidance: str | None = None
    detection_guidance: str | None = None


class UpdateGlobalRiskRequest(BaseModel):
    risk_category_code: str | None = Field(None, min_length=1, max_length=50)
    risk_level_code: str | None = None
    inherent_likelihood: int | None = Field(None, ge=1, le=5)
    inherent_impact: int | None = Field(None, ge=1, le=5)
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    short_description: str | None = None
    mitigation_guidance: str | None = None
    detection_guidance: str | None = None


class GlobalRiskResponse(BaseModel):
    id: str
    tenant_key: str
    risk_code: str
    risk_category_code: str
    risk_category_name: str | None = None
    risk_level_code: str | None = None
    risk_level_name: str | None = None
    risk_level_color: str | None = None
    inherent_likelihood: int | None = None
    inherent_impact: int | None = None
    inherent_risk_score: int | None = None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None = None
    title: str | None = None
    description: str | None = None
    short_description: str | None = None
    mitigation_guidance: str | None = None
    detection_guidance: str | None = None
    linked_control_count: int = 0
    version: int = 1


class GlobalRiskListResponse(BaseModel):
    items: list[GlobalRiskResponse]
    total: int


class LinkControlRequest(BaseModel):
    control_id: str
    mapping_type: str = Field("mitigating", pattern=r"^(mitigating|compensating|related|detecting)$")


class LinkedControlResponse(BaseModel):
    id: str
    control_id: str
    mapping_type: str
    created_at: str


class DeployGlobalRisksRequest(BaseModel):
    global_risk_ids: list[str] = Field(..., min_length=1, max_length=200)


class RiskLibraryDeploymentResponse(BaseModel):
    id: str
    global_risk_id: str
    workspace_risk_id: str | None = None
    deployment_status: str
    is_active: bool
    created_at: str
    updated_at: str
    risk_code: str
    title: str | None = None
    short_description: str | None = None
    risk_category_code: str
    risk_category_name: str | None = None
    risk_level_code: str | None = None
    risk_level_name: str | None = None
    risk_level_color: str | None = None
    inherent_likelihood: int | None = None
    inherent_impact: int | None = None
    inherent_risk_score: int | None = None
    linked_control_count: int = 0


class RiskLibraryDeploymentListResponse(BaseModel):
    items: list[RiskLibraryDeploymentResponse]
    total: int


class DeployGlobalRisksResponse(BaseModel):
    deployed: int
    inserted: int
    skipped: int
    org_id: str
    workspace_id: str
