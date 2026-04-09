"""kprotect decisions repository — read-only.

Reads from v_decisions and v_decision_details views.
No writes — decisions are written by the evaluate engine.
"""

from __future__ import annotations

from datetime import datetime


async def list_decisions(
    conn: object,
    org_id: str,
    *,
    limit: int,
    offset: int,
    user_hash: str | None,
    outcome: str | None,
    action: str | None,
    since: datetime | None,
    until: datetime | None,
) -> list[dict]:
    conditions: list[str] = ["org_id = $1"]
    params: list = [org_id, limit, offset]

    if user_hash is not None:
        params.append(user_hash)
        conditions.append(f"user_hash = ${len(params)}")

    if outcome is not None:
        params.append(outcome)
        conditions.append(f"outcome = ${len(params)}")

    if action is not None:
        params.append(action)
        conditions.append(f"action = ${len(params)}")

    if since is not None:
        params.append(since)
        conditions.append(f"created_at >= ${len(params)}")

    if until is not None:
        params.append(until)
        conditions.append(f"created_at <= ${len(params)}")

    where = "WHERE " + " AND ".join(conditions)

    rows = await conn.fetch(  # type: ignore[union-attr]
        f"""
        SELECT id, org_id, session_id, user_hash, device_uuid,
               outcome, action, policy_set_id,
               total_latency_ms, kbio_latency_ms, policy_latency_ms,
               metadata, created_at
          FROM "11_kprotect".v_decisions
          {where}
         ORDER BY created_at DESC
         LIMIT $2 OFFSET $3
        """,
        *params,
    )
    return [dict(r) for r in rows]


async def count_decisions(
    conn: object,
    org_id: str,
    *,
    user_hash: str | None,
    outcome: str | None,
    action: str | None,
    since: datetime | None,
    until: datetime | None,
) -> int:
    conditions: list[str] = ["org_id = $1"]
    params: list = [org_id]

    if user_hash is not None:
        params.append(user_hash)
        conditions.append(f"user_hash = ${len(params)}")

    if outcome is not None:
        params.append(outcome)
        conditions.append(f"outcome = ${len(params)}")

    if action is not None:
        params.append(action)
        conditions.append(f"action = ${len(params)}")

    if since is not None:
        params.append(since)
        conditions.append(f"created_at >= ${len(params)}")

    if until is not None:
        params.append(until)
        conditions.append(f"created_at <= ${len(params)}")

    where = "WHERE " + " AND ".join(conditions)

    total = await conn.fetchval(  # type: ignore[union-attr]
        f"""
        SELECT COUNT(*)
          FROM "11_kprotect".v_decisions
          {where}
        """,
        *params,
    )
    return int(total)


async def get_decision(conn: object, decision_id: str) -> dict | None:
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, org_id, session_id, user_hash, device_uuid,
               outcome, action, policy_set_id,
               total_latency_ms, kbio_latency_ms, policy_latency_ms,
               metadata, created_at
          FROM "11_kprotect".v_decisions
         WHERE id = $1
        """,
        decision_id,
    )
    return dict(row) if row else None


async def get_decision_details(conn: object, decision_id: str) -> list[dict]:
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT id, decision_id, policy_selection_id,
               action, reason, execution_ms, error_message, created_at
          FROM "11_kprotect".v_decision_details
         WHERE decision_id = $1
         ORDER BY created_at ASC
        """,
        decision_id,
    )
    return [dict(r) for r in rows]
