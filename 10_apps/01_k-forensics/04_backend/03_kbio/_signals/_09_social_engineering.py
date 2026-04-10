"""Social engineering signals — coercion, coaching, impersonation."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


# ---------------------------------------------------------------------------
# 107. coercion_detected
# ---------------------------------------------------------------------------
@signal(
    code="coercion_detected",
    name="Coercion Detected",
    description="Coercion score exceeds threshold",
    category="social_engineering",
    severity=75,
    default_config={"threshold": 0.60},
    tags=["social_engineering", "coercion"],
)
def compute_coercion_detected(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("coercion_score", 0.0)
    threshold = config.get("threshold", 0.60)
    return SignalResult(
        value=score > threshold,
        confidence=0.7,
        details={"coercion_score": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 108. hesitation_before_action
# ---------------------------------------------------------------------------
@signal(
    code="hesitation_before_action",
    name="Hesitation Before Action",
    description="Unusually long pause before a critical action",
    category="social_engineering",
    severity=50,
    default_config={"pause_ms": 5000},
    tags=["social_engineering", "hesitation"],
)
def compute_hesitation_before_action(ctx: dict, config: dict) -> SignalResult:
    pause = ctx.get("session", {}).get("pre_action_pause_ms")
    pause_ms = config.get("pause_ms", 5000)
    if pause is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    hit = pause > pause_ms
    return SignalResult(
        value=hit, confidence=0.7,
        details={"pre_action_pause_ms": pause, "threshold_ms": pause_ms},
    )


# ---------------------------------------------------------------------------
# 109. coached_behavior
# ---------------------------------------------------------------------------
@signal(
    code="coached_behavior",
    name="Coached Behavior",
    description="Low drift combined with high cognitive load suggests coaching",
    category="social_engineering",
    severity=65,
    default_config={"max_drift": 0.30, "min_cognitive_load": 0.65},
    tags=["social_engineering", "coaching"],
)
def compute_coached_behavior(ctx: dict, config: dict) -> SignalResult:
    scores = ctx.get("scores", {})
    drift = scores.get("behavioral_drift", 1.0)
    cog_load = scores.get("cognitive_load", 0.0)
    max_drift = config.get("max_drift", 0.30)
    min_cog = config.get("min_cognitive_load", 0.65)
    hit = drift < max_drift and cog_load > min_cog
    return SignalResult(
        value=hit, confidence=0.65,
        details={"behavioral_drift": drift, "cognitive_load": cog_load},
    )


# ---------------------------------------------------------------------------
# 110. re_entry_pattern
# ---------------------------------------------------------------------------
@signal(
    code="re_entry_pattern",
    name="Re-Entry Pattern",
    description="User re-types input multiple times suggesting dictation",
    category="social_engineering",
    severity=55,
    default_config={"min_retypes": 3},
    tags=["social_engineering", "retype"],
)
def compute_re_entry_pattern(ctx: dict, config: dict) -> SignalResult:
    retypes = ctx.get("session", {}).get("retype_count", 0) or 0
    min_r = config.get("min_retypes", 3)
    hit = retypes >= min_r
    return SignalResult(
        value=hit, confidence=0.7,
        details={"retype_count": retypes, "min_retypes": min_r},
    )


# ---------------------------------------------------------------------------
# 111. rhythm_breaks_frequent
# ---------------------------------------------------------------------------
@signal(
    code="rhythm_breaks_frequent",
    name="Rhythm Breaks Frequent",
    description="Frequent rhythm breaks indicating external interruption",
    category="social_engineering",
    severity=45,
    default_config={"min_breaks": 5},
    tags=["social_engineering", "rhythm"],
)
def compute_rhythm_breaks_frequent(ctx: dict, config: dict) -> SignalResult:
    breaks = ctx.get("session", {}).get("rhythm_break_count", 0) or 0
    min_b = config.get("min_breaks", 5)
    hit = breaks >= min_b
    return SignalResult(
        value=hit, confidence=0.65,
        details={"rhythm_break_count": breaks, "min_breaks": min_b},
    )


# ---------------------------------------------------------------------------
# 112. navigation_anomaly_under_duress
# ---------------------------------------------------------------------------
@signal(
    code="navigation_anomaly_under_duress",
    name="Navigation Anomaly Under Duress",
    description="Unfamiliar navigation combined with coercion indicators",
    category="social_engineering",
    severity=60,
    default_config={},
    tags=["social_engineering", "navigation", "coercion"],
)
def compute_navigation_anomaly_under_duress(ctx: dict, config: dict) -> SignalResult:
    scores = ctx.get("scores", {})
    familiarity = scores.get("familiarity_score", 1.0)
    coercion = scores.get("coercion_score", 0.0)
    hit = familiarity < 0.30 and coercion > 0.40
    return SignalResult(
        value=hit, confidence=0.65,
        details={"familiarity_score": familiarity, "coercion_score": coercion},
    )


# ---------------------------------------------------------------------------
# 113. impersonation_detected
# ---------------------------------------------------------------------------
@signal(
    code="impersonation_detected",
    name="Impersonation Detected",
    description="Impersonation score exceeds threshold",
    category="social_engineering",
    severity=75,
    default_config={"threshold": 0.65},
    tags=["social_engineering", "impersonation"],
)
def compute_impersonation_detected(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("impersonation_score", 0.0)
    threshold = config.get("threshold", 0.65)
    return SignalResult(
        value=score > threshold,
        confidence=0.7,
        details={"impersonation_score": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 114. high_drift_low_bot
# ---------------------------------------------------------------------------
@signal(
    code="high_drift_low_bot",
    name="High Drift Low Bot",
    description="High behavioral drift with low bot score suggests human impersonator",
    category="social_engineering",
    severity=70,
    default_config={"drift_threshold": 0.70, "bot_max": 0.30},
    tags=["social_engineering", "drift", "impersonation"],
)
def compute_high_drift_low_bot(ctx: dict, config: dict) -> SignalResult:
    scores = ctx.get("scores", {})
    drift = scores.get("behavioral_drift", 0.0)
    bot = scores.get("bot_score", 0.0)
    drift_thresh = config.get("drift_threshold", 0.70)
    bot_max = config.get("bot_max", 0.30)
    hit = drift > drift_thresh and bot < bot_max
    return SignalResult(
        value=hit, confidence=0.7,
        details={"behavioral_drift": drift, "bot_score": bot},
    )
