"""Role expiry sweeper — runs every N seconds, revokes expired assignments."""

from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Any

_repo: Any = import_module("backend.02_features.03_iam.sub_features.04_roles.repository")
_catalog: Any = import_module("backend.01_catalog")
_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_log = logging.getLogger(__name__)
_AUDIT_KEY = "iam.roles.expired"


async def run_once(pool: Any) -> int:
    """Revoke all expired role assignments. Returns count of rows revoked."""
    async with pool.acquire() as conn:
        revoked = await _repo.expire_due(conn)

    if not revoked:
        return 0

    for row in revoked:
        try:
            ctx = _ctx_mod.NodeContext(
                user_id=None,
                session_id=None,
                org_id=row.get("org_id"),
                workspace_id=None,
                trace_id=_id.uuid7(),
                span_id=_id.uuid7(),
                audit_category="setup",
                pool=pool,
                extras={"pool": pool},
            )
            await _catalog.run_node(
                pool,
                "audit.events.emit",
                ctx,
                {
                    "event_key": _AUDIT_KEY,
                    "outcome": "success",
                    "metadata": {
                        "user_id": row["user_id"],
                        "role_id": row["role_id"],
                        "org_id": row["org_id"],
                        "expires_at": row["expires_at"].isoformat() if row.get("expires_at") else None,
                    },
                },
            )
        except Exception:
            pass  # best-effort audit

    _log.info("role_expiry_sweeper: revoked %d assignment(s)", len(revoked))
    return len(revoked)


async def start_sweeper(pool: Any, interval_seconds: int = 300) -> None:
    """Background task — sweeps every interval_seconds."""
    while True:
        try:
            await run_once(pool)
        except Exception as exc:
            _log.warning("role_expiry_sweeper error: %s", exc)
        await asyncio.sleep(interval_seconds)
