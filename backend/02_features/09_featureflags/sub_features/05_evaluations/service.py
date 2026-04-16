"""
featureflags.evaluations — the evaluation engine.

Given (flag_key, environment, context), picks the most-specific flag by scope,
resolves overrides → rules → defaults in that precedence order, and returns
{value, reason, ...trace fields}.

No writes, no audit (reads are not auditable in v0.1 — analytics module will
own exposure logging).
"""

from __future__ import annotations

import hashlib
from importlib import import_module
from typing import Any

_errors: Any = import_module("backend.01_core.errors")

_ORG_ENTITY_TYPE_ID = 1
_USER_ENTITY_TYPE_ID = 3
_APP_ENTITY_TYPE_ID = 6
# Workspace = 2, Role = 4, Group = 5 — not used as override entity types in v0.1.


async def _resolve_flag_by_scope(
    conn: Any, *,
    flag_key: str,
    org_id: str | None,
    application_id: str | None,
) -> dict | None:
    """Pick the most-specific flag matching the context. application > org > global."""
    # application scope
    if application_id is not None:
        row = await conn.fetchrow(
            """
            SELECT f.id, f.flag_key, s.code AS scope, vt.code AS value_type,
                   f.default_value_jsonb AS default_value, f.is_active
            FROM "09_featureflags"."10_fct_flags" f
            JOIN "09_featureflags"."03_dim_flag_scopes" s ON s.id = f.scope_id
            JOIN "09_featureflags"."02_dim_value_types" vt ON vt.id = f.value_type_id
            WHERE f.flag_key = $1 AND f.deleted_at IS NULL
              AND s.code = 'application' AND f.application_id = $2
            """,
            flag_key, application_id,
        )
        if row:
            return dict(row)
    # org scope
    if org_id is not None:
        row = await conn.fetchrow(
            """
            SELECT f.id, f.flag_key, s.code AS scope, vt.code AS value_type,
                   f.default_value_jsonb AS default_value, f.is_active
            FROM "09_featureflags"."10_fct_flags" f
            JOIN "09_featureflags"."03_dim_flag_scopes" s ON s.id = f.scope_id
            JOIN "09_featureflags"."02_dim_value_types" vt ON vt.id = f.value_type_id
            WHERE f.flag_key = $1 AND f.deleted_at IS NULL
              AND s.code = 'org' AND f.org_id = $2
            """,
            flag_key, org_id,
        )
        if row:
            return dict(row)
    # global scope
    row = await conn.fetchrow(
        """
        SELECT f.id, f.flag_key, s.code AS scope, vt.code AS value_type,
               f.default_value_jsonb AS default_value, f.is_active
        FROM "09_featureflags"."10_fct_flags" f
        JOIN "09_featureflags"."03_dim_flag_scopes" s ON s.id = f.scope_id
        JOIN "09_featureflags"."02_dim_value_types" vt ON vt.id = f.value_type_id
        WHERE f.flag_key = $1 AND f.deleted_at IS NULL AND s.code = 'global'
        """,
        flag_key,
    )
    return dict(row) if row else None


async def _get_env(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "09_featureflags"."01_dim_environments" WHERE code = $1',
        code,
    )


async def _get_flag_state(
    conn: Any, *, flag_id: str, environment_id: int,
) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, is_enabled, env_default_value_jsonb AS env_default_value '
        'FROM "09_featureflags"."11_fct_flag_states" '
        'WHERE flag_id = $1 AND environment_id = $2 AND deleted_at IS NULL',
        flag_id, environment_id,
    )
    return dict(row) if row else None


async def _lookup_overrides(
    conn: Any, *,
    flag_id: str, environment_id: int,
    entity_pairs: list[tuple[int, str]],
) -> dict | None:
    """Find the highest-precedence override among the given entity pairs.
    Precedence: application > user > org (for this v0.1 pass).
    """
    if not entity_pairs:
        return None
    for et_id, eid in entity_pairs:
        row = await conn.fetchrow(
            'SELECT id, value_jsonb AS value, entity_type_id '
            'FROM "09_featureflags"."21_fct_overrides" '
            'WHERE flag_id = $1 AND environment_id = $2 '
            '  AND entity_type_id = $3 AND entity_id = $4 '
            '  AND deleted_at IS NULL AND is_active = true',
            flag_id, environment_id, et_id, eid,
        )
        if row:
            return dict(row)
    return None


async def _load_rules(
    conn: Any, *, flag_id: str, environment_id: int,
) -> list[dict]:
    rows = await conn.fetch(
        'SELECT id, priority, conditions_jsonb AS conditions, '
        '       value_jsonb AS value, rollout_percentage '
        'FROM "09_featureflags"."20_fct_rules" '
        'WHERE flag_id = $1 AND environment_id = $2 '
        '  AND deleted_at IS NULL AND is_active = true '
        'ORDER BY priority ASC',
        flag_id, environment_id,
    )
    return [dict(r) for r in rows]


# ─── Condition tree evaluator ────────────────────────────────────────

def _context_get(ctx_attrs: dict, path: str) -> Any:
    """Fetch attr from context. Supports dotted paths like 'user.email'."""
    cur: Any = ctx_attrs
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _eval_condition(node: Any, ctx_attrs: dict) -> bool:
    """
    Recursive condition evaluator. Supports:
      {op: and|or, children: [...]}
      {op: not, child: {...}}
      {op: eq|neq, attr, value}
      {op: in,  attr, values: [...]}  (also accepts "value" as list)
      {op: startswith|endswith|contains, attr, value}
      {op: gt|gte|lt|lte, attr, value}
      {op: exists, attr}
      {op: true|false}  — literal truth values for trivial rules
    """
    if not isinstance(node, dict):
        return bool(node)
    op = node.get("op", "").lower()

    if op == "true":
        return True
    if op == "false":
        return False
    if op == "and":
        return all(_eval_condition(c, ctx_attrs) for c in node.get("children", []))
    if op == "or":
        return any(_eval_condition(c, ctx_attrs) for c in node.get("children", []))
    if op == "not":
        return not _eval_condition(node.get("child", {}), ctx_attrs)

    attr = node.get("attr")
    if op == "exists":
        return attr is not None and _context_get(ctx_attrs, attr) is not None

    if attr is None:
        return False

    actual = _context_get(ctx_attrs, attr)
    value = node.get("value")
    values = node.get("values", value if isinstance(value, list) else None)

    if op == "eq":
        return actual == value
    if op == "neq":
        return actual != value
    if op == "in":
        return isinstance(values, list) and actual in values
    if op == "startswith":
        return isinstance(actual, str) and isinstance(value, str) and actual.startswith(value)
    if op == "endswith":
        return isinstance(actual, str) and isinstance(value, str) and actual.endswith(value)
    if op == "contains":
        if isinstance(actual, str) and isinstance(value, str):
            return value in actual
        if isinstance(actual, list):
            return value in actual
        return False
    if op in ("gt", "gte", "lt", "lte"):
        try:
            a = float(actual)  # type: ignore[arg-type]
            b = float(value)
        except (TypeError, ValueError):
            return False
        return (
            (op == "gt" and a > b)
            or (op == "gte" and a >= b)
            or (op == "lt" and a < b)
            or (op == "lte" and a <= b)
        )
    return False


def _in_rollout(flag_key: str, entity_id: str | None, percentage: int) -> bool:
    """Deterministic bucketing: hash(flag_key + entity_id) mod 100 < percentage."""
    if percentage >= 100:
        return True
    if percentage <= 0:
        return False
    anchor = entity_id or "__anonymous__"
    h = hashlib.sha256(f"{flag_key}:{anchor}".encode()).digest()
    bucket = int.from_bytes(h[:4], "big") % 100
    return bucket < percentage


# ─── Public evaluate ────────────────────────────────────────────────

async def evaluate(
    conn: Any, *,
    flag_key: str,
    environment: str,
    context: dict,
) -> dict:
    """
    Resolve a flag_key + environment + context into:
      {value, reason, flag_id?, flag_scope?, rule_id?, override_id?}
    """
    user_id = context.get("user_id")
    org_id = context.get("org_id")
    application_id = context.get("application_id")
    attrs = context.get("attrs") or {}

    env_id = await _get_env(conn, environment)
    if env_id is None:
        raise _errors.ValidationError(f"unknown environment {environment!r}")

    flag = await _resolve_flag_by_scope(
        conn, flag_key=flag_key, org_id=org_id, application_id=application_id,
    )
    if flag is None:
        return {"value": None, "reason": "flag_not_found"}

    if not flag["is_active"]:
        return {
            "value": flag["default_value"],
            "reason": "flag_inactive",
            "flag_id": flag["id"], "flag_scope": flag["scope"],
        }

    state = await _get_flag_state(conn, flag_id=flag["id"], environment_id=env_id)
    if state is None or not state["is_enabled"]:
        env_default = state["env_default_value"] if state else None
        value = env_default if env_default is not None else flag["default_value"]
        return {
            "value": value,
            "reason": "flag_disabled_in_env",
            "flag_id": flag["id"], "flag_scope": flag["scope"],
        }

    # Overrides: application > user > org precedence.
    entity_pairs: list[tuple[int, str]] = []
    if application_id:
        entity_pairs.append((_APP_ENTITY_TYPE_ID, application_id))
    if user_id:
        entity_pairs.append((_USER_ENTITY_TYPE_ID, user_id))
    if org_id:
        entity_pairs.append((_ORG_ENTITY_TYPE_ID, org_id))
    ov = await _lookup_overrides(
        conn, flag_id=flag["id"], environment_id=env_id, entity_pairs=entity_pairs,
    )
    if ov:
        et_id = ov["entity_type_id"]
        reason = (
            "application_override" if et_id == _APP_ENTITY_TYPE_ID
            else "user_override" if et_id == _USER_ENTITY_TYPE_ID
            else "org_override"
        )
        return {
            "value": ov["value"],
            "reason": reason,
            "flag_id": flag["id"], "flag_scope": flag["scope"],
            "override_id": ov["id"],
        }

    # Rules
    rules = await _load_rules(conn, flag_id=flag["id"], environment_id=env_id)
    anchor_id = user_id or org_id or application_id  # bucketing key
    for rule in rules:
        if not _eval_condition(rule["conditions"], attrs):
            continue
        if not _in_rollout(flag_key, anchor_id, int(rule["rollout_percentage"])):
            continue
        return {
            "value": rule["value"],
            "reason": "rule_match",
            "flag_id": flag["id"], "flag_scope": flag["scope"],
            "rule_id": rule["id"],
        }

    # Fall-through
    env_default = state["env_default_value"] if state else None
    if env_default is not None:
        return {
            "value": env_default,
            "reason": "default_env",
            "flag_id": flag["id"], "flag_scope": flag["scope"],
        }
    return {
        "value": flag["default_value"],
        "reason": "default_flag",
        "flag_id": flag["id"], "flag_scope": flag["scope"],
    }
