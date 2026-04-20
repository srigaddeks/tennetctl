"""Service layer for monitoring.alerts — DSL validation + audit (13-08a)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

logger = logging.getLogger("tennetctl.monitoring.alerts.service")

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.repository"
)


def _validate_dsl(target: str, dsl: dict[str, Any]) -> None:
    """Dry-run validation of rule DSL via 13-05 validator."""
    try:
        if target == "metrics":
            _dsl.validate_metrics_query(dsl)
        elif target == "logs":
            _dsl.validate_logs_query(dsl)
        else:
            raise _errors.AppError(
                "INVALID_DSL", f"unknown target {target!r}", 400,
            )
    except _dsl.InvalidQueryError as e:
        raise _errors.AppError("INVALID_DSL", f"invalid DSL: {e}", 400) from e


# ── Rule CRUD ─────────────────────────────────────────────────────────

async def create_rule(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    name: str,
    description: str | None,
    target: str,
    dsl: dict[str, Any],
    condition: dict[str, Any],
    severity: str,
    notify_template_key: str,
    labels: dict[str, Any],
) -> dict[str, Any]:
    _validate_dsl(target, dsl)
    sev_id = await _repo.severity_id_by_code(conn, severity)
    if sev_id is None:
        raise _errors.AppError(
            "INVALID_SEVERITY",
            f"unknown severity {severity!r}",
            400,
        )
    existing = await conn.fetchrow(
        """
        SELECT id FROM "05_monitoring"."12_fct_monitoring_alert_rules"
         WHERE org_id = $1 AND name = $2 AND deleted_at IS NULL
        """,
        org_id, name,
    )
    if existing is not None:
        raise _errors.AppError(
            "DUPLICATE",
            f"alert rule {name!r} already exists in this org",
            400,
        )
    rule_id = _core_id.uuid7()
    row = await _repo.insert_rule(
        conn,
        id=rule_id, org_id=org_id, name=name, description=description,
        target=target, dsl=dsl, condition=condition,
        severity_id=sev_id, notify_template_key=notify_template_key,
        labels=labels,
    )
    await _emit_audit(
        pool, ctx, "monitoring.alerts.rule_created",
        {"rule_id": rule_id, "name": name, "target": target, "severity": severity},
    )
    return row


async def get_rule(
    conn: Any, ctx: Any, *, org_id: str, rule_id: str,
) -> dict[str, Any] | None:
    del ctx
    return await _repo.get_rule(conn, rule_id=rule_id, org_id=org_id)


async def list_rules(
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    del ctx
    return await _repo.list_rules(conn, org_id=org_id, is_active=is_active)


async def update_rule(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    rule_id: str,
    name: str | None = None,
    description: str | None = None,
    dsl: dict[str, Any] | None = None,
    condition: dict[str, Any] | None = None,
    severity: str | None = None,
    notify_template_key: str | None = None,
    labels: dict[str, Any] | None = None,
    is_active: bool | None = None,
    paused_until: datetime | None = None,
) -> dict[str, Any] | None:
    existing = await _repo.get_rule(conn, rule_id=rule_id, org_id=org_id)
    if existing is None:
        return None
    if dsl is not None:
        _validate_dsl(existing["target"], dsl)
    sev_id: int | None = None
    if severity is not None:
        sev_id = await _repo.severity_id_by_code(conn, severity)
        if sev_id is None:
            raise _errors.AppError(
                "INVALID_SEVERITY",
                f"unknown severity {severity!r}",
                400,
            )
    row = await _repo.update_rule(
        conn,
        rule_id=rule_id, org_id=org_id,
        name=name, description=description, dsl=dsl, condition=condition,
        severity_id=sev_id, notify_template_key=notify_template_key,
        labels=labels, is_active=is_active, paused_until=paused_until,
    )
    changed = [
        k for k, v in {
            "name": name, "description": description, "dsl": dsl,
            "condition": condition, "severity": severity,
            "notify_template_key": notify_template_key, "labels": labels,
            "is_active": is_active, "paused_until": paused_until,
        }.items() if v is not None
    ]
    await _emit_audit(
        pool, ctx, "monitoring.alerts.rule_updated",
        {"rule_id": rule_id, "fields": changed},
    )
    return row


async def delete_rule(
    pool: Any, conn: Any, ctx: Any, *, org_id: str, rule_id: str,
) -> bool:
    ok = await _repo.soft_delete_rule(conn, rule_id=rule_id, org_id=org_id)
    if ok:
        await _emit_audit(
            pool, ctx, "monitoring.alerts.rule_deleted",
            {"rule_id": rule_id},
        )
    return ok


async def pause_rule(
    pool: Any, conn: Any, ctx: Any,
    *, org_id: str, rule_id: str, paused_until: datetime,
) -> dict[str, Any] | None:
    existing = await _repo.get_rule(conn, rule_id=rule_id, org_id=org_id)
    if existing is None:
        return None
    row = await _repo.update_rule(
        conn, rule_id=rule_id, org_id=org_id, paused_until=paused_until,
    )
    await _emit_audit(
        pool, ctx, "monitoring.alerts.rule_paused",
        {"rule_id": rule_id, "paused_until": paused_until.isoformat()},
    )
    return row


async def unpause_rule(
    pool: Any, conn: Any, ctx: Any,
    *, org_id: str, rule_id: str,
) -> dict[str, Any] | None:
    existing = await _repo.get_rule(conn, rule_id=rule_id, org_id=org_id)
    if existing is None:
        return None
    row = await _repo.update_rule(
        conn, rule_id=rule_id, org_id=org_id, clear_paused_until=True,
    )
    await _emit_audit(
        pool, ctx, "monitoring.alerts.rule_unpaused",
        {"rule_id": rule_id},
    )
    return row


# ── Silence CRUD ──────────────────────────────────────────────────────

async def create_silence(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    created_by: str,
    matcher: dict[str, Any],
    starts_at: datetime,
    ends_at: datetime,
    reason: str,
) -> dict[str, Any]:
    silence_id = _core_id.uuid7()
    row = await _repo.insert_silence(
        conn,
        id=silence_id, org_id=org_id, matcher=matcher,
        starts_at=starts_at, ends_at=ends_at,
        reason=reason, created_by=created_by,
    )
    await _emit_audit(
        pool, ctx, "monitoring.alerts.silence_created",
        {
            "silence_id": silence_id,
            "matcher": matcher,
            "reason": reason,
            "ends_at": ends_at.isoformat(),
        },
    )
    return row


async def list_silences(
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    active_only: bool = True,
) -> list[dict[str, Any]]:
    del ctx
    return await _repo.list_silences(
        conn, org_id=org_id, active_only=active_only,
    )


async def get_silence(
    conn: Any, ctx: Any, *, org_id: str, silence_id: str,
) -> dict[str, Any] | None:
    del ctx
    return await _repo.get_silence(conn, silence_id=silence_id, org_id=org_id)


async def delete_silence(
    pool: Any, conn: Any, ctx: Any, *, org_id: str, silence_id: str,
) -> bool:
    ok = await _repo.soft_delete_silence(
        conn, silence_id=silence_id, org_id=org_id,
    )
    if ok:
        await _emit_audit(
            pool, ctx, "monitoring.alerts.silence_deleted",
            {"silence_id": silence_id},
        )
    return ok


# ── Alert event reads ─────────────────────────────────────────────────

async def list_alert_events(
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    rule_id: str | None = None,
    state: str | None = None,
    severity: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    del ctx
    return await _repo.list_alert_events(
        conn,
        org_id=org_id, rule_id=rule_id, state=state, severity=severity,
        since=since, limit=limit,
    )


async def get_alert_event(
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    event_id: str,
    started_at: datetime,
) -> dict[str, Any] | None:
    del ctx
    return await _repo.get_alert_event(
        conn, event_id=event_id, started_at=started_at, org_id=org_id,
    )


# ── Evaluator helpers (13-08b) ────────────────────────────────────────

async def insert_alert_event(
    conn: Any,
    *,
    id: str,
    rule_id: str,
    fingerprint: str,
    value: float | None,
    threshold: float | None,
    org_id: str,
    started_at: datetime,
    labels: dict[str, Any],
    annotations: dict[str, Any] | None = None,
    silenced: bool = False,
    silence_id: str | None = None,
) -> None:
    """INSERT a new firing alert event row. Emits monitoring_alert_fired NOTIFY after commit."""
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."60_evt_monitoring_alert_events"
            (id, rule_id, fingerprint, state, value, threshold, org_id,
             started_at, silenced, silence_id, labels, annotations,
             notification_count)
        VALUES ($1,$2,$3,'firing',$4,$5,$6,$7,$8,$9,$10,$11,0)
        """,
        id, rule_id, fingerprint, value, threshold, org_id, started_at,
        silenced, silence_id, labels, annotations or {},
    )
    # Notify incident grouper worker about new firing alert
    await conn.execute(
        "SELECT pg_notify('monitoring_alert_fired', $1)",
        id,
    )


async def update_alert_event(
    conn: Any,
    *,
    id: str,
    started_at: datetime,
    resolved_at: datetime | None = None,
    last_notified_at: datetime | None = None,
    notification_count: int | None = None,
    value: float | None = None,
    state: str | None = None,
) -> None:
    sets: list[str] = []
    params: list[Any] = []

    def _add(col: str, val: Any) -> None:
        params.append(val)
        sets.append(f"{col} = ${len(params)}")

    if resolved_at is not None:        _add("resolved_at", resolved_at)
    if last_notified_at is not None:   _add("last_notified_at", last_notified_at)
    if notification_count is not None: _add("notification_count", notification_count)
    if value is not None:              _add("value", value)
    if state is not None:              _add("state", state)
    if not sets:
        return
    params.append(id)
    params.append(started_at)
    await conn.execute(
        f"""
        UPDATE "05_monitoring"."60_evt_monitoring_alert_events"
           SET {', '.join(sets)}
         WHERE id = ${len(params) - 1} AND started_at = ${len(params)}
        """,
        *params,
    )


async def find_firing_event(
    conn: Any, *, rule_id: str, fingerprint: str,
) -> dict[str, Any] | None:
    """Return the latest firing event row for (rule_id, fingerprint) or None."""
    row = await conn.fetchrow(
        """
        SELECT id, rule_id, fingerprint, state, value, threshold, org_id,
               started_at, resolved_at, last_notified_at, notification_count,
               silenced, silence_id, labels, annotations
          FROM "05_monitoring"."60_evt_monitoring_alert_events"
         WHERE rule_id = $1 AND fingerprint = $2 AND state = 'firing'
         ORDER BY started_at DESC
         LIMIT 1
        """,
        rule_id, fingerprint,
    )
    return dict(row) if row else None


async def find_matching_silences(
    conn: Any,
    *,
    org_id: str,
    rule_id: str,
    labels: dict[str, Any],
    now: datetime,
) -> str | None:
    """Return a matching silence_id if any active silence matches the alert.

    Matcher shape (stored JSONB):
      {"rule_id": "<uuid>"}                 → match by rule_id
      {"labels": {"team": "platform", ...}} → all label k/v must match
      {"rule_id": "...", "labels": {...}}   → both
    Empty matcher ({}) matches nothing (per migration comment).
    """
    rows = await conn.fetch(
        """
        SELECT id, matcher FROM "05_monitoring".v_monitoring_silences
         WHERE org_id = $1 AND is_active = TRUE
           AND starts_at <= $2 AND ends_at > $2
        """,
        org_id, now,
    )
    import json as _json
    for r in rows:
        m = r["matcher"]
        if isinstance(m, str):
            try:
                m = _json.loads(m)
            except Exception:  # noqa: BLE001
                continue
        if not m:
            continue
        m_rule = m.get("rule_id")
        m_labels = m.get("labels") or {}
        if m_rule and m_rule != rule_id:
            continue
        if m_labels:
            if not isinstance(labels, dict):
                continue
            ok = all(str(labels.get(k)) == str(v) for k, v in m_labels.items())
            if not ok:
                continue
        # At least one matcher field must be specified (no empty-match).
        if not m_rule and not m_labels:
            continue
        return str(r["id"])
    return None


async def update_rule_state(
    conn: Any,
    *,
    rule_id: str,
    pending_fingerprints: dict[str, Any] | None = None,
    last_eval_at: datetime | None = None,
    last_eval_duration_ms: int | None = None,
    last_error: str | None = None,
) -> None:
    """Upsert rule state row — used by worker after each evaluation cycle."""
    now = datetime.now(timezone.utc).replace(tzinfo=None) if last_eval_at is None else last_eval_at
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."20_dtl_monitoring_rule_state"
            (rule_id, pending_fingerprints, last_eval_at,
             last_eval_duration_ms, last_error, updated_at)
        VALUES ($1, COALESCE($2::jsonb, '{}'::jsonb), $3, $4, $5, $3)
        ON CONFLICT (rule_id) DO UPDATE SET
            pending_fingerprints  = COALESCE(EXCLUDED.pending_fingerprints, "20_dtl_monitoring_rule_state".pending_fingerprints),
            last_eval_at          = EXCLUDED.last_eval_at,
            last_eval_duration_ms = EXCLUDED.last_eval_duration_ms,
            last_error            = EXCLUDED.last_error,
            updated_at            = EXCLUDED.updated_at
        """,
        rule_id,
        None if pending_fingerprints is None else _json_dumps(pending_fingerprints),
        now,
        last_eval_duration_ms,
        last_error,
    )


def _json_dumps(obj: Any) -> str:
    import json as _json
    return _json.dumps(obj)


async def evaluate_all_active_rules(
    pool: Any,
    ctx_factory: Any,
) -> dict[str, Any]:
    """Orchestrator — invoked by the evaluator worker.

    ``ctx_factory(rule)`` must return a NodeContext with the correct
    ``org_id`` so DSL compilation scopes to the right tenant.

    Returns a summary dict: {evaluated, transitions, errors}.
    """
    _evaluator: Any = import_module(
        "backend.02_features.05_monitoring.sub_features.07_alerts.evaluator"
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, org_id, name, description, target, dsl, condition,
                   severity_id, severity_code, notify_template_key,
                   labels, is_active, paused_until
              FROM "05_monitoring"."v_monitoring_alert_rules"
             WHERE is_active = TRUE
               AND (paused_until IS NULL OR paused_until < $1)
            """,
            now,
        )
    rules = [dict(r) for r in rows]

    evaluated = 0
    transition_total = 0
    errors = 0
    for rule in rules:
        ctx = ctx_factory(rule)
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    transitions = await _evaluator.evaluate_rule(
                        conn, rule, ctx, now=now,
                    )
                    transition_total += len(transitions)
            evaluated += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning("rule %s evaluation failed: %r", rule.get("id"), e)
            try:
                async with pool.acquire() as conn:
                    await update_rule_state(
                        conn, rule_id=rule["id"],
                        last_eval_at=now, last_error=repr(e),
                    )
            except Exception:  # noqa: BLE001
                pass
    return {"evaluated": evaluated, "transitions": transition_total, "errors": errors}


# ── Audit helper ──────────────────────────────────────────────────────

async def _emit_audit(
    pool: Any, ctx: Any, event_key: str, metadata: dict[str, Any],
) -> None:
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": event_key, "outcome": "success", "metadata": metadata},
        )
    except Exception:  # noqa: BLE001
        # Audit failures never break the mutation path (mirrors 06_synthetic).
        pass
