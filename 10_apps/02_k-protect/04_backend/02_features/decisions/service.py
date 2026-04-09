"""kprotect decisions service — read-only history queries."""

from __future__ import annotations

import importlib
from datetime import datetime

_repo = importlib.import_module("02_features.decisions.repository")
_errors_mod = importlib.import_module("01_core.errors")

AppError = _errors_mod.AppError


async def list_decisions(
    conn: object,
    org_id: str,
    *,
    limit: int,
    offset: int,
    filters: dict,
) -> dict:
    """Return a paginated list of decisions with optional filters.

    filters keys: user_hash, outcome, action, since, until
    """
    user_hash: str | None = filters.get("user_hash")
    outcome: str | None = filters.get("outcome")
    action: str | None = filters.get("action")
    since: datetime | None = filters.get("since")
    until: datetime | None = filters.get("until")

    items = await _repo.list_decisions(
        conn,
        org_id,
        limit=limit,
        offset=offset,
        user_hash=user_hash,
        outcome=outcome,
        action=action,
        since=since,
        until=until,
    )
    total = await _repo.count_decisions(
        conn,
        org_id,
        user_hash=user_hash,
        outcome=outcome,
        action=action,
        since=since,
        until=until,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def get_decision(conn: object, decision_id: str) -> dict:
    """Return a decision with its per-policy detail rows attached."""
    row = await _repo.get_decision(conn, decision_id)
    if row is None:
        raise AppError("DECISION_NOT_FOUND", f"Decision '{decision_id}' not found.", 404)
    details = await _repo.get_decision_details(conn, decision_id)
    return {**row, "details": details}
