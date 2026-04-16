from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    tenant_key: str
    scope: str
    org_id: str | None
    category_code: str
    category_name: str | None
    title: str
    description: str | None
    tags: list[str]
    version_label: str | None
    original_filename: str
    storage_key: str
    storage_provider: str
    storage_bucket: str
    storage_url: str | None
    content_type: str
    file_size_bytes: int
    checksum_sha256: str | None
    virus_scan_status: str
    virus_scan_at: str | None
    uploaded_by: str
    uploader_display_name: str | None
    is_visible: bool
    is_deleted: bool
    deleted_at: str | None
    deleted_by: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DocCategoryRecord:
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool


@dataclass(frozen=True)
class DocEventRecord:
    id: str
    document_id: str | None
    scope: str | None
    org_id: str | None
    event_type: str
    actor_user_id: str
    actor_display_name: str | None
    tenant_key: str
    metadata: dict
    created_at: str
