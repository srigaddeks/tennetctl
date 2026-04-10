"""Fraud ring threat types."""
from __future__ import annotations

from ._registry import threat_type


@threat_type(
    code="ring-coordinated",
    name="Fraud Ring: Coordinated Timing",
    description="Monitors sessions with coordinated timing and cross-account shared IP.",
    category="fraud_ring",
    severity=70,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.coordinated_timing", "op": "==", "value": True},
            {"field": "signals.shared_ip_cross_account", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "Fraud ring: coordinated timing with shared IP",
    },
    default_config={},
    reason_template="Fraud ring: coordinated timing with shared IP",
    tags=["fraud_ring", "coordination"],
)
def ring_coordinated():
    pass


@threat_type(
    code="ring-mule-account",
    name="Fraud Ring: Mule Account",
    description="Blocks mule account patterns from datacenter IPs.",
    category="fraud_ring",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.mule_account_pattern", "op": "==", "value": True},
            {"field": "signals.datacenter_ip", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Fraud ring: mule account from datacenter IP",
    },
    default_config={},
    reason_template="Fraud ring: mule account from datacenter IP",
    tags=["fraud_ring", "mule", "critical"],
)
def ring_mule_account():
    pass


@threat_type(
    code="ring-device-sharing",
    name="Fraud Ring: Device Sharing",
    description="Monitors cross-account device sharing with rapid account creation from same IP.",
    category="fraud_ring",
    severity=65,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.shared_device_cross_account", "op": "==", "value": True},
            {"field": "signals.rapid_account_creation_ip", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "Fraud ring: device sharing with rapid account creation",
    },
    default_config={},
    reason_template="Fraud ring: device sharing with rapid account creation",
    tags=["fraud_ring", "device"],
)
def ring_device_sharing():
    pass


@threat_type(
    code="ring-similar-behavior",
    name="Fraud Ring: Similar Behavior",
    description="Challenges sessions with similar cross-account behavior on shared devices.",
    category="fraud_ring",
    severity=75,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.similar_behavior_cross_account", "op": "==", "value": True},
            {"field": "signals.shared_device_cross_account", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Fraud ring: similar behavior across accounts on shared device",
    },
    default_config={},
    reason_template="Fraud ring: similar behavior across accounts on shared device",
    tags=["fraud_ring", "coordination"],
)
def ring_similar_behavior():
    pass
