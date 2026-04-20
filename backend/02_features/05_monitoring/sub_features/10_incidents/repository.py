"""Repository layer for incidents sub-feature — all DB reads/writes."""

from __future__ import annotations

from typing import Any
from importlib import import_module

_core_id = import_module("backend.01_core.id")

# All repo functions read from views and write to raw tables. No business logic here.


async def list_incidents(
    conn: Any,
    org_id: str,
    state_id: int | None = None,
    severity_id: int | None = None,
    rule_id: str | None = None,
    label_search: str | None = None,
    opened_after: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List incidents with filters. Returns (rows, total_count)."""
    where_parts = ["i.org_id = $1", "i.deleted_at IS NULL"]
    params: list[Any] = [org_id]
    param_idx = 2

    if state_id is not None:
        where_parts.append(f"i.state_id = ${param_idx}")
        params.append(state_id)
        param_idx += 1

    if severity_id is not None:
        where_parts.append(f"i.severity_id = ${param_idx}")
        params.append(severity_id)
        param_idx += 1

    if opened_after:
        where_parts.append(f"i.opened_at >= ${param_idx}::timestamp")
        params.append(opened_after)
        param_idx += 1

    where_clause = " AND ".join(where_parts)

    # Total count
    count_sql = f"""
        SELECT COUNT(*) as cnt FROM "05_monitoring".v_monitoring_incidents i
        WHERE {where_clause}
    """
    count_row = await conn.fetchrow(count_sql, *params)
    total = count_row["cnt"] if count_row else 0

    # List with pagination
    sql = f"""
        SELECT * FROM "05_monitoring".v_monitoring_incidents i
        WHERE {where_clause}
        ORDER BY i.opened_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([limit, offset])
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows], total


async def get_incident(conn: Any, incident_id: str) -> dict | None:
    """Get single incident by id."""
    row = await conn.fetchrow(
        'SELECT * FROM "05_monitoring".v_monitoring_incidents WHERE id = $1',
        incident_id,
    )
    return dict(row) if row else None


async def create_incident(
    conn: Any,
    org_id: str,
    group_key: str,
    title: str,
    severity_id: int,
) -> dict:
    """Create new incident (state=open). Returns the created row."""
    incident_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."10_fct_monitoring_incidents"
            (id, org_id, group_key, title, severity_id, state_id, opened_at, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        incident_id, org_id, group_key, title, severity_id,
    )
    row = await conn.fetchrow(
        'SELECT * FROM "05_monitoring".v_monitoring_incidents WHERE id = $1',
        incident_id,
    )
    return dict(row) if row else {}


async def find_open_incident_by_group(
    conn: Any,
    org_id: str,
    group_key: str,
    within_seconds: int,
) -> dict | None:
    """Find open or acknowledged incident for (org_id, group_key) opened within window."""
    cutoff = f"CURRENT_TIMESTAMP - INTERVAL '{within_seconds} seconds'"
    row = await conn.fetchrow(
        f"""
        SELECT * FROM "05_monitoring".v_monitoring_incidents
        WHERE org_id = $1
          AND group_key = $2
          AND state_id IN (1, 2)
          AND opened_at >= {cutoff}
        ORDER BY opened_at DESC
        LIMIT 1
        """,
        org_id, group_key,
    )
    return dict(row) if row else None


async def link_alert_to_incident(
    conn: Any,
    incident_id: str,
    alert_event_id: str,
) -> None:
    """Link alert event to incident (idempotent via upsert)."""
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."40_lnk_monitoring_incident_alerts"
            (incident_id, alert_event_id, joined_at)
        VALUES ($1, $2, CURRENT_TIMESTAMP)
        ON CONFLICT DO NOTHING
        """,
        incident_id, alert_event_id,
    )


async def update_incident_state(
    conn: Any,
    incident_id: str,
    state_id: int,
    user_id: str | None = None,
) -> None:
    """Update incident state. Sets acknowledged_at/resolved_at/closed_at as needed."""
    now = "CURRENT_TIMESTAMP"
    if state_id == 2:  # acknowledged
        await conn.execute(
            f"""
            UPDATE "05_monitoring"."10_fct_monitoring_incidents"
            SET state_id = $1, acknowledged_at = {now}, ack_user_id = $2, updated_at = {now}
            WHERE id = $3
            """,
            state_id, user_id, incident_id,
        )
    elif state_id == 3:  # resolved
        await conn.execute(
            f"""
            UPDATE "05_monitoring"."10_fct_monitoring_incidents"
            SET state_id = $1, resolved_at = {now}, resolved_by_user_id = $2, updated_at = {now}
            WHERE id = $3
            """,
            state_id, user_id, incident_id,
        )
    elif state_id == 4:  # closed
        await conn.execute(
            f"""
            UPDATE "05_monitoring"."10_fct_monitoring_incidents"
            SET state_id = $1, closed_at = {now}, updated_at = {now}
            WHERE id = $2
            """,
            state_id, incident_id,
        )
    else:
        await conn.execute(
            f"""
            UPDATE "05_monitoring"."10_fct_monitoring_incidents"
            SET state_id = $1, updated_at = {now}
            WHERE id = $2
            """,
            state_id, incident_id,
        )


async def update_incident_summary(
    conn: Any,
    incident_id: str,
    summary: str | None = None,
    root_cause: str | None = None,
    postmortem_ref: str | None = None,
) -> None:
    """Update incident summary/root_cause/postmortem_ref."""
    parts = []
    params: list[Any] = []
    idx = 1
    if summary is not None:
        parts.append(f"summary = ${idx}")
        params.append(summary)
        idx += 1
    if root_cause is not None:
        parts.append(f"root_cause = ${idx}")
        params.append(root_cause)
        idx += 1
    if postmortem_ref is not None:
        parts.append(f"postmortem_ref = ${idx}")
        params.append(postmortem_ref)
        idx += 1

    if parts:
        parts.append(f"updated_at = CURRENT_TIMESTAMP")
        sql = f"""
            UPDATE "05_monitoring"."10_fct_monitoring_incidents"
            SET {", ".join(parts)}
            WHERE id = ${idx}
        """
        params.append(incident_id)
        await conn.execute(sql, *params)


async def get_incident_timeline(
    conn: Any,
    incident_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Get timeline events for incident."""
    rows = await conn.fetch(
        """
        SELECT
            t.id,
            t.incident_id,
            t.kind_id,
            k.code AS kind_code,
            k.label AS kind_label,
            t.actor_user_id,
            t.payload,
            t.occurred_at,
            t.created_at
        FROM "05_monitoring"."60_evt_monitoring_incident_timeline" t
        LEFT JOIN "05_monitoring"."02_dim_incident_event_kind" k ON t.kind_id = k.id
        WHERE t.incident_id = $1
        ORDER BY t.occurred_at ASC
        LIMIT $2 OFFSET $3
        """,
        incident_id, limit, offset,
    )
    return [dict(r) for r in rows]


async def add_timeline_event(
    conn: Any,
    incident_id: str,
    kind_id: int,
    actor_user_id: str | None = None,
    payload: dict | None = None,
) -> dict:
    """Add event to incident timeline."""
    event_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."60_evt_monitoring_incident_timeline"
            (id, incident_id, kind_id, actor_user_id, payload, occurred_at, created_at)
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        event_id, incident_id, kind_id, actor_user_id, payload or {},
    )
    row = await conn.fetchrow(
        'SELECT * FROM "05_monitoring"."60_evt_monitoring_incident_timeline" WHERE id = $1',
        event_id,
    )
    return dict(row) if row else {}


async def get_linked_alerts(
    conn: Any,
    incident_id: str,
) -> list[dict]:
    """Get all alert events linked to incident."""
    rows = await conn.fetch(
        """
        SELECT a.* FROM "05_monitoring".v_monitoring_alert_events a
        INNER JOIN "05_monitoring"."40_lnk_monitoring_incident_alerts" l ON a.id = l.alert_event_id
        WHERE l.incident_id = $1
        ORDER BY a.started_at DESC
        """,
        incident_id,
    )
    return [dict(r) for r in rows]


async def get_grouping_rule(
    conn: Any,
    rule_id: str,
) -> dict | None:
    """Get grouping rule for alert rule."""
    row = await conn.fetchrow(
        """
        SELECT *
        FROM "05_monitoring"."20_dtl_monitoring_incident_grouping_rules"
        WHERE rule_id = $1
        """,
        rule_id,
    )
    return dict(row) if row else None


async def upsert_grouping_rule(
    conn: Any,
    rule_id: str,
    dedup_strategy: str = "fingerprint",
    group_by: list | None = None,
    group_window_seconds: int = 300,
    custom_template: str | None = None,
    is_active: bool = True,
) -> None:
    """Create or update grouping rule."""
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."20_dtl_monitoring_incident_grouping_rules"
            (rule_id, dedup_strategy, group_by, group_window_seconds, custom_template, is_active, created_at, updated_at)
        VALUES ($1, $2, $3::jsonb, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (rule_id) DO UPDATE SET
            dedup_strategy = EXCLUDED.dedup_strategy,
            group_by = EXCLUDED.group_by,
            group_window_seconds = EXCLUDED.group_window_seconds,
            custom_template = EXCLUDED.custom_template,
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP
        """,
        rule_id, dedup_strategy, group_by or [], group_window_seconds, custom_template, is_active,
    )
