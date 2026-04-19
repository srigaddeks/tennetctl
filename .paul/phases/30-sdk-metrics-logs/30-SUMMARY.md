# Phase 30 SUMMARY — SDK metrics + logs modules

**Status:** ✅ Complete (2026-04-18, both languages in one pass)

## Shipped in both SDKs

### `client.metrics` (counter / gauge / histogram)

| Method | HTTP |
|---|---|
| `metrics.register({key, kind, description?, buckets?, cardinality_limit?})` | `POST /v1/monitoring/metrics` |
| `metrics.list(filters?)` | `GET /v1/monitoring/metrics` |
| `metrics.get(key)` | `GET /v1/monitoring/metrics/{key}` |
| `metrics.increment(key, {value?, labels?})` | `POST /v1/monitoring/metrics/{key}/increment` |
| `metrics.set(key, {value, labels?})` | `POST /v1/monitoring/metrics/{key}/set` |
| `metrics.observe(key, {value, labels?})` | `POST /v1/monitoring/metrics/{key}/observe` |
| `metrics.query(body)` | `POST /v1/monitoring/metrics/query` |

### `client.logs`

| Method | HTTP |
|---|---|
| `logs.emit({severity, body, attributes?, service_name?, trace_id?, span_id?})` | `POST /v1/monitoring/otlp/v1/logs` (wraps as OTLP JSON) |
| `logs.emit_batch(records)` / `logs.emitBatch(records)` | same endpoint, raw `resourceLogs` |
| `logs.query(body)` | `POST /v1/monitoring/logs/query` |
| `logs.tail(filters?)` | `GET /v1/monitoring/logs/tail` |

OTLP JSON wrapping handles attribute value typing (bool/int/double/string) automatically.

## Verification

Python: 80 tests green, 90% overall coverage (metrics 84%, logs 81%).
TypeScript: 71 tests green, 96.81% overall (metrics 100%, logs 89%).

## Deferred

- Async batch + drop-on-retry-exhaustion (v0.2.2 refinement)
- True auto-instrument (Python FastAPI middleware + asyncpg hooks) — Phase 31
- Browser SDK page-view + long-task auto-capture — Phase 31
