"""
Job handler for signal_test_dataset_gen jobs.

Input JSON:
  signal_id         — UUID of the signal to generate tests for
  session_id        — UUID of the spec session
  source_dataset_id — UUID of the real dataset to use as schema source
  connector_type_code
  spec              — full signal spec dict

Output:
  Creates a new dataset with dataset_source_code='ai_generated_tests'
  Writes test_bundle_json to dataset EAV
  Writes test_dataset_id to signal EAV
  Auto-enqueues signal_codegen job
"""

from __future__ import annotations

import json
import uuid
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.test_dataset_gen.job_handler")

_llm_utils_mod = import_module("backend.20_ai._llm_utils")
llm_complete = _llm_utils_mod.llm_complete
resolve_llm_config = _llm_utils_mod.resolve_llm_config
strip_fences = _llm_utils_mod.strip_fences

_JOBS = '"20_ai"."45_fct_job_queue"'
_DATASETS = '"15_sandbox"."21_fct_datasets"'
_DATASET_PROPS = '"15_sandbox"."42_dtl_dataset_properties"'
_DATASET_RECORDS = '"15_sandbox"."43_dtl_dataset_records"'
_SIGNAL_PROPS = '"15_sandbox"."45_dtl_signal_properties"'


async def handle_test_dataset_gen_job(job, pool, settings) -> None:
    inp = job.input_json
    signal_id = inp.get("signal_id")
    session_id = inp.get("session_id")
    source_dataset_id = inp.get("source_dataset_id")
    connector_type_code = inp.get("connector_type_code", "")
    spec = inp.get("spec", {})
    tenant_key = getattr(job, "tenant_key", None) or inp.get("tenant_key", "")
    user_id = getattr(job, "user_id", None) or inp.get("user_id")
    org_id = getattr(job, "org_id", None) or inp.get("org_id")
    workspace_id = getattr(job, "workspace_id", None) or inp.get("workspace_id")
    auto_compose_threats = inp.get("auto_compose_threats", True)
    auto_build_library = inp.get("auto_build_library", True)

    _logger.info(
        "test_dataset_gen.starting",
        extra={"signal_id": signal_id, "source_dataset_id": source_dataset_id},
    )

    _logger.info("test_dataset_gen.pool_type: %s", type(pool).__name__)

    # Extract rich schema from source dataset records
    rich_schema = {}
    if source_dataset_id:
        rich_schema = await _extract_rich_schema(pool, source_dataset_id)
        _logger.info("test_dataset_gen.schema_extracted: %d fields", len(rich_schema))

    if not rich_schema:
        _logger.warning("test_dataset_gen.no_schema", extra={"signal_id": signal_id})
        # Build minimal schema from spec fields_used
        for field in spec.get("dataset_fields_used", []):
            path = field.get("field_path", "")
            if path:
                rich_schema[path] = {
                    "type": field.get("type", "string"),
                    "example": field.get("example"),
                    "nullable": False,
                }

    # Resolve LLM config + run agent
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    _agent_mod = import_module("backend.20_ai.23_test_dataset_gen.agent")

    config_repo = _config_repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo,
        database_pool=pool,
        settings=settings,
    )
    llm_config = await resolver.resolve(agent_type_code="test_dataset_gen", org_id=None)

    _tracer_mod = import_module("backend.20_ai.14_llm_providers.langfuse_tracer")
    tracer = _tracer_mod.LangFuseTracer.from_settings(settings)

    agent = _agent_mod.TestDatasetAgent(llm_config=llm_config, settings=settings, tracer=tracer)

    test_cases = await agent.generate_test_bundle(
        spec=spec,
        rich_schema=rich_schema,
        num_cases=18,
        job_id=str(job.id),
    )

    # Create new AI test dataset
    test_dataset_id = str(uuid.uuid4())
    signal_code = spec.get("signal_code", "signal")
    dataset_code = f"ai-tests-{signal_code}-{test_dataset_id[:8]}"
    dataset_name = f"AI Tests — {signal_code}"

    async with pool.acquire() as conn:
        await conn.execute(
            f"""
            INSERT INTO {_DATASETS} (
                id, tenant_key, org_id, workspace_id,
                dataset_code, dataset_source_code, version_number,
                is_locked, is_active,
                created_at, updated_at
            ) VALUES (
                $1::uuid, $2, $3::uuid, $4::uuid,
                $5, 'ai_generated_tests', 1,
                false, true,
                NOW(), NOW()
            )
            """,
            test_dataset_id, tenant_key,
            org_id, workspace_id,
            dataset_code,
        )

        # Write dataset properties (name, metadata)
        for key, val in [
            ("name", dataset_name),
            ("is_ai_test_dataset", "true"),
            ("linked_signal_id", str(signal_id)),
            ("test_bundle_json", json.dumps(test_cases)),
        ]:
            await conn.execute(
                f"""
                INSERT INTO {_DATASET_PROPS} (id, dataset_id, property_key, property_value)
                VALUES (gen_random_uuid(), $1::uuid, $2, $3)
                ON CONFLICT (dataset_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                """,
                test_dataset_id, key, val,
            )

        # Write each test case as a dataset record
        for i, case in enumerate(test_cases):
            await conn.execute(
                f"""
                INSERT INTO {_DATASET_RECORDS} (id, dataset_id, record_seq, record_data, recorded_at)
                VALUES (gen_random_uuid(), $1::uuid, $2, $3::jsonb, NOW())
                """,
                test_dataset_id, i + 1, json.dumps(case),
            )

    # ── Verify test case expected_outputs against the signal spec ──────────
    provider_url, api_key, model = resolve_llm_config(llm_config, settings)
    _tracer_mod2 = import_module("backend.20_ai.14_llm_providers.langfuse_tracer")
    tracer2 = _tracer_mod2.LangFuseTracer.from_settings(settings)
    trace2 = tracer2.trace(
        name="test_case_verification",
        metadata={"signal_id": str(signal_id), "dataset_id": test_dataset_id},
        tags=["test_verifier"],
    )

    verified_cases = await _verify_test_cases(
        test_cases=test_cases,
        spec=spec,
        provider_url=provider_url,
        api_key=api_key,
        model=model,
        tracer=tracer2,
        trace=trace2,
    )

    # Update records with corrected expected_outputs
    corrections_applied = sum(1 for c in verified_cases if "_verification" in c)
    if corrections_applied > 0:
        _logger.info(
            "test_dataset_gen.verification_corrections",
            extra={"corrections": corrections_applied, "total": len(verified_cases)},
        )
        async with pool.acquire() as conn:
            for i, case in enumerate(verified_cases):
                await conn.execute(
                    f'UPDATE {_DATASET_RECORDS} SET record_data = $1::jsonb WHERE dataset_id = $2::uuid AND record_seq = $3',
                    json.dumps(case), test_dataset_id, i + 1,
                )

    tracer2.flush()

    async with pool.acquire() as conn:
        # Write test_dataset_id back to signal EAV
        await conn.execute(
            f"""
            INSERT INTO {_SIGNAL_PROPS} (id, signal_id, property_key, property_value)
            VALUES (gen_random_uuid(), $1::uuid, 'test_dataset_id', $2)
            ON CONFLICT (signal_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
            """,
            signal_id, str(test_dataset_id),
        )

        # Auto-enqueue signal_codegen job
        codegen_job_id = str(uuid.uuid4())
        await conn.execute(
            f"""
            INSERT INTO {_JOBS} (
                id, tenant_key, user_id, org_id, workspace_id,
                agent_type_code,
                job_type, status_code, priority_code, scheduled_at,
                input_json, created_at, updated_at
            ) VALUES (
                $1::uuid, $2, $3::uuid, $4::uuid, $5::uuid,
                'signal_codegen',
                'signal_codegen', 'queued', 'normal', NOW(),
                $6::jsonb, NOW(), NOW()
            )
            """,
            codegen_job_id, tenant_key, user_id,
            org_id, workspace_id,
            json.dumps({
                "signal_id": str(signal_id),
                "session_id": str(session_id) if session_id else None,
                "test_dataset_id": str(test_dataset_id),
                "spec": spec,
                "rich_schema": rich_schema,
                "auto_compose_threats": auto_compose_threats,
                "auto_build_library": auto_build_library,
            }),
        )

    _logger.info(
        "test_dataset_gen.complete",
        extra={
            "signal_id": signal_id,
            "test_dataset_id": test_dataset_id,
            "num_cases": len(test_cases),
            "codegen_job_id": codegen_job_id,
        },
    )


async def _extract_rich_schema(pool, dataset_id: str) -> dict:
    """Extract rich schema from real dataset records (not payloads table)."""
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT record_data
                FROM {_DATASET_RECORDS}
                WHERE dataset_id = $1::uuid
                ORDER BY record_seq
                LIMIT 5
                """,
                dataset_id,
            )
        records = []
        for r in rows:
            rd = r["record_data"]
            # Handle double-encoded JSON
            if isinstance(rd, str):
                try:
                    rd = json.loads(rd)
                except Exception:
                    rd = {}
            if isinstance(rd, str):
                try:
                    rd = json.loads(rd)
                except Exception:
                    rd = {}
            if isinstance(rd, dict):
                records.append(rd)

        if not records:
            return {}

        # Build schema from actual records
        schema: dict = {}
        for rec in records:
            for key, val in rec.items():
                if key.startswith("_"):
                    continue
                if key not in schema:
                    val_type = "string"
                    if isinstance(val, bool):
                        val_type = "boolean"
                    elif isinstance(val, int):
                        val_type = "integer"
                    elif isinstance(val, float):
                        val_type = "number"
                    schema[key] = {
                        "type": val_type,
                        "example": val,
                        "nullable": val is None,
                    }
        return schema
    except Exception as exc:
        _logger.warning("test_dataset_gen.schema_extraction_failed: %s", exc)
        return {}


_VERIFY_PROMPT = """You are a compliance signal test case verifier.

Given the signal specification and a test case input, verify if the expected output is correct.

Signal Spec:
{spec}

The evaluate() function checks a SINGLE JSON record and returns:
- "pass" = record is compliant, no issues found
- "fail" = record has critical compliance violations
- "warning" = record has minor issues but not critical violations

Test Case:
- Input: {input_json}
- Expected Result: {expected_result}
- Scenario: {scenario}
- Description: {description}

Is the expected result CORRECT for this input given the signal spec?

Rules for determining the correct result:
- "fail" = ANY critical check fails (public visibility, fork from untrusted source, etc.)
- "warning" = no critical failures but minor issues (empty description, slightly stale, etc.)
- "pass" = all checks pass, fully compliant

Respond with ONLY a JSON object:
{{"correct": true/false, "corrected_result": "pass"|"fail"|"warning", "reason": "brief explanation"}}"""


async def _verify_test_cases(
    *,
    test_cases: list[dict],
    spec: dict,
    provider_url: str,
    api_key: str,
    model: str,
    tracer=None,
    trace=None,
) -> list[dict]:
    """Verify each test case's expected_output against the signal spec using LLM."""
    verified: list[dict] = []
    corrections = 0

    for case in test_cases:
        expected = case.get("expected_output", {})
        expected_result = expected.get("result", "pass") if isinstance(expected, dict) else "pass"

        prompt = _VERIFY_PROMPT.format(
            spec=json.dumps(spec, indent=2),
            input_json=json.dumps(case.get("dataset_input", {}), indent=2),
            expected_result=expected_result,
            scenario=case.get("scenario_name", ""),
            description=case.get("description", ""),
        )

        try:
            raw = await llm_complete(
                provider_url=provider_url,
                api_key=api_key,
                model=model,
                system=prompt,
                user="Verify this test case now.",
                max_tokens=500,
                temperature=1.0,
                tracer=tracer,
                trace=trace,
                generation_name=f"verify_case_{case.get('case_id', '?')}",
                generation_metadata={
                    "case_id": case.get("case_id"),
                    "expected_result": expected_result,
                },
            )

            cleaned = strip_fences(raw)
            result = json.loads(cleaned)

            if not result.get("correct", True):
                corrected = result.get("corrected_result", expected_result)
                # Update the expected_output with corrected result
                if isinstance(expected, dict):
                    updated_expected = {**expected, "result": corrected}
                else:
                    updated_expected = {"result": corrected}
                case = {
                    **case,
                    "expected_output": updated_expected,
                    "_verification": {
                        "original_result": expected_result,
                        "corrected_result": corrected,
                        "reason": result.get("reason", ""),
                    },
                }
                corrections += 1
                _logger.info(
                    "test_verifier.corrected",
                    extra={
                        "case_id": case.get("case_id"),
                        "original": expected_result,
                        "corrected": corrected,
                        "reason": result.get("reason", "")[:100],
                    },
                )
        except Exception as exc:
            _logger.warning("test_verifier.failed_for_case: %s: %s", case.get("case_id"), exc)

        verified.append(case)

    _logger.info(
        "test_verifier.complete",
        extra={"total": len(verified), "corrections": corrections},
    )
    return verified
