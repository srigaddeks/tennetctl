"""
Job handler for signal_codegen jobs.

Iterative LangGraph-style directed graph:
  generate → compile_check → [fix_compile] → run_test_suite → [fix_failures] → gen_args_schema → finalize

Up to 10 iterations. On success: writes validated Python + args schema + ssf_mapping to signal EAV.
On failure after 10 iterations: sets signal status to 'draft' + writes codegen_failure_reason EAV.

LangFuse tracing:
  - One root trace per job (keyed by job_id / signal_id)
  - One generation span for the initial code generation
  - One generation span per compile-fix attempt
  - One generation span per test-fix attempt
  - Span for args schema extraction
  - Scored with: pass_rate, iterations_used
  - Events: compile_check (pass/fail), test_suite_run (per-case results), finalize
"""

from __future__ import annotations

import json
import uuid
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.signal_codegen.job_handler")

_llm_utils_mod = import_module("backend.20_ai._llm_utils")
llm_complete = _llm_utils_mod.llm_complete
resolve_llm_config = _llm_utils_mod.resolve_llm_config
strip_fences = _llm_utils_mod.strip_fences

_SIGNAL_PROPS = '"15_sandbox"."45_dtl_signal_properties"'
_JOBS = '"20_ai"."45_fct_job_queue"'

MAX_ITERATIONS = 10


class _PoolAdapter:
    def __init__(self, pool):
        self._pool = pool

    async def acquire(self):
        return self._pool.acquire()


async def handle_signal_codegen_job(job, pool, settings) -> None:
    inp = job.input_json
    signal_id = inp.get("signal_id")
    test_dataset_id = inp.get("test_dataset_id")
    spec = inp.get("spec", {})
    rich_schema = inp.get("rich_schema", {})
    tenant_key = getattr(job, "tenant_key", None) or inp.get("tenant_key", "")
    user_id = getattr(job, "user_id", None) or inp.get("user_id")
    org_id = getattr(job, "org_id", None) or inp.get("org_id")
    workspace_id = getattr(job, "workspace_id", None) or inp.get("workspace_id")
    auto_compose_threats = inp.get("auto_compose_threats", True)
    auto_build_library = inp.get("auto_build_library", True)

    _logger.info("signal_codegen.starting", extra={"signal_id": signal_id, "pool_type": type(pool).__name__})

    try:
        async with pool.acquire() as _test_conn:
            _logger.info("signal_codegen.pool_test_ok")
    except Exception as _pool_err:
        _logger.error("signal_codegen.pool_test_failed: %s", _pool_err)
        raise

    # Init LangFuse tracer
    _tracer_mod = import_module("backend.20_ai.14_llm_providers.langfuse_tracer")
    tracer = _tracer_mod.LangFuseTracer.from_settings(settings)
    trace = tracer.trace(
        name="signal_codegen",
        job_id=str(job.id),
        user_id=str(user_id) if user_id else None,
        metadata={
            "signal_id": str(signal_id),
            "signal_code": spec.get("signal_code", ""),
            "connector_type": spec.get("connector_type_code", ""),
            "test_dataset_id": str(test_dataset_id) if test_dataset_id else None,
        },
        tags=["signal_codegen", spec.get("connector_type_code", "")],
    )

    # Resolve LLM config
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    _prompts_mod = import_module("backend.20_ai.24_signal_codegen.prompts")

    config_repo = _config_repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo,
        database_pool=pool,
        settings=settings,
    )
    llm_config = await resolver.resolve(agent_type_code="signal_codegen", org_id=None)
    provider_url, api_key, model = resolve_llm_config(llm_config, settings)

    # Load test cases from dataset
    test_cases = await _load_test_cases(pool, test_dataset_id)

    # Quick-verify test case expected results against spec before iteration loop
    test_cases = await _quick_verify_test_cases(
        test_cases=test_cases,
        spec=spec,
        provider_url=provider_url,
        api_key=api_key,
        model=model,
        tracer=tracer,
        trace=trace,
    )

    # Load AgentTools (compile + execute)
    _tools_mod = import_module("backend.10_sandbox.13_signal_agent.tools")
    _engine_mod = import_module("backend.10_sandbox.07_execution.engine")
    engine = _engine_mod.SignalExecutionEngine(
        timeout_ms=getattr(settings, "sandbox_execution_timeout_ms", 10000),
        max_memory_mb=getattr(settings, "sandbox_execution_max_memory_mb", 256),
    )
    tools = _tools_mod.AgentTools(execution_engine=engine)

    # ── Directed graph: generate → compile → test → fix → repeat ──────────────
    generated_code = None
    fix_history = []
    test_run_results = []
    iterations_used = 0

    # Phase 1: Initial generation — pass ALL test cases so LLM sees full picture
    test_records_formatted = []
    for tc in test_cases:
        test_records_formatted.append(
            f"Test: {tc.get('case_id', '?')} — {tc.get('scenario_name', '?')}\n"
            f"  Description: {tc.get('description', '')}\n"
            f"  Input: {json.dumps(tc.get('dataset_input', {}), default=str)}\n"
            f"  Expected result: {tc.get('expected_output', {}).get('result', '?') if isinstance(tc.get('expected_output'), dict) else '?'}"
        )
    test_records_str = "\n\n".join(test_records_formatted) if test_records_formatted else "No test cases"
    system = _prompts_mod.CODEGEN_SYSTEM_PROMPT.format(
        spec=json.dumps(spec, indent=2),
        test_records=test_records_str,
    )
    generated_code = await llm_complete(
        provider_url=provider_url,
        api_key=api_key,
        model=model,
        system=system,
        user="Generate the signal code now.",
        max_tokens=4000,
        temperature=1.0,
        tracer=tracer,
        trace=trace,
        generation_name="initial_generation",
        generation_metadata={"signal_code": spec.get("signal_code", ""), "phase": "generate"},
    )
    generated_code = strip_fences(generated_code)

    tracer.event(trace, name="initial_generation_complete",
                 metadata={"code_length": len(generated_code)})

    iteration_history = []

    for iteration in range(MAX_ITERATIONS):
        iterations_used = iteration + 1
        _logger.info("signal_codegen.iteration", extra={"signal_id": signal_id, "iteration": iterations_used})

        # ── Compile check ──────────────────────────────────────────────────────
        with tracer.span(trace, name=f"compile_check_iter_{iterations_used}",
                         input={"iteration": iterations_used}) as compile_span:
            compile_result = await tools.compile_signal(generated_code)
            compile_ok = compile_result.get("success", False)
            compile_errors = compile_result.get("errors", [])
            error_msg = "; ".join(compile_errors) if compile_errors else ""
            compile_span.end(
                output={"ok": compile_ok, "error": error_msg[:200]},
                level="DEFAULT" if compile_ok else "WARNING",
            )

        if not compile_ok:
            _logger.debug("signal_codegen.compile_error", extra={"error": error_msg[:200]})
            fix_history.append({"iteration": iterations_used, "type": "compile", "error": error_msg})

            tracer.event(trace, name="compile_error", level="WARNING",
                         metadata={"iteration": iterations_used, "error": error_msg[:300]})

            # Track iteration for UI
            iteration_history.append({
                "iteration": iterations_used,
                "compile_success": False,
                "compile_errors": compile_errors[:3],
                "pass_rate": 0,
                "passed_count": 0,
                "total_count": 0,
                "note": "compile error",
            })
            # Update job progress in DB so UI can poll
            await _update_job_progress(pool, job, {
                "current_iteration": iterations_used,
                "max_iterations": MAX_ITERATIONS,
                "generated_code_preview": (generated_code or "")[:2000],
                "compile_success": False,
                "compile_errors": compile_errors[:5],
                "test_results": [],
                "pass_rate": 0,
                "status": "iterating",
                "iteration_history": iteration_history,
            })

            fix_prompt = _prompts_mod.CODEGEN_FIX_PROMPT.format(
                failing_code=generated_code,
                passed_count=0,
                total_count=len(test_cases),
                pass_pct=0,
                passing_tests="None — code doesn't compile",
                failing_tests="All — compilation failed",
                error_details=f"COMPILE ERROR:\n{error_msg}",
                fix_history=json.dumps(fix_history[-3:], indent=2, default=str),
            )
            generated_code = await llm_complete(
                provider_url=provider_url,
                api_key=api_key,
                model=model,
                system=fix_prompt,
                user="Fix the compile error.",
                max_tokens=4000,
                temperature=1.0,
                tracer=tracer,
                trace=trace,
                generation_name=f"fix_compile_iter_{iterations_used}",
                generation_metadata={"iteration": iterations_used, "error_type": "compile"},
            )
            generated_code = strip_fences(generated_code)
            continue

        # ── Test suite run ─────────────────────────────────────────────────────
        all_passed = True
        test_run_results = []

        with tracer.span(trace, name=f"test_suite_iter_{iterations_used}",
                         input={"test_case_count": len(test_cases), "iteration": iterations_used}) as test_span:
            for case in test_cases:
                dataset_input = case.get("dataset_input", case)
                expected_output = case.get("expected_output", {})
                expected_result = expected_output.get("result", "pass") if isinstance(expected_output, dict) else "pass"
                args_override = case.get("configurable_args_override", {})

                exec_result = await tools.execute_signal(
                    code=generated_code,
                    dataset=dataset_input,
                    configurable_args=args_override,
                )
                actual_result = exec_result.get("result_code") if exec_result.get("status") == "completed" else "error"

                passed = actual_result == expected_result
                test_run_results.append({
                    "case_id": case.get("case_id"),
                    "scenario": case.get("scenario_name"),
                    "expected": expected_result,
                    "actual": actual_result,
                    "passed": passed,
                    "error": exec_result.get("error_message"),
                    "stdout": exec_result.get("stdout_capture", "")[:200],
                })
                if not passed:
                    all_passed = False

            passed_count = sum(1 for r in test_run_results if r["passed"])
            pass_rate = passed_count / max(len(test_run_results), 1)
            test_span.end(output={
                "passed": passed_count,
                "total": len(test_run_results),
                "pass_rate": round(pass_rate, 3),
                "all_passed": all_passed,
            })

        # Track iteration for UI
        iteration_history.append({
            "iteration": iterations_used,
            "compile_success": True,
            "pass_rate": round(pass_rate, 3),
            "passed_count": passed_count,
            "total_count": len(test_run_results),
            "note": "all passed" if all_passed else f"{len(test_run_results) - passed_count} failing",
        })
        # Update job progress in DB so UI can poll
        await _update_job_progress(pool, job, {
            "current_iteration": iterations_used,
            "max_iterations": MAX_ITERATIONS,
            "generated_code_preview": (generated_code or "")[:2000],
            "compile_success": True,
            "compile_errors": [],
            "test_results": test_run_results,
            "pass_rate": round(pass_rate, 3),
            "status": "iterating",
            "iteration_history": iteration_history,
        })

        if all_passed:
            _logger.info(
                "signal_codegen.tests_passed",
                extra={"signal_id": signal_id, "iterations": iterations_used},
            )
            tracer.event(trace, name="all_tests_passed",
                         metadata={"iteration": iterations_used, "total_cases": len(test_run_results)})
            break

        # ── Fix failing tests ──────────────────────────────────────────────────
        failed_cases = [r for r in test_run_results if not r["passed"]]
        fix_history.append({
            "iteration": iterations_used,
            "type": "test_failure",
            "failed_count": len(failed_cases),
            "failures": failed_cases[:3],
        })

        tracer.event(trace, name="test_failures", level="WARNING",
                     metadata={
                         "iteration": iterations_used,
                         "failed_count": len(failed_cases),
                         "pass_rate": round(pass_rate, 3),
                         "failures": [{"scenario": f["scenario"], "expected": f["expected"], "actual": f["actual"]}
                                       for f in failed_cases[:5]],
                     })

        # Build structured feedback for the LLM
        passing_tests_str = "\n".join(
            f"  ✓ {r['case_id']} ({r['scenario']}): expected={r['expected']} actual={r['actual']}"
            for r in test_run_results if r["passed"]
        ) or "  None"
        failing_tests_str = "\n".join(
            f"  ✗ {r['case_id']} ({r['scenario']}): expected={r['expected']} actual={r['actual']}"
            + (f"\n    Error: {str(r.get('error', ''))[:200]}" if r.get("error") else "")
            + (f"\n    Input: {json.dumps(next((tc.get('dataset_input', {}) for tc in test_cases if tc.get('case_id') == r['case_id']), {}), default=str)[:300]}" if test_cases else "")
            for r in test_run_results if not r["passed"]
        ) or "  None"
        error_details_str = "\n".join(
            f"Case {r['case_id']}: {(r.get('error') or 'no error detail')[:200]}"
            for r in failed_cases[:5]
        )
        passed_count = sum(1 for r in test_run_results if r["passed"])

        fix_prompt = _prompts_mod.CODEGEN_FIX_PROMPT.format(
            failing_code=generated_code,
            passed_count=passed_count,
            total_count=len(test_run_results),
            pass_pct=round(pass_rate * 100),
            passing_tests=passing_tests_str,
            failing_tests=failing_tests_str,
            error_details=error_details_str,
            fix_history=json.dumps(fix_history[-3:], indent=2, default=str),
        )
        generated_code = await llm_complete(
            provider_url=provider_url,
            api_key=api_key,
            model=model,
            system=fix_prompt,
            user=f"Fix the {len(failed_cases)} failing tests. The signal spec requires: {spec.get('intent', '')}",
            max_tokens=4000,
            temperature=1.0,
            tracer=tracer,
            trace=trace,
            generation_name=f"fix_tests_iter_{iterations_used}",
            generation_metadata={
                "iteration": iterations_used,
                "failed_count": len(failed_cases),
                "error_type": "test_failure",
            },
        )
        generated_code = strip_fences(generated_code)

    else:
        # Exhausted iterations — mark signal as draft with failure reason
        _logger.warning("signal_codegen.exhausted", extra={"signal_id": signal_id, "iterations": iterations_used})

        final_pass_rate = sum(1 for r in test_run_results if r["passed"]) / max(len(test_run_results), 1)
        tracer.event(trace, name="iterations_exhausted", level="ERROR",
                     metadata={"iterations": iterations_used, "final_pass_rate": round(final_pass_rate, 3)})
        tracer.score(trace, name="pass_rate", value=final_pass_rate, comment="exhausted")
        tracer.score(trace, name="iterations_used", value=iterations_used / MAX_ITERATIONS,
                     comment=f"{iterations_used}/{MAX_ITERATIONS} iterations")

        # Write final exhausted status to output_json
        await _update_job_progress(pool, job, {
            "current_iteration": iterations_used,
            "max_iterations": MAX_ITERATIONS,
            "generated_code_preview": (generated_code or "")[:2000],
            "compile_success": True,
            "compile_errors": [],
            "test_results": test_run_results,
            "pass_rate": round(final_pass_rate, 3),
            "status": "exhausted",
            "iteration_history": iteration_history,
        })

        try:
            async with pool.acquire() as conn:
                await _upsert_prop(conn, signal_id, "codegen_failure_reason", json.dumps({
                    "iterations_used": iterations_used,
                    "last_test_results": test_run_results,
                }))
                await _update_signal_status(conn, signal_id, "draft")
        except Exception as save_err:
            _logger.error("signal_codegen.save_failure_reason_failed: %s — trying raw pool", save_err)
            raw_pool = getattr(pool, 'pool', getattr(pool, '_pool', pool))
            async with pool.acquire() as conn:
                await _upsert_prop(conn, signal_id, "codegen_failure_reason", json.dumps({
                    "iterations_used": iterations_used,
                    "last_test_results": test_run_results,
                }))
                await _update_signal_status(conn, signal_id, "draft")
        tracer.flush()
        raise RuntimeError(f"Signal codegen exhausted {MAX_ITERATIONS} iterations without passing all tests")

    # ── Generate args schema ───────────────────────────────────────────────────
    args_schema = await _generate_args_schema(
        provider_url=provider_url,
        api_key=api_key,
        model=model,
        code=generated_code,
        prompts_mod=_prompts_mod,
        tracer=tracer,
        trace=trace,
    )

    # ── Score the trace ────────────────────────────────────────────────────────
    final_pass_rate = sum(1 for r in test_run_results if r["passed"]) / max(len(test_run_results), 1)
    tracer.score(trace, name="pass_rate", value=final_pass_rate, comment="success")
    tracer.score(trace, name="iterations_used", value=iterations_used / MAX_ITERATIONS,
                 comment=f"{iterations_used}/{MAX_ITERATIONS} iterations")

    # Write final success status to output_json
    await _update_job_progress(pool, job, {
        "current_iteration": iterations_used,
        "max_iterations": MAX_ITERATIONS,
        "generated_code_preview": (generated_code or "")[:2000],
        "compile_success": True,
        "compile_errors": [],
        "test_results": test_run_results,
        "pass_rate": round(final_pass_rate, 3),
        "status": "completed",
        "iteration_history": iteration_history,
    })

    # ── Write results to signal EAV ────────────────────────────────────────────
    try:
        async with pool.acquire() as conn:
            await _upsert_prop(conn, signal_id, "python_source", generated_code)
            await _upsert_prop(conn, signal_id, "signal_args_schema", json.dumps(args_schema))
            await _upsert_prop(conn, signal_id, "codegen_iterations", str(iterations_used))
            await _upsert_prop(conn, signal_id, "codegen_test_results", json.dumps(test_run_results))
            await _update_signal_status(conn, signal_id, "validated")
    except Exception as save_err:
        _logger.error("signal_codegen.save_failed: %s — trying direct execute", save_err)
        # Fallback: try using pool.pool directly (raw asyncpg pool)
        raw_pool = getattr(pool, 'pool', getattr(pool, '_pool', pool))
        async with pool.acquire() as conn:
            await _upsert_prop(conn, signal_id, "python_source", generated_code)
            await _upsert_prop(conn, signal_id, "signal_args_schema", json.dumps(args_schema))
            await _upsert_prop(conn, signal_id, "codegen_iterations", str(iterations_used))
            await _upsert_prop(conn, signal_id, "codegen_test_results", json.dumps(test_run_results))
            await _update_signal_status(conn, signal_id, "validated")

    tracer.event(trace, name="signal_finalized",
                 metadata={"status": "validated", "args_count": len(args_schema), "iterations": iterations_used})

    # ── Write to signal file store if configured ───────────────────────────────
    store_root = getattr(settings, "signal_store_root", "") or ""
    if store_root and org_id:
        try:
            _store_mod = import_module("backend.10_sandbox.signal_store.writer")
            writer = _store_mod.SignalFileWriter(store_root=store_root)
            signal_code = spec.get("signal_code", f"signal_{str(signal_id)[:8]}")
            writer.write_signal(
                org_id=str(org_id),
                signal_code=signal_code,
                version=1,
                signal_id=str(signal_id),
                code=generated_code,
                args_schema=args_schema,
                codegen_iterations=iterations_used,
                status="validated",
            )
            _logger.info(
                "signal_codegen.file_written",
                extra={"signal_id": signal_id, "signal_code": signal_code},
            )
        except Exception as exc:
            _logger.warning("signal_codegen.file_write_failed: %s", exc)

    # ── Auto-enqueue threat_composer if requested ──────────────────────────────
    if auto_compose_threats and signal_id:
        threat_job_id = str(uuid.uuid4())
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
                    'threat_composer',
                    'threat_composer', 'queued', 'normal', NOW(),
                    $6::jsonb, NOW(), NOW()
                )
                """,
                threat_job_id, tenant_key, user_id,
                org_id, workspace_id,
                json.dumps({
                    "signal_ids": [str(signal_id)],
                    "org_id": str(org_id) if org_id else None,
                    "workspace_id": str(workspace_id) if workspace_id else None,
                    "auto_build_library": auto_build_library,
                }),
            )
        _logger.info(
            "signal_codegen.enqueued_threat_composer",
            extra={"signal_id": signal_id, "threat_job_id": threat_job_id},
        )
        tracer.event(trace, name="enqueued_threat_composer",
                     metadata={"threat_job_id": threat_job_id})

    _logger.info(
        "signal_codegen.complete",
        extra={"signal_id": signal_id, "iterations": iterations_used, "args_count": len(args_schema)},
    )
    tracer.flush()


async def _generate_args_schema(
    *,
    provider_url: str,
    api_key: str,
    model: str,
    code: str,
    prompts_mod,
    tracer=None,
    trace=None,
) -> list:
    prompt = prompts_mod.ARGS_SCHEMA_PROMPT.format(code=code)
    try:
        raw = await llm_complete(
            provider_url=provider_url,
            api_key=api_key,
            model=model,
            system=prompt,
            user="Extract args schema.",
            max_tokens=1000,
            temperature=1.0,
            tracer=tracer,
            trace=trace,
            generation_name="extract_args_schema",
        )
        result = json.loads(strip_fences(raw))
        return result if isinstance(result, list) else []
    except Exception as exc:
        _logger.warning("signal_codegen.args_schema_failed: %s", exc)
        return []


async def _load_test_cases(pool, test_dataset_id: str | None) -> list[dict]:
    if not test_dataset_id:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT record_data FROM "15_sandbox"."43_dtl_dataset_records" WHERE dataset_id = $1::uuid ORDER BY record_seq',
                test_dataset_id,
            )
        cases = []
        for r in rows:
            payload = r["record_data"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            if isinstance(payload, dict):
                cases.append(payload)
        return cases
    except Exception as exc:
        _logger.warning("signal_codegen.load_test_cases_failed: %s", exc)
        return []


async def _upsert_prop(conn, signal_id: str, key: str, value: str) -> None:
    await conn.execute(
        f"""
        INSERT INTO {_SIGNAL_PROPS} (id, signal_id, property_key, property_value)
        VALUES (gen_random_uuid(), $1::uuid, $2, $3)
        ON CONFLICT (signal_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
        """,
        signal_id, key, value,
    )


async def _update_signal_status(conn, signal_id: str, status_code: str) -> None:
    await conn.execute(
        """
        UPDATE "15_sandbox"."22_fct_signals"
        SET signal_status_code = $2, updated_at = NOW()
        WHERE id = $1::uuid
        """,
        signal_id, status_code,
    )


async def _update_job_progress(pool, job, progress: dict) -> None:
    """Write iteration progress to the job's output_json so the UI can poll it."""
    try:
        raw_pool = getattr(pool, 'pool', getattr(pool, '_pool', pool))
        async with pool.acquire() as conn:
            await conn.execute(
                f'UPDATE {_JOBS} SET output_json = $1::jsonb, updated_at = NOW() WHERE id = $2::uuid',
                json.dumps(progress, default=str), str(job.id),
            )
    except Exception as exc:
        _logger.warning("signal_codegen.progress_update_failed: %s", exc)


async def _quick_verify_test_cases(
    *,
    test_cases: list[dict],
    spec: dict,
    provider_url: str,
    api_key: str,
    model: str,
    tracer=None,
    trace=None,
) -> list[dict]:
    """Batch-verify test case expected results against spec. Fixes incorrect ones.

    Uses a single LLM call for speed (~5s) rather than one call per case.
    Corrections are ephemeral — used for this codegen run only, not written back to DB.
    """
    if not test_cases:
        return test_cases

    cases_summary = []
    for tc in test_cases:
        expected = tc.get("expected_output", {})
        expected_result = expected.get("result", "pass") if isinstance(expected, dict) else "pass"
        cases_summary.append({
            "case_id": tc.get("case_id"),
            "scenario": tc.get("scenario_name"),
            "description": tc.get("description"),
            "input_keys": list(tc.get("dataset_input", {}).keys()),
            "key_values": {k: v for k, v in list(tc.get("dataset_input", {}).items())[:8]},
            "expected_result": expected_result,
        })

    batch_verify_prompt = """You are verifying test cases for a compliance signal.

Signal spec intent: {intent}
Signal checks: {checks}

For each test case, verify if the expected_result is correct.
- "fail" = critical compliance violation found
- "warning" = minor issue, not critical
- "pass" = fully compliant

Test cases to verify:
{cases_json}

Return a JSON array with corrections ONLY for incorrect cases:
[{{"case_id": "tc_XXX", "corrected_result": "pass"|"fail"|"warning", "reason": "why"}}]

If all are correct, return []"""

    try:
        raw = await llm_complete(
            provider_url=provider_url,
            api_key=api_key,
            model=model,
            system=batch_verify_prompt.format(
                intent=spec.get("intent", ""),
                checks=json.dumps(spec.get("dataset_fields_used", []), indent=2),
                cases_json=json.dumps(cases_summary, indent=2, default=str),
            ),
            user="Verify all test cases now. Return corrections as JSON array.",
            max_tokens=2000,
            temperature=1.0,
            tracer=tracer,
            trace=trace,
            generation_name="codegen_batch_verify",
            generation_metadata={
                "signal_code": spec.get("signal_code", ""),
                "case_count": len(test_cases),
            },
        )

        cleaned = strip_fences(raw)
        corrections = json.loads(cleaned)
        if not isinstance(corrections, list):
            return test_cases

        correction_map = {
            c["case_id"]: c["corrected_result"]
            for c in corrections
            if "case_id" in c and "corrected_result" in c
        }

        if not correction_map:
            _logger.info("codegen_verifier.all_correct: %d cases verified", len(test_cases))
            return test_cases

        # Apply corrections immutably
        updated_cases = []
        for tc in test_cases:
            cid = tc.get("case_id")
            if cid in correction_map:
                expected = tc.get("expected_output", {})
                if isinstance(expected, dict):
                    old = expected.get("result", "?")
                    updated_expected = {**expected, "result": correction_map[cid]}
                    tc = {**tc, "expected_output": updated_expected}
                    _logger.info("codegen_verifier.corrected: %s %s->%s", cid, old, correction_map[cid])
            updated_cases.append(tc)

        _logger.info("codegen_verifier.corrections_applied: %d", len(correction_map))
        return updated_cases

    except Exception as exc:
        _logger.warning("codegen_verifier.batch_verify_failed: %s", exc)
        return test_cases
