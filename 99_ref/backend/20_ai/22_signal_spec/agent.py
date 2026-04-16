"""
Signal Specification Agent
==========================
Interactive streaming LLM agent for designing signal specifications.

Flow:
  stream_generate()  — user describes a signal idea → AI builds full spec + feasibility in one pass
  stream_refine()    — user sends a refinement message → AI updates spec + re-runs feasibility
  check_feasibility() — standalone feasibility check (sync, returns dict)

All streaming methods yield SSE-formatted strings (same pattern as FrameworkBuilderAgent).

SSE events emitted:
  spec_analyzing         — Starting analysis
  spec_field_identified  — Each real field discovered in dataset
  spec_section_ready     — Each spec section as it is built
  spec_complete          — Full spec ready (with feasibility result)
  feasibility_checking   — Starting feasibility check
  feasibility_result     — Gate result (feasible | partial | infeasible)
  spec_refined           — After a refine cycle
  error                  — Any failure

LangFuse tracing:
  Each agent instance can hold a tracer + root trace.
  All LLM calls are wrapped in generation spans.
  Feasibility gate results are logged as scored events.
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import AsyncGenerator

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods

from .prompts import SPEC_SYSTEM_PROMPT, REFINE_SYSTEM_PROMPT, FEASIBILITY_SYSTEM_PROMPT

_llm_utils_mod = import_module("backend.20_ai._llm_utils")
llm_complete = _llm_utils_mod.llm_complete
llm_complete_with_history = _llm_utils_mod.llm_complete_with_history
resolve_llm_config = _llm_utils_mod.resolve_llm_config
parse_json = _llm_utils_mod.parse_json

_logger = get_logger("backend.ai.signal_spec.agent")


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@instrument_class_methods(
    namespace="ai.signal_spec.agent",
    logger_name="backend.ai.signal_spec.instrumentation",
)
class SignalSpecAgent:
    """Interactive streaming signal specification agent with feasibility gate."""

    def __init__(self, *, llm_config, settings, tracer=None) -> None:
        self._config = llm_config
        self._settings = settings
        self._tracer = tracer  # LangFuseTracer instance (or None)

    # ── Public streaming entry points ──────────────────────────────────────────

    async def stream_generate(
        self,
        *,
        prompt: str,
        connector_type_code: str,
        rich_schema: dict,
        session_id: str | None = None,
        user_id: str | None = None,
        dataset_records: list[dict] | None = None,
        record_names: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a fresh signal spec from a user prompt."""
        yield _sse("spec_analyzing", {"message": "Analysing dataset schema...", "pct": 5})

        # Emit identified fields
        field_count = 0
        for field_path, meta in list(rich_schema.items())[:20]:
            field_count += 1
            yield _sse("spec_field_identified", {
                "field_path": field_path,
                "type": meta.get("type", "unknown"),
                "example": meta.get("example"),
                "pct": min(5 + field_count * 2, 25),
            })

        yield _sse("spec_analyzing", {"message": "Building signal specification...", "pct": 30})

        # Build dataset records context
        dataset_records_str = "(No dataset records available)"
        if dataset_records and record_names:
            parts = []
            for rec, name in zip(dataset_records[:15], record_names[:15]):
                rec_json = json.dumps(rec, indent=2, default=str)[:2000]
                parts.append(f"--- {name} ---\n{rec_json}")
            dataset_records_str = "\n\n".join(parts)

        system = SPEC_SYSTEM_PROMPT.format(
            connector_type_code=connector_type_code,
            rich_schema=json.dumps(rich_schema, indent=2),
            dataset_records_with_names=dataset_records_str,
        )

        # Open root LangFuse trace for this session
        trace = None
        if self._tracer:
            trace = self._tracer.trace(
                name="signal_spec.generate",
                session_id=session_id,
                user_id=user_id,
                metadata={
                    "connector_type_code": connector_type_code,
                    "field_count": len(rich_schema),
                },
                tags=["signal_spec", "generate"],
            )

        provider_url, api_key, model = resolve_llm_config(self._config, self._settings)

        try:
            raw = await llm_complete(
                provider_url=provider_url,
                api_key=api_key,
                model=model,
                system=system,
                user=prompt,
                max_tokens=4096,

                tracer=self._tracer,
                trace=trace,
                generation_name="spec_generate",
                generation_metadata={"session_id": session_id, "connector": connector_type_code},
            )
            spec = parse_json(raw)
        except Exception as exc:
            _logger.exception("signal_spec.generate_failed: %s", exc)
            if self._tracer and trace:
                self._tracer.event(trace, name="generate_failed", level="ERROR",
                                   metadata={"error": str(exc)[:500]})
            yield _sse("error", {"message": f"Failed to generate spec: {exc}"})
            return

        # Handle clarification requests from the LLM
        if spec.get("type") == "clarification_needed":
            if self._tracer and trace:
                self._tracer.event(trace, name="clarification_needed",
                                   metadata={"questions": spec.get("questions", [])})
            yield _sse("clarification_needed", {
                "questions": spec.get("questions", []),
                "message": "The AI needs more information to build the spec.",
            })
            return

        # Emit per-section progress
        sections = [
            ("signal_code", "Signal code"),
            ("display_name", "Display name"),
            ("detection_logic", "Detection logic"),
            ("configurable_args", "Configurable arguments"),
            ("test_scenarios", "Test scenarios"),
            ("ssf_mapping", "SSF mapping"),
        ]
        for key, label in sections:
            if key in spec:
                yield _sse("spec_section_ready", {"section": key, "value": spec[key], "label": label})

        yield _sse("feasibility_checking", {"message": "Checking implementability against dataset..."})

        feasibility = spec.get("feasibility") or await self._check_feasibility_llm(
            fields_used=spec.get("dataset_fields_used", []),
            rich_schema=rich_schema,
            trace=trace,
        )
        spec["feasibility"] = feasibility

        # Score the trace with feasibility confidence
        if self._tracer and trace:
            confidence_score = {"high": 1.0, "medium": 0.6, "low": 0.2}.get(
                feasibility.get("confidence", "low"), 0.2
            )
            feasibility_score = {"feasible": 1.0, "partial": 0.5, "infeasible": 0.0}.get(
                feasibility.get("status", "infeasible"), 0.0
            )
            self._tracer.score(trace, name="feasibility", value=feasibility_score,
                               comment=feasibility.get("status"))
            self._tracer.score(trace, name="confidence", value=confidence_score,
                               comment=feasibility.get("confidence"))

        yield _sse("feasibility_result", {
            "status": feasibility.get("status", "unknown"),
            "confidence": feasibility.get("confidence", "low"),
            "missing_fields": feasibility.get("missing_fields", []),
            "blocking_issues": feasibility.get("blocking_issues", []),
            "notes": feasibility.get("notes", ""),
        })

        yield _sse("spec_complete", {"spec": spec})

    async def stream_refine(
        self,
        *,
        message: str,
        current_spec: dict,
        connector_type_code: str,
        rich_schema: dict,
        conversation_history: list,
        session_id: str | None = None,
        user_id: str | None = None,
        dataset_records: list[dict] | None = None,
        record_names: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Refine an existing spec based on user feedback."""
        yield _sse("spec_analyzing", {"message": "Applying your changes...", "pct": 10})

        # Build dataset records context
        dataset_records_str = "(No dataset records available)"
        if dataset_records and record_names:
            parts = []
            for rec, name in zip(dataset_records[:15], record_names[:15]):
                rec_json = json.dumps(rec, indent=2, default=str)[:2000]
                parts.append(f"--- {name} ---\n{rec_json}")
            dataset_records_str = "\n\n".join(parts)

        system = REFINE_SYSTEM_PROMPT.format(
            current_spec=json.dumps(current_spec, indent=2),
            rich_schema=json.dumps(rich_schema, indent=2),
            dataset_records_with_names=dataset_records_str,
        )

        # Build conversation context
        messages = []
        for turn in conversation_history[-10:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": message})

        # Open LangFuse trace
        trace = None
        if self._tracer:
            trace = self._tracer.trace(
                name="signal_spec.refine",
                session_id=session_id,
                user_id=user_id,
                metadata={
                    "connector_type_code": connector_type_code,
                    "turn_count": len(conversation_history),
                    "message_preview": message[:100],
                },
                tags=["signal_spec", "refine"],
            )

        provider_url, api_key, model = resolve_llm_config(self._config, self._settings)

        try:
            raw = await llm_complete_with_history(
                provider_url=provider_url,
                api_key=api_key,
                model=model,
                system=system,
                messages=messages,
                max_tokens=4096,

                tracer=self._tracer,
                trace=trace,
                generation_name="spec_refine",
                generation_metadata={"session_id": session_id, "turn": len(conversation_history)},
            )
            updated_spec = parse_json(raw)
        except Exception as exc:
            _logger.exception("signal_spec.refine_failed: %s", exc)
            if self._tracer and trace:
                self._tracer.event(trace, name="refine_failed", level="ERROR",
                                   metadata={"error": str(exc)[:500]})
            yield _sse("error", {"message": f"Failed to refine spec: {exc}"})
            return

        # Handle clarification requests
        if updated_spec.get("type") == "clarification_needed":
            yield _sse("clarification_needed", {
                "questions": updated_spec.get("questions", []),
                "message": "The AI needs clarification before applying changes.",
            })
            return

        yield _sse("feasibility_checking", {"message": "Re-checking implementability..."})

        feasibility = updated_spec.get("feasibility") or await self._check_feasibility_llm(
            fields_used=updated_spec.get("dataset_fields_used", []),
            rich_schema=rich_schema,
            trace=trace,
        )
        updated_spec["feasibility"] = feasibility

        if self._tracer and trace:
            feasibility_score = {"feasible": 1.0, "partial": 0.5, "infeasible": 0.0}.get(
                feasibility.get("status", "infeasible"), 0.0
            )
            self._tracer.score(trace, name="feasibility", value=feasibility_score)

        yield _sse("feasibility_result", {
            "status": feasibility.get("status", "unknown"),
            "confidence": feasibility.get("confidence", "low"),
            "missing_fields": feasibility.get("missing_fields", []),
            "blocking_issues": feasibility.get("blocking_issues", []),
            "notes": feasibility.get("notes", ""),
        })

        yield _sse("spec_refined", {"spec": updated_spec, "message": message})

    async def check_feasibility(
        self,
        *,
        fields_used: list[dict],
        rich_schema: dict,
        dataset_records: list[dict] | None = None,
        record_names: list[str] | None = None,
    ) -> dict:
        """Standalone feasibility check. Returns feasibility dict."""
        return await self._check_feasibility_llm(
            fields_used=fields_used,
            rich_schema=rich_schema,
            dataset_records=dataset_records,
            record_names=record_names,
            trace=None,
        )

    # ── Internal LLM helpers ───────────────────────────────────────────────────

    async def _check_feasibility_llm(
        self,
        *,
        fields_used: list[dict],
        rich_schema: dict,
        dataset_records: list[dict] | None = None,
        record_names: list[str] | None = None,
        trace=None,
    ) -> dict:
        # Build dataset records context
        dataset_records_str = "(No records available for verification)"
        if dataset_records and record_names:
            parts = []
            for rec, name in zip(dataset_records[:10], record_names[:10]):
                rec_json = json.dumps(rec, indent=2, default=str)[:1500]
                parts.append(f"--- {name} ---\n{rec_json}")
            dataset_records_str = "\n\n".join(parts)

        system = FEASIBILITY_SYSTEM_PROMPT.format(
            fields_used=json.dumps(fields_used, indent=2),
            rich_schema=json.dumps(rich_schema, indent=2),
            dataset_records_with_names=dataset_records_str,
        )

        provider_url, api_key, model = resolve_llm_config(self._config, self._settings)

        try:
            raw = await llm_complete(
                provider_url=provider_url,
                api_key=api_key,
                model=model,
                system=system,
                user="Check feasibility now.",
                max_tokens=1024,

                tracer=self._tracer,
                trace=trace,
                generation_name="feasibility_check",
                generation_metadata={"fields_count": len(fields_used)},
            )
            return parse_json(raw)
        except Exception as exc:
            _logger.warning("signal_spec.feasibility_failed: %s", exc)
            return {
                "status": "infeasible",
                "confidence": "low",
                "missing_fields": [],
                "blocking_issues": [f"Feasibility check failed: {exc}"],
                "notes": "Could not determine feasibility",
            }
