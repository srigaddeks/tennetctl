"""Tests for api_key_auth middleware.

Verifies API key validation against the DB, legacy service token fallback,
and proper error handling for missing/invalid/expired/revoked keys.
"""

from __future__ import annotations

import hashlib
import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_auth = importlib.import_module("01_core.api_key_auth")
_errors = importlib.import_module("01_core.errors")


def _make_request(headers: dict | None = None) -> MagicMock:
    req = MagicMock()
    req.headers = headers or {}
    req.state = MagicMock()
    return req


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Happy path: valid X-API-Key
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_valid_api_key():
    raw_key = "kbio_live_abc123secret"
    key_hash = _hash_key(raw_key)

    row = {
        "id": "key-001",
        "org_id": "org-001",
        "workspace_id": "ws-001",
        "key_hash": key_hash,
        "status": "active",
        "is_active": True,
        "is_deleted": False,
        "expires_at": None,
    }

    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=row)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_conn))

    request = _make_request({"x-api-key": raw_key})

    with patch.object(_auth, "_get_pool", return_value=mock_pool):
        result = await _auth.validate_api_key(request)

    assert result["org_id"] == "org-001"
    assert result["workspace_id"] == "ws-001"
    assert result["key_id"] == "key-001"


# ---------------------------------------------------------------------------
# Missing header — no X-API-Key, no X-Internal-Service-Token
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_header_raises_401():
    request = _make_request({})

    with pytest.raises(_errors.AppError) as exc_info:
        await _auth.validate_api_key(request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "UNAUTHORIZED"


# ---------------------------------------------------------------------------
# X-API-Key present but not found in DB
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unknown_key_raises_401():
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=None)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_conn))

    request = _make_request({"x-api-key": "kbio_live_unknown"})

    with patch.object(_auth, "_get_pool", return_value=mock_pool):
        with pytest.raises(_errors.AppError) as exc_info:
            await _auth.validate_api_key(request)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Revoked key
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_revoked_key_raises_403():
    raw_key = "kbio_live_revoked"
    row = {
        "id": "key-002",
        "org_id": "org-001",
        "workspace_id": "ws-001",
        "key_hash": _hash_key(raw_key),
        "status": "revoked",
        "is_active": False,
        "is_deleted": False,
        "expires_at": None,
    }

    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=row)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_conn))

    request = _make_request({"x-api-key": raw_key})

    with patch.object(_auth, "_get_pool", return_value=mock_pool):
        with pytest.raises(_errors.AppError) as exc_info:
            await _auth.validate_api_key(request)

    assert exc_info.value.status_code == 403
    assert "revoked" in exc_info.value.message.lower()


# ---------------------------------------------------------------------------
# Expired key
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_expired_key_raises_403():
    raw_key = "kbio_live_expired"
    row = {
        "id": "key-003",
        "org_id": "org-001",
        "workspace_id": "ws-001",
        "key_hash": _hash_key(raw_key),
        "status": "expired",
        "is_active": False,
        "is_deleted": False,
        "expires_at": "2025-01-01T00:00:00",
    }

    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=row)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_conn))

    request = _make_request({"x-api-key": raw_key})

    with patch.object(_auth, "_get_pool", return_value=mock_pool):
        with pytest.raises(_errors.AppError) as exc_info:
            await _auth.validate_api_key(request)

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Deleted key
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_deleted_key_raises_401():
    raw_key = "kbio_live_deleted"
    row = {
        "id": "key-004",
        "org_id": "org-001",
        "workspace_id": "ws-001",
        "key_hash": _hash_key(raw_key),
        "status": "active",
        "is_active": True,
        "is_deleted": True,
        "expires_at": None,
    }

    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=row)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_conn))

    request = _make_request({"x-api-key": raw_key})

    with patch.object(_auth, "_get_pool", return_value=mock_pool):
        with pytest.raises(_errors.AppError) as exc_info:
            await _auth.validate_api_key(request)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Legacy X-Internal-Service-Token fallback (dev mode)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_legacy_service_token_fallback():
    request = _make_request({"x-internal-service-token": "kbio-dev-internal-token"})

    mock_settings = MagicMock()
    mock_settings.kbio_internal_service_token = "kbio-dev-internal-token"

    with patch.object(_auth, "_get_settings", return_value=mock_settings):
        result = await _auth.validate_api_key(request)

    assert result["org_id"] == "service"
    assert result["key_id"] == "service-token"


@pytest.mark.asyncio
async def test_legacy_service_token_wrong_value():
    request = _make_request({"x-internal-service-token": "wrong-token"})

    mock_settings = MagicMock()
    mock_settings.kbio_internal_service_token = "kbio-dev-internal-token"

    with patch.object(_auth, "_get_settings", return_value=mock_settings):
        with pytest.raises(_errors.AppError) as exc_info:
            await _auth.validate_api_key(request)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# X-API-Key takes precedence over X-Internal-Service-Token
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_key_takes_precedence():
    raw_key = "kbio_live_precedence"
    key_hash = _hash_key(raw_key)

    row = {
        "id": "key-005",
        "org_id": "org-005",
        "workspace_id": "ws-005",
        "key_hash": key_hash,
        "status": "active",
        "is_active": True,
        "is_deleted": False,
        "expires_at": None,
    }

    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=row)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=AsyncContextManager(mock_conn))

    request = _make_request({
        "x-api-key": raw_key,
        "x-internal-service-token": "kbio-dev-internal-token",
    })

    with patch.object(_auth, "_get_pool", return_value=mock_pool):
        result = await _auth.validate_api_key(request)

    assert result["org_id"] == "org-005"
    assert result["key_id"] == "key-005"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class AsyncContextManager:
    """Minimal async context manager wrapper for mock connections."""

    def __init__(self, mock_conn):
        self._conn = mock_conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        pass
