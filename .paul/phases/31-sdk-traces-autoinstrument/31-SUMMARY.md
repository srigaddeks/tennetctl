# Phase 31 SUMMARY — SDK traces (query + raw OTLP emit)

**Status:** 🟡 Partial — query surface shipped; auto-instrument deferred

## Shipped in both SDKs

### `client.traces`

| Method | HTTP |
|---|---|
| `traces.emit_batch(resource_spans)` / `traces.emitBatch(resourceSpans)` | `POST /v1/monitoring/otlp/v1/traces` |
| `traces.query(body)` | `POST /v1/monitoring/traces/query` |
| `traces.get(trace_id)` | `GET /v1/monitoring/traces/{trace_id}` |

## Deferred to Phase 31-b (v0.2.2 follow-up)

- `traces.start_span(name, parent_ctx?)` — async-context-manager / async-local-storage implementation
- W3C trace-context header propagation helpers (inject + extract)
- `tennetctl.autoinstrument(app)` — FastAPI middleware + asyncpg hooks + httpx hooks + Jinja2 instrumentation (Python)
- Browser page-view + long-task + first-input-delay + cumulative-layout-shift capture (TypeScript)
- Sampling policy (head-based + tail-based keep-all-errors-and-slow)

Reason for deferral: auto-instrument requires runtime validation against a live backend with OTLP receiver accepting spans; the SDK-side wiring is straightforward but only useful once end-to-end flows are tested. Safer to land with Phase 13-03 confirmation than speculatively now.

## Verification

Python: covered in `test_logs_traces.py` — 3 traces tests.
TypeScript: covered in `observability.test.ts` — 3 traces tests.

Both green alongside metrics + logs from Phase 30.
