"""kbio ingest service (V2).

Orchestrates the behavioral batch ingest pipeline:
1. Validate batch (dedup, timestamp)
2. Load/create session state from Valkey
3. Handle session lifecycle events
4. Delegate scoring to _pipeline.scoring_pipeline (pure computation)
5. Persist updated session state to Valkey
6. Return response

The service owns all I/O (Valkey, DB, Qdrant).  The pipeline is pure
computation with no side effects.

Target: <50ms compute (excluding network I/O).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
import importlib
from typing import Any

_db = importlib.import_module("01_core.db")
_valkey_mod = importlib.import_module("01_core.valkey")
_qdrant = importlib.import_module("01_core.qdrant")
_repo = importlib.import_module("03_kbio.ingest.repository")
_errors = importlib.import_module("01_core.errors")
_pipeline = importlib.import_module("03_kbio._pipeline.scoring_pipeline")
_stats = importlib.import_module("03_kbio._stats")

_log = logging.getLogger("kbio.ingest")


# Dim ID lookups (populated at startup, cached in memory)
_DIM_CACHE: dict[str, dict[str, int]] = {}


async def _ensure_dim_cache() -> None:
    """Load dim table code->id mappings into memory."""
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
    """Process a behavioral batch and return scoring results.

    This is the hot path. Every millisecond counts.

    V2: delegates pure computation to _pipeline.scoring_pipeline.process_batch().
    The service handles I/O only -- Valkey, DB, Qdrant.
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
            raise _errors.AppError(
                "DUPLICATE_BATCH",
                f"Batch '{batch_id}' already processed.",
                409,
            )

    # Step 2: Load or create session state from Valkey
    session_key = f"kbio:session:{session_id}"
    session_raw = await valkey.get(session_key)
    session_state = json.loads(session_raw) if session_raw else {}

    if not session_state:
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

    session_state = {
        **session_state,
        "pulse_count": session_state.get("pulse_count", 0) + 1,
    }

    # Step 3: Handle session lifecycle events
    if batch_type == "session_start":
        await valkey.set(session_key, json.dumps(session_state), ex=86400)
        return _build_lifecycle_response(batch_id, session_state, start)

    if batch_type == "session_end":
        ended_state = {**session_state, "status": "terminated"}
        await valkey.set(session_key, json.dumps(ended_state), ex=3600)
        return _build_lifecycle_response(batch_id, ended_state, start)

    if batch_type == "keepalive":
        await valkey.set(session_key, json.dumps(session_state), ex=86400)
        return _build_lifecycle_response(batch_id, session_state, start)

    # Step 4: Load user profile from cache/DB
    profile = await _load_profile(user_hash, valkey)

    if not profile or profile.get("baseline_quality") == "insufficient":
        enrolling_state = {
            **session_state,
            "baseline_quality": "insufficient",
            "current_drift_score": -1.0,
        }
        await valkey.set(
            session_key, json.dumps(enrolling_state), ex=86400,
        )
        return _build_lifecycle_response(
            batch_id, enrolling_state, start, enrolling=True,
        )

    session_state = {
        **session_state,
        "baseline_quality": profile.get("baseline_quality", "forming"),
    }

    # Steps 5+6: Parallel pre-fetch — ALL I/O runs concurrently before pipeline.
    # device_info, population stats, user stats, device stats, network stats
    # are all fetched in one asyncio.gather() so signal functions get real data.
    ip_address = batch.get("context", {}).get("ip", "")
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        (
            device_info,
            population_stats,
            user_stats,
            device_stats,
            network_stats,
        ) = await asyncio.gather(
            _load_device_info(device_uuid, valkey),
            _load_population_stats(valkey),
            _stats.fetch_user_stats(user_hash, valkey, conn),
            _stats.fetch_device_stats(device_uuid, valkey, conn),
            _stats.fetch_network_stats(ip_address, valkey, conn),
        )

    # Step 7: Delegate ALL pure computation to the pipeline.
    # Pre-fetched stats are passed directly so _build_signal_context
    # can populate all 40+ historical signal fields with real values.
    pipeline_result = _pipeline.process_batch(
        batch,
        profile,
        session_state,
        device_info=device_info,
        population_stats=population_stats,
        required_signals=batch.get("required_signals"),
        required_threats=batch.get("required_threats"),
        signal_configs=batch.get("signal_configs"),
        user_stats=user_stats,
        device_stats=device_stats,
        network_stats=network_stats,
    )

    # Step 8: Persist updated session state to Valkey
    updated_session = pipeline_result.get("_updated_session_state", {})
    await valkey.set(session_key, json.dumps(updated_session), ex=86400)

    # Step 9: Fire-and-forget velocity counter increments (never block hot path)
    asyncio.ensure_future(
        _increment_all_counters(user_hash, device_uuid, ip_address, valkey)
    )

    # Step 10: Log bot events if detected
    bot_score = pipeline_result.get("humanness", {}).get("bot_score", 0.0)
    if bot_score > 0.7:
        _schedule_bot_event(updated_session, batch_id, bot_score)

    # Step 10: Build public response (strip internal fields)
    processing_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "batch_id": batch_id,
        "processed_at": int(time.time() * 1000),
        "identity": pipeline_result.get("identity", {}),
        "anomaly": pipeline_result.get("anomaly", {}),
        "humanness": pipeline_result.get("humanness", {}),
        "threat": pipeline_result.get("threat", {}),
        "trust": pipeline_result.get("trust", {}),
        "session": pipeline_result.get("session", {}),
        "meta": pipeline_result.get("meta", {}),
        "verdict": pipeline_result.get("verdict", {}),
        "factors": pipeline_result.get("factors", []),
        "alerts": pipeline_result.get("alerts", []),
        "signals": pipeline_result.get("signals"),
        "threats_detected": pipeline_result.get("threats_detected"),
        "processing_ms": processing_ms,
    }


# ---------------------------------------------------------------------------
# Stats pre-fetch helpers
# ---------------------------------------------------------------------------


async def _increment_all_counters(
    user_hash: str,
    device_uuid: str,
    ip_address: str,
    valkey: Any,
) -> None:
    """Increment all sliding-window velocity counters. Fire-and-forget."""
    try:
        await asyncio.gather(
            _stats.increment_user_counters(user_hash, valkey),
            _stats.increment_device_counters(device_uuid, valkey),
            _stats.increment_network_counters(ip_address, user_hash, valkey),
        )
    except Exception as exc:  # noqa: BLE001
        _log.warning("Counter increment failed: %s", exc)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


async def _load_profile(
    user_hash: str, valkey: Any,
) -> dict[str, Any] | None:
    """Load user profile from Valkey cache, falling back to DB."""
    cache_key = f"kbio:profile:{user_hash}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        profile = await _repo.get_user_profile(conn, user_hash)

    if profile:
        await valkey.set(
            cache_key, json.dumps(profile, default=str), ex=3600,
        )

    return profile


async def _load_device_info(
    device_uuid: str, valkey: Any,
) -> dict[str, Any] | None:
    """Load device info from Valkey cache. Returns None if not found."""
    if not device_uuid:
        return None

    cache_key = f"kbio:device:{device_uuid}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)

    return None


async def _load_population_stats(
    valkey: Any,
) -> dict[str, Any] | None:
    """Load global population statistics from Valkey cache."""
    cache_key = "kbio:population_stats"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)

    return None


# Minimum similarity score to consider a Qdrant centroid match valid
_QDRANT_MIN_SIMILARITY = 0.5


async def _search_qdrant_centroid(
    user_hash: str, modality: str, query_vector: list[float],
) -> dict[str, Any] | None:
    """Try to find nearest centroid via Qdrant (sub-ms). Falls back to None."""
    try:
        _drift_scorer = importlib.import_module(
            "03_kbio._scoring.drift_scorer",
        )
        client = _qdrant.get_client()
        results = await _drift_scorer.search_nearest_centroid(
            client, user_hash, modality, query_vector, limit=1,
        )
        if results and results[0]["score"] > _QDRANT_MIN_SIMILARITY:
            return results[0]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def _build_lifecycle_response(
    batch_id: str,
    session_state: dict[str, Any],
    start: float,
    *,
    enrolling: bool = False,
) -> dict[str, Any]:
    """Build a minimal response for non-scoring batch types."""
    return {
        "batch_id": batch_id,
        "processed_at": int(time.time() * 1000),
        "identity": {
            "behavioral_drift": -1.0 if enrolling else session_state.get(
                "current_drift_score", 0.0,
            ),
            "credential_drift": None,
            "identity_confidence": 0.0 if enrolling else 0.5,
            "familiarity_score": -1.0,
            "cognitive_load": -1.0,
            "modality_drifts": {},
            "fusion_weights": {},
            "matched_cluster": None,
        },
        "anomaly": {},
        "humanness": {
            "bot_score": 0.0,
            "replay_score": 0.0,
            "automation_score": 0.0,
            "population_anomaly": 0.5,
            "is_human": True,
        },
        "threat": {
            "coercion_score": 0.0,
            "impersonation_score": 0.0,
        },
        "trust": {
            "session_trust": 0.5,
            "user_trust": float(session_state.get("user_trust", 0.5)),
            "device_trust": 0.0,
        },
        "session": {},
        "meta": {
            "confidence": 0.0 if enrolling else 0.5,
            "signal_richness": 0.0,
            "profile_maturity": 0.0,
        },
        "verdict": {
            "action": "allow",
            "risk_level": "low",
            "primary_reason": "session_lifecycle",
        },
        "factors": [],
        "alerts": [],
        "processing_ms": round((time.perf_counter() - start) * 1000, 2),
    }


def _schedule_bot_event(
    session_state: dict[str, Any], batch_id: str, bot_score: float,
) -> None:
    """Schedule async write of bot detection event. Fire-and-forget."""
    import logging

    logging.getLogger("kbio.ingest").info(
        "Bot detected: session=%s batch=%s score=%.2f",
        session_state.get("sdk_session_id"),
        batch_id,
        bot_score,
    )
