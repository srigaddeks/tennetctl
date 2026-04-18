"""iam.tos — service layer."""

from __future__ import annotations

import hashlib
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module("backend.02_features.03_iam.sub_features.27_tos.repository")


async def _emit(pool: Any, ctx: Any, event_key: str, metadata: dict) -> None:
    try:
        await _catalog.run_node(pool, "audit.events.emit", ctx, {
            "event_key": event_key, "outcome": "success", "metadata": metadata,
        })
    except Exception:
        pass


async def list_versions(conn: Any) -> list[dict]:
    return await _repo.list_versions(conn)


async def create_version(
    pool: Any, conn: Any, ctx: Any, *, version: str, title: str, body_markdown: str,
) -> dict:
    v = await _repo.insert_version(
        conn, id=_core_id.uuid7(), version=version, title=title,
        body_markdown=body_markdown, created_by=ctx.user_id or "sys",
    )
    await _emit(pool, ctx, "iam.tos.published", {"version": version})
    return v


async def mark_effective(
    pool: Any, conn: Any, ctx: Any, *, version_id: str, effective_at: str,
) -> dict:
    v = await _repo.mark_effective(
        conn, version_id=version_id, effective_at=effective_at,
        updated_by=ctx.user_id or "sys",
    )
    if v is None:
        raise _errors.NotFoundError(f"TOS version {version_id!r} not found")
    await _emit(pool, ctx, "iam.tos.effective", {"version_id": version_id, "effective_at": effective_at})
    return v


async def get_current(conn: Any) -> dict | None:
    return await _repo.get_current_version(conn)


async def accept_tos(
    pool: Any, conn: Any, ctx: Any, *, user_id: str, version_id: str, client_ip: str | None,
) -> None:
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest() if client_ip else None
    await _repo.insert_acceptance(
        conn, id=_core_id.uuid7(), user_id=user_id, version_id=version_id, ip_hash=ip_hash,
    )
    await _emit(pool, ctx, "iam.tos.accepted", {"user_id": user_id, "version_id": version_id})


async def check_tos_gate(conn: Any, *, user_id: str) -> str | None:
    """Return pending version_id if user has not accepted the current TOS, else None."""
    current = await _repo.get_current_version(conn)
    if current is None:
        return None  # no TOS published yet — allow all
    accepted = await _repo.has_accepted(conn, user_id=user_id, version_id=current["id"])
    if not accepted:
        return current["id"]
    return None
