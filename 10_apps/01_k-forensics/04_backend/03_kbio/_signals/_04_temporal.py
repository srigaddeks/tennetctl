"""Temporal signals — time-of-day, account age, session velocity."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


@signal(
    code="outside_working_hours",
    name="Outside Working Hours",
    description="Session occurs outside the user's typical active hours",
    category="temporal",
    severity=25,
    default_config={"default_hours": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]},
    tags=["temporal", "hours"],
)
def compute_outside_working_hours(ctx: dict, config: dict) -> SignalResult:
    local_hour = ctx.get("session", {}).get("local_hour")
    if local_hour is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_local_hour"})
    typical = ctx.get("user", {}).get("typical_hours") or config.get("default_hours", [])
    hit = local_hour not in typical
    return SignalResult(value=hit, confidence=0.9, details={"local_hour": local_hour})


@signal(
    code="weekend_activity",
    name="Weekend Activity",
    description="Session occurs on a weekend day",
    category="temporal",
    severity=20,
    default_config={"weekend_days": [0, 6]},
    tags=["temporal", "weekend"],
)
def compute_weekend_activity(ctx: dict, config: dict) -> SignalResult:
    dow = ctx.get("session", {}).get("day_of_week")
    if dow is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_day_of_week"})
    weekend_days = config.get("weekend_days", [0, 6])
    hit = dow in weekend_days
    return SignalResult(value=hit, confidence=0.95, details={"day_of_week": dow})


@signal(
    code="dormant_account",
    name="Dormant Account",
    description="User has not had a session in a long time (90+ days)",
    category="temporal",
    severity=55,
    default_config={"dormant_days": 90},
    tags=["temporal", "dormancy"],
)
def compute_dormant_account(ctx: dict, config: dict) -> SignalResult:
    days = ctx.get("user", {}).get("days_since_last_session")
    if days is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("dormant_days", 90)
    hit = days > threshold
    return SignalResult(value=hit, confidence=0.9, details={"days": days, "threshold": threshold})


@signal(
    code="very_dormant_account",
    name="Very Dormant Account",
    description="User has not had a session in a very long time (180+ days)",
    category="temporal",
    severity=70,
    default_config={"dormant_days": 180},
    tags=["temporal", "dormancy"],
)
def compute_very_dormant_account(ctx: dict, config: dict) -> SignalResult:
    days = ctx.get("user", {}).get("days_since_last_session")
    if days is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("dormant_days", 180)
    hit = days > threshold
    return SignalResult(value=hit, confidence=0.9, details={"days": days, "threshold": threshold})


@signal(
    code="rapid_session_succession",
    name="Rapid Session Succession",
    description="Multiple sessions created in rapid succession",
    category="temporal",
    severity=50,
    default_config={"max_sessions_5min": 3},
    tags=["temporal", "velocity"],
)
def compute_rapid_session_succession(ctx: dict, config: dict) -> SignalResult:
    sessions_24h = ctx.get("user", {}).get("sessions_last_24h", 0) or 0
    threshold = config.get("max_sessions_5min", 3)
    hit = sessions_24h > threshold
    return SignalResult(value=hit, confidence=0.7, details={"sessions_last_24h": sessions_24h, "threshold": threshold})


@signal(
    code="late_night_activity",
    name="Late Night Activity",
    description="Session occurs during late night hours (1-5 AM)",
    category="temporal",
    severity=30,
    default_config={"start_hour": 1, "end_hour": 5},
    tags=["temporal", "hours"],
)
def compute_late_night_activity(ctx: dict, config: dict) -> SignalResult:
    local_hour = ctx.get("session", {}).get("local_hour")
    if local_hour is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_local_hour"})
    start = config.get("start_hour", 1)
    end = config.get("end_hour", 5)
    hit = start <= local_hour < end
    return SignalResult(value=hit, confidence=0.9, details={"local_hour": local_hour})


@signal(
    code="session_velocity_abnormal",
    name="Session Velocity Abnormal",
    description="Session frequency significantly exceeds historical average",
    category="temporal",
    severity=45,
    default_config={"stdev_multiplier": 3.0},
    tags=["temporal", "velocity"],
)
def compute_session_velocity_abnormal(ctx: dict, config: dict) -> SignalResult:
    user = ctx.get("user", {})
    sessions_24h = user.get("sessions_last_24h", 0) or 0
    total = user.get("total_sessions", 0) or 0
    age_days = max(user.get("account_age_days", 1) or 1, 1)
    multiplier = config.get("stdev_multiplier", 3.0)
    expected_daily = total / age_days
    threshold = expected_daily * multiplier * 24
    hit = sessions_24h > threshold
    return SignalResult(
        value=hit, confidence=0.75,
        details={"sessions_24h": sessions_24h, "threshold": round(threshold, 2)},
    )


@signal(
    code="first_session_ever",
    name="First Session Ever",
    description="This is the user's very first session",
    category="temporal",
    severity=20,
    tags=["temporal", "new_user"],
)
def compute_first_session_ever(ctx: dict, config: dict) -> SignalResult:
    total = ctx.get("user", {}).get("total_sessions")
    hit = total is None or total == 0
    return SignalResult(value=hit, confidence=1.0, details={"total_sessions": total})


@signal(
    code="account_age_young",
    name="Account Age Young",
    description="User account was created very recently",
    category="temporal",
    severity=35,
    default_config={"min_age_days": 7},
    tags=["temporal", "new_user"],
)
def compute_account_age_young(ctx: dict, config: dict) -> SignalResult:
    age = ctx.get("user", {}).get("account_age_days")
    if age is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("min_age_days", 7)
    hit = age < threshold
    return SignalResult(value=hit, confidence=0.95, details={"age_days": age, "threshold": threshold})


@signal(
    code="burst_activity",
    name="Burst Activity",
    description="Unusually high number of sessions in 24 hours",
    category="temporal",
    severity=50,
    default_config={"max_sessions_24h": 10},
    tags=["temporal", "velocity"],
)
def compute_burst_activity(ctx: dict, config: dict) -> SignalResult:
    sessions_24h = ctx.get("user", {}).get("sessions_last_24h", 0) or 0
    threshold = config.get("max_sessions_24h", 10)
    hit = sessions_24h > threshold
    return SignalResult(value=hit, confidence=0.85, details={"sessions_24h": sessions_24h, "threshold": threshold})
