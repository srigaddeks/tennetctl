"""Transaction signals — sensitive actions with behavioral anomalies."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult

_SENSITIVE_FINANCIAL = {"payment", "transfer", "withdrawal"}


# ---------------------------------------------------------------------------
# 115. high_value_action_low_trust
# ---------------------------------------------------------------------------
@signal(
    code="high_value_action_low_trust",
    name="High Value Action Low Trust",
    description="Financial action with low session trust",
    category="transaction",
    severity=75,
    default_config={"min_trust": 0.50},
    tags=["transaction", "trust"],
)
def compute_high_value_action_low_trust(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type", "")
    trust = ctx.get("scores", {}).get("session_trust", 1.0)
    min_trust = config.get("min_trust", 0.50)
    hit = event_type in _SENSITIVE_FINANCIAL and trust < min_trust
    return SignalResult(
        value=hit, confidence=0.8,
        details={"event_type": event_type, "session_trust": trust, "min_trust": min_trust},
    )


# ---------------------------------------------------------------------------
# 116. email_change_with_drift
# ---------------------------------------------------------------------------
@signal(
    code="email_change_with_drift",
    name="Email Change With Drift",
    description="Email change attempted with elevated behavioral drift",
    category="transaction",
    severity=75,
    default_config={"drift_threshold": 0.50},
    tags=["transaction", "account_change"],
)
def compute_email_change_with_drift(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type", "")
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0)
    thresh = config.get("drift_threshold", 0.50)
    hit = event_type == "email_change" and drift > thresh
    return SignalResult(
        value=hit, confidence=0.8,
        details={"event_type": event_type, "behavioral_drift": drift, "threshold": thresh},
    )


# ---------------------------------------------------------------------------
# 117. phone_change_with_drift
# ---------------------------------------------------------------------------
@signal(
    code="phone_change_with_drift",
    name="Phone Change With Drift",
    description="Phone change attempted with elevated behavioral drift",
    category="transaction",
    severity=75,
    default_config={"drift_threshold": 0.50},
    tags=["transaction", "account_change"],
)
def compute_phone_change_with_drift(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type", "")
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0)
    thresh = config.get("drift_threshold", 0.50)
    hit = event_type == "phone_change" and drift > thresh
    return SignalResult(
        value=hit, confidence=0.8,
        details={"event_type": event_type, "behavioral_drift": drift, "threshold": thresh},
    )


# ---------------------------------------------------------------------------
# 118. privilege_escalation_attempt
# ---------------------------------------------------------------------------
@signal(
    code="privilege_escalation_attempt",
    name="Privilege Escalation Attempt",
    description="Role change with elevated session anomaly",
    category="transaction",
    severity=80,
    default_config={"anomaly_threshold": 0.60},
    tags=["transaction", "privilege"],
)
def compute_privilege_escalation_attempt(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type", "")
    anomaly = ctx.get("scores", {}).get("session_anomaly", 0.0)
    thresh = config.get("anomaly_threshold", 0.60)
    hit = event_type == "role_change" and anomaly > thresh
    return SignalResult(
        value=hit, confidence=0.8,
        details={"event_type": event_type, "session_anomaly": anomaly, "threshold": thresh},
    )


# ---------------------------------------------------------------------------
# 119. data_export_with_anomaly
# ---------------------------------------------------------------------------
@signal(
    code="data_export_with_anomaly",
    name="Data Export With Anomaly",
    description="Data export with elevated session anomaly",
    category="transaction",
    severity=65,
    default_config={"anomaly_threshold": 0.50},
    tags=["transaction", "data_export"],
)
def compute_data_export_with_anomaly(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type", "")
    anomaly = ctx.get("scores", {}).get("session_anomaly", 0.0)
    thresh = config.get("anomaly_threshold", 0.50)
    hit = event_type == "data_export" and anomaly > thresh
    return SignalResult(
        value=hit, confidence=0.75,
        details={"event_type": event_type, "session_anomaly": anomaly, "threshold": thresh},
    )


# ---------------------------------------------------------------------------
# 120. payment_method_change
# ---------------------------------------------------------------------------
@signal(
    code="payment_method_change",
    name="Payment Method Change",
    description="Payment method change with elevated behavioral drift",
    category="transaction",
    severity=70,
    default_config={"drift_threshold": 0.40},
    tags=["transaction", "payment"],
)
def compute_payment_method_change(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type", "")
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0)
    thresh = config.get("drift_threshold", 0.40)
    hit = event_type == "payment_method_change" and drift > thresh
    return SignalResult(
        value=hit, confidence=0.8,
        details={"event_type": event_type, "behavioral_drift": drift, "threshold": thresh},
    )


# ---------------------------------------------------------------------------
# 121. address_change_with_drift
# ---------------------------------------------------------------------------
@signal(
    code="address_change_with_drift",
    name="Address Change With Drift",
    description="Address change attempted with elevated behavioral drift",
    category="transaction",
    severity=65,
    default_config={"drift_threshold": 0.50},
    tags=["transaction", "account_change"],
)
def compute_address_change_with_drift(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type", "")
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0)
    thresh = config.get("drift_threshold", 0.50)
    hit = event_type == "address_change" and drift > thresh
    return SignalResult(
        value=hit, confidence=0.75,
        details={"event_type": event_type, "behavioral_drift": drift, "threshold": thresh},
    )


# ---------------------------------------------------------------------------
# 122. beneficiary_add_new_session
# ---------------------------------------------------------------------------
@signal(
    code="beneficiary_add_new_session",
    name="Beneficiary Add New Session",
    description="Beneficiary added from new device or with behavioral drift",
    category="transaction",
    severity=75,
    default_config={"drift_threshold": 0.40},
    tags=["transaction", "beneficiary"],
)
def compute_beneficiary_add_new_session(ctx: dict, config: dict) -> SignalResult:
    event_type = ctx.get("session", {}).get("event_type", "")
    device = ctx.get("device", {})
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0)
    thresh = config.get("drift_threshold", 0.40)
    is_new = device.get("is_new", False)
    hit = event_type == "beneficiary_add" and (is_new or drift > thresh)
    return SignalResult(
        value=hit, confidence=0.8,
        details={"event_type": event_type, "is_new_device": is_new, "behavioral_drift": drift},
    )
