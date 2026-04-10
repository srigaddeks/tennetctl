"""kbio trust scorer V2.

Computes trust scores at session, user, and device levels.

Session trust uses a multiplicative formula with decay.
User trust uses EMA across sessions.
Device trust uses familiarity and consistency.

Trust scale: 0.0 (zero trust) to 1.0 (fully trusted).
"""
from __future__ import annotations

from typing import Any

from ._math import clamp


def compute_session_trust(
    *,
    identity_confidence: float,
    bot_score: float,
    replay_score: float,
    automation_score: float,
    session_anomaly: float,
    takeover_probability: float,
    profile_maturity: float,
    previous_trust: float | None = None,
) -> dict[str, Any]:
    """V2 multiplicative trust formula with decay.

    session_trust = identity_confidence * humanness * anomaly * maturity

    where:
        humanness = (1-bot_score) * (1-replay_score) * (1-automation_score)
        anomaly = 1 - (0.5*session_anomaly + 0.5*takeover_probability)
        maturity = min(1.0, profile_maturity + 0.2)

    Decay: trust drops fast (one bad batch), recovers slowly.
        if previous_trust: apply decay_factor=0.7
        trust = max(calculated, previous*0.7 + calculated*0.3)

    Floor: if takeover > 0.8 OR bot > 0.8 -> floor at 0.1

    Args:
        identity_confidence: How confident we are this is the claimed user (0-1).
        bot_score: Bot detection score (0=human, 1=bot).
        replay_score: Replay detection score (0=fresh, 1=replayed).
        automation_score: Automation tool score (0=manual, 1=automated).
        session_anomaly: Session anomaly score (0=normal, 1=anomalous).
        takeover_probability: Account takeover probability (0=safe, 1=takeover).
        profile_maturity: User profile maturity (0=new, 1=established).
        previous_trust: Trust from previous batch in this session, if any.

    Returns:
        {
            session_trust: float (0.0-1.0),
            factors: {
                identity_confidence: float,
                humanness: float,
                anomaly_factor: float,
                maturity_factor: float,
                decay_applied: bool,
            },
            trust_level: "high" | "medium" | "low" | "critical",
        }
    """
    # Compute multiplicative factors
    humanness = (
        (1.0 - clamp(bot_score, 0.0, 1.0))
        * (1.0 - clamp(replay_score, 0.0, 1.0))
        * (1.0 - clamp(automation_score, 0.0, 1.0))
    )

    anomaly_factor = 1.0 - (
        0.5 * clamp(session_anomaly, 0.0, 1.0)
        + 0.5 * clamp(takeover_probability, 0.0, 1.0)
    )

    maturity_factor = min(1.0, clamp(profile_maturity, 0.0, 1.0) + 0.2)

    # Multiplicative trust
    calculated = (
        clamp(identity_confidence, 0.0, 1.0)
        * humanness
        * anomaly_factor
        * maturity_factor
    )

    # Decay: blend with previous trust for slow recovery
    decay_applied = False
    if previous_trust is not None:
        prev = clamp(previous_trust, 0.0, 1.0)
        blended = prev * 0.7 + calculated * 0.3
        calculated = max(calculated, blended)
        decay_applied = True

    # Floor: hard threats force trust to 0.1
    if takeover_probability > 0.8 or bot_score > 0.8:
        calculated = min(calculated, 0.1)

    session_trust = round(clamp(calculated, 0.0, 1.0), 4)

    # Determine trust level
    if session_trust >= 0.75:
        trust_level = "high"
    elif session_trust >= 0.50:
        trust_level = "medium"
    elif session_trust >= 0.25:
        trust_level = "low"
    else:
        trust_level = "critical"

    return {
        "session_trust": session_trust,
        "factors": {
            "identity_confidence": round(clamp(identity_confidence, 0.0, 1.0), 4),
            "humanness": round(humanness, 4),
            "anomaly_factor": round(anomaly_factor, 4),
            "maturity_factor": round(maturity_factor, 4),
            "decay_applied": decay_applied,
        },
        "trust_level": trust_level,
    }


def compute_user_trust(
    current_user_trust: float,
    session_outcome: float,
    challenge_passed: bool = False,
    challenge_failed: bool = False,
) -> float:
    """Long-term user trust EMA across sessions.

    Good session (> 0.7): trust += (1 - trust) * 0.05
    Bad session (< 0.3): trust -= trust * 0.15
    Mediocre (< 0.5): trust -= trust * 0.05
    Challenge passed: trust += (1 - trust) * 0.10
    Challenge failed: trust -= trust * 0.25
    Clamp to [0.05, 0.99]

    Args:
        current_user_trust: Current long-term user trust value.
        session_outcome: Trust score from the completed session.
        challenge_passed: Whether the user passed an explicit challenge.
        challenge_failed: Whether the user failed an explicit challenge.

    Returns:
        Updated user trust value (0.05-0.99).
    """
    trust = clamp(current_user_trust, 0.05, 0.99)

    # Apply session outcome adjustments
    if session_outcome > 0.7:
        trust += (1.0 - trust) * 0.05
    elif session_outcome < 0.3:
        trust -= trust * 0.15
    elif session_outcome < 0.5:
        trust -= trust * 0.05

    # Apply challenge results (can stack with session outcome)
    if challenge_passed:
        trust += (1.0 - trust) * 0.10
    if challenge_failed:
        trust -= trust * 0.25

    return round(clamp(trust, 0.05, 0.99), 4)


def compute_device_trust(
    device_sessions: int,
    device_age_days: int,
    recent_session_trusts: list[float],
) -> float:
    """Device trust based on familiarity and consistency.

    base = sessions / (sessions + 5)  # asymptotically -> 1.0
    consistency = mean(recent_session_trusts[-10:]) if available else 0.5
    device_trust = base * consistency

    Decay: not seen 30 days -> halve. Not seen 90 days -> reset to 0.3.

    Args:
        device_sessions: Total number of sessions from this device.
        device_age_days: Days since device was first seen.
            Also used as proxy for last-seen if the device is inactive.
        recent_session_trusts: Trust scores from recent sessions on this device.

    Returns:
        Device trust value (0.0-1.0).
    """
    sessions = max(0, device_sessions)

    # Base familiarity: asymptotically approaches 1.0
    base = sessions / (sessions + 5) if sessions > 0 else 0.0

    # Consistency from recent session trust scores
    recent = recent_session_trusts[-10:] if recent_session_trusts else []
    if recent:
        consistency = sum(recent) / len(recent)
    else:
        consistency = 0.5

    device_trust = base * clamp(consistency, 0.0, 1.0)

    # Decay based on device age (proxy for inactivity)
    # If device hasn't been seen recently, reduce trust
    if device_age_days > 90:
        device_trust = min(device_trust, 0.3)
    elif device_age_days > 30:
        device_trust *= 0.5

    return round(clamp(device_trust, 0.0, 1.0), 4)


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
    # Variance of 0.01 -> consistency ~0.9
    # Variance of 0.1 -> consistency ~0.5
    # Variance of 0.5 -> consistency ~0.1
    consistency = 1.0 / (1.0 + 10.0 * variance)

    # Also penalize high mean drift
    if mean > 0.5:
        consistency *= (1.0 - mean) * 2.0

    return max(0.0, min(1.0, consistency))
