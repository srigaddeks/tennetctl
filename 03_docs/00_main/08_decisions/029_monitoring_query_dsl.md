# ADR-029: Monitoring Query DSL

**Status:** Accepted
**Date:** 2026-04-17
**Related:** ADR-001 (Postgres primary), ADR-003 (raw SQL, no ORM), ADR-006 (DB conventions), ADR-008 (monitoring scope), ADR-026 (minimum surface principle).
**Note on numbering:** Plan 13-05 reserved the label "ADR-028" but that number was already taken by `028_vault_foundation.md`. The next free integer (029) is used; all references to "ADR-028" in Plan 13-05 refer to this document.

---

## Context

Phase 13 stores logs, metrics, and traces in Postgres behind `v_monitoring_*` views. Phases 13-02 through 13-04 ship the write path. 13-05 must expose a read path.

Three options were on the table:

1. **PromQL** — industry-standard, but requires a full parser/AST and a semantics layer. Out of scope for a developer platform that already has SQL as its lingua franca.
2. **Raw SQL passthrough** — simple, but every caller becomes a SQL-injection risk and no UI/alert layer can share code with the API.
3. **A JSON DSL that compiles to parameterized SQL against the existing views.** Callers speak JSON; the compiler speaks asyncpg `$1, $2, ...`.

We pick option 3.

---

## Decision

Adopt a **JSON-based Monitoring Query DSL** with three top-level shapes (`logs`, `metrics`, `traces`) sharing a common `filter` tree, `timerange`, and `cursor`. The DSL compiles to parameterized SQL against `v_monitoring_logs`, `v_monitoring_spans`, `v_monitoring_metrics`, and — for metric points — the raw partitioned `evt_monitoring_metric_points` table (rollup-aware selection is a 13-07 follow-up).

### Shape (summary)

```jsonc
{
  "target": "logs" | "metrics" | "traces",
  "filter": { /* recursive Filter tree */ },
  "timerange": {"from_ts": "...", "to_ts": "..."} | {"last": "15m|1h|24h|7d|30d|90d"},
  "limit": 100,
  "cursor": "<opaque base64>"
}
```

Shape-specific fields:

- `logs`: `severity_min`, `body_contains`, `trace_id`
- `metrics`: `metric_key` (required), `labels`, `aggregate` (`sum|avg|min|max|count|rate|p50|p95|p99`), `bucket` (`1m|5m|1h|1d`), `groupby`
- `traces`: `service_name`, `span_name_contains`, `duration_min_ms`, `duration_max_ms`, `has_error`, `trace_id`

### Filter operators

`and`, `or`, `not`, `eq`, `ne`, `in`, `nin`, `lt`, `lte`, `gt`, `gte`, `contains`, `jsonb_path`, `regex_limited`.

### Security model (non-negotiable)

1. **Zero string-concat on user values.** Every filter value is bound as an asyncpg parameter (`$1, $2, …`).
2. **Field allowlist.** The compiler has a per-target allowlist of columns that may appear in `field`. Unknown fields are rejected with `INVALID_QUERY`. This stops both typos and injection-via-field-name.
3. **Org scope auto-injection.** `org_id = $N` is appended by the compiler from `NodeContext.org_id`. The user cannot override. If ctx has a `workspace_id`, it is injected likewise.
4. **Timerange cap.** `to_ts - from_ts ≤ 90 days`. Unresolved `{last}` tokens are capped by whitelist, so a user can't ask for "99999d".
5. **Regex limiter.** `regex_limited` values must be ≤100 chars and disallow nested quantifiers (`(a+)+`, `(a*)*`, `(a+)*`, `(a*)+`) to defeat catastrophic backtracking / ReDoS.
6. **Filter tree depth cap.** Max 10 levels of nesting.
7. **Views, not tables.** Compiled SQL reads `v_monitoring_*`. The raw `evt_*` tables are read only by the metrics compiler (which needs rollup visibility).
8. **Cursor is opaque.** Base64-encoded JSON of `(recorded_at, id)`; the server treats it as an advance-key only, never as SQL.

### Alternatives rejected

- **PromQL.** Parser complexity is larger than the rest of 13-05 combined. We can compile PromQL to the DSL later; we can't do the reverse.
- **Raw SQL.** One missed bind = one data breach. Out.
- **GraphQL.** Costs a runtime for no win — our shapes are three, not three hundred.

### Forward compatibility

A v0.2 compiler can:
- Route long ranges to `evt_monitoring_metric_points_1m / _5m / _1h / _1d` when those tables are populated (13-07).
- Add a privileged `sql_passthrough` mode for admins, compiled through the same allowlist.
- Add `PromQL → DSL` transpilation that uses the same compiler downstream.

---

## Consequences

### Positive

- One language for UI, alerts, API, CLI, MCP. JSON round-trips cleanly through all.
- Parameterization is a compiler invariant, not a caller discipline. Safe by default.
- The DSL grammar is the Pydantic model; validation is the type check.
- Rollup awareness lives in one compiler function, not scattered through callers.

### Negative

- Less expressive than raw SQL (by design). Niche queries must be added as new DSL ops.
- Compiler must be kept in sync with view schemas. Mitigated by the field allowlist being a small constant per target.

### Out of scope for 13-05

- Rollup-table selection by `bucket × span` (13-07 cron populates the rollup tables first).
- Alerting hooks (13-08 will consume saved queries).
- UI (13-06).

---

## References

- `backend/02_features/05_monitoring/query_dsl/` — implementation.
- `tests/features/05_monitoring/test_query_dsl.py` — negative/positive test matrix.
