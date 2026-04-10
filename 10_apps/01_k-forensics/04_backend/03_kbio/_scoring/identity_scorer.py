"""kbio identity scorer (V2).

Computes identity-layer scores beyond raw drift:
- identity_confidence: how sure we are this IS the enrolled user
- familiarity_score: how familiar the user is with the current UI
- cognitive_load: estimated mental effort during interaction

Pure computation -- no I/O.
"""
from __future__ import annotations

from typing import Any

from ._math import clamp, sigmoid


# ---------------------------------------------------------------------------
# Weight constants
# ---------------------------------------------------------------------------

_FAMILIARITY_WEIGHTS = {
    "navigation_speed": 0.30,
    "scroll_efficiency": 0.20,
    "field_interaction_efficiency": 0.20,
    "direct_vs_search_ratio": 0.15,
    "time_to_interact": 0.15,
}

_COGNITIVE_WEIGHTS = {
    "rhythm_irregularity": 0.25,
    "movement_jerkiness": 0.20,
    "pause_frequency": 0.20,
    "error_rate": 0.20,
    "speed_variance": 0.15,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_identity_confidence(
    behavioral_drift: float,
    credential_drift: float | None,
    confidence: float,
) -> float:
    """Identity confidence = inverse of drift, adjusted by meta confidence.

    raw = 1.0 - max(behavioral_drift, credential_drift or 0)
    result = raw * confidence

    Returns 0.0-1.0.  Returns 0.0 if drift is unavailable (-1).
    """
    if behavioral_drift < 0:
        return 0.0

    effective_cred = max(credential_drift or 0.0, 0.0)
    worst_drift = max(behavioral_drift, effective_cred)
    raw = 1.0 - worst_drift
    result = raw * clamp(confidence, 0.0, 1.0)
    return round(clamp(result, 0.0, 1.0), 4)


def compute_familiarity_score(
    pointer_features: dict[str, Any],
    session_state: dict[str, Any],
) -> float:
    """How familiar is the user with this UI flow?

    Signals (all from pointer/interaction data):
    1. navigation_speed: time to first interaction per page (weight 0.30)
    2. scroll_efficiency: direct scrolls vs search scrolling (weight 0.20)
    3. field_interaction_efficiency: tab order vs random clicking (weight 0.20)
    4. direct_vs_search_ratio: straight mouse paths vs scanning (weight 0.15)
    5. time_to_interact: seconds from page load to first action (weight 0.15)

    Returns 0.0-1.0.  Higher = more familiar.  Returns -1.0 if no data.
    """
    movement = (pointer_features or {}).get("movement", {})
    idle = (pointer_features or {}).get("idle", {})
    clicks = (pointer_features or {}).get("clicks", {})

    if not movement:
        return -1.0

    signals: dict[str, float] = {}

    # 1. navigation_speed -- use path_efficiency + velocity ratio as proxy
    #    High velocity mean with low stdev = decisive, fast navigation
    v_mean = _safe_float(movement.get("velocity_mean"))
    v_stdev = _safe_float(movement.get("velocity_stdev"))
    if v_mean > 0:
        decisiveness = v_mean / (v_mean + v_stdev) if (v_mean + v_stdev) > 0 else 0.5
        signals["navigation_speed"] = clamp(decisiveness, 0.0, 1.0)
    else:
        signals["navigation_speed"] = 0.5

    # 2. scroll_efficiency -- fewer direction changes = efficient scrolling
    dir_changes = _safe_float(movement.get("direction_changes"))
    # Normalize: 0 changes = 1.0 familiarity, 20+ changes = 0.0
    signals["scroll_efficiency"] = clamp(1.0 - dir_changes / 20.0, 0.0, 1.0)

    # 3. field_interaction_efficiency -- overshoot rate as proxy
    #    Low overshoot = knows where targets are
    overshoot = _safe_float(clicks.get("overshoot_rate"))
    signals["field_interaction_efficiency"] = clamp(1.0 - overshoot, 0.0, 1.0)

    # 4. direct_vs_search_ratio -- path_efficiency directly
    path_eff = _safe_float(movement.get("path_efficiency"))
    signals["direct_vs_search_ratio"] = clamp(path_eff, 0.0, 1.0)

    # 5. time_to_interact -- idle count as proxy for hesitation
    #    More idles = more hesitation = less familiar
    idle_count = _safe_float(idle.get("count"))
    signals["time_to_interact"] = clamp(1.0 - idle_count / 10.0, 0.0, 1.0)

    # Weighted sum
    score = sum(
        signals[name] * weight
        for name, weight in _FAMILIARITY_WEIGHTS.items()
    )

    return round(clamp(score, 0.0, 1.0), 4)


def compute_cognitive_load(
    keystroke_features: dict[str, Any],
    pointer_features: dict[str, Any],
    session_state: dict[str, Any],
) -> float:
    """Estimate cognitive load from behavioral signals.

    Signals:
    1. rhythm_irregularity (0.25): keystroke rhythm variance (CV)
    2. movement_jerkiness (0.20): pointer acceleration variance
    3. pause_frequency (0.20): number of pauses per minute
    4. error_rate (0.20): backspace/correction rate
    5. speed_variance (0.15): coefficient of variation of interaction speed

    Returns 0.0 (automatic/low effort) to 1.0 (high effort/stress).
    Returns -1.0 if insufficient data.
    """
    ks = keystroke_features or {}
    ptr = pointer_features or {}

    rhythm = ks.get("rhythm", {})
    error_proxy = ks.get("error_proxy", {})
    movement = ptr.get("movement", {})

    kps_mean = _safe_float(rhythm.get("kps_mean"))
    kps_stdev = _safe_float(rhythm.get("kps_stdev"))
    pause_count = _safe_float(rhythm.get("pause_count"))
    backspace_rate = _safe_float(error_proxy.get("backspace_rate"))
    accel_mean = _safe_float(movement.get("acceleration_mean"))
    v_mean = _safe_float(movement.get("velocity_mean"))
    v_stdev = _safe_float(movement.get("velocity_stdev"))

    # Need at least one keystroke or pointer signal
    has_keystroke = kps_mean > 0 or pause_count > 0
    has_pointer = v_mean > 0 or accel_mean > 0
    if not has_keystroke and not has_pointer:
        return -1.0

    signals: dict[str, float] = {}

    # 1. rhythm_irregularity -- CV of typing speed
    #    High CV = irregular rhythm = high cognitive load
    if kps_mean > 0:
        cv = kps_stdev / kps_mean
        # Sigmoid-map: CV 0.3 -> ~0.5 load, CV 0.6+ -> high load
        signals["rhythm_irregularity"] = sigmoid((cv - 0.3) * 5.0)
    else:
        signals["rhythm_irregularity"] = 0.5

    # 2. movement_jerkiness -- acceleration magnitude as proxy
    #    Normalize: accel_mean > 500 is very jerky
    if accel_mean > 0:
        signals["movement_jerkiness"] = clamp(accel_mean / 500.0, 0.0, 1.0)
    else:
        signals["movement_jerkiness"] = 0.5

    # 3. pause_frequency -- pauses per window
    #    Normalize: 0 pauses = 0.0 load, 10+ pauses = 1.0 load
    signals["pause_frequency"] = clamp(pause_count / 10.0, 0.0, 1.0)

    # 4. error_rate -- backspace rate
    #    Normalize: 0% = 0.0 load, 20%+ = 1.0 load
    signals["error_rate"] = clamp(backspace_rate / 0.20, 0.0, 1.0)

    # 5. speed_variance -- CV of pointer velocity
    if v_mean > 0:
        speed_cv = v_stdev / v_mean
        signals["speed_variance"] = clamp(speed_cv / 1.5, 0.0, 1.0)
    else:
        signals["speed_variance"] = 0.5

    # Weighted sum
    score = sum(
        signals[name] * weight
        for name, weight in _COGNITIVE_WEIGHTS.items()
    )

    return round(clamp(score, 0.0, 1.0), 4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Convert to float, replacing None/-1 with default."""
    if val is None or val == -1:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
