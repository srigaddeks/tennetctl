"""Business logic for the document library."""
from __future__ import annotations

import hashlib
import os
import re
import uuid
from importlib import import_module

from .constants import (
    CACHE_TTL_DOCS,
    PRESIGNED_URL_TTL_SECONDS,
    VALID_CATEGORIES,
    DocAuditEventType,
)
from .repository import DocumentRepository
from .schemas import (
    DocCategoryResponse,
    DocumentListResponse,
    DocumentResponse,
    PresignedDownloadResponse,
    UpdateDocumentRequest,
    UploadDocumentResponse,
    DocEventResponse,
    DocHistoryResponse,
)
from fastapi import UploadFile

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_storage_module = import_module("backend.09_attachments.storage")
_attachments_constants_module = import_module("backend.09_attachments.constants")

DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuthorizationError = _errors_module.AuthorizationError
ServiceUnavailableError = _errors_module.ServiceUnavailableError
get_storage_provider = _storage_module.get_storage_provider
ALLOWED_CONTENT_TYPES = _attachments_constants_module.ALLOWED_CONTENT_TYPES
EXTENSION_CONTENT_TYPE_MAP = _attachments_constants_module.EXTENSION_CONTENT_TYPE_MAP

_MAX_FILE_SIZE_MB_DEFAULT = 100

# Null bytes and unsafe filename characters
_NULL_BYTE_RE = re.compile(r"[\x00\u0000]")
_UNSAFE_CHARS = re.compile(r"[^\w\-. ]", re.UNICODE)
_PATH_TRAVERSAL = re.compile(r"(\.\.[\\/]|^[\\/]|[\\/]\.\.)", re.UNICODE)


def _sanitize_filename(filename: str) -> str:
    filename = _NULL_BYTE_RE.sub("", filename)
    name = os.path.basename(filename.replace("\\", "/"))
    if _PATH_TRAVERSAL.search(name):
        name = name.replace("..", "_")
    name = name.lstrip(".")
    name = _UNSAFE_CHARS.sub("_", name)
    name = name.strip("_").strip()
    if not name:
        name = "document"
    return name[:200]


def _doc_response(doc) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        tenant_key=doc.tenant_key,
        scope=doc.scope,
        org_id=doc.org_id,
        category_code=doc.category_code,
        category_name=doc.category_name,
        title=doc.title,
        description=doc.description,
        tags=doc.tags,
        version_label=doc.version_label,
        original_filename=doc.original_filename,
        content_type=doc.content_type,
        file_size_bytes=doc.file_size_bytes,
        virus_scan_status=doc.virus_scan_status,
        is_visible=doc.is_visible,
        uploaded_by=doc.uploaded_by,
        uploader_display_name=doc.uploader_display_name,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _cat_response(r) -> DocCategoryResponse:
    return DocCategoryResponse(
        code=r.code,
        name=r.name,
        description=r.description,
        sort_order=r.sort_order,
        is_active=r.is_active,
    )


def _event_response(r) -> DocEventResponse:
    return DocEventResponse(
        id=r.id,
        event_type=r.event_type,
        actor_user_id=r.actor_user_id,
        actor_display_name=r.actor_display_name,
        created_at=r.created_at,
        metadata=r.metadata,
    )


@instrument_class_methods(
    namespace="docs.service",
    logger_name="backend.docs.service.instrumentation",
)
class DocumentService:
    def __init__(self, *, settings, database_pool: DatabasePool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repo = DocumentRepository()
        self._log = get_logger("backend.docs.service")

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def list_categories(self) -> list[DocCategoryResponse]:
        async with self._database_pool.acquire() as conn:
            cats = await self._repo.list_categories(conn)
        return [_cat_response(c) for c in cats]

    async def list_global_docs(
        self,
        *,
        tenant_key: str,
        category_code: str | None = None,
        search: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        per_page: int = 50,
        include_invisible: bool = False,
    ) -> DocumentListResponse:
        offset = (page - 1) * per_page
        async with self._database_pool.acquire() as conn:
            docs, total = await self._repo.list_global_docs(
                conn,
                tenant_key=tenant_key,
                category_code=category_code,
                search=search,
                tags=tags,
                limit=per_page,
                offset=offset,
                include_invisible=include_invisible,
            )
        return DocumentListResponse(
            items=[_doc_response(d) for d in docs],
            total=total,
        )

    async def list_org_docs(
        self,
        *,
        tenant_key: str,
        org_id: str,
        category_code: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 50,
        include_invisible: bool = False,
    ) -> DocumentListResponse:
        offset = (page - 1) * per_page
        async with self._database_pool.acquire() as conn:
            docs, total = await self._repo.list_org_docs(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                category_code=category_code,
                search=search,
                limit=per_page,
                offset=offset,
                include_invisible=include_invisible,
            )
        return DocumentListResponse(
            items=[_doc_response(d) for d in docs],
            total=total,
        )

    async def get_download_url(
        self,
        *,
        doc_id: str,
        user_id: str,
        tenant_key: str,
        client_ip: str | None,
        user_agent: str | None,
    ) -> PresignedDownloadResponse:
        async with self._database_pool.acquire() as conn:
            doc = await self._repo.get_document_by_id(conn, tenant_key=tenant_key, doc_id=doc_id)
            if not doc:
                raise NotFoundError("Document not found")
            if doc.tenant_key != tenant_key:
                raise AuthorizationError("Access denied")

            storage = get_storage_provider(self._settings)
            try:
                result = await storage.generate_presigned_download_url(
                    storage_key=doc.storage_key,
                    filename=doc.original_filename,
                    expires_seconds=PRESIGNED_URL_TTL_SECONDS,
                )
            except Exception as exc:
                raise ServiceUnavailableError(f"Storage unavailable: {exc}") from exc

            await self._repo.record_download(
                conn,
                doc_id=doc_id,
                downloaded_by=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            await self._repo.write_audit_event(
                conn,
                doc_id=doc_id,
                scope=doc.scope,
                org_id=doc.org_id,
                event_type=DocAuditEventType.DOWNLOADED,
                actor_user_id=user_id,
                tenant_key=tenant_key,
                metadata={"filename": doc.original_filename},
            )

        return PresignedDownloadResponse(
            document_id=doc_id,
            filename=doc.original_filename,
            download_url=result.url,
            expires_at=result.expires_at.isoformat(),
            content_type=doc.content_type,
            file_size_bytes=doc.file_size_bytes,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def upload_document(
        self,
        *,
        user_id: str,
        tenant_key: str,
        scope: str,
        org_id: str | None,
        category_code: str,
        title: str,
        description: str | None,
        tags: list[str],
        version_label: str | None,
        file: UploadFile,
    ) -> UploadDocumentResponse:
        if scope not in ("global", "org"):
            raise ValidationError("scope must be 'global' or 'org'")
        if scope == "org" and not org_id:
            raise ValidationError("org_id is required for org-scoped documents")
            
        safe_filename = _sanitize_filename(file.filename or "document")
        _, ext = os.path.splitext(safe_filename)
        actual_content_type = file.content_type
        if actual_content_type == "application/octet-stream" and ext.lower() in EXTENSION_CONTENT_TYPE_MAP:
            actual_content_type = EXTENSION_CONTENT_TYPE_MAP[ext.lower()]

        if actual_content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(f"Content type '{actual_content_type}' is not allowed")

        max_bytes = (
            getattr(self._settings, "storage_max_file_size_mb", _MAX_FILE_SIZE_MB_DEFAULT)
            or _MAX_FILE_SIZE_MB_DEFAULT
        ) * 1024 * 1024
        
        file_bytes, checksum = await self._read_and_validate_file(file, max_bytes)

        doc_id = str(uuid.uuid4())

        storage = get_storage_provider(self._settings)
        bucket = (
            getattr(self._settings, "storage_azure_container", None)
            or getattr(self._settings, "storage_s3_bucket", None)
            or getattr(self._settings, "storage_gcs_bucket", None)
            or getattr(self._settings, "storage_minio_bucket", None)
            or "kcontrol"
        )

        if scope == "global":
            storage_key = f"{tenant_key}/docs/global/{doc_id}/{safe_filename}"
        else:
            storage_key = f"{tenant_key}/docs/org/{org_id}/{doc_id}/{safe_filename}"

        try:
            upload_result = await storage.upload(
                file_data=file_bytes,
                storage_key=storage_key,
                content_type=actual_content_type,
                metadata={
                    "tenant_key": tenant_key,
                    "uploaded_by": user_id,
                    "original_filename": safe_filename,
                    "doc_id": doc_id,
                    "scope": scope,
                },
            )
        except Exception as exc:
            raise ServiceUnavailableError(f"Storage unavailable: {exc}") from exc

        try:
            async with self._database_pool.acquire() as conn:
                async with conn.transaction():
                    doc = await self._repo.create_document(
                        conn,
                        tenant_key=tenant_key,
                        scope=scope,
                        org_id=org_id,
                        category_code=category_code,
                        title=title.strip(),
                        description=description,
                        tags=[t.strip().lower() for t in tags if t.strip()],
                        version_label=version_label,
                        original_filename=safe_filename,
                        storage_key=upload_result.storage_key,
                        storage_provider=upload_result.storage_provider,
                        storage_bucket=upload_result.storage_bucket,
                        storage_url=None,
                        content_type=actual_content_type,
                        file_size_bytes=upload_result.file_size_bytes,
                        checksum_sha256=upload_result.checksum_sha256,
                        uploaded_by=user_id,
                        is_visible=True,
                    )
                    await self._repo.write_audit_event(
                        conn,
                        doc_id=doc.id,
                        scope=scope,
                        org_id=org_id,
                        event_type=DocAuditEventType.UPLOADED,
                        actor_user_id=user_id,
                        tenant_key=tenant_key,
                        metadata={"filename": safe_filename, "size": len(file_bytes)},
                    )
        except Exception:
            # Best-effort storage cleanup on DB failure
            try:
                await storage.delete(storage_key=upload_result.storage_key)
            except Exception:
                pass
            raise

        await self._cache.delete_pattern(f"docs:global:{tenant_key}:*")
        if org_id:
            await self._cache.delete_pattern(f"docs:org:{org_id}:*")

        return UploadDocumentResponse(document=_doc_response(doc))

    async def update_document(
        self,
        *,
        doc_id: str,
        user_id: str,
        tenant_key: str,
        request: UpdateDocumentRequest,
    ) -> DocumentResponse:
        async with self._database_pool.acquire() as conn:
            existing = await self._repo.get_document_by_id(conn, tenant_key=tenant_key, doc_id=doc_id)
            if not existing:
                raise NotFoundError("Document not found")
            if existing.tenant_key != tenant_key:
                raise AuthorizationError("Access denied")

            doc = await self._repo.update_document(
                conn,
                tenant_key=tenant_key,
                doc_id=doc_id,
                title=request.title,
                description=request.description,
                tags=request.tags,
                version_label=request.version_label,
                category_code=request.category_code,
                is_visible=request.is_visible,
            )

            changed = []
            if request.tags is not None:
                changed.append("tags")
            if request.title is not None:
                changed.append("title")
            if request.description is not None:
                changed.append("description")
            if request.version_label is not None:
                changed.append("version_label")
            if request.category_code is not None:
                changed.append("category_code")

            event_type = (
                DocAuditEventType.TAGS_UPDATED
                if changed == ["tags"]
                else DocAuditEventType.TITLE_UPDATED
            )
            await self._repo.write_audit_event(
                conn,
                doc_id=doc_id,
                scope=existing.scope,
                org_id=existing.org_id,
                event_type=event_type,
                actor_user_id=user_id,
                tenant_key=tenant_key,
                metadata={"changed": changed},
            )

        await self._cache.delete_pattern(f"docs:global:{tenant_key}:*")
        if existing.org_id:
            await self._cache.delete_pattern(f"docs:org:{existing.org_id}:*")
        return _doc_response(doc)

    async def delete_document(
        self,
        *,
        doc_id: str,
        user_id: str,
        tenant_key: str,
    ) -> None:
        async with self._database_pool.acquire() as conn:
            existing = await self._repo.get_document_by_id(conn, tenant_key=tenant_key, doc_id=doc_id)
            if not existing:
                raise NotFoundError("Document not found")
            if existing.tenant_key != tenant_key:
                raise AuthorizationError("Access denied")

            async with conn.transaction():
                deleted = await self._repo.soft_delete_document(
                    conn, doc_id=doc_id, deleted_by=user_id
                )
                if not deleted:
                    raise NotFoundError("Document not found or already deleted")
                await self._repo.write_audit_event(
                    conn,
                    doc_id=doc_id,
                    scope=existing.scope,
                    org_id=existing.org_id,
                    event_type=DocAuditEventType.DELETED,
                    actor_user_id=user_id,
                    tenant_key=tenant_key,
                    metadata={"filename": existing.original_filename},
                )

        await self._cache.delete_pattern(f"docs:global:{tenant_key}:*")
        if existing.org_id:
            await self._cache.delete_pattern(f"docs:org:{existing.org_id}:*")
    
    async def replace_document(
        self,
        *,
        doc_id: str,
        user_id: str,
        tenant_key: str,
        file: UploadFile,
    ) -> DocumentResponse:
        safe_filename = _sanitize_filename(file.filename or "document")
        _, ext = os.path.splitext(safe_filename)
        actual_content_type = file.content_type
        if actual_content_type == "application/octet-stream" and ext.lower() in EXTENSION_CONTENT_TYPE_MAP:
            actual_content_type = EXTENSION_CONTENT_TYPE_MAP[ext.lower()]

        if actual_content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(f"Content type '{actual_content_type}' is not allowed")

        max_bytes = (
            getattr(self._settings, "storage_max_file_size_mb", _MAX_FILE_SIZE_MB_DEFAULT)
            or _MAX_FILE_SIZE_MB_DEFAULT
        ) * 1024 * 1024
        
        file_bytes, checksum = await self._read_and_validate_file(file, max_bytes)

        async with self._database_pool.acquire() as conn:
            existing = await self._repo.get_document_by_id(conn, tenant_key=tenant_key, doc_id=doc_id)
            if not existing:
                raise NotFoundError("Document not found")
            if existing.tenant_key != tenant_key:
                raise AuthorizationError("Access denied")

            storage = get_storage_provider(self._settings)
            
            if existing.scope == "global":
                storage_key = f"{tenant_key}/docs/global/{doc_id}/{safe_filename}"
            else:
                storage_key = f"{tenant_key}/docs/org/{existing.org_id}/{doc_id}/{safe_filename}"

            try:
                upload_result = await storage.upload(
                    file_data=file_bytes,
                    storage_key=storage_key,
                    content_type=actual_content_type,
                    metadata={
                        "tenant_key": tenant_key,
                        "uploaded_by": user_id,
                        "original_filename": safe_filename,
                        "doc_id": doc_id,
                        "scope": existing.scope,
                        "is_replacement": "true",
                    },
                )
            except Exception as exc:
                raise ServiceUnavailableError(f"Storage unavailable: {exc}") from exc

            try:
                async with conn.transaction():
                    doc = await self._repo.update_document_file(
                        conn,
                        doc_id=doc_id,
                        storage_key=upload_result.storage_key,
                        storage_provider=upload_result.storage_provider,
                        storage_bucket=upload_result.storage_bucket,
                        original_filename=safe_filename,
                        content_type=actual_content_type,
                        file_size_bytes=upload_result.file_size_bytes,
                        checksum_sha256=upload_result.checksum_sha256,
                    )
                    
                    await self._repo.write_audit_event(
                        conn,
                        doc_id=doc_id,
                        scope=existing.scope,
                        org_id=existing.org_id,
                        event_type=DocAuditEventType.REPLACED,
                        actor_user_id=user_id,
                        tenant_key=tenant_key,
                        metadata={
                            "old_filename": existing.original_filename,
                            "new_filename": safe_filename,
                            "new_size": len(file_bytes),
                            "previous_storage": {
                                "key": existing.storage_key,
                                "provider": existing.storage_provider,
                                "bucket": existing.storage_bucket,
                                "size": existing.file_size_bytes,
                                "checksum": existing.checksum_sha256,
                            }
                        },
                    )
                    
                    # Cleanup old storage object if the key has changed and it's not the same file
                    if existing.storage_key != upload_result.storage_key:
                        try:
                            # Note: Deleting prevents reversion if versioning isn't enabled on bucket.
                            # We delete here to address the orphaned storage risk.
                            await storage.delete(storage_key=existing.storage_key)
                        except Exception as e:
                            self._log.warning(f"Failed to delete orphaned storage {existing.storage_key}: {e}")
            except Exception:
                # Best-effort storage cleanup on DB failure
                try:
                    await storage.delete(storage_key=upload_result.storage_key)
                except Exception:
                    pass
                raise

        await self._cache.delete_pattern(f"docs:global:{tenant_key}:*")
        if existing.org_id:
            await self._cache.delete_pattern(f"docs:org:{existing.org_id}:*")
        
        return _doc_response(doc) if doc else _doc_response(existing) # Fallback to existing if update returned None for some reason

    async def list_history(
        self, tenant_key: str, doc_id: str
    ) -> DocHistoryResponse:
        async with self._database_pool.acquire() as conn:
            doc = await self._repo.get_document_by_id(conn, tenant_key=tenant_key, doc_id=doc_id)
            if not doc:
                raise NotFoundError("Document not found")
            if doc.tenant_key != tenant_key:
                raise AuthorizationError("Access denied")
            
            events = await self._repo.list_document_events(conn, tenant_key=tenant_key, doc_id=doc_id)
            return DocHistoryResponse(items=[_event_response(e) for e in events])

    async def revert_to_version(
        self, tenant_key: str, doc_id: str, event_id: str, user_id: str
    ) -> DocumentResponse:
        async with self._database_pool.acquire() as conn:
            doc = await self._repo.get_document_by_id(conn, tenant_key=tenant_key, doc_id=doc_id)
            if not doc:
                raise NotFoundError("Document not found")
            if doc.tenant_key != tenant_key:
                raise AuthorizationError("Access denied")
            
            event = await self._repo.get_audit_event(conn, tenant_key=tenant_key, event_id=event_id)
            if not event or event.document_id != doc_id:
                raise NotFoundError("Version not found")
            
            prev_storage = event.metadata.get("previous_storage")
            if not prev_storage:
                raise ValidationError("This event does not contain version information")
            
            async with conn.transaction():
                # Update DB with old file info
                new_doc = await self._repo.update_document_file(
                    conn,
                    doc_id=doc_id,
                    storage_key=prev_storage["key"],
                    storage_provider=prev_storage["provider"],
                    storage_bucket=prev_storage["bucket"],
                    original_filename=event.metadata.get("old_filename", doc.original_filename),
                    content_type=doc.content_type, # Audit doesn't store content type yet, reuse current
                    file_size_bytes=prev_storage.get("size", 0),
                    checksum_sha256=prev_storage.get("checksum"),
                )
                
                await self._repo.write_audit_event(
                    conn,
                    doc_id=doc_id,
                    scope=doc.scope,
                    org_id=doc.org_id,
                    event_type=DocAuditEventType.REVERTED,
                    actor_user_id=user_id,
                    tenant_key=tenant_key,
                    metadata={
                        "reverted_from_event_id": event_id,
                        "old_filename": doc.original_filename,
                        "new_filename": new_doc.original_filename,
                        "previous_storage": {
                            "key": doc.storage_key,
                            "provider": doc.storage_provider,
                            "bucket": doc.storage_bucket,
                            "size": doc.file_size_bytes,
                            "checksum": doc.checksum_sha256,
                        }
                    },
                )

        await self._cache.delete_pattern(f"docs:global:{tenant_key}:*")
        if doc.org_id:
            await self._cache.delete_pattern(f"docs:org:{doc.org_id}:*")
            
        return _doc_response(new_doc)

    async def _read_and_validate_file(self, file: UploadFile, max_bytes: int) -> tuple[bytes, str]:
        """Read file in chunks to avoid memory exhaustion and validate size/checksum."""
        buffer = []
        total_size = 0
        sha256 = hashlib.sha256()
        
        # Reset file pointer just in case
        await file.seek(0)
        
        while chunk := await file.read(1024 * 1024): # 1MB chunks
            total_size += len(chunk)
            if total_size > max_bytes:
                raise ValidationError(f"File exceeds maximum size of {max_bytes // (1024 * 1024)} MB")
            buffer.append(chunk)
            sha256.update(chunk)
            
        return b"".join(buffer), sha256.hexdigest()

