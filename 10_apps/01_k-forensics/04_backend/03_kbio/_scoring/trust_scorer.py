"""kbio trust scorer.

Computes a composite trust score from multiple trust signals.
Higher score = more trusted (inverse of risk).

Trust scale: 0.0 (zero trust) to 1.0 (fully trusted).
"""
from __future__ import annotations

from typing import Any


# Weight configuration for trust factors
TRUST_WEIGHTS = {
    "behavioral_drift": 0.30,    # Low drift = high trust
    "device_familiarity": 0.20,  # Known device = trust
    "session_consistency": 0.15, # Stable session = trust
    "baseline_maturity": 0.15,   # Strong baseline = more reliable
    "bot_confidence": 0.10,      # Not a bot = trust
    "anomaly_inverse": 0.10,     # Not anomalous = trust
}


def compute_trust_score(
    *,
    drift_score: float,
    anomaly_score: float,
    bot_score: float,
    device_known: bool,
    device_age_days: int,
    baseline_quality: str,
    profile_maturity: float,
    session_state: dict[str, Any],
    confidence: float,
) -> dict[str, Any]:
    """Compute composite trust score from multiple signals.

    Each factor is normalized to 0.0-1.0 where higher = more trust.

    Args:
        drift_score: Behavioral drift (0=same, 1=different). -1 if unavailable.
        anomaly_score: Population anomaly (0=normal, 1=outlier). -1 if unavailable.
        bot_score: Bot probability (0=human, 1=bot).
        device_known: Whether this device has been seen before.
        device_age_days: Days since device was first seen (0 if new).
        baseline_quality: 'insufficient', 'forming', 'established', 'strong'.
        profile_maturity: 0.0-1.0 maturity of the user's behavioral profile.
        session_state: Session state dict from Valkey.
        confidence: Overall drift confidence score.

    Returns:
        {
            trust_score: float (0.0-1.0),
            factors: {factor_name: {value, weight, contribution}},
            trust_level: "high" | "medium" | "low" | "critical",
        }
    """
    factors: dict[str, dict[str, float]] = {}

    # Factor 1: Behavioral drift (invert: low drift = high trust)
    if drift_score >= 0:
        drift_trust = 1.0 - drift_score
    else:
        drift_trust = 0.5  # neutral when no data
    factors["behavioral_drift"] = {
        "value": round(drift_trust, 4),
        "weight": TRUST_WEIGHTS["behavioral_drift"],
    }

    # Factor 2: Device familiarity
    if device_known:
        device_trust = min(1.0, 0.6 + (device_age_days / 90.0) * 0.4)
    else:
        device_trust = 0.2  # new device = low trust
    factors["device_familiarity"] = {
        "value": round(device_trust, 4),
        "weight": TRUST_WEIGHTS["device_familiarity"],
    }

    # Factor 3: Session consistency (based on drift trend stability)
    drift_history = session_state.get("drift_history", [])
    session_trust = _compute_session_consistency(drift_history)
    factors["session_consistency"] = {
        "value": round(session_trust, 4),
        "weight": TRUST_WEIGHTS["session_consistency"],
    }

    # Factor 4: Baseline maturity
    maturity_map = {"insufficient": 0.1, "forming": 0.4, "established": 0.7, "strong": 1.0}
    maturity_trust = maturity_map.get(baseline_quality, 0.1)
    # Blend with numeric maturity
    maturity_trust = 0.6 * maturity_trust + 0.4 * min(1.0, profile_maturity)
    factors["baseline_maturity"] = {
        "value": round(maturity_trust, 4),
        "weight": TRUST_WEIGHTS["baseline_maturity"],
    }

    # Factor 5: Bot confidence (invert: not bot = trust)
    bot_trust = 1.0 - bot_score
    factors["bot_confidence"] = {
        "value": round(bot_trust, 4),
        "weight": TRUST_WEIGHTS["bot_confidence"],
    }

    # Factor 6: Anomaly inverse (not anomalous = trust)
    if anomaly_score >= 0:
        anomaly_trust = 1.0 - anomaly_score
    else:
        anomaly_trust = 0.5  # neutral when no data
    factors["anomaly_inverse"] = {
        "value": round(anomaly_trust, 4),
        "weight": TRUST_WEIGHTS["anomaly_inverse"],
    }

    # Compute weighted sum
    weighted_sum = 0.0
    total_weight = 0.0
    for name, factor in factors.items():
        contribution = factor["value"] * factor["weight"]
        factor["contribution"] = round(contribution, 4)
        weighted_sum += contribution
        total_weight += factor["weight"]

    trust_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    # Apply confidence dampening (low confidence pulls toward neutral)
    trust_score = trust_score * confidence + 0.5 * (1.0 - confidence)

    trust_score = round(min(1.0, max(0.0, trust_score)), 4)

    # Determine trust level
    if trust_score >= 0.75:
        trust_level = "high"
    elif trust_score >= 0.50:
        trust_level = "medium"
    elif trust_score >= 0.25:
        trust_level = "low"
    else:
        trust_level = "critical"

    return {
        "trust_score": trust_score,
        "factors": factors,
        "trust_level": trust_level,
    }


def _compute_session_consistency(drift_history: list[float]) -> float:
    """Compute session consistency from drift history stability.

    Stable sessions (low variance in drift) = high consistency.
    Rapidly changing drift = low consistency (possible takeover).
    """
    if len(drift_history) < 2:
        return 0.5  # neutral with insufficient data

    valid = [d for d in drift_history if d >= 0]
    if len(valid) < 2:
        return 0.5

    mean = sum(valid) / len(valid)
    variance = sum((d - mean) ** 2 for d in valid) / len(valid)

    # Low variance = high consistency
    # Variance of 0.01 → consistency ~0.9
    # Variance of 0.1 → consistency ~0.5
    # Variance of 0.5 → consistency ~0.1
    consistency = 1.0 / (1.0 + 10.0 * variance)

    # Also penalize high mean drift
    if mean > 0.5:
        consistency *= (1.0 - mean) * 2.0

    return max(0.0, min(1.0, consistency))
