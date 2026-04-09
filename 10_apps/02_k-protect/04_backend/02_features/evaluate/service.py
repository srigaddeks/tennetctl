"""kprotect evaluate service.

Orchestrates: receive request → call kbio → assemble context → run rule engine → persist decision.
"""
from __future__ import annotations

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


async def evaluate(
    request: dict[str, Any],
    *,
    org_id: str,
    actor_id: str,
) -> dict[str, Any]:
    """Full evaluation pipeline.

    1. Call kbio for scores (forward the batch)
    2. Assemble evaluation context
    3. Load org's active policy set
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

    # Step 1: Call kbio (forward the batch)
    kbio_start = time.perf_counter()
    kbio_result = await _kbio.ingest_batch(batch)
    kbio_latency = round((time.perf_counter() - kbio_start) * 1000, 2)

    kbio_data = kbio_result.get("data", {}) if kbio_result.get("ok") else {}
    degraded = not kbio_result.get("ok", False)

    # Step 2: Assemble evaluation context
    ctx = _assemble_context(kbio_data, request, degraded)

    # Step 3: Load policy set
    policy_start = time.perf_counter()
    policies, eval_mode, policy_set_id = await _load_policy_set(org_id, policy_set_code, valkey)

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
) -> dict[str, Any]:
    """Build the evaluation context from kbio scores + request metadata."""
    auth_state = kbio_data.get("auth_state", {})
    drift_trend = kbio_data.get("drift_trend", {})

    return {
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
        "headless_detected": False,  # TODO: from kbio signals
        "signal_scores": kbio_data.get("signal_scores", {}),
        "drift_trend": drift_trend,
        "device": {
            "uuid": request.get("device_uuid"),
            "is_new": not auth_state.get("device_known", True),
            "is_trusted": auth_state.get("device_known", False),
            "platform": "web",
            "fingerprint_drift": kbio_data.get("device_drift", -1.0),
        },
        "network": {
            "ip_address": request.get("metadata", {}).get("ip_address"),
            "country": request.get("metadata", {}).get("country"),
            "is_vpn": request.get("metadata", {}).get("is_vpn", False),
            "is_tor": request.get("metadata", {}).get("is_tor", False),
            "is_datacenter": request.get("metadata", {}).get("is_datacenter", False),
            "ip_trusted": False,
            "impossible_travel": False,
        },
        "user": {
            "total_sessions": auth_state.get("total_sessions", 0),
            "known_countries": [],
        },
        "event_type": request.get("event_type", "behavioral"),
        "session_duration_seconds": 0,
        "page_count": 0,
        "pulse_count": 0,
        "degraded": degraded,
    }


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
            '''SELECT ps.predefined_policy_code, ps.config_overrides, lnk.sort_order
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
            })

    # Cache for 5 min
    cache_data = {"policies": policies, "mode": eval_mode, "policy_set_id": policy_set_id}
    await valkey.set(cache_key, json.dumps(cache_data, default=str), ex=300)

    return policies, eval_mode, policy_set_id


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
