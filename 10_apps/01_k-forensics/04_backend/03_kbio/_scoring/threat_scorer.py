"""kbio threat scorer (V2).

Computes threat-level scores:
- coercion_score: user acting under duress/instruction
- impersonation_score: derived impostor probability

Pure computation -- no I/O.
"""
from __future__ import annotations

from typing import Any

from ._math import clamp, sigmoid


# ---------------------------------------------------------------------------
# Weight constants
# ---------------------------------------------------------------------------

_COERCION_WEIGHTS = {
    "hesitation_before_actions": 0.30,
    "navigation_anomaly": 0.25,
    "rhythm_breaks": 0.20,
    "re_entry_patterns": 0.15,
    "duration_anomaly": 0.10,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_coercion_score(
    keystroke_features: dict[str, Any],
    pointer_features: dict[str, Any],
    session_state: dict[str, Any],
    behavioral_drift: float,
    cognitive_load: float,
) -> float:
    """Detect when a legitimate user is acting under duress.

    Key insight: drift is LOW (it IS the right person) but behavior is
    abnormal.  If drift > 0.3, coercion is unlikely -- it is probably a
    different person, so we return 0.0.

    Signals:
    1. hesitation_before_actions (0.30): unusual pauses before high-value ops
    2. navigation_anomaly (0.25): direct-to-target without normal browsing
    3. rhythm_breaks (0.20): mid-word pauses suggesting dictation
    4. re_entry_patterns (0.15): typing, deleting, retyping (being corrected)
    5. duration_anomaly (0.10): session much longer than normal for action type

    Returns 0.0-1.0.
    """
    # If drift is high, the person is likely an impostor -- not coercion
    if behavioral_drift > 0.3 or behavioral_drift < 0:
        return 0.0

    ks = keystroke_features or {}
    ptr = pointer_features or {}
    ss = session_state or {}

    rhythm = ks.get("rhythm", {})
    error_proxy = ks.get("error_proxy", {})
    movement = ptr.get("movement", {})
    idle = ptr.get("idle", {})

    signals: dict[str, float] = {}

    # 1. hesitation_before_actions -- idle count as proxy for hesitation
    #    Under duress: pause -> act pattern (waiting for instruction)
    idle_count = _safe_float(idle.get("count"))
    # Normalize: 5+ idles = strong hesitation signal
    signals["hesitation_before_actions"] = clamp(idle_count / 5.0, 0.0, 1.0)

    # 2. navigation_anomaly -- very high path efficiency + low direction changes
    #    means the user went straight to target (told exactly where to go)
    path_eff = _safe_float(movement.get("path_efficiency"))
    dir_changes = _safe_float(movement.get("direction_changes"))
    if path_eff > 0:
        # High efficiency + low exploration = suspicious
        nav_direct = path_eff * clamp(1.0 - dir_changes / 10.0, 0.0, 1.0)
        signals["navigation_anomaly"] = clamp(nav_direct, 0.0, 1.0)
    else:
        signals["navigation_anomaly"] = 0.0

    # 3. rhythm_breaks -- kps_stdev / kps_mean (CV) indicates irregularity
    #    Mid-word pauses = listening to instructions between keystrokes
    kps_mean = _safe_float(rhythm.get("kps_mean"))
    kps_stdev = _safe_float(rhythm.get("kps_stdev"))
    pause_count = _safe_float(rhythm.get("pause_count"))
    if kps_mean > 0:
        cv = kps_stdev / kps_mean
        # High CV + many pauses = dictation pattern
        rhythm_signal = sigmoid((cv - 0.3) * 4.0) * clamp(pause_count / 8.0, 0.3, 1.0)
        signals["rhythm_breaks"] = clamp(rhythm_signal, 0.0, 1.0)
    else:
        signals["rhythm_breaks"] = 0.0

    # 4. re_entry_patterns -- high backspace + rapid same zone = type-delete-retype
    backspace_rate = _safe_float(error_proxy.get("backspace_rate"))
    rapid_same = _safe_float(error_proxy.get("rapid_same_zone_count"))
    re_entry = (backspace_rate / 0.15) * 0.6 + (rapid_same / 5.0) * 0.4
    signals["re_entry_patterns"] = clamp(re_entry, 0.0, 1.0)

    # 5. duration_anomaly -- session pulse count vs typical
    #    Under duress sessions tend to be unusually long for simple actions
    pulse_count = _safe_float(ss.get("pulse_count"))
    # Normalize: 20+ pulses for a simple session is suspicious
    signals["duration_anomaly"] = clamp(pulse_count / 20.0, 0.0, 1.0)

    # Weighted sum
    raw_score = sum(
        signals[name] * weight
        for name, weight in _COERCION_WEIGHTS.items()
    )

    # Boost by cognitive load when available (high cognitive load + low drift
    # is the classic coercion signature)
    if cognitive_load >= 0:
        raw_score = raw_score * 0.6 + cognitive_load * 0.4

    return round(clamp(raw_score, 0.0, 1.0), 4)


def compute_impersonation_score(
    behavioral_drift: float,
    credential_drift: float | None,
    familiarity_score: float,
    cognitive_load: float,
    bot_score: float,
) -> float:
    """Derived impostor probability combining multiple signals.

    impersonation = max(behavioral_drift, credential_drift or 0)
                  * (1 - bot_score)  -- if bot, it is automation not impersonation
                  * weight_from_familiarity_and_cognitive

    Enhanced: unfamiliar navigation with high cognitive load boosts the
    score since the impostor does not know the UI.

    Returns 0.0-1.0.
    """
    if behavioral_drift < 0:
        return 0.0

    effective_cred = max(credential_drift or 0.0, 0.0)
    worst_drift = max(behavioral_drift, effective_cred)

    # Bot guard: if this is automation, it is not impersonation
    human_factor = 1.0 - clamp(bot_score, 0.0, 1.0)

    # Familiarity and cognitive load modifiers
    # Unfamiliar (low familiarity) + high cognitive load = impostor struggling
    fam = familiarity_score if familiarity_score >= 0 else 0.5
    cog = cognitive_load if cognitive_load >= 0 else 0.5

    unfamiliarity_boost = (1.0 - fam) * 0.5 + cog * 0.5
    # Map to a 0.7-1.3 multiplier so it modulates but does not dominate
    modifier = 0.7 + unfamiliarity_boost * 0.6

    score = worst_drift * human_factor * modifier
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
