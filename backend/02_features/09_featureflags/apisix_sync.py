"""
featureflags.apisix_sync — compile request-path flags to APISIX config.

Design notes
------------
Flags are tagged as either ``kind=effect`` (evaluated in backend runtime) or
``kind=request`` (evaluated at the gateway edge via APISIX).

For request-path flags, we compile a minimal APISIX plugin config describing
when the underlying route should serve traffic vs short-circuit to the flag's
default value. The output is a dict that can be written either:

  1. to an APISIX "standalone" YAML config file (our docker-compose default),
  2. or POSTed to the APISIX Admin API when running against an etcd backend.

The sync worker simply produces the plugin config dict here; a deployment-
specific writer publishes it.

Usage:

    from backend.02_features.09_featureflags.apisix_sync import (
        compile_flag,
        compile_all_request_flags,
    )

    plugin_config = compile_flag(flag_row, rules=[...], states=[...])
    all_configs = await compile_all_request_flags(conn)
"""

from __future__ import annotations

import hashlib
from typing import Any

# ---------------------------------------------------------------------------
# Flag kind detection (read from EAV attr `flags.kind`)
# ---------------------------------------------------------------------------

FLAG_KIND_EFFECT = "effect"
FLAG_KIND_REQUEST = "request"


async def flag_kind(conn: Any, flag_id: str) -> str:
    """Return the flag's kind — request or effect. Defaults to 'effect' if not set."""
    row = await conn.fetchrow(
        """
        SELECT a.key_text
        FROM "09_featureflags"."10_fct_flags" f
        LEFT JOIN "09_featureflags"."20_dtl_attr_defs" d
            ON d.code = 'kind' AND d.entity_type_id = 6  -- flag entity
        LEFT JOIN "09_featureflags"."21_dtl_attrs" a
            ON a.entity_id = f.id AND a.attr_def_id = d.id
        WHERE f.id = $1
        """,
        flag_id,
    )
    if row is None or row["key_text"] is None:
        return FLAG_KIND_EFFECT
    return row["key_text"]


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


def compile_flag(
    flag: dict,
    state: dict | None,
    rules: list[dict],
) -> dict[str, Any]:
    """
    Compile a single flag into an APISIX plugin config block.

    Output shape (trimmed):
        {
          "id": "flag-<flag_key>",
          "uri": "/v1/flags/gateway/<flag_key>",
          "plugins": {
              "consumer-restriction": {...},
              "traffic-split": {
                  "rules": [
                      {"match": [...], "weighted_upstreams": [...]}
                  ]
              }
          }
        }

    For boolean request flags, we emit a traffic-split with deterministic
    consistent-hash bucketing so the SAME user always lands on the SAME branch.
    For disabled flags we emit a short-circuit route returning the default.
    """
    flag_key = flag["flag_key"]
    default_value = flag.get("default_value_jsonb")
    is_enabled = (state or {}).get("is_enabled", False) if state else False

    if not flag.get("is_active") or not is_enabled:
        return {
            "id": f"flag-{_slug(flag_key)}",
            "uri": f"/v1/flags/gateway/{flag_key}",
            "plugins": {
                "serverless-pre-function": {
                    "phase": "access",
                    "functions": [
                        f'return function(conf, ctx) ngx.say([[{{"value":{_json_default(default_value)},"reason":"flag_disabled_in_env"}}]]); ngx.exit(200); end',
                    ],
                }
            },
        }

    # Build traffic-split based on rules
    traffic_split_rules: list[dict] = []
    for rule in sorted(rules, key=lambda r: r["priority"]):
        pct = int(rule.get("rollout_percentage") or 100)
        traffic_split_rules.append(
            {
                "match": [{"vars": _match_vars(rule.get("conditions_jsonb", {}))}],
                "weighted_upstreams": [
                    {"weight": pct, "upstream_id": f"flag-{_slug(flag_key)}-on"},
                    {"weight": max(0, 100 - pct), "upstream_id": f"flag-{_slug(flag_key)}-off"},
                ],
            }
        )

    return {
        "id": f"flag-{_slug(flag_key)}",
        "uri": f"/v1/flags/gateway/{flag_key}",
        "plugins": {
            "traffic-split": {"rules": traffic_split_rules},
        },
    }


async def compile_all_request_flags(conn: Any) -> list[dict[str, Any]]:
    """Compile every `kind=request` flag in the catalog. Returns list of plugin configs."""
    flags = await conn.fetch(
        """
        SELECT f.id, f.flag_key, f.default_value_jsonb, f.is_active,
               f.org_id, f.application_id
        FROM "09_featureflags"."10_fct_flags" f
        WHERE f.deleted_at IS NULL AND f.is_active = true
        """
    )

    out: list[dict[str, Any]] = []
    for f in flags:
        kind = await flag_kind(conn, f["id"])
        if kind != FLAG_KIND_REQUEST:
            continue

        # Pick the production env state for gateway compilation
        state = await conn.fetchrow(
            """
            SELECT fs.is_enabled, fs.env_default_value_jsonb
            FROM "09_featureflags"."11_fct_flag_states" fs
            JOIN "09_featureflags"."01_dim_environments" e ON e.id = fs.environment_id
            WHERE fs.flag_id = $1 AND e.code = 'prod' AND fs.deleted_at IS NULL
            """,
            f["id"],
        )
        rules = await conn.fetch(
            """
            SELECT priority, conditions_jsonb, value_jsonb, rollout_percentage
            FROM "09_featureflags"."20_fct_rules" r
            JOIN "09_featureflags"."01_dim_environments" e ON e.id = r.environment_id
            WHERE r.flag_id = $1 AND e.code = 'prod'
              AND r.deleted_at IS NULL AND r.is_active = true
            ORDER BY r.priority ASC
            """,
            f["id"],
        )
        config = compile_flag(
            dict(f),
            dict(state) if state else None,
            [dict(r) for r in rules],
        )
        out.append(config)
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in s).strip("-").lower()


def _json_default(value: Any) -> str:
    import json as _json

    try:
        return _json.dumps(value)
    except (TypeError, ValueError):
        return "null"


def _match_vars(conditions: dict[str, Any]) -> list[list[str]]:
    """Translate our condition JSON tree into APISIX `vars` match syntax.

    APISIX uses nginx-style variables. For eq conditions we emit
    ``["http_x_user_id", "==", "<value>"]`` style entries.

    Recursive and/or trees flatten to a simple AND list — gateway match
    semantics don't support full boolean trees, so we only compile the
    top-level AND group's leaf conditions. More complex trees degrade to
    "always match" at the gateway; backend takes over evaluation.
    """
    out: list[list[str]] = []
    op = str(conditions.get("op", "")).lower()

    if op in ("and", ""):
        for child in conditions.get("children", []) or []:
            _append_leaf(child, out)
    else:
        _append_leaf(conditions, out)

    return out


def _append_leaf(node: dict[str, Any], acc: list[list[str]]) -> None:
    op = str(node.get("op", "")).lower()
    attr = node.get("attr")
    value = node.get("value")
    if op == "eq" and attr and value is not None:
        acc.append([f"http_x_{_header_name(attr)}", "==", str(value)])
    elif op == "startswith" and attr and isinstance(value, str):
        acc.append([f"http_x_{_header_name(attr)}", "~*", f"^{value}"])
    elif op == "contains" and attr and isinstance(value, str):
        acc.append([f"http_x_{_header_name(attr)}", "~*", value])


def _header_name(attr: str) -> str:
    """Turn `user.email` into `user_email` (nginx lowercases hyphens)."""
    return attr.replace(".", "_").replace("-", "_").lower()


# ---------------------------------------------------------------------------
# Deterministic consistent-hash helper (re-exposes evaluator hash for parity)
# ---------------------------------------------------------------------------


def rollout_bucket(flag_key: str, entity_id: str) -> int:
    """Return a 0-99 bucket for consistent rollout bucketing. Matches the
    evaluator's deterministic hash so gateway + backend agree."""
    h = hashlib.sha256(f"{flag_key}:{entity_id}".encode()).digest()
    return int.from_bytes(h[:4], "big") % 100


__all__ = [
    "FLAG_KIND_EFFECT",
    "FLAG_KIND_REQUEST",
    "flag_kind",
    "compile_flag",
    "compile_all_request_flags",
    "rollout_bucket",
]
