"""Adaptive modality fusion for drift scoring.

Combines per-modality drift scores into a single composite score using
adaptive weights. Missing modalities redistribute weight proportionally.
Low event counts reduce weight.
"""

from __future__ import annotations

from typing import Any

# Base weights (sum to 1.0)
BASE_WEIGHTS: dict[str, float] = {
    "keystroke": 0.40,
    "pointer": 0.25,
    "touch": 0.20,
    "sensor": 0.15,
}

# Minimum event count for full weight
MIN_EVENTS_FULL_WEIGHT: dict[str, int] = {
    "keystroke": 20,
    "pointer": 10,
    "touch": 5,
    "sensor": 5,
}


def fuse(
    modality_drifts: dict[str, float],
    event_counts: dict[str, int] | None = None,
) -> tuple[float, dict[str, float]]:
    """Compute fused drift score with adaptive weights.

    Args:
        modality_drifts: {modality: drift_score} for available modalities.
            Only includes modalities with valid drift (not -1).
        event_counts: Optional {modality: count} for weight adjustment.

    Returns:
        (fused_drift, actual_weights) tuple.
    """
    if not modality_drifts:
        return -1.0, {}

    event_counts = event_counts or {}

    # Step 1: Filter to available modalities with valid drift
    available = {k: v for k, v in modality_drifts.items() if v >= 0.0}
    if not available:
        return -1.0, {}

    # Step 2: Compute raw weights (base weight, zeroed for missing)
    raw_weights: dict[str, float] = {}
    for modality in available:
        base = BASE_WEIGHTS.get(modality, 0.0)
        if base <= 0.0:
            continue

        # Reduce weight for low event counts
        count = event_counts.get(modality, 0)
        min_count = MIN_EVENTS_FULL_WEIGHT.get(modality, 10)
        if count > 0 and count < min_count:
            base *= count / min_count

        raw_weights[modality] = base

    if not raw_weights:
        return -1.0, {}

    # Step 3: Normalize weights to sum to 1.0
    total = sum(raw_weights.values())
    if total <= 0.0:
        return -1.0, {}

    actual_weights = {k: v / total for k, v in raw_weights.items()}

    # Step 4: Weighted sum
    fused = sum(actual_weights[m] * available[m] for m in actual_weights)

    return round(fused, 4), {k: round(v, 4) for k, v in actual_weights.items()}


def compute_confidence(
    modality_drifts: dict[str, float],
    event_counts: dict[str, int],
    profile_maturity: float,
    total_events_session: int,
) -> float:
    """Compute confidence score for the drift assessment.

    confidence = min(signal_richness, data_volume, profile_maturity)

    Returns 0.0-1.0.
    """
    # Signal richness: fraction of modalities with valid data
    available_count = sum(1 for v in modality_drifts.values() if v >= 0.0)
    total_modalities = len(BASE_WEIGHTS)
    signal_richness = available_count / total_modalities if total_modalities > 0 else 0.0

    # Data volume: min(1.0, events / 100)
    data_volume = min(1.0, total_events_session / 100.0) if total_events_session > 0 else 0.0

    # Profile maturity (0.0-1.0 from profile)
    maturity = max(0.0, min(1.0, profile_maturity))

    return round(min(signal_richness, data_volume, maturity), 4)
