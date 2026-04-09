"""kbio bot detection pipeline.

Four detection layers executed in order with short-circuit on high confidence:
1. Automation signals (webdriver, CDP, headless)
2. Timing analysis (impossible keystroke timing, zero variance)
3. Fingerprint consistency (UA vs behavior mismatch)
4. Behavioral heuristics (suspicious patterns)

Bot score: 0.0 (human) to 1.0 (definitely bot).
"""

from __future__ import annotations

from typing import Any


def detect(
    batch: dict[str, Any],
    session_state: dict[str, Any] | None = None,
    device_cache: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run full bot detection pipeline.

    Returns:
        {
            bot_score: float (0.0-1.0),
            detection_layers: { layer_name: { score, signals } },
            is_bot: bool (bot_score > 0.7),
            action: "allow" | "challenge" | "block",
        }
    """
    session_state = session_state or {}
    device_cache = device_cache or {}

    layers: dict[str, dict[str, Any]] = {}

    # Layer 1: Automation signals
    auto_result = _check_automation(batch, device_cache)
    layers["automation"] = auto_result
    if auto_result["score"] > 0.85:
        return _build_result(auto_result["score"], layers)

    # Layer 2: Timing analysis
    timing_result = _check_timing(batch)
    layers["timing"] = timing_result
    if timing_result["score"] > 0.85:
        return _build_result(timing_result["score"], layers)

    # Layer 3: Fingerprint consistency
    consistency_result = _check_consistency(batch, device_cache)
    layers["consistency"] = consistency_result

    # Layer 4: Behavioral heuristics
    heuristic_result = _check_heuristics(batch, session_state)
    layers["heuristics"] = heuristic_result

    # Composite score
    composite = max(
        auto_result["score"],
        timing_result["score"],
        consistency_result["score"] * 0.8,
        heuristic_result["score"] * 0.6,
    )

    return _build_result(composite, layers)


def _build_result(bot_score: float, layers: dict) -> dict[str, Any]:
    """Assemble bot detection result."""
    bot_score = round(min(1.0, max(0.0, bot_score)), 4)
    if bot_score > 0.7:
        action = "block"
    elif bot_score > 0.4:
        action = "challenge"
    else:
        action = "allow"

    return {
        "bot_score": bot_score,
        "detection_layers": layers,
        "is_bot": bot_score > 0.7,
        "action": action,
    }


def _check_automation(batch: dict, device_cache: dict) -> dict[str, Any]:
    """Layer 1: Check for automation tool artifacts."""
    score = 0.0
    signals: list[str] = []

    # Check device fingerprint automation signals
    automation = device_cache.get("automation", {})
    if not automation:
        signals_data = batch.get("signals", {})
        automation = signals_data.get("automation", {})

    if automation.get("webdriver"):
        score = max(score, 0.9)
        signals.append("webdriver_detected")

    if automation.get("cdp_detected"):
        score = max(score, 0.8)
        signals.append("cdp_detected")

    if automation.get("selenium_detected"):
        score = max(score, 0.9)
        signals.append("selenium_detected")

    if automation.get("headless"):
        score = max(score, 0.7)
        signals.append("headless_browser")

    if automation.get("puppeteer_detected"):
        score = max(score, 0.85)
        signals.append("puppeteer_detected")

    if automation.get("playwright_detected"):
        score = max(score, 0.85)
        signals.append("playwright_detected")

    sdk_automation_score = float(automation.get("automation_score", 0))
    if sdk_automation_score > 0.5:
        score = max(score, sdk_automation_score)
        signals.append(f"sdk_automation_score={sdk_automation_score}")

    return {"score": round(score, 4), "signals": signals}


def _check_timing(batch: dict) -> dict[str, Any]:
    """Layer 2: Analyze timing patterns for impossibility."""
    score = 0.0
    signals: list[str] = []

    # Check keystroke windows
    keystroke_windows = batch.get("keystroke_windows", [])
    for window in keystroke_windows:
        dwell_means = window.get("zone_dwell_means", [])
        valid_dwells = [d for d in dwell_means if d is not None and d >= 0]

        if valid_dwells:
            min_dwell = min(valid_dwells)
            if min_dwell < 10 and min_dwell > 0:
                score = max(score, 0.95)
                signals.append(f"impossible_dwell_ms={min_dwell}")

        dwell_stdevs = window.get("zone_dwell_stdevs", [])
        valid_stdevs = [s for s in dwell_stdevs if s is not None and s >= 0]
        if valid_stdevs and all(s == 0.0 for s in valid_stdevs) and len(valid_stdevs) > 3:
            score = max(score, 0.9)
            signals.append("zero_variance_dwells")

    # Check pointer windows
    pointer_windows = batch.get("pointer_windows", [])
    for window in pointer_windows:
        movement = window.get("movement", {})
        curvature = movement.get("curvature_mean", -1)
        if curvature == 0.0 and movement.get("total_distance", 0) > 100:
            score = max(score, 0.85)
            signals.append("perfectly_linear_pointer")

        clicks = window.get("clicks", {})
        hold_stdev = clicks.get("hold_stdev", -1)
        if hold_stdev == 0.0 and clicks.get("count", 0) > 3:
            score = max(score, 0.8)
            signals.append("identical_click_holds")

    return {"score": round(score, 4), "signals": signals}


def _check_consistency(batch: dict, device_cache: dict) -> dict[str, Any]:
    """Layer 3: Cross-reference signals for consistency."""
    score = 0.0
    signals: list[str] = []

    context = batch.get("context", {})
    ua = context.get("user_agent", "")

    has_pointer = bool(batch.get("pointer_windows"))
    has_touch = bool(batch.get("touch_windows"))

    # Mobile UA but only pointer input
    is_mobile_ua = any(kw in ua.lower() for kw in ["mobile", "android", "iphone", "ipad"])
    if is_mobile_ua and has_pointer and not has_touch:
        score = max(score, 0.5)
        signals.append("mobile_ua_pointer_only")

    # Desktop UA but only touch input
    is_desktop_ua = not is_mobile_ua and ua
    if is_desktop_ua and has_touch and not has_pointer:
        score = max(score, 0.3)
        signals.append("desktop_ua_touch_only")

    # Hardware concurrency check
    hw_concurrency = context.get("hardware_concurrency", -1)
    if hw_concurrency == 0:
        score = max(score, 0.3)
        signals.append("zero_hardware_concurrency")
    elif isinstance(hw_concurrency, (int, float)) and hw_concurrency > 128:
        score = max(score, 0.3)
        signals.append(f"absurd_hardware_concurrency={hw_concurrency}")

    return {"score": round(score, 4), "signals": signals}


def _check_heuristics(batch: dict, session_state: dict) -> dict[str, Any]:
    """Layer 4: Behavioral heuristic checks."""
    score = 0.0
    signals: list[str] = []

    # Check if first batch is suspiciously complete
    pulse_count = session_state.get("pulse_count", 0)
    if pulse_count <= 1:
        modality_count = sum(1 for k in ["keystroke_windows", "pointer_windows",
                                          "touch_windows", "sensor_windows"]
                            if batch.get(k))
        if modality_count >= 3:
            score = max(score, 0.3)
            signals.append("suspiciously_complete_first_batch")

    # Check for perfectly uniform batch timing
    header = batch.get("header", {})
    batch_interval = header.get("batch_interval_ms")
    if batch_interval is not None and session_state.get("last_batch_interval_ms") is not None:
        diff = abs(batch_interval - session_state["last_batch_interval_ms"])
        if diff == 0 and pulse_count > 3:
            score = max(score, 0.4)
            signals.append("perfectly_uniform_batch_timing")

    # Round event counts
    for key in ["keystroke_windows", "pointer_windows"]:
        windows = batch.get(key, [])
        for window in windows:
            hit_counts = window.get("zone_hit_counts", [])
            total = sum(h for h in hit_counts if h and h > 0)
            if total > 0 and total % 10 == 0 and total >= 50:
                score = max(score, 0.2)
                signals.append(f"round_event_count_{key}={total}")

    return {"score": round(score, 4), "signals": signals}


# ---------------------------------------------------------------------------
# V2: ML-style weighted ensemble
# Uses V1 heuristic layers as input features + additional signals
# ---------------------------------------------------------------------------

# Learned weights for the logistic regression ensemble
# In production, these would be trained on labeled data
_ENSEMBLE_WEIGHTS = {
    "automation_score": 3.5,      # Strong signal
    "timing_score": 3.0,          # Strong signal
    "consistency_score": 1.5,     # Medium signal
    "heuristics_score": 1.0,      # Weak signal
    "timing_entropy": -2.0,       # High entropy = human (negative weight)
    "event_regularity": 1.5,      # High regularity = bot
    "modality_diversity": -1.0,   # Multiple modalities = human
    "velocity_variance": -1.2,    # High variance = human
}

_ENSEMBLE_BIAS = -1.5  # Bias toward "human" (reduce false positives)


def detect_v2(
    batch: dict[str, Any],
    session_state: dict[str, Any] | None = None,
    device_cache: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """V2 bot detection using ML-style weighted ensemble.

    Runs V1 heuristic layers, then extracts additional features,
    and feeds everything into a logistic regression ensemble.

    Returns same shape as detect() plus additional fields.
    """
    # Run V1 pipeline first to get layer scores
    v1_result = detect(batch, session_state, device_cache)
    layers = v1_result.get("detection_layers", {})

    # Extract V1 layer scores
    features: dict[str, float] = {
        "automation_score": layers.get("automation", {}).get("score", 0.0),
        "timing_score": layers.get("timing", {}).get("score", 0.0),
        "consistency_score": layers.get("consistency", {}).get("score", 0.0),
        "heuristics_score": layers.get("heuristics", {}).get("score", 0.0),
    }

    # Extract additional ML features
    features["timing_entropy"] = _compute_timing_entropy(batch)
    features["event_regularity"] = _compute_event_regularity(batch)
    features["modality_diversity"] = _compute_modality_diversity(batch)
    features["velocity_variance"] = _compute_velocity_variance(batch)

    # Logistic regression: sigmoid(bias + sum(w_i * x_i))
    logit = _ENSEMBLE_BIAS
    for feat_name, feat_val in features.items():
        weight = _ENSEMBLE_WEIGHTS.get(feat_name, 0.0)
        logit += weight * feat_val

    import math
    logit = max(-10.0, min(10.0, logit))
    ml_score = 1.0 / (1.0 + math.exp(-logit))

    # Blend V1 and V2 (V1 short-circuits on high-confidence automation)
    v1_score = v1_result["bot_score"]
    if v1_score > 0.85:
        # V1 caught a definitive signal — trust it
        final_score = v1_score
    else:
        # Weighted blend: 40% V1, 60% V2
        final_score = 0.4 * v1_score + 0.6 * ml_score

    final_score = round(min(1.0, max(0.0, final_score)), 4)

    if final_score > 0.7:
        action = "block"
    elif final_score > 0.4:
        action = "challenge"
    else:
        action = "allow"

    return {
        "bot_score": final_score,
        "v1_score": v1_score,
        "v2_score": round(ml_score, 4),
        "detection_layers": layers,
        "ml_features": {k: round(v, 4) for k, v in features.items()},
        "is_bot": final_score > 0.7,
        "action": action,
    }


def _compute_timing_entropy(batch: dict[str, Any]) -> float:
    """Compute entropy of inter-event timing. High entropy = human."""
    import math as _math

    keystroke_windows = batch.get("keystroke_windows", [])
    if not keystroke_windows:
        return 0.5  # neutral

    # Collect all dwell times
    dwells: list[float] = []
    for window in keystroke_windows:
        means = window.get("zone_dwell_means", [])
        dwells.extend(d for d in means if d is not None and d > 0)

    if len(dwells) < 5:
        return 0.5

    # Bin dwells into 10 buckets and compute entropy
    min_d = min(dwells)
    max_d = max(dwells)
    if max_d <= min_d:
        return 0.0  # zero entropy = definitely bot-like

    bins = [0] * 10
    for d in dwells:
        idx = min(9, int((d - min_d) / (max_d - min_d + 0.001) * 10))
        bins[idx] += 1

    total = sum(bins)
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in bins:
        if count > 0:
            p = count / total
            entropy -= p * _math.log2(p)

    # Normalize to 0-1 (max entropy for 10 bins is log2(10) ≈ 3.32)
    return min(1.0, entropy / 3.32)


def _compute_event_regularity(batch: dict[str, Any]) -> float:
    """Compute regularity of event timing. High regularity = bot-like."""
    keystroke_windows = batch.get("keystroke_windows", [])
    if not keystroke_windows:
        return 0.0

    stdevs: list[float] = []
    for window in keystroke_windows:
        s = window.get("zone_dwell_stdevs", [])
        stdevs.extend(v for v in s if v is not None and v >= 0)

    if not stdevs:
        return 0.0

    mean_stdev = sum(stdevs) / len(stdevs)
    # Low stdev in timing = high regularity = bot-like
    # Map: stdev=0 → regularity=1.0, stdev=50+ → regularity=0.0
    regularity = max(0.0, 1.0 - mean_stdev / 50.0)
    return min(1.0, regularity)


def _compute_modality_diversity(batch: dict[str, Any]) -> float:
    """Count distinct modalities present. More modalities = more human."""
    modalities = ["keystroke_windows", "pointer_windows", "touch_windows",
                  "scroll_windows", "sensor_windows"]
    present = sum(1 for m in modalities if batch.get(m))
    return min(1.0, present / 3.0)  # 3+ modalities = max diversity


def _compute_velocity_variance(batch: dict[str, Any]) -> float:
    """Compute variance in pointer velocities. High variance = human."""
    pointer_windows = batch.get("pointer_windows", [])
    if not pointer_windows:
        return 0.5  # neutral

    velocities: list[float] = []
    for window in pointer_windows:
        m = window.get("movement", {})
        v_mean = m.get("velocity_mean", -1)
        v_stdev = m.get("velocity_stdev", -1)
        if v_mean >= 0:
            velocities.append(v_mean)
        if v_stdev >= 0:
            velocities.append(v_stdev)

    if len(velocities) < 2:
        return 0.5

    mean = sum(velocities) / len(velocities)
    variance = sum((v - mean) ** 2 for v in velocities) / len(velocities)

    # Normalize: variance of 1000+ → 1.0
    return min(1.0, variance / 1000.0)
