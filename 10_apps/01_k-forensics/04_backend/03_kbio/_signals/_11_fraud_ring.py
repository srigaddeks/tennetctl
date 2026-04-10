"""Fraud ring signals — cross-account patterns, coordinated activity."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


# ---------------------------------------------------------------------------
# 123. shared_device_cross_account
# ---------------------------------------------------------------------------
@signal(
    code="shared_device_cross_account",
    name="Shared Device Cross Account",
    description="Device is used by more accounts than allowed",
    category="fraud_ring",
    severity=70,
    default_config={"max_accounts": 2},
    tags=["fraud_ring", "device"],
)
def compute_shared_device_cross_account(ctx: dict, config: dict) -> SignalResult:
    users_count = ctx.get("device", {}).get("users_count", 0) or 0
    max_accts = config.get("max_accounts", 2)
    hit = users_count > max_accts
    return SignalResult(
        value=hit, confidence=0.85,
        details={"users_count": users_count, "max_accounts": max_accts},
    )


# ---------------------------------------------------------------------------
# 124. shared_ip_cross_account
# ---------------------------------------------------------------------------
@signal(
    code="shared_ip_cross_account",
    name="Shared IP Cross Account",
    description="IP address used by many accounts in 24 hours",
    category="fraud_ring",
    severity=60,
    default_config={"max_accounts_1h": 5},
    tags=["fraud_ring", "ip"],
)
def compute_shared_ip_cross_account(ctx: dict, config: dict) -> SignalResult:
    ip_users = ctx.get("network", {}).get("ip_user_count_24h", 0) or 0
    max_accts = config.get("max_accounts_1h", 5)
    hit = ip_users > max_accts
    return SignalResult(
        value=hit, confidence=0.8,
        details={"ip_user_count_24h": ip_users, "max_accounts": max_accts},
    )


# ---------------------------------------------------------------------------
# 125. similar_behavior_cross_account
# ---------------------------------------------------------------------------
@signal(
    code="similar_behavior_cross_account",
    name="Similar Behavior Cross Account",
    description="Behavioral similarity across accounts exceeds threshold",
    category="fraud_ring",
    severity=75,
    default_config={"similarity_threshold": 0.90},
    tags=["fraud_ring", "similarity"],
)
def compute_similar_behavior_cross_account(ctx: dict, config: dict) -> SignalResult:
    similarity = ctx.get("session", {}).get("cross_account_similarity")
    if similarity is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    thresh = config.get("similarity_threshold", 0.90)
    hit = similarity > thresh
    return SignalResult(
        value=hit, confidence=0.8,
        details={"cross_account_similarity": similarity, "threshold": thresh},
    )


# ---------------------------------------------------------------------------
# 126. rapid_account_creation_ip
# ---------------------------------------------------------------------------
@signal(
    code="rapid_account_creation_ip",
    name="Rapid Account Creation IP",
    description="Too many new accounts created from same IP in 24 hours",
    category="fraud_ring",
    severity=70,
    default_config={"max_new_accounts_24h": 3},
    tags=["fraud_ring", "account_creation"],
)
def compute_rapid_account_creation_ip(ctx: dict, config: dict) -> SignalResult:
    new_accts = ctx.get("network", {}).get("new_accounts_from_ip_24h")
    if new_accts is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    max_new = config.get("max_new_accounts_24h", 3)
    hit = new_accts > max_new
    return SignalResult(
        value=hit, confidence=0.85,
        details={"new_accounts_from_ip_24h": new_accts, "max_new_accounts_24h": max_new},
    )


# ---------------------------------------------------------------------------
# 127. coordinated_timing
# ---------------------------------------------------------------------------
@signal(
    code="coordinated_timing",
    name="Coordinated Timing",
    description="Actions coordinated across accounts within time window",
    category="fraud_ring",
    severity=65,
    default_config={"time_window_seconds": 5},
    tags=["fraud_ring", "coordination"],
)
def compute_coordinated_timing(ctx: dict, config: dict) -> SignalResult:
    coord_count = ctx.get("session", {}).get("coordinated_action_count")
    if coord_count is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    hit = coord_count > 0
    return SignalResult(
        value=hit, confidence=0.75,
        details={
            "coordinated_action_count": coord_count,
            "time_window_seconds": config.get("time_window_seconds", 5),
        },
    )


# ---------------------------------------------------------------------------
# 128. mule_account_pattern
# ---------------------------------------------------------------------------
@signal(
    code="mule_account_pattern",
    name="Mule Account Pattern",
    description="Young account performing financial transactions",
    category="fraud_ring",
    severity=80,
    default_config={"max_account_age_days": 7},
    tags=["fraud_ring", "mule"],
)
def compute_mule_account_pattern(ctx: dict, config: dict) -> SignalResult:
    user = ctx.get("user", {})
    session = ctx.get("session", {})
    age = user.get("account_age_days")
    event_type = session.get("event_type", "")
    max_age = config.get("max_account_age_days", 7)
    financial_events = {"transfer", "withdrawal", "payment"}
    if age is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    hit = age < max_age and event_type in financial_events
    return SignalResult(
        value=hit, confidence=0.8,
        details={"account_age_days": age, "event_type": event_type, "max_age_days": max_age},
    )
