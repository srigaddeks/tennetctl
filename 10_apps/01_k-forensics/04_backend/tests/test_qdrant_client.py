"""Tests for Qdrant client lifecycle."""

import pytest


def test_qdrant_collections_defined():
    import importlib

    qdrant = importlib.import_module("01_core.qdrant")
    assert "kbio_user_centroids" in qdrant.COLLECTIONS
    assert "kbio_session_embeddings" in qdrant.COLLECTIONS
    assert "kbio_credential_embeddings" in qdrant.COLLECTIONS
    assert qdrant.COLLECTIONS["kbio_user_centroids"]["size"] == 128
    assert qdrant.COLLECTIONS["kbio_credential_embeddings"]["size"] == 64


def test_get_client_raises_before_init():
    import importlib

    qdrant = importlib.import_module("01_core.qdrant")
    # Reset state
    qdrant._client = None
    with pytest.raises(RuntimeError, match="not initialised"):
        qdrant.get_client()
