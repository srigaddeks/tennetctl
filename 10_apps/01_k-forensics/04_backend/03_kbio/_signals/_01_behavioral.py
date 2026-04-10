"""Behavioral signals — drift, identity, anomaly, consistency.

18 signals covering behavioral drift patterns, identity confidence,
cognitive load, and profile maturity indicators.
"""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


# ---------------------------------------------------------------------------
# 1. high_behavioral_drift
# ---------------------------------------------------------------------------
@signal(
    code="high_behavioral_drift",
    name="High Behavioral Drift",
    description="Behavioral drift score exceeds threshold",
    category="behavioral",
    signal_type="score",
    default_config={"threshold": 0.65},
    severity=70,
    tags=["behavioral", "drift"],
)
def compute_high_behavioral_drift(ctx: dict, config: dict) -> SignalResult:
    scores = ctx.get("scores", {})
    drift = scores.get("behavioral_drift", 0.0)
    threshold = config.get("threshold", 0.65)
    return SignalResult(
        value=drift,
        confidence=scores.get("confidence", 0.5),
        details={"drift": drift, "threshold": threshold, "exceeded": drift > threshold},
    )


# ---------------------------------------------------------------------------
# 2. critical_behavioral_drift
# ---------------------------------------------------------------------------
@signal(
    code="critical_behavioral_drift",
    name="Critical Behavioral Drift",
    description="Behavioral drift exceeds critical threshold",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.85},
    severity=90,
    tags=["behavioral", "drift", "critical"],
)
def compute_critical_behavioral_drift(ctx: dict, config: dict) -> SignalResult:
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0)
    threshold = config.get("threshold", 0.85)
    return SignalResult(
        value=drift > threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"drift": drift, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 3. credential_drift_elevated
# ---------------------------------------------------------------------------
@signal(
    code="credential_drift_elevated",
    name="Credential Drift Elevated",
    description="Credential-based drift score exceeds threshold",
    category="behavioral",
    signal_type="score",
    default_config={"threshold": 0.60},
    severity=75,
    tags=["behavioral", "credential", "drift"],
)
def compute_credential_drift_elevated(ctx: dict, config: dict) -> SignalResult:
    cred_drift = ctx.get("scores", {}).get("credential_drift")
    threshold = config.get("threshold", 0.60)
    if cred_drift is None:
        return SignalResult(value=0.0, confidence=0.0, details={"reason": "no_data"})
    return SignalResult(
        value=cred_drift,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"credential_drift": cred_drift, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 4. low_identity_confidence
# ---------------------------------------------------------------------------
@signal(
    code="low_identity_confidence",
    name="Low Identity Confidence",
    description="Identity confidence score is below threshold",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.40},
    severity=65,
    tags=["behavioral", "identity"],
)
def compute_low_identity_confidence(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("identity_confidence", 1.0)
    threshold = config.get("threshold", 0.40)
    return SignalResult(
        value=score < threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"identity_confidence": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 5. unfamiliar_navigation
# ---------------------------------------------------------------------------
@signal(
    code="unfamiliar_navigation",
    name="Unfamiliar Navigation",
    description="Familiarity score indicates unfamiliar navigation patterns",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.30},
    severity=40,
    tags=["behavioral", "familiarity"],
)
def compute_unfamiliar_navigation(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("familiarity_score", 1.0)
    threshold = config.get("threshold", 0.30)
    return SignalResult(
        value=score < threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"familiarity_score": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 6. high_cognitive_load
# ---------------------------------------------------------------------------
@signal(
    code="high_cognitive_load",
    name="High Cognitive Load",
    description="Cognitive load score exceeds normal threshold",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.70},
    severity=50,
    tags=["behavioral", "cognitive"],
)
def compute_high_cognitive_load(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("cognitive_load", 0.0)
    threshold = config.get("threshold", 0.70)
    return SignalResult(
        value=score > threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"cognitive_load": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 7. session_anomaly_elevated
# ---------------------------------------------------------------------------
@signal(
    code="session_anomaly_elevated",
    name="Session Anomaly Elevated",
    description="Session anomaly score exceeds threshold",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.65},
    severity=60,
    tags=["behavioral", "anomaly", "session"],
)
def compute_session_anomaly_elevated(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("session_anomaly", 0.0)
    threshold = config.get("threshold", 0.65)
    return SignalResult(
        value=score > threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"session_anomaly": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 8. velocity_spike
# ---------------------------------------------------------------------------
@signal(
    code="velocity_spike",
    name="Velocity Spike",
    description="Velocity anomaly exceeds threshold indicating rapid input",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.70},
    severity=70,
    tags=["behavioral", "velocity"],
)
def compute_velocity_spike(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("velocity_anomaly", 0.0)
    threshold = config.get("threshold", 0.70)
    return SignalResult(
        value=score > threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"velocity_anomaly": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 9. mid_session_takeover
# ---------------------------------------------------------------------------
@signal(
    code="mid_session_takeover",
    name="Mid-Session Takeover",
    description="Takeover probability indicates possible session hijack",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.60},
    severity=85,
    tags=["behavioral", "takeover"],
)
def compute_mid_session_takeover(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("takeover_probability", 0.0)
    threshold = config.get("threshold", 0.60)
    return SignalResult(
        value=score > threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"takeover_probability": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 10. pattern_break_detected
# ---------------------------------------------------------------------------
@signal(
    code="pattern_break_detected",
    name="Pattern Break Detected",
    description="Significant break from established behavioral patterns",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.65},
    severity=65,
    tags=["behavioral", "pattern"],
)
def compute_pattern_break_detected(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("pattern_break", 0.0)
    threshold = config.get("threshold", 0.65)
    return SignalResult(
        value=score > threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"pattern_break": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 11. low_consistency
# ---------------------------------------------------------------------------
@signal(
    code="low_consistency",
    name="Low Consistency",
    description="Behavioral consistency score is below threshold",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.35},
    severity=55,
    tags=["behavioral", "consistency"],
)
def compute_low_consistency(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("consistency_score", 1.0)
    threshold = config.get("threshold", 0.35)
    return SignalResult(
        value=score < threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"consistency_score": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 12. population_outlier
# ---------------------------------------------------------------------------
@signal(
    code="population_outlier",
    name="Population Outlier",
    description="Behavior deviates significantly from population norms",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.70},
    severity=50,
    tags=["behavioral", "population"],
)
def compute_population_outlier(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("population_anomaly", 0.0)
    threshold = config.get("threshold", 0.70)
    return SignalResult(
        value=score > threshold,
        confidence=ctx.get("scores", {}).get("confidence", 0.5),
        details={"population_anomaly": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 13. drift_trend_worsening
# ---------------------------------------------------------------------------
@signal(
    code="drift_trend_worsening",
    name="Drift Trend Worsening",
    description="Drift slope is positive and accelerating",
    category="behavioral",
    signal_type="boolean",
    default_config={"slope_threshold": 0.02},
    severity=60,
    tags=["behavioral", "drift", "trend"],
)
def compute_drift_trend_worsening(ctx: dict, config: dict) -> SignalResult:
    trend = ctx.get("drift_trend", {})
    slope = trend.get("slope", 0.0)
    accel = trend.get("acceleration", 0.0)
    slope_thresh = config.get("slope_threshold", 0.02)
    triggered = slope > slope_thresh and accel > 0
    return SignalResult(
        value=triggered,
        confidence=0.7 if trend else 0.0,
        details={"slope": slope, "acceleration": accel, "slope_threshold": slope_thresh},
    )


# ---------------------------------------------------------------------------
# 14. drift_spike_sudden
# ---------------------------------------------------------------------------
@signal(
    code="drift_spike_sudden",
    name="Drift Spike Sudden",
    description="Current drift deviates sharply from historical mean",
    category="behavioral",
    signal_type="boolean",
    default_config={"delta_threshold": 0.30},
    severity=75,
    tags=["behavioral", "drift", "spike"],
)
def compute_drift_spike_sudden(ctx: dict, config: dict) -> SignalResult:
    trend = ctx.get("drift_trend", {})
    mean = trend.get("mean", 0.0)
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0)
    delta = abs(mean - drift)
    delta_thresh = config.get("delta_threshold", 0.30)
    triggered = delta > delta_thresh and drift > mean
    return SignalResult(
        value=triggered,
        confidence=0.7 if trend else 0.0,
        details={"delta": delta, "drift": drift, "mean": mean, "delta_threshold": delta_thresh},
    )


# ---------------------------------------------------------------------------
# 15. multi_modality_concordance
# ---------------------------------------------------------------------------
@signal(
    code="multi_modality_concordance",
    name="Multi-Modality Concordance",
    description="Multiple input modalities show drift simultaneously",
    category="behavioral",
    signal_type="boolean",
    default_config={"drift_threshold": 0.60, "min_modalities": 2},
    severity=80,
    tags=["behavioral", "modality", "drift"],
)
def compute_multi_modality_concordance(ctx: dict, config: dict) -> SignalResult:
    md = ctx.get("modality_drift", {})
    drift_thresh = config.get("drift_threshold", 0.60)
    min_mod = config.get("min_modalities", 2)
    drifting = [k for k in ("keystroke", "pointer", "touch", "sensor")
                if md.get(k, 0.0) > drift_thresh]
    triggered = len(drifting) >= min_mod
    return SignalResult(
        value=triggered,
        confidence=0.8 if md else 0.0,
        details={"drifting_modalities": drifting, "count": len(drifting), "min_required": min_mod},
    )


# ---------------------------------------------------------------------------
# 16. keystroke_only_drift
# ---------------------------------------------------------------------------
@signal(
    code="keystroke_only_drift",
    name="Keystroke-Only Drift",
    description="Keystroke modality drifts while all others remain stable",
    category="behavioral",
    signal_type="boolean",
    default_config={"ks_threshold": 0.70, "other_max": 0.30},
    severity=55,
    tags=["behavioral", "modality", "keystroke"],
)
def compute_keystroke_only_drift(ctx: dict, config: dict) -> SignalResult:
    md = ctx.get("modality_drift", {})
    ks_thresh = config.get("ks_threshold", 0.70)
    other_max = config.get("other_max", 0.30)
    ks = md.get("keystroke", 0.0)
    others = [md.get(m, 0.0) for m in ("pointer", "touch", "sensor")]
    triggered = ks > ks_thresh and all(v < other_max for v in others)
    return SignalResult(
        value=triggered,
        confidence=0.8 if md else 0.0,
        details={"keystroke_drift": ks, "other_drifts": others},
    )


# ---------------------------------------------------------------------------
# 17. low_signal_richness
# ---------------------------------------------------------------------------
@signal(
    code="low_signal_richness",
    name="Low Signal Richness",
    description="Insufficient signal data for reliable scoring",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.30},
    severity=30,
    tags=["behavioral", "quality"],
)
def compute_low_signal_richness(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("signal_richness", 1.0)
    threshold = config.get("threshold", 0.30)
    return SignalResult(
        value=score < threshold,
        confidence=0.9,
        details={"signal_richness": score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 18. immature_profile
# ---------------------------------------------------------------------------
@signal(
    code="immature_profile",
    name="Immature Profile",
    description="User profile lacks sufficient history for reliable comparison",
    category="behavioral",
    signal_type="boolean",
    default_config={"threshold": 0.40},
    severity=25,
    tags=["behavioral", "quality", "profile"],
)
def compute_immature_profile(ctx: dict, config: dict) -> SignalResult:
    score = ctx.get("scores", {}).get("profile_maturity", 1.0)
    threshold = config.get("threshold", 0.40)
    return SignalResult(
        value=score < threshold,
        confidence=0.9,
        details={"profile_maturity": score, "threshold": threshold},
    )
