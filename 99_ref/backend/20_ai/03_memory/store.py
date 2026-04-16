from __future__ import annotations

import uuid
import datetime
from dataclasses import dataclass, field, asdict
from importlib import import_module
from typing import Literal

import httpx

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.memory.store")

COLLECTION_NAME = "kcontrol_user_memory"
VECTOR_SIZE = 1536
DISTANCE = "Cosine"

MemoryType = Literal["fact", "preference", "interaction", "insight"]


@dataclass
class MemoryEntry:
    id: str
    tenant_key: str
    user_id: str
    org_id: str | None
    memory_type: MemoryType
    content: str
    source_conversation_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    score: float | None = None  # populated on retrieval


class QdrantMemoryStore:
    """
    Persists and retrieves user memory vectors in Qdrant.

    Collection payload schema (used for filtering):
      tenant_key       str   — required, isolates tenants
      user_id          str   — required, per-user scope
      org_id           str   — optional, per-org scope
      memory_type      str   — fact | preference | interaction | insight
      content          str   — the text that was embedded
      source_conv_id   str   — conversation that produced this memory
      created_at       str   — ISO timestamp
    """

    def __init__(self, *, qdrant_url: str, api_key: str) -> None:
        self._url = qdrant_url.rstrip("/")
        self._headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
        }

    async def ensure_collection(self) -> None:
        """Create the collection if it does not exist. Idempotent."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Check if collection exists
            resp = await client.get(
                f"{self._url}/collections/{COLLECTION_NAME}",
                headers=self._headers,
            )
            if resp.status_code == 200:
                return  # already exists

            # Create it
            resp = await client.put(
                f"{self._url}/collections/{COLLECTION_NAME}",
                headers=self._headers,
                json={
                    "vectors": {
                        "size": VECTOR_SIZE,
                        "distance": DISTANCE,
                    },
                    "optimizers_config": {
                        "default_segment_number": 2,
                    },
                    "replication_factor": 1,
                },
            )
            if resp.status_code not in (200, 201):
                _logger.error("Failed to create Qdrant collection: %s %s", resp.status_code, resp.text[:200])
                return

            # Create payload indexes for efficient filtering
            await self._ensure_index(client, "tenant_key", "keyword")
            await self._ensure_index(client, "user_id", "keyword")
            await self._ensure_index(client, "org_id", "keyword")
            await self._ensure_index(client, "memory_type", "keyword")
            _logger.info("Created Qdrant collection %s with indexes", COLLECTION_NAME)

    async def _ensure_index(self, client: httpx.AsyncClient, field_name: str, schema_type: str) -> None:
        await client.put(
            f"{self._url}/collections/{COLLECTION_NAME}/index",
            headers=self._headers,
            json={"field_name": field_name, "field_schema": schema_type},
        )

    async def upsert(self, entry: MemoryEntry, vector: list[float]) -> bool:
        """Store a memory entry with its embedding vector. Returns True on success."""
        point = {
            "id": entry.id,
            "vector": vector,
            "payload": {
                "tenant_key": entry.tenant_key,
                "user_id": entry.user_id,
                "org_id": entry.org_id,
                "memory_type": entry.memory_type,
                "content": entry.content,
                "source_conv_id": entry.source_conversation_id,
                "created_at": entry.created_at,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.put(
                    f"{self._url}/collections/{COLLECTION_NAME}/points",
                    headers=self._headers,
                    json={"points": [point]},
                )
                if resp.status_code not in (200, 201):
                    _logger.warning("Qdrant upsert failed: %s", resp.text[:200])
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
        user_id: str,
        org_id: str | None = None,
        memory_type: MemoryType | None = None,
        top_k: int = 5,
        score_threshold: float = 0.55,
    ) -> list[MemoryEntry]:
        """
        Semantic search scoped to tenant+user.
        Filters: tenant_key (required), user_id (required), org_id (optional), memory_type (optional).
        """
        must_conditions = [
            {"key": "tenant_key", "match": {"value": tenant_key}},
            {"key": "user_id", "match": {"value": user_id}},
        ]
        if org_id:
            must_conditions.append({"key": "org_id", "match": {"value": org_id}})
        if memory_type:
            must_conditions.append({"key": "memory_type", "match": {"value": memory_type}})

        payload = {
            "vector": query_vector,
            "limit": top_k,
            "score_threshold": score_threshold,
            "with_payload": True,
            "filter": {"must": must_conditions},
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self._url}/collections/{COLLECTION_NAME}/points/search",
                    headers=self._headers,
                    json=payload,
                )
                if resp.status_code != 200:
                    _logger.warning("Qdrant search failed: %s", resp.text[:200])
                    return []
                data = resp.json()
                results = []
                for hit in data.get("result", []):
                    p = hit.get("payload", {})
                    results.append(MemoryEntry(
                        id=str(hit["id"]),
                        tenant_key=p.get("tenant_key", ""),
                        user_id=p.get("user_id", ""),
                        org_id=p.get("org_id"),
                        memory_type=p.get("memory_type", "fact"),
                        content=p.get("content", ""),
                        source_conversation_id=p.get("source_conv_id"),
                        created_at=p.get("created_at", ""),
                        score=hit.get("score"),
                    ))
                return results
        except Exception as exc:
            _logger.warning("Qdrant search error: %s", exc)
            return []

    async def delete_user_memories(self, *, tenant_key: str, user_id: str) -> bool:
        """Delete all memory entries for a user."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self._url}/collections/{COLLECTION_NAME}/points/delete",
                    headers=self._headers,
                    json={
                        "filter": {
                            "must": [
                                {"key": "tenant_key", "match": {"value": tenant_key}},
                                {"key": "user_id", "match": {"value": user_id}},
                            ]
                        }
                    },
                )
                return resp.status_code == 200
        except Exception as exc:
            _logger.warning("Qdrant delete error: %s", exc)
            return False


class NullQdrantMemoryStore:
    """No-op store — used when AI_QDRANT_URL is not configured."""

    async def ensure_collection(self) -> None:
        pass

    async def upsert(self, entry: MemoryEntry, vector: list[float]) -> bool:  # noqa: ARG002
        return False

    async def search(self, **kwargs) -> list[MemoryEntry]:  # noqa: ARG002
        return []

    async def delete_user_memories(self, **kwargs) -> bool:  # noqa: ARG002
        return False
