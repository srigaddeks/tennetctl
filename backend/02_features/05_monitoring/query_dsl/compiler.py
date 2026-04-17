"""Monitoring Query DSL compiler.

Produces ``(sql, params)`` tuples for asyncpg. Callers pass a validated query
model + a ``NodeContext`` (for org_id / workspace_id auto-injection) and the
compiler returns a parameterized SELECT against the appropriate view.

Security invariants (enforced per ADR-029):
- User values are NEVER interpolated into SQL; they always go into ``params``.
- Filter ``field`` names are checked against a per-target allowlist.
- ``org_id`` (and ``workspace_id`` when present) come from the context and are
  bound as parameters.
- ``recorded_at`` timerange bounds come from ``Timerange.resolve()``.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from importlib import import_module
from typing import Any

_types: Any = import_module("backend.02_features.05_monitoring.query_dsl.types")
_validator: Any = import_module("backend.02_features.05_monitoring.query_dsl.validator")

InvalidQueryError = _validator.InvalidQueryError


# 13-07: retention defaults (seconds). These match the seeded retention policies
# in migration 045 — used as an advisory check at compile time so that queries
# for timeranges older than retention return a clear 400 instead of silently
# empty. Not the source of truth; the DB table is.
_DEFAULT_RETENTION_DAYS = {
    "60_evt_monitoring_logs":               14,
    "62_evt_monitoring_spans":               7,
    "61_evt_monitoring_metric_points":       7,
    "70_evt_monitoring_metric_points_1m":   30,
    "71_evt_monitoring_metric_points_5m":   90,
    "72_evt_monitoring_metric_points_1h":  365,
}


def _check_retention(table_name: str, from_ts: Any) -> None:
    """Raise InvalidQueryError if from_ts is older than the retention window."""
    from datetime import datetime, timedelta, timezone
    days = _DEFAULT_RETENTION_DAYS.get(table_name)
    if days is None:
        return
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # 1 day slack so "last 7d" against 7d retention is not rejected.
    cutoff = now - timedelta(days=days + 1)
    # from_ts may be naive UTC; compare safely.
    ts = from_ts
    if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
        ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
    if ts < cutoff:
        raise InvalidQueryError(
            f"data expired per retention policy for table {table_name} "
            f"(retention={days} days)"
        )


# ── Field allowlists per target ───────────────────────────────────────

# Map user-facing field names -> view column expression.
# Values marked "JSONB" are used by the compiler to wrap paths as ->>.
LOGS_FIELDS: dict[str, str] = {
    "id": "id",
    "recorded_at": "recorded_at",
    "observed_at": "observed_at",
    "severity_id": "severity_id",
    "severity_code": "severity_code",
    "severity_text": "severity_text",
    "body": "body",
    "trace_id": "trace_id",
    "span_id": "span_id",
    "service_name": "service_name",
    "service_instance_id": "service_instance_id",
    "service_version": "service_version",
    "scope_name": "scope_name",
    "scope_version": "scope_version",
    "resource_id": "resource_id",
    "org_id": "org_id",
    "workspace_id": "workspace_id",
    # JSONB attributes path — value must be a string key.
    "attributes": "attributes",
}

METRICS_FIELDS: dict[str, str] = {
    "metric_id": "metric_id",
    "resource_id": "resource_id",
    "recorded_at": "recorded_at",
    "org_id": "org_id",
    "workspace_id": "workspace_id",
    "value": "value",
    "labels": "labels",
    "trace_id": "trace_id",
    "span_id": "span_id",
}

TRACES_FIELDS: dict[str, str] = {
    "trace_id": "trace_id",
    "span_id": "span_id",
    "parent_span_id": "parent_span_id",
    "recorded_at": "recorded_at",
    "name": "name",
    "kind_id": "kind_id",
    "kind_code": "kind_code",
    "status_id": "status_id",
    "status_code": "status_code",
    "status_message": "status_message",
    "duration_ns": "duration_ns",
    "service_name": "service_name",
    "service_instance_id": "service_instance_id",
    "service_version": "service_version",
    "org_id": "org_id",
    "workspace_id": "workspace_id",
    "resource_id": "resource_id",
    "attributes": "attributes",
}


# ── Cursor codec (opaque base64 of JSON) ──────────────────────────────

def encode_cursor(row: dict[str, Any]) -> str:
    """Encode a cursor row ``{recorded_at, id}`` into an opaque base64 token."""
    payload = {
        "recorded_at": _iso(row.get("recorded_at")),
        "id": row.get("id"),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def decode_cursor(token: str | None) -> tuple[datetime, str] | None:
    """Decode a cursor token back into ``(recorded_at, id)`` or ``None``."""
    if not token:
        return None
    try:
        pad = "=" * (-len(token) % 4)
        data = base64.urlsafe_b64decode((token + pad).encode("ascii"))
        obj = json.loads(data.decode("utf-8"))
        ts_raw = obj.get("recorded_at")
        row_id = obj.get("id")
        if not isinstance(ts_raw, str) or not isinstance(row_id, str):
            raise InvalidQueryError("invalid cursor payload")
        ts = datetime.fromisoformat(ts_raw)
        if ts.tzinfo is not None:
            ts = ts.replace(tzinfo=None)
        return ts, row_id
    except InvalidQueryError:
        raise
    except Exception as e:  # noqa: BLE001
        raise InvalidQueryError(f"invalid cursor: {e}") from e


def _iso(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v.isoformat()
    return str(v)


# ── Filter compiler ───────────────────────────────────────────────────

_SIMPLE_OPS = {
    "eq": "=",
    "ne": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
}


def _resolve_field(field_name: str, allowlist: dict[str, str]) -> str:
    """Translate user field name to a safe SQL column expression.

    Supports JSONB sub-paths for 'attributes' / 'labels' via dotted suffix:
    ``attributes.http_method`` → ``attributes->>'http_method'``.
    Every segment is validated against a conservative allowlist character set.
    """
    if "." in field_name:
        head, _, tail = field_name.partition(".")
        col = allowlist.get(head)
        if col is None:
            raise InvalidQueryError(f"field {field_name!r} is not queryable")
        # Tail must be a simple identifier-ish token (no quotes, no SQL).
        if not tail or not all(c.isalnum() or c in "_-" for c in tail):
            raise InvalidQueryError(
                f"field {field_name!r}: JSONB key must be alphanumeric/underscore",
            )
        # Bind the tail as a text literal via parameter — but JSONB operators
        # need literal keys, and the key is pre-validated, so we can quote it
        # inline safely (chars were hardwhitelisted above).
        return f"{col}->>'{tail}'"
    col = allowlist.get(field_name)
    if col is None:
        raise InvalidQueryError(f"field {field_name!r} is not queryable")
    return col


def _bind(bindings: list[Any], value: Any) -> str:
    bindings.append(value)
    return f"${len(bindings)}"


def compile_filter(
    node: Any,
    bindings: list[Any],
    allowlist: dict[str, str],
) -> str:
    """Compile a Filter tree into a parameterized SQL WHERE fragment."""
    if node is None:
        return "TRUE"

    if node.and_:
        parts = [compile_filter(c, bindings, allowlist) for c in node.and_]
        return "(" + " AND ".join(parts) + ")" if parts else "TRUE"

    if node.or_:
        parts = [compile_filter(c, bindings, allowlist) for c in node.or_]
        return "(" + " OR ".join(parts) + ")" if parts else "FALSE"

    if node.not_:
        return "(NOT " + compile_filter(node.not_, bindings, allowlist) + ")"

    for op_name, sql_op in _SIMPLE_OPS.items():
        leaf = getattr(node, op_name)
        if leaf is not None:
            col = _resolve_field(leaf.field, allowlist)
            return f"{col} {sql_op} {_bind(bindings, leaf.value)}"

    if node.in_ is not None:
        col = _resolve_field(node.in_.field, allowlist)
        placeholders = ", ".join(_bind(bindings, v) for v in node.in_.values)
        return f"{col} IN ({placeholders})"

    if node.nin is not None:
        col = _resolve_field(node.nin.field, allowlist)
        placeholders = ", ".join(_bind(bindings, v) for v in node.nin.values)
        return f"{col} NOT IN ({placeholders})"

    if node.contains is not None:
        col = _resolve_field(node.contains.field, allowlist)
        return f"{col} ILIKE '%' || {_bind(bindings, node.contains.value)} || '%'"

    if node.jsonb_path is not None:
        # Value is a literal text to match against the JSONB column rendered as text.
        col = _resolve_field(node.jsonb_path.field, allowlist)
        return f"{col}::text ILIKE '%' || {_bind(bindings, node.jsonb_path.value)} || '%'"

    if node.regex_limited is not None:
        col = _resolve_field(node.regex_limited.field, allowlist)
        return f"{col} ~ {_bind(bindings, node.regex_limited.value)}"

    # Model validator guarantees exactly one branch set; unreachable.
    raise InvalidQueryError("empty filter node")


# ── Context helpers ───────────────────────────────────────────────────

def _ctx_org(ctx: Any) -> str:
    org = getattr(ctx, "org_id", None)
    if not org:
        raise InvalidQueryError(
            "context.org_id is required for monitoring queries",
        )
    return org


def _ctx_ws(ctx: Any) -> str | None:
    return getattr(ctx, "workspace_id", None)


# ── Per-target compilers ──────────────────────────────────────────────

def compile_logs_query(q: Any, ctx: Any) -> tuple[str, list[Any]]:
    bindings: list[Any] = []
    wheres: list[str] = []

    org = _ctx_org(ctx)
    wheres.append(f"org_id = {_bind(bindings, org)}")
    ws = _ctx_ws(ctx)
    if ws is not None:
        wheres.append(f"(workspace_id IS NULL OR workspace_id = {_bind(bindings, ws)})")

    from_ts, to_ts = q.timerange.resolve()
    _check_retention("60_evt_monitoring_logs", from_ts)
    wheres.append(f"recorded_at >= {_bind(bindings, from_ts)}")
    wheres.append(f"recorded_at <  {_bind(bindings, to_ts)}")

    if q.severity_min is not None:
        wheres.append(f"severity_id >= {_bind(bindings, q.severity_min)}")
    if q.body_contains is not None:
        wheres.append(
            f"body ILIKE '%' || {_bind(bindings, q.body_contains)} || '%'",
        )
    if q.trace_id is not None:
        wheres.append(f"trace_id = {_bind(bindings, q.trace_id)}")

    if q.filter is not None:
        wheres.append(compile_filter(q.filter, bindings, LOGS_FIELDS))

    cursor = decode_cursor(q.cursor)
    if cursor is not None:
        ts_c, id_c = cursor
        # DESC order — cursor: (recorded_at, id) < cursor
        wheres.append(
            f"(recorded_at, id) < ({_bind(bindings, ts_c)}, {_bind(bindings, id_c)})",
        )

    where_sql = " AND ".join(wheres)
    sql = f"""
        SELECT id, org_id, workspace_id, resource_id, service_name,
               service_instance_id, service_version, recorded_at, observed_at,
               severity_id, severity_code, severity_text, body,
               trace_id, span_id, trace_flags, scope_name, scope_version,
               attributes, dropped_attributes_count
        FROM "05_monitoring"."v_monitoring_logs"
        WHERE {where_sql}
        ORDER BY recorded_at DESC, id DESC
        LIMIT {_bind(bindings, q.limit)}
    """
    return sql, bindings


def compile_metrics_query(q: Any, ctx: Any) -> tuple[str, list[Any]]:
    """Compile a metrics timeseries query against ``evt_monitoring_metric_points``.

    13-05 uses the raw partitioned table. 13-07 will add rollup-table selection
    based on (bucket, span). The public API contract does not change.
    """
    bindings: list[Any] = []
    wheres: list[str] = []

    org = _ctx_org(ctx)
    wheres.append(f"p.org_id = {_bind(bindings, org)}")
    ws = _ctx_ws(ctx)
    if ws is not None:
        wheres.append(f"(p.workspace_id IS NULL OR p.workspace_id = {_bind(bindings, ws)})")

    # metric_key -> join with registry.
    wheres.append(f"m.key = {_bind(bindings, q.metric_key)}")

    from_ts, to_ts = q.timerange.resolve()
    _check_retention("61_evt_monitoring_metric_points", from_ts)
    wheres.append(f"p.recorded_at >= {_bind(bindings, from_ts)}")
    wheres.append(f"p.recorded_at <  {_bind(bindings, to_ts)}")

    if q.labels:
        for k, v in q.labels.items():
            # Validate label key (alphanumeric+underscore) to quote inline safely.
            if not k or not all(c.isalnum() or c == "_" for c in k):
                raise InvalidQueryError(f"invalid label key {k!r}")
            wheres.append(f"p.labels->>'{k}' = {_bind(bindings, v)}")

    if q.filter is not None:
        # Filter allowlist for metrics uses p.* columns.
        wheres.append(compile_filter(q.filter, bindings, METRICS_FIELDS))

    bucket = q.bucket or "1m"
    bucket_seconds = _types.BUCKET_SECONDS[bucket]

    agg = q.aggregate
    if agg in ("p50", "p95", "p99"):
        # Histogram percentile approximation. For now we compute
        # percentile_cont over the value column (gauge/counter fallback). A
        # histogram-bucket approximation is a 13-07 follow-up when rollup
        # tables carry summed histogram_counts.
        pct = {"p50": 0.5, "p95": 0.95, "p99": 0.99}[agg]
        agg_sql = (
            f"percentile_cont({pct}) WITHIN GROUP (ORDER BY p.value)"
        )
    elif agg == "count":
        agg_sql = "count(*)::double precision"
    elif agg == "rate":
        # Rate = delta of monotonic counter per bucket width seconds.
        # Approximated as (max - min) / bucket_seconds — exact-enough for
        # fixed-width buckets. Real rate with reset handling is a 13-07 item.
        agg_sql = f"(max(p.value) - min(p.value)) / {bucket_seconds}.0"
    else:
        agg_sql = f"{agg}(p.value)"

    group_cols: list[str] = []
    select_group: list[str] = []
    if q.groupby:
        for g in q.groupby:
            if not g or not all(c.isalnum() or c == "_" for c in g):
                raise InvalidQueryError(f"invalid groupby key {g!r}")
            expr = f"p.labels->>'{g}'"
            group_cols.append(expr)
            select_group.append(f"{expr} AS {g}")

    group_select = (", " + ", ".join(select_group)) if select_group else ""
    group_by_extra = (", " + ", ".join(group_cols)) if group_cols else ""

    sql = f"""
        SELECT
            to_timestamp(floor(extract(epoch from p.recorded_at) / {bucket_seconds}) * {bucket_seconds})
                AT TIME ZONE 'UTC' AS bucket_ts,
            {agg_sql} AS value
            {group_select}
        FROM "05_monitoring"."61_evt_monitoring_metric_points" p
        JOIN "05_monitoring"."10_fct_monitoring_metrics" m ON m.id = p.metric_id
        WHERE {" AND ".join(wheres)}
        GROUP BY bucket_ts {group_by_extra}
        ORDER BY bucket_ts ASC
        LIMIT {_bind(bindings, q.limit)}
    """
    return sql, bindings


def compile_traces_query(q: Any, ctx: Any) -> tuple[str, list[Any]]:
    bindings: list[Any] = []
    wheres: list[str] = []

    org = _ctx_org(ctx)
    wheres.append(f"org_id = {_bind(bindings, org)}")
    ws = _ctx_ws(ctx)
    if ws is not None:
        wheres.append(f"(workspace_id IS NULL OR workspace_id = {_bind(bindings, ws)})")

    from_ts, to_ts = q.timerange.resolve()
    _check_retention("62_evt_monitoring_spans", from_ts)
    wheres.append(f"recorded_at >= {_bind(bindings, from_ts)}")
    wheres.append(f"recorded_at <  {_bind(bindings, to_ts)}")

    if q.service_name is not None:
        wheres.append(f"service_name = {_bind(bindings, q.service_name)}")
    if q.span_name_contains is not None:
        wheres.append(
            f"name ILIKE '%' || {_bind(bindings, q.span_name_contains)} || '%'",
        )
    if q.duration_min_ms is not None:
        wheres.append(
            f"duration_ns >= {_bind(bindings, int(q.duration_min_ms * 1_000_000))}",
        )
    if q.duration_max_ms is not None:
        wheres.append(
            f"duration_ns <= {_bind(bindings, int(q.duration_max_ms * 1_000_000))}",
        )
    if q.has_error is True:
        wheres.append("status_code = 'error'")
    elif q.has_error is False:
        wheres.append("status_code <> 'error'")
    if q.trace_id is not None:
        wheres.append(f"trace_id = {_bind(bindings, q.trace_id)}")

    if q.filter is not None:
        wheres.append(compile_filter(q.filter, bindings, TRACES_FIELDS))

    cursor = decode_cursor(q.cursor)
    if cursor is not None:
        ts_c, id_c = cursor
        wheres.append(
            f"(recorded_at, span_id) < ({_bind(bindings, ts_c)}, {_bind(bindings, id_c)})",
        )

    sql = f"""
        SELECT trace_id, span_id, parent_span_id, org_id, workspace_id,
               resource_id, service_name, service_instance_id, service_version,
               name, kind_id, kind_code, status_id, status_code, status_message,
               recorded_at, start_time_unix_nano, end_time_unix_nano, duration_ns,
               attributes, events, links
        FROM "05_monitoring"."v_monitoring_spans"
        WHERE {" AND ".join(wheres)}
        ORDER BY recorded_at DESC, span_id DESC
        LIMIT {_bind(bindings, q.limit)}
    """
    return sql, bindings


def compile_trace_detail(trace_id: str, ctx: Any) -> tuple[str, list[Any]]:
    """Return all spans for a single trace_id, scoped by context org."""
    bindings: list[Any] = []
    wheres = [f"org_id = {_bind(bindings, _ctx_org(ctx))}"]
    ws = _ctx_ws(ctx)
    if ws is not None:
        wheres.append(f"(workspace_id IS NULL OR workspace_id = {_bind(bindings, ws)})")
    wheres.append(f"trace_id = {_bind(bindings, trace_id)}")
    sql = f"""
        SELECT trace_id, span_id, parent_span_id, name, kind_code, status_code,
               status_message, recorded_at, start_time_unix_nano,
               end_time_unix_nano, duration_ns, service_name, attributes,
               events, links
        FROM "05_monitoring"."v_monitoring_spans"
        WHERE {" AND ".join(wheres)}
        ORDER BY start_time_unix_nano ASC, span_id ASC
        LIMIT 5000
    """
    return sql, bindings


__all__ = [
    "compile_logs_query", "compile_metrics_query", "compile_traces_query",
    "compile_trace_detail", "compile_filter",
    "encode_cursor", "decode_cursor",
    "LOGS_FIELDS", "METRICS_FIELDS", "TRACES_FIELDS",
]
