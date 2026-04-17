"""Repository for monitoring.alerts — raw SQL reads/writes (13-08a)."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Severity lookup ───────────────────────────────────────────────────

async def severity_id_by_code(conn: Any, code: str) -> int | None:
    row = await conn.fetchrow(
        """
        SELECT id FROM "05_monitoring"."01_dim_monitoring_alert_severity"
         WHERE code = $1
        """,
        code,
    )
    return int(row["id"]) if row else None


# ── Alert rules ───────────────────────────────────────────────────────

_SELECT_RULE = """
    SELECT id, org_id, name, description, target, dsl, condition,
           severity_id, severity_code, severity_label,
           notify_template_key, labels, is_active, paused_until,
           created_at, updated_at
      FROM "05_monitoring"."v_monitoring_alert_rules"
"""


async def insert_rule(
    conn: Any,
    *,
    id: str,
    org_id: str,
    name: str,
    description: str | None,
    target: str,
    dsl: dict[str, Any],
    condition: dict[str, Any],
    severity_id: int,
    notify_template_key: str,
    labels: dict[str, Any],
) -> dict[str, Any]:
    now = _now()
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."12_fct_monitoring_alert_rules"
            (id, org_id, name, description, target, dsl, condition,
             severity_id, notify_template_key, labels,
             is_active, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,TRUE,$11,$11)
        """,
        id, org_id, name, description, target, dsl, condition,
        severity_id, notify_template_key, labels, now,
    )
    row = await get_rule(conn, rule_id=id, org_id=org_id)
    assert row is not None
    return row


async def get_rule(
    conn: Any, *, rule_id: str, org_id: str,
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        _SELECT_RULE + " WHERE id = $1 AND org_id = $2",
        rule_id, org_id,
    )
    return dict(row) if row else None


async def list_rules(
    conn: Any,
    *,
    org_id: str,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    sql = _SELECT_RULE + " WHERE org_id = $1"
    params: list[Any] = [org_id]
    if is_active is not None:
        params.append(is_active)
        sql += f" AND is_active = ${len(params)}"
    sql += " ORDER BY name"
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def update_rule(
    conn: Any,
    *,
    rule_id: str,
    org_id: str,
    name: str | None = None,
    description: str | None = None,
    dsl: dict[str, Any] | None = None,
    condition: dict[str, Any] | None = None,
    severity_id: int | None = None,
    notify_template_key: str | None = None,
    labels: dict[str, Any] | None = None,
    is_active: bool | None = None,
    paused_until: datetime | None = None,
    clear_paused_until: bool = False,
) -> dict[str, Any] | None:
    sets: list[str] = []
    params: list[Any] = []

    def _add(col: str, val: Any) -> None:
        params.append(val)
        sets.append(f"{col} = ${len(params)}")

    if name is not None:                _add("name", name)
    if description is not None:         _add("description", description)
    if dsl is not None:                 _add("dsl", dsl)
    if condition is not None:           _add("condition", condition)
    if severity_id is not None:         _add("severity_id", severity_id)
    if notify_template_key is not None: _add("notify_template_key", notify_template_key)
    if labels is not None:              _add("labels", labels)
    if is_active is not None:           _add("is_active", is_active)
    if clear_paused_until:
        sets.append("paused_until = NULL")
    elif paused_until is not None:
        _add("paused_until", paused_until)

    if not sets:
        return await get_rule(conn, rule_id=rule_id, org_id=org_id)

    params.append(_now())
    sets.append(f"updated_at = ${len(params)}")
    params.append(rule_id)
    params.append(org_id)

    await conn.execute(
        f"""
        UPDATE "05_monitoring"."12_fct_monitoring_alert_rules"
           SET {', '.join(sets)}
         WHERE id = ${len(params) - 1}
           AND org_id = ${len(params)}
           AND deleted_at IS NULL
        """,
        *params,
    )
    return await get_rule(conn, rule_id=rule_id, org_id=org_id)


async def soft_delete_rule(conn: Any, *, rule_id: str, org_id: str) -> bool:
    now = _now()
    result = await conn.execute(
        """
        UPDATE "05_monitoring"."12_fct_monitoring_alert_rules"
           SET deleted_at = $1, is_active = FALSE, updated_at = $1
         WHERE id = $2 AND org_id = $3 AND deleted_at IS NULL
        """,
        now, rule_id, org_id,
    )
    return result.endswith(" 1")


# ── Silences ──────────────────────────────────────────────────────────

_SELECT_SILENCE = """
    SELECT id, org_id, matcher, starts_at, ends_at, reason, created_by,
           is_active, created_at, updated_at
      FROM "05_monitoring"."v_monitoring_silences"
"""


async def insert_silence(
    conn: Any,
    *,
    id: str,
    org_id: str,
    matcher: dict[str, Any],
    starts_at: datetime,
    ends_at: datetime,
    reason: str,
    created_by: str,
) -> dict[str, Any]:
    now = _now()
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."13_fct_monitoring_silences"
            (id, org_id, matcher, starts_at, ends_at, reason, created_by,
             is_active, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,TRUE,$8,$8)
        """,
        id, org_id, matcher, starts_at, ends_at, reason, created_by, now,
    )
    row = await get_silence(conn, silence_id=id, org_id=org_id)
    assert row is not None
    return row


async def get_silence(
    conn: Any, *, silence_id: str, org_id: str,
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        _SELECT_SILENCE + " WHERE id = $1 AND org_id = $2",
        silence_id, org_id,
    )
    return dict(row) if row else None


async def list_silences(
    conn: Any,
    *,
    org_id: str,
    active_only: bool = True,
) -> list[dict[str, Any]]:
    sql = _SELECT_SILENCE + " WHERE org_id = $1"
    params: list[Any] = [org_id]
    if active_only:
        params.append(_now())
        sql += f" AND is_active = TRUE AND ends_at > ${len(params)}"
    sql += " ORDER BY starts_at DESC"
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def soft_delete_silence(conn: Any, *, silence_id: str, org_id: str) -> bool:
    now = _now()
    result = await conn.execute(
        """
        UPDATE "05_monitoring"."13_fct_monitoring_silences"
           SET deleted_at = $1, is_active = FALSE, updated_at = $1
         WHERE id = $2 AND org_id = $3 AND deleted_at IS NULL
        """,
        now, silence_id, org_id,
    )
    return result.endswith(" 1")


# ── Alert events ──────────────────────────────────────────────────────

_SELECT_EVENT = """
    SELECT id, rule_id, rule_name, severity_id, severity_code, severity_label,
           fingerprint, state, value, threshold, org_id, started_at,
           resolved_at, last_notified_at, notification_count,
           silenced, silence_id, labels, annotations
      FROM "05_monitoring"."v_monitoring_alert_events"
"""


async def list_alert_events(
    conn: Any,
    *,
    org_id: str,
    rule_id: str | None = None,
    state: str | None = None,
    severity: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    sql = _SELECT_EVENT + " WHERE org_id = $1"
    params: list[Any] = [org_id]
    if rule_id is not None:
        params.append(rule_id)
        sql += f" AND rule_id = ${len(params)}"
    if state is not None:
        params.append(state)
        sql += f" AND state = ${len(params)}"
    if severity is not None:
        params.append(severity)
        sql += f" AND severity_code = ${len(params)}"
    if since is not None:
        params.append(since)
        sql += f" AND started_at >= ${len(params)}"
    params.append(limit)
    sql += f" ORDER BY started_at DESC LIMIT ${len(params)}"
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_alert_event(
    conn: Any,
    *,
    event_id: str,
    started_at: datetime,
    org_id: str,
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        _SELECT_EVENT + " WHERE id = $1 AND started_at = $2 AND org_id = $3",
        event_id, started_at, org_id,
    )
    return dict(row) if row else None
