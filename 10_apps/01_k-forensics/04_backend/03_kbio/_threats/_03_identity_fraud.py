"""Identity fraud threat types."""
from __future__ import annotations

from ._registry import threat_type


@threat_type(
    code="idf-impersonation",
    name="Identity Fraud: Impersonation Detected",
    description="Challenges sessions where impersonation is detected by a human actor.",
    category="identity_fraud",
    severity=80,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.impersonation_detected", "op": "==", "value": True},
            {"field": "signals.is_bot", "op": "==", "value": False},
        ],
        "action": "challenge",
        "reason_template": "Identity fraud: impersonation detected (human actor)",
    },
    default_config={},
    reason_template="Identity fraud: impersonation detected (human actor)",
    tags=["identity", "fraud"],
)
def idf_impersonation():
    pass


@threat_type(
    code="idf-high-drift-human",
    name="Identity Fraud: High Drift Human",
    description="Challenges sessions with high drift, low bot score, and credential cadence mismatch.",
    category="identity_fraud",
    severity=75,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.high_drift_low_bot", "op": "==", "value": True},
            {
                "field": "signals.credential_cadence_mismatch",
                "op": ">",
                "value": 0.5,
                "config_key": "threshold",
            },
        ],
        "action": "challenge",
        "reason_template": "Identity fraud: high drift human with credential mismatch",
    },
    default_config={},
    reason_template="Identity fraud: high drift human with credential mismatch",
    tags=["identity", "fraud", "drift"],
)
def idf_high_drift_human():
    pass


@threat_type(
    code="idf-coached-session",
    name="Identity Fraud: Coached Session",
    description="Challenges sessions with coached behavior and unfamiliar navigation.",
    category="identity_fraud",
    severity=65,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.coached_behavior", "op": "==", "value": True},
            {"field": "signals.unfamiliar_navigation", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Identity fraud: coached session with unfamiliar navigation",
    },
    default_config={},
    reason_template="Identity fraud: coached session with unfamiliar navigation",
    tags=["identity", "fraud", "social_engineering"],
)
def idf_coached_session():
    pass


@threat_type(
    code="idf-credential-mismatch",
    name="Identity Fraud: Credential Mismatch",
    description="Challenges sessions with credential cadence mismatch and hesitation.",
    category="identity_fraud",
    severity=60,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {
                "field": "signals.credential_cadence_mismatch",
                "op": ">",
                "value": 0.5,
                "config_key": "threshold",
            },
            {"field": "signals.credential_hesitation", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Identity fraud: credential mismatch with hesitation",
    },
    default_config={},
    reason_template="Identity fraud: credential mismatch with hesitation",
    tags=["identity", "fraud", "credential"],
)
def idf_credential_mismatch():
    pass


@threat_type(
    code="idf-new-device-new-country",
    name="Identity Fraud: New Device + New Country",
    description="Blocks sessions from a new device in a new country with high behavioral drift.",
    category="identity_fraud",
    severity=80,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.new_device", "op": "==", "value": True},
            {"field": "signals.geo_new_country", "op": "==", "value": True},
            {"field": "signals.high_behavioral_drift", "op": ">", "value": 0.5},
        ],
        "action": "block",
        "reason_template": "Identity fraud: new device from new country with high drift",
    },
    default_config={},
    reason_template="Identity fraud: new device from new country with high drift",
    tags=["identity", "fraud", "geo"],
)
def idf_new_device_new_country():
    pass


@threat_type(
    code="idf-synthetic-identity",
    name="Identity Fraud: Synthetic Identity",
    description="Monitors first-ever sessions with credential paste from datacenter IPs.",
    category="identity_fraud",
    severity=65,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.first_session_ever", "op": "==", "value": True},
            {"field": "signals.credential_paste_detected", "op": "==", "value": True},
            {"field": "signals.datacenter_ip", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "Identity fraud: synthetic identity suspected (first session, paste, datacenter)",
    },
    default_config={},
    reason_template="Identity fraud: synthetic identity suspected (first session, paste, datacenter)",
    tags=["identity", "fraud", "synthetic"],
)
def idf_synthetic_identity():
    pass


@threat_type(
    code="idf-device-share",
    name="Identity Fraud: Device Sharing",
    description="Challenges sessions on shared devices with high behavioral drift.",
    category="identity_fraud",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.shared_device_cross_account", "op": "==", "value": True},
            {"field": "signals.high_behavioral_drift", "op": ">", "value": 0.5},
        ],
        "action": "challenge",
        "reason_template": "Identity fraud: shared device with high behavioral drift",
    },
    default_config={},
    reason_template="Identity fraud: shared device with high behavioral drift",
    tags=["identity", "fraud", "device"],
)
def idf_device_share():
    pass


@threat_type(
    code="idf-low-familiarity",
    name="Identity Fraud: Low Familiarity",
    description="Monitors sessions with unfamiliar navigation, high cognitive load, and low identity confidence.",
    category="identity_fraud",
    severity=55,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.unfamiliar_navigation", "op": "==", "value": True},
            {"field": "signals.high_cognitive_load", "op": "==", "value": True},
            {"field": "signals.low_identity_confidence", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "Identity fraud: low familiarity with high cognitive load",
    },
    default_config={},
    reason_template="Identity fraud: low familiarity with high cognitive load",
    tags=["identity", "fraud"],
)
def idf_low_familiarity():
    pass
