"""Shared API key validation for kbio routes.

Supports two auth mechanisms (X-API-Key preferred, legacy fallback):
  1. X-API-Key — hashed with SHA-256, looked up in v_api_keys view.
  2. X-Internal-Service-Token — legacy dev-only shared secret.

X-API-Key takes precedence when both headers are present.

Returns a dict with org_id, workspace_id, and key_id on success.
Raises AppError(401) for missing/invalid keys, AppError(403) for revoked/expired.
"""

from __future__ import annotations

import hashlib
import importlib

from fastapi import Request

_errors = importlib.import_module("01_core.errors")
_config = importlib.import_module("01_core.config")
_db = importlib.import_module("01_core.db")

_QUERY = """
    SELECT id, org_id, workspace_id, key_hash, status,
           is_active, is_deleted, expires_at
    FROM "10_kbio".v_api_keys
    WHERE key_hash = $1
    LIMIT 1
"""


def _get_pool():
    return _db.get_pool()


def _get_settings():
    return _config.get_settings()


async def validate_api_key(request: Request) -> dict:
    """Validate the request's API key or legacy service token.

    Returns {"org_id": ..., "workspace_id": ..., "key_id": ...} on success.
    """
    api_key = request.headers.get("x-api-key", "")
    service_token = request.headers.get("x-internal-service-token", "")

    if api_key:
        return await _validate_db_key(api_key)

    if service_token:
        return _validate_legacy_token(service_token)

    raise _errors.AppError("UNAUTHORIZED", "Missing API key.", 401)


async def _validate_db_key(raw_key: str) -> dict:
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    pool = _get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(_QUERY, key_hash)

    if row is None or row["is_deleted"]:
        raise _errors.AppError("UNAUTHORIZED", "Invalid API key.", 401)

    status = row["status"]
    if status == "revoked":
        raise _errors.AppError("FORBIDDEN", "API key has been revoked.", 403)
    if status == "expired" or not row["is_active"]:
        raise _errors.AppError("FORBIDDEN", "API key has expired.", 403)

    return {
        "org_id": row["org_id"],
        "workspace_id": row["workspace_id"],
        "key_id": row["id"],
    }


def _validate_legacy_token(token: str) -> dict:
    settings = _get_settings()
    if token != settings.kbio_internal_service_token:
        raise _errors.AppError("UNAUTHORIZED", "Invalid service token.", 401)

    return {
        "org_id": "service",
        "workspace_id": "service",
        "key_id": "service-token",
    }
