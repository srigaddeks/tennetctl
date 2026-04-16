"""
Signal Code Generator Service — direct API for interactive code generation.
Generates Python evaluate() function from spec + test data, with iterative fix loop.

Architecture:
  - Each generation run gets its own temp directory (isolated workspace)
  - All iterations logged with full trace (code, errors, test results)
  - Generated code tested in sandbox subprocess (resource-limited)
  - Args schema extracted and saved as form-ready JSON
"""
from __future__ import annotations

import json
import hashlib
import uuid
import tempfile
import os
import time
from pathlib import Path
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.signal_codegen.service")

MAX_ITERATIONS = 8


def _strip_fences(code: str) -> str:
    """Remove markdown code fences from LLM output."""
    code = code.strip()
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    elif code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()
    return code


def _parse_json(raw: str) -> list | dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = len(lines) - 1
        while end > 0 and lines[end].strip() in ("```", ""):
            end -= 1
        text = "\n".join(lines[1:end + 1])
    return json.loads(text)


class SignalCodegenService:
    """Interactive signal code generation with compile + test loop."""

    def __init__(self, *, database_pool, settings):
        self._pool = database_pool
        self._settings = settings

    async def generate_signal_code(
        self,
        *,
        user_id: str,
        signal_spec: dict,
        test_records: list[dict],
        signal_id: str | None = None,
        org_id: str | None = None,
        is_retry: bool = False,
    ) -> dict:
        """
        Generate Python signal code from spec + test data.
        Iterative loop: generate → compile → test → fix (up to 8 iterations).
        On retry, loads prior fix_history so LLM can learn from past failures.
        Returns generated code + test results + args schema.
        """
        from .prompts import CODEGEN_SYSTEM_PROMPT, CODEGEN_FIX_PROMPT, ARGS_SCHEMA_PROMPT

        # Resolve LLM
        provider, config = await self._get_provider()

        # Load prior fix history if retrying (learning from past failures)
        prior_fix_history = []
        prior_code = None
        if is_retry and signal_id:
            try:
                async with self._pool.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        SELECT property_key, property_value
                        FROM "15_sandbox"."45_dtl_signal_properties"
                        WHERE signal_id = $1::uuid AND property_key IN ('codegen_fix_history', 'python_source')
                        """,
                        signal_id,
                    )
                    # Actually fetch both
                    rows = await conn.fetch(
                        """
                        SELECT property_key, property_value
                        FROM "15_sandbox"."45_dtl_signal_properties"
                        WHERE signal_id = $1::uuid AND property_key IN ('codegen_fix_history', 'python_source')
                        """,
                        signal_id,
                    )
                    for r in rows:
                        if r["property_key"] == "codegen_fix_history":
                            try:
                                prior_fix_history = json.loads(r["property_value"])
                            except Exception:
                                pass
                        elif r["property_key"] == "python_source":
                            prior_code = r["property_value"]
            except Exception as exc:
                _logger.warning("codegen: failed to load prior history: %s", exc)

        # Build test records context for the LLM
        test_ctx_parts = []
        for i, rec in enumerate(test_records[:10]):
            name = rec.get("_scenario_name", f"test_{i+1}")
            expected = rec.get("_expected_result", "?")
            test_ctx_parts.append(f"--- {name} (expected: {expected}) ---\n{json.dumps(rec, indent=2, default=str)[:1500]}")
        test_records_str = "\n\n".join(test_ctx_parts) if test_ctx_parts else "(No test records)"

        # Create isolated workspace for this codegen run
        run_id = str(uuid.uuid4())[:8]
        signal_code = signal_spec.get("signal_code", "unknown")
        workspace = Path(tempfile.mkdtemp(prefix=f"codegen_{signal_code}_{run_id}_"))
        trace_log = []
        t_start = time.time()

        def _trace(event: str, **kwargs):
            entry = {"t": round(time.time() - t_start, 2), "event": event, **kwargs}
            trace_log.append(entry)
            _logger.info("codegen.%s [%s] %s", event, run_id, json.dumps({k: str(v)[:200] for k, v in kwargs.items()}))

        _trace("start", signal_code=signal_code, workspace=str(workspace),
               test_records=len(test_records), is_retry=is_retry,
               prior_history_count=len(prior_fix_history))

        # Phase 1: Generate initial code (or use prior code if retry)
        system = CODEGEN_SYSTEM_PROMPT.format(
            spec=json.dumps(signal_spec, indent=2, default=str)[:4000],
            test_records=test_records_str,
        )

        # If retrying with prior code, use it as starting point with fix context
        if is_retry and prior_code and prior_fix_history:
            _trace("retry_with_prior_code", prior_code_length=len(prior_code))
            from .prompts import CODEGEN_FIX_PROMPT
            retry_prompt = CODEGEN_FIX_PROMPT.format(
                error_type="RetryFromPriorAttempt",
                error_message=f"Previous attempt failed after {len(prior_fix_history)} iterations. Fix the issues and improve the code.",
                fix_history=json.dumps(prior_fix_history[-5:]),
                failing_code=prior_code,
                test_results=json.dumps([h for h in prior_fix_history if h.get("type") == "test_failure"][-2:]),
            )
            generated_code = await self._llm_call(provider, retry_prompt, "Fix the prior code based on the failure history.")
            generated_code = _strip_fences(generated_code)
            fix_history = prior_fix_history.copy()
        else:
            _trace("llm_generate_start")
            generated_code = await self._llm_call(
                provider, system,
                "Generate the evaluate() function now. Return ONLY Python code. No import statements.",
            )
            generated_code = _strip_fences(generated_code)
            fix_history = []
        _trace("llm_generate_done", code_length=len(generated_code))

        # Save initial code to workspace
        (workspace / "v0_initial.py").write_text(generated_code)
        all_passed = False

        # Phase 2: Iterative compile + test + fix
        test_results = []
        iterations_used = 0

        _engine_mod = import_module("backend.10_sandbox.07_execution.engine")
        engine = _engine_mod.SignalExecutionEngine(
            timeout_ms=self._settings.sandbox_execution_timeout_ms,
            max_memory_mb=self._settings.sandbox_execution_max_memory_mb,
        )

        SESSION_TIMEOUT = 600  # 10 minutes max per codegen session

        for iteration in range(MAX_ITERATIONS):
            iterations_used = iteration + 1

            # Session timeout check
            if time.time() - t_start > SESSION_TIMEOUT:
                _trace("session_timeout", elapsed=round(time.time() - t_start, 1))
                break

            _trace("iteration_start", iteration=iterations_used)

            # Compile check (try to compile the code)
            try:
                compile(generated_code, "<signal>", "exec")
            except SyntaxError as e:
                error_msg = f"SyntaxError: {e.msg} at line {e.lineno}"
                _trace("compile_error", iteration=iterations_used, error=error_msg)
                fix_history.append({"iteration": iterations_used, "type": "compile", "error": error_msg})
                fix_prompt = CODEGEN_FIX_PROMPT.format(
                    error_type="SyntaxError",
                    error_message=error_msg,
                    fix_history=json.dumps(fix_history[-3:]),
                    failing_code=generated_code,
                    test_results="N/A",
                )
                generated_code = await self._llm_call(provider, fix_prompt, "Fix the syntax error.")
                generated_code = _strip_fences(generated_code)
                continue

            # Run against test records
            all_passed = True
            test_results = []

            for rec in test_records[:15]:
                scenario = rec.get("_scenario_name", "unnamed")
                # Map expected_result to anomalous boolean
                expected_result = rec.get("_expected_result", "pass")
                expected_anomalous = expected_result in ("fail", "warning")

                exec_result = await engine.execute(
                    python_source=generated_code,
                    dataset=rec,
                    configurable_args={},
                )

                if exec_result.status == "completed":
                    # Parse the result — handle both old and new format
                    actual_code = exec_result.result_code
                    actual_summary = exec_result.result_summary

                    # Check if result uses new format (anomalous) or old (result)
                    actual_anomalous = actual_code in ("fail", "warning") if actual_code else None

                    # Try to get anomalous from metadata
                    if exec_result.metadata and "anomalous" in exec_result.metadata:
                        actual_anomalous = exec_result.metadata["anomalous"]

                    passed = actual_anomalous == expected_anomalous if actual_anomalous is not None else False
                    test_results.append({
                        "scenario": scenario,
                        "expected_anomalous": expected_anomalous,
                        "actual_anomalous": actual_anomalous,
                        "actual_result_code": actual_code,
                        "passed": passed,
                        "summary": actual_summary[:100] if actual_summary else "",
                    })
                    if not passed:
                        all_passed = False
                else:
                    # Execution error
                    test_results.append({
                        "scenario": scenario,
                        "expected_anomalous": expected_anomalous,
                        "actual_anomalous": None,
                        "passed": False,
                        "error": exec_result.error_message[:200] if exec_result.error_message else "Unknown error",
                    })
                    all_passed = False

            if all_passed:
                _trace("all_tests_passed", iteration=iterations_used, passed=sum(1 for r in test_results if r["passed"]))
                # Save final code to workspace
                (workspace / f"v{iterations_used}_final.py").write_text(generated_code)
                break

            # Save iteration code
            (workspace / f"v{iterations_used}_iteration.py").write_text(generated_code)
            _trace("tests_failed", iteration=iterations_used, passed=sum(1 for r in test_results if r["passed"]), total=len(test_results))

            # Fix failing tests
            failed = [r for r in test_results if not r["passed"]]
            fix_history.append({
                "iteration": iterations_used,
                "type": "test_failure",
                "failed_count": len(failed),
                "failures": failed[:3],
            })
            fix_prompt = CODEGEN_FIX_PROMPT.format(
                error_type="TestFailure",
                error_message=f"{len(failed)}/{len(test_results)} tests failed",
                fix_history=json.dumps(fix_history[-3:]),
                failing_code=generated_code,
                test_results=json.dumps(failed[:5], indent=2),
            )
            generated_code = await self._llm_call(provider, fix_prompt, "Fix the failing tests.")
            generated_code = _strip_fences(generated_code)
        else:
            _trace("exhausted_iterations", iterations=MAX_ITERATIONS)
            # Mark signal as draft with failure reason if all iterations exhausted
            if signal_id:
                try:
                    async with self._pool.acquire() as conn:
                        prop_id = str(uuid.uuid4())
                        await conn.execute(
                            """
                            INSERT INTO "15_sandbox"."45_dtl_signal_properties"
                                (id, signal_id, property_key, property_value)
                            VALUES ($1::uuid, $2::uuid, 'codegen_failure_reason', $3)
                            ON CONFLICT (signal_id, property_key)
                                DO UPDATE SET property_value = EXCLUDED.property_value, updated_at = now()
                            """,
                            prop_id, signal_id,
                            json.dumps({
                                "iterations_used": iterations_used,
                                "last_pass_rate": round(sum(1 for r in test_results if r["passed"]) / max(len(test_results), 1), 2),
                                "last_failures": [r for r in test_results if not r["passed"]][:5],
                                "fix_history_summary": [{"iter": h.get("iteration"), "type": h.get("type")} for h in fix_history],
                            }),
                        )
                        await conn.execute(
                            'UPDATE "15_sandbox"."22_fct_signals" SET signal_status_code = $1, updated_at = now() WHERE id = $2::uuid',
                            "draft", signal_id,
                        )
                except Exception as save_exc:
                    _logger.warning("codegen: failed to mark signal as draft: %s", save_exc)

        # Phase 3: Extract args schema
        args_schema = []
        try:
            args_prompt = ARGS_SCHEMA_PROMPT.format(code=generated_code)
            args_raw = await self._llm_call(provider, args_prompt, "Extract the args schema.")
            args_schema = _parse_json(args_raw)
            if not isinstance(args_schema, list):
                args_schema = []
        except Exception as exc:
            _logger.warning("codegen.args_schema_failed: %s", exc)

        # Phase 4: Save to signal if signal_id provided
        saved = False
        if signal_id:
            try:
                python_hash = hashlib.sha256(generated_code.encode()).hexdigest()
                async with self._pool.acquire() as conn:
                    for key, value in [
                        ("python_source", generated_code),
                        ("signal_args_schema", json.dumps(args_schema)),
                        ("codegen_iterations", str(iterations_used)),
                        ("codegen_test_results", json.dumps(test_results[:20])),
                    ]:
                        prop_id = str(uuid.uuid4())
                        await conn.execute(
                            """
                            INSERT INTO "15_sandbox"."45_dtl_signal_properties"
                                (id, signal_id, property_key, property_value)
                            VALUES ($1::uuid, $2::uuid, $3, $4)
                            ON CONFLICT (signal_id, property_key)
                                DO UPDATE SET property_value = EXCLUDED.property_value, updated_at = now()
                            """,
                            prop_id, signal_id, key, value,
                        )
                    # Update python_hash on the signal
                    await conn.execute(
                        'UPDATE "15_sandbox"."22_fct_signals" SET python_hash = $1, signal_status_code = $2, updated_at = now() WHERE id = $3::uuid',
                        python_hash,
                        "validated" if all_passed else "testing",
                        signal_id,
                    )
                saved = True
            except Exception as exc:
                _logger.warning("codegen.save_failed: %s", exc)

        passed_count = sum(1 for r in test_results if r["passed"])
        total_count = len(test_results)
        elapsed = round(time.time() - t_start, 1)

        # Save trace log to workspace
        # Determine final status
        if all_passed:
            final_status = "success"
        elif passed_count > 0:
            final_status = "partial"
        else:
            final_status = "failed"

        _trace("complete", elapsed=elapsed, status=final_status,
               pass_rate=round(passed_count / total_count, 2) if total_count else 0)

        # Save fix_history to signal EAV for future retry learning
        if signal_id and fix_history:
            try:
                async with self._pool.acquire() as conn:
                    prop_id = str(uuid.uuid4())
                    await conn.execute(
                        """
                        INSERT INTO "15_sandbox"."45_dtl_signal_properties"
                            (id, signal_id, property_key, property_value)
                        VALUES ($1::uuid, $2::uuid, 'codegen_fix_history', $3)
                        ON CONFLICT (signal_id, property_key)
                            DO UPDATE SET property_value = EXCLUDED.property_value, updated_at = now()
                        """,
                        prop_id, signal_id, json.dumps(fix_history),
                    )
            except Exception:
                pass

        # Always cleanup workspace
        try:
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)
        except Exception:
            pass

        return {
            "status": final_status,
            "iterations_used": iterations_used,
            "all_tests_passed": all_passed,
            "test_pass_rate": round(passed_count / total_count, 2) if total_count else 0,
            "test_results": test_results,
            "generated_code": generated_code,
            "args_schema": args_schema,
            "saved_to_signal": saved,
            "signal_id": signal_id,
            "elapsed_seconds": elapsed,
            "trace_log": trace_log,
        }

    async def _get_provider(self):
        _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
        _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
        _factory_mod = import_module("backend.20_ai.14_llm_providers.factory")

        resolver = _resolver_mod.AgentConfigResolver(
            repository=_config_repo_mod.AgentConfigRepository(),
            database_pool=self._pool,
            settings=self._settings,
        )
        config = await resolver.resolve(agent_type_code="signal_codegen", org_id=None)
        provider = _factory_mod.get_provider(
            provider_type=config.provider_type,
            provider_base_url=config.provider_base_url,
            api_key=config.api_key,
            model_id=config.model_id,
            temperature=1.0,
        )
        return provider, config

    async def _llm_call(self, provider, system: str, user: str, max_retries: int = 3) -> str:
        """LLM call with retry, rate limit backoff, and validation."""
        import asyncio

        for attempt in range(max_retries):
            try:
                response = await asyncio.wait_for(
                    provider.chat_completion(
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        temperature=1.0,
                        max_tokens=None,
                    ),
                    timeout=60.0,  # 60s per LLM call
                )
                content = response.content.strip()
                if not content:
                    raise ValueError("LLM returned empty response")
                return content
            except asyncio.TimeoutError:
                _logger.warning("codegen._llm_call: timeout attempt %d", attempt + 1)
                if attempt == max_retries - 1:
                    raise
            except Exception as exc:
                err_str = str(exc)
                # Rate limit — backoff
                if "429" in err_str or "rate" in err_str.lower():
                    wait = min(30, 5 * (attempt + 1))
                    _logger.warning("codegen._llm_call: rate limited, waiting %ds", wait)
                    import asyncio as _aio
                    await _aio.sleep(wait)
                elif attempt == max_retries - 1:
                    raise
                else:
                    _logger.warning("codegen._llm_call: attempt %d failed: %s", attempt + 1, err_str[:200])
                    import asyncio as _aio
                    await _aio.sleep(2 ** attempt)
        raise RuntimeError("LLM call failed after all retries")
