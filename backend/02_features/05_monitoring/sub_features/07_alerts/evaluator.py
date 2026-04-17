"""Alert evaluator — for_duration gating, fingerprint dedup, transition detection.

Pure logic module. Given an alert rule row and a live DB connection, runs the
rule's DSL via the 13-05 query compilers, derives per-fingerprint observations,
and returns a list of ``AlertTransition`` tuples describing what changed since
the last evaluation.

State lives in ``20_dtl_monitoring_rule_state.pending_fingerprints`` — a JSON
map from ``fingerprint`` -> ``first_breach_iso``. The evaluator reads the map,
updates it, and writes it back. The partitioned ``evt_monitoring_alert_events``
is the firing-history source of truth.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from importlib import import_module
from typing import Any, Literal

_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")

logger = logging.getLogger("tennetctl.monitoring.alerts.evaluator")

TransitionKind = Literal["firing_new", "firing_update", "resolving"]


@dataclass(frozen=True)
class AlertTransition:
    kind: TransitionKind
    fingerprint: str
    value: float
    threshold: float
    labels: dict[str, str]


def fingerprint_for(rule_id: str, labels: dict[str, str]) -> str:
    """Exposed for tests — deterministic sha256 over (rule_id, sorted labels)."""
    canonical = json.dumps(labels, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{rule_id}|{canonical}".encode()).hexdigest()


def _condition_breached(op: str, value: float, threshold: float) -> bool:
    if op == "gt":
        return value > threshold
    if op == "gte":
        return value >= threshold
    if op == "lt":
        return value < threshold
    if op == "lte":
        return value <= threshold
    if op == "eq":
        return value == threshold
    if op == "ne":
        return value != threshold
    raise ValueError(f"unknown condition op: {op}")


async def evaluate_rule(
    conn: Any,
    rule: dict[str, Any],
    ctx: Any,
    now: datetime | None = None,
) -> list[AlertTransition]:
    """Evaluate a single rule. Returns list of transitions to persist.

    Idempotent: fingerprint gating + state table prevent double-fires.
    Caller is responsible for applying the returned transitions
    (INSERT/UPDATE into evt_monitoring_alert_events + notify fan-out).
    """
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    condition = rule["condition"]
    if isinstance(condition, str):
        condition = json.loads(condition)
    threshold = float(condition["threshold"])
    op = condition["op"]
    for_duration_s = int(condition.get("for_duration_seconds", 0) or 0)

    # Build DSL with a synthetic timerange ending at ``now``. The evaluation
    # window is the LARGER of (for_duration, rule's own timerange.last, 60s)
    # so the query sees enough history to trip the condition.
    dsl = rule["dsl"]
    if isinstance(dsl, str):
        dsl = json.loads(dsl)
    dsl = dict(dsl)
    rule_tr = dsl.get("timerange") or {}
    _last_to_s = {
        "15m": 15 * 60, "1h": 3600, "24h": 86400,
        "7d": 7 * 86400, "30d": 30 * 86400, "90d": 90 * 86400,
    }
    rule_window_s = 0
    if isinstance(rule_tr, dict) and isinstance(rule_tr.get("last"), str):
        rule_window_s = _last_to_s.get(rule_tr["last"], 0)
    window_s = max(for_duration_s, rule_window_s, 60)
    dsl["timerange"] = {
        "from_ts": (now - timedelta(seconds=window_s)).isoformat(),
        "to_ts": now.isoformat(),
    }

    target = rule["target"]
    if target == "metrics":
        q = _dsl.validate_metrics_query(dsl)
        sql, params = _dsl.compile_metrics_query(q, ctx)
    elif target == "logs":
        q = _dsl.validate_logs_query(dsl)
        sql, params = _dsl.compile_logs_query(q, ctx)
    else:
        raise ValueError(f"unsupported alert target: {target!r}")

    rows = await conn.fetch(sql, *params)

    # Observed: fingerprint -> (value, labels) for the latest bucket.
    observed: dict[str, tuple[float, dict[str, str]]] = {}
    if target == "metrics":
        # compiler orders bucket_ts ASC; the last row per label-group wins.
        for r in rows:
            raw_labels = r.get("labels") if hasattr(r, "get") else None
            if raw_labels is None:
                # groupby fields come back as top-level columns. Collect all
                # non-bucket_ts/non-value cols as labels.
                labels = {
                    k: str(v) for k, v in dict(r).items()
                    if k not in ("bucket_ts", "value") and v is not None
                }
            else:
                if isinstance(raw_labels, str):
                    raw_labels = json.loads(raw_labels)
                labels = {k: str(v) for k, v in (raw_labels or {}).items()}
            fp = fingerprint_for(rule["id"], labels)
            val = r["value"]
            observed[fp] = (float(val) if val is not None else 0.0, labels)
    else:  # logs — treat all matches as a single unlabeled group.
        fp = fingerprint_for(rule["id"], {})
        observed[fp] = (float(len(rows)), {})

    # Load pending fingerprint state.
    state_row = await conn.fetchrow(
        'SELECT pending_fingerprints FROM "05_monitoring"."20_dtl_monitoring_rule_state" '
        'WHERE rule_id=$1',
        rule["id"],
    )
    pending: dict[str, str] = {}
    if state_row and state_row["pending_fingerprints"]:
        raw = state_row["pending_fingerprints"]
        pending = raw if isinstance(raw, dict) else json.loads(raw)

    transitions: list[AlertTransition] = []
    next_pending: dict[str, str] = {}

    # Detect breaches → firing_new or pending.
    for fp, (value, labels) in observed.items():
        if not _condition_breached(op, value, threshold):
            continue
        first_seen_iso = pending.get(fp)
        if first_seen_iso is None:
            if for_duration_s <= 0:
                transitions.append(
                    AlertTransition("firing_new", fp, value, threshold, labels)
                )
            else:
                next_pending[fp] = now.isoformat()
        else:
            try:
                first_seen = datetime.fromisoformat(first_seen_iso)
            except ValueError:
                first_seen = now
            elapsed = (now - first_seen).total_seconds()
            if elapsed >= for_duration_s:
                transitions.append(
                    AlertTransition("firing_new", fp, value, threshold, labels)
                )
            else:
                next_pending[fp] = first_seen_iso  # still waiting

    # Detect resolves: fingerprints currently in firing state whose observation
    # either disappeared or no longer breaches the threshold.
    firing_rows = await conn.fetch(
        'SELECT fingerprint FROM "05_monitoring".v_monitoring_alert_events '
        "WHERE rule_id = $1 AND state = 'firing'",
        rule["id"],
    )
    firing_fps = {r["fingerprint"] for r in firing_rows}
    for fp in firing_fps:
        obs = observed.get(fp)
        if obs is None or not _condition_breached(op, obs[0], threshold):
            transitions.append(
                AlertTransition("resolving", fp, 0.0, threshold, {})
            )

    # Persist state row.
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."20_dtl_monitoring_rule_state"
            (rule_id, pending_fingerprints, last_eval_at, updated_at)
        VALUES ($1, $2::jsonb, $3, $3)
        ON CONFLICT (rule_id) DO UPDATE SET
            pending_fingerprints = EXCLUDED.pending_fingerprints,
            last_eval_at         = EXCLUDED.last_eval_at,
            updated_at           = EXCLUDED.updated_at
        """,
        rule["id"], json.dumps(next_pending), now,
    )

    return transitions


__all__ = ["AlertTransition", "TransitionKind", "evaluate_rule", "fingerprint_for"]
