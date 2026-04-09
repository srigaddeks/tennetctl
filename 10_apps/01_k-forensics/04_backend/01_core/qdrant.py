"""kbio Qdrant vector client.

Manages the async Qdrant client for behavioral embedding storage.
Collections: kbio_user_centroids (128d), kbio_session_embeddings (128d),
kbio_credential_embeddings (64d).

Requires: pip install qdrant-client
"""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient  # type: ignore[import-untyped]
from qdrant_client.models import Distance, VectorParams  # type: ignore[import-untyped]

_client: AsyncQdrantClient | None = None

# Collection definitions
COLLECTIONS = {
    "kbio_user_centroids": {"size": 128, "distance": Distance.COSINE},
    "kbio_session_embeddings": {"size": 128, "distance": Distance.COSINE},
    "kbio_credential_embeddings": {"size": 64, "distance": Distance.COSINE},
}


async def init_client(url: str) -> None:
    """Initialize the Qdrant async client and ensure collections exist."""
    global _client
    if _client is not None:
        return
    _client = AsyncQdrantClient(url=url, timeout=10.0)

    # Ensure collections exist
    client = _client
    existing = await client.get_collections()
    existing_names = {c.name for c in existing.collections}

    for name, params in COLLECTIONS.items():
        if name not in existing_names:
            await client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=params["size"],
                    distance=params["distance"],
                ),
            )


async def close_client() -> None:
    """Close the Qdrant client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_client() -> AsyncQdrantClient:
    """Get the initialized Qdrant client."""
    if _client is None:
        raise RuntimeError("Qdrant client not initialised. Call init_client() first.")
    return _client
