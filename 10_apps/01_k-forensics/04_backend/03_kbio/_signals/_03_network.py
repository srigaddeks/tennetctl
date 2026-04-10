"""Network signals — VPN, Tor, geo anomalies, impossible travel.

14 signals covering network origin trust, proxy detection,
geographic anomalies, and IP reputation indicators.
"""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


# ---------------------------------------------------------------------------
# 35. vpn_detected
# ---------------------------------------------------------------------------
@signal(
    code="vpn_detected",
    name="VPN Detected",
    description="Session originates from a known VPN exit node",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=40,
    tags=["network", "vpn"],
)
def compute_vpn_detected(ctx: dict, config: dict) -> SignalResult:
    is_vpn = ctx.get("network", {}).get("is_vpn", False)
    return SignalResult(
        value=bool(is_vpn),
        confidence=0.9,
        details={"is_vpn": is_vpn},
    )


# ---------------------------------------------------------------------------
# 36. tor_exit_node
# ---------------------------------------------------------------------------
@signal(
    code="tor_exit_node",
    name="Tor Exit Node",
    description="Session originates from a Tor exit node",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=75,
    tags=["network", "tor", "anonymity"],
)
def compute_tor_exit_node(ctx: dict, config: dict) -> SignalResult:
    is_tor = ctx.get("network", {}).get("is_tor", False)
    return SignalResult(
        value=bool(is_tor),
        confidence=0.95,
        details={"is_tor": is_tor},
    )


# ---------------------------------------------------------------------------
# 37. datacenter_ip
# ---------------------------------------------------------------------------
@signal(
    code="datacenter_ip",
    name="Datacenter IP",
    description="Session originates from a known datacenter IP range",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=60,
    tags=["network", "datacenter"],
)
def compute_datacenter_ip(ctx: dict, config: dict) -> SignalResult:
    is_dc = ctx.get("network", {}).get("is_datacenter", False)
    return SignalResult(
        value=bool(is_dc),
        confidence=0.9,
        details={"is_datacenter": is_dc},
    )


# ---------------------------------------------------------------------------
# 38. proxy_detected
# ---------------------------------------------------------------------------
@signal(
    code="proxy_detected",
    name="Proxy Detected",
    description="Session originates from a known proxy server",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=55,
    tags=["network", "proxy"],
)
def compute_proxy_detected(ctx: dict, config: dict) -> SignalResult:
    is_proxy = ctx.get("network", {}).get("is_proxy", False)
    return SignalResult(
        value=bool(is_proxy),
        confidence=0.9,
        details={"is_proxy": is_proxy},
    )


# ---------------------------------------------------------------------------
# 39. residential_proxy
# ---------------------------------------------------------------------------
@signal(
    code="residential_proxy",
    name="Residential Proxy",
    description="Session uses a residential proxy to mask true origin",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=70,
    tags=["network", "proxy", "residential"],
)
def compute_residential_proxy(ctx: dict, config: dict) -> SignalResult:
    is_rp = ctx.get("network", {}).get("is_residential_proxy", False)
    return SignalResult(
        value=bool(is_rp),
        confidence=0.85,
        details={"is_residential_proxy": is_rp},
    )


# ---------------------------------------------------------------------------
# 40. impossible_travel
# ---------------------------------------------------------------------------
@signal(
    code="impossible_travel",
    name="Impossible Travel",
    description="Travel speed between sessions exceeds physically possible threshold",
    category="network",
    signal_type="boolean",
    default_config={"max_speed_kmh": 900},
    severity=85,
    tags=["network", "geo", "travel"],
)
def compute_impossible_travel(ctx: dict, config: dict) -> SignalResult:
    speed = ctx.get("network", {}).get("travel_speed_kmh", 0.0)
    max_speed = config.get("max_speed_kmh", 900)
    return SignalResult(
        value=speed > max_speed,
        confidence=0.9,
        details={"travel_speed_kmh": speed, "max_speed_kmh": max_speed},
    )


# ---------------------------------------------------------------------------
# 41. geo_country_mismatch
# ---------------------------------------------------------------------------
@signal(
    code="geo_country_mismatch",
    name="Geo Country Mismatch",
    description="Session country does not match user's known countries",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=50,
    tags=["network", "geo"],
)
def compute_geo_country_mismatch(ctx: dict, config: dict) -> SignalResult:
    country = ctx.get("network", {}).get("country", "")
    known = ctx.get("user", {}).get("known_countries", [])
    if not known:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_known_countries"})
    mismatch = country not in known
    return SignalResult(
        value=mismatch,
        confidence=0.8,
        details={"country": country, "known_countries": known},
    )


# ---------------------------------------------------------------------------
# 42. geo_new_country
# ---------------------------------------------------------------------------
@signal(
    code="geo_new_country",
    name="Geo New Country",
    description="User is accessing from a country not seen before",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=45,
    tags=["network", "geo"],
)
def compute_geo_new_country(ctx: dict, config: dict) -> SignalResult:
    country = ctx.get("network", {}).get("country", "")
    user = ctx.get("user", {})
    known = user.get("known_countries", [])
    sessions = user.get("total_sessions", 0)
    triggered = country not in known and sessions > 0 if known else False
    return SignalResult(
        value=triggered,
        confidence=0.8 if known else 0.0,
        details={"country": country, "known_countries": known, "total_sessions": sessions},
    )


# ---------------------------------------------------------------------------
# 43. ip_velocity_high
# ---------------------------------------------------------------------------
@signal(
    code="ip_velocity_high",
    name="IP Velocity High",
    description="IP address has unusually high session or user count",
    category="network",
    signal_type="boolean",
    default_config={"max_sessions_1h": 50, "max_users_1h": 10},
    severity=65,
    tags=["network", "velocity", "ip"],
)
def compute_ip_velocity_high(ctx: dict, config: dict) -> SignalResult:
    net = ctx.get("network", {})
    sess_count = net.get("ip_session_count_24h", 0)
    user_count = net.get("ip_user_count_24h", 0)
    max_sess = config.get("max_sessions_1h", 50)
    max_users = config.get("max_users_1h", 10)
    triggered = sess_count > max_sess or user_count > max_users
    return SignalResult(
        value=triggered,
        confidence=0.85,
        details={"ip_session_count_24h": sess_count, "ip_user_count_24h": user_count},
    )


# ---------------------------------------------------------------------------
# 44. ip_not_trusted
# ---------------------------------------------------------------------------
@signal(
    code="ip_not_trusted",
    name="IP Not Trusted",
    description="IP address is not in the trusted list",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=25,
    tags=["network", "ip", "trust"],
)
def compute_ip_not_trusted(ctx: dict, config: dict) -> SignalResult:
    trusted = ctx.get("network", {}).get("ip_trusted", True)
    return SignalResult(
        value=not trusted,
        confidence=1.0,
        details={"ip_trusted": trusted},
    )


# ---------------------------------------------------------------------------
# 45. high_risk_country
# ---------------------------------------------------------------------------
@signal(
    code="high_risk_country",
    name="High Risk Country",
    description="Session originates from a configured high-risk country",
    category="network",
    signal_type="boolean",
    default_config={"countries": []},
    severity=55,
    tags=["network", "geo", "risk"],
)
def compute_high_risk_country(ctx: dict, config: dict) -> SignalResult:
    country = ctx.get("network", {}).get("country", "")
    risk_countries = config.get("countries", [])
    triggered = country in risk_countries if risk_countries else False
    return SignalResult(
        value=triggered,
        confidence=0.95,
        details={"country": country, "high_risk_countries": risk_countries},
    )


# ---------------------------------------------------------------------------
# 46. ip_reputation_bad
# ---------------------------------------------------------------------------
@signal(
    code="ip_reputation_bad",
    name="IP Reputation Bad",
    description="IP threat score exceeds acceptable threshold",
    category="network",
    signal_type="boolean",
    default_config={"min_threat_score": 0.70},
    severity=70,
    tags=["network", "ip", "reputation"],
)
def compute_ip_reputation_bad(ctx: dict, config: dict) -> SignalResult:
    threat = ctx.get("network", {}).get("threat_score", 0.0)
    min_score = config.get("min_threat_score", 0.70)
    return SignalResult(
        value=threat > min_score,
        confidence=0.85,
        details={"threat_score": threat, "min_threat_score": min_score},
    )


# ---------------------------------------------------------------------------
# 47. asn_mismatch
# ---------------------------------------------------------------------------
@signal(
    code="asn_mismatch",
    name="ASN Mismatch",
    description="Network ASN does not match user's typical ASN",
    category="network",
    signal_type="boolean",
    default_config={},
    severity=35,
    tags=["network", "asn"],
)
def compute_asn_mismatch(ctx: dict, config: dict) -> SignalResult:
    asn = ctx.get("network", {}).get("asn", "")
    typical = ctx.get("user", {}).get("typical_asn", "")
    if not typical or not asn:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    mismatch = asn != typical
    return SignalResult(
        value=mismatch,
        confidence=0.7,
        details={"asn": asn, "typical_asn": typical},
    )


# ---------------------------------------------------------------------------
# 48. vpn_with_drift
# ---------------------------------------------------------------------------
@signal(
    code="vpn_with_drift",
    name="VPN with Behavioral Drift",
    description="VPN usage combined with elevated behavioral drift",
    category="network",
    signal_type="boolean",
    default_config={"drift_threshold": 0.50},
    severity=70,
    tags=["network", "vpn", "drift", "compound"],
)
def compute_vpn_with_drift(ctx: dict, config: dict) -> SignalResult:
    is_vpn = ctx.get("network", {}).get("is_vpn", False)
    drift = ctx.get("scores", {}).get("behavioral_drift", 0.0)
    drift_thresh = config.get("drift_threshold", 0.50)
    triggered = bool(is_vpn) and drift > drift_thresh
    return SignalResult(
        value=triggered,
        confidence=0.8,
        details={"is_vpn": is_vpn, "behavioral_drift": drift, "drift_threshold": drift_thresh},
    )
