from __future__ import annotations

import httpx
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.memory.embedder")

EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small
EMBED_BATCH_SIZE = 32
EMBED_TIMEOUT_SECONDS = 90.0


class Embedder:
    """
    Calls an OpenAI-compatible /embeddings endpoint.
    Uses ai_embedding_url (if set) or falls back to ai_provider_url.
    """

    def __init__(self, *, settings) -> None:
        base_url = settings.ai_embedding_url or settings.ai_provider_url or ""
        self._base_url = base_url.rstrip("/")
        self._api_key = settings.ai_embedding_api_key or settings.ai_api_key or ""
        self._model = settings.ai_embedding_model
        self._timeout = EMBED_TIMEOUT_SECONDS

    async def embed(self, text: str) -> list[float] | None:
        """Return embedding vector or None on failure."""
        if not self._base_url:
            _logger.warning("No embedding URL configured — skipping embed")
            return None
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                embeddings = await self._embed_inputs(client, [text])
                return embeddings[0] if embeddings else None
        except Exception as exc:
            _logger.warning("Embedding call failed: %s", exc)
            return None

    async def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
        """Embed multiple texts. Failures return None per item."""
        if not self._base_url or not texts:
            return [None] * len(texts)
        results: list[list[float] | None] = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for start in range(0, len(texts), EMBED_BATCH_SIZE):
                batch = texts[start:start + EMBED_BATCH_SIZE]
                try:
                    results.extend(await self._embed_inputs(client, batch))
                except Exception as exc:
                    _logger.warning(
                        "Batch embedding call failed for batch starting at %d (%d items): %s",
                        start,
                        len(batch),
                        exc,
                    )
                    results.extend([None] * len(batch))
        return results

    async def _embed_inputs(self, client: httpx.AsyncClient, inputs: list[str]) -> list[list[float]]:
        resp = await client.post(
            f"{self._base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self._model, "input": inputs},
        )
        resp.raise_for_status()
        data = resp.json()
        ordered = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in ordered]


class NullEmbedder:
    """No-op embedder — used when Qdrant is not configured."""

    async def embed(self, text: str) -> list[float] | None:  # noqa: ARG002
        return None

    async def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
        return [None] * len(texts)
