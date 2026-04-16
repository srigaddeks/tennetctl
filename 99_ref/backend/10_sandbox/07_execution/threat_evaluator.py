from __future__ import annotations


def evaluate_threat(
    expression: dict, signal_results: dict[str, str],
) -> tuple[bool, list[dict]]:
    """
    Evaluate expression tree against signal results.

    Args:
        expression: Threat type expression tree (AND/OR/NOT of signal conditions).
        signal_results: Map of signal_code -> result_code ("pass"|"fail"|"warning").

    Returns:
        Tuple of (is_triggered, evaluation_trace).
    """
    trace: list[dict] = []
    result = _eval_node(expression, signal_results, trace)
    return result, trace


def _eval_node(node: dict, signal_results: dict[str, str], trace: list[dict]) -> bool:
    """Recursively evaluate an expression tree node."""

    # Leaf node: check a single signal result
    if "signal_code" in node:
        actual = signal_results.get(node["signal_code"])
        expected = node["expected_result"]
        matched = actual == expected
        trace.append({
            "signal_code": node["signal_code"],
            "expected": expected,
            "actual": actual,
            "matched": matched,
        })
        return matched

    # Branch node: combine child results with operator
    op = node.get("operator", "AND")
    conditions = node.get("conditions", [])
    results = [_eval_node(c, signal_results, trace) for c in conditions]

    if op == "AND":
        result = all(results)
    elif op == "OR":
        result = any(results)
    elif op == "NOT":
        result = not results[0] if results else False
    else:
        result = False

    trace.append({
        "operator": op,
        "result": result,
        "child_count": len(results),
    })
    return result
