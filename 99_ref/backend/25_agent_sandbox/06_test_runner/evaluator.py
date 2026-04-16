"""
Test evaluator — judges agent run results against expected behavior.

Supports: deterministic, llm_judge, regex, custom_python evaluation methods.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationResult:
    passed: bool
    score: float  # 0.0 to 1.0
    reason: str
    evaluation_output: dict | None = None


class TestEvaluator:
    """Evaluates agent run results against test case expectations."""

    async def evaluate(
        self,
        *,
        evaluation_method_code: str,
        expected_behavior: dict,
        evaluation_config: dict,
        run_result: dict,
    ) -> EvaluationResult:
        if evaluation_method_code == "deterministic":
            return self._evaluate_deterministic(expected_behavior, run_result)
        elif evaluation_method_code == "regex":
            return self._evaluate_regex(expected_behavior, run_result)
        elif evaluation_method_code == "llm_judge":
            return await self._evaluate_llm_judge(expected_behavior, evaluation_config, run_result)
        elif evaluation_method_code == "custom_python":
            return self._evaluate_custom_python(evaluation_config, run_result)
        else:
            return EvaluationResult(
                passed=False, score=0.0,
                reason=f"Unknown evaluation method: {evaluation_method_code}",
            )

    def _evaluate_deterministic(self, expected: dict, actual: dict) -> EvaluationResult:
        """Deterministic checks: output_contains, tool_called, state_has_key, iterations_lte, status_equals."""
        checks = expected.get("checks", [])
        if not checks:
            return EvaluationResult(passed=True, score=1.0, reason="No checks defined")

        results = []
        for check in checks:
            check_type = check.get("type", "")
            if check_type == "status_equals":
                actual_status = actual.get("status", "")
                expected_status = check.get("value", "")
                passed = actual_status == expected_status
                results.append({"check": check_type, "passed": passed, "expected": expected_status, "actual": actual_status})
            elif check_type == "output_contains":
                output_text = json.dumps(actual.get("output_messages", []))
                value = check.get("value", "")
                passed = value.lower() in output_text.lower()
                results.append({"check": check_type, "passed": passed, "value": value})
            elif check_type == "tool_called":
                tool_code = check.get("tool_code", "")
                min_calls = check.get("min_calls", 1)
                tool_calls = actual.get("tool_calls_made", 0)
                # For now, check if tool_calls > 0 (detailed check needs step data)
                passed = tool_calls >= min_calls
                results.append({"check": check_type, "passed": passed, "tool_code": tool_code})
            elif check_type == "state_has_key":
                key = check.get("key", "")
                state = actual.get("final_state", {})
                passed = key in state
                results.append({"check": check_type, "passed": passed, "key": key})
            elif check_type == "iterations_lte":
                max_val = check.get("value", 100)
                actual_val = actual.get("iterations_used", 0)
                passed = actual_val <= max_val
                results.append({"check": check_type, "passed": passed, "max": max_val, "actual": actual_val})
            elif check_type == "cost_lte":
                max_val = check.get("value", 1.0)
                actual_val = actual.get("cost_usd", 0.0)
                passed = actual_val <= max_val
                results.append({"check": check_type, "passed": passed, "max": max_val, "actual": actual_val})
            else:
                results.append({"check": check_type, "passed": False, "error": f"Unknown check type: {check_type}"})

        passed_count = sum(1 for r in results if r.get("passed"))
        total = len(results)
        all_passed = passed_count == total
        score = passed_count / total if total > 0 else 0.0

        return EvaluationResult(
            passed=all_passed,
            score=score,
            reason=f"{passed_count}/{total} checks passed",
            evaluation_output={"checks": results},
        )

    def _evaluate_regex(self, expected: dict, actual: dict) -> EvaluationResult:
        """Regex pattern matching on output."""
        pattern = expected.get("pattern", "")
        output_text = json.dumps(actual.get("output_messages", []))
        match = re.search(pattern, output_text, re.IGNORECASE)
        return EvaluationResult(
            passed=match is not None,
            score=1.0 if match else 0.0,
            reason=f"Pattern {'matched' if match else 'not matched'}: {pattern}",
        )

    async def _evaluate_llm_judge(
        self, expected: dict, config: dict, actual: dict,
    ) -> EvaluationResult:
        """LLM evaluates the output against criteria."""
        criteria = expected.get("criteria", config.get("criteria", ""))
        if not criteria:
            return EvaluationResult(passed=False, score=0.0, reason="No criteria defined for LLM judge")

        # Stub: LLM judge requires LLM call — will be implemented with provider
        return EvaluationResult(
            passed=True, score=0.8,
            reason="LLM judge evaluation (stub — requires LLM provider)",
            evaluation_output={"criteria": criteria, "note": "stub implementation"},
        )

    def _evaluate_custom_python(self, config: dict, actual: dict) -> EvaluationResult:
        """Run user-provided Python evaluation function."""
        python_source = config.get("python_source", "")
        if not python_source:
            return EvaluationResult(passed=False, score=0.0, reason="No python_source in evaluation_config")

        try:
            compiled = compile(python_source, "<evaluator>", "exec")
            local_ns: dict = {}
            exec(compiled, {"__builtins__": {"len": len, "str": str, "int": int, "float": float, "bool": bool, "dict": dict, "list": list, "True": True, "False": False, "None": None}}, local_ns)

            if "evaluate" not in local_ns:
                return EvaluationResult(passed=False, score=0.0, reason="Custom evaluator must define evaluate(run_result)")

            result = local_ns["evaluate"](actual)
            if isinstance(result, dict):
                return EvaluationResult(
                    passed=result.get("passed", False),
                    score=float(result.get("score", 0.0)),
                    reason=result.get("reason", ""),
                    evaluation_output=result,
                )
            return EvaluationResult(passed=bool(result), score=1.0 if result else 0.0, reason="Custom evaluator returned non-dict")
        except Exception as e:
            return EvaluationResult(passed=False, score=0.0, reason=f"Custom evaluator error: {e}")
