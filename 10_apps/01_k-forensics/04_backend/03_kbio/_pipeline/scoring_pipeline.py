"""kbio V2 scoring pipeline.

Orchestrates the full 22-score computation for each behavioral batch.
Target: <50ms server-side latency on cached profiles.

Pure computation layer -- I/O is handled by the caller (ingest service).
"""
from __future__ import annotations

import importlib
import time
from typing import Any

_normalizer = importlib.import_module("03_kbio._features.normalizer")
_session_desc = importlib.import_module("03_kbio._features.session_descriptor")
_drift = importlib.import_module("03_kbio._scoring.drift_scorer")
_anomaly = importlib.import_module("03_kbio._scoring.anomaly_scorer")
_bot = importlib.import_module("03_kbio._scoring.bot_detector")
_cred = importlib.import_module("03_kbio._scoring.credential_scorer")
_trust = importlib.import_module("03_kbio._scoring.trust_scorer")
_fusion = importlib.import_module("03_kbio._scoring.fusion")
_session = importlib.import_module("03_kbio._scoring.session_tracker")
_identity = importlib.import_module("03_kbio._scoring.identity_scorer")
_threat = importlib.import_module("03_kbio._scoring.threat_scorer")
_verdict = importlib.import_module("03_kbio._scoring.verdict_engine")
_bayesian = importlib.import_module("03_kbio._clustering.bayesian_selector")
_baseline = importlib.import_module("03_kbio._clustering.rolling_baseline")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def process_batch(
    batch: dict[str, Any],
    profile: dict[str, Any] | None,
    session_state: dict[str, Any],
    *,
    device_info: dict[str, Any] | None = None,
    population_stats: dict[str, Any] | None = None,
    required_signals: list[str] | None = None,
    required_threats: list[str] | None = None,
    signal_configs: dict[str, dict[str, Any]] | None = None,
    # Pre-fetched historical stats (from _stats service via asyncio.gather).
    # When provided, signals get real data instead of empty defaults.
    user_stats: dict[str, Any] | None = None,
    device_stats: dict[str, Any] | None = None,
    network_stats: dict[str, Any] | None = None,
    # Legacy passthrough parameters — accepted but not used in pipeline.
    # The ingest service passes these; having them here avoids TypeError.
    valkey: Any = None,  # noqa: ARG001
    user_hash: str = "",  # noqa: ARG001
    device_uuid: str = "",  # noqa: ARG001
    ip_address: str = "",  # noqa: ARG001
) -> dict[str, Any]:
    """Process a behavioral batch and compute all 22 scores.

    This is the hot path. All I/O (Valkey, PG, Qdrant) is done by the caller.
    This function is PURE -- given the same inputs, it always returns the
    same outputs.

    Pipeline steps:
    1. BOT DETECTION (short-circuit if > 0.85)
    2. FEATURE EXTRACTION (per-modality vectors)
    3. CLUSTER SELECTION (Bayesian posterior)
    4. DRIFT SCORING (per-modality -> fusion)
    5. CREDENTIAL DRIFT (if credential fields present)
    6. IDENTITY SCORES (confidence, familiarity, cognitive_load)
    7. ANOMALY SCORES (5 scores including takeover)
    8. HUMANNESS SCORES (bot + replay + automation + population)
    9. THREAT SCORES (coercion, impersonation)
    10. TRUST SCORES (session, user, device)
    11. META SCORES (confidence, signal_richness, maturity)
    12. VERDICT (action + risk_level)
    13. EXPLAINABILITY (top factors)
    14. SIGNAL + THREAT EVALUATION (if requested)

    Args:
        batch: Raw batch from SDK (keystroke_windows, pointer_windows, etc.)
        profile: User behavioral profile with clusters. None if enrolling.
        session_state: Current session state from Valkey.
        device_info: Device trust data.
        population_stats: Global population statistics for anomaly scoring.
        required_signals: Signal codes to compute. None = skip signals.
        required_threats: Threat codes to evaluate. None = skip threats.
        signal_configs: Per-signal config overrides from org settings.

    Returns:
        Full ScoringResponse dict with all 22 scores + verdict + session
        update.
    """
    start = time.perf_counter()

    # ------------------------------------------------------------------
    # 1. Bot detection (short-circuit)
    # ------------------------------------------------------------------
    bot_result = _bot.detect_v2(batch, session_state)
    bot_score = bot_result["bot_score"]
    automation_score = (
        bot_result
        .get("detection_layers", {})
        .get("automation", {})
        .get("score", 0.0)
    )

    # Replay detection
    replay_result = _bot.compute_replay_score(
        batch, session_state.get("sequence_hashes", []),
    )
    replay_score = replay_result.get("replay_score", 0.0)

    if bot_score > 0.85:
        return _build_bot_response(
            batch, session_state, bot_result, replay_score, start,
        )

    # ------------------------------------------------------------------
    # 2. Feature extraction
    # ------------------------------------------------------------------
    feature_vecs = _normalizer.normalize_features(batch)

    # ------------------------------------------------------------------
    # 3. Session descriptor + cluster selection
    # ------------------------------------------------------------------
    descriptor = _session_desc.compute_session_descriptor(
        batch.get("context", {}),
        keystroke_features=feature_vecs.get("keystroke"),
        pointer_features=feature_vecs.get("pointer"),
    )

    clusters = profile.get("clusters", []) if profile else []
    general_vec = _build_general_embedding(feature_vecs)

    cluster_result = (
        _bayesian.select_cluster(clusters, descriptor, general_vec)
        if clusters
        else {
            "cluster": None,
            "cluster_id": None,
            "posterior": 0.0,
            "match_quality": 0.0,
            "is_new_context": True,
            "all_posteriors": {},
        }
    )
    selected_cluster = cluster_result.get("cluster")

    # Grace period check
    grace: dict[str, Any] = {
        "in_grace_period": False,
        "remaining_sessions": 0,
        "max_verdict": None,
    }
    if selected_cluster:
        grace = _baseline.check_grace_period(
            selected_cluster,
            selected_cluster.get("session_count", 0),
        )

    # ------------------------------------------------------------------
    # 4. Drift scoring
    # ------------------------------------------------------------------
    modality_drifts_raw: dict[str, dict[str, Any]] = {}
    if selected_cluster:
        modality_drifts_raw = _drift.compute_all_modality_drifts(
            feature_vecs, selected_cluster,
        )

    modality_drifts = {m: d["drift"] for m, d in modality_drifts_raw.items()}
    event_counts = _count_events(batch)

    fused_drift, fusion_weights = _fusion.fuse(modality_drifts, event_counts)

    # ------------------------------------------------------------------
    # 5. Credential drift
    # ------------------------------------------------------------------
    credential_drift: float | None = None
    if batch.get("credential_fields") and profile:
        enrolled = profile.get("credential_profiles", [])
        if enrolled and batch["credential_fields"]:
            cred_result = _cred.score_credential_drift(
                batch["credential_fields"][0],
                enrolled[0],
            )
            credential_drift = cred_result.get("drift")

    # ------------------------------------------------------------------
    # 6. Identity scores
    # ------------------------------------------------------------------
    profile_maturity = (
        float(profile.get("profile_maturity", 0)) if profile else 0.0
    )
    total_events = sum(event_counts.values())

    meta = _fusion.compute_meta_scores(
        modality_drifts, event_counts, profile_maturity, total_events,
    )
    confidence = meta["confidence"]

    identity_confidence = _identity.compute_identity_confidence(
        fused_drift, credential_drift, confidence,
    )

    # Latest windows for familiarity and cognitive load
    ks_window = (
        (batch.get("keystroke_windows") or [{}])[-1]
        if batch.get("keystroke_windows")
        else {}
    )
    ptr_window = (
        (batch.get("pointer_windows") or [{}])[-1]
        if batch.get("pointer_windows")
        else {}
    )

    familiarity = _identity.compute_familiarity_score(
        ptr_window, session_state,
    )
    cognitive_load = _identity.compute_cognitive_load(
        ks_window, ptr_window, session_state,
    )

    # ------------------------------------------------------------------
    # 7. Anomaly scores (5 scores)
    # ------------------------------------------------------------------
    drift_history = list(session_state.get("drift_history", []))
    if fused_drift >= 0:
        drift_history.append(fused_drift)

    anomaly_result = _anomaly.compute_all_anomaly_scores(
        feature_vecs,
        modality_drifts,
        drift_history,
        session_state.get("modality_drift_history"),
        batch,
    )

    # ------------------------------------------------------------------
    # 8. Humanness scores
    # ------------------------------------------------------------------
    pop_anomaly = _bot.compute_population_anomaly(
        feature_vecs, population_stats,
    )

    humanness = {
        "bot_score": round(bot_score, 4),
        "replay_score": round(replay_score, 4),
        "automation_score": round(automation_score, 4),
        "population_anomaly": round(pop_anomaly, 4),
        "is_human": bot_score < 0.5,
    }

    # ------------------------------------------------------------------
    # 9. Threat scores
    # ------------------------------------------------------------------
    coercion = _threat.compute_coercion_score(
        ks_window, ptr_window, session_state, fused_drift, cognitive_load,
    )
    impersonation = _threat.compute_impersonation_score(
        fused_drift, credential_drift, familiarity, cognitive_load, bot_score,
    )

    # ------------------------------------------------------------------
    # 10. Trust scores
    # ------------------------------------------------------------------
    trust_result = _trust.compute_session_trust(
        identity_confidence=identity_confidence,
        bot_score=bot_score,
        replay_score=replay_score,
        automation_score=automation_score,
        session_anomaly=anomaly_result.get("session_anomaly", 0.0),
        takeover_probability=anomaly_result.get(
            "takeover", {},
        ).get("takeover_probability", 0.0),
        profile_maturity=profile_maturity,
        previous_trust=session_state.get("trust_score"),
    )
    session_trust = trust_result.get("session_trust", 0.5)

    user_trust = float(session_state.get("user_trust", 0.5))
    device_trust = _trust.compute_device_trust(
        device_info.get("session_count", 0) if device_info else 0,
        device_info.get("age_days", 0) if device_info else 0,
        device_info.get("recent_trusts", []) if device_info else [],
    )

    # ------------------------------------------------------------------
    # 11. Session timeline
    # ------------------------------------------------------------------
    timeline = _session.compute_session_timeline(
        drift_history, session_state.get("pulse_count", 0),
    )

    # ------------------------------------------------------------------
    # 12. Verdict
    # ------------------------------------------------------------------
    takeover_prob = anomaly_result.get(
        "takeover", {},
    ).get("takeover_probability", 0.0)

    verdict_result = _verdict.decide(
        session_trust,
        confidence,
        bot_score=bot_score,
        replay_score=replay_score,
        credential_drift=credential_drift,
        credential_confidence=(
            confidence if credential_drift is not None else 0.0
        ),
        coercion_score=coercion,
        takeover_probability=takeover_prob,
        grace_max_verdict=grace.get("max_verdict"),
    )

    # ------------------------------------------------------------------
    # 13. Build full response
    # ------------------------------------------------------------------
    processing_ms = round((time.perf_counter() - start) * 1000, 2)

    # ------------------------------------------------------------------
    # 14. Signal + Threat evaluation (if requested)
    # ------------------------------------------------------------------
    signal_output: dict[str, Any] | None = None
    threats_output: list[dict[str, Any]] | None = None

    if required_signals is not None or required_threats is not None:
        signal_ctx = _build_signal_context(
            identity_confidence=identity_confidence,
            familiarity=familiarity,
            cognitive_load=cognitive_load,
            fused_drift=fused_drift,
            credential_drift=credential_drift,
            confidence=confidence,
            anomaly_result=anomaly_result,
            humanness=humanness,
            coercion=coercion,
            impersonation=impersonation,
            session_trust=session_trust,
            user_trust=user_trust,
            device_trust=device_trust,
            meta=meta,
            timeline=timeline,
            modality_drifts=modality_drifts,
            batch=batch,
            device_info=device_info,
            session_state=session_state,
            user_stats=user_stats,
            device_stats=device_stats,
            network_stats=network_stats,
        )

        _signals_mod = importlib.import_module("03_kbio._signals")
        signal_include = set(required_signals) if required_signals else None
        signal_results = _signals_mod.compute_signals(
            signal_ctx, signal_configs, include=signal_include,
        )
        signal_output = {k: dict(v) for k, v in signal_results.items()}

        # Add signals to context for threat evaluation
        signal_ctx["signals"] = signal_results

        _threats_mod = importlib.import_module("03_kbio._threats")
        threat_include = set(required_threats) if required_threats else None
        threats_detected = _threats_mod.evaluate_threats(
            signal_ctx, include=threat_include,
        )
        threats_output = [dict(t) for t in threats_detected]

    updated_session = _build_updated_session(
        session_state,
        fused_drift,
        modality_drifts,
        drift_history,
        bot_score,
        anomaly_result.get("session_anomaly", 0.0),
        session_trust,
        credential_drift,
        timeline,
        cluster_result,
        batch,
    )

    return {
        "identity": {
            "behavioral_drift": round(fused_drift, 4),
            "credential_drift": (
                round(credential_drift, 4)
                if credential_drift is not None
                else None
            ),
            "identity_confidence": round(identity_confidence, 4),
            "familiarity_score": round(familiarity, 4),
            "cognitive_load": round(cognitive_load, 4),
            "modality_drifts": {
                m: {
                    "drift": round(d["drift"], 4),
                    "z_score": round(d.get("z_score", 0), 4),
                    "raw_distance": round(d.get("raw_distance", 0), 4),
                }
                for m, d in modality_drifts_raw.items()
            },
            "fusion_weights": fusion_weights,
            "matched_cluster": (
                {
                    "cluster_id": cluster_result.get("cluster_id"),
                    "match_quality": round(
                        cluster_result.get("match_quality", 0), 4,
                    ),
                    "posterior": round(
                        cluster_result.get("posterior", 0), 4,
                    ),
                }
                if selected_cluster
                else None
            ),
        },
        "anomaly": anomaly_result,
        "humanness": humanness,
        "threat": {
            "coercion_score": round(coercion, 4),
            "impersonation_score": round(impersonation, 4),
        },
        "trust": {
            "session_trust": round(session_trust, 4),
            "user_trust": round(user_trust, 4),
            "device_trust": round(device_trust, 4),
        },
        "session": timeline,
        "meta": meta,
        "verdict": verdict_result,
        "factors": [],  # TODO: explainability factors
        "alerts": [],   # TODO: alert evaluation
        "signals": signal_output,
        "threats_detected": threats_output,
        "processing_ms": processing_ms,
        "_updated_session_state": updated_session,
        "_updated_drift_history": drift_history[-50:],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_signal_context(
    *,
    identity_confidence: float,
    familiarity: float,
    cognitive_load: float,
    fused_drift: float,
    credential_drift: float | None,
    confidence: float,
    anomaly_result: dict[str, Any],
    humanness: dict[str, Any],
    coercion: float,
    impersonation: float,
    session_trust: float,
    user_trust: float,
    device_trust: float,
    meta: dict[str, Any],
    timeline: dict[str, Any],
    modality_drifts: dict[str, float],
    batch: dict[str, Any],
    device_info: dict[str, Any] | None,
    session_state: dict[str, Any],
    user_stats: dict[str, Any] | None = None,
    device_stats: dict[str, Any] | None = None,
    network_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the evaluation context that signal functions expect.

    Namespaces:
        scores.*          - all pipeline scores (flat)
        drift_trend.*     - drift trend from session timeline
        modality_drift.*  - per-modality drift values
        device.*          - device metadata (enriched from device_stats)
        network.*         - network metadata (enriched from network_stats)
        user.*            - user metadata (enriched from user_stats)
        session.*         - session metadata from session state + batch

    When user_stats / device_stats / network_stats are provided (pre-fetched
    from Valkey by the ingest service), the context has real historical data.
    Otherwise signal functions receive safe zero/empty defaults.
    """
    takeover = anomaly_result.get("takeover", {})

    scores = {
        "behavioral_drift": fused_drift,
        "credential_drift": credential_drift,
        "identity_confidence": identity_confidence,
        "familiarity_score": familiarity,
        "cognitive_load": cognitive_load,
        "session_anomaly": anomaly_result.get("session_anomaly", 0.0),
        "velocity_anomaly": anomaly_result.get("velocity_anomaly", 0.0),
        "takeover_probability": takeover.get("takeover_probability", 0.0),
        "pattern_break": anomaly_result.get("pattern_break", 0.0),
        "consistency_score": anomaly_result.get("consistency", 0.5),
        "bot_score": humanness.get("bot_score", 0.0),
        "replay_score": humanness.get("replay_score", 0.0),
        "automation_score": humanness.get("automation_score", 0.0),
        "population_anomaly": humanness.get("population_anomaly", 0.0),
        "coercion_score": coercion,
        "impersonation_score": impersonation,
        "session_trust": session_trust,
        "user_trust": user_trust,
        "device_trust": device_trust,
        "confidence": confidence,
        "signal_richness": meta.get("signal_richness", 0.0),
        "profile_maturity": meta.get("profile_maturity", 0.0),
    }

    drift_trend = timeline.get("trend", {})
    drift_trend_ctx = {
        "slope": drift_trend.get("slope", 0.0),
        "acceleration": drift_trend.get("acceleration", 0.0),
        "direction": drift_trend.get("direction", "stable"),
        "mean": timeline.get("drift_mean", 0.0),
        "max": timeline.get("drift_max", 0.0),
        "stdev": timeline.get("drift_stdev", 0.0),
    }

    batch_ctx = batch.get("context", {})

    # Device context: merge device_info (trust cache) with device_stats (DB history)
    _dev = device_stats or {}
    device_ctx: dict[str, Any] = {
        # device_info from trust cache takes precedence for trust fields
        "is_trusted": (
            device_info.get("is_trusted", _dev.get("is_trusted", False))
            if device_info else _dev.get("is_trusted", False)
        ),
        "is_emulator": (
            device_info.get("is_emulator", _dev.get("is_emulator", False))
            if device_info else _dev.get("is_emulator", False)
        ),
        "fingerprint_drift": (
            device_info.get("fingerprint_drift", _dev.get("fingerprint_drift", 0.0))
            if device_info else _dev.get("fingerprint_drift", 0.0)
        ),
        "platform": (
            device_info.get("platform", _dev.get("platform", ""))
            if device_info else _dev.get("platform", "")
        ),
        # device_stats has authoritative historical counts
        "session_count": _dev.get(
            "session_count",
            device_info.get("session_count", 0) if device_info else 0,
        ),
        "sessions_last_24h": _dev.get("sessions_last_24h", 0),
        "age_days": _dev.get(
            "age_days",
            device_info.get("age_days", 0) if device_info else 0,
        ),
        "user_count": _dev.get("user_count", 1),
        # Derived fields
        "is_new": _dev.get(
            "session_count",
            device_info.get("session_count", 0) if device_info else 0,
        ) < 2,
        "is_multi_user": _dev.get("user_count", 1) > 1,
    }

    # Network context: batch metadata + pre-fetched reputation/velocity stats
    _net = network_stats or {}
    network_ctx: dict[str, Any] = {
        "ip": batch_ctx.get("ip", ""),
        "country": batch_ctx.get("country", _net.get("country", "")),
        # Batch flags take precedence; fall back to pre-fetched reputation data
        "is_vpn": batch_ctx.get("is_vpn", _net.get("is_vpn", False)),
        "is_tor": batch_ctx.get("is_tor", _net.get("is_tor", False)),
        "is_proxy": batch_ctx.get("is_proxy", _net.get("is_proxy", False)),
        "is_datacenter": batch_ctx.get(
            "is_datacenter", _net.get("is_datacenter", False)
        ),
        "is_residential_proxy": _net.get("is_residential_proxy", False),
        "ip_reputation_score": _net.get("ip_reputation_score", 0.0),
        "asn": batch_ctx.get("asn", _net.get("asn", "")),
        # Real-time velocity from Valkey sliding-window counters
        "ip_sessions_1h": _net.get("ip_sessions_1h", 0),
        "ip_users_1h": _net.get("ip_users_1h", 0),
        "ip_sessions_24h": _net.get("ip_sessions_24h", 0),
        # Derived: is the current country new for this user?
        "known_countries": _net.get("known_countries", []),
        "is_new_country": _net.get("is_new_country", False),
        "last_session_country": _net.get("last_session_country", ""),
    }

    # User context: session state + pre-fetched historical stats
    _usr = user_stats or {}
    user_ctx: dict[str, Any] = {
        "user_hash": session_state.get("user_hash", ""),
        "trust_level": _usr.get(
            "trust_level", session_state.get("trust_level", "trusted")
        ),
        "user_trust": user_trust,
        # Historical stats from Valkey (real data, no mocks)
        "account_age_days": _usr.get("account_age_days", 0),
        "total_sessions": _usr.get("total_sessions", 0),
        "sessions_last_24h": _usr.get("sessions_last_24h", 0),
        "days_since_last_session": _usr.get("days_since_last_session", 0),
        "typical_hours": _usr.get("typical_hours", []),
        "known_countries": _usr.get("known_countries", []),
        "total_devices": _usr.get("total_devices", 0),
        "failed_challenges_24h": _usr.get("failed_challenges_24h", 0),
        "last_session_country": _usr.get("last_session_country", ""),
    }

    # Device context: device_info (from trust tables) + pre-fetched stats
    _dev = device_stats or {}
    session_ctx: dict[str, Any] = {
        "pulse_count": session_state.get("pulse_count", 0),
        "status": session_state.get("status", "active"),
        "baseline_quality": session_state.get("baseline_quality", ""),
        "duration_seconds": batch_ctx.get("session_duration_seconds"),
        "page_count": batch_ctx.get("page_count"),
    }

    return {
        "scores": scores,
        "drift_trend": drift_trend_ctx,
        "modality_drift": modality_drifts,
        "device": device_ctx,
        "network": network_ctx,
        "user": user_ctx,
        "session": session_ctx,
        # Top-level backward-compat fields
        "behavioral_drift": fused_drift,
        "bot_score": humanness.get("bot_score", 0.0),
        "session_trust": session_trust,
        "confidence": confidence,
    }


_TARGET_EMBEDDING_DIM = 128


def _build_general_embedding(
    feature_vecs: dict[str, list[float]],
) -> list[float]:
    """Concatenate per-modality vectors and pad/truncate to 128d."""
    combined: list[float] = []
    for modality in ("keystroke", "pointer", "touch", "sensor"):
        vec = feature_vecs.get(modality, [])
        combined.extend(vec)

    # Pad or truncate to target dimension
    if len(combined) >= _TARGET_EMBEDDING_DIM:
        combined = combined[:_TARGET_EMBEDDING_DIM]
    else:
        combined.extend([0.0] * (_TARGET_EMBEDDING_DIM - len(combined)))

    # L2 normalize
    return _normalizer.l2_normalize(combined)


def _count_events(batch: dict[str, Any]) -> dict[str, int]:
    """Count events per modality from batch windows."""
    counts: dict[str, int] = {}
    modality_map = {
        "keystroke": "keystroke_windows",
        "pointer": "pointer_windows",
        "touch": "touch_windows",
        "sensor": "sensor_windows",
    }

    for modality, window_key in modality_map.items():
        windows = batch.get(window_key, [])
        if not windows:
            continue

        total = 0
        for w in windows:
            if modality == "keystroke":
                hit_counts = w.get("zone_hit_counts", [])
                total += sum(
                    h for h in hit_counts if isinstance(h, (int, float)) and h > 0
                )
            else:
                total += w.get("event_count", 1)

        counts[modality] = int(total)

    return counts


def _build_bot_response(
    _batch: dict[str, Any],
    session_state: dict[str, Any],
    bot_result: dict[str, Any],
    replay_score: float,
    start: float,
) -> dict[str, Any]:
    """Build minimal response when bot is detected (short-circuit)."""
    processing_ms = round((time.perf_counter() - start) * 1000, 2)
    bot_score = bot_result["bot_score"]
    automation_score = (
        bot_result
        .get("detection_layers", {})
        .get("automation", {})
        .get("score", 0.0)
    )

    # Minimal session update for bot detection
    updated_session = dict(session_state)
    updated_session["bot_score"] = bot_score
    updated_session["trust_level"] = "anomalous"

    return {
        "identity": {
            "behavioral_drift": -1.0,
            "credential_drift": None,
            "identity_confidence": 0.0,
            "familiarity_score": -1.0,
            "cognitive_load": -1.0,
            "modality_drifts": {},
            "fusion_weights": {},
            "matched_cluster": None,
        },
        "anomaly": {
            "session_anomaly": -1.0,
            "modality_anomalies": {},
            "velocity_anomaly": 0.0,
            "takeover": {
                "takeover_probability": 0.0,
                "cusum_signal": 0.0,
                "velocity_signal": 0.0,
                "concordance_signal": 0.0,
                "changepoint_detected": False,
            },
            "pattern_break": 0.0,
            "consistency": 0.5,
            "method": "bot_short_circuit",
        },
        "humanness": {
            "bot_score": round(bot_score, 4),
            "replay_score": round(replay_score, 4),
            "automation_score": round(automation_score, 4),
            "population_anomaly": 0.5,
            "is_human": False,
        },
        "threat": {
            "coercion_score": 0.0,
            "impersonation_score": 0.0,
        },
        "trust": {
            "session_trust": 0.0,
            "user_trust": float(session_state.get("user_trust", 0.5)),
            "device_trust": 0.0,
        },
        "session": {
            "drift_current": 0.0,
            "drift_mean": 0.0,
            "drift_max": 0.0,
            "drift_stdev": 0.0,
            "batches_processed": session_state.get("pulse_count", 0) + 1,
            "trend": {
                "direction": "stable",
                "slope": 0.0,
                "acceleration": 0.0,
                "changepoint_detected": False,
                "changepoint_batch_seq": -1,
            },
            "stability_score": 1.0,
        },
        "meta": {
            "confidence": 0.0,
            "signal_richness": 0.0,
            "profile_maturity": 0.0,
        },
        "verdict": {
            "action": bot_result.get("action", "block"),
            "risk_level": "critical",
            "primary_reason": "bot_score",
        },
        "factors": [],
        "alerts": [],
        "processing_ms": processing_ms,
        "_updated_session_state": updated_session,
        "_updated_drift_history": list(
            session_state.get("drift_history", [])
        )[-50:],
    }


def _build_updated_session(
    session_state: dict[str, Any],
    fused_drift: float,
    modality_drifts: dict[str, float],
    drift_history: list[float],
    bot_score: float,
    anomaly_score: float,
    trust_score: float,
    credential_drift: float | None,
    timeline: dict[str, Any],
    cluster_result: dict[str, Any],
    batch: dict[str, Any],
) -> dict[str, Any]:
    """Build updated session state dict for Valkey persistence.

    Returns a new dict -- never mutates the input session_state.
    """
    updated = dict(session_state)

    # Drift state
    updated["current_drift_score"] = fused_drift
    if fused_drift >= 0:
        updated["max_drift_score"] = max(
            session_state.get("max_drift_score", 0.0), fused_drift,
        )

    updated["drift_history"] = drift_history[-50:]

    # Per-modality drift history (for concordance detection)
    mod_history: dict[str, list[float]] = dict(
        session_state.get("modality_drift_history", {}),
    )
    for modality, drift_val in modality_drifts.items():
        existing = list(mod_history.get(modality, []))
        existing.append(drift_val)
        mod_history[modality] = existing[-50:]
    updated["modality_drift_history"] = mod_history

    # Scores
    updated["bot_score"] = bot_score
    updated["anomaly_score"] = anomaly_score
    updated["trust_score"] = trust_score
    updated["credential_drift"] = credential_drift

    # Trust level classification
    if fused_drift >= 0.65:
        updated["trust_level"] = "anomalous"
    elif fused_drift >= 0.30:
        updated["trust_level"] = "suspicious"
    else:
        updated["trust_level"] = "trusted"

    # Cluster tracking
    updated["last_cluster_id"] = cluster_result.get("cluster_id")
    updated["last_match_quality"] = round(
        cluster_result.get("match_quality", 0), 4,
    )

    # Sequence hash for replay detection
    batch_hash = _bot.compute_batch_hash(batch)
    existing_hashes = list(session_state.get("sequence_hashes", []))
    existing_hashes.append(batch_hash)
    updated["sequence_hashes"] = existing_hashes[-100:]

    # Session timeline summary
    updated["session_timeline"] = timeline

    return updated
