"""Credential signals — typing cadence, paste detection, sensitive actions."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


@signal(
    code="credential_paste_detected",
    name="Credential Paste Detected",
    description="Credentials were pasted rather than typed",
    category="credential",
    severity=55,
    tags=["credential", "paste"],
)
def compute_credential_paste_detected(ctx: dict, config: dict) -> SignalResult:
    hit = ctx.get("session", {}).get("credential_paste") is True
    return SignalResult(value=hit, confidence=0.95, details={})


@signal(
    code="credential_autofill_detected",
    name="Credential Autofill Detected",
    description="Credentials were entered via browser autofill",
    category="credential",
    severity=15,
    tags=["credential", "autofill"],
)
def compute_credential_autofill_detected(ctx: dict, config: dict) -> SignalResult:
    hit = ctx.get("session", {}).get("credential_autofill") is True
    return SignalResult(value=hit, confidence=0.9, details={})


@signal(
    code="credential_typing_too_fast",
    name="Credential Typing Too Fast",
    description="Credential keystrokes arrive faster than human typing",
    category="credential",
    severity=70,
    default_config={"min_ms_per_char": 30},
    tags=["credential", "cadence"],
)
def compute_credential_typing_too_fast(ctx: dict, config: dict) -> SignalResult:
    ms = ctx.get("session", {}).get("credential_ms_per_char")
    if ms is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("min_ms_per_char", 30)
    hit = ms < threshold
    return SignalResult(value=hit, confidence=0.9, details={"ms_per_char": ms, "threshold": threshold})


@signal(
    code="credential_typing_too_slow",
    name="Credential Typing Too Slow",
    description="Credential keystrokes arrive unusually slowly",
    category="credential",
    severity=40,
    default_config={"max_ms_per_char": 800},
    tags=["credential", "cadence"],
)
def compute_credential_typing_too_slow(ctx: dict, config: dict) -> SignalResult:
    ms = ctx.get("session", {}).get("credential_ms_per_char")
    if ms is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("max_ms_per_char", 800)
    hit = ms > threshold
    return SignalResult(value=hit, confidence=0.85, details={"ms_per_char": ms, "threshold": threshold})


@signal(
    code="credential_hesitation",
    name="Credential Hesitation",
    description="Long pause detected during credential entry",
    category="credential",
    severity=45,
    default_config={"pause_threshold_ms": 3000},
    tags=["credential", "cadence"],
)
def compute_credential_hesitation(ctx: dict, config: dict) -> SignalResult:
    pause = ctx.get("session", {}).get("credential_max_pause_ms")
    if pause is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("pause_threshold_ms", 3000)
    hit = pause > threshold
    return SignalResult(value=hit, confidence=0.85, details={"max_pause_ms": pause, "threshold": threshold})


@signal(
    code="credential_backspace_heavy",
    name="Credential Backspace Heavy",
    description="High ratio of backspace usage during credential entry",
    category="credential",
    severity=40,
    default_config={"max_backspace_ratio": 0.30},
    tags=["credential", "cadence"],
)
def compute_credential_backspace_heavy(ctx: dict, config: dict) -> SignalResult:
    ratio = ctx.get("session", {}).get("credential_backspace_ratio")
    if ratio is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("max_backspace_ratio", 0.30)
    hit = ratio > threshold
    return SignalResult(value=hit, confidence=0.85, details={"backspace_ratio": ratio, "threshold": threshold})


@signal(
    code="credential_retyped",
    name="Credential Retyped",
    description="Credentials were cleared and retyped multiple times",
    category="credential",
    severity=50,
    default_config={"min_retypes": 2},
    tags=["credential", "retype"],
)
def compute_credential_retyped(ctx: dict, config: dict) -> SignalResult:
    count = ctx.get("session", {}).get("credential_retype_count")
    if count is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    threshold = config.get("min_retypes", 2)
    hit = count >= threshold
    return SignalResult(value=hit, confidence=0.9, details={"retype_count": count, "threshold": threshold})


@signal(
    code="credential_cadence_mismatch",
    name="Credential Cadence Mismatch",
    description="Credential typing cadence diverges from stored profile",
    category="credential",
    signal_type="score",
    severity=65,
    default_config={"threshold": 0.60},
    tags=["credential", "drift"],
)
def compute_credential_cadence_mismatch(ctx: dict, config: dict) -> SignalResult:
    value = ctx.get("scores", {}).get("credential_drift", 0.0) or 0.0
    return SignalResult(value=value, confidence=0.85, details={"credential_drift": value})


@signal(
    code="mfa_bypass_attempt",
    name="MFA Bypass Attempt",
    description="MFA disable event with elevated behavioral drift",
    category="credential",
    severity=80,
    default_config={"drift_threshold": 0.50},
    tags=["credential", "mfa", "critical"],
)
def compute_mfa_bypass_attempt(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type")
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0) or 0.0
    threshold = config.get("drift_threshold", 0.50)
    hit = event_type == "mfa_disable" and drift > threshold
    return SignalResult(value=hit, confidence=0.9, details={"event_type": event_type, "drift": drift})


@signal(
    code="password_change_with_drift",
    name="Password Change With Drift",
    description="Password change event with elevated behavioral drift",
    category="credential",
    severity=75,
    default_config={"drift_threshold": 0.50},
    tags=["credential", "password", "critical"],
)
def compute_password_change_with_drift(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type")
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0) or 0.0
    threshold = config.get("drift_threshold", 0.50)
    hit = event_type == "password_change" and drift > threshold
    return SignalResult(value=hit, confidence=0.9, details={"event_type": event_type, "drift": drift})
