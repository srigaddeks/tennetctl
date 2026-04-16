from __future__ import annotations
from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: str
    conversation_id: str
    filename: str
    content_type: str
    file_size_bytes: int
    chunk_count: int
    ingest_status: str
    error_message: str | None = None
    created_at: str
    # PageIndex
    pageindex_status: str = "none"   # none | indexing | ready | failed
    pageindex_error: str | None = None
    # pageindex_tree is NOT returned to the client (can be large / sensitive)


class AttachmentListResponse(BaseModel):
    items: list[AttachmentResponse]
    total: int
