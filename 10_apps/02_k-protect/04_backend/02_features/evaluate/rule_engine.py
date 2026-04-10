"""kprotect rule engine.

Evaluates structured JSON policy conditions against an evaluation context.
Pure computation — no I/O, no side effects, no code execution.

Supports operators: ==, !=, >, <, >=, <=, IN, NOT_IN, EXISTS, NOT_EXISTS
Supports condition operators: AND, OR
Supports dot-path field resolution: "device.is_new", "signal_scores.keystroke"
Supports config_key overrides: when a rule has config_key, use org's config override instead of hardcoded value.
"""
from __future__ import annotations

import time
from typing import Any


# Action severity ordering (higher index = more severe)
ACTION_SEVERITY = ["allow", "monitor", "flag", "throttle", "challenge", "block"]


def evaluate_policy(
    conditions: dict[str, Any],
    ctx: dict[str, Any],
    config_overrides: dict[str, Any] | None = None,
) -> tuple[str, str | None, float]:
    """Evaluate a single policy's conditions against the context.

    Args:
        conditions: Structured JSON conditions from kbio predefined policy.
            { "operator": "AND", "rules": [...], "action": "block", "reason_template": "..." }
        ctx: Evaluation context dict with all score data.
        config_overrides: Optional org-specific threshold overrides.

    Returns:
        (action, reason, execution_ms) tuple.
        Returns ("allow", None, ms) if conditions don't match.
    """
    start = time.perf_counter()
    config = config_overrides or {}

    matched = _evaluate_condition_group(conditions, ctx, config)

    elapsed = round((time.perf_counter() - start) * 1000, 4)

    if matched:
        action = conditions.get("action", "allow")
        reason_template = conditions.get("reason_template", "")
        reason = _format_reason(reason_template, ctx)
        return action, reason, elapsed

    return "allow", None, elapsed


def evaluate_policy_set(
    policies: list[dict[str, Any]],
    ctx: dict[str, Any],
    *,
    mode: str = "short_circuit",
) -> tuple[str, list[dict[str, Any]]]:
    """Evaluate a set of policies against the context.

    Args:
        policies: List of policy dicts, each with:
            - code: str
            - conditions: dict (structured JSON)
            - config_overrides: dict | None
            - priority: int (lower = evaluated first, already sorted)
        ctx: Evaluation context.
        mode: "short_circuit" (stop on first block) or "all" (evaluate all).

    Returns:
        (final_action, results_list) where results_list is per-policy details.
    """
    results: list[dict[str, Any]] = []
    highest_action = "allow"

    for policy in policies:
        conditions = policy.get("conditions", {})
        config_overrides = policy.get("config_overrides")

        action, reason, exec_ms = evaluate_policy(conditions, ctx, config_overrides)

        result = {
            "policy_code": policy.get("code", "unknown"),
            "action": action,
            "reason": reason,
            "execution_ms": exec_ms,
        }
        results.append(result)

        # Track highest severity action
        if _action_severity(action) > _action_severity(highest_action):
            highest_action = action

        # Short-circuit: stop on block
        if mode == "short_circuit" and action == "block":
            break

    return highest_action, results


def _evaluate_condition_group(
    group: dict[str, Any],
    ctx: dict[str, Any],
    config: dict[str, Any],
) -> bool:
    """Evaluate an AND/OR group of rules."""
    operator = group.get("operator", "AND")
    rules = group.get("rules", [])

    if not rules:
        return False

    if operator == "AND":
        return all(_evaluate_rule(rule, ctx, config) for rule in rules)
    elif operator == "OR":
        return any(_evaluate_rule(rule, ctx, config) for rule in rules)

    return False


def _evaluate_rule(
    rule: dict[str, Any],
    ctx: dict[str, Any],
    config: dict[str, Any],
) -> bool:
    """Evaluate a single rule against the context."""
    field = rule.get("field", "")
    op = rule.get("op", "==")

    # Resolve the threshold: use config override if config_key is set
    config_key = rule.get("config_key")
    if config_key and config_key in config:
        threshold = config[config_key]
    else:
        threshold = rule.get("value")

    # Resolve field value from context (supports dot paths)
    field_value = _resolve_field(ctx, field)

    return _compare(field_value, op, threshold)


def _resolve_field(ctx: dict[str, Any], path: str) -> Any:
    """Resolve a dot-separated field path from the context dict."""
    parts = path.split(".")
    current: Any = ctx
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    # Auto-unwrap SignalResult to its value
    if isinstance(current, dict) and "value" in current and "confidence" in current:
        return current["value"]
    return current


def _compare(field_value: Any, op: str, threshold: Any) -> bool:
    """Compare a field value against a threshold using the given operator."""
    if op == "EXISTS":
        return field_value is not None
    if op == "NOT_EXISTS":
        return field_value is None

    if field_value is None:
        return False

    try:
        if op == "==":
            return field_value == threshold
        elif op == "!=":
            return field_value != threshold
        elif op == ">":
            return float(field_value) > float(threshold)
        elif op == "<":
            return float(field_value) < float(threshold)
        elif op == ">=":
            return float(field_value) >= float(threshold)
        elif op == "<=":
            return float(field_value) <= float(threshold)
        elif op == "IN":
            if isinstance(threshold, list):
                return field_value in threshold
            return False
        elif op == "NOT_IN":
            if isinstance(threshold, list):
                return field_value not in threshold
            return True
    except (TypeError, ValueError):
        return False

    return False


def _action_severity(action: str) -> int:
    """Get severity index for action comparison."""
    try:
        return ACTION_SEVERITY.index(action)
    except ValueError:
        return 0


def _format_reason(template: str, ctx: dict[str, Any]) -> str:
    """Format a reason template with context values. Safe — ignores missing keys."""
    if not template:
        return ""
    try:
        # Flatten context for simple format substitution
        flat: dict[str, Any] = {}
        for k, v in ctx.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    flat[f"{k}.{k2}"] = v2
            flat[k] = v
        return template.format(**flat)
    except (KeyError, ValueError, IndexError):
        return template
