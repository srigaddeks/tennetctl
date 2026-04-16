"""
vault.secrets — service layer.

Business rules: key-uniqueness check, envelope encryption/decryption, version bumps on
rotate, soft-delete cascade, cache invalidation, audit emission on every mutation.

The service never acquires conns — routes/nodes own the tx boundary. Audit emission
goes through `run_node("audit.events.emit", ...)` with tx=caller so the audit row
commits atomically with the secret write.

vault_client is required for writes so the in-process SWR cache can be invalidated on
rotate/delete. For reads we also accept a client to return (value, version) in one hop.
"""

from __future__ import annotations

import asyncpg
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_crypto: Any = import_module("backend.02_features.02_vault.crypto")
_client_mod: Any = import_module("backend.02_features.02_vault.client")
_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.repository"
)

_AUDIT_NODE_KEY = "audit.events.emit"


def _root_key_from_ctx(vault_client: Any) -> bytes:
    """Extract the root key from the VaultClient instance. Service layer never
    reads TENNETCTL_VAULT_ROOT_KEY directly."""
    return vault_client._root_key  # pylint: disable=protected-access


async def _emit_audit(
    pool: Any,
    ctx: Any,
    *,
    event_key: str,
    metadata: dict,
    outcome: str = "success",
) -> None:
    """Dispatch audit.events.emit; runner reuses ctx.conn for atomicity."""
    await _catalog.run_node(
        pool,
        _AUDIT_NODE_KEY,
        ctx,
        {"event_key": event_key, "outcome": outcome, "metadata": metadata},
    )


async def create_secret(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    key: str,
    value: str,
    description: str | None,
    source: str = "api",
) -> dict:
    """Create a new secret at version=1. Raises ConflictError if the key was ever used."""
    if await _repo.any_row_exists(conn, key):
        raise _errors.ConflictError(
            f"vault key {key!r} has been used; choose another key (v0.2 does not allow recycling)"
        )

    secret_id = _core_id.uuid7()
    root_key = _root_key_from_ctx(vault_client)
    env = _crypto.encrypt(value, root_key)
    created_by = ctx.user_id or "sys"

    try:
        await _repo.insert_secret(
            conn,
            id=secret_id,
            key=key,
            version=1,
            ciphertext=env.ciphertext,
            wrapped_dek=env.wrapped_dek,
            nonce=env.nonce,
            created_by=created_by,
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"vault key {key!r} already exists"
        ) from e

    if description:
        attr_id = _core_id.uuid7()
        await _repo.set_description(
            conn,
            secret_id=secret_id,
            description=description,
            attr_row_id=attr_id,
        )

    await _emit_audit(
        pool,
        ctx,
        event_key="vault.secrets.created",
        metadata={"key": key, "version": 1, "source": source},
    )

    vault_client.invalidate(key)
    created = await _repo.get_metadata_by_key(conn, key)
    if created is None:
        raise RuntimeError(
            f"vault secret {key!r} not visible after insert — tx isolation issue?"
        )
    return created


async def read_secret(
    pool: Any,
    ctx: Any,
    *,
    vault_client: Any,
    key: str,
) -> dict:
    """Read plaintext for a key. Emits vault.secrets.read audit (HTTP path only —
    nodes bypass via VaultClient.get directly). Raises NotFoundError if missing."""
    try:
        value, version = await vault_client.get_with_version(key)
    except _client_mod.VaultSecretNotFound as e:
        raise _errors.NotFoundError(
            f"vault key {key!r} not found"
        ) from e

    await _emit_audit(
        pool,
        ctx,
        event_key="vault.secrets.read",
        metadata={"key": key, "version": version},
    )
    return {"key": key, "version": version, "value": value}


async def list_secrets(
    conn: Any,
    _ctx: Any,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Read-only — no audit. Returns (items, total). Items carry metadata only."""
    return await _repo.list_metadata(conn, limit=limit, offset=offset)


async def rotate_secret(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    key: str,
    value: str,
    description: str | None,
) -> dict:
    """Bump version; encrypt new value under a fresh DEK; emit audit; invalidate cache."""
    latest = await _repo.get_latest_envelope(conn, key)
    if latest is None:
        raise _errors.NotFoundError(f"vault key {key!r} not found")

    new_secret_id = _core_id.uuid7()
    new_version = int(latest["version"]) + 1
    root_key = _root_key_from_ctx(vault_client)
    env = _crypto.encrypt(value, root_key)
    created_by = ctx.user_id or "sys"

    await _repo.insert_secret(
        conn,
        id=new_secret_id,
        key=key,
        version=new_version,
        ciphertext=env.ciphertext,
        wrapped_dek=env.wrapped_dek,
        nonce=env.nonce,
        created_by=created_by,
        rotated_from_id=latest["id"],
    )

    if description:
        attr_id = _core_id.uuid7()
        await _repo.set_description(
            conn,
            secret_id=new_secret_id,
            description=description,
            attr_row_id=attr_id,
        )

    await _emit_audit(
        pool,
        ctx,
        event_key="vault.secrets.rotated",
        metadata={"key": key, "version": new_version, "rotated_from_version": int(latest["version"])},
    )

    vault_client.invalidate(key)
    updated = await _repo.get_metadata_by_key(conn, key)
    if updated is None:
        raise RuntimeError(
            f"vault secret {key!r} not visible after rotate"
        )
    return updated


async def delete_secret(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    key: str,
) -> None:
    """Soft-delete all versions of a key. Raises NotFoundError if nothing to delete."""
    affected = await _repo.soft_delete_all_versions(
        conn, key, updated_by=(ctx.user_id or "sys"),
    )
    if affected == 0:
        raise _errors.NotFoundError(f"vault key {key!r} not found")

    await _emit_audit(
        pool,
        ctx,
        event_key="vault.secrets.deleted",
        metadata={"key": key, "versions_affected": affected},
    )
    vault_client.invalidate(key)
