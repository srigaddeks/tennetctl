from __future__ import annotations

import uuid
from importlib import import_module
from .store import MemoryEntry, MemoryType

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.memory.service")


def _get_store_and_embedder(settings):
    """Lazy factory — returns (store, embedder) based on settings."""
    _store_mod = import_module("backend.20_ai.03_memory.store")
    _embed_mod = import_module("backend.20_ai.03_memory.embedder")

    if settings.ai_qdrant_url:
        store = _store_mod.QdrantMemoryStore(
            qdrant_url=settings.ai_qdrant_url,
            api_key=settings.ai_qdrant_api_key or "",
        )
    else:
        store = _store_mod.NullQdrantMemoryStore()

    # Use embedding if Qdrant is configured AND embedding endpoint works
    if settings.ai_qdrant_url and (settings.ai_embedding_url or settings.ai_provider_url):
        embedder = _embed_mod.Embedder(settings=settings)
    else:
        embedder = _embed_mod.NullEmbedder()

    return store, embedder


class MemoryService:
    """
    High-level API for user long-term memory via Qdrant RAG.

    Usage pattern in agent:
      memories = await memory_service.recall(query=user_message, tenant_key=..., user_id=..., org_id=...)
      # inject memories into system prompt as context
      await memory_service.remember(content=..., memory_type="fact", tenant_key=..., user_id=..., ...)
    """

    def __init__(self, *, settings) -> None:
        self._settings = settings
        self._store, self._embedder = _get_store_and_embedder(settings)
        self._initialized = False

    async def _ensure_init(self) -> None:
        if not self._initialized:
            await self._store.ensure_collection()
            self._initialized = True

    async def recall(
        self,
        *,
        query: str,
        tenant_key: str,
        user_id: str,
        org_id: str | None = None,
        memory_type: MemoryType | None = None,
        top_k: int = 5,
    ) -> list[MemoryEntry]:
        """
        Retrieve semantically relevant memories for a user.
        Returns empty list if Qdrant/embeddings are not configured or on any error.
        """
        try:
            await self._ensure_init()
            vector = await self._embedder.embed(query)
            if vector is None:
                return []
            return await self._store.search(
                query_vector=vector,
                tenant_key=tenant_key,
                user_id=user_id,
                org_id=org_id,
                memory_type=memory_type,
                top_k=top_k,
            )
        except Exception as exc:
            _logger.warning("recall() failed silently: %s", exc)
            return []

    async def remember(
        self,
        *,
        content: str,
        memory_type: MemoryType,
        tenant_key: str,
        user_id: str,
        org_id: str | None = None,
        source_conversation_id: str | None = None,
    ) -> bool:
        """
        Store a new memory. Embeds content and upserts into Qdrant.
        Returns True on success, False on any failure (silent).
        """
        try:
            await self._ensure_init()
            vector = await self._embedder.embed(content)
            if vector is None:
                return False
            entry = MemoryEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                user_id=user_id,
                org_id=org_id,
                memory_type=memory_type,
                content=content,
                source_conversation_id=source_conversation_id,
            )
            return await self._store.upsert(entry, vector)
        except Exception as exc:
            _logger.warning("remember() failed silently: %s", exc)
            return False

    async def forget_user(self, *, tenant_key: str, user_id: str) -> bool:
        """Delete all memories for a user (GDPR / user request)."""
        try:
            await self._ensure_init()
            return await self._store.delete_user_memories(tenant_key=tenant_key, user_id=user_id)
        except Exception as exc:
            _logger.warning("forget_user() failed: %s", exc)
            return False

    @staticmethod
    def format_for_prompt(memories: list[MemoryEntry]) -> str:
        """
        Format recalled memories for injection into the system prompt.
        Returns empty string if no memories.
        """
        if not memories:
            return ""
        lines = ["## User Memory Context (from previous sessions)"]
        for m in memories:
            prefix = {
                "fact": "Fact",
                "preference": "Preference",
                "interaction": "Past interaction",
                "insight": "Insight",
            }.get(m.memory_type, "Memory")
            lines.append(f"- [{prefix}] {m.content}")
        return "\n".join(lines)
