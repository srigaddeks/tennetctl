"""Emit synthetic alert for SLO burn rate breach.

Effect node, tx=caller. Called by evaluator when fast/slow burn threshold crossed.
Reuses the alert event stream from Plan 40-03 so incidents group correctly.
"""

from __future__ import annotations

import json
import logging
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.repository"
)

logger = logging.getLogger("tennetctl.monitoring.slo.burn_alert")


async def emit_synthetic_alert(
    conn: Any,
    *,
    slo_id: str,
    org_id: str,
    breach_kind: str,  # "fast_burn" or "slow_burn"
    burn_rate: float,
    severity_id: int,
) -> str:
    """Emit a synthetic alert event for SLO burn rate breach.

    Creates an evt_monitoring_alert_events row with a virtual rule key "slo:{slo_id}".
    This allows existing alert → incident → escalation → action chain to handle SLO breaches.

    Args:
        conn: DB connection.
        slo_id: SLO that breached.
        org_id: Organization ID.
        breach_kind: "fast_burn" or "slow_burn".
        burn_rate: Observed burn rate multiplier.
        severity_id: Alert severity.

    Returns:
        Alert event ID.
    """
    event_id = _core_id.uuid7()

    # Create synthetic alert event
    # In production, would also update rule's rule_state or directly insert into alert_events table
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."60_evt_monitoring_alert_events"
            (id, rule_id, org_id, fingerprint, state, severity_id,
             value, threshold, labels, metadata, started_at, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
        """,
        event_id,
        f"slo:{slo_id}",  # Virtual rule key
        org_id,
        slo_id,  # Fingerprint is the SLO ID
        "firing",
        severity_id,
        burn_rate,  # Value is the burn rate multiplier
        1.0,  # Threshold (breach if burn_rate >= threshold, always true here)
        json.dumps({"breach_kind": breach_kind}),
        json.dumps({"burn_rate": burn_rate}),
    )

    logger.info(
        f"Emitted synthetic alert for SLO {slo_id} {breach_kind} breach: {event_id}"
    )
    return event_id


__all__ = ["emit_synthetic_alert"]
