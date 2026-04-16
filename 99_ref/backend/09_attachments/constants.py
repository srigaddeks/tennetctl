from __future__ import annotations

from enum import StrEnum


class AttachmentAuditEventType(StrEnum):
    UPLOADED = "uploaded"
    DOWNLOADED = "downloaded"
    DELETED = "deleted"
    VIRUS_SCAN_COMPLETED = "virus_scan_completed"
    DESCRIPTION_UPDATED = "description_updated"
    STORAGE_CLEANUP_FAILED = "storage_cleanup_failed"
    GDPR_DATA_DELETED = "gdpr_data_deleted"


class AttachmentUnifiedAuditEventType(StrEnum):
    """Event types for the unified audit system (03_auth_manage.40_aud_events)."""
    ATTACHMENT_UPLOADED = "attachment_uploaded"
    ATTACHMENT_DOWNLOADED = "attachment_downloaded"
    ATTACHMENT_DELETED = "attachment_deleted"
    ATTACHMENT_DESCRIPTION_UPDATED = "attachment_description_updated"
    ATTACHMENT_STORAGE_CLEANUP_FAILED = "attachment_storage_cleanup_failed"
    ATTACHMENT_GDPR_DATA_DELETED = "attachment_gdpr_data_deleted"


class VirusScanStatus(StrEnum):
    PENDING = "pending"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"
    SKIPPED = "skipped"


# Entity types that support attachments
VALID_ENTITY_TYPES = frozenset({
    "task",
    "risk",
    "control",
    "framework",
    "evidence_template",
    "test",
    "comment",
    "feedback_ticket",
    "org",
    "workspace",
    "requirement",
    "engagement",
})

# Allowed MIME content types — comprehensive enterprise list
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({
    # Documents
    "application/pdf",
    "application/msword",                                                           # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",     # .docx
    "application/vnd.ms-excel",                                                    # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",           # .xlsx
    "application/vnd.ms-powerpoint",                                               # .ppt
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",   # .pptx
    "text/plain",                                                                  # .txt
    "text/csv",                                                                    # .csv
    "text/markdown",                                                               # .md
    "application/rtf",                                                             # .rtf
    "application/vnd.oasis.opendocument.text",                                     # .odt
    "application/vnd.oasis.opendocument.spreadsheet",                              # .ods
    "application/vnd.oasis.opendocument.presentation",                             # .odp
    # Images
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/bmp",
    "image/tiff",
    # Archives
    "application/zip",
    "application/x-zip-compressed",
    "application/x-tar",
    "application/gzip",
    "application/x-gzip",
    "application/x-bzip2",
    "application/x-7z-compressed",
    # Structured data / code
    "application/json",
    "application/yaml",
    "text/yaml",
    "application/xml",
    "text/xml",
    "text/html",
    # Video (with size limits enforced in service)
    "video/mp4",
    "video/quicktime",   # .mov
    "video/x-msvideo",  # .avi
    # Audio
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
})

# Extension → MIME mapping used for sniff validation
EXTENSION_CONTENT_TYPE_MAP: dict[str, str] = {
    ".pdf":   "application/pdf",
    ".doc":   "application/msword",
    ".docx":  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls":   "application/vnd.ms-excel",
    ".xlsx":  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt":   "application/vnd.ms-powerpoint",
    ".pptx":  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt":   "text/plain",
    ".csv":   "text/csv",
    ".md":    "text/markdown",
    ".rtf":   "application/rtf",
    ".jpg":   "image/jpeg",
    ".jpeg":  "image/jpeg",
    ".png":   "image/png",
    ".gif":   "image/gif",
    ".webp":  "image/webp",
    ".svg":   "image/svg+xml",
    ".bmp":   "image/bmp",
    ".tiff":  "image/tiff",
    ".zip":   "application/zip",
    ".tar":   "application/x-tar",
    ".gz":    "application/gzip",
    ".bz2":   "application/x-bzip2",
    ".7z":    "application/x-7z-compressed",
    ".json":  "application/json",
    ".yaml":  "application/yaml",
    ".yml":   "application/yaml",
    ".xml":   "application/xml",
    ".html":  "text/html",
    ".mp4":   "video/mp4",
    ".mov":   "video/quicktime",
    ".avi":   "video/x-msvideo",
    ".mp3":   "audio/mpeg",
    ".wav":   "audio/wav",
    ".ogg":   "audio/ogg",
}

# Default presigned URL expiry (seconds)
PRESIGNED_URL_TTL_SECONDS = 3600  # 1 hour

# Cache TTL for attachment lists
CACHE_TTL_ATTACHMENTS = 120  # 2 minutes

# Maximum file size allowed for uploads (in megabytes)
MAX_FILE_SIZE_DEFAULT_MB = 100

# Maximum number of files in a single bulk-upload request
MAX_BULK_UPLOAD_COUNT = 10

# Presigned URL expiry (seconds) — alias for clarity
PRESIGNED_URL_EXPIRY_SECONDS = 3600

# Rate limiting: downloads per user per minute
DOWNLOAD_RATE_LIMIT_PER_MINUTE = 60

# Threshold above which files are read in chunks to avoid OOM
CHUNKED_READ_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB

# Chunk size for incremental file reads (1 MB)
CHUNKED_READ_SIZE_BYTES = 1 * 1024 * 1024

# Default storage quota per tenant (10 GB)
DEFAULT_STORAGE_QUOTA_BYTES = 10 * 1024 * 1024 * 1024  # 10 GB per tenant
