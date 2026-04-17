"""
audit.outbox — service layer (thin wrappers over repo).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.03_outbox.repository"
)


async def poll(
    conn: Any,
    *,
    since_id: int,
    limit: int = 50,
    org_id: str | None = None,
) -> list[dict]:
    return await _repo.poll_outbox(conn, since_id=since_id, limit=limit, org_id=org_id)


async def current_cursor(conn: Any) -> int:
    return await _repo.latest_outbox_id(conn)
