from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class AttachmentRecord:
    id: str
    conversation_id: str
    tenant_key: str
    user_id: str
    filename: str
    content_type: str
    file_size_bytes: int
    chunk_count: int
    ingest_status: str
    error_message: str | None
    qdrant_collection: str
    created_at: str
    updated_at: str
    # PageIndex fields — default to 'none' / None so older rows work before migration
    pageindex_status: str = field(default="none")
    pageindex_tree: dict | None = field(default=None)
    pageindex_error: str | None = field(default=None)
