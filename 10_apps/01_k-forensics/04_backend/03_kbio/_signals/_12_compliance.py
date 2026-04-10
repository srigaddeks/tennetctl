"""Compliance signals — AML patterns, jurisdiction risk, structuring."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


# ---------------------------------------------------------------------------
# 129. unusual_transaction_pattern
# ---------------------------------------------------------------------------
@signal(
    code="unusual_transaction_pattern",
    name="Unusual Transaction Pattern",
    description="Transaction amount z-score exceeds stdev multiplier",
    category="compliance",
    severity=55,
    default_config={"stdev_multiplier": 3.0},
    tags=["compliance", "aml"],
)
def compute_unusual_transaction_pattern(ctx: dict, config: dict) -> SignalResult:
    zscore = ctx.get("session", {}).get("transaction_amount_zscore")
    if zscore is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    multiplier = config.get("stdev_multiplier", 3.0)
    hit = zscore > multiplier
    return SignalResult(
        value=hit, confidence=0.8,
        details={"transaction_amount_zscore": zscore, "stdev_multiplier": multiplier},
    )


# ---------------------------------------------------------------------------
# 130. structuring_pattern
# ---------------------------------------------------------------------------
@signal(
    code="structuring_pattern",
    name="Structuring Pattern",
    description="Multiple near-threshold transactions suggest structuring",
    category="compliance",
    severity=75,
    default_config={"threshold_amount": 10000, "max_txns_24h": 3},
    tags=["compliance", "aml", "structuring"],
)
def compute_structuring_pattern(ctx: dict, config: dict) -> SignalResult:
    count = ctx.get("session", {}).get("near_threshold_txn_count_24h")
    if count is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    max_txns = config.get("max_txns_24h", 3)
    hit = count >= max_txns
    return SignalResult(
        value=hit, confidence=0.85,
        details={
            "near_threshold_txn_count_24h": count,
            "max_txns_24h": max_txns,
            "threshold_amount": config.get("threshold_amount", 10000),
        },
    )


# ---------------------------------------------------------------------------
# 131. high_risk_jurisdiction
# ---------------------------------------------------------------------------
@signal(
    code="high_risk_jurisdiction",
    name="High Risk Jurisdiction",
    description="Session originates from a high-risk jurisdiction",
    category="compliance",
    severity=60,
    default_config={"jurisdictions": []},
    tags=["compliance", "jurisdiction"],
)
def compute_high_risk_jurisdiction(ctx: dict, config: dict) -> SignalResult:
    country = ctx.get("network", {}).get("country")
    jurisdictions = config.get("jurisdictions", [])
    hit = country is not None and country in jurisdictions
    return SignalResult(
        value=hit, confidence=0.95,
        details={"country": country, "jurisdictions_count": len(jurisdictions)},
    )


# ---------------------------------------------------------------------------
# 132. sanctions_country
# ---------------------------------------------------------------------------
@signal(
    code="sanctions_country",
    name="Sanctions Country",
    description="Session originates from a sanctioned country",
    category="compliance",
    severity=90,
    default_config={"countries": []},
    tags=["compliance", "sanctions"],
)
def compute_sanctions_country(ctx: dict, config: dict) -> SignalResult:
    country = ctx.get("network", {}).get("country")
    countries = config.get("countries", [])
    hit = country is not None and country in countries
    return SignalResult(
        value=hit, confidence=1.0,
        details={"country": country, "sanctioned_countries_count": len(countries)},
    )


# ---------------------------------------------------------------------------
# 133. rapid_fund_movement
# ---------------------------------------------------------------------------
@signal(
    code="rapid_fund_movement",
    name="Rapid Fund Movement",
    description="Deposit-to-withdrawal time is suspiciously short",
    category="compliance",
    severity=70,
    default_config={"max_hold_minutes": 30},
    tags=["compliance", "aml"],
)
def compute_rapid_fund_movement(ctx: dict, config: dict) -> SignalResult:
    minutes = ctx.get("session", {}).get("deposit_to_withdrawal_minutes")
    if minutes is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    max_hold = config.get("max_hold_minutes", 30)
    hit = minutes < max_hold
    return SignalResult(
        value=hit, confidence=0.8,
        details={"deposit_to_withdrawal_minutes": minutes, "max_hold_minutes": max_hold},
    )


# ---------------------------------------------------------------------------
# 134. round_amount_pattern
# ---------------------------------------------------------------------------
@signal(
    code="round_amount_pattern",
    name="Round Amount Pattern",
    description="Multiple transactions with round amounts",
    category="compliance",
    severity=45,
    default_config={"min_round_txns": 3},
    tags=["compliance", "aml"],
)
def compute_round_amount_pattern(ctx: dict, config: dict) -> SignalResult:
    count = ctx.get("session", {}).get("round_amount_txn_count")
    if count is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    min_txns = config.get("min_round_txns", 3)
    hit = count >= min_txns
    return SignalResult(
        value=hit, confidence=0.7,
        details={"round_amount_txn_count": count, "min_round_txns": min_txns},
    )
