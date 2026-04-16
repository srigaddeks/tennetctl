from __future__ import annotations

from pydantic import BaseModel, Field

from ..schemas import (
    CreateTemplateRequest,
    CreateTemplateVersionRequest,
    PreviewTemplateRequest,
    PreviewTemplateResponse,
    RenderRawRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateVersionResponse,
)


class UpdateTemplateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    is_disabled: bool | None = None
    active_version_id: str | None = None
    static_variables: dict[str, str] | None = None


class TemplateDetailResponse(BaseModel):
    """Single template with embedded versions."""

    id: str
    tenant_key: str
    code: str
    name: str
    description: str
    notification_type_code: str
    channel_code: str
    category_code: str | None = None
    active_version_id: str | None = None
    base_template_id: str | None = None
    org_id: str | None = None
    static_variables: dict[str, str] = Field(default_factory=dict)
    is_active: bool
    is_system: bool
    created_at: str
    updated_at: str
    versions: list[TemplateVersionResponse]


__all__ = [
    "CreateTemplateRequest",
    "CreateTemplateVersionRequest",
    "PreviewTemplateRequest",
    "PreviewTemplateResponse",
    "RenderRawRequest",
    "TemplateDetailResponse",
    "TemplateListResponse",
    "TemplateResponse",
    "TemplateVersionResponse",
    "UpdateTemplateRequest",
]
