"""kbio verdict engine (V2).

Maps session trust to verdicts with hard override rules.
This is the final decision layer -- consumes all 22 scores.

Pure computation -- no I/O.
"""
from __future__ import annotations

from typing import Any

from ._math import clamp

# Verdict action severity ordering (for max() comparisons)
_ACTION_ORDER = {"allow": 0, "monitor": 1, "challenge": 2, "step_up": 3, "block": 4}
_ORDER_TO_ACTION = {v: k for k, v in _ACTION_ORDER.items()}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def decide(
    session_trust: float,
    confidence: float,
    *,
    bot_score: float = 0.0,
    replay_score: float = 0.0,
    credential_drift: float | None = None,
    credential_confidence: float = 0.0,
    coercion_score: float = 0.0,
    takeover_probability: float = 0.0,
    grace_max_verdict: str | None = None,
) -> dict[str, Any]:
    """Determine verdict from scores.

    Base rules (from session_trust):
        confidence < 0.40          -> "monitor" (never escalate on low confidence)
        session_trust > 0.70       -> "allow"
        session_trust > 0.50       -> "monitor"
        session_trust > 0.30       -> "challenge"
        session_trust > 0.15       -> "step_up"
        else                       -> "block"

    Override rules (escalate only, never downgrade):
        bot_score > 0.85                                        -> "block"
        replay_score > 0.90                                     -> "block"
        credential_drift > 0.80 AND credential_confidence > 0.6 -> "step_up"
        coercion_score > 0.70                                   -> "challenge"
        takeover_probability > 0.75                              -> "block"

    Grace period: if grace_max_verdict is set, cap action at that level.

    Returns:
        {
            "action": str,
            "risk_level": str,       # low | medium | high | critical
            "primary_reason": str,
        }
    """
    trust = clamp(session_trust, 0.0, 1.0)
    conf = clamp(confidence, 0.0, 1.0)

    # ---- Base action from trust ----
    if conf < 0.40:
        base_action = "monitor"
    elif trust > 0.70:
        base_action = "allow"
    elif trust > 0.50:
        base_action = "monitor"
    elif trust > 0.30:
        base_action = "challenge"
    elif trust > 0.15:
        base_action = "step_up"
    else:
        base_action = "block"

    action = base_action

    # ---- Override rules (escalate only) ----
    if bot_score > 0.85:
        action = _escalate(action, "block")
    if replay_score > 0.90:
        action = _escalate(action, "block")
    if (
        credential_drift is not None
        and credential_drift > 0.80
        and credential_confidence > 0.60
    ):
        action = _escalate(action, "step_up")
    if coercion_score > 0.70:
        action = _escalate(action, "challenge")
    if takeover_probability > 0.75:
        action = _escalate(action, "block")

    # ---- Grace period cap ----
    if grace_max_verdict is not None and grace_max_verdict in _ACTION_ORDER:
        grace_level = _ACTION_ORDER[grace_max_verdict]
        current_level = _ACTION_ORDER.get(action, 0)
        if current_level > grace_level:
            action = grace_max_verdict

    return {
        "action": action,
        "risk_level": _risk_level(action),
        "primary_reason": _primary_reason(
            action,
            base_action=base_action,
            session_trust=trust,
            bot_score=bot_score,
            replay_score=replay_score,
            credential_drift=credential_drift,
            coercion_score=coercion_score,
            takeover_probability=takeover_probability,
        ),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _escalate(current: str, proposed: str) -> str:
    """Return the more severe of two actions."""
    cur = _ACTION_ORDER.get(current, 0)
    prop = _ACTION_ORDER.get(proposed, 0)
    winner = max(cur, prop)
    return _ORDER_TO_ACTION.get(winner, current)


def _risk_level(action: str) -> str:
    """Map action to risk level.

    allow    -> low
    monitor  -> medium
    challenge -> high
    step_up  -> critical
    block    -> critical
    """
    return {
        "allow": "low",
        "monitor": "medium",
        "challenge": "high",
        "step_up": "critical",
        "block": "critical",
    }.get(action, "medium")


def _primary_reason(
    action: str,
    *,
    base_action: str,
    session_trust: float,
    bot_score: float,
    replay_score: float,
    credential_drift: float | None,
    coercion_score: float,
    takeover_probability: float,
) -> str:
    """Determine the primary reason for the verdict.

    Returns the score name that most influenced the final decision.
    If the action was escalated from base, the override trigger is the reason.
    If the action matches base, session_trust is the reason.
    """
    # If action was escalated beyond base, find the override that caused it
    if _ACTION_ORDER.get(action, 0) > _ACTION_ORDER.get(base_action, 0):
        # Return the highest-severity override that fired
        overrides: list[tuple[float, str]] = []
        if bot_score > 0.85:
            overrides.append((bot_score, "bot_score"))
        if replay_score > 0.90:
            overrides.append((replay_score, "replay_score"))
        if takeover_probability > 0.75:
            overrides.append((takeover_probability, "takeover_probability"))
        if credential_drift is not None and credential_drift > 0.80:
            overrides.append((credential_drift, "credential_drift"))
        if coercion_score > 0.70:
            overrides.append((coercion_score, "coercion_score"))

        if overrides:
            overrides.sort(key=lambda t: t[0], reverse=True)
            return overrides[0][1]

    # Base action was used -- reason is trust level
    if session_trust > 0.70:
        return "session_trust_high"
    if session_trust > 0.50:
        return "session_trust_moderate"
    if session_trust > 0.30:
        return "session_trust_low"
    return "session_trust_critical"
