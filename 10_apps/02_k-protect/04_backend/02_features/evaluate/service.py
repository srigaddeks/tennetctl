"""kprotect evaluate service.

Orchestrates: receive request → call kbio → assemble context → run rule engine → persist decision.

Valkey strategy:
  - Policy set + signal selections cached at 300s each (org config rarely changes)
  - Policy catalog cached at 600s (rarely changes)
  - User stats, device stats, network velocity fetched from kbio _stats service
    via a single Valkey pipeline GET burst (all keys in one round trip) before
    calling kbio, so _assemble_context has real data not stale zeros.
  - Valkey pipeline batching: all three stat GETs execute in one pipe.execute()
    to minimise Valkey round-trips on the critical path.
"""
from __future__ import annotations

import asyncio
import importlib
import json
import time
import uuid
from typing import Any

_db = importlib.import_module("01_core.db")
_valkey_mod = importlib.import_module("01_core.valkey")
_errors = importlib.import_module("01_core.errors")
_kbio = importlib.import_module("02_features.evaluate.kbio_client")
_engine = importlib.import_module("02_features.evaluate.rule_engine")
_signals_registry = importlib.import_module("03_kbio._signals._registry")
_threats_registry = importlib.import_module("03_kbio._threats._registry")


async def evaluate(
    request: dict[str, Any],
    *,
    org_id: str,
    actor_id: str,
) -> dict[str, Any]:
    """Full evaluation pipeline.

    0. Load org's active policy set + signal selections
    1. Resolve required signals (from selections + threat types)
    2. Call kbio for scores (forward batch + signal/threat context)
    3. Assemble evaluation context
    4. Run rule engine
    5. Persist decision (async)
    6. Return result
    """
    start = time.perf_counter()
    valkey = _valkey_mod.get_client()

    session_id = request.get("session_id", "")
    user_hash = request.get("user_hash", "")
    device_uuid = request.get("device_uuid", "")
    event_type = request.get("event_type", "behavioral")
    batch = request.get("batch", {})
    policy_set_code = request.get("policy_set_code")

    # Step 0: Load policy set + signal selections in parallel.
    # Also batch-fetch stats cache keys from Valkey in the same asyncio.gather()
    # so context assembly has real data without sequential round-trips.
    policy_start = time.perf_counter()
    ip_address = request.get("metadata", {}).get("ip_address", "")

    (
        (policies, eval_mode, policy_set_id),
        signal_selections,
        cached_stats,
    ) = await asyncio.gather(
        _load_policy_set(org_id, policy_set_code, valkey),
        _load_signal_selections(org_id, valkey),
        # Batch-fetch all three stat blobs in a single Valkey pipeline
        _batch_fetch_stats(user_hash, device_uuid, ip_address, valkey),
    )

    required_signals = [s["signal_code"] for s in signal_selections if s.get("signal_code")]
    signal_configs: dict[str, Any] = {}
    for s in signal_selections:
        code = s.get("signal_code")
        overrides = s.get("config_overrides")
        if code and overrides:
            signal_configs[code] = overrides

    threat_type_codes = [p.get("threat_type_code") for p in policies if p.get("threat_type_code")]

    threat_signals = _signals_registry.get_required_signals_for_threats(
        threat_type_codes, _threats_registry.get_all_threat_types()
    )
    all_required_signals = list(set(required_signals) | threat_signals)

    # Step 1: Call kbio (forward the batch with signal/threat context)
    kbio_start = time.perf_counter()
    kbio_result = await _kbio.ingest_batch(
        batch,
        required_signals=all_required_signals if all_required_signals else None,
        required_threats=threat_type_codes if threat_type_codes else None,
        signal_configs=signal_configs if signal_configs else None,
    )
    kbio_latency = round((time.perf_counter() - kbio_start) * 1000, 2)

    kbio_data = kbio_result.get("data", {}) if kbio_result.get("ok") else {}
    degraded = not kbio_result.get("ok", False)

    # Step 2: Assemble evaluation context (with pre-fetched stats)
    ctx = _assemble_context(kbio_data, request, degraded, cached_stats=cached_stats)

    if not policies:
        # No policies configured — allow by default
        return _build_response(
            action="allow",
            results=[],
            ctx=ctx,
            kbio_data=kbio_data,
            degraded=degraded,
            start=start,
            kbio_latency=kbio_latency,
            policy_latency=0.0,
            policy_set_id=policy_set_id,
        )

    # Step 4: Run rule engine
    final_action, results = _engine.evaluate_policy_set(policies, ctx, mode=eval_mode)
    policy_latency = round((time.perf_counter() - policy_start) * 1000, 2)

    # Step 5: Persist decision (fire-and-forget background)
    decision_id = str(uuid.uuid4())
    _schedule_decision_persist(
        decision_id=decision_id,
        org_id=org_id,
        session_id=session_id,
        user_hash=user_hash,
        device_uuid=device_uuid,
        policy_set_id=policy_set_id,
        action=final_action,
        degraded=degraded,
        kbio_latency=kbio_latency,
        policy_latency=policy_latency,
        total_latency=round((time.perf_counter() - start) * 1000, 2),
        results=results,
        actor_id=actor_id,
    )

    # Step 6: Return result
    return _build_response(
        action=final_action,
        results=results,
        ctx=ctx,
        kbio_data=kbio_data,
        degraded=degraded,
        start=start,
        kbio_latency=kbio_latency,
        policy_latency=policy_latency,
        policy_set_id=policy_set_id,
        decision_id=decision_id,
    )


def _assemble_context(
    kbio_data: dict[str, Any],
    request: dict[str, Any],
    degraded: bool,
    *,
    cached_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the evaluation context from kbio scores + request metadata.

    cached_stats contains pre-fetched historical data from Valkey:
      user_stats   — account_age_days, sessions_last_24h, known_countries, etc.
      device_stats — age_days, session_count, user_count, etc.
      network_stats — ip_sessions_1h, ip_users_1h, is_residential_proxy, etc.
    These replace the zero/empty auth_state defaults with real values.
    """
    auth_state = kbio_data.get("auth_state", {})
    drift_trend = kbio_data.get("drift_trend", {})
    scores = kbio_data.get("scores", {})
    metadata = request.get("metadata", {})

    _cs = cached_stats or {}
    _usr = _cs.get("user_stats") or {}
    _dev = _cs.get("device_stats") or {}
    _net = _cs.get("network_stats") or {}

    return {
        # --- Backward-compat top-level fields ---
        "behavioral_drift": kbio_data.get("drift_score", -1.0),
        "device_drift": kbio_data.get("device_drift", -1.0),
        "network_drift": kbio_data.get("network_drift", -1.0),
        "credential_drift": kbio_data.get("credential_drift"),
        "bot_score": kbio_data.get("bot_score", 0.0),
        "composite_score": kbio_data.get("composite_score", -1.0),
        "confidence": kbio_data.get("confidence", 0.0),
        "baseline_quality": auth_state.get("baseline_quality", "insufficient"),
        "baseline_age_days": auth_state.get("baseline_age_days", 0),
        "automation_detected": kbio_data.get("bot_score", 0.0) > 0.7,
        "headless_detected": metadata.get("is_headless", False),
        "signal_scores": kbio_data.get("signal_scores", {}),
        "drift_trend": drift_trend,
        # --- All 22 scores ---
        "scores": {
            "behavioral_drift": scores.get("behavioral_drift", kbio_data.get("drift_score", -1.0)),
            "credential_drift": scores.get("credential_drift", kbio_data.get("credential_drift")),
            "identity_confidence": scores.get("identity_confidence", 0.0),
            "familiarity_score": scores.get("familiarity_score", -1.0),
            "cognitive_load": scores.get("cognitive_load", -1.0),
            "session_anomaly": scores.get("session_anomaly", -1.0),
            "velocity_anomaly": scores.get("velocity_anomaly", 0.0),
            "takeover_probability": scores.get("takeover_probability", 0.0),
            "pattern_break": scores.get("pattern_break", 0.0),
            "consistency_score": scores.get("consistency_score", 0.5),
            "bot_score": scores.get("bot_score", kbio_data.get("bot_score", 0.0)),
            "replay_score": scores.get("replay_score", 0.0),
            "automation_score": scores.get("automation_score", 0.0),
            "population_anomaly": scores.get("population_anomaly", 0.0),
            "coercion_score": scores.get("coercion_score", 0.0),
            "impersonation_score": scores.get("impersonation_score", 0.0),
            "session_trust": scores.get("session_trust", 0.5),
            "user_trust": scores.get("user_trust", 0.5),
            "device_trust": scores.get("device_trust", 0.3),
            "confidence": scores.get("confidence", kbio_data.get("confidence", 0.0)),
            "signal_richness": scores.get("signal_richness", 0.0),
            "profile_maturity": scores.get("profile_maturity", 0.0),
        },
        # --- Modality drifts ---
        "modality_drift": kbio_data.get("modality_drift", {
            "keystroke": -1.0,
            "pointer": -1.0,
            "touch": -1.0,
            "sensor": -1.0,
        }),
        # --- Device (pre-fetched stats take precedence over auth_state zeros) ---
        "device": {
            "uuid": request.get("device_uuid"),
            "is_new": (
                not auth_state.get("device_known", True)
                or _dev.get("session_count", 0) < 2
            ),
            "is_trusted": (
                auth_state.get("device_known", False)
                or _dev.get("is_trusted", False)
            ),
            "platform": metadata.get("platform", _dev.get("platform", "web")),
            "fingerprint_drift": (
                kbio_data.get("device_drift")
                if kbio_data.get("device_drift", -1.0) >= 0
                else _dev.get("fingerprint_drift", 0.0)
            ),
            "age_days": _dev.get("age_days", auth_state.get("device_age_days", 0)),
            "session_count": _dev.get(
                "session_count", auth_state.get("device_session_count", 0)
            ),
            "sessions_last_24h": _dev.get("sessions_last_24h", 0),
            "users_count": _dev.get("user_count", auth_state.get("device_users_count", 1)),
            "is_multi_user": _dev.get("user_count", 1) > 1,
            # SDK metadata fields
            "is_mobile": metadata.get("is_mobile", False),
            "is_emulator": (
                metadata.get("is_emulator", False) or _dev.get("is_emulator", False)
            ),
            "is_headless": metadata.get("is_headless", False),
            "webdriver_present": metadata.get("webdriver_present", False),
            "automation_artifacts": metadata.get("automation_artifacts", False),
            "cdp_detected": metadata.get("cdp_detected", False),
            "proxy_overridden": metadata.get("proxy_overridden", False),
            "browser_name": metadata.get("browser_name", ""),
            "os_name": metadata.get("os_name", ""),
            "timezone_offset_minutes": metadata.get("timezone_offset_minutes", 0),
            "language": metadata.get("language", ""),
            "plugins_count": metadata.get("plugins_count", -1),
            "screen_width": metadata.get("screen_width", 0),
            "screen_height": metadata.get("screen_height", 0),
            "canvas_anomaly": metadata.get("canvas_anomaly", False),
            "webgl_anomaly": metadata.get("webgl_anomaly", False),
            "rooted_jailbroken": metadata.get("rooted_jailbroken", False),
        },
        # --- Network (pre-fetched reputation + velocity from Valkey INCR) ---
        "network": {
            "ip_address": metadata.get("ip_address"),
            "country": metadata.get("country", _net.get("country", "")),
            "city": metadata.get("city", _net.get("city", "")),
            # SDK flags take precedence; fall back to Valkey reputation data
            "is_vpn": metadata.get("is_vpn", False) or _net.get("is_vpn", False),
            "is_tor": metadata.get("is_tor", False) or _net.get("is_tor", False),
            "is_datacenter": (
                metadata.get("is_datacenter", False) or _net.get("is_datacenter", False)
            ),
            "is_proxy": (
                metadata.get("is_proxy", False) or _net.get("is_proxy", False)
            ),
            "is_residential_proxy": (
                metadata.get("is_residential_proxy", False)
                or _net.get("is_residential_proxy", False)
            ),
            "asn": metadata.get("asn", _net.get("asn", "")),
            "ip_trusted": auth_state.get("ip_trusted", False),
            # Real-time Valkey INCR sliding-window counters (never stale)
            "ip_sessions_1h": _net.get("ip_sessions_1h", 0),
            "ip_session_count_24h": _net.get(
                "ip_sessions_24h", auth_state.get("ip_session_count_24h", 0)
            ),
            "ip_user_count_24h": _net.get(
                "ip_users_1h", auth_state.get("ip_user_count_24h", 0)
            ),
            "ip_reputation_score": _net.get(
                "ip_reputation_score", metadata.get("threat_score", 0.0)
            ),
            "threat_score": metadata.get(
                "threat_score", _net.get("ip_reputation_score", 0.0)
            ),
            # Derived from pre-fetched user history
            "known_countries": _usr.get("known_countries", []),
            "last_session_country": _usr.get("last_session_country", ""),
            "is_new_country": (
                bool(metadata.get("country"))
                and bool(_usr.get("known_countries"))
                and metadata.get("country") not in _usr.get("known_countries", [])
            ),
            "impossible_travel": auth_state.get("impossible_travel", False),
            "travel_speed_kmh": auth_state.get("travel_speed_kmh", 0),
        },
        # --- User (pre-fetched historical stats replace auth_state zeros) ---
        "user": {
            "total_sessions": _usr.get(
                "total_sessions", auth_state.get("total_sessions", 0)
            ),
            "known_countries": _usr.get(
                "known_countries", auth_state.get("known_countries", [])
            ),
            "account_age_days": _usr.get(
                "account_age_days", auth_state.get("account_age_days", 0)
            ),
            "total_devices": _usr.get(
                "total_devices", auth_state.get("total_devices", 0)
            ),
            "sessions_last_24h": _usr.get(
                "sessions_last_24h", auth_state.get("sessions_last_24h", 0)
            ),
            "sessions_last_7d": auth_state.get("sessions_last_7d", 0),
            "days_since_last_session": _usr.get(
                "days_since_last_session", auth_state.get("days_since_last_session", 0)
            ),
            "typical_hours": _usr.get(
                "typical_hours", auth_state.get("typical_hours", [])
            ),
            "failed_challenges_last_24h": _usr.get(
                "failed_challenges_24h", auth_state.get("failed_challenges_last_24h", 0)
            ),
            "trust_level": _usr.get("trust_level", "trusted"),
            "previously_blocked": auth_state.get("previously_blocked", False),
        },
        # --- Session ---
        "session": {
            "duration_seconds": metadata.get("session_duration_seconds", 0),
            "page_count": metadata.get("page_count", 0),
            "pulse_count": metadata.get("pulse_count", 0),
            "local_hour": metadata.get("local_hour"),
            "day_of_week": metadata.get("day_of_week"),
            "event_type": request.get("event_type", "behavioral"),
            "is_sensitive_page": metadata.get("is_sensitive_page", False),
            "credential_paste": metadata.get("credential_paste", False),
            "credential_autofill": metadata.get("credential_autofill", False),
            "credential_ms_per_char": metadata.get("credential_ms_per_char"),
            "credential_max_pause_ms": metadata.get("credential_max_pause_ms"),
            "credential_backspace_ratio": metadata.get("credential_backspace_ratio"),
            "credential_retype_count": metadata.get("credential_retype_count"),
            "min_iki_ms": metadata.get("min_iki_ms"),
            "iki_cv": metadata.get("iki_cv"),
            "dwell_cv": metadata.get("dwell_cv"),
            "pointer_curvature": metadata.get("pointer_curvature"),
            "batch_timing_cv": metadata.get("batch_timing_cv"),
            "has_pointer_only": metadata.get("has_pointer_only", False),
            "max_idle_seconds": metadata.get("max_idle_seconds"),
            "pre_action_pause_ms": metadata.get("pre_action_pause_ms"),
            "retype_count": metadata.get("retype_count"),
            "rhythm_break_count": metadata.get("rhythm_break_count"),
            "referrer_is_new": metadata.get("referrer_is_new", False),
        },
        # --- Meta ---
        "event_type": request.get("event_type", "behavioral"),
        "session_duration_seconds": metadata.get("session_duration_seconds", 0),
        "page_count": metadata.get("page_count", 0),
        "pulse_count": metadata.get("pulse_count", 0),
        "degraded": degraded,
    }


async def _load_signal_selections(org_id: str, valkey: Any) -> list[dict]:
    """Load enabled signal selections for an org. Cached in Valkey."""
    cache_key = f"kp:signalsel:{org_id}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            '''SELECT signal_code, config_overrides
               FROM "11_kprotect".v_signal_selections
               WHERE org_id = $1 AND is_active = TRUE AND deleted_at IS NULL''',
            org_id,
        )
        selections = [dict(r) for r in rows]

    await valkey.set(cache_key, json.dumps(selections, default=str), ex=300)
    return selections


async def _load_policy_set(
    org_id: str,
    policy_set_code: str | None,
    valkey: Any,
) -> tuple[list[dict[str, Any]], str, str | None]:
    """Load the active policy set for an org.

    Returns (policies, evaluation_mode, policy_set_id).
    """
    cache_key = f"kp:policyset:{org_id}:{policy_set_code or 'default'}"
    cached = await valkey.get(cache_key)
    if cached:
        data = json.loads(cached)
        return data["policies"], data["mode"], data.get("policy_set_id")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        # Find the policy set
        if policy_set_code:
            row = await conn.fetchrow(
                '''SELECT id, evaluation_mode FROM "11_kprotect".v_policy_sets
                   WHERE org_id = $1 AND code = $2 AND is_active = TRUE AND is_deleted = FALSE''',
                org_id, policy_set_code,
            )
        else:
            row = await conn.fetchrow(
                '''SELECT id, evaluation_mode FROM "11_kprotect".v_policy_sets
                   WHERE org_id = $1 AND is_default = TRUE AND is_active = TRUE AND is_deleted = FALSE''',
                org_id,
            )

        if not row:
            return [], "short_circuit", None

        policy_set_id = row["id"]
        eval_mode = row["evaluation_mode"] or "short_circuit"

        # Load the policy selections in this set, ordered by sort_order
        selections = await conn.fetch(
            '''SELECT ps.predefined_policy_code, ps.config_overrides,
                      ps.threat_type_code, lnk.sort_order
               FROM "11_kprotect"."40_lnk_policy_set_selections" lnk
               JOIN "11_kprotect".v_policy_selections ps ON ps.id = lnk.policy_selection_id
               WHERE lnk.policy_set_id = $1 AND ps.is_active = TRUE AND ps.is_deleted = FALSE
               ORDER BY lnk.sort_order ASC, ps.priority ASC''',
            policy_set_id,
        )

        if not selections:
            return [], eval_mode, policy_set_id

        # Load the actual policy conditions from kbio catalog (via Valkey cache)
        catalog_key = "kp:library"
        catalog_raw = await valkey.get(catalog_key)
        if catalog_raw:
            catalog = json.loads(catalog_raw)
        else:
            catalog = await _kbio.get_policy_catalog()
            if catalog:
                await valkey.set(catalog_key, json.dumps(catalog, default=str), ex=600)

        # Build policy lookup by code
        catalog_by_code = {p.get("code"): p for p in catalog}

        policies = []
        for sel in selections:
            code = sel["predefined_policy_code"]
            policy_def = catalog_by_code.get(code, {})
            conditions = policy_def.get("conditions")
            if isinstance(conditions, str):
                conditions = json.loads(conditions)
            if not conditions:
                continue

            config_overrides = sel.get("config_overrides")
            if isinstance(config_overrides, str):
                config_overrides = json.loads(config_overrides)

            policies.append({
                "code": code,
                "conditions": conditions,
                "config_overrides": config_overrides,
                "threat_type_code": sel.get("threat_type_code"),
            })

    # Cache for 5 min
    cache_data = {"policies": policies, "mode": eval_mode, "policy_set_id": policy_set_id}
    await valkey.set(cache_key, json.dumps(cache_data, default=str), ex=300)

    return policies, eval_mode, policy_set_id


async def _batch_fetch_stats(
    user_hash: str,
    device_uuid: str,
    ip_address: str,
    valkey: Any,
) -> dict[str, Any]:
    """Fetch all three stat blobs from Valkey in a single pipeline round-trip.

    If a key is not cached, that stat dict will be empty ({}). kbio will have
    already warmed these keys via its own _stats service on the previous request.
    For first-ever sessions, empty dicts are fine — signals default gracefully.

    Using a Valkey pipeline means all three GETs happen in one network round-trip
    instead of three sequential round-trips (saves ~1-2ms at p99).

    Returns:
        {
            "user_stats": {...} | {},
            "device_stats": {...} | {},
            "network_stats": {...} | {},
        }
    """
    user_key = f"kbio:stats:user:{user_hash}" if user_hash else None
    device_key = f"kbio:stats:device:{device_uuid}" if device_uuid else None
    net_key = f"kbio:stats:net:{ip_address}" if ip_address else None

    # Build pipeline with only the keys that exist
    keys = [k for k in (user_key, device_key, net_key) if k]
    if not keys:
        return {"user_stats": {}, "device_stats": {}, "network_stats": {}}

    try:
        pipe = valkey.pipeline()
        for k in keys:
            pipe.get(k)
        results = await pipe.execute()
    except Exception:  # noqa: BLE001
        results = [None] * len(keys)

    # Map back to the three blobs
    idx = 0
    user_raw = results[idx] if user_key and idx < len(results) else None
    idx += 1 if user_key else 0
    device_raw = results[idx] if device_key and idx < len(results) else None
    idx += 1 if device_key else 0
    net_raw = results[idx] if net_key and idx < len(results) else None

    return {
        "user_stats": json.loads(user_raw) if user_raw else {},
        "device_stats": json.loads(device_raw) if device_raw else {},
        "network_stats": json.loads(net_raw) if net_raw else {},
    }


def _build_response(
    *,
    action: str,
    results: list[dict[str, Any]],
    ctx: dict[str, Any],
    kbio_data: dict[str, Any],
    degraded: bool,
    start: float,
    kbio_latency: float,
    policy_latency: float,
    policy_set_id: str | None = None,
    decision_id: str | None = None,
) -> dict[str, Any]:
    """Build the evaluate response."""
    total_latency = round((time.perf_counter() - start) * 1000, 2)
    triggered = [r for r in results if r.get("action") != "allow"]

    return {
        "decision_id": decision_id or str(uuid.uuid4()),
        "action": action if not degraded else "allow",
        "reason": triggered[0]["reason"] if triggered else None,
        "degraded": degraded,
        "policies_evaluated": len(results),
        "policies_triggered": len(triggered),
        "latency_ms": {
            "total": total_latency,
            "kbio": kbio_latency,
            "policy_execution": policy_latency,
        },
        "details": results,
        "context_summary": {
            "behavioral_drift": ctx.get("behavioral_drift", -1.0),
            "device_known": ctx.get("device", {}).get("is_trusted", False),
            "bot_score": ctx.get("bot_score", 0.0),
            "baseline_quality": ctx.get("baseline_quality", "insufficient"),
            "confidence": ctx.get("confidence", 0.0),
        },
        # Pass through kbio scores
        "drift_score": kbio_data.get("drift_score", -1.0),
        "confidence": kbio_data.get("confidence", 0.0),
        "bot_score": kbio_data.get("bot_score", 0.0),
        "signal_scores": kbio_data.get("signal_scores", {}),
        "auth_state": kbio_data.get("auth_state", {}),
        "drift_trend": kbio_data.get("drift_trend", {}),
        "alerts": kbio_data.get("alerts", []),
        # Signal and threat summaries
        "signals_summary": {
            "total_evaluated": len(kbio_data.get("signals", {}) or {}),
            "elevated_count": sum(
                1 for s in (kbio_data.get("signals", {}) or {}).values()
                if (s.get("value") is True)
                or (isinstance(s.get("value"), (int, float)) and s["value"] > 0.5)
            ),
            "elevated": [
                code for code, s in (kbio_data.get("signals", {}) or {}).items()
                if (s.get("value") is True)
                or (isinstance(s.get("value"), (int, float)) and s["value"] > 0.5)
            ],
        },
        "threats_detected": kbio_data.get("threats_detected", []),
    }


def _schedule_decision_persist(**kwargs: Any) -> None:
    """Schedule async write of decision event. Fire-and-forget."""
    import logging
    logging.getLogger("kprotect.evaluate").info(
        "Decision: action=%s session=%s policies=%d triggered=%d latency=%.1fms",
        kwargs.get("action"), kwargs.get("session_id"),
        len(kwargs.get("results", [])),
        sum(1 for r in kwargs.get("results", []) if r.get("action") != "allow"),
        kwargs.get("total_latency", 0),
    )
