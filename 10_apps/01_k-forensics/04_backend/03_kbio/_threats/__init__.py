"""Threat type evaluation orchestrator.

Evaluates threat types by running their JSON conditions against the
signal-enriched evaluation context using the kprotect rule engine.
"""
from __future__ import annotations

import importlib
import logging
import time
from typing import Any

from ._registry import get_all_threat_types, get_threat_type, get_threat_types_by_category
from ._types import ThreatResult

_log = logging.getLogger("kbio.threats")

# Force-import all category modules so @threat_type decorators execute.
from . import (  # noqa: F401, E402
    _01_account_takeover,
    _02_bot_attacks,
    _03_identity_fraud,
    _04_social_engineering,
    _05_network_threats,
    _06_transaction_fraud,
    _07_fraud_ring,
    _08_compliance,
)

__all__ = [
    "evaluate_threats",
    "get_all_threat_types",
    "get_threat_type",
    "get_threat_types_by_category",
]


def _extract_matched_signals(conditions: dict[str, Any]) -> list[str]:
    """Extract signal codes referenced in a threat type's conditions."""
    codes: list[str] = []
    for rule in conditions.get("rules", []):
        field = rule.get("field", "")
        if field.startswith("signals."):
            codes.append(field.split(".", 1)[1])
    return codes


def evaluate_threats(
    ctx: dict[str, Any],
    *,
    include: set[str] | None = None,
    config_overrides: dict[str, dict[str, Any]] | None = None,
) -> list[ThreatResult]:
    """Evaluate threat types against the signal-enriched context.

    Uses the kprotect rule engine's condition evaluation logic
    (pure computation, no I/O).

    Args:
        ctx: Evaluation context with ``signals`` dict populated.
        include: If provided, only evaluate these threat type codes.
            ``None`` means evaluate **all** registered threat types.
        config_overrides: Per-threat-type config overrides.

    Returns:
        List of detected threats (only those whose conditions matched).
    """
    _engine = importlib.import_module(
        "02_features.evaluate.rule_engine"
    )

    configs = config_overrides or {}
    registry = get_all_threat_types()
    detected: list[ThreatResult] = []

    for code, threat_def in registry.items():
        if include is not None and code not in include:
            continue

        conditions = threat_def["conditions"]
        merged_config = {**threat_def["default_config"], **configs.get(code, {})}

        start = time.perf_counter()
        action, reason, _ = _engine.evaluate_policy(
            conditions, ctx, merged_config
        )
        elapsed = round((time.perf_counter() - start) * 1000, 4)

        if action != "allow":
            detected.append(
                ThreatResult(
                    code=code,
                    name=threat_def["name"],
                    category=threat_def["category"],
                    severity=threat_def["severity"],
                    default_action=threat_def["default_action"],
                    reason=reason or "",
                    matched_signals=_extract_matched_signals(conditions),
                    execution_ms=elapsed,
                )
            )

    return detected
