"""Historical signals — login frequency, device count, trust, location history."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


# ---------------------------------------------------------------------------
# 81. login_frequency_anomaly
# ---------------------------------------------------------------------------
@signal(
    code="login_frequency_anomaly",
    name="Login Frequency Anomaly",
    description="Login rate exceeds expected daily average by stdev multiplier",
    category="historical",
    severity=45,
    default_config={"stdev_multiplier": 3.0},
    tags=["historical", "frequency"],
)
def compute_login_frequency_anomaly(ctx: dict, config: dict) -> SignalResult:
    user = ctx.get("user", {})
    sessions_24h = user.get("sessions_last_24h", 0) or 0
    total = user.get("total_sessions", 0) or 0
    age_days = max(user.get("account_age_days", 1) or 1, 1)
    multiplier = config.get("stdev_multiplier", 3.0)
    expected_daily = total / age_days
    threshold = expected_daily * multiplier
    hit = sessions_24h > threshold
    return SignalResult(
        value=hit, confidence=0.8,
        details={"sessions_24h": sessions_24h, "threshold": round(threshold, 2)},
    )


# ---------------------------------------------------------------------------
# 82. device_count_anomaly
# ---------------------------------------------------------------------------
@signal(
    code="device_count_anomaly",
    name="Device Count Anomaly",
    description="User has more devices than the allowed maximum",
    category="historical",
    severity=50,
    default_config={"max_devices": 5},
    tags=["historical", "device"],
)
def compute_device_count_anomaly(ctx: dict, config: dict) -> SignalResult:
    total_devices = ctx.get("user", {}).get("total_devices", 0) or 0
    max_dev = config.get("max_devices", 5)
    hit = total_devices > max_dev
    return SignalResult(
        value=hit, confidence=0.9,
        details={"total_devices": total_devices, "max_devices": max_dev},
    )


# ---------------------------------------------------------------------------
# 83. failed_challenges_recent
# ---------------------------------------------------------------------------
@signal(
    code="failed_challenges_recent",
    name="Failed Challenges Recent",
    description="Too many failed challenges in the last 24 hours",
    category="historical",
    severity=70,
    default_config={"max_failures_24h": 3},
    tags=["historical", "challenge"],
)
def compute_failed_challenges_recent(ctx: dict, config: dict) -> SignalResult:
    failures = ctx.get("user", {}).get("failed_challenges_last_24h", 0) or 0
    max_fail = config.get("max_failures_24h", 3)
    hit = failures >= max_fail
    return SignalResult(
        value=hit, confidence=0.95,
        details={"failures_24h": failures, "max_failures_24h": max_fail},
    )


# ---------------------------------------------------------------------------
# 84. trust_level_degraded
# ---------------------------------------------------------------------------
@signal(
    code="trust_level_degraded",
    name="Trust Level Degraded",
    description="User trust is low despite sufficient session history",
    category="historical",
    severity=60,
    default_config={},
    tags=["historical", "trust"],
)
def compute_trust_level_degraded(ctx: dict, config: dict) -> SignalResult:
    user_trust = ctx.get("scores", {}).get("user_trust", 1.0)
    total_sessions = ctx.get("user", {}).get("total_sessions", 0) or 0
    hit = user_trust < 0.30 and total_sessions > 5
    return SignalResult(
        value=hit, confidence=0.85,
        details={"user_trust": user_trust, "total_sessions": total_sessions},
    )


# ---------------------------------------------------------------------------
# 85. never_challenged
# ---------------------------------------------------------------------------
@signal(
    code="never_challenged",
    name="Never Challenged",
    description="User has never been challenged despite many sessions",
    category="historical",
    severity=15,
    default_config={},
    tags=["historical", "challenge"],
)
def compute_never_challenged(ctx: dict, config: dict) -> SignalResult:
    user = ctx.get("user", {})
    failures = user.get("failed_challenges_last_24h")
    total_sessions = user.get("total_sessions", 0) or 0
    hit = (failures is None or failures == 0) and total_sessions > 10
    return SignalResult(
        value=hit, confidence=0.7,
        details={"failed_challenges_last_24h": failures, "total_sessions": total_sessions},
    )


# ---------------------------------------------------------------------------
# 86. previously_blocked
# ---------------------------------------------------------------------------
@signal(
    code="previously_blocked",
    name="Previously Blocked",
    description="User was previously blocked within lookback window",
    category="historical",
    severity=55,
    default_config={"lookback_days": 30},
    tags=["historical", "block"],
)
def compute_previously_blocked(ctx: dict, config: dict) -> SignalResult:
    blocked = ctx.get("user", {}).get("previously_blocked", False)
    hit = blocked is True
    return SignalResult(
        value=hit, confidence=0.95,
        details={"previously_blocked": blocked, "lookback_days": config.get("lookback_days", 30)},
    )


# ---------------------------------------------------------------------------
# 87. multiple_countries_24h
# ---------------------------------------------------------------------------
@signal(
    code="multiple_countries_24h",
    name="Multiple Countries 24h",
    description="User accessed from multiple countries in 24 hours",
    category="historical",
    severity=65,
    default_config={"max_countries_24h": 2},
    tags=["historical", "geo"],
)
def compute_multiple_countries_24h(ctx: dict, config: dict) -> SignalResult:
    user = ctx.get("user", {})
    countries = user.get("countries_last_24h") or user.get("known_countries") or []
    max_c = config.get("max_countries_24h", 2)
    hit = len(countries) > max_c
    return SignalResult(
        value=hit, confidence=0.9,
        details={"country_count": len(countries), "max_countries_24h": max_c},
    )


# ---------------------------------------------------------------------------
# 88. new_device_new_location
# ---------------------------------------------------------------------------
@signal(
    code="new_device_new_location",
    name="New Device New Location",
    description="Session from a new device in an unfamiliar country",
    category="historical",
    severity=70,
    default_config={},
    tags=["historical", "device", "geo"],
)
def compute_new_device_new_location(ctx: dict, config: dict) -> SignalResult:
    device = ctx.get("device", {})
    network = ctx.get("network", {})
    user = ctx.get("user", {})
    is_new = device.get("is_new", False)
    country = network.get("country")
    known = user.get("known_countries") or []
    hit = is_new and country is not None and country not in known
    return SignalResult(
        value=hit, confidence=0.85,
        details={"is_new": is_new, "country": country, "known_countries": known},
    )


# ---------------------------------------------------------------------------
# 89. known_device_new_location
# ---------------------------------------------------------------------------
@signal(
    code="known_device_new_location",
    name="Known Device New Location",
    description="Trusted device used from an unfamiliar country",
    category="historical",
    severity=40,
    default_config={},
    tags=["historical", "device", "geo"],
)
def compute_known_device_new_location(ctx: dict, config: dict) -> SignalResult:
    device = ctx.get("device", {})
    network = ctx.get("network", {})
    user = ctx.get("user", {})
    is_new = device.get("is_new", False)
    is_trusted = device.get("is_trusted", False)
    country = network.get("country")
    known = user.get("known_countries") or []
    hit = (not is_new) and is_trusted and country is not None and country not in known
    return SignalResult(
        value=hit, confidence=0.8,
        details={"is_new": is_new, "is_trusted": is_trusted, "country": country},
    )


# ---------------------------------------------------------------------------
# 90. new_device_known_location
# ---------------------------------------------------------------------------
@signal(
    code="new_device_known_location",
    name="New Device Known Location",
    description="New device from a familiar or unknown location",
    category="historical",
    severity=35,
    default_config={},
    tags=["historical", "device", "geo"],
)
def compute_new_device_known_location(ctx: dict, config: dict) -> SignalResult:
    device = ctx.get("device", {})
    network = ctx.get("network", {})
    user = ctx.get("user", {})
    is_new = device.get("is_new", False)
    country = network.get("country")
    known = user.get("known_countries") or []
    hit = is_new and (not known or country in known)
    return SignalResult(
        value=hit, confidence=0.8,
        details={"is_new": is_new, "country": country, "known_countries": known},
    )


# ---------------------------------------------------------------------------
# 91. baseline_quality_insufficient
# ---------------------------------------------------------------------------
@signal(
    code="baseline_quality_insufficient",
    name="Baseline Quality Insufficient",
    description="Behavioral baseline has not been sufficiently established",
    category="historical",
    severity=20,
    default_config={},
    tags=["historical", "quality"],
)
def compute_baseline_quality_insufficient(ctx: dict, config: dict) -> SignalResult:
    quality = ctx.get("baseline_quality", "unknown")
    hit = quality == "insufficient"
    return SignalResult(
        value=hit, confidence=0.95,
        details={"baseline_quality": quality},
    )


# ---------------------------------------------------------------------------
# 92. baseline_quality_established
# ---------------------------------------------------------------------------
@signal(
    code="baseline_quality_established",
    name="Baseline Quality Established",
    description="Behavioral baseline is established or strong",
    category="historical",
    severity=0,
    default_config={},
    tags=["historical", "quality"],
)
def compute_baseline_quality_established(ctx: dict, config: dict) -> SignalResult:
    quality = ctx.get("baseline_quality", "unknown")
    hit = quality in ("established", "strong")
    return SignalResult(
        value=hit, confidence=0.95,
        details={"baseline_quality": quality},
    )
