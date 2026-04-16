from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttachmentRecord:
    """Raw database record from 09_attachments.01_fct_attachments."""

    id: str
    tenant_key: str
    entity_type: str
    entity_id: str
    uploaded_by: str
    original_filename: str
    storage_key: str
    storage_provider: str
    storage_bucket: str
    storage_url: str | None
    content_type: str
    file_size_bytes: int
    checksum_sha256: str
    is_deleted: bool
    deleted_at: str | None
    deleted_by: str | None
    virus_scan_status: str
    virus_scan_at: str | None
    description: str | None
    auditor_access: bool
    published_for_audit_by: str | None
    published_for_audit_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DownloadRecord:
    """Raw database record from 09_attachments.02_trx_attachment_downloads."""

    id: str
    attachment_id: str
    downloaded_by: str
    downloaded_at: str
    client_ip: str | None
    user_agent: str | None
