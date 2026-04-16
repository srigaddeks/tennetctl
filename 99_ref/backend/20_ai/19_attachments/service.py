from __future__ import annotations

"""
Attachment ingest service.

Flow:
  1. Receive file bytes + metadata
  2. Create DB record (status=pending)
  3. Extract text (chunker.py)
  4. Embed each chunk (embedder.py)
  5. Upsert vectors into Qdrant kcontrol_copilot collection (document_store.py)
  6. Update DB record (status=ready, chunk_count=N)

On any failure: status=failed + error_message stored.
"""

import base64
import asyncio
import uuid
from importlib import import_module

from .models import AttachmentRecord
from .repository import AttachmentRepository
from .schemas import AttachmentListResponse, AttachmentResponse

_logging_module = import_module("backend.01_core.logging_utils")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_factory_module = import_module("backend.20_ai.14_llm_providers.factory")

get_logger = _logging_module.get_logger
NotFoundError = _errors_module.NotFoundError
AuthorizationError = _errors_module.AuthorizationError
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission
get_provider = _factory_module.get_provider

ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/x-csv",
    "text/html",
    "application/json",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Excel
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    # Images (stored in DB, returned as-is — no text extraction but upload succeeds)
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/svg+xml",
    # Generic fallback — allow any octet-stream and detect by extension
    "application/octet-stream",
}


def _to_response(r: AttachmentRecord) -> AttachmentResponse:
    return AttachmentResponse(
        id=r.id,
        conversation_id=r.conversation_id,
        filename=r.filename,
        content_type=r.content_type,
        file_size_bytes=r.file_size_bytes,
        chunk_count=r.chunk_count,
        ingest_status=r.ingest_status,
        error_message=r.error_message,
        created_at=r.created_at,
        pageindex_status=r.pageindex_status,
        pageindex_error=r.pageindex_error,
    )


# File types that have meaningful document hierarchy — PageIndex is most
# valuable for these.  Plain text, CSV, and JSON get vector RAG only.
_PAGEINDEX_SUPPORTED_TYPES = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
})

_IMAGE_DESCRIPTION_PROMPT = (
    "Describe the image in plain English. Include visible objects, text, labels, "
    "logos, colors, layout, and any important details that would help a user "
    "understand what is in the image. Keep it factual and specific."
)

_IMAGE_MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "tif": "image/tiff",
    "tiff": "image/tiff",
}


class AttachmentService:
    def __init__(self, *, settings, database_pool) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._repository = AttachmentRepository()
        self._logger = get_logger("backend.ai.attachments")

    async def _resolve_scoped_conversation(
        self,
        *,
        conn,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
    ) -> dict:
        row = await conn.fetchrow(
            """
            SELECT id::text AS id,
                   org_id::text AS org_id,
                   workspace_id::text AS workspace_id
            FROM "20_ai"."20_fct_conversations"
            WHERE id = $1::uuid
              AND user_id = $2::uuid
              AND tenant_key = $3
            """,
            conversation_id,
            user_id,
            tenant_key,
        )
        if not row:
            raise NotFoundError(f"Conversation {conversation_id} not found")
        conversation = dict(row)
        if not conversation.get("org_id") or not conversation.get("workspace_id"):
            raise ValidationError("Conversation is missing org/workspace scope and cannot be accessed")
        if conversation["org_id"] != org_id or conversation["workspace_id"] != workspace_id:
            raise NotFoundError(f"Conversation {conversation_id} not found")
        return conversation

    @property
    def _max_file_bytes(self) -> int:
        """Mirror the repo-wide storage upload cap for copilot attachments."""
        return self._settings.storage_max_file_size_mb * 1024 * 1024

    def _get_pageindexer(self):
        _pi_mod = import_module("backend.20_ai.03_memory.pageindex")
        if self._settings.ai_pageindex_enabled and self._settings.ai_provider_url:
            # Allow a dedicated PageIndex model override (e.g. a cheaper model)
            if self._settings.ai_pageindex_model:
                import dataclasses as _dc
                overridden = _dc.replace(
                    self._settings,
                    ai_model=self._settings.ai_pageindex_model,
                )
                return _pi_mod.PageIndexer(settings=overridden)
            return _pi_mod.PageIndexer(settings=self._settings)
        return _pi_mod.NullPageIndexer()

    def _get_chat_provider(self):
        if not self._settings.ai_provider_url:
            return None
        return get_provider(
            provider_type=getattr(self._settings, "ai_provider_type", "openai_compatible"),
            provider_base_url=self._settings.ai_provider_url,
            api_key=self._settings.ai_api_key,
            model_id=self._settings.ai_model,
            temperature=1.0,
        )

    def _get_doc_store(self):
        _doc_store_mod = import_module("backend.20_ai.03_memory.document_store")
        if self._settings.ai_qdrant_url:
            return _doc_store_mod.CopilotDocumentStore(
                qdrant_url=self._settings.ai_qdrant_url,
                api_key=self._settings.ai_qdrant_api_key or "",
            )
        return _doc_store_mod.NullCopilotDocumentStore()

    def _get_embedder(self):
        _embed_mod = import_module("backend.20_ai.03_memory.embedder")
        if self._settings.ai_qdrant_url and (
            self._settings.ai_embedding_url or self._settings.ai_provider_url
        ):
            return _embed_mod.Embedder(settings=self._settings)
        return _embed_mod.NullEmbedder()

    async def _build_pageindex(self, attachment_id: str, text: str) -> None:
        """
        Background task: build a hierarchical TOC tree (Phase 1) and persist it.
        Runs after vector ingest completes.  Failures update status=failed but
        never propagate — vector RAG remains functional as the fallback.
        """
        try:
            async with self._database_pool.acquire() as conn:
                await self._repository.update_pageindex_status(
                    conn, attachment_id=attachment_id, pageindex_status="indexing",
                )

            pageindexer = self._get_pageindexer()
            tree = await pageindexer.build_index(text)

            if not tree or not tree.get("sections"):
                async with self._database_pool.acquire() as conn:
                    await self._repository.update_pageindex_status(
                        conn, attachment_id=attachment_id,
                        pageindex_status="failed",
                        pageindex_error="LLM returned empty TOC tree",
                    )
                return

            async with self._database_pool.acquire() as conn:
                await self._repository.update_pageindex_status(
                    conn, attachment_id=attachment_id,
                    pageindex_status="ready",
                    pageindex_tree=tree,
                )
            self._logger.info(
                "PageIndex: attachment %s indexed (%d top-level sections)",
                attachment_id, len(tree.get("sections", [])),
            )
        except Exception as exc:
            self._logger.error(
                "PageIndex: background build failed for attachment %s: %s",
                attachment_id, exc,
            )
            try:
                async with self._database_pool.acquire() as conn:
                    await self._repository.update_pageindex_status(
                        conn, attachment_id=attachment_id,
                        pageindex_status="failed",
                        pageindex_error=str(exc)[:500],
                    )
            except Exception as inner:
                self._logger.error(
                    "PageIndex: could not persist failure status for %s: %s",
                    attachment_id, inner,
                )

    async def _describe_image(self, *, file_bytes: bytes, content_type: str, filename: str) -> str:
        """
        Ask the shared chat provider to describe an image attachment.
        Returns an empty string if vision is unavailable or the provider fails.
        """
        provider = self._get_chat_provider()
        if provider is None:
            return ""

        mime = content_type.lower().split(";")[0].strip()
        if mime == "image/jpg":
            mime = "image/jpeg"
        if mime == "image/jpeg" and filename.lower().endswith(".jpg"):
            mime = "image/jpeg"
        if mime not in _IMAGE_MIME_MAP.values():
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            mime = _IMAGE_MIME_MAP.get(ext, "")
        if not mime:
            return ""

        try:
            encoded = base64.b64encode(file_bytes).decode("ascii")
            response = await provider.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime};base64,{encoded}"},
                            },
                            {
                                "type": "text",
                                "text": _IMAGE_DESCRIPTION_PROMPT,
                            },
                        ],
                    }
                ],
                tools=None,
                temperature=1.0,
                max_tokens=1024,
            )
            return (response.content or "").strip()
        except Exception as exc:
            self._logger.warning("Image description failed for %s: %s", filename, exc)
            return ""

    async def _ingest_text_content(
        self,
        record: AttachmentRecord,
        *,
        text: str,
        chunker_mod,
        allow_pageindex: bool,
    ) -> None:
        attachment_id = record.id
        async with self._database_pool.acquire() as conn:
            await self._repository.update_ingest_status(conn, attachment_id=attachment_id, ingest_status="ingesting")

        try:
            if not text.strip():
                async with self._database_pool.acquire() as conn:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="failed",
                        error_message="No extractable text in document",
                    )
                return

            chunks = chunker_mod.chunk_text(text)
            if not chunks:
                async with self._database_pool.acquire() as conn:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="failed",
                        error_message="Document produced no text chunks",
                    )
                return

            embedder = self._get_embedder()
            vectors = await embedder.embed_batch(chunks)

            _doc_store_mod = import_module("backend.20_ai.03_memory.document_store")
            doc_chunks = []
            valid_vectors = []
            for i, (chunk_text, vec) in enumerate(zip(chunks, vectors)):
                if vec is None:
                    continue
                doc_chunks.append(_doc_store_mod.DocumentChunk(
                    id=str(uuid.uuid4()),
                    tenant_key=record.tenant_key,
                    user_id=record.user_id,
                    conversation_id=record.conversation_id,
                    attachment_id=attachment_id,
                    filename=record.filename,
                    chunk_index=i,
                    chunk_text=chunk_text,
                ))
                valid_vectors.append(vec)

            if not doc_chunks:
                async with self._database_pool.acquire() as conn:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="ready",
                        chunk_count=0,
                        error_message="Embedding not configured — file stored but not searchable via vector",
                    )
                if allow_pageindex and record.content_type in _PAGEINDEX_SUPPORTED_TYPES:
                    asyncio.create_task(
                        self._build_pageindex(attachment_id, text),
                        name=f"pageindex-{attachment_id}",
                    )
                return

            doc_store = self._get_doc_store()
            await doc_store.ensure_collection()
            ok = await doc_store.upsert_chunks(doc_chunks, valid_vectors)

            async with self._database_pool.acquire() as conn:
                if ok:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="ready",
                        chunk_count=len(doc_chunks),
                    )
                    if allow_pageindex and record.content_type in _PAGEINDEX_SUPPORTED_TYPES:
                        asyncio.create_task(
                            self._build_pageindex(attachment_id, text),
                            name=f"pageindex-{attachment_id}",
                        )
                else:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="failed",
                        error_message="Failed to store chunks in Qdrant",
                    )
        except Exception as exc:
            self._logger.error("Ingest failed for attachment %s: %s", attachment_id, exc)
            async with self._database_pool.acquire() as conn:
                await self._repository.update_ingest_status(
                    conn, attachment_id=attachment_id, ingest_status="failed",
                    error_message=str(exc)[:500],
                )

    async def upload_and_ingest(
        self,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> AttachmentResponse:
        """
        Validate, persist metadata, extract text, embed, store in Qdrant.
        Returns the attachment record (status reflects ingest outcome).
        """
        _chunker_mod = import_module("backend.20_ai.03_memory.chunker")

        # Validate
        if len(file_bytes) > self._max_file_bytes:
            raise ValidationError(
                f"File too large: max {self._max_file_bytes // (1024 * 1024)} MB"
            )

        # Normalise content_type — some browsers send charset suffix
        ct_base = content_type.lower().split(";")[0].strip()
        if ct_base not in ALLOWED_CONTENT_TYPES:
            # Fallback by extension
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            ext_map = {
                "txt": "text/plain", "md": "text/markdown",
                "csv": "text/csv", "html": "text/html", "json": "application/json",
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "xls": "application/vnd.ms-excel",
                "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
                "svg": "image/svg+xml",
            }
            ct_base = ext_map.get(ext, "application/octet-stream")

        # Permission check + create DB record
        async with self._database_pool.acquire() as conn:
            await self._resolve_scoped_conversation(
                conn=conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
            )
            await require_permission(
                conn,
                user_id,
                "ai_copilot.execute",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )

            record = await self._repository.create(
                conn,
                conversation_id=conversation_id,
                tenant_key=tenant_key,
                user_id=user_id,
                filename=filename,
                content_type=ct_base,
                file_size_bytes=len(file_bytes),
            )

        # Images are described with the same chat provider, then indexed as text.
        is_image = ct_base.startswith("image/")
        if is_image:
            description = await self._describe_image(
                file_bytes=file_bytes,
                content_type=ct_base,
                filename=filename,
            )
            if description:
                image_text = (
                    f"Image filename: {filename}\n"
                    f"Image type: {ct_base}\n\n"
                    f"Vision description:\n{description}"
                )
                await self._ingest_text_content(
                    record,
                    text=image_text,
                    chunker_mod=_chunker_mod,
                    allow_pageindex=False,
                )
            else:
                async with self._database_pool.acquire() as conn:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=record.id, ingest_status="ready",
                        chunk_count=0,
                        error_message="Image stored — vision description unavailable",
                    )
            async with self._database_pool.acquire() as conn:
                updated = await self._repository.get(conn, attachment_id=record.id, user_id=user_id)
            return _to_response(updated or record)

        # Text-based ingest: extract → chunk → embed → Qdrant
        await self._ingest(record, file_bytes, _chunker_mod)
        # Re-fetch final status
        async with self._database_pool.acquire() as conn:
            updated = await self._repository.get(conn, attachment_id=record.id, user_id=user_id)
        return _to_response(updated or record)

    async def _ingest(self, record: AttachmentRecord, file_bytes: bytes, chunker_mod) -> None:
        attachment_id = record.id
        async with self._database_pool.acquire() as conn:
            await self._repository.update_ingest_status(conn, attachment_id=attachment_id, ingest_status="ingesting")

        try:
            # 1. Extract text
            text = chunker_mod.extract_text(file_bytes, record.content_type, record.filename)
            if not text.strip():
                async with self._database_pool.acquire() as conn:
                    if record.content_type == "application/pdf":
                        await self._repository.update_ingest_status(
                            conn,
                            attachment_id=attachment_id,
                            ingest_status="ready",
                            chunk_count=0,
                            error_message=(
                                "No extractable text found. This PDF appears to be scanned/image-only, "
                                "and OCR is not enabled."
                            ),
                        )
                    else:
                        await self._repository.update_ingest_status(
                            conn, attachment_id=attachment_id, ingest_status="failed",
                            error_message="No extractable text in document",
                        )
                return

            # 2. Chunk
            chunks = chunker_mod.chunk_text(text)
            if not chunks:
                async with self._database_pool.acquire() as conn:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="failed",
                        error_message="Document produced no text chunks",
                    )
                return

            # 3. Embed (batch)
            embedder = self._get_embedder()
            vectors = await embedder.embed_batch(chunks)

            # 4. Build DocumentChunk objects, skip chunks with null vectors
            _doc_store_mod = import_module("backend.20_ai.03_memory.document_store")
            doc_chunks = []
            valid_vectors = []
            for i, (chunk_text, vec) in enumerate(zip(chunks, vectors)):
                if vec is None:
                    continue
                doc_chunks.append(_doc_store_mod.DocumentChunk(
                    id=str(uuid.uuid4()),
                    tenant_key=record.tenant_key,
                    user_id=record.user_id,
                    conversation_id=record.conversation_id,
                    attachment_id=attachment_id,
                    filename=record.filename,
                    chunk_index=i,
                    chunk_text=chunk_text,
                ))
                valid_vectors.append(vec)

            if not doc_chunks:
                # Embedding not configured — store as ready with 0 chunks.
                # PageIndex can still provide value without vector RAG.
                async with self._database_pool.acquire() as conn:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="ready",
                        chunk_count=0,
                        error_message="Embedding not configured — file stored but not searchable via vector",
                    )
                if record.content_type in _PAGEINDEX_SUPPORTED_TYPES:
                    asyncio.create_task(
                        self._build_pageindex(attachment_id, text),
                        name=f"pageindex-{attachment_id}",
                    )
                return

            # 5. Upsert into Qdrant
            doc_store = self._get_doc_store()
            await doc_store.ensure_collection()
            ok = await doc_store.upsert_chunks(doc_chunks, valid_vectors)

            async with self._database_pool.acquire() as conn:
                if ok:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="ready",
                        chunk_count=len(doc_chunks),
                    )
                    # Fire-and-forget PageIndex build for supported document types.
                    # This runs in the background — vector RAG is already available
                    # as a fallback.  Supported types: PDF, DOCX.
                    if record.content_type in _PAGEINDEX_SUPPORTED_TYPES:
                        asyncio.create_task(
                            self._build_pageindex(attachment_id, text),
                            name=f"pageindex-{attachment_id}",
                        )
                else:
                    await self._repository.update_ingest_status(
                        conn, attachment_id=attachment_id, ingest_status="failed",
                        error_message="Failed to store chunks in Qdrant",
                    )

        except Exception as exc:
            self._logger.error("Ingest failed for attachment %s: %s", attachment_id, exc)
            async with self._database_pool.acquire() as conn:
                await self._repository.update_ingest_status(
                    conn, attachment_id=attachment_id, ingest_status="failed",
                    error_message=str(exc)[:500],
                )

    async def list_attachments(
        self,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
    ) -> AttachmentListResponse:
        async with self._database_pool.acquire() as conn:
            await self._resolve_scoped_conversation(
                conn=conn,
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
            )
            await require_permission(
                conn,
                user_id,
                "ai_copilot.view",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )
            records = await self._repository.list_by_conversation(conn, conversation_id=conversation_id)
        return AttachmentListResponse(items=[_to_response(r) for r in records], total=len(records))

    async def delete_attachment(
        self,
        *,
        conversation_id: str,
        attachment_id: str,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
    ) -> None:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get(conn, attachment_id=attachment_id, user_id=user_id)
            if not record:
                raise NotFoundError(f"Attachment {attachment_id} not found")
            if record.conversation_id != conversation_id:
                raise NotFoundError(f"Attachment {attachment_id} not found")
            await self._resolve_scoped_conversation(
                conn=conn,
                conversation_id=record.conversation_id,
                user_id=user_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
            )
            await require_permission(
                conn,
                user_id,
                "ai_copilot.execute",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )
            await self._repository.delete(conn, attachment_id=attachment_id, user_id=user_id)

        # Delete chunks from Qdrant
        doc_store = self._get_doc_store()
        await doc_store.delete_attachment_chunks(tenant_key=tenant_key, attachment_id=attachment_id)
