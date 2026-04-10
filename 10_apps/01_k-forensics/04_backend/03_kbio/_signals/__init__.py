"""Signal evaluation orchestrator.

Computes signals selectively based on org configuration.
All signal functions are pure compute — no I/O on the hot path.
Historical data is pre-fetched into ctx before signals run.
"""
from __future__ import annotations

import logging
from typing import Any

from ._registry import get_all_signals, get_signal, get_signals_by_category
from ._types import SignalResult

_log = logging.getLogger("kbio.signals")

# Force-import all category modules so @signal decorators execute.
from . import (  # noqa: F401, E402
    _01_behavioral,
    _02_device,
    _03_network,
    _04_temporal,
    _05_credential,
    _06_session,
    _07_historical,
    _08_bot,
    _09_social_engineering,
    _10_transaction,
    _11_fraud_ring,
    _12_compliance,
)

__all__ = [
    "compute_signals",
    "get_all_signals",
    "get_signal",
    "get_signals_by_category",
]


def compute_signals(
    ctx: dict[str, Any],
    signal_configs: dict[str, dict[str, Any]] | None = None,
    *,
    include: set[str] | None = None,
) -> dict[str, SignalResult]:
    """Compute signals against the evaluation context.

    Args:
        ctx: Enriched evaluation context (scores + device + network +
            user + session).  Read-only — signals never mutate it.
        signal_configs: Per-signal config overrides from org settings.
            Maps ``signal_code -> {param: value}``.
        include: If provided, only compute these signal codes.
            ``None`` means compute **all** registered signals.

    Returns:
        Dict mapping ``signal_code -> SignalResult``.
    """
    configs = signal_configs or {}
    results: dict[str, SignalResult] = {}
    registry = get_all_signals()

    for code, signal_def in registry.items():
        if include is not None and code not in include:
            continue

        merged_config = {**signal_def["default_config"], **configs.get(code, {})}

        try:
            result = signal_def["function"](ctx, merged_config)
            results[code] = result
        except Exception:
            _log.warning("Signal %s failed", code, exc_info=True)
            results[code] = SignalResult(
                value=False, confidence=0.0, details={"error": True}
            )

    return results
