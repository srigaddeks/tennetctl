"""Service for notify.suppression — signed unsubscribe tokens + auto-skip list.

Token: base64url(payload_json) + "." + base64url(HMAC-SHA256(signing_key, payload_json))
Payload shape: {"org_id":..., "email":..., "category_code":..., "ts": epoch_seconds}
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from importlib import import_module
from typing import Any

_repo: Any = import_module("backend.02_features.06_notify.sub_features.16_suppression.repository")
_core_id: Any = import_module("backend.01_core.id")

_SIGNING_KEY_VAULT_KEY = "notify.unsubscribe.signing_key"
_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 365  # 1 year; unsubscribe tokens stay valid


# ── Token helpers ─────────────────────────────────────────────────────────

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def make_unsubscribe_token(
    *, org_id: str, email: str, category_code: str | None, signing_key: bytes,
) -> str:
    payload = {
        "org_id": org_id,
        "email": email,
        "category_code": category_code,
        "ts": int(time.time()),
    }
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _b64url(hmac.new(signing_key, body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


def parse_unsubscribe_token(token: str, signing_key: bytes) -> dict | None:
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    expected = hmac.new(signing_key, body.encode("ascii"), hashlib.sha256).digest()
    try:
        if not hmac.compare_digest(expected, _b64url_decode(sig)):
            return None
        payload = json.loads(_b64url_decode(body))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    ts = payload.get("ts")
    if not isinstance(ts, int) or abs(time.time() - ts) > _TOKEN_MAX_AGE_SECONDS:
        return None
    if not payload.get("org_id") or not payload.get("email"):
        return None
    return payload


async def _signing_key_bytes(vault_client: Any) -> bytes:
    """Get or bootstrap the HMAC signing key. Same pattern as magic-link."""
    _vault_client_mod = import_module("backend.02_features.02_vault.client")
    _vault_secrets_service = import_module(
        "backend.02_features.02_vault.sub_features.01_secrets.service"
    )
    _core_errors = import_module("backend.01_core.errors")
    _catalog_ctx = import_module("backend.01_catalog.context")

    VaultSecretNotFound = _vault_client_mod.VaultSecretNotFound
    try:
        raw = await vault_client.get(_SIGNING_KEY_VAULT_KEY)
        return base64.b64decode(raw)
    except VaultSecretNotFound:
        generated = base64.b64encode(os.urandom(32)).decode("ascii")
        pool = vault_client._pool
        sys_ctx = _catalog_ctx.NodeContext(
            audit_category="setup",
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
        )
        async with pool.acquire() as conn:
            try:
                await _vault_secrets_service.create_secret(
                    pool, conn, sys_ctx,
                    vault_client=vault_client,
                    key=_SIGNING_KEY_VAULT_KEY,
                    value=generated,
                    description="HMAC key for notify unsubscribe tokens (RFC 8058)",
                    scope="global",
                    source="bootstrap",
                )
            except _core_errors.ConflictError:
                vault_client.invalidate(_SIGNING_KEY_VAULT_KEY)
                raw = await vault_client.get(_SIGNING_KEY_VAULT_KEY)
                return base64.b64decode(raw)
        vault_client.invalidate(_SIGNING_KEY_VAULT_KEY)
        return base64.b64decode(generated)


# ── Suppression CRUD wrappers ─────────────────────────────────────────────

async def list_suppressions(conn: Any, *, org_id: str, limit: int = 100) -> list[dict]:
    return await _repo.list_suppressions(conn, org_id=org_id, limit=limit)


async def add_suppression(
    conn: Any,
    *,
    org_id: str,
    email: str,
    reason_code: str,
    created_by: str,
    delivery_id: str | None = None,
    notes: str | None = None,
) -> dict | None:
    return await _repo.add_suppression(
        conn,
        id=_core_id.uuid7(),
        org_id=org_id,
        email=email.lower(),
        reason_code=reason_code,
        created_by=created_by,
        delivery_id=delivery_id,
        notes=notes,
    )


async def remove_suppression(conn: Any, *, org_id: str, email: str) -> bool:
    return await _repo.remove_suppression(conn, org_id=org_id, email=email.lower())


async def is_suppressed(conn: Any, *, org_id: str, email: str) -> bool:
    return await _repo.is_suppressed(conn, org_id=org_id, email=email)
