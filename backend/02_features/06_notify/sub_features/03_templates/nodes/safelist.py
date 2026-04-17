"""
notify.templates.nodes.safelist — SQL safelist validator for dynamic_sql variables.

Pure module: no DB access, no imports from other notify sub-features.
Called at schema validation time (save-time) to reject obviously unsafe SQL.
Runtime enforcement is: SET LOCAL statement_timeout = '2000' + read-only pgpool connection.
"""

from __future__ import annotations

import re

_FORBIDDEN_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|EXECUTE|EXEC|COPY|VACUUM|ANALYZE|CLUSTER|REINDEX)\b",
    re.IGNORECASE,
)

_ALLOWED_CONTEXT_KEYS: frozenset[str] = frozenset({
    "actor_user_id",
    "org_id",
    "workspace_id",
    "event_metadata",
})


def validate_dynamic_sql(sql_template: str | None, param_bindings: dict | None) -> None:
    """
    Raises ValueError if sql_template fails safelist checks (save-time validation).

    Rules:
    1. Must start with SELECT (after whitespace strip)
    2. No DML/DDL keywords in the SQL body
    3. All param_bindings values must be in _ALLOWED_CONTEXT_KEYS

    Runtime enforcement (not here):
    - Executes with SET LOCAL statement_timeout = '2000' (2 seconds)
    - Connection is in caller's transaction — no additional write protection needed
      because the save-time DML/DDL check has already blocked mutations
    """
    stripped = (sql_template or "").strip()
    if not stripped.upper().startswith("SELECT"):
        raise ValueError(
            "dynamic_sql must start with SELECT — only read-only queries are allowed"
        )
    if _FORBIDDEN_RE.search(stripped):
        raise ValueError(
            "dynamic_sql contains a forbidden keyword (DML/DDL not permitted)"
        )
    for param, context_key in (param_bindings or {}).items():
        if context_key not in _ALLOWED_CONTEXT_KEYS:
            raise ValueError(
                f"param_bindings key {context_key!r} (mapped from {param!r}) is not allowed. "
                f"Allowed context keys: {sorted(_ALLOWED_CONTEXT_KEYS)}"
            )
