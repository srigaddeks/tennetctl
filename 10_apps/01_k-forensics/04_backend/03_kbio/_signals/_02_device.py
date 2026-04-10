"""Device signals — trust, fingerprint, emulator, hardware anomalies.

16 signals covering device trust state, fingerprint drift,
emulation detection, and device-user relationship indicators.
"""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


# ---------------------------------------------------------------------------
# 19. new_device
# ---------------------------------------------------------------------------
@signal(
    code="new_device",
    name="New Device",
    description="Session originates from a previously unseen device",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=40,
    tags=["device", "trust"],
)
def compute_new_device(ctx: dict, config: dict) -> SignalResult:
    is_new = ctx.get("device", {}).get("is_new", False)
    return SignalResult(
        value=bool(is_new),
        confidence=1.0,
        details={"is_new": is_new},
    )


# ---------------------------------------------------------------------------
# 20. untrusted_device
# ---------------------------------------------------------------------------
@signal(
    code="untrusted_device",
    name="Untrusted Device",
    description="Device has not been marked as trusted",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=35,
    tags=["device", "trust"],
)
def compute_untrusted_device(ctx: dict, config: dict) -> SignalResult:
    is_trusted = ctx.get("device", {}).get("is_trusted", True)
    return SignalResult(
        value=not is_trusted,
        confidence=1.0,
        details={"is_trusted": is_trusted},
    )


# ---------------------------------------------------------------------------
# 21. device_fingerprint_drift
# ---------------------------------------------------------------------------
@signal(
    code="device_fingerprint_drift",
    name="Device Fingerprint Drift",
    description="Device fingerprint has drifted from baseline",
    category="device",
    signal_type="score",
    default_config={"threshold": 0.50},
    severity=60,
    tags=["device", "fingerprint", "drift"],
)
def compute_device_fingerprint_drift(ctx: dict, config: dict) -> SignalResult:
    drift = ctx.get("device", {}).get("fingerprint_drift", 0.0)
    threshold = config.get("threshold", 0.50)
    return SignalResult(
        value=drift,
        confidence=0.9,
        details={"fingerprint_drift": drift, "threshold": threshold, "exceeded": drift > threshold},
    )


# ---------------------------------------------------------------------------
# 22. device_age_young
# ---------------------------------------------------------------------------
@signal(
    code="device_age_young",
    name="Device Age Young",
    description="Device was first seen very recently",
    category="device",
    signal_type="boolean",
    default_config={"min_age_days": 7},
    severity=35,
    tags=["device", "age"],
)
def compute_device_age_young(ctx: dict, config: dict) -> SignalResult:
    age = ctx.get("device", {}).get("age_days", 999)
    min_age = config.get("min_age_days", 7)
    return SignalResult(
        value=age < min_age,
        confidence=1.0,
        details={"age_days": age, "min_age_days": min_age},
    )


# ---------------------------------------------------------------------------
# 23. device_low_session_count
# ---------------------------------------------------------------------------
@signal(
    code="device_low_session_count",
    name="Device Low Session Count",
    description="Device has very few recorded sessions",
    category="device",
    signal_type="boolean",
    default_config={"min_sessions": 3},
    severity=30,
    tags=["device", "history"],
)
def compute_device_low_session_count(ctx: dict, config: dict) -> SignalResult:
    count = ctx.get("device", {}).get("session_count", 0)
    min_sessions = config.get("min_sessions", 3)
    return SignalResult(
        value=count < min_sessions,
        confidence=1.0,
        details={"session_count": count, "min_sessions": min_sessions},
    )


# ---------------------------------------------------------------------------
# 24. multi_user_device
# ---------------------------------------------------------------------------
@signal(
    code="multi_user_device",
    name="Multi-User Device",
    description="Device has been used by more users than expected",
    category="device",
    signal_type="boolean",
    default_config={"max_users": 1},
    severity=65,
    tags=["device", "sharing"],
)
def compute_multi_user_device(ctx: dict, config: dict) -> SignalResult:
    users = ctx.get("device", {}).get("users_count", 1)
    max_users = config.get("max_users", 1)
    return SignalResult(
        value=users > max_users,
        confidence=1.0,
        details={"users_count": users, "max_users": max_users},
    )


# ---------------------------------------------------------------------------
# 25. device_switching_rapid
# ---------------------------------------------------------------------------
@signal(
    code="device_switching_rapid",
    name="Rapid Device Switching",
    description="User has used an unusually high number of devices",
    category="device",
    signal_type="boolean",
    default_config={"max_switches_24h": 3},
    severity=55,
    tags=["device", "switching"],
)
def compute_device_switching_rapid(ctx: dict, config: dict) -> SignalResult:
    total_devices = ctx.get("user", {}).get("total_devices", 1)
    max_switches = config.get("max_switches_24h", 3)
    return SignalResult(
        value=total_devices > max_switches,
        confidence=0.7,
        details={"total_devices": total_devices, "max_switches_24h": max_switches},
    )


# ---------------------------------------------------------------------------
# 26. mobile_device
# ---------------------------------------------------------------------------
@signal(
    code="mobile_device",
    name="Mobile Device",
    description="Session originates from a mobile device",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=10,
    tags=["device", "platform"],
)
def compute_mobile_device(ctx: dict, config: dict) -> SignalResult:
    is_mobile = ctx.get("device", {}).get("is_mobile", False)
    return SignalResult(
        value=bool(is_mobile),
        confidence=1.0,
        details={"is_mobile": is_mobile},
    )


# ---------------------------------------------------------------------------
# 27. emulator_detected
# ---------------------------------------------------------------------------
@signal(
    code="emulator_detected",
    name="Emulator Detected",
    description="Device appears to be running in an emulator",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=80,
    tags=["device", "emulator", "fraud"],
)
def compute_emulator_detected(ctx: dict, config: dict) -> SignalResult:
    is_emulator = ctx.get("device", {}).get("is_emulator", False)
    return SignalResult(
        value=bool(is_emulator),
        confidence=1.0,
        details={"is_emulator": is_emulator},
    )


# ---------------------------------------------------------------------------
# 28. rooted_jailbroken
# ---------------------------------------------------------------------------
@signal(
    code="rooted_jailbroken",
    name="Rooted / Jailbroken",
    description="Device appears to be rooted or jailbroken",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=70,
    tags=["device", "root", "jailbreak"],
)
def compute_rooted_jailbroken(ctx: dict, config: dict) -> SignalResult:
    rooted = ctx.get("device", {}).get("rooted_jailbroken", False)
    return SignalResult(
        value=bool(rooted),
        confidence=1.0,
        details={"rooted_jailbroken": rooted},
    )


# ---------------------------------------------------------------------------
# 29. screen_resolution_anomaly
# ---------------------------------------------------------------------------
@signal(
    code="screen_resolution_anomaly",
    name="Screen Resolution Anomaly",
    description="Screen dimensions are outside plausible range",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=45,
    tags=["device", "fingerprint"],
)
def compute_screen_resolution_anomaly(ctx: dict, config: dict) -> SignalResult:
    dev = ctx.get("device", {})
    width = dev.get("screen_width", 1920)
    height = dev.get("screen_height", 1080)
    anomaly = width < 100 or width > 10000 or height < 100 or height > 10000
    return SignalResult(
        value=anomaly,
        confidence=1.0 if anomaly else 0.9,
        details={"screen_width": width, "screen_height": height},
    )


# ---------------------------------------------------------------------------
# 30. timezone_mismatch
# ---------------------------------------------------------------------------
@signal(
    code="timezone_mismatch",
    name="Timezone Mismatch",
    description="Device timezone does not match expected offset for IP location",
    category="device",
    signal_type="boolean",
    default_config={"max_offset_hours": 3},
    severity=50,
    tags=["device", "timezone", "geo"],
)
def compute_timezone_mismatch(ctx: dict, config: dict) -> SignalResult:
    dev = ctx.get("device", {})
    net = ctx.get("network", {})
    device_tz = dev.get("timezone_offset_minutes", 0)
    expected_tz = net.get("expected_tz_offset_minutes", 0)
    max_offset = config.get("max_offset_hours", 3) * 60
    diff = abs(device_tz - expected_tz)
    return SignalResult(
        value=diff > max_offset,
        confidence=0.7,
        details={"device_tz_offset": device_tz, "expected_tz_offset": expected_tz, "diff_minutes": diff},
    )


# ---------------------------------------------------------------------------
# 31. language_mismatch
# ---------------------------------------------------------------------------
@signal(
    code="language_mismatch",
    name="Language Mismatch",
    description="Device language does not match user's known languages",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=40,
    tags=["device", "language"],
)
def compute_language_mismatch(ctx: dict, config: dict) -> SignalResult:
    lang = ctx.get("device", {}).get("language", "")
    known = ctx.get("user", {}).get("known_languages", [])
    if not known or not lang:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    mismatch = lang not in known
    return SignalResult(
        value=mismatch,
        confidence=0.8,
        details={"device_language": lang, "known_languages": known},
    )


# ---------------------------------------------------------------------------
# 32. plugins_zero
# ---------------------------------------------------------------------------
@signal(
    code="plugins_zero",
    name="Plugins Zero",
    description="Browser reports zero plugins, possible headless or hardened browser",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=55,
    tags=["device", "fingerprint", "headless"],
)
def compute_plugins_zero(ctx: dict, config: dict) -> SignalResult:
    count = ctx.get("device", {}).get("plugins_count", -1)
    return SignalResult(
        value=count == 0,
        confidence=0.8,
        details={"plugins_count": count},
    )


# ---------------------------------------------------------------------------
# 33. canvas_fingerprint_anomaly
# ---------------------------------------------------------------------------
@signal(
    code="canvas_fingerprint_anomaly",
    name="Canvas Fingerprint Anomaly",
    description="Canvas fingerprint indicates spoofing or virtualization",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=50,
    tags=["device", "fingerprint", "canvas"],
)
def compute_canvas_fingerprint_anomaly(ctx: dict, config: dict) -> SignalResult:
    anomaly = ctx.get("device", {}).get("canvas_anomaly", False)
    return SignalResult(
        value=bool(anomaly),
        confidence=0.85,
        details={"canvas_anomaly": anomaly},
    )


# ---------------------------------------------------------------------------
# 34. webgl_fingerprint_anomaly
# ---------------------------------------------------------------------------
@signal(
    code="webgl_fingerprint_anomaly",
    name="WebGL Fingerprint Anomaly",
    description="WebGL renderer indicates spoofing or virtualization",
    category="device",
    signal_type="boolean",
    default_config={},
    severity=50,
    tags=["device", "fingerprint", "webgl"],
)
def compute_webgl_fingerprint_anomaly(ctx: dict, config: dict) -> SignalResult:
    anomaly = ctx.get("device", {}).get("webgl_anomaly", False)
    return SignalResult(
        value=bool(anomaly),
        confidence=0.85,
        details={"webgl_anomaly": anomaly},
    )
