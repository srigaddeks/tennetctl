"""
Test Dataset Generator Agent
=============================
Autonomous agent that generates shape-preserving test datasets for signals.

Given a signal spec and a source dataset, it:
1. Extracts rich schema from real collected data (types + example values)
2. Generates 15-20 test cases covering all spec test_scenarios + edge cases
3. Runs structural diff validation on each generated case
4. Rejects and regenerates any case that deviates from the real data shape (up to 3 attempts)
5. Returns validated test bundle ready for persistence

Shape preservation is the top priority — the LLM generates VALUES, never changes STRUCTURE.

LangFuse tracing:
  - One root trace per generate_test_bundle() call (keyed by signal_code)
  - One generation span for the initial bundle call
  - One generation span per structural fix attempt
  - Scored with: validated_ratio (0.0–1.0), fix_attempts_total
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods

from .prompts import TEST_DATASET_SYSTEM_PROMPT, STRUCTURAL_DIFF_PROMPT

_llm_utils_mod = import_module("backend.20_ai._llm_utils")
llm_complete = _llm_utils_mod.llm_complete
resolve_llm_config = _llm_utils_mod.resolve_llm_config
parse_json = _llm_utils_mod.parse_json
parse_json_array = _llm_utils_mod.parse_json_array

_logger = get_logger("backend.ai.test_dataset_gen.agent")


def structural_diff(reference_schema: dict, generated_record: dict, path: str = "") -> list[str]:
    """
    Compare generated record against reference schema for structural violations.
    Returns list of violation messages (empty = valid).

    Checks:
    1. Array vs object type at every node
    2. Presence of all required keys at each nesting level
    3. No extra keys added by LLM
    """
    violations = []

    for key, schema_meta in reference_schema.items():
        full_path = f"{path}.{key}" if path else key
        schema_type = schema_meta.get("type", "unknown") if isinstance(schema_meta, dict) else schema_meta

        if key not in generated_record:
            violations.append(f"Missing required key: {full_path}")
            continue

        val = generated_record[key]

        if schema_type == "array":
            if not isinstance(val, list):
                violations.append(f"Expected array at {full_path}, got {type(val).__name__}")
        elif schema_type == "object":
            if not isinstance(val, dict):
                violations.append(f"Expected object at {full_path}, got {type(val).__name__}")

    # Check for extra keys
    for key in generated_record:
        if key not in reference_schema:
            violations.append(f"Extra key not in schema: {path}.{key}" if path else f"Extra key: {key}")

    return violations


@instrument_class_methods(
    namespace="ai.test_dataset_gen.agent",
    logger_name="backend.ai.test_dataset_gen.instrumentation",
)
class TestDatasetAgent:
    """Generates shape-preserving test datasets from signal specs."""

    def __init__(self, *, llm_config, settings, tracer=None) -> None:
        self._config = llm_config
        self._settings = settings
        self._tracer = tracer  # LangFuseTracer instance (or None)

    async def generate_test_bundle(
        self,
        *,
        spec: dict,
        rich_schema: dict,
        num_cases: int = 18,
        job_id: str | None = None,
    ) -> list[dict]:
        """
        Generate a full test bundle. Returns list of validated test cases.
        Each case: {case_id, scenario_name, description, dataset_input, expected_output, configurable_args_override}
        """
        signal_code = spec.get("signal_code", "unknown")
        test_scenarios = spec.get("test_scenarios", [])
        connector_type = spec.get("connector_type_code", "unknown")

        # Always generate more than requested to account for rejections
        target = max(num_cases, len(test_scenarios) + 5)

        # Open root LangFuse trace
        trace = None
        if self._tracer:
            trace = self._tracer.trace(
                name="test_dataset_gen",
                job_id=job_id,
                metadata={
                    "signal_code": signal_code,
                    "connector_type": connector_type,
                    "target_cases": target,
                    "scenario_count": len(test_scenarios),
                },
                tags=["test_dataset_gen", connector_type],
            )

        system = TEST_DATASET_SYSTEM_PROMPT.format(
            spec=json.dumps(spec, indent=2),
            rich_schema=json.dumps(rich_schema, indent=2),
            num_cases=target,
            test_scenarios=json.dumps(test_scenarios, indent=2),
        )

        _logger.info(
            "test_dataset_gen.generating",
            extra={"signal_code": signal_code, "num_cases": target},
        )

        provider_url, api_key, model = resolve_llm_config(self._config, self._settings)

        raw = await llm_complete(
            provider_url=provider_url,
            api_key=api_key,
            model=model,
            system=system,
            user=f"Generate {target} test cases for a {connector_type} signal.",
            max_tokens=8000,
            temperature=1.0,
            timeout=180.0,
            tracer=self._tracer,
            trace=trace,
            generation_name="generate_bundle",
            generation_metadata={
                "signal_code": signal_code,
                "target_cases": target,
            },
        )

        try:
            cases = parse_json_array(raw)
        except Exception as exc:
            _logger.error("test_dataset_gen.parse_failed: %s", exc)
            if self._tracer and trace:
                self._tracer.event(trace, name="parse_failed", level="ERROR",
                                   metadata={"error": str(exc)[:500]})
            raise ValueError(f"Failed to parse test cases: {exc}") from exc

        # Validate + fix each case
        validated = []
        total_fix_attempts = 0

        for i, case in enumerate(cases):
            dataset_input = case.get("dataset_input", {})
            violations = structural_diff(rich_schema, dataset_input)

            if not violations:
                validated.append(case)
                continue

            # Attempt structural fix (up to 3 times)
            fixed_input = dataset_input
            fixed = False
            for attempt in range(3):
                total_fix_attempts += 1
                _logger.debug(
                    "test_dataset_gen.fixing_structure",
                    extra={"case_index": i, "attempt": attempt + 1, "violations": violations},
                )
                if self._tracer and trace:
                    self._tracer.event(
                        trace,
                        name="structural_fix_attempt",
                        level="WARNING",
                        metadata={
                            "case_index": i,
                            "attempt": attempt + 1,
                            "violations": violations[:5],
                            "case_scenario": case.get("scenario_name", ""),
                        },
                    )
                try:
                    fix_system = STRUCTURAL_DIFF_PROMPT.format(
                        rich_schema=json.dumps(rich_schema, indent=2),
                        broken_input=json.dumps(fixed_input, indent=2),
                        violations="\n".join(violations),
                    )
                    fix_raw = await llm_complete(
                        provider_url=provider_url,
                        api_key=api_key,
                        model=model,
                        system=fix_system,
                        user="Fix the structural violations.",
                        max_tokens=2000,
                        temperature=1.0,
                        tracer=self._tracer,
                        trace=trace,
                        generation_name=f"fix_structure_case_{i}_attempt_{attempt + 1}",
                        generation_metadata={
                            "case_index": i,
                            "attempt": attempt + 1,
                            "violation_count": len(violations),
                        },
                    )
                    fixed_input = parse_json(fix_raw)
                    violations = structural_diff(rich_schema, fixed_input)
                    if not violations:
                        case["dataset_input"] = fixed_input
                        validated.append(case)
                        fixed = True
                        break
                except Exception as fix_exc:
                    _logger.warning("test_dataset_gen.fix_attempt_failed: %s", fix_exc)

            if not fixed:
                _logger.warning(
                    "test_dataset_gen.case_rejected",
                    extra={"case_index": i, "violations": violations},
                )
                if self._tracer and trace:
                    self._tracer.event(
                        trace,
                        name="case_rejected",
                        level="WARNING",
                        metadata={
                            "case_index": i,
                            "violations": violations[:5],
                            "scenario": case.get("scenario_name", ""),
                        },
                    )

        validated_ratio = len(validated) / max(len(cases), 1)

        _logger.info(
            "test_dataset_gen.complete",
            extra={
                "total": len(cases),
                "validated": len(validated),
                "rejected": len(cases) - len(validated),
                "fix_attempts": total_fix_attempts,
            },
        )

        # Score the trace
        if self._tracer and trace:
            self._tracer.score(trace, name="validated_ratio", value=validated_ratio,
                               comment=f"{len(validated)}/{len(cases)} cases validated")
            self._tracer.event(
                trace,
                name="generation_complete",
                metadata={
                    "total_generated": len(cases),
                    "validated": len(validated),
                    "rejected": len(cases) - len(validated),
                    "total_fix_attempts": total_fix_attempts,
                },
            )

        return validated
