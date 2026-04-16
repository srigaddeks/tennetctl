"""
vault.secrets — service layer.

Scope model (07-03): every operation takes scope + org_id + workspace_id.
Rotate preserves the scope of the latest row. Delete soft-deletes every version
at the exact (scope, org_id, workspace_id, key). Same key can exist at multiple
scopes simultaneously.

The plaintext HTTP read path (GET /v1/vault/{key}) is gone. Values never leave
the server except through the reveal-once UI immediately after create/rotate
(held client-side in a ref) and through the in-process VaultClient (used by
backend features like Phase 8 auth).
"""

from __future__ import annotations

import asyncpg
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_crypto: Any = import_module("backend.02_features.02_vault.crypto")
_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.repository"
)

_AUDIT_NODE_KEY = "audit.events.emit"


def _root_key_from_vault(vault_client: Any) -> bytes:
    return vault_client._root_key  # pylint: disable=protected-access


async def _emit_audit(
    pool: Any,
    ctx: Any,
    *,
    event_key: str,
    metadata: dict,
    outcome: str = "success",
) -> None:
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
    scope: str = "global",
    org_id: str | None = None,
    workspace_id: str | None = None,
    source: str = "api",
) -> dict:
    """Create a new secret at version=1 within the given scope."""
    if await _repo.any_row_exists_at_scope(
        conn, scope=scope, org_id=org_id, workspace_id=workspace_id, key=key,
    ):
        raise _errors.ConflictError(
            f"vault key {key!r} already used at scope={scope!r} "
            f"(org_id={org_id!r}, workspace_id={workspace_id!r}); "
            "choose another key (v0.2 does not allow recycling)"
        )

    secret_id = _core_id.uuid7()
    root_key = _root_key_from_vault(vault_client)
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
            scope=scope,
            org_id=org_id,
            workspace_id=workspace_id,
            created_by=created_by,
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"vault key {key!r} already exists at scope={scope!r}"
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
        pool, ctx,
        event_key="vault.secrets.created",
        metadata={
            "key": key, "version": 1, "scope": scope,
            "org_id": org_id, "workspace_id": workspace_id, "source": source,
        },
    )

    vault_client.invalidate(key)
    created = await _repo.get_metadata_by_scope_key(
        conn, scope=scope, org_id=org_id, workspace_id=workspace_id, key=key,
    )
    if created is None:
        raise RuntimeError(
            f"vault secret {key!r} not visible after insert — tx isolation issue?"
        )
    return created


async def list_secrets(
    conn: Any,
    _ctx: Any,
    *,
    limit: int = 50,
    offset: int = 0,
    scope: str | None = None,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_metadata(
        conn, limit=limit, offset=offset,
        scope=scope, org_id=org_id, workspace_id=workspace_id,
    )


async def rotate_secret(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    key: str,
    value: str,
    description: str | None,
    scope: str = "global",
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> dict:
    """Rotate preserves the scope from the identified (scope, org_id, workspace_id, key)."""
    latest = await _repo.get_latest_envelope(
        conn, scope=scope, org_id=org_id, workspace_id=workspace_id, key=key,
    )
    if latest is None:
        raise _errors.NotFoundError(
            f"vault key {key!r} not found at scope={scope!r}"
        )

    new_secret_id = _core_id.uuid7()
    new_version = int(latest["version"]) + 1
    root_key = _root_key_from_vault(vault_client)
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
        scope=scope,
        org_id=org_id,
        workspace_id=workspace_id,
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
        pool, ctx,
        event_key="vault.secrets.rotated",
        metadata={
            "key": key, "version": new_version,
            "rotated_from_version": int(latest["version"]),
            "scope": scope, "org_id": org_id, "workspace_id": workspace_id,
        },
    )

    vault_client.invalidate(key)
    updated = await _repo.get_metadata_by_scope_key(
        conn, scope=scope, org_id=org_id, workspace_id=workspace_id, key=key,
    )
    if updated is None:
        raise RuntimeError(f"vault secret {key!r} not visible after rotate")
    return updated


async def delete_secret(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    key: str,
    scope: str = "global",
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> None:
    affected = await _repo.soft_delete_all_versions(
        conn, scope=scope, org_id=org_id, workspace_id=workspace_id, key=key,
        updated_by=(ctx.user_id or "sys"),
    )
    if affected == 0:
        raise _errors.NotFoundError(
            f"vault key {key!r} not found at scope={scope!r}"
        )

    await _emit_audit(
        pool, ctx,
        event_key="vault.secrets.deleted",
        metadata={
            "key": key, "versions_affected": affected,
            "scope": scope, "org_id": org_id, "workspace_id": workspace_id,
        },
    )
    vault_client.invalidate(key)
