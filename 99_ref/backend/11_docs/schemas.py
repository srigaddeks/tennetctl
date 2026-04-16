from __future__ import annotations
from pydantic import BaseModel, Field


class DocCategoryResponse(BaseModel):
    code: str
    name: str
    description: str | None = None
    sort_order: int
    is_active: bool


class DocumentResponse(BaseModel):
    id: str
    tenant_key: str
    scope: str
    org_id: str | None = None
    category_code: str
    category_name: str | None = None
    title: str
    description: str | None = None
    tags: list[str] = []
    version_label: str | None = None
    original_filename: str
    content_type: str
    file_size_bytes: int
    virus_scan_status: str
    is_visible: bool
    uploaded_by: str
    uploader_display_name: str | None = None
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class UploadDocumentResponse(BaseModel):
    document: DocumentResponse
    message: str = "Document uploaded successfully"


class PresignedDownloadResponse(BaseModel):
    document_id: str
    filename: str
    download_url: str
    expires_at: str
    content_type: str
    file_size_bytes: int


class UpdateDocumentRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    tags: list[str] | None = None
    version_label: str | None = None
    category_code: str | None = None
    is_visible: bool | None = None


class DocEventResponse(BaseModel):
    id: str
    event_type: str
    actor_user_id: str
    actor_display_name: str | None = None
    created_at: str
    metadata: dict


class DocHistoryResponse(BaseModel):
    items: list[DocEventResponse]
