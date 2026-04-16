"""Business logic for the attachments domain.

Architecture:
- Storage upload happens BEFORE the database write.  On DB failure the
  uploaded object is cleaned up from storage automatically.
- Filenames are sanitised to prevent path traversal and null-byte injection.
- Content-type is normalised from declared MIME type; callers should never
  rely solely on the browser-supplied value.
- All mutations run inside ``self._database_pool.transaction()``.
- Storage errors (provider down) are raised as ``ServiceUnavailableError``
  so the router can return 503 to the client.
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from importlib import import_module
from pathlib import PurePosixPath

from opentelemetry import metrics as otel_metrics

from .repository import AttachmentRepository
from .schemas import (
    AttachmentCountsResponse,
    AttachmentListResponse,
    AttachmentResponse,
    BulkUploadResponse,
    DownloadHistoryItem,
    DownloadHistoryResponse,
    PresignedDownloadResponse,
    StorageHealthResponse,
    UpdateAttachmentRequest,
    UploadAttachmentResponse,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.09_attachments.constants")
_storage_module = import_module("backend.09_attachments.storage")
_auth_constants_module = import_module("backend.03_auth_manage.constants")
_access_scope_module = import_module("backend.07_tasks.access_scope")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuthorizationError = _errors_module.AuthorizationError
ServiceUnavailableError = _errors_module.ServiceUnavailableError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
utc_now_sql = _time_module.utc_now_sql

AttachmentAuditEventType = _constants_module.AttachmentAuditEventType
AttachmentUnifiedAuditEventType = _constants_module.AttachmentUnifiedAuditEventType
VirusScanStatus = _constants_module.VirusScanStatus
VALID_ENTITY_TYPES = _constants_module.VALID_ENTITY_TYPES
ALLOWED_CONTENT_TYPES = _constants_module.ALLOWED_CONTENT_TYPES
PRESIGNED_URL_TTL_SECONDS = _constants_module.PRESIGNED_URL_TTL_SECONDS
CACHE_TTL_ATTACHMENTS = _constants_module.CACHE_TTL_ATTACHMENTS
CHUNKED_READ_THRESHOLD_BYTES = _constants_module.CHUNKED_READ_THRESHOLD_BYTES
CHUNKED_READ_SIZE_BYTES = _constants_module.CHUNKED_READ_SIZE_BYTES
DEFAULT_STORAGE_QUOTA_BYTES = _constants_module.DEFAULT_STORAGE_QUOTA_BYTES
get_storage_provider = _storage_module.get_storage_provider
AuditEventCategory = _auth_constants_module.AuditEventCategory
assert_assignee_task_entity_access = _access_scope_module.assert_assignee_task_entity_access
is_assignee_portal_mode = _access_scope_module.is_assignee_portal_mode

# ---------------------------------------------------------------------------
# OTEL Metrics
# ---------------------------------------------------------------------------

_attachment_meter = otel_metrics.get_meter("kcontrol.attachments")

attachment_uploaded_counter = _attachment_meter.create_counter(
    "attachments.uploaded",
    description="Number of attachments uploaded",
    unit="1",
)
attachment_upload_size = _attachment_meter.create_histogram(
    "attachments.upload_size_bytes",
    description="Size of uploaded attachments in bytes",
    unit="By",
)
attachment_downloaded_counter = _attachment_meter.create_counter(
    "attachments.downloaded",
    description="Number of attachment downloads",
    unit="1",
)
attachment_deleted_counter = _attachment_meter.create_counter(
    "attachments.deleted",
    description="Number of attachments deleted",
    unit="1",
)
storage_error_counter = _attachment_meter.create_counter(
    "attachments.storage_errors",
    description="Number of storage provider errors",
    unit="1",
)

# Maximum files accepted in a single bulk-upload request
_MAX_BULK_FILES = 10
# Maximum entity IDs accepted by the counts endpoint
_MAX_COUNT_ENTITY_IDS = 100

# Null bytes (ASCII and Unicode variants) — blocked in filenames
_NULL_BYTE_RE = re.compile(r"[\x00\u0000]")
# Characters not in the safe set for filenames
_UNSAFE_CHARS = re.compile(r"[^\w\-. ]", re.UNICODE)
# Double-dot path traversal in any form
_PATH_TRAVERSAL = re.compile(r"(\.\.[\\/]|^[\\/]|[\\/]\.\.)", re.UNICODE)


def _sanitize_filename(filename: str) -> str:
    """Return a safe filename stripped of all path traversal and injection vectors.

    Steps:
    1. Remove null bytes (prevents certain HTTP parser tricks).
    2. Strip Windows and Unix directory separators to get the basename only.
    3. Remove leading dots (prevents dotfile-only names like ``..``).
    4. Replace remaining unsafe characters with underscores.
    5. Clamp to 200 characters.
    6. Fall back to ``"attachment"`` if the result is empty.
    """
    # 1. Strip null bytes
    filename = _NULL_BYTE_RE.sub("", filename)
    # 2. Normalise path separators and extract basename
    name = os.path.basename(filename.replace("\\", "/"))
    # 3. Guard against pure traversal names like ".." or "..."
    if _PATH_TRAVERSAL.search(name):
        name = name.replace("..", "_")
    # 4. Strip leading dots (hidden-file protection)
    name = name.lstrip(".")
    # 5. Replace unsafe chars
    name = _UNSAFE_CHARS.sub("_", name)
    name = name.strip("_").strip()
    # 6. Fallback
    if not name:
        name = "attachment"
    return name[:200]


def _build_storage_key(
    tenant_key: str,
    entity_type: str,
    entity_id: str,
    attachment_id: str,
    filename: str,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> str:
    """Build a structured, safe object storage key.

    Path layout (when org/workspace provided):
        {tenant}/{org_id}/{workspace_id}/{entity_type}/{entity_id}/{attachment_id}/{filename}
    Fallback (legacy / no org context):
        {tenant}/{entity_type}/{entity_id}/{attachment_id}/{filename}

    The ``attachment_id`` (UUID) component guarantees uniqueness and prevents
    user-controlled collisions.  ``tenant_key`` is treated as a path segment
    and must not contain slashes — strip them defensively.
    """
    safe_tenant = tenant_key.replace("/", "_").replace("\\", "_")
    safe_filename = _sanitize_filename(filename)
    if org_id and workspace_id:
        return f"{safe_tenant}/{org_id}/{workspace_id}/{entity_type}/{entity_id}/{attachment_id}/{safe_filename}"
    if org_id:
        return f"{safe_tenant}/{org_id}/{entity_type}/{entity_id}/{attachment_id}/{safe_filename}"
    return f"{safe_tenant}/{entity_type}/{entity_id}/{attachment_id}/{safe_filename}"


def _build_storage_url(account_name: str, container: str, storage_key: str) -> str:
    """Build the canonical Azure blob URL for a storage key."""
    return f"https://{account_name}.blob.core.windows.net/{container}/{storage_key}"


@instrument_class_methods(
    namespace="attachments.service",
    logger_name="backend.attachments.instrumentation",
)
class AttachmentService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AttachmentRepository()
        # Unified audit writer — attachments use 03_auth_manage schema for audit
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.attachments")

    async def _assert_entity_access_for_portal(
        self,
        conn,
        *,
        portal_mode: str | None,
        user_id: str,
        entity_type: str,
        entity_id: str,
    ) -> None:
        await assert_assignee_task_entity_access(
            conn,
            portal_mode=portal_mode,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )

    # ------------------------------------------------------------------
    # List attachments for an entity
    # ------------------------------------------------------------------

    async def list_attachments(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        engagement_id: str | None = None,
        auditor_only: bool = False,
        viewer_membership_id: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> AttachmentListResponse:
        if not engagement_id and entity_type not in VALID_ENTITY_TYPES:
            raise ValidationError(
                f"Invalid entity_type '{entity_type}'. Valid types: {sorted(VALID_ENTITY_TYPES)}"
            )

        limit = max(1, min(per_page, 200))
        offset = max(0, (page - 1) * limit)

        cache_key = f"attachments:{engagement_id or 'all'}:{entity_type or 'all'}:{entity_id or 'all'}:p{page}:{limit}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return AttachmentListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            if not engagement_id and entity_type and entity_id:
                await self._assert_entity_access_for_portal(
                    conn,
                    portal_mode=portal_mode,
                    user_id=user_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
            records, total = await self._repository.list_attachments(
                conn,
                tenant_key=tenant_key,
                entity_type=entity_type,
                entity_id=entity_id,
                engagement_id=engagement_id,
                auditor_only=auditor_only,
                viewer_membership_id=viewer_membership_id,
                limit=limit,
                offset=offset,
            )
            # Batch-fetch uploader display names
            uploader_ids = list({r.uploaded_by for r in records})
            display_names = await self._repository.get_user_display_names_batch(conn, uploader_ids)

        items = [
            _attachment_response(r, uploader_display_name=display_names.get(r.uploaded_by))
            for r in records
        ]
        result = AttachmentListResponse(items=items, total=total)
        await self._cache.set(cache_key, result.model_dump_json(), CACHE_TTL_ATTACHMENTS)
        return result

    # ------------------------------------------------------------------
    # Get single attachment metadata
    # ------------------------------------------------------------------

    async def get_attachment(
        self,
        *,
        user_id: str,
        attachment_id: str,
        portal_mode: str | None = None,
    ) -> AttachmentResponse:
        cache_key = f"attachment:{attachment_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return AttachmentResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_attachment_by_id(conn, attachment_id)
            if record is None:
                raise NotFoundError("Attachment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
            )
            display_name = await self._repository.get_user_display_name(conn, record.uploaded_by)

        result = _attachment_response(record, uploader_display_name=display_name)
        await self._cache.set(cache_key, result.model_dump_json(), CACHE_TTL_ATTACHMENTS)
        return result

    # ------------------------------------------------------------------
    # Upload (single file)
    # ------------------------------------------------------------------

    async def upload_attachment(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        entity_type: str,
        entity_id: str,
        description: str | None,
        original_filename: str,
        declared_content_type: str,
        file_data: bytes,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> UploadAttachmentResponse:
        if entity_type not in VALID_ENTITY_TYPES:
            raise ValidationError(
                f"Invalid entity_type '{entity_type}'. Valid types: {sorted(VALID_ENTITY_TYPES)}"
            )

        async with self._database_pool.acquire() as conn:
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
            )

        max_bytes = self._settings.storage_max_file_size_mb * 1024 * 1024
        if len(file_data) > max_bytes:
            raise ValidationError(
                f"File size {len(file_data):,} bytes exceeds the "
                f"{self._settings.storage_max_file_size_mb} MB maximum."
            )

        # Storage quota enforcement
        await self._check_storage_quota(tenant_key, len(file_data))

        effective_content_type = _resolve_content_type(declared_content_type, original_filename)
        if effective_content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                "This file type is not permitted. Allowed types include documents, "
                "images, archives, and structured data files."
            )

        checksum = hashlib.sha256(file_data).hexdigest()
        attachment_id = str(uuid.uuid4())
        storage_key = _build_storage_key(
            tenant_key, entity_type, entity_id, attachment_id, original_filename,
            org_id=org_id, workspace_id=workspace_id,
        )

        # Upload to storage FIRST — only write DB if upload succeeds.
        # Storage failures surface as ServiceUnavailableError (503).
        storage_provider = get_storage_provider(self._settings)
        try:
            upload_result = await storage_provider.upload(
                file_data=file_data,
                storage_key=storage_key,
                content_type=effective_content_type,
                metadata={
                    "tenant_key": tenant_key,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "uploaded_by": user_id,
                    "original_filename": _sanitize_filename(original_filename),
                    "attachment_id": attachment_id,
                },
            )
        except Exception as exc:
            storage_error_counter.add(1, {"provider": "object_storage", "operation": "upload"})
            self._logger.error(
                "attachment_storage_upload_failed",
                extra={
                    "action": "attachments.upload.storage",
                    "outcome": "error",
                    "error": str(exc),
                },
            )
            raise ServiceUnavailableError(
                "The file storage service is temporarily unavailable. Please try again later."
            ) from exc

        # Build the canonical blob URL if using Azure
        storage_url: str | None = None
        if self._settings.storage_provider == "azure" and self._settings.storage_azure_account_name:
            storage_url = _build_storage_url(
                self._settings.storage_azure_account_name,
                self._settings.storage_azure_container,
                storage_key,
            )

        now = utc_now_sql()
        try:
            async with self._database_pool.transaction() as conn:
                record = await self._repository.create_attachment(
                    conn,
                    attachment_id=attachment_id,
                    tenant_key=tenant_key,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    uploaded_by=user_id,
                    original_filename=_sanitize_filename(original_filename),
                    storage_key=upload_result.storage_key,
                    storage_provider=upload_result.storage_provider,
                    storage_bucket=upload_result.storage_bucket,
                    storage_url=storage_url,
                    content_type=upload_result.content_type,
                    file_size_bytes=upload_result.file_size_bytes,
                    checksum_sha256=upload_result.checksum_sha256,
                    description=description,
                    now=now,
                )
                await self._repository.write_audit_event(
                    conn,
                    event_id=str(uuid.uuid4()),
                    attachment_id=attachment_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    event_type=AttachmentAuditEventType.UPLOADED.value,
                    actor_user_id=user_id,
                    tenant_key=tenant_key,
                    metadata={
                        "original_filename": _sanitize_filename(original_filename),
                        "content_type": effective_content_type,
                        "file_size_bytes": upload_result.file_size_bytes,
                        "storage_provider": upload_result.storage_provider,
                        "checksum_sha256": checksum,
                    },
                    now=now,
                )
                # Unified audit
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="attachment",
                        entity_id=attachment_id,
                        event_type=AttachmentUnifiedAuditEventType.ATTACHMENT_UPLOADED.value,
                        event_category=AuditEventCategory.ATTACHMENT.value,
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "original_filename": _sanitize_filename(original_filename),
                            "content_type": effective_content_type,
                            "file_size_bytes": str(upload_result.file_size_bytes),
                            "parent_entity_type": entity_type,
                            "parent_entity_id": entity_id,
                        },
                    ),
                )
        except Exception:
            # Rollback: remove the already-uploaded object from storage
            try:
                await storage_provider.delete(storage_key)
            except Exception as cleanup_exc:
                self._logger.warning(
                    "attachment_storage_cleanup_failed",
                    extra={
                        "action": "attachments.upload.cleanup",
                        "outcome": "error",
                        "storage_key": storage_key,
                        "error": str(cleanup_exc),
                    },
                )
            raise

        await self._cache.delete_pattern(f"attachments:{entity_type}:{entity_id}:*")

        # OTEL metrics
        metric_attrs = {"entity_type": entity_type, "tenant_key": tenant_key, "content_type": effective_content_type}
        attachment_uploaded_counter.add(1, metric_attrs)
        attachment_upload_size.record(len(file_data), metric_attrs)

        return UploadAttachmentResponse(
            id=record.id,
            tenant_key=record.tenant_key,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            uploaded_by=record.uploaded_by,
            original_filename=record.original_filename,
            storage_provider=record.storage_provider,
            storage_bucket=record.storage_bucket,
            storage_url=record.storage_url,
            content_type=record.content_type,
            file_size_bytes=record.file_size_bytes,
            checksum_sha256=record.checksum_sha256,
            virus_scan_status=_present_virus_scan_status(record.virus_scan_status),
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    # ------------------------------------------------------------------
    # Bulk upload (up to _MAX_BULK_FILES files per request)
    # ------------------------------------------------------------------

    async def bulk_upload_attachments(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        entity_type: str,
        entity_id: str,
        files: list[dict],  # list of {filename, content_type, data, description}
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> BulkUploadResponse:
        """Upload up to ``_MAX_BULK_FILES`` files in one call.

        Each file is processed independently — a failure on one file does not
        block the others.  The caller receives a ``failed`` list with per-file
        error messages.
        """
        if not files:
            return BulkUploadResponse(
                uploaded=[], failed=[], total_uploaded=0, total_failed=0
            )
        if len(files) > _MAX_BULK_FILES:
            raise ValidationError(
                f"Too many files. Maximum {_MAX_BULK_FILES} files per request."
            )

        uploaded: list[UploadAttachmentResponse] = []
        failed: list[dict] = []

        for file_info in files:
            filename = file_info.get("filename", "attachment")
            try:
                result = await self.upload_attachment(
                    user_id=user_id,
                    tenant_key=tenant_key,
                    portal_mode=portal_mode,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    description=file_info.get("description"),
                    original_filename=filename,
                    declared_content_type=file_info.get("content_type", "application/octet-stream"),
                    file_data=file_info["data"],
                    org_id=org_id,
                    workspace_id=workspace_id,
                )
                uploaded.append(result)
            except Exception as exc:
                # Surface a user-friendly message; do not expose internal details
                error_msg = str(exc) if isinstance(exc, (ValidationError, ServiceUnavailableError)) else "Upload failed."
                failed.append({"filename": _sanitize_filename(filename), "error": error_msg})
                self._logger.warning(
                    "bulk_upload_file_failed",
                    extra={
                        "action": "attachments.bulk_upload",
                        "outcome": "error",
                        "filename": _sanitize_filename(filename),
                        "error": str(exc),
                    },
                )

        return BulkUploadResponse(
            uploaded=uploaded,
            failed=failed,
            total_uploaded=len(uploaded),
            total_failed=len(failed),
        )

    # ------------------------------------------------------------------
    # Generate presigned download URL
    # ------------------------------------------------------------------

    async def get_download_url(
        self,
        *,
        user_id: str,
        attachment_id: str,
        portal_mode: str | None = None,
        client_ip: str | None,
        user_agent: str | None,
    ) -> PresignedDownloadResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_attachment_by_id(conn, attachment_id)
            if record is None:
                raise NotFoundError("Attachment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
            )

        # Generate presigned URL
        storage_provider = get_storage_provider(self._settings)
        try:
            presigned = await storage_provider.generate_presigned_download_url(
                storage_key=record.storage_key,
                filename=record.original_filename,
                expires_seconds=PRESIGNED_URL_TTL_SECONDS,
            )
        except Exception as exc:
            storage_error_counter.add(1, {"provider": "object_storage", "operation": "presign"})
            self._logger.error(
                "attachment_presign_failed",
                extra={
                    "action": "attachments.download.presign",
                    "outcome": "error",
                    "attachment_id": attachment_id,
                    "error": str(exc),
                },
            )
            raise ServiceUnavailableError(
                "The file storage service is temporarily unavailable. Please try again later."
            ) from exc

        # Record download event — non-fatal if this errors
        now = utc_now_sql()
        download_id = str(uuid.uuid4())
        try:
            async with self._database_pool.acquire() as conn:
                await self._repository.record_download(
                    conn,
                    download_id=download_id,
                    attachment_id=attachment_id,
                    downloaded_by=user_id,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    now=now,
                )
                await self._repository.write_audit_event(
                    conn,
                    event_id=str(uuid.uuid4()),
                    attachment_id=attachment_id,
                    entity_type=record.entity_type,
                    entity_id=record.entity_id,
                    event_type=AttachmentAuditEventType.DOWNLOADED.value,
                    actor_user_id=user_id,
                    tenant_key=record.tenant_key,
                    metadata={
                        "download_id": download_id,
                        "client_ip": client_ip or "",
                        "original_filename": record.original_filename,
                    },
                    now=now,
                )
                # Unified audit
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=record.tenant_key,
                        entity_type="attachment",
                        entity_id=attachment_id,
                        event_type=AttachmentUnifiedAuditEventType.ATTACHMENT_DOWNLOADED.value,
                        event_category=AuditEventCategory.ATTACHMENT.value,
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        ip_address=client_ip,
                        properties={
                            "download_id": download_id,
                            "original_filename": record.original_filename,
                        },
                    ),
                )
        except Exception as exc:
            self._logger.warning(
                "attachment_download_tracking_failed",
                extra={
                    "action": "attachments.download.tracking",
                    "outcome": "error",
                    "attachment_id": attachment_id,
                    "error": str(exc),
                },
            )

        # OTEL metrics
        attachment_downloaded_counter.add(1, {"entity_type": record.entity_type, "tenant_key": record.tenant_key})

        return PresignedDownloadResponse(
            url=presigned.url,
            expires_at=presigned.expires_at.isoformat(),
            filename=record.original_filename,
            attachment_id=attachment_id,
            content_type=record.content_type,
            file_size_bytes=record.file_size_bytes,
        )

    # ------------------------------------------------------------------
    # Update description
    # ------------------------------------------------------------------

    async def update_attachment(
        self,
        *,
        user_id: str,
        attachment_id: str,
        request: UpdateAttachmentRequest,
        portal_mode: str | None = None,
    ) -> AttachmentResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_attachment_by_id(conn, attachment_id)
            if existing is None:
                raise NotFoundError("Attachment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            record = await self._repository.update_description(
                conn, attachment_id, description=request.description, now=now
            )
            if record is None:
                raise NotFoundError("Attachment not found.")

            # Handle auditor_access toggle if provided
            if request.auditor_access is not None and request.auditor_access != existing.auditor_access:
                record = await self._repository.set_auditor_access(
                    conn, attachment_id,
                    auditor_access=request.auditor_access,
                    actor_id=user_id,
                    now=now,
                )

            await self._repository.write_audit_event(
                conn,
                event_id=str(uuid.uuid4()),
                attachment_id=attachment_id,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                event_type=AttachmentAuditEventType.DESCRIPTION_UPDATED.value,
                actor_user_id=user_id,
                tenant_key=record.tenant_key,
                metadata={"description": request.description or "", "auditor_access": str(record.auditor_access)},
                now=now,
            )
            # Unified audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=record.tenant_key,
                    entity_type="attachment",
                    entity_id=attachment_id,
                    event_type=AttachmentUnifiedAuditEventType.ATTACHMENT_DESCRIPTION_UPDATED.value,
                    event_category=AuditEventCategory.ATTACHMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "parent_entity_type": record.entity_type,
                        "parent_entity_id": record.entity_id,
                    },
                ),
            )

        await self._cache.delete(f"attachment:{attachment_id}")
        await self._cache.delete_pattern(f"attachments:{record.entity_type}:{record.entity_id}:*")

        async with self._database_pool.acquire() as conn:
            updated = await self._repository.get_attachment_by_id(conn, attachment_id)
            display_name = await self._repository.get_user_display_name(conn, updated.uploaded_by)
        return _attachment_response(updated, uploader_display_name=display_name)

    # ------------------------------------------------------------------
    # Delete (soft delete + storage removal)
    # ------------------------------------------------------------------

    async def delete_attachment(
        self,
        *,
        user_id: str,
        attachment_id: str,
        portal_mode: str | None = None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_attachment_by_id(conn, attachment_id)
            if record is None:
                raise NotFoundError("Attachment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
            )

        async with self._database_pool.transaction() as conn:
            deleted = await self._repository.soft_delete_attachment(
                conn, attachment_id, deleted_by=user_id, now=now
            )
            if not deleted:
                raise NotFoundError("Attachment not found.")

            await self._repository.write_audit_event(
                conn,
                event_id=str(uuid.uuid4()),
                attachment_id=attachment_id,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                event_type=AttachmentAuditEventType.DELETED.value,
                actor_user_id=user_id,
                tenant_key=record.tenant_key,
                metadata={
                    "original_filename": record.original_filename,
                    "storage_key": record.storage_key,
                },
                now=now,
            )
            # Unified audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=record.tenant_key,
                    entity_type="attachment",
                    entity_id=attachment_id,
                    event_type=AttachmentUnifiedAuditEventType.ATTACHMENT_DELETED.value,
                    event_category=AuditEventCategory.ATTACHMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "original_filename": record.original_filename,
                        "parent_entity_type": record.entity_type,
                        "parent_entity_id": record.entity_id,
                    },
                ),
            )

        # OTEL metrics
        attachment_deleted_counter.add(1, {"entity_type": record.entity_type, "tenant_key": record.tenant_key})

        # Remove from object storage — best effort; DB is already soft-deleted
        try:
            storage_provider = get_storage_provider(self._settings)
            await storage_provider.delete(record.storage_key)
        except Exception as exc:
            storage_error_counter.add(1, {"provider": "object_storage", "operation": "delete"})
            self._logger.warning(
                "attachment_storage_delete_failed",
                extra={
                    "action": "attachments.delete.storage",
                    "outcome": "error",
                    "storage_key": record.storage_key,
                    "attachment_id": attachment_id,
                    "error": str(exc),
                },
            )
            # Write audit event noting storage cleanup failure (non-fatal)
            try:
                cleanup_now = utc_now_sql()
                async with self._database_pool.acquire() as conn:
                    await self._repository.write_audit_event(
                        conn,
                        event_id=str(uuid.uuid4()),
                        attachment_id=attachment_id,
                        entity_type=record.entity_type,
                        entity_id=record.entity_id,
                        event_type=AttachmentAuditEventType.STORAGE_CLEANUP_FAILED.value,
                        actor_user_id=user_id,
                        tenant_key=record.tenant_key,
                        metadata={
                            "storage_key": record.storage_key,
                            "error": str(exc),
                        },
                        now=cleanup_now,
                    )
                    await self._audit_writer.write_entry(
                        conn,
                        AuditEntry(
                            id=str(uuid.uuid4()),
                            tenant_key=record.tenant_key,
                            entity_type="attachment",
                            entity_id=attachment_id,
                            event_type=AttachmentUnifiedAuditEventType.ATTACHMENT_STORAGE_CLEANUP_FAILED.value,
                            event_category=AuditEventCategory.ATTACHMENT.value,
                            occurred_at=cleanup_now,
                            actor_id=user_id,
                            actor_type="user",
                            properties={
                                "storage_key": record.storage_key,
                                "error": str(exc),
                            },
                        ),
                    )
            except Exception as audit_exc:
                self._logger.warning(
                    "attachment_storage_cleanup_audit_failed",
                    extra={
                        "action": "attachments.delete.storage.audit",
                        "outcome": "error",
                        "attachment_id": attachment_id,
                        "error": str(audit_exc),
                    },
                )

        await self._cache.delete(f"attachment:{attachment_id}")
        await self._cache.delete_pattern(f"attachments:{record.entity_type}:{record.entity_id}:*")

    # ------------------------------------------------------------------
    # Download history (admin)
    # ------------------------------------------------------------------

    async def get_download_history(
        self,
        *,
        user_id: str,
        attachment_id: str,
        portal_mode: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> DownloadHistoryResponse:
        limit = max(1, min(per_page, 200))
        offset = max(0, (page - 1) * limit)

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_attachment_including_deleted(conn, attachment_id)
            if record is None:
                raise NotFoundError("Attachment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
            )

            downloads, total = await self._repository.list_downloads(
                conn, attachment_id, limit=limit, offset=offset
            )

        items = [
            DownloadHistoryItem(
                id=d.id,
                attachment_id=d.attachment_id,
                downloaded_by=d.downloaded_by,
                downloaded_at=d.downloaded_at,
                client_ip=d.client_ip,
                user_agent=d.user_agent,
            )
            for d in downloads
        ]
        return DownloadHistoryResponse(items=items, total=total)

    # ------------------------------------------------------------------
    # Attachment counts (for list-page badges)
    # ------------------------------------------------------------------

    async def get_attachment_counts(
        self,
        *,
        user_id: str,
        portal_mode: str | None = None,
        entity_type: str,
        entity_ids: list[str],
    ) -> AttachmentCountsResponse:
        if entity_type not in VALID_ENTITY_TYPES:
            raise ValidationError(
                f"Invalid entity_type '{entity_type}'. Valid types: {sorted(VALID_ENTITY_TYPES)}"
            )
        if not entity_ids:
            return AttachmentCountsResponse(counts={})
        if len(entity_ids) > _MAX_COUNT_ENTITY_IDS:
            raise ValidationError(
                f"Too many entity IDs. Maximum is {_MAX_COUNT_ENTITY_IDS}."
            )

        async with self._database_pool.acquire() as conn:
            if is_assignee_portal_mode(portal_mode):
                if entity_type != "task":
                    raise AuthorizationError("Assignee portal can only access task entities.")
                for entity_id in entity_ids:
                    await self._assert_entity_access_for_portal(
                        conn,
                        portal_mode=portal_mode,
                        user_id=user_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                    )
            counts = await self._repository.get_attachment_counts_batch(
                conn,
                entity_type=entity_type,
                entity_ids=entity_ids,
            )
        return AttachmentCountsResponse(counts=counts)

    # ------------------------------------------------------------------
    # Storage health check (ops endpoint)
    # ------------------------------------------------------------------

    async def check_storage_health(self) -> StorageHealthResponse:
        """Verify connectivity to the configured storage provider."""
        storage_provider = get_storage_provider(self._settings)
        result = await storage_provider.health_check()
        return StorageHealthResponse(
            provider=result.provider,
            status="ok" if result.healthy else "error",
            latency_ms=result.latency_ms,
            error=result.error,
        )

    # ------------------------------------------------------------------
    # Chunked file reading (avoids OOM for large files)
    # ------------------------------------------------------------------

    @staticmethod
    async def _read_file_chunked(upload_file) -> tuple[bytes, str]:
        """Read an UploadFile in chunks, computing SHA-256 incrementally.

        For files under CHUNKED_READ_THRESHOLD_BYTES, reads the entire file at
        once.  For larger files, reads in CHUNKED_READ_SIZE_BYTES increments to
        avoid loading 100 MB+ files fully into memory at once.

        Returns (file_data, sha256_hex).
        """
        hasher = hashlib.sha256()
        # Read first chunk to decide strategy
        first_chunk = await upload_file.read(CHUNKED_READ_THRESHOLD_BYTES + 1)

        if len(first_chunk) <= CHUNKED_READ_THRESHOLD_BYTES:
            # Small file — already fully read
            hasher.update(first_chunk)
            return first_chunk, hasher.hexdigest()

        # Large file — read in chunks and accumulate
        chunks = [first_chunk]
        hasher.update(first_chunk)
        while True:
            chunk = await upload_file.read(CHUNKED_READ_SIZE_BYTES)
            if not chunk:
                break
            chunks.append(chunk)
            hasher.update(chunk)

        return b"".join(chunks), hasher.hexdigest()

    # ------------------------------------------------------------------
    # Storage quota
    # ------------------------------------------------------------------

    async def _check_storage_quota(self, tenant_key: str, new_file_size: int) -> None:
        """Check if upload would exceed org storage quota."""
        async with self._database_pool.acquire() as conn:
            usage = await self._repository.get_org_storage_usage(conn, tenant_key)

            # Default quota — can be overridden by org settings
            quota_bytes = DEFAULT_STORAGE_QUOTA_BYTES

            try:
                row = await conn.fetchrow(
                    """
                    SELECT setting_value FROM "03_auth_manage"."30_dtl_org_settings"
                    WHERE entity_id = (
                        SELECT id FROM "03_auth_manage"."29_fct_orgs"
                        WHERE tenant_key = $1 AND is_active = TRUE LIMIT 1
                    )
                    AND setting_key = 'storage_quota_bytes'
                    """,
                    tenant_key,
                )
                if row:
                    quota_bytes = int(row["setting_value"])
            except Exception:
                pass  # Use default quota

        if usage["total_bytes"] + new_file_size > quota_bytes:
            raise ValidationError(
                f"Storage quota exceeded. Used: {usage['total_bytes']} bytes, "
                f"Quota: {quota_bytes} bytes, "
                f"Requested: {new_file_size} bytes"
            )

    async def get_storage_usage(self, *, tenant_key: str) -> dict:
        """Return storage usage and quota for a tenant."""
        async with self._database_pool.acquire() as conn:
            usage = await self._repository.get_org_storage_usage(conn, tenant_key)

            quota_bytes = DEFAULT_STORAGE_QUOTA_BYTES
            try:
                row = await conn.fetchrow(
                    """
                    SELECT setting_value FROM "03_auth_manage"."30_dtl_org_settings"
                    WHERE entity_id = (
                        SELECT id FROM "03_auth_manage"."29_fct_orgs"
                        WHERE tenant_key = $1 AND is_active = TRUE LIMIT 1
                    )
                    AND setting_key = 'storage_quota_bytes'
                    """,
                    tenant_key,
                )
                if row:
                    quota_bytes = int(row["setting_value"])
            except Exception:
                pass

        total_bytes = usage["total_bytes"]
        usage_percent = round((total_bytes / quota_bytes) * 100, 2) if quota_bytes > 0 else 0.0

        return {
            "tenant_key": tenant_key,
            "total_bytes": total_bytes,
            "file_count": usage["total_files"],
            "quota_bytes": quota_bytes,
            "usage_percent": usage_percent,
        }

    # ------------------------------------------------------------------
    # GDPR — user data deletion
    # ------------------------------------------------------------------

    async def gdpr_delete_user_data(
        self,
        *,
        user_id: str,
        tenant_key: str,
        actor_user_id: str,
    ) -> dict:
        """GDPR right to be forgotten — soft-delete all user attachments."""
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            count = await self._repository.soft_delete_user_attachments(
                conn, user_id, tenant_key, actor_user_id, now
            )
            # Write domain audit
            await self._repository.write_audit_event(
                conn,
                event_id=str(uuid.uuid4()),
                attachment_id=None,
                entity_type="user",
                entity_id=user_id,
                event_type=AttachmentAuditEventType.GDPR_DATA_DELETED.value,
                actor_user_id=actor_user_id,
                tenant_key=tenant_key,
                metadata={
                    "attachments_deleted": count,
                    "compliance": "GDPR Article 17",
                },
                now=now,
            )
            # Unified audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="user",
                    entity_id=user_id,
                    event_type=AttachmentUnifiedAuditEventType.ATTACHMENT_GDPR_DATA_DELETED.value,
                    event_category=AuditEventCategory.ATTACHMENT.value,
                    occurred_at=now,
                    actor_id=actor_user_id,
                    actor_type="user",
                    properties={
                        "attachments_deleted": str(count),
                        "compliance": "GDPR Article 17",
                    },
                ),
            )

        return {"attachments_deleted": count, "user_id": user_id}

    # ------------------------------------------------------------------
    # Permission helper (used by router)
    # ------------------------------------------------------------------

    async def is_uploader(self, *, user_id: str, attachment_id: str) -> bool:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_attachment_by_id(conn, attachment_id)
        return record is not None and record.uploaded_by == user_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_content_type(declared: str, filename: str) -> str:
    """Return the normalised effective content type.

    Normalises common MIME aliases so the allow-list check works correctly.
    Extension-based sniffing acts as a fallback for cases where the declared
    type is missing or generic (``application/octet-stream``).
    """
    _ALIASES: dict[str, str] = {
        "image/jpg": "image/jpeg",
        "text/x-csv": "text/csv",
        "application/x-yaml": "application/yaml",
        "text/x-yaml": "application/yaml",
        "application/x-zip-compressed": "application/zip",
    }
    base_declared = declared.lower().split(";")[0].strip()
    normalized = _ALIASES.get(base_declared, base_declared)

    # If declared is generic or missing, infer from extension
    if normalized in ("", "application/octet-stream", "binary/octet-stream"):
        from pathlib import PurePosixPath as _PP
        from importlib import import_module as _im
        ext = PurePosixPath(filename.lower()).suffix
        ext_map = _im("backend.09_attachments.constants").EXTENSION_CONTENT_TYPE_MAP
        normalized = ext_map.get(ext, "application/octet-stream")

    return normalized


def _present_virus_scan_status(status: str) -> str:
    if status == VirusScanStatus.PENDING.value:
        return VirusScanStatus.SKIPPED.value
    return status


def _attachment_response(
    r,
    *,
    uploader_display_name: str | None = None,
) -> AttachmentResponse:
    return AttachmentResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        entity_type=r.entity_type,
        entity_id=r.entity_id,
        uploaded_by=r.uploaded_by,
        uploader_display_name=uploader_display_name,
        original_filename=r.original_filename,
        storage_provider=r.storage_provider,
        storage_bucket=r.storage_bucket,
        storage_url=r.storage_url,
        content_type=r.content_type,
        file_size_bytes=r.file_size_bytes,
        checksum_sha256=r.checksum_sha256,
        virus_scan_status=_present_virus_scan_status(r.virus_scan_status),
        virus_scan_at=r.virus_scan_at,
        description=r.description,
        auditor_access=getattr(r, "auditor_access", False),
        published_for_audit_by=getattr(r, "published_for_audit_by", None),
        published_for_audit_at=getattr(r, "published_for_audit_at", None),
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
