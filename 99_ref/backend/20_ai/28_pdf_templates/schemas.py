from __future__ import annotations

from pydantic import BaseModel, Field

COVER_STYLES = ("dark_navy", "light_minimal", "gradient_accent")


class CreatePdfTemplateRequest(BaseModel):
    name: str
    description: str | None = None
    cover_style: str = "dark_navy"
    primary_color: str = "#1e2a45"
    secondary_color: str = "#c9a96e"
    header_text: str | None = None
    footer_text: str | None = None
    prepared_by: str | None = None
    doc_ref_prefix: str | None = None
    classification_label: str | None = None
    applicable_report_types: list[str] = Field(default_factory=list)
    is_default: bool = False


class UpdatePdfTemplateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    cover_style: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    header_text: str | None = None
    footer_text: str | None = None
    prepared_by: str | None = None
    doc_ref_prefix: str | None = None
    classification_label: str | None = None
    applicable_report_types: list[str] | None = None
    is_default: bool | None = None


class PdfTemplateResponse(BaseModel):
    id: str
    tenant_key: str
    name: str
    description: str | None
    cover_style: str
    primary_color: str
    secondary_color: str
    header_text: str | None
    footer_text: str | None
    prepared_by: str | None
    doc_ref_prefix: str | None
    classification_label: str | None
    applicable_report_types: list[str]
    is_default: bool
    shell_file_key: str | None
    shell_file_name: str | None
    created_by: str
    created_at: str
    updated_at: str


class PdfTemplateListResponse(BaseModel):
    items: list[PdfTemplateResponse]
    total: int
