"""Repository for monitoring.escalation — raw SQL access to escalation + on-call tables."""

from __future__ import annotations

from typing import Any
from importlib import import_module

_core_id = import_module("backend.01_core.id")


async def get_escalation_policy(conn: Any, policy_id: str) -> dict[str, Any] | None:
    """Fetch escalation policy by ID with steps aggregated."""
    return await conn.fetchrow(
        'SELECT * FROM "05_monitoring"."v_monitoring_escalation_policies" WHERE id = $1',
        policy_id,
    )


async def list_escalation_policies(
    conn: Any,
    org_id: str,
    is_active: bool | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """List escalation policies for an org."""
    where_clauses = ['org_id = $1']
    params: list[Any] = [org_id]
    param_idx = 2

    if is_active is not None:
        where_clauses.append(f'is_active = ${param_idx}')
        params.append(is_active)
        param_idx += 1

    where_sql = ' AND '.join(where_clauses)

    # Total count
    count_row = await conn.fetchrow(
        f'SELECT COUNT(*) as cnt FROM "05_monitoring"."v_monitoring_escalation_policies" WHERE {where_sql}',
        *params,
    )
    total = count_row["cnt"] if count_row else 0

    # Paginated list
    rows = await conn.fetch(
        f'''SELECT * FROM "05_monitoring"."v_monitoring_escalation_policies"
           WHERE {where_sql}
           ORDER BY created_at DESC
           OFFSET ${param_idx} LIMIT ${param_idx + 1}''',
        *params, offset, limit,
    )

    return rows or [], total


async def create_escalation_policy(
    conn: Any,
    org_id: str,
    name: str,
    description: str | None,
    steps: list[dict[str, Any]],
    user_id: str,
) -> dict[str, Any]:
    """Create escalation policy + steps. Returns policy with steps aggregated."""
    policy_id = _core_id.uuid7()
    now = _core_id.now_utc()

    # Insert policy
    await conn.execute(
        '''INSERT INTO "05_monitoring"."10_fct_monitoring_escalation_policies"
           (id, org_id, name, description, created_by, updated_by, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $7)''',
        policy_id, org_id, name, description or None, user_id, user_id, now,
    )

    # Insert steps
    for step_order, step in enumerate(steps):
        await conn.execute(
            '''INSERT INTO "05_monitoring"."40_lnk_monitoring_escalation_steps"
               (policy_id, step_order, kind_id, target_ref, wait_seconds, priority, created_by, created_at)
               VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8)''',
            policy_id, step_order, _step_kind_to_id(step["kind"]),
            step.get("target_ref") or {},
            step.get("wait_seconds"),
            step.get("priority", 2),
            user_id, now,
        )

    # Fetch and return with steps
    return await get_escalation_policy(conn, policy_id)


async def update_escalation_policy(
    conn: Any,
    policy_id: str,
    name: str | None,
    description: str | None,
    is_active: bool | None,
    steps: list[dict[str, Any]] | None,
    user_id: str,
) -> dict[str, Any]:
    """Update escalation policy. If steps provided, replaces entire step set."""
    now = _core_id.now_utc()
    updates = []
    params: list[Any] = []
    param_idx = 1

    if name is not None:
        params.append(name)
        updates.append(f'name = ${param_idx}')
        param_idx += 1
    if description is not None:
        params.append(description)
        updates.append(f'description = ${param_idx}')
        param_idx += 1
    if is_active is not None:
        params.append(is_active)
        updates.append(f'is_active = ${param_idx}')
        param_idx += 1

    # Always update updated_by and updated_at
    updates.append(f'updated_by = ${param_idx}')
    params.append(user_id)
    param_idx += 1
    updates.append(f'updated_at = ${param_idx}')
    params.append(now)
    param_idx += 1

    params.append(policy_id)

    if updates:
        await conn.execute(
            f'''UPDATE "05_monitoring"."10_fct_monitoring_escalation_policies"
               SET {', '.join(updates)}
               WHERE id = ${param_idx}''',
            *params,
        )

    # Replace steps if provided
    if steps is not None:
        # Delete old steps
        await conn.execute(
            'DELETE FROM "05_monitoring"."40_lnk_monitoring_escalation_steps" WHERE policy_id = $1',
            policy_id,
        )
        # Insert new steps
        for step_order, step in enumerate(steps):
            await conn.execute(
                '''INSERT INTO "05_monitoring"."40_lnk_monitoring_escalation_steps"
                   (policy_id, step_order, kind_id, target_ref, wait_seconds, priority, created_by, created_at)
                   VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8)''',
                policy_id, step_order, _step_kind_to_id(step["kind"]),
                step.get("target_ref") or {},
                step.get("wait_seconds"),
                step.get("priority", 2),
                user_id, now,
            )

    return await get_escalation_policy(conn, policy_id)


async def soft_delete_escalation_policy(
    conn: Any,
    policy_id: str,
) -> None:
    """Soft delete escalation policy."""
    now = _core_id.now_utc()
    await conn.execute(
        '''UPDATE "05_monitoring"."10_fct_monitoring_escalation_policies"
           SET deleted_at = $1
           WHERE id = $2''',
        now, policy_id,
    )


async def is_policy_in_use(conn: Any, policy_id: str) -> bool:
    """Check if policy is referenced by an active alert rule."""
    row = await conn.fetchrow(
        '''SELECT COUNT(*) as cnt FROM "05_monitoring"."12_fct_monitoring_alert_rules"
           WHERE escalation_policy_id = $1 AND is_active = true AND deleted_at IS NULL''',
        policy_id,
    )
    return (row["cnt"] if row else 0) > 0


# ── On-call Schedules ───────────────────────────────────────────────────

async def get_oncall_schedule(conn: Any, schedule_id: str) -> dict[str, Any] | None:
    """Fetch on-call schedule by ID with members aggregated."""
    return await conn.fetchrow(
        'SELECT * FROM "05_monitoring"."v_monitoring_oncall_schedules" WHERE id = $1',
        schedule_id,
    )


async def list_oncall_schedules(
    conn: Any,
    org_id: str,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """List on-call schedules for an org."""
    count_row = await conn.fetchrow(
        'SELECT COUNT(*) as cnt FROM "05_monitoring"."v_monitoring_oncall_schedules" WHERE org_id = $1',
        org_id,
    )
    total = count_row["cnt"] if count_row else 0

    rows = await conn.fetch(
        '''SELECT * FROM "05_monitoring"."v_monitoring_oncall_schedules"
           WHERE org_id = $1
           ORDER BY created_at DESC
           OFFSET $2 LIMIT $3''',
        org_id, offset, limit,
    )

    return rows or [], total


async def create_oncall_schedule(
    conn: Any,
    org_id: str,
    name: str,
    description: str | None,
    timezone: str,
    rotation_period_seconds: int,
    rotation_start: Any,  # datetime
    member_ids: list[str],
    user_id: str,
) -> dict[str, Any]:
    """Create on-call schedule + members. Returns schedule with members aggregated."""
    schedule_id = _core_id.uuid7()
    now = _core_id.now_utc()

    # Insert schedule
    await conn.execute(
        '''INSERT INTO "05_monitoring"."10_fct_monitoring_oncall_schedules"
           (id, org_id, name, description, timezone, rotation_period_seconds, rotation_start,
            created_by, updated_by, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8, $9, $9)''',
        schedule_id, org_id, name, description or None, timezone, rotation_period_seconds,
        rotation_start, user_id, now,
    )

    # Insert members
    for member_order, member_id in enumerate(member_ids):
        await conn.execute(
            '''INSERT INTO "05_monitoring"."40_lnk_monitoring_oncall_members"
               (schedule_id, member_order, user_id, created_by, created_at)
               VALUES ($1, $2, $3, $4, $5)''',
            schedule_id, member_order, member_id, user_id, now,
        )

    return await get_oncall_schedule(conn, schedule_id)


async def update_oncall_schedule(
    conn: Any,
    schedule_id: str,
    name: str | None,
    description: str | None,
    timezone: str | None,
    rotation_period_seconds: int | None,
    rotation_start: Any | None,
    member_ids: list[str] | None,
    user_id: str,
) -> dict[str, Any]:
    """Update on-call schedule. If members provided, replaces entire member set."""
    now = _core_id.now_utc()
    updates = []
    params: list[Any] = []
    param_idx = 1

    if name is not None:
        params.append(name)
        updates.append(f'name = ${param_idx}')
        param_idx += 1
    if description is not None:
        params.append(description)
        updates.append(f'description = ${param_idx}')
        param_idx += 1
    if timezone is not None:
        params.append(timezone)
        updates.append(f'timezone = ${param_idx}')
        param_idx += 1
    if rotation_period_seconds is not None:
        params.append(rotation_period_seconds)
        updates.append(f'rotation_period_seconds = ${param_idx}')
        param_idx += 1
    if rotation_start is not None:
        params.append(rotation_start)
        updates.append(f'rotation_start = ${param_idx}')
        param_idx += 1

    # Always update updated_by and updated_at
    updates.append(f'updated_by = ${param_idx}')
    params.append(user_id)
    param_idx += 1
    updates.append(f'updated_at = ${param_idx}')
    params.append(now)
    param_idx += 1

    params.append(schedule_id)

    if updates:
        await conn.execute(
            f'''UPDATE "05_monitoring"."10_fct_monitoring_oncall_schedules"
               SET {', '.join(updates)}
               WHERE id = ${param_idx}''',
            *params,
        )

    # Replace members if provided
    if member_ids is not None:
        await conn.execute(
            'DELETE FROM "05_monitoring"."40_lnk_monitoring_oncall_members" WHERE schedule_id = $1',
            schedule_id,
        )
        for member_order, member_id in enumerate(member_ids):
            await conn.execute(
                '''INSERT INTO "05_monitoring"."40_lnk_monitoring_oncall_members"
                   (schedule_id, member_order, user_id, created_by, created_at)
                   VALUES ($1, $2, $3, $4, $5)''',
                schedule_id, member_order, member_id, user_id, now,
            )

    return await get_oncall_schedule(conn, schedule_id)


async def soft_delete_oncall_schedule(
    conn: Any,
    schedule_id: str,
) -> None:
    """Soft delete on-call schedule."""
    now = _core_id.now_utc()
    await conn.execute(
        '''UPDATE "05_monitoring"."10_fct_monitoring_oncall_schedules"
           SET deleted_at = $1
           WHERE id = $2''',
        now, schedule_id,
    )


# ── Escalation State ────────────────────────────────────────────────────

async def create_escalation_state(
    conn: Any,
    alert_event_id: str,
    policy_id: str,
    next_action_at: Any,  # datetime
) -> None:
    """Create initial escalation state for a firing alert."""
    await conn.execute(
        '''INSERT INTO "05_monitoring"."20_dtl_monitoring_alert_escalation_state"
           (alert_event_id, policy_id, current_step, next_action_at)
           VALUES ($1, $2, 0, $3)''',
        alert_event_id, policy_id, next_action_at,
    )


async def get_escalation_state(
    conn: Any,
    alert_event_id: str,
) -> dict[str, Any] | None:
    """Get escalation state for an alert."""
    return await conn.fetchrow(
        '''SELECT * FROM "05_monitoring"."20_dtl_monitoring_alert_escalation_state"
           WHERE alert_event_id = $1''',
        alert_event_id,
    )


async def list_escalation_states_due(
    conn: Any,
    now_ts: Any,  # datetime
) -> list[dict[str, Any]]:
    """List all escalation states ready for processing."""
    return await conn.fetch(
        '''SELECT * FROM "05_monitoring"."20_dtl_monitoring_alert_escalation_state"
           WHERE next_action_at <= $1
             AND ack_at IS NULL
             AND exhausted_at IS NULL
           ORDER BY next_action_at ASC
           LIMIT 1000''',
        now_ts,
    )


async def update_escalation_state(
    conn: Any,
    alert_event_id: str,
    current_step: int | None = None,
    next_action_at: Any | None = None,
    ack_user_id: str | None = None,
    ack_at: Any | None = None,
    exhausted_at: Any | None = None,
) -> None:
    """Update escalation state (used by worker)."""
    updates = []
    params: list[Any] = []
    param_idx = 1

    if current_step is not None:
        updates.append(f'current_step = ${param_idx}')
        params.append(current_step)
        param_idx += 1
    if next_action_at is not None:
        updates.append(f'next_action_at = ${param_idx}')
        params.append(next_action_at)
        param_idx += 1
    if ack_user_id is not None:
        updates.append(f'ack_user_id = ${param_idx}')
        params.append(ack_user_id)
        param_idx += 1
    if ack_at is not None:
        updates.append(f'ack_at = ${param_idx}')
        params.append(ack_at)
        param_idx += 1
    if exhausted_at is not None:
        updates.append(f'exhausted_at = ${param_idx}')
        params.append(exhausted_at)
        param_idx += 1

    params.append(alert_event_id)

    if updates:
        await conn.execute(
            f'''UPDATE "05_monitoring"."20_dtl_monitoring_alert_escalation_state"
               SET {', '.join(updates)}
               WHERE alert_event_id = ${param_idx}''',
            *params,
        )


def _step_kind_to_id(kind: str) -> int:
    """Map step kind code to dim ID."""
    mapping = {
        "notify_user": 1,
        "notify_group": 2,
        "notify_oncall": 3,
        "wait": 4,
        "repeat": 5,
    }
    return mapping.get(kind, 1)


__all__ = [
    "get_escalation_policy",
    "list_escalation_policies",
    "create_escalation_policy",
    "update_escalation_policy",
    "soft_delete_escalation_policy",
    "is_policy_in_use",
    "get_oncall_schedule",
    "list_oncall_schedules",
    "create_oncall_schedule",
    "update_oncall_schedule",
    "soft_delete_oncall_schedule",
    "create_escalation_state",
    "get_escalation_state",
    "list_escalation_states_due",
    "update_escalation_state",
]
