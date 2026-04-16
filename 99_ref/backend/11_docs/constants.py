from __future__ import annotations
from enum import StrEnum


class DocAuditEventType(StrEnum):
    UPLOADED = "uploaded"
    DOWNLOADED = "downloaded"
    DELETED = "deleted"
    DESCRIPTION_UPDATED = "description_updated"
    TAGS_UPDATED = "tags_updated"
    TITLE_UPDATED = "title_updated"
    VERSION_UPDATED = "version_updated"
    REPLACED = "replaced"
    REVERTED = "reverted"
    VIRUS_SCAN_COMPLETED = "virus_scan_completed"


VALID_SCOPES: frozenset[str] = frozenset({"global", "org"})

VALID_CATEGORIES: frozenset[str] = frozenset({
    "policy", "procedure", "framework_guide", "template",
    "reference", "compliance", "sandbox", "training", "other",
})

CACHE_TTL_DOCS = 300  # 5 minutes

PRESIGNED_URL_TTL_SECONDS = 3600  # 1 hour
