"""
Signal Generation Agent
=======================

Iterative LLM-driven code generation for K-Control sandbox signals.

Quick-generate flow (prompt → code):
  1. _generate_code()      — LLM call: prompt + dataset schema + connector examples → Python code
  2. _compile_check()      — RestrictedPython compile, capture errors
  3. _run_test()           — Execute in sandbox against sample_dataset + configurable_args
  4. _fix_code()           — LLM fix call with error context (loop up to max_iterations)
  5. _detect_ssf()         — Keyword heuristic → CAEP/RISC event mapping
  6. _generate_args_schema() — LLM call: extract kwargs → signal_args_schema JSON
  7. _suggest_name()       — LLM call: suggest display name + description

Spec-driven flow (used by 24_signal_codegen):
  — Uses signal_spec.detection_logic + dataset_fields_used in the system prompt
  — Runs against all test cases from test_dataset (not just sample_dataset)
  — Writes signal_args_schema matching signal_spec.configurable_args

Both modes stream SSE events via stream_generate() for real-time frontend feedback.
Batch mode via run() for job queue workers.
"""
from __future__ import annotations

import asyncio
import json
import re
from importlib import import_module
from typing import AsyncGenerator

import httpx

from .prompts import (
    CONNECTOR_EXAMPLES,
    SIGNAL_ARGS_SCHEMA_PROMPT,
    SIGNAL_FIX_PROMPT,
    SIGNAL_NAME_PROMPT,
    SIGNAL_SSF_MAPPING_PROMPT,
    SIGNAL_SYSTEM_PROMPT,
)
from .state import SignalGenState
from .tools import AgentTools

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.10_sandbox.13_signal_agent.agent")


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


class SignalGenerationAgent:
    """
    Stateless agent. Instantiated per request with injected LLM config + tools.
    Matches the FrameworkBuilderAgent architecture pattern exactly.
    """

    def __init__(
        self,
        *,
        llm_config,    # ResolvedLLMConfig from AgentConfigResolver
        settings,      # app Settings
        tools: AgentTools,
    ) -> None:
        self._config = llm_config
        self._settings = settings
        self._tools = tools

    # ──────────────────────────────────────────────────────────────────────────
    # Public: batch entry point (used by job queue worker)
    # ──────────────────────────────────────────────────────────────────────────

    async def run(self, state: SignalGenState) -> SignalGenState:
        """Run the full generation pipeline. Returns final state."""
        _logger.info(
            "signal_gen.start",
            extra={"connector": state.get("connector_type"), "max_iterations": state.get("max_iterations", 10)},
        )
        state.setdefault("iteration", 0)
        state.setdefault("max_iterations", 10)
        state.setdefault("fix_history", [])
        state.setdefault("configurable_args", {})
        state["is_complete"] = False
        state["error"] = None

        state = await self._generate_code(state)
        if state.get("error"):
            return state

        for i in range(state["max_iterations"]):
            state["iteration"] = i + 1
            compile_result = await self._tools.compile_signal(state["generated_code"] or "")
            if not compile_result["success"]:
                state["compile_error"] = "; ".join(compile_result.get("errors", ["compile error"]))
                state["fix_history"].append({
                    "iteration": state["iteration"],
                    "error_type": "compile",
                    "error_message": state["compile_error"],
                })
                state = await self._fix_code(state)
                if state.get("error"):
                    break
                continue
            state["compile_error"] = None

            if state.get("sample_dataset") is not None:
                test_result = await self._tools.execute_signal(
                    state["generated_code"] or "",
                    state["sample_dataset"],
                    configurable_args=state.get("configurable_args") or {},
                )
                state["test_result"] = test_result
                if test_result.get("status") != "completed":
                    state["fix_history"].append({
                        "iteration": state["iteration"],
                        "error_type": "runtime",
                        "error_message": test_result.get("error_message", "execution failed"),
                    })
                    state = await self._fix_code(state)
                    if state.get("error"):
                        break
                    continue

            # All checks passed
            state["final_code"] = state["generated_code"]
            state["is_complete"] = True
            break

        state["iterations_used"] = state["iteration"]

        if not state["is_complete"] and not state.get("error"):
            # Best-effort: return last generated code even if tests didn't pass
            state["error"] = f"Could not pass all tests after {state['max_iterations']} iterations"
            state["final_code"] = state.get("generated_code")

        state = self._detect_ssf(state)
        state = await self._generate_args_schema(state)
        state = await self._suggest_name(state)

        _logger.info(
            "signal_gen.complete",
            extra={"iterations_used": state["iterations_used"], "is_complete": state["is_complete"]},
        )
        return state

    # ──────────────────────────────────────────────────────────────────────────
    # Public: streaming SSE entry point (used by quick-generate endpoint)
    # ──────────────────────────────────────────────────────────────────────────

    async def stream_generate(self, state: SignalGenState) -> AsyncGenerator[str, None]:
        """Yield SSE events during generation. Matches FrameworkBuilderAgent streaming pattern."""
        state.setdefault("iteration", 0)
        state.setdefault("max_iterations", 10)
        state.setdefault("fix_history", [])
        state.setdefault("configurable_args", {})

        yield _sse("gen_started", {"message": "Starting signal generation…", "pct": 5})

        state = await self._generate_code(state)
        if state.get("error"):
            yield _sse("gen_error", {"message": state["error"]})
            return

        yield _sse("gen_progress", {"phase": "initial_code_ready", "pct": 20, "message": "Code generated, running tests…"})

        for i in range(state["max_iterations"]):
            state["iteration"] = i + 1
            pct = 20 + int((i / state["max_iterations"]) * 55)

            compile_result = await self._tools.compile_signal(state["generated_code"] or "")
            if not compile_result["success"]:
                error_msg = "; ".join(compile_result.get("errors", ["compile error"]))
                state["compile_error"] = error_msg
                state["fix_history"].append({"iteration": i + 1, "error_type": "compile", "error_message": error_msg})
                yield _sse("gen_progress", {
                    "phase": "fixing_compile",
                    "pct": pct,
                    "iteration": i + 1,
                    "message": f"Compile error — fixing (attempt {i + 1}/{state['max_iterations']})",
                    "error": error_msg,
                })
                state = await self._fix_code(state)
                if state.get("error"):
                    yield _sse("gen_error", {"message": state["error"]})
                    return
                continue
            state["compile_error"] = None

            if state.get("sample_dataset") is not None:
                test_result = await self._tools.execute_signal(
                    state["generated_code"] or "",
                    state["sample_dataset"],
                    configurable_args=state.get("configurable_args") or {},
                )
                state["test_result"] = test_result
                if test_result.get("status") != "completed":
                    err = test_result.get("error_message", "execution failed")
                    state["fix_history"].append({"iteration": i + 1, "error_type": "runtime", "error_message": err})
                    yield _sse("gen_progress", {
                        "phase": "fixing_runtime",
                        "pct": pct,
                        "iteration": i + 1,
                        "message": f"Test failed — fixing (attempt {i + 1}/{state['max_iterations']})",
                        "error": err,
                    })
                    state = await self._fix_code(state)
                    if state.get("error"):
                        yield _sse("gen_error", {"message": state["error"]})
                        return
                    continue

            # All checks passed
            state["final_code"] = state["generated_code"]
            state["is_complete"] = True
            yield _sse("gen_progress", {"phase": "tests_passed", "pct": 75, "iteration": i + 1})
            break

        state["iterations_used"] = state["iteration"]
        if not state.get("is_complete"):
            state["final_code"] = state.get("generated_code")
            yield _sse("gen_warning", {
                "message": f"Could not fully pass tests after {state['max_iterations']} attempts — returning best effort code"
            })

        yield _sse("gen_progress", {"phase": "finalizing", "pct": 80, "message": "Detecting SSF mapping…"})
        state = self._detect_ssf(state)

        yield _sse("gen_progress", {"phase": "args_schema", "pct": 88, "message": "Extracting configurable args…"})
        state = await self._generate_args_schema(state)

        yield _sse("gen_progress", {"phase": "naming", "pct": 94, "message": "Generating name and description…"})
        state = await self._suggest_name(state)

        yield _sse("gen_complete", {
            "final_code": state.get("final_code"),
            "signal_name_suggestion": state.get("signal_name_suggestion"),
            "signal_description_suggestion": state.get("signal_description_suggestion"),
            "signal_args_schema": state.get("signal_args_schema"),
            "ssf_mapping": state.get("ssf_mapping"),
            "iterations_used": state.get("iterations_used", 0),
            "is_complete": state.get("is_complete", False),
        })

    # ──────────────────────────────────────────────────────────────────────────
    # LLM call
    # ──────────────────────────────────────────────────────────────────────────

    async def _llm_complete(self, system: str, user: str, max_tokens: int = 4000) -> str:
        """Single LLM completion call. Logs every call. Raises with context on failure."""
        provider_url = (
            getattr(self._config, "provider_base_url", None)
            or getattr(self._settings, "ai_provider_url", None)
        )
        api_key = (
            getattr(self._config, "api_key", None)
            or getattr(self._settings, "ai_api_key", None)
        )
        model = (
            getattr(self._config, "model_id", None)
            or getattr(self._settings, "ai_model", "gpt-4o")
        )
        temperature = float(
            getattr(
                self._config,
                "temperature",
                getattr(self._settings, "ai_temperature", 0.2),
            )
        )
        if str(model).lower().startswith("gpt-5"):
            # GPT-5 family models on the configured provider reject low temperatures.
            temperature = 1.0

        if not provider_url or not api_key:
            raise RuntimeError(
                "LLM not configured — set ai_api_key + ai_provider_url in settings or agent config"
            )

        _logger.debug(
            "signal_gen.llm_call",
            extra={"model": model, "max_tokens": max_tokens, "system_len": len(system)},
        )

        payload: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{provider_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if not resp.is_success:
                _logger.error(
                    "signal_gen.llm_http_error",
                    extra={"status": resp.status_code, "body": resp.text[:500]},
                )
            resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            end = -1 if lines[-1].strip() == "```" else len(lines)
            content = "\n".join(lines[1:end])
        return content.strip()

    # ──────────────────────────────────────────────────────────────────────────
    # Graph nodes
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_code(self, state: SignalGenState) -> SignalGenState:
        """Generate initial signal code from prompt + dataset schema + connector examples."""
        connector = state.get("connector_type", "")
        examples = CONNECTOR_EXAMPLES.get(connector) or CONNECTOR_EXAMPLES.get("aws_iam", [])
        examples_str = "\n\n".join(
            f"### Example: {ex['name']}\n```python\n{ex['code']}\n```"
            for ex in examples[:2]
        )
        schema_str = json.dumps(state.get("dataset_schema") or {}, indent=2)

        # If spec-driven mode, inject detection_logic from the spec
        spec = state.get("signal_spec")
        extra_context = ""
        if spec:
            extra_context = (
                f"\n\nDetection logic to implement:\n{spec.get('detection_logic', '')}\n"
                f"\nConfigurable args required: {json.dumps(spec.get('configurable_args', []))}"
            )

        system = SIGNAL_SYSTEM_PROMPT.format(
            dataset_schema=schema_str,
            connector_type=connector or "unknown",
            examples=examples_str,
        )
        user = (
            f"Generate a Python signal function for: {state.get('prompt', 'compliance check')}"
            f"{extra_context}\n\nReturn ONLY the Python code, no explanation."
        )

        try:
            response = await self._llm_complete(system, user, max_tokens=2000)
            state["generated_code"] = _extract_code(response)
        except Exception as exc:
            _logger.error("signal_gen.generate_failed", extra={"error": str(exc)})
            state["error"] = f"Code generation failed: {exc}"

        return state

    async def _fix_code(self, state: SignalGenState) -> SignalGenState:
        """Fix code based on compile or runtime error, using full fix history for context."""
        compile_err = state.get("compile_error")
        test_err = (state.get("test_result") or {}).get("error_message", "")
        error_type = "compile" if compile_err else "runtime"
        error_message = compile_err or test_err or "Unknown error"

        fix_history_str = "\n".join(
            f"  Attempt {h['iteration']}: [{h['error_type']}] {h['error_message']}"
            for h in (state.get("fix_history") or [])[-3:]  # last 3 only
        ) or "  (none)"

        user = SIGNAL_FIX_PROMPT.format(
            error_type=error_type,
            error_message=error_message,
            failing_code=state.get("generated_code") or "",
            fix_history=fix_history_str,
        )
        system = "You are fixing a Python signal function. Return ONLY the corrected Python code — no markdown fences, no explanation."

        try:
            response = await self._llm_complete(system, user, max_tokens=2000)
            state["generated_code"] = _extract_code(response)
        except Exception as exc:
            _logger.error("signal_gen.fix_failed", extra={"error": str(exc)})
            state["error"] = f"Code fix failed: {exc}"

        return state

    async def _suggest_name(self, state: SignalGenState) -> SignalGenState:
        """Suggest a display name and description for the signal."""
        code = state.get("final_code") or state.get("generated_code")
        if not code:
            return state
        user = SIGNAL_NAME_PROMPT.format(
            prompt=state.get("prompt", ""),
            code=code,
        )
        try:
            response = await self._llm_complete(
                "Return ONLY valid JSON — no markdown fences.",
                user,
                max_tokens=256,
            )
            parsed = json.loads(response)
            state["signal_name_suggestion"] = parsed.get("name", "")
            state["signal_description_suggestion"] = parsed.get("description", "")
        except Exception:
            # Non-critical — leave empty
            state.setdefault("signal_name_suggestion", "")
            state.setdefault("signal_description_suggestion", "")
        return state

    async def _generate_args_schema(self, state: SignalGenState) -> SignalGenState:
        """Extract named kwargs from generated code and produce signal_args_schema."""
        code = state.get("final_code") or state.get("generated_code")
        if not code:
            state["signal_args_schema"] = []
            return state
        user = SIGNAL_ARGS_SCHEMA_PROMPT.format(code=code)
        try:
            response = await self._llm_complete(
                "Return ONLY a JSON array — no markdown fences, no explanation.",
                user,
                max_tokens=512,
            )
            state["signal_args_schema"] = json.loads(response)
        except Exception:
            state["signal_args_schema"] = []
        return state

    @staticmethod
    def _detect_ssf(state: SignalGenState) -> SignalGenState:
        """Keyword heuristic: map signal to CAEP/RISC event type. Non-LLM, instant."""
        prompt_lower = (state.get("prompt") or "").lower()

        caep_keywords: dict[str, str] = {
            "session revok": "session-revoked",
            "credential change": "credential-change",
            "credential rotation": "credential-change",
            "mfa": "assurance-level-change",
            "multi-factor": "assurance-level-change",
            "device compliance": "device-compliance-change",
            "device posture": "device-compliance-change",
            "login": "session-established",
            "session establish": "session-established",
        }
        risc_keywords: dict[str, str] = {
            "password leak": "credential-compromise",
            "credential compromise": "credential-compromise",
            "account disabl": "account-disabled",
            "account deactivat": "account-disabled",
            "recovery activ": "recovery-activated",
        }

        caep_match = next(
            (event for kw, event in caep_keywords.items() if kw in prompt_lower), None
        )
        risc_match = next(
            (event for kw, event in risc_keywords.items() if kw in prompt_lower), None
        ) if not caep_match else None

        connector = (state.get("connector_type") or "unknown").lower()
        signal_slug = re.sub(r"[^a-z0-9-]", "-", (state.get("prompt") or "signal")[:60].lower()).strip("-")
        custom_uri = f"https://kcontrol.io/events/sandbox/{connector}/{signal_slug}" if not caep_match and not risc_match else None

        state["caep_event_type"] = caep_match
        state["risc_event_type"] = risc_match
        state["custom_event_uri"] = custom_uri
        state["ssf_mapping"] = {
            "standard": "caep" if caep_match else "risc" if risc_match else "custom",
            "event_type": caep_match or risc_match,
            "event_uri": (
                f"https://schemas.openid.net/secevent/caep/event-type/{caep_match}" if caep_match
                else f"https://schemas.openid.net/secevent/risc/event-type/{risc_match}" if risc_match
                else None
            ),
            "custom_event_uri": custom_uri,
            "signal_severity": "medium",
            "subject_type": "repository" if connector == "github" else "user",
        }
        return state


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _extract_code(response: str) -> str:
    """Extract Python code block from LLM response, stripping markdown fences."""
    if "```python" in response:
        return response.split("```python")[1].split("```")[0].strip()
    if "```" in response:
        return response.split("```")[1].split("```")[0].strip()
    return response.strip()
