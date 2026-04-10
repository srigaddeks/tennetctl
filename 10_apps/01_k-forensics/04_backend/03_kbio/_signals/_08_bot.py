"""Bot detection signals — automation, replay, timing artifacts."""
from __future__ import annotations

from ._registry import signal
from ._types import SignalResult


# ---------------------------------------------------------------------------
# 93. is_bot
# ---------------------------------------------------------------------------
@signal(
    code="is_bot",
    name="Is Bot",
    description="Bot score exceeds threshold",
    category="bot",
    severity=80,
    default_config={"threshold": 0.70},
    tags=["bot"],
)
def compute_is_bot(ctx: dict, config: dict) -> SignalResult:
    bot_score = ctx.get("scores", {}).get("bot_score", 0.0)
    threshold = config.get("threshold", 0.70)
    return SignalResult(
        value=bot_score > threshold,
        confidence=0.8,
        details={"bot_score": bot_score, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 94. is_bot_high_confidence
# ---------------------------------------------------------------------------
@signal(
    code="is_bot_high_confidence",
    name="Is Bot High Confidence",
    description="Bot score exceeds high threshold with strong confidence",
    category="bot",
    severity=95,
    default_config={"threshold": 0.90},
    tags=["bot", "critical"],
)
def compute_is_bot_high_confidence(ctx: dict, config: dict) -> SignalResult:
    scores = ctx.get("scores", {})
    bot_score = scores.get("bot_score", 0.0)
    confidence = scores.get("confidence", 0.0)
    threshold = config.get("threshold", 0.90)
    hit = bot_score > threshold and confidence > 0.60
    return SignalResult(
        value=hit, confidence=confidence,
        details={"bot_score": bot_score, "threshold": threshold, "confidence": confidence},
    )


# ---------------------------------------------------------------------------
# 95. headless_browser
# ---------------------------------------------------------------------------
@signal(
    code="headless_browser",
    name="Headless Browser",
    description="Session originates from a headless browser",
    category="bot",
    severity=85,
    default_config={},
    tags=["bot", "headless"],
)
def compute_headless_browser(ctx: dict, config: dict) -> SignalResult:
    hit = ctx.get("device", {}).get("is_headless", False) is True
    return SignalResult(value=hit, confidence=0.95, details={"is_headless": hit})


# ---------------------------------------------------------------------------
# 96. webdriver_detected
# ---------------------------------------------------------------------------
@signal(
    code="webdriver_detected",
    name="WebDriver Detected",
    description="WebDriver API presence detected in browser",
    category="bot",
    severity=80,
    default_config={},
    tags=["bot", "webdriver"],
)
def compute_webdriver_detected(ctx: dict, config: dict) -> SignalResult:
    hit = ctx.get("device", {}).get("webdriver_present", False) is True
    return SignalResult(value=hit, confidence=0.95, details={"webdriver_present": hit})


# ---------------------------------------------------------------------------
# 97. cdp_detected
# ---------------------------------------------------------------------------
@signal(
    code="cdp_detected",
    name="CDP Detected",
    description="Chrome DevTools Protocol detected",
    category="bot",
    severity=85,
    default_config={},
    tags=["bot", "cdp"],
)
def compute_cdp_detected(ctx: dict, config: dict) -> SignalResult:
    hit = ctx.get("device", {}).get("cdp_detected", False) is True
    return SignalResult(value=hit, confidence=0.95, details={"cdp_detected": hit})


# ---------------------------------------------------------------------------
# 98. automation_framework
# ---------------------------------------------------------------------------
@signal(
    code="automation_framework",
    name="Automation Framework",
    description="Automation framework artifacts detected",
    category="bot",
    severity=85,
    default_config={},
    tags=["bot", "automation"],
)
def compute_automation_framework(ctx: dict, config: dict) -> SignalResult:
    hit = ctx.get("device", {}).get("automation_artifacts", False) is True
    return SignalResult(value=hit, confidence=0.95, details={"automation_artifacts": hit})


# ---------------------------------------------------------------------------
# 99. replay_attack
# ---------------------------------------------------------------------------
@signal(
    code="replay_attack",
    name="Replay Attack",
    description="Replay score exceeds threshold indicating recorded input",
    category="bot",
    severity=90,
    default_config={"threshold": 0.80},
    tags=["bot", "replay"],
)
def compute_replay_attack(ctx: dict, config: dict) -> SignalResult:
    replay = ctx.get("scores", {}).get("replay_score", 0.0)
    threshold = config.get("threshold", 0.80)
    return SignalResult(
        value=replay > threshold,
        confidence=0.85,
        details={"replay_score": replay, "threshold": threshold},
    )


# ---------------------------------------------------------------------------
# 100. impossible_keystroke_timing
# ---------------------------------------------------------------------------
@signal(
    code="impossible_keystroke_timing",
    name="Impossible Keystroke Timing",
    description="Inter-key intervals or variance are impossibly low",
    category="bot",
    severity=80,
    default_config={"min_iki_ms": 15, "max_cv": 0.05},
    tags=["bot", "keystroke"],
)
def compute_impossible_keystroke_timing(ctx: dict, config: dict) -> SignalResult:
    session = ctx.get("session", {})
    min_iki = session.get("min_iki_ms")
    iki_cv = session.get("iki_cv")
    min_iki_thresh = config.get("min_iki_ms", 15)
    max_cv = config.get("max_cv", 0.05)
    if min_iki is None and iki_cv is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    iki_fail = min_iki is not None and min_iki < min_iki_thresh
    cv_fail = iki_cv is not None and iki_cv < max_cv
    hit = iki_fail or cv_fail
    return SignalResult(
        value=hit, confidence=0.9,
        details={"min_iki_ms": min_iki, "iki_cv": iki_cv, "iki_fail": iki_fail, "cv_fail": cv_fail},
    )


# ---------------------------------------------------------------------------
# 101. zero_variance_dwell
# ---------------------------------------------------------------------------
@signal(
    code="zero_variance_dwell",
    name="Zero Variance Dwell",
    description="Dwell time coefficient of variation is near zero",
    category="bot",
    severity=85,
    default_config={"max_cv": 0.02},
    tags=["bot", "dwell"],
)
def compute_zero_variance_dwell(ctx: dict, config: dict) -> SignalResult:
    dwell_cv = ctx.get("session", {}).get("dwell_cv")
    max_cv = config.get("max_cv", 0.02)
    if dwell_cv is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    hit = dwell_cv < max_cv
    return SignalResult(
        value=hit, confidence=0.9,
        details={"dwell_cv": dwell_cv, "max_cv": max_cv},
    )


# ---------------------------------------------------------------------------
# 102. linear_pointer_movement
# ---------------------------------------------------------------------------
@signal(
    code="linear_pointer_movement",
    name="Linear Pointer Movement",
    description="Pointer movement curvature is unnaturally straight",
    category="bot",
    severity=75,
    default_config={"min_curvature": 0.01},
    tags=["bot", "pointer"],
)
def compute_linear_pointer_movement(ctx: dict, config: dict) -> SignalResult:
    curvature = ctx.get("session", {}).get("pointer_curvature")
    min_c = config.get("min_curvature", 0.01)
    if curvature is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    hit = curvature < min_c
    return SignalResult(
        value=hit, confidence=0.85,
        details={"pointer_curvature": curvature, "min_curvature": min_c},
    )


# ---------------------------------------------------------------------------
# 103. uniform_batch_timing
# ---------------------------------------------------------------------------
@signal(
    code="uniform_batch_timing",
    name="Uniform Batch Timing",
    description="Batch event timing variance is suspiciously uniform",
    category="bot",
    severity=65,
    default_config={"max_cv": 0.05},
    tags=["bot", "timing"],
)
def compute_uniform_batch_timing(ctx: dict, config: dict) -> SignalResult:
    batch_cv = ctx.get("session", {}).get("batch_timing_cv")
    max_cv = config.get("max_cv", 0.05)
    if batch_cv is None:
        return SignalResult(value=False, confidence=0.0, details={"reason": "no_data"})
    hit = batch_cv < max_cv
    return SignalResult(
        value=hit, confidence=0.8,
        details={"batch_timing_cv": batch_cv, "max_cv": max_cv},
    )


# ---------------------------------------------------------------------------
# 104. round_event_counts
# ---------------------------------------------------------------------------
@signal(
    code="round_event_counts",
    name="Round Event Counts",
    description="Pulse count is a suspiciously round number",
    category="bot",
    severity=50,
    default_config={"divisor": 50},
    tags=["bot", "count"],
)
def compute_round_event_counts(ctx: dict, config: dict) -> SignalResult:
    pulse_count = ctx.get("session", {}).get("pulse_count", 0) or 0
    divisor = config.get("divisor", 50)
    hit = pulse_count > 0 and pulse_count % divisor == 0
    return SignalResult(
        value=hit, confidence=0.6,
        details={"pulse_count": pulse_count, "divisor": divisor},
    )


# ---------------------------------------------------------------------------
# 105. ua_behavior_mismatch
# ---------------------------------------------------------------------------
@signal(
    code="ua_behavior_mismatch",
    name="UA Behavior Mismatch",
    description="Mobile user-agent but only pointer events, no touch",
    category="bot",
    severity=60,
    default_config={},
    tags=["bot", "mismatch"],
)
def compute_ua_behavior_mismatch(ctx: dict, config: dict) -> SignalResult:
    device = ctx.get("device", {})
    session = ctx.get("session", {})
    is_mobile = device.get("is_mobile", False)
    pointer_only = session.get("has_pointer_only", False)
    hit = is_mobile is True and pointer_only is True
    return SignalResult(
        value=hit, confidence=0.8,
        details={"is_mobile": is_mobile, "has_pointer_only": pointer_only},
    )


# ---------------------------------------------------------------------------
# 106. proxy_api_overridden
# ---------------------------------------------------------------------------
@signal(
    code="proxy_api_overridden",
    name="Proxy API Overridden",
    description="Browser proxy API has been overridden",
    category="bot",
    severity=70,
    default_config={},
    tags=["bot", "proxy"],
)
def compute_proxy_api_overridden(ctx: dict, config: dict) -> SignalResult:
    hit = ctx.get("device", {}).get("proxy_overridden", False) is True
    return SignalResult(value=hit, confidence=0.9, details={"proxy_overridden": hit})
