"""kbio ingest service.

Orchestrates the behavioral batch ingest pipeline:
1. Validate batch (dedup, timestamp)
2. Bot detection
3. Load profile from cache/DB
4. Drift scoring (per-modality → fusion → trend)
5. Alert evaluation
6. Return response, schedule async DB writes

Target: <50ms compute (excluding network I/O).
"""

from __future__ import annotations

import json
import time
import uuid
import importlib
from typing import Any

_db = importlib.import_module("01_core.db")
_valkey_mod = importlib.import_module("01_core.valkey")
_qdrant = importlib.import_module("01_core.qdrant")
_drift_scorer = importlib.import_module("03_kbio._scoring.drift_scorer")
_fusion = importlib.import_module("03_kbio._scoring.fusion")
_session_tracker = importlib.import_module("03_kbio._scoring.session_tracker")
_credential_scorer = importlib.import_module("03_kbio._scoring.credential_scorer")
_bot_detector = importlib.import_module("03_kbio._scoring.bot_detector")
_anomaly_scorer = importlib.import_module("03_kbio._scoring.anomaly_scorer")
_trust_scorer = importlib.import_module("03_kbio._scoring.trust_scorer")
_repo = importlib.import_module("03_kbio.ingest.repository")
_errors = importlib.import_module("01_core.errors")


# Drift action thresholds (default, overridable per tenant)
DRIFT_THRESHOLDS = {
    "monitor": 0.30,
    "challenge": 0.65,
    "block": 0.85,
}

# Dim ID lookups (populated at startup, cached in memory)
_DIM_CACHE: dict[str, dict[str, int]] = {}


async def _ensure_dim_cache() -> None:
    """Load dim table code→id mappings into memory."""
    if _DIM_CACHE:
        return
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        for table, key in [
            ("01_dim_session_statuses", "session_statuses"),
            ("02_dim_batch_types", "batch_types"),
            ("03_dim_trust_levels", "trust_levels"),
            ("04_dim_drift_actions", "drift_actions"),
            ("05_dim_baseline_qualities", "baseline_qualities"),
            ("08_dim_alert_severities", "alert_severities"),
        ]:
            rows = await conn.fetch(f'SELECT id, code FROM "10_kbio"."{table}"')
            _DIM_CACHE[key] = {r["code"]: r["id"] for r in rows}


def _dim_id(table_key: str, code: str) -> int:
    """Look up a dim table ID by code."""
    return _DIM_CACHE.get(table_key, {}).get(code, 1)


async def ingest_batch(
    batch: dict[str, Any],
    *,
    headers: dict[str, str],
) -> dict[str, Any]:
    """Process a behavioral batch and return drift scores.

    This is the hot path. Every millisecond counts.
    """
    await _ensure_dim_cache()
    start = time.perf_counter()

    header = batch.get("header", {})
    batch_id = header.get("batch_id", "")
    session_id = header.get("session_id", "")
    user_hash = header.get("user_hash", "")
    device_uuid = header.get("device_uuid", "")
    batch_type = batch.get("type", "behavioral")

    valkey = _valkey_mod.get_client()

    # Step 1: Batch idempotency check
    dedup_key = f"kbio:batch:{batch_id}"
    if batch_id:
        was_set = await valkey.set(dedup_key, "1", ex=86400, nx=True)
        if not was_set:
            raise _errors.AppError("DUPLICATE_BATCH", f"Batch '{batch_id}' already processed.", 409)

    # Step 2: Load or create session state from Valkey
    session_key = f"kbio:session:{session_id}"
    session_raw = await valkey.get(session_key)
    session_state = json.loads(session_raw) if session_raw else {}

    if not session_state:
        # New session
        session_state = {
            "id": str(uuid.uuid4()),
            "sdk_session_id": session_id,
            "user_hash": user_hash,
            "device_uuid": device_uuid,
            "status": "active",
            "trust_level": "trusted",
            "baseline_quality": "insufficient",
            "pulse_count": 0,
            "drift_history": [],
            "max_drift_score": 0.0,
            "current_drift_score": 0.0,
            "bot_score": 0.0,
        }

    session_state["pulse_count"] = session_state.get("pulse_count", 0) + 1

    # Step 3: Handle session lifecycle events
    if batch_type == "session_start":
        await valkey.set(session_key, json.dumps(session_state), ex=86400)
        return _build_response(batch_id, session_state, start)

    if batch_type == "session_end":
        session_state["status"] = "terminated"
        await valkey.set(session_key, json.dumps(session_state), ex=3600)
        return _build_response(batch_id, session_state, start)

    if batch_type == "keepalive":
        await valkey.set(session_key, json.dumps(session_state), ex=86400)
        return _build_response(batch_id, session_state, start)

    # Step 4: Bot detection (behavioral/critical_action batches)
    bot_result = _bot_detector.detect_v2(batch, session_state)
    session_state["bot_score"] = bot_result["bot_score"]

    if bot_result["is_bot"]:
        session_state["trust_level"] = "anomalous"
        await valkey.set(session_key, json.dumps(session_state), ex=86400)
        # Schedule async bot event write
        _schedule_bot_event(session_state, batch_id, bot_result)
        return _build_response(batch_id, session_state, start, bot_result=bot_result)

    # Step 5: Load user profile from cache/DB
    profile = await _load_profile(user_hash, valkey)

    if not profile or profile.get("baseline_quality") == "insufficient":
        session_state["baseline_quality"] = "insufficient"
        session_state["current_drift_score"] = -1.0
        await valkey.set(session_key, json.dumps(session_state), ex=86400)
        return _build_response(batch_id, session_state, start, enrolling=True)

    session_state["baseline_quality"] = profile.get("baseline_quality", "forming")

    # Step 6: Normalize features
    feature_vecs = _drift_scorer.normalize_features(batch)

    # Step 7: Select centroid
    centroids = profile.get("centroids", [])
    if isinstance(centroids, str):
        centroids = json.loads(centroids) if centroids else []
    centroid = _drift_scorer.select_centroid(centroids, batch.get("context", {}))

    # Step 8: Per-modality drift
    modality_drifts: dict[str, float] = {}
    event_counts: dict[str, int] = {}

    for modality, vec in feature_vecs.items():
        if centroid:
            centroid_vec = centroid.get(f"{modality}_embedding", [])
            intra = centroid.get("intra_distance", {})
            drift = _drift_scorer.compute_modality_drift(
                vec, centroid_vec,
                intra.get("mean", 0.5), intra.get("stdev", 0.1),
            )
            modality_drifts[modality] = drift

        # Count events per modality
        windows = batch.get(f"{modality}_windows", [])
        total_events = sum(
            sum(w.get("zone_hit_counts", [0])) if modality == "keystroke"
            else w.get("event_count", 1)
            for w in windows
        ) if windows else 0
        event_counts[modality] = total_events

    # Step 9: Adaptive fusion
    fused_drift, fusion_weights = _fusion.fuse(modality_drifts, event_counts)

    # Step 9b: Anomaly scoring (population-level)
    anomaly_result = _anomaly_scorer.compute_anomaly_score(
        feature_vecs, modality_drifts, batch,
    )
    anomaly_score = anomaly_result.get("anomaly_score", -1.0)

    # Step 10: Credential drift (if credential fields present)
    cred_drift = None
    if batch.get("credential_fields"):
        enrolled_cred = profile.get("credential_profiles", [])
        if isinstance(enrolled_cred, str):
            enrolled_cred = json.loads(enrolled_cred) if enrolled_cred else []
        if enrolled_cred:
            cred_result = _credential_scorer.score_credential_drift(
                batch["credential_fields"][0],
                enrolled_cred[0],
            )
            cred_drift = cred_result["drift"]

    # Step 11: Session trend (CUSUM)
    drift_history = session_state.get("drift_history", [])
    if fused_drift >= 0:
        drift_history.append(fused_drift)
    session_state["drift_history"] = drift_history[-50:]  # keep last 50

    trend = _session_tracker.compute_trend(drift_history)
    changepoint = _session_tracker.detect_changepoint(drift_history)

    # Step 12: Confidence
    profile_maturity = float(profile.get("profile_maturity", 0))
    total_events = sum(event_counts.values())
    confidence = _fusion.compute_confidence(
        modality_drifts, event_counts, profile_maturity, total_events,
    )

    # Step 12b: Trust scoring (composite)
    trust_result = _trust_scorer.compute_trust_score(
        drift_score=fused_drift,
        anomaly_score=anomaly_score,
        bot_score=bot_result.get("bot_score", 0.0),
        device_known=True,  # TODO: check device registry
        device_age_days=0,  # TODO: from device profile
        baseline_quality=session_state.get("baseline_quality", "insufficient"),
        profile_maturity=profile_maturity,
        session_state=session_state,
        confidence=confidence,
    )
    trust_score_val = trust_result.get("trust_score", 0.5)

    # Step 13: Determine action
    action = "allow"
    if fused_drift >= 0:
        if fused_drift > DRIFT_THRESHOLDS["block"]:
            action = "block"
        elif fused_drift > DRIFT_THRESHOLDS["challenge"]:
            action = "challenge"
        elif fused_drift > DRIFT_THRESHOLDS["monitor"]:
            action = "monitor"

    if changepoint.get("detected"):
        action = max(action, "challenge", key=lambda a: ["allow", "monitor", "challenge", "block"].index(a))

    # Step 14: Update session state
    session_state["current_drift_score"] = fused_drift
    if fused_drift >= 0:
        session_state["max_drift_score"] = max(
            session_state.get("max_drift_score", 0.0), fused_drift
        )

    # Update trust level
    if fused_drift >= 0.65:
        session_state["trust_level"] = "anomalous"
    elif fused_drift >= 0.30:
        session_state["trust_level"] = "suspicious"
    else:
        session_state["trust_level"] = "trusted"

    await valkey.set(session_key, json.dumps(session_state), ex=86400)

    # Build response
    processed_at = int(time.time() * 1000)

    return {
        "batch_id": batch_id,
        "processed_at": processed_at,
        "drift_score": fused_drift,
        "confidence": confidence,
        "signal_scores": modality_drifts,
        "fusion_weights": fusion_weights,
        "action": action,
        "bot_score": bot_result.get("bot_score", 0.0),
        "anomaly_score": anomaly_score,
        "trust_score": trust_score_val,
        "device_drift": -1.0,  # TODO: implement device drift
        "network_drift": -1.0,  # TODO: implement network drift
        "credential_drift": cred_drift,
        "composite_score": fused_drift,  # V1: composite = behavioral
        "auth_state": {
            "session_trust": session_state.get("trust_level", "trusted"),
            "device_known": True,  # TODO: check device registry
            "baseline_quality": session_state.get("baseline_quality", "insufficient"),
            "baseline_age_days": 0,  # TODO: compute from profile
        },
        "drift_trend": {
            **trend,
            "changepoint_detected": changepoint.get("detected", False),
        },
        "alerts": [],  # TODO: alert evaluation
        "_latency_ms": round((time.perf_counter() - start) * 1000, 2),
    }


async def _load_profile(user_hash: str, valkey: Any) -> dict[str, Any] | None:
    """Load user profile from Valkey cache, falling back to DB."""
    cache_key = f"kbio:profile:{user_hash}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fall back to DB
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        profile = await _repo.get_user_profile(conn, user_hash)

    if profile:
        # Cache for 1 hour
        await valkey.set(cache_key, json.dumps(profile, default=str), ex=3600)

    return profile


# Minimum similarity score to consider a Qdrant centroid match valid
_QDRANT_MIN_SIMILARITY = 0.5


async def _search_qdrant_centroid(
    user_hash: str, modality: str, query_vector: list[float]
) -> dict[str, Any] | None:
    """Try to find nearest centroid via Qdrant (sub-ms). Falls back to None."""
    try:
        client = _qdrant.get_client()
        results = await _drift_scorer.search_nearest_centroid(
            client, user_hash, modality, query_vector, limit=1,
        )
        if results and results[0]["score"] > _QDRANT_MIN_SIMILARITY:
            return results[0]
    except Exception:
        pass
    return None


def _build_response(
    batch_id: str,
    session_state: dict,
    start: float,
    *,
    bot_result: dict | None = None,
    enrolling: bool = False,
) -> dict[str, Any]:
    """Build a minimal response for non-scoring batch types."""
    return {
        "batch_id": batch_id,
        "processed_at": int(time.time() * 1000),
        "drift_score": -1.0 if enrolling else session_state.get("current_drift_score", 0.0),
        "confidence": 0.0 if enrolling else 0.5,
        "signal_scores": {},
        "fusion_weights": {},
        "action": bot_result["action"] if bot_result and bot_result.get("is_bot") else "allow",
        "bot_score": bot_result["bot_score"] if bot_result else 0.0,
        "anomaly_score": -1.0,
        "trust_score": 0.5,
        "device_drift": -1.0,
        "network_drift": -1.0,
        "credential_drift": None,
        "composite_score": -1.0,
        "auth_state": {
            "session_trust": session_state.get("trust_level", "trusted"),
            "device_known": True,
            "baseline_quality": session_state.get("baseline_quality", "insufficient"),
            "baseline_age_days": 0,
        },
        "drift_trend": {},
        "alerts": [],
        "_latency_ms": round((time.perf_counter() - start) * 1000, 2),
    }


def _schedule_bot_event(session_state: dict, batch_id: str, bot_result: dict) -> None:
    """Schedule async write of bot detection event. Fire-and-forget."""
    import logging
    logging.getLogger("kbio.ingest").info(
        "Bot detected: session=%s batch=%s score=%.2f",
        session_state.get("sdk_session_id"), batch_id, bot_result["bot_score"],
    )
