"""Session signals — duration, page navigation, pulse activity, concurrency."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


@signal(
    code="session_too_short",
    name="Session Too Short",
    description="Session duration is suspiciously short",
    category="session",
    severity=35,
    default_config={"min_seconds": 5},
    tags=["session", "duration"],
)
def compute_session_too_short(ctx: dict, config: dict) -> SignalResult:
    dur = ctx.get("session", {}).get("duration_seconds")
    if dur is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("min_seconds", 5)
    hit = dur < threshold
    return SignalResult(value=hit, confidence=0.9, details={"duration_seconds": dur, "threshold": threshold})


@signal(
    code="session_too_long",
    name="Session Too Long",
    description="Session duration exceeds reasonable maximum (8 hours)",
    category="session",
    severity=30,
    default_config={"max_seconds": 28800},
    tags=["session", "duration"],
)
def compute_session_too_long(ctx: dict, config: dict) -> SignalResult:
    dur = ctx.get("session", {}).get("duration_seconds")
    if dur is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("max_seconds", 28800)
    hit = dur > threshold
    return SignalResult(value=hit, confidence=0.85, details={"duration_seconds": dur, "threshold": threshold})


@signal(
    code="rapid_page_navigation",
    name="Rapid Page Navigation",
    description="Pages visited per minute exceeds human reading speed",
    category="session",
    severity=55,
    default_config={"max_pages_per_minute": 10},
    tags=["session", "navigation"],
)
def compute_rapid_page_navigation(ctx: dict, config: dict) -> SignalResult:
    session = ctx.get("session", {})
    pages = session.get("page_count", 0) or 0
    dur = session.get("duration_seconds", 0) or 0
    minutes = max(dur / 60, 1)
    rate = pages / minutes
    threshold = config.get("max_pages_per_minute", 10)
    hit = rate > threshold
    return SignalResult(value=hit, confidence=0.85, details={"pages_per_minute": round(rate, 2), "threshold": threshold})


@signal(
    code="single_page_session",
    name="Single Page Session",
    description="Session visited only one page or none",
    category="session",
    severity=20,
    tags=["session", "navigation"],
)
def compute_single_page_session(ctx: dict, config: dict) -> SignalResult:
    pages = ctx.get("session", {}).get("page_count", 0) or 0
    hit = pages <= 1
    return SignalResult(value=hit, confidence=0.9, details={"page_count": pages})


@signal(
    code="idle_session_long",
    name="Idle Session Long",
    description="Longest idle period in session exceeds threshold",
    category="session",
    severity=25,
    default_config={"idle_threshold_seconds": 1800},
    tags=["session", "idle"],
)
def compute_idle_session_long(ctx: dict, config: dict) -> SignalResult:
    idle = ctx.get("session", {}).get("max_idle_seconds")
    if idle is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("idle_threshold_seconds", 1800)
    hit = idle > threshold
    return SignalResult(value=hit, confidence=0.85, details={"max_idle_seconds": idle, "threshold": threshold})


@signal(
    code="concurrent_sessions",
    name="Concurrent Sessions",
    description="User has more active sessions than allowed",
    category="session",
    severity=60,
    default_config={"max_concurrent": 2},
    tags=["session", "concurrency"],
)
def compute_concurrent_sessions(ctx: dict, config: dict) -> SignalResult:
    count = ctx.get("user", {}).get("concurrent_session_count")
    if count is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("max_concurrent", 2)
    hit = count > threshold
    return SignalResult(value=hit, confidence=0.9, details={"concurrent": count, "threshold": threshold})


@signal(
    code="session_from_new_referrer",
    name="Session From New Referrer",
    description="Session arrived from a referrer not seen before",
    category="session",
    severity=30,
    tags=["session", "referrer"],
)
def compute_session_from_new_referrer(ctx: dict, config: dict) -> SignalResult:
    is_new = ctx.get("session", {}).get("referrer_is_new")
    if is_new is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    return SignalResult(value=is_new is True, confidence=0.85, details={})


@signal(
    code="high_pulse_count",
    name="High Pulse Count",
    description="Session generated an unusually high number of telemetry pulses",
    category="session",
    severity=45,
    default_config={"max_pulses": 500},
    tags=["session", "pulse"],
)
def compute_high_pulse_count(ctx: dict, config: dict) -> SignalResult:
    pulses = ctx.get("session", {}).get("pulse_count", 0) or 0
    threshold = config.get("max_pulses", 500)
    hit = pulses > threshold
    return SignalResult(value=hit, confidence=0.85, details={"pulse_count": pulses, "threshold": threshold})


@signal(
    code="low_pulse_count",
    name="Low Pulse Count",
    description="Pulse rate per minute is below expected minimum",
    category="session",
    severity=35,
    default_config={"min_pulses_per_minute": 1},
    tags=["session", "pulse"],
)
def compute_low_pulse_count(ctx: dict, config: dict) -> SignalResult:
    session = ctx.get("session", {})
    pulses = session.get("pulse_count", 0) or 0
    dur = session.get("duration_seconds", 0) or 0
    minutes = max(dur / 60, 1)
    rate = pulses / minutes
    threshold = config.get("min_pulses_per_minute", 1)
    hit = rate < threshold
    return SignalResult(value=hit, confidence=0.8, details={"pulses_per_minute": round(rate, 2), "threshold": threshold})


@signal(
    code="no_interaction_detected",
    name="No Interaction Detected",
    description="Session has zero telemetry pulses — no user interaction",
    category="session",
    severity=60,
    tags=["session", "pulse"],
)
def compute_no_interaction_detected(ctx: dict, config: dict) -> SignalResult:
    pulses = ctx.get("session", {}).get("pulse_count")
    hit = pulses is None or pulses == 0
    return SignalResult(value=hit, confidence=0.95, details={"pulse_count": pulses})


@signal(
    code="critical_action_first_session",
    name="Critical Action First Session",
    description="High-risk action performed on user's first session",
    category="session",
    severity=65,
    tags=["session", "critical_action"],
)
def compute_critical_action_first_session(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type")
    total = ctx.get("user", {}).get("total_sessions", 0) or 0
    critical = {"payment", "transfer", "password_change", "mfa_disable"}
    hit = event_type in critical and total <= 1
    return SignalResult(value=hit, confidence=0.9, details={"event_type": event_type, "total_sessions": total})


@signal(
    code="sensitive_page_with_drift",
    name="Sensitive Page With Drift",
    description="User is on a sensitive page with elevated behavioral drift",
    category="session",
    severity=60,
    default_config={"drift_threshold": 0.50},
    tags=["session", "drift", "sensitive"],
)
def compute_sensitive_page_with_drift(ctx: dict, config: dict) -> SignalResult:
    is_sensitive = ctx.get("session", {}).get("is_sensitive_page") is True
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0) or 0.0
    threshold = config.get("drift_threshold", 0.50)
    hit = is_sensitive and drift > threshold
    return SignalResult(value=hit, confidence=0.85, details={"is_sensitive_page": is_sensitive, "drift": drift})
