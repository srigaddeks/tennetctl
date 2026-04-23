"""Pydantic schemas for action templates and deliveries."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ActionTemplateBase(BaseModel):
    """Base schema for action template input/output."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    kind: str = Field(..., pattern="^(webhook|email|slack|ms_teams)$")
    target_url: Optional[str] = None
    target_address: Optional[str] = None
    body_template: str = Field(..., min_length=1)
    headers_template: dict = Field(default_factory=dict)
    signing_secret_vault_ref: Optional[str] = None
    retry_policy: Optional[dict] = Field(
        default_factory=lambda: {
            "max_attempts": 3,
            "base_seconds": 5,
            "max_seconds": 300,
        }
    )
    is_active: bool = True


class ActionTemplateCreate(ActionTemplateBase):
    """Schema for creating an action template."""

    pass


class ActionTemplateUpdate(BaseModel):
    """Schema for updating an action template."""

    name: Optional[str] = None
    description: Optional[str] = None
    body_template: Optional[str] = None
    headers_template: Optional[dict] = None
    signing_secret_vault_ref: Optional[str] = None
    retry_policy: Optional[dict] = None
    is_active: Optional[bool] = None


class ActionTemplate(ActionTemplateBase):
    """Full action template with metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    org_id: str
    kind_code: str
    kind_label: str
    success_rate_24h: float
    last_delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ActionDelivery(BaseModel):
    """Action delivery record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    template_id: str
    template_name: str
    alert_event_id: Optional[str] = None
    escalation_state_id: Optional[str] = None
    attempt: int
    status_code: Optional[int] = None
    status: str = Field(..., pattern="^(succeeded|failed|pending)$")
    response_excerpt: Optional[str] = None
    error_excerpt: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    succeeded_at: Optional[datetime] = None
    kind_code: str
    kind_label: str


class RenderRequest(BaseModel):
    """Request to render a template with variables."""

    template_id: str
    variables: dict = Field(default_factory=dict)


class RenderResponse(BaseModel):
    """Response from rendering a template."""

    rendered_body: str
    rendered_headers: dict
    payload_hash: str


class DispatchRequest(BaseModel):
    """Request to dispatch an action."""

    delivery_id: str
    template_id: str
    rendered_body: str
    rendered_headers: dict


class DispatchResult(BaseModel):
    """Result of a dispatch attempt."""

    success: bool
    status_code: Optional[int] = None
    response_excerpt: Optional[str] = None
    error_message: Optional[str] = None


class TestDispatchRequest(BaseModel):
    """Request to test dispatch a template with sample variables."""

    sample_variables: dict = Field(default_factory=dict)
