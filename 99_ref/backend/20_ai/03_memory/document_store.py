from __future__ import annotations

"""
Qdrant store for conversation-scoped document chunks (copilot attachments).

Collection: kcontrol_copilot
Payload per point:
  tenant_key       str   — tenant isolation
  user_id          str   — who uploaded
  conversation_id  str   — scopes retrieval to this chat session
  attachment_id    str   — which uploaded file this chunk came from
  filename         str   — original filename
  chunk_index      int   — position within the document (0-based)
  chunk_text       str   — the actual text chunk
  created_at       str   — ISO timestamp
"""

import datetime
import uuid
from dataclasses import dataclass, field
from importlib import import_module

import httpx

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.memory.document_store")

COPILOT_COLLECTION = "kcontrol_copilot"
VECTOR_SIZE = 1536
DISTANCE = "Cosine"
QDRANT_UPSERT_BATCH_SIZE = 64
QDRANT_UPSERT_TIMEOUT_SECONDS = 60.0


@dataclass
class DocumentChunk:
    id: str
    tenant_key: str
    user_id: str
    conversation_id: str
    attachment_id: str
    filename: str
    chunk_index: int
    chunk_text: str
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    score: float | None = None  # populated on retrieval


class CopilotDocumentStore:
    """
    Stores and retrieves document chunk vectors in Qdrant kcontrol_copilot collection.
    Used for per-conversation RAG over uploaded attachments.
    """

    def __init__(self, *, qdrant_url: str, api_key: str) -> None:
        self._url = qdrant_url.rstrip("/")
        self._headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
        }
        self._upsert_timeout = QDRANT_UPSERT_TIMEOUT_SECONDS

    async def ensure_collection(self) -> None:
        """Create the collection if it does not exist. Idempotent."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self._url}/collections/{COPILOT_COLLECTION}",
                headers=self._headers,
            )
            if resp.status_code == 200:
                return

            resp = await client.put(
                f"{self._url}/collections/{COPILOT_COLLECTION}",
                headers=self._headers,
                json={
                    "vectors": {"size": VECTOR_SIZE, "distance": DISTANCE},
                    "optimizers_config": {"default_segment_number": 2},
                    "replication_factor": 1,
                },
            )
            if resp.status_code not in (200, 201):
                _logger.error("Failed to create copilot collection: %s %s", resp.status_code, resp.text[:200])
                return

            for fname, ftype in [
                ("tenant_key", "keyword"),
                ("user_id", "keyword"),
                ("conversation_id", "keyword"),
                ("attachment_id", "keyword"),
            ]:
                await self._ensure_index(client, fname, ftype)

            _logger.info("Created Qdrant collection %s", COPILOT_COLLECTION)

    async def _ensure_index(self, client: httpx.AsyncClient, field_name: str, schema_type: str) -> None:
        await client.put(
            f"{self._url}/collections/{COPILOT_COLLECTION}/index",
            headers=self._headers,
            json={"field_name": field_name, "field_schema": schema_type},
        )

    async def upsert_chunks(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> bool:
        """Batch upsert chunk vectors. Returns True on success."""
        points = []
        for chunk, vector in zip(chunks, vectors):
            points.append({
                "id": chunk.id,
                "vector": vector,
                "payload": {
                    "tenant_key": chunk.tenant_key,
                    "user_id": chunk.user_id,
                    "conversation_id": chunk.conversation_id,
                    "attachment_id": chunk.attachment_id,
                    "filename": chunk.filename,
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "created_at": chunk.created_at,
                },
            })
        try:
            async with httpx.AsyncClient(timeout=self._upsert_timeout) as client:
                for start in range(0, len(points), QDRANT_UPSERT_BATCH_SIZE):
                    batch = points[start:start + QDRANT_UPSERT_BATCH_SIZE]
                    resp = await client.put(
                        f"{self._url}/collections/{COPILOT_COLLECTION}/points",
                        headers=self._headers,
                        json={"points": batch},
                    )
                    if resp.status_code not in (200, 201):
                        _logger.warning(
                            "Qdrant upsert failed for batch starting at %d: %s",
                            start,
                            resp.text[:200],
                        )
                        return False
                return True
        except Exception as exc:
            _logger.warning("Qdrant upsert error: %s", exc)
            return False

    async def search(
        self,
        *,
        query_vector: list[float],
        tenant_key: str,
        conversation_id: str,
        top_k: int = 5,
        score_threshold: float = 0.45,
    ) -> list[DocumentChunk]:
        """
        Semantic search scoped to tenant + conversation_id.
        Returns top_k most relevant chunks.
        """
        payload = {
            "vector": query_vector,
            "limit": top_k,
            "score_threshold": score_threshold,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "tenant_key", "match": {"value": tenant_key}},
                    {"key": "conversation_id", "match": {"value": conversation_id}},
                ]
            },
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self._url}/collections/{COPILOT_COLLECTION}/points/search",
                    headers=self._headers,
                    json=payload,
                )
                if resp.status_code != 200:
                    _logger.warning("Copilot search failed: %s", resp.text[:200])
                    return []
                data = resp.json()
                results = []
                for hit in data.get("result", []):
                    p = hit.get("payload", {})
                    results.append(DocumentChunk(
                        id=str(hit["id"]),
                        tenant_key=p.get("tenant_key", ""),
                        user_id=p.get("user_id", ""),
                        conversation_id=p.get("conversation_id", ""),
                        attachment_id=p.get("attachment_id", ""),
                        filename=p.get("filename", ""),
                        chunk_index=p.get("chunk_index", 0),
                        chunk_text=p.get("chunk_text", ""),
                        created_at=p.get("created_at", ""),
                        score=hit.get("score"),
                    ))
                return results
        except Exception as exc:
            _logger.warning("Copilot doc search error: %s", exc)
            return []

    async def list_attachment_chunks(
        self,
        *,
        tenant_key: str,
        conversation_id: str,
        attachment_id: str,
        limit: int = 5,
    ) -> list[DocumentChunk]:
        """
        Return the first stored chunks for an attachment.

        This is a deterministic fallback for generic prompts such as
        "summarize the uploaded document" where semantic retrieval may not
        find a strong match.
        """
        payload = {
            "limit": limit,
            "with_payload": True,
            "with_vectors": False,
            "filter": {
                "must": [
                    {"key": "tenant_key", "match": {"value": tenant_key}},
                    {"key": "conversation_id", "match": {"value": conversation_id}},
                    {"key": "attachment_id", "match": {"value": attachment_id}},
                ]
            },
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self._url}/collections/{COPILOT_COLLECTION}/points/scroll",
                    headers=self._headers,
                    json=payload,
                )
                if resp.status_code != 200:
                    _logger.warning("Copilot attachment scroll failed: %s", resp.text[:200])
                    return []
                data = resp.json()
                result = data.get("result", {})
                points = result.get("points", []) if isinstance(result, dict) else []
                chunks: list[DocumentChunk] = []
                for point in points:
                    payload_data = point.get("payload", {})
                    chunks.append(DocumentChunk(
                        id=str(point.get("id", "")),
                        tenant_key=payload_data.get("tenant_key", ""),
                        user_id=payload_data.get("user_id", ""),
                        conversation_id=payload_data.get("conversation_id", ""),
                        attachment_id=payload_data.get("attachment_id", ""),
                        filename=payload_data.get("filename", ""),
                        chunk_index=payload_data.get("chunk_index", 0),
                        chunk_text=payload_data.get("chunk_text", ""),
                        created_at=payload_data.get("created_at", ""),
                    ))
                chunks.sort(key=lambda chunk: chunk.chunk_index)
                return chunks[:limit]
        except Exception as exc:
            _logger.warning("Copilot attachment scroll error: %s", exc)
            return []

    async def delete_attachment_chunks(self, *, tenant_key: str, attachment_id: str) -> bool:
        """Delete all chunks for a specific attachment."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self._url}/collections/{COPILOT_COLLECTION}/points/delete",
                    headers=self._headers,
                    json={
                        "filter": {
                            "must": [
                                {"key": "tenant_key", "match": {"value": tenant_key}},
                                {"key": "attachment_id", "match": {"value": attachment_id}},
                            ]
                        }
                    },
                )
                return resp.status_code == 200
        except Exception as exc:
            _logger.warning("Qdrant delete chunks error: %s", exc)
            return False

    async def delete_conversation_chunks(self, *, tenant_key: str, conversation_id: str) -> bool:
        """Delete all document chunks for a conversation (e.g. on archive)."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self._url}/collections/{COPILOT_COLLECTION}/points/delete",
                    headers=self._headers,
                    json={
                        "filter": {
                            "must": [
                                {"key": "tenant_key", "match": {"value": tenant_key}},
                                {"key": "conversation_id", "match": {"value": conversation_id}},
                            ]
                        }
                    },
                )
                return resp.status_code == 200
        except Exception as exc:
            _logger.warning("Qdrant delete conversation chunks error: %s", exc)
            return False


class NullCopilotDocumentStore:
    """No-op store — used when AI_QDRANT_URL is not configured."""

    async def ensure_collection(self) -> None:
        pass

    async def upsert_chunks(self, chunks: list, vectors: list) -> bool:
        return False

    async def search(self, **kwargs) -> list:
        return []

    async def list_attachment_chunks(self, **kwargs) -> list:
        return []

    async def delete_attachment_chunks(self, **kwargs) -> bool:
        return False

    async def delete_conversation_chunks(self, **kwargs) -> bool:
        return False
