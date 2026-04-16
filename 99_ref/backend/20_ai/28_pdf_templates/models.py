from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfTemplateRecord:
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
