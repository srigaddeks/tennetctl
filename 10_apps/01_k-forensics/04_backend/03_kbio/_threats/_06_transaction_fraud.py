"""Transaction fraud threat types."""
from __future__ import annotations

from ._registry import threat_type


@threat_type(
    code="txn-high-value-risky",
    name="Transaction Fraud: High Value Risky",
    description="Challenges high-value actions with low trust from a new device.",
    category="transaction_fraud",
    severity=80,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.high_value_action_low_trust", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Transaction fraud: high-value action with low trust on new device",
    },
    default_config={},
    reason_template="Transaction fraud: high-value action with low trust on new device",
    tags=["transaction", "fraud"],
)
def txn_high_value_risky():
    pass


@threat_type(
    code="txn-credential-change",
    name="Transaction Fraud: Credential Change with Drift",
    description="Blocks password changes with behavioral drift from a new device.",
    category="transaction_fraud",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.password_change_with_drift", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Transaction fraud: password change with drift on new device",
    },
    default_config={},
    reason_template="Transaction fraud: password change with drift on new device",
    tags=["transaction", "fraud", "credential"],
)
def txn_credential_change():
    pass


@threat_type(
    code="txn-mfa-disable",
    name="Transaction Fraud: MFA Disable Attempt",
    description="Blocks MFA bypass attempts from a new device.",
    category="transaction_fraud",
    severity=90,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.mfa_bypass_attempt", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Transaction fraud: MFA disable attempt from new device",
    },
    default_config={},
    reason_template="Transaction fraud: MFA disable attempt from new device",
    tags=["transaction", "fraud", "critical"],
)
def txn_mfa_disable():
    pass


@threat_type(
    code="txn-payment-change",
    name="Transaction Fraud: Payment Method Change",
    description="Challenges payment method changes on dormant accounts.",
    category="transaction_fraud",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.payment_method_change", "op": "==", "value": True},
            {"field": "signals.dormant_account", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Transaction fraud: payment change on dormant account",
    },
    default_config={},
    reason_template="Transaction fraud: payment change on dormant account",
    tags=["transaction", "fraud"],
)
def txn_payment_change():
    pass


@threat_type(
    code="txn-data-exfil",
    name="Transaction Fraud: Data Exfiltration",
    description="Blocks data export anomalies from bot sessions.",
    category="transaction_fraud",
    severity=80,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.data_export_with_anomaly", "op": "==", "value": True},
            {"field": "signals.is_bot", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Transaction fraud: data exfiltration by bot",
    },
    default_config={},
    reason_template="Transaction fraud: data exfiltration by bot",
    tags=["transaction", "fraud", "exfil"],
)
def txn_data_exfil():
    pass


@threat_type(
    code="txn-privilege-escalation",
    name="Transaction Fraud: Privilege Escalation",
    description="Blocks privilege escalation attempts from a new device.",
    category="transaction_fraud",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.privilege_escalation_attempt", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Transaction fraud: privilege escalation from new device",
    },
    default_config={},
    reason_template="Transaction fraud: privilege escalation from new device",
    tags=["transaction", "fraud", "critical"],
)
def txn_privilege_escalation():
    pass
