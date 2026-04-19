"""
Eligibility rule evaluator. Tiny JSONB AST interpreter — no DSL parsing,
no string templating, no eval(). The contract is:

    rule:
      Leaf:    {"op": "eq"|"ne"|"gt"|"gte"|"lt"|"lte"|"in"|"nin"|"exists",
                 "field": "visitor.country", "value": <literal>}
      Compound: {"op": "all"|"any", "rules": [<rule>, ...]}
      Negation: {"op": "not", "rule": <rule>}
      True:     {} (empty rule = always true)

    context:
      Plain dict, e.g. {"visitor": {"country": "US", "plan": "free", ...},
                        "order":   {"total_cents": 5000, "skus": ["A","B"]},
                        "promo":   {"code": "..."}}

    Field paths use dot notation: "visitor.country" → context["visitor"]["country"].

Used by:
  - product_ops.promos.service.redeem (promo.eligibility)
  - product_ops.campaigns.service.pick_promo (campaign.audience_rule)
  - any future caller that needs rule eval
"""

from __future__ import annotations

from typing import Any

# Unwrap into base ops the evaluator natively supports
_LEAF_OPS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "nin", "exists"}
_COMPOUND_OPS = {"all", "any"}


def _resolve(context: dict, dotted_path: str) -> Any:
    """Walk a dot path through nested dicts. Missing key returns _MISSING sentinel."""
    cur: Any = context
    for part in dotted_path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return _MISSING
    return cur


class _Missing:
    def __repr__(self) -> str:  # pragma: no cover
        return "<missing>"


_MISSING = _Missing()


def evaluate(rule: dict | None, context: dict) -> bool:
    """
    Evaluate `rule` against `context`. Empty / None rule = True (no constraint).

    Returns True if the rule is satisfied; False otherwise. Malformed rules
    are treated as False (fail-closed).
    """
    if not rule:
        return True
    op = rule.get("op")
    if op is None:
        # Empty dict already handled above; lone {"op": ...} with nothing else is malformed.
        return False

    if op in _COMPOUND_OPS:
        children = rule.get("rules") or []
        if not isinstance(children, list):
            return False
        if op == "all":
            return all(evaluate(r, context) for r in children)
        return any(evaluate(r, context) for r in children)

    if op == "not":
        inner = rule.get("rule")
        if not isinstance(inner, dict):
            return False
        return not evaluate(inner, context)

    if op not in _LEAF_OPS:
        return False

    field = rule.get("field")
    if not isinstance(field, str):
        return False
    value = rule.get("value")
    actual = _resolve(context, field)

    if op == "exists":
        return actual is not _MISSING

    if actual is _MISSING:
        return False

    if op == "eq":
        return actual == value
    if op == "ne":
        return actual != value
    if op == "in":
        return _maybe_iter_contains(value, actual)
    if op == "nin":
        return not _maybe_iter_contains(value, actual)

    # Numeric comparisons. Coerce strings only when both sides cleanly cast.
    try:
        a = _to_num(actual)
        b = _to_num(value)
    except (TypeError, ValueError):
        return False
    if op == "gt":
        return a > b
    if op == "gte":
        return a >= b
    if op == "lt":
        return a < b
    if op == "lte":
        return a <= b

    return False


def _maybe_iter_contains(haystack: Any, needle: Any) -> bool:
    if not isinstance(haystack, (list, tuple, set)):
        return False
    return needle in haystack


def _to_num(v: Any) -> float:
    if isinstance(v, bool):
        # Reject booleans — too easy to coerce to 0/1 by accident in JSONB
        raise ValueError("bool not numeric")
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        return float(v)
    raise TypeError(f"not numeric: {type(v).__name__}")


# ── Convenience: build a context from caller-supplied bits ─────────

def build_context(
    *,
    visitor: dict | None = None,
    order: dict | None = None,
    promo: dict | None = None,
    extra: dict | None = None,
) -> dict:
    ctx: dict[str, Any] = {}
    if visitor is not None:
        ctx["visitor"] = visitor
    if order is not None:
        ctx["order"] = order
    if promo is not None:
        ctx["promo"] = promo
    if extra:
        ctx.update(extra)
    return ctx
