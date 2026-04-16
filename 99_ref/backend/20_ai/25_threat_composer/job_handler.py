"""
Job handler for threat_composer jobs.

Input JSON:
  signal_ids       — list of validated signal UUIDs to compose from
  org_id           — org to create threat types in
  workspace_id     — workspace to create threat types in
  max_threat_types — max number of threat types to generate (default 100)

Output:
  Creates threat type records via ThreatTypeService
  Writes ai_generated=true EAV on each created threat type
  Reports count of created vs rejected threat types

LangFuse tracing:
  - One root trace per job
  - One generation span for the composition LLM call
  - One event per proposal (validated / rejected / created)
  - Scored with: creation_rate, valid_tree_rate
"""

from __future__ import annotations

import json
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.threat_composer.job_handler")

_llm_utils_mod = import_module("backend.20_ai._llm_utils")
llm_complete = _llm_utils_mod.llm_complete
resolve_llm_config = _llm_utils_mod.resolve_llm_config
parse_json_array = _llm_utils_mod.parse_json_array

_SIGNALS = '"15_sandbox"."22_fct_signals"'
_SIGNAL_PROPS = '"15_sandbox"."45_dtl_signal_properties"'
_THREAT_PROPS = '"15_sandbox"."46_dtl_threat_type_properties"'


class _PoolAdapter:
    def __init__(self, pool):
        self._pool = pool

    async def acquire(self):
        return self._pool.acquire()


def _normalize_connector_type_code(raw: str | None) -> str:
    if not raw:
        return "unknown"
    return raw.split(",")[0].strip().lower() or "unknown"


def _validate_expression_tree(tree: dict) -> bool:
    """Validate expression tree structure matches ThreatTypeService expectations."""
    if not isinstance(tree, dict):
        return False
    if "signal_code" in tree:
        return "expected_result" in tree
    if "operator" in tree:
        operator = tree["operator"]
        conditions = tree.get("conditions", [])
        if operator == "NOT":
            if len(conditions) != 1:
                return False
            return _validate_expression_tree(conditions[0])
        elif operator in ("AND", "OR"):
            if len(conditions) < 2:
                return False
            return all(_validate_expression_tree(c) for c in conditions)
    return False


def _fix_not_operator(tree: dict) -> dict:
    """Fix NOT nodes with wrong child count — keep only first child."""
    if not isinstance(tree, dict):
        return tree
    if "operator" in tree:
        operator = tree["operator"]
        conditions = [_fix_not_operator(c) for c in tree.get("conditions", [])]
        if operator == "NOT" and len(conditions) != 1:
            conditions = conditions[:1] if conditions else [{"signal_code": "unknown", "expected_result": "fail"}]
        return {"operator": operator, "conditions": conditions}
    return tree


def _collect_signal_codes(tree: dict) -> set[str]:
    if not isinstance(tree, dict):
        return set()
    if "signal_code" in tree:
        signal_code = tree.get("signal_code")
        return {signal_code} if isinstance(signal_code, str) and signal_code else set()
    codes: set[str] = set()
    for condition in tree.get("conditions", []):
        codes.update(_collect_signal_codes(condition))
    return codes


def _infer_connector_type_code(tree: dict, signal_catalog: list[dict]) -> str:
    signal_lookup = {
        entry["signal_code"]: _normalize_connector_type_code(entry.get("connector_type_code"))
        for entry in signal_catalog
    }
    connectors = {
        signal_lookup[signal_code]
        for signal_code in _collect_signal_codes(tree)
        if signal_lookup.get(signal_code)
    }
    if len(connectors) == 1:
        return next(iter(connectors))
    return "unknown"


async def handle_threat_composer_job(job, pool, settings) -> None:
    inp = job.input_json
    signal_ids = inp.get("signal_ids", [])
    org_id = getattr(job, "org_id", None) or inp.get("org_id")
    workspace_id = getattr(job, "workspace_id", None) or inp.get("workspace_id")
    tenant_key = getattr(job, "tenant_key", None) or inp.get("tenant_key", "")
    user_id = getattr(job, "user_id", None) or inp.get("user_id")
    max_threat_types = inp.get("max_threat_types", 100)
    auto_build_library = inp.get("auto_build_library", True)

    _logger.info(
        "threat_composer.starting",
        extra={"signal_count": len(signal_ids), "max_threat_types": max_threat_types},
    )

    # Init LangFuse tracer
    _tracer_mod = import_module("backend.20_ai.14_llm_providers.langfuse_tracer")
    tracer = _tracer_mod.LangFuseTracer.from_settings(settings)
    trace = tracer.trace(
        name="threat_composer",
        job_id=str(job.id),
        user_id=str(user_id) if user_id else None,
        metadata={
            "signal_count": len(signal_ids),
            "max_threat_types": max_threat_types,
            "org_id": str(org_id) if org_id else None,
        },
        tags=["threat_composer"],
    )

    # Load signal catalog
    signal_catalog = await _load_signal_catalog(pool, signal_ids, tenant_key)
    if not signal_catalog:
        tracer.event(trace, name="no_signals", level="ERROR",
                     metadata={"signal_ids": signal_ids})
        tracer.flush()
        raise ValueError("No valid signals found to compose threat types from")

    tracer.event(trace, name="catalog_loaded",
                 metadata={"catalog_size": len(signal_catalog),
                           "connectors": list({s["connector_type_code"] for s in signal_catalog})})

    # Resolve LLM config
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    _prompts_mod = import_module("backend.20_ai.25_threat_composer.prompts")

    config_repo = _config_repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo,
        database_pool=pool,
        settings=settings,
    )
    llm_config = await resolver.resolve(agent_type_code="threat_composer", org_id=None)
    provider_url, api_key, model = resolve_llm_config(llm_config, settings)

    # Generate threat types
    system = _prompts_mod.THREAT_COMPOSER_SYSTEM_PROMPT.format(
        signal_catalog=json.dumps(signal_catalog, indent=2),
        max_threat_types=max_threat_types,
    )
    raw = await llm_complete(
        provider_url=provider_url,
        api_key=api_key,
        model=model,
        system=system,
        user="Compose threat types now.",
        max_tokens=8000,
        temperature=1.0,
        timeout=180.0,
        tracer=tracer,
        trace=trace,
        generation_name="compose_threat_types",
        generation_metadata={"signal_count": len(signal_catalog), "max_output": max_threat_types},
    )

    try:
        proposals = parse_json_array(raw)
    except Exception as exc:
        tracer.event(trace, name="parse_failed", level="ERROR",
                     metadata={"error": str(exc)[:500]})
        tracer.flush()
        raise ValueError(f"Failed to parse threat type proposals: {exc}") from exc

    _logger.info("threat_composer.proposals_parsed", extra={"count": len(proposals)})
    tracer.event(trace, name="proposals_parsed", metadata={"count": len(proposals)})

    # Create threat types
    created = 0
    rejected = 0
    invalid_tree = 0
    created_threat_ids = []

    for proposal in proposals[:max_threat_types]:
        threat_code = proposal.get("threat_type_code", "unknown")
        try:
            # Fix + validate expression tree
            tree = _fix_not_operator(proposal.get("expression_tree", {}))
            proposal["expression_tree"] = tree

            if not _validate_expression_tree(tree):
                _logger.warning(
                    "threat_composer.invalid_tree",
                    extra={"code": threat_code},
                )
                tracer.event(trace, name="invalid_tree", level="WARNING",
                             metadata={"code": threat_code, "tree_keys": list(tree.keys())})
                invalid_tree += 1
                rejected += 1
                continue

            threat_id = await _create_threat_type(
                pool=pool,
                tenant_key=tenant_key,
                user_id=user_id,
                org_id=org_id,
                workspace_id=workspace_id,
                proposal=proposal,
                connector_type_code=_infer_connector_type_code(tree, signal_catalog),
            )
            created_threat_ids.append(threat_id)
            created += 1
            tracer.event(trace, name="threat_type_created",
                         metadata={"code": threat_code, "severity": proposal.get("severity_code", "medium")})

        except Exception as exc:
            _logger.warning(
                "threat_composer.create_failed",
                extra={"code": threat_code, "error": str(exc)[:200]},
            )
            tracer.event(trace, name="create_failed", level="ERROR",
                         metadata={"code": threat_code, "error": str(exc)[:300]})
            rejected += 1

    creation_rate = created / max(len(proposals[:max_threat_types]), 1)
    valid_tree_rate = (len(proposals[:max_threat_types]) - invalid_tree) / max(len(proposals[:max_threat_types]), 1)

    tracer.score(trace, name="creation_rate", value=creation_rate,
                 comment=f"{created}/{len(proposals[:max_threat_types])} created")
    tracer.score(trace, name="valid_tree_rate", value=valid_tree_rate,
                 comment=f"invalid_tree={invalid_tree}")

    _logger.info(
        "threat_composer.complete",
        extra={"threats_created": created, "threats_rejected": rejected},
    )
    tracer.event(trace, name="composition_complete",
                 metadata={"created": created, "rejected": rejected, "invalid_tree": invalid_tree})

    # Auto-enqueue library_builder if requested
    if auto_build_library and created_threat_ids:
        import uuid as _uuid
        _JOBS = '"20_ai"."45_fct_job_queue"'
        lib_job_id = str(_uuid.uuid4())
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {_JOBS} (
                    id, tenant_key, user_id, org_id, workspace_id,
                    agent_type_code,
                    job_type, status_code, priority_code, scheduled_at,
                    input_json, created_at, updated_at
                ) VALUES (
                    $1::uuid, $2, $3::uuid, $4::uuid, $5::uuid,
                    'library_builder',
                    'library_builder', 'queued', 'normal', NOW(),
                    $6::jsonb, NOW(), NOW()
                )
                """,
                lib_job_id, tenant_key, user_id,
                org_id, workspace_id,
                json.dumps({
                    "threat_type_ids": created_threat_ids,
                    "org_id": str(org_id) if org_id else None,
                    "workspace_id": str(workspace_id) if workspace_id else None,
                }),
            )
        _logger.info(
            "threat_composer.enqueued_library_builder",
            extra={"threat_count": len(created_threat_ids), "lib_job_id": lib_job_id},
        )
        tracer.event(trace, name="enqueued_library_builder",
                     metadata={"lib_job_id": lib_job_id, "threat_count": len(created_threat_ids)})

    tracer.flush()


async def _load_signal_catalog(pool, signal_ids: list, tenant_key: str) -> list[dict]:
    """Load signal metadata for the catalog."""
    catalog = []
    for signal_id in signal_ids:
        try:
            async with pool.acquire() as conn:
                sig = await conn.fetchrow(
                    f"""
                    SELECT s.id::text, s.signal_code,
                           p_name.property_value AS name,
                           p_desc.property_value AS description,
                           p_spec.property_value AS signal_spec,
                           p_conn.property_value AS connector_type_code
                    FROM {_SIGNALS} s
                    LEFT JOIN "15_sandbox"."45_dtl_signal_properties" p_name
                        ON p_name.signal_id = s.id AND p_name.property_key = 'name'
                    LEFT JOIN "15_sandbox"."45_dtl_signal_properties" p_desc
                        ON p_desc.signal_id = s.id AND p_desc.property_key = 'description'
                    LEFT JOIN "15_sandbox"."45_dtl_signal_properties" p_spec
                        ON p_spec.signal_id = s.id AND p_spec.property_key = 'signal_spec'
                    LEFT JOIN "15_sandbox"."45_dtl_signal_properties" p_conn
                        ON p_conn.signal_id = s.id AND p_conn.property_key = 'connector_types'
                    WHERE s.id = $1::uuid AND s.tenant_key = $2
                    """,
                    signal_id, tenant_key,
                )
            if not sig:
                continue

            spec = {}
            if sig["signal_spec"]:
                try:
                    spec = json.loads(sig["signal_spec"])
                except Exception:
                    pass

            catalog.append({
                "signal_code": sig["signal_code"],
                "name": sig["name"] or sig["signal_code"],
                "description": sig["description"] or "",
                "connector_type_code": _normalize_connector_type_code(sig["connector_type_code"]),
                "intent": spec.get("intent", ""),
                "ssf_event_type": spec.get("ssf_mapping", {}).get("event_type", ""),
            })
        except Exception as exc:
            _logger.warning("threat_composer.signal_load_failed: %s", exc)

    return catalog


async def _create_threat_type(
    pool,
    *,
    tenant_key: str,
    user_id: str,
    org_id: str,
    workspace_id: str,
    proposal: dict,
    connector_type_code: str,
) -> str:
    import uuid
    threat_id = str(uuid.uuid4())
    threat_code = proposal.get("threat_code") or proposal.get("threat_type_code", f"threat_{threat_id[:8]}")
    name = proposal.get("name", threat_code)
    description = proposal.get("description", "")
    severity_code = proposal.get("severity_code", "medium")
    expression_tree = proposal.get("expression_tree", {})

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO "15_sandbox"."23_fct_threat_types" (
                id, tenant_key, org_id, workspace_id,
                threat_code, version_number,
                severity_code, expression_tree,
                is_active, is_deleted,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            ) VALUES (
                $1::uuid, $2, $3::uuid, $4::uuid,
                $5, 1,
                $6, $7::jsonb,
                true, false,
                NOW(), NOW(), $8::uuid, $8::uuid, NULL, NULL
            )
            """,
            threat_id, tenant_key, org_id, workspace_id,
            threat_code, severity_code,
            json.dumps(expression_tree),
            user_id,
        )

        for key, val in [
            ("name", name),
            ("description", description),
            ("ai_generated", "true"),
            ("connector_type_code", connector_type_code or "unknown"),
        ]:
            await conn.execute(
                """
                INSERT INTO "15_sandbox"."46_dtl_threat_type_properties" (threat_type_id, property_key, property_value)
                VALUES ($1::uuid, $2, $3)
                ON CONFLICT (threat_type_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                """,
                threat_id, key, val,
            )

    return threat_id
