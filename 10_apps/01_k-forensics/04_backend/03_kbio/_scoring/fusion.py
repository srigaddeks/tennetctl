"""Adaptive modality fusion for drift scoring.

Combines per-modality drift scores into a single composite score using
adaptive weights. Missing modalities redistribute weight proportionally.
Low event counts reduce weight.

V2: adds signal richness, meta scores, and full 22-score aggregation.
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


# ---------------------------------------------------------------------------
# V2: Signal richness, meta scores, and full score aggregation
# ---------------------------------------------------------------------------


def compute_signal_richness(
    modality_drifts: dict[str, float],
) -> float:
    """Fraction of modalities with valid drift data.

    signal_richness = count(valid modalities) / 4
    Valid = drift >= 0.

    Args:
        modality_drifts: {modality: drift_score} for all modalities.

    Returns:
        0.0-1.0 signal richness score.
    """
    total_modalities = len(BASE_WEIGHTS)
    if total_modalities == 0:
        return round(0.0, 4)

    valid_count = sum(
        1 for v in modality_drifts.values()
        if v >= 0.0
    )

    return round(min(1.0, valid_count / total_modalities), 4)


def compute_meta_scores(
    modality_drifts: dict[str, float],
    event_counts: dict[str, int],
    profile_maturity: float,
    total_events: int,
) -> dict[str, float]:
    """Compute all 3 meta scores: confidence, signal_richness, profile_maturity.

    Args:
        modality_drifts: {modality: drift_score} for all modalities.
        event_counts: {modality: event_count} for volume assessment.
        profile_maturity: Raw profile maturity from user profile (0-1).
        total_events: Total events in the current session.

    Returns:
        {"confidence": float, "signal_richness": float, "profile_maturity": float}
    """
    richness = compute_signal_richness(modality_drifts)
    confidence = compute_confidence(
        modality_drifts, event_counts, profile_maturity, total_events,
    )
    maturity = round(max(0.0, min(1.0, profile_maturity)), 4)

    return {
        "confidence": confidence,
        "signal_richness": richness,
        "profile_maturity": maturity,
    }


def aggregate_all_scores(
    identity: dict,
    anomaly: dict,
    humanness: dict,
    threat: dict,
    trust: dict,
    meta: dict,
) -> dict[str, Any]:
    """Collect all 22 scores into the unified ScoringResponse shape.

    Organizes scores from individual scorer outputs into a single
    structured response with categorized score groups.

    Args:
        identity: Identity scores dict. Expected keys:
            fused_drift, keystroke_drift, pointer_drift, touch_drift,
            sensor_drift, credential_drift
        anomaly: Anomaly scores dict. Expected keys:
            session_anomaly, population_anomaly, takeover_probability
        humanness: Humanness scores dict. Expected keys:
            bot_score, replay_score, automation_score
        threat: Threat scores dict. Expected keys:
            credential_drift (from credential scorer), velocity_anomaly
        trust: Trust scores dict. Expected keys:
            session_trust, user_trust, device_trust
        meta: Meta scores dict. Expected keys:
            confidence, signal_richness, profile_maturity

    Returns:
        A dict matching the full response structure with all score categories:
        {
            identity: {fused_drift, keystroke_drift, pointer_drift,
                       touch_drift, sensor_drift, credential_drift},
            anomaly: {session_anomaly, population_anomaly, takeover_probability},
            humanness: {bot_score, replay_score, automation_score},
            threat: {credential_drift, velocity_anomaly},
            trust: {session_trust, user_trust, device_trust},
            meta: {confidence, signal_richness, profile_maturity},
            score_count: int,
        }
    """
    result: dict[str, Any] = {
        "identity": {
            "fused_drift": round(identity.get("fused_drift", -1.0), 4),
            "keystroke_drift": round(identity.get("keystroke_drift", -1.0), 4),
            "pointer_drift": round(identity.get("pointer_drift", -1.0), 4),
            "touch_drift": round(identity.get("touch_drift", -1.0), 4),
            "sensor_drift": round(identity.get("sensor_drift", -1.0), 4),
            "credential_drift": round(identity.get("credential_drift", -1.0), 4),
        },
        "anomaly": {
            "session_anomaly": round(anomaly.get("session_anomaly", -1.0), 4),
            "population_anomaly": round(anomaly.get("population_anomaly", -1.0), 4),
            "takeover_probability": round(anomaly.get("takeover_probability", -1.0), 4),
        },
        "humanness": {
            "bot_score": round(humanness.get("bot_score", 0.0), 4),
            "replay_score": round(humanness.get("replay_score", 0.0), 4),
            "automation_score": round(humanness.get("automation_score", 0.0), 4),
        },
        "threat": {
            "credential_drift": round(threat.get("credential_drift", -1.0), 4),
            "velocity_anomaly": round(threat.get("velocity_anomaly", -1.0), 4),
        },
        "trust": {
            "session_trust": round(trust.get("session_trust", 0.0), 4),
            "user_trust": round(trust.get("user_trust", 0.5), 4),
            "device_trust": round(trust.get("device_trust", 0.0), 4),
        },
        "meta": {
            "confidence": round(meta.get("confidence", 0.0), 4),
            "signal_richness": round(meta.get("signal_richness", 0.0), 4),
            "profile_maturity": round(meta.get("profile_maturity", 0.0), 4),
        },
    }

    # Count total scores across all categories
    score_count = sum(len(v) for v in result.values() if isinstance(v, dict))
    result["score_count"] = score_count

    return result
