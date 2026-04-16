"""
VaultClient — app-singleton in-process reader for vault secrets.

Every backend feature that needs a secret calls `request.app.state.vault.get(key)`.
Values are cached for 60 seconds (SWR) per key; rotate/delete service paths call
`invalidate(key)` to bust the cache immediately.

The node `vault.secrets.get` also reads through this client (not HTTP) — see
AC-5 of plan 07-01: node reads bypass audit for latency; HTTP `GET /v1/vault/{key}`
audits every access for operator visibility.
"""

from __future__ import annotations

import time
from importlib import import_module
from typing import Any

_crypto: Any = import_module("backend.02_features.02_vault.crypto")


class VaultSecretNotFound(Exception):
    """Raised when VaultClient.get is called with a key that does not exist."""


class VaultClient:
    def __init__(self, pool: Any, root_key: bytes, ttl_seconds: float = 60.0) -> None:
        self._pool = pool
        self._root_key = root_key
        self._ttl = ttl_seconds
        # key -> (fetched_at_monotonic, plaintext, version)
        self._cache: dict[str, tuple[float, str, int]] = {}
        # Counter for tests — increments on every DB hit (not cache hits).
        self._fetch_count = 0

    async def get(self, key: str) -> str:
        """Return the latest non-deleted plaintext for `key`. Raises VaultSecretNotFound."""
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and now - cached[0] < self._ttl:
            return cached[1]
        value, version = await self._fetch(key)
        self._cache[key] = (now, value, version)
        return value

    async def get_with_version(self, key: str) -> tuple[str, int]:
        """Same as get() but also returns the version number."""
        await self.get(key)
        entry = self._cache[key]
        return entry[1], entry[2]

    def invalidate(self, key: str) -> None:
        """Drop a key from the cache. Called by rotate/delete service paths."""
        self._cache.pop(key, None)

    def invalidate_all(self) -> None:
        """Drop every cache entry. No wire path yet; used by tests + future LISTEN/NOTIFY."""
        self._cache.clear()

    async def _fetch(self, key: str) -> tuple[str, int]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT ciphertext, wrapped_dek, nonce, version '
                'FROM "02_vault"."10_fct_vault_entries" '
                'WHERE key = $1 AND deleted_at IS NULL '
                'ORDER BY version DESC LIMIT 1',
                key,
            )
        if row is None:
            raise VaultSecretNotFound(f"vault key not found: {key}")
        self._fetch_count += 1
        env = _crypto.Envelope(
            ciphertext=bytes(row["ciphertext"]),
            wrapped_dek=bytes(row["wrapped_dek"]),
            nonce=bytes(row["nonce"]),
        )
        return _crypto.decrypt(env, self._root_key), int(row["version"])
