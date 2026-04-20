"""
Vault boot-time bootstrap.

On first start after migrations, ensures the auth subsystem has the secrets it
needs to function. Idempotent — re-running against a populated vault is a no-op.

Bootstrap keys (ADR-028):
  - auth.argon2.pepper          32 random bytes, base64
  - auth.session.signing_key_v1 32 random bytes, base64
"""

from __future__ import annotations

import base64
import logging
import os
from dataclasses import replace
from importlib import import_module
from typing import Any

_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.service"
)
_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.repository"
)

logger = logging.getLogger("tennetctl.vault.bootstrap")


_BOOTSTRAP_KEYS = [
    ("auth.argon2.pepper", "Argon2 pepper for password hashing (phase 8)."),
    ("auth.session.signing_key_v1", "Ed25519 session signing key seed (phase 8)."),
]


def _generate_secret() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


async def ensure_bootstrap_secrets(pool: Any, vault_client: Any) -> int:
    """
    Ensure each bootstrap key exists in the vault. Returns the count of secrets
    newly inserted. Idempotent: re-runs against populated vault insert 0 new rows.
    """
    inserted = 0
    for key, description in _BOOTSTRAP_KEYS:
        async with pool.acquire() as conn:
            async with conn.transaction():
                existing = await _repo.get_metadata_by_scope_key(
                    conn, scope="global", org_id=None, workspace_id=None, key=key,
                )
                if existing is not None:
                    continue

                ctx = _catalog_ctx.NodeContext(
                    user_id="sys",
                    session_id="bootstrap",
                    org_id=None,
                    workspace_id=None,
                    trace_id=_core_id.uuid7(),
                    span_id=_core_id.uuid7(),
                    request_id=_core_id.uuid7(),
                    audit_category="setup",
                    pool=pool,
                    extras={"pool": pool, "vault": vault_client},
                )
                ctx = replace(ctx, conn=conn)

                await _service.create_secret(
                    pool, conn, ctx,
                    vault_client=vault_client,
                    key=key,
                    value=_generate_secret(),
                    description=description,
                    scope="global",
                    org_id=None,
                    workspace_id=None,
                    source="bootstrap",
                )
                inserted += 1
                logger.info("Vault bootstrap: seeded %s (version=1)", key)

    if inserted == 0:
        logger.info("Vault bootstrap: no-op (all keys present).")
    return inserted
