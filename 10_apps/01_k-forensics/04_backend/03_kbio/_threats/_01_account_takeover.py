"""Account takeover threat types."""
from __future__ import annotations

from ._registry import threat_type


@threat_type(
    code="ato-new-device-high-drift",
    name="Account Takeover: New Device + High Drift",
    description="Blocks sessions with critical behavioral drift on a device never seen before.",
    category="account_takeover",
    severity=90,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.critical_behavioral_drift", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": True},
            {"field": "signals.is_bot", "op": "==", "value": False},
        ],
        "action": "block",
        "reason_template": "ATO: critical drift on new device",
    },
    default_config={},
    reason_template="ATO: critical drift on new device",
    tags=["ato", "fraud", "critical"],
)
def ato_new_device_high_drift():
    pass


@threat_type(
    code="ato-known-device-high-drift",
    name="Account Takeover: Known Device + High Drift",
    description="Challenges sessions with critical behavioral drift on a previously seen device.",
    category="account_takeover",
    severity=80,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.critical_behavioral_drift", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": False},
        ],
        "action": "challenge",
        "reason_template": "ATO: critical drift on known device",
    },
    default_config={},
    reason_template="ATO: critical drift on known device",
    tags=["ato", "fraud"],
)
def ato_known_device_high_drift():
    pass


@threat_type(
    code="ato-credential-stuffing",
    name="Account Takeover: Credential Stuffing",
    description="Blocks credential paste with abnormally fast typing on a new device.",
    category="account_takeover",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.credential_paste_detected", "op": "==", "value": True},
            {"field": "signals.credential_typing_too_fast", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "ATO: credential stuffing detected on new device",
    },
    default_config={},
    reason_template="ATO: credential stuffing detected on new device",
    tags=["ato", "fraud", "credential"],
)
def ato_credential_stuffing():
    pass


@threat_type(
    code="ato-session-hijack",
    name="Account Takeover: Session Hijack",
    description="Blocks sessions where mid-session identity takeover is detected with velocity spike.",
    category="account_takeover",
    severity=90,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.mid_session_takeover", "op": "==", "value": True},
            {"field": "signals.velocity_spike", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "ATO: mid-session hijack with velocity spike",
    },
    default_config={},
    reason_template="ATO: mid-session hijack with velocity spike",
    tags=["ato", "fraud", "critical"],
)
def ato_session_hijack():
    pass


@threat_type(
    code="ato-impossible-travel",
    name="Account Takeover: Impossible Travel",
    description="Blocks sessions with impossible geographic travel combined with high behavioral drift.",
    category="account_takeover",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.impossible_travel", "op": "==", "value": True},
            {"field": "signals.high_behavioral_drift", "op": ">", "value": 0.5},
        ],
        "action": "block",
        "reason_template": "ATO: impossible travel with high behavioral drift",
    },
    default_config={},
    reason_template="ATO: impossible travel with high behavioral drift",
    tags=["ato", "fraud", "geo"],
)
def ato_impossible_travel():
    pass


@threat_type(
    code="ato-concurrent-sessions",
    name="Account Takeover: Concurrent Sessions",
    description="Challenges when concurrent sessions detected from new device with country mismatch.",
    category="account_takeover",
    severity=75,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.concurrent_sessions", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": True},
            {"field": "signals.geo_country_mismatch", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "ATO: concurrent sessions from new device with geo mismatch",
    },
    default_config={},
    reason_template="ATO: concurrent sessions from new device with geo mismatch",
    tags=["ato", "fraud", "geo"],
)
def ato_concurrent_sessions():
    pass


@threat_type(
    code="ato-dormant-activation",
    name="Account Takeover: Dormant Account Activation",
    description="Blocks dormant account reactivation from a new device with high drift.",
    category="account_takeover",
    severity=80,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.dormant_account", "op": "==", "value": True},
            {"field": "signals.new_device", "op": "==", "value": True},
            {"field": "signals.high_behavioral_drift", "op": ">", "value": 0.5},
        ],
        "action": "block",
        "reason_template": "ATO: dormant account activated from new device with high drift",
    },
    default_config={},
    reason_template="ATO: dormant account activated from new device with high drift",
    tags=["ato", "fraud"],
)
def ato_dormant_activation():
    pass


@threat_type(
    code="ato-brute-force",
    name="Account Takeover: Brute Force",
    description="Blocks brute force attempts with elevated credential drift.",
    category="account_takeover",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.failed_challenges_recent", "op": "==", "value": True},
            {"field": "signals.credential_drift_elevated", "op": ">", "value": 0.5},
        ],
        "action": "block",
        "reason_template": "ATO: brute force with elevated credential drift",
    },
    default_config={},
    reason_template="ATO: brute force with elevated credential drift",
    tags=["ato", "fraud", "credential"],
)
def ato_brute_force():
    pass


@threat_type(
    code="ato-vpn-drift",
    name="Account Takeover: VPN + Drift",
    description="Challenges sessions with VPN-associated drift and country mismatch.",
    category="account_takeover",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.vpn_with_drift", "op": "==", "value": True},
            {"field": "signals.geo_country_mismatch", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "ATO: VPN with drift and geo mismatch",
    },
    default_config={},
    reason_template="ATO: VPN with drift and geo mismatch",
    tags=["ato", "network"],
)
def ato_vpn_drift():
    pass


@threat_type(
    code="ato-multi-signal",
    name="Account Takeover: Multi-Signal",
    description="Challenges sessions with high drift, VPN usage, and off-hours activity.",
    category="account_takeover",
    severity=75,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.high_behavioral_drift", "op": ">", "value": 0.5},
            {"field": "signals.outside_working_hours", "op": "==", "value": True},
            {"field": "signals.vpn_detected", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Multi-signal: drift + anonymizer + off-hours",
    },
    default_config={},
    reason_template="Multi-signal: drift + anonymizer + off-hours",
    tags=["ato", "fraud", "network"],
)
def ato_multi_signal():
    pass
