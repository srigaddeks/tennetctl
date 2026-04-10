"""Network threat types."""
from __future__ import annotations

from ._registry import threat_type


@threat_type(
    code="net-tor-activity",
    name="Network: Tor Exit Node Activity",
    description="Blocks sessions from Tor exit nodes with high behavioral drift.",
    category="network_threats",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.tor_exit_node", "op": "==", "value": True},
            {"field": "signals.high_behavioral_drift", "op": ">", "value": 0.5},
        ],
        "action": "block",
        "reason_template": "Network: Tor exit node with high behavioral drift",
    },
    default_config={},
    reason_template="Network: Tor exit node with high behavioral drift",
    tags=["network", "anonymizer"],
)
def net_tor_activity():
    pass


@threat_type(
    code="net-datacenter-bot",
    name="Network: Datacenter Bot",
    description="Blocks bot sessions originating from datacenter IPs.",
    category="network_threats",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.datacenter_ip", "op": "==", "value": True},
            {"field": "signals.is_bot", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Network: bot from datacenter IP",
    },
    default_config={},
    reason_template="Network: bot from datacenter IP",
    tags=["network", "bot"],
)
def net_datacenter_bot():
    pass


@threat_type(
    code="net-residential-proxy",
    name="Network: Residential Proxy",
    description="Challenges sessions from residential proxies with high behavioral drift.",
    category="network_threats",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.residential_proxy", "op": "==", "value": True},
            {"field": "signals.high_behavioral_drift", "op": ">", "value": 0.5},
        ],
        "action": "challenge",
        "reason_template": "Network: residential proxy with high behavioral drift",
    },
    default_config={},
    reason_template="Network: residential proxy with high behavioral drift",
    tags=["network", "proxy"],
)
def net_residential_proxy():
    pass


@threat_type(
    code="net-ip-velocity",
    name="Network: IP Velocity",
    description="Monitors sessions with high IP velocity and cross-account shared IP usage.",
    category="network_threats",
    severity=65,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.ip_velocity_high", "op": "==", "value": True},
            {"field": "signals.shared_ip_cross_account", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "Network: high IP velocity with cross-account sharing",
    },
    default_config={},
    reason_template="Network: high IP velocity with cross-account sharing",
    tags=["network", "velocity"],
)
def net_ip_velocity():
    pass


@threat_type(
    code="net-geo-anomaly",
    name="Network: Geographic Anomaly",
    description="Challenges sessions with country mismatch, off-hours access, and high behavioral drift.",
    category="network_threats",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.geo_country_mismatch", "op": "==", "value": True},
            {"field": "signals.outside_working_hours", "op": "==", "value": True},
            {"field": "signals.high_behavioral_drift", "op": ">", "value": 0.5},
        ],
        "action": "challenge",
        "reason_template": "Network: geo anomaly with off-hours access and high drift",
    },
    default_config={},
    reason_template="Network: geo anomaly with off-hours access and high drift",
    tags=["network", "geo"],
)
def net_geo_anomaly():
    pass
