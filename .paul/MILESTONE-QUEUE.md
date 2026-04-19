# Milestone Queue

**Generated:** 2026-04-18 (rescoped: unified SDK + admin UI coverage)
**Status:** 7 milestones staged for sequential execution

**Order:**
1. v0.2.1 Unified SDK Core — auth + flags + iam + audit + notify *(ACTIVE)*
2. v0.2.2 Unified SDK Observability — metrics + logs + traces + auto-instrument
3. v0.2.3 Unified SDK Platform — vault + catalog + APISIX gateway sync
4. v0.2.4 Admin UI Coverage Pass — every feature has a full admin portal page
5. v0.1.8 Runtime Hardening — DX, auth hardening, NCP v1 maturity
6. v0.3.0 Monitoring Alerting + SLOs — alerting engine, dashboard sharing
7. v0.4.0 Canvas + Visual Flow Viewer — React Flow reads live catalog

---

## ▶ v0.2.1 — Unified SDK Core *(ACTIVE)*

**Theme:** One `tennetctl-py` (Python) + one `@tennetctl/sdk` (TypeScript). Single client, capability-scoped modules. Single bearer-auth boundary. Single SWR cache. Consistent error envelope.

**SDK architecture (both languages):**
```
client = Tennetctl(base_url, api_key)        # or session token
client.auth.signin(...), .signout(), .me(), .session.validate(), .api_keys.list/create/revoke
client.flags.evaluate(key, entity), .evaluate_bulk(entities)
client.iam.users.list/get, .orgs.list/get, .workspaces.list/get, .roles.list/get
client.audit.emit(event), .query(filters)
client.notify.send(template_key, recipient, vars)
```

**Phases:**
- **28** — SDK skeleton + `auth` module (both Python + TS)
  - Package scaffolding, versioning, release pipeline
  - Transport layer (httpx / native fetch) with bearer auth + retry + envelope parsing
  - `auth` module: signin/signout/me/session.validate/api_keys.*
  - pytest + vitest coverage ≥80% on transport + auth
  - Published to internal registry or git-tagged
- **29** — `flags` + `iam` + `audit` + `notify` modules (both Python + TS)
  - `flags.evaluate` / `evaluate_bulk` with 60s SWR cache keyed on (flag_key, entity_hash)
  - `iam.users/orgs/workspaces/roles` read-only helpers
  - `audit.emit` / `query` (scoped to caller's org/ws via API)
  - `notify.send` transactional API wrapper
  - End-to-end integration test: signin → emit audit → send notify → evaluate flag
  - Docs: SDK quickstart + per-module reference

**Constraints:**
- Python ≥3.10, TS ≥ES2022, zero heavy deps (httpx + pydantic for py; native fetch only for ts)
- Same method names + return shape in both languages (polyglot parity)
- SDK never imports backend code — always hits HTTP endpoints
- Request cost: one bearer check per call; batch endpoints exist where fanout would hurt
- Every SDK call that mutates emits an audit event server-side (already wired — SDK just triggers it)

---

## ☐ v0.2.2 — Unified SDK Observability

**Theme:** Add metrics + logs + traces to the same SDK. Auto-instrument hook makes backend Python services self-observing in one line.

**Phases:**
- **30** — `metrics` + `logs` modules
  - `client.metrics.increment(name, labels)`, `.observe(name, value, labels)`, `.gauge(name, value, labels)`
  - `client.logs.emit(level, msg, attrs)` — structlog-compatible in Python
  - Batching + async flush (drop after retry budget, never block hot path)
  - Cardinality cap enforced SDK-side (mirrors backend) so bad label values fail fast
- **31** — `traces` module + auto-instrument helper
  - `client.traces.start_span(name, parent_ctx?)`, context managers in py / async-local-storage in ts
  - W3C trace-context propagation (inject/extract headers)
  - `tennetctl.autoinstrument(app)` — one call instruments FastAPI + asyncpg + httpx + Jinja2 in Python
  - Browser SDK: page-view + long-task traces
  - Sampling policy (head-based + tail-based configurable)

**Constraints:**
- Auto-instrument is opt-in, never monkey-patches unless called
- Fail-open — if tennetctl backend is down, telemetry drops silently (app continues)
- Same OTel semconv keys the backend already uses (trace_id, span_id, service_name, severity)

---

## ☐ v0.2.3 — Unified SDK Platform

**Theme:** Close SDK coverage. Vault + catalog inspection + APISIX gateway compilation.

**Phases:**
- **32** — `vault` + `catalog` modules
  - `client.vault.get_secret(key)` — scoped, audited, zero-caching (secrets are hot-path but never cached in SDK memory beyond the call)
  - `client.catalog.list_features()`, `.list_nodes(feature?)`, `.get_flow(key)` — read-only manifest inspection
  - Useful for meta-UIs and for the v0.4.0 canvas to consume the same surface external apps do
- **33** — APISIX gateway compilation
  - Add `kind` column on `fct_flags` (dim: `effect` / `request`)
  - APISIX sync worker: on `request`-kind flag mutation, PATCH APISIX Admin API with `traffic-split` + `consumer-restriction`
  - Boot reconcile: diff APISIX vs Postgres, push deltas
  - Audit `flags.apisix.synced|sync_failed`
  - Admin UI badge per flag showing sync status (in-sync / drift / failed)

**Constraints:**
- Vault SDK never returns raw secret to TS SDK in browser — browser can only request signed short-lived references, not plaintext
- APISIX is the only supported gateway in this phase; Envoy/Kong future

---

## ☐ v0.2.4 — Admin UI Coverage Pass

**Theme:** Every feature module has a complete admin portal page. No "backend works but no UI yet" gaps.

**Known UI gaps (from current state):**
- Workspaces — backend done, admin UI thin/missing
- Catalog browser — no UI at all (inspect features/sub-features/nodes/flows)
- System health dashboard — no single-pane view of module status
- Org switcher polish — exists, but cross-feature consistency is rough
- Module toggle UI — `TENNETCTL_MODULES` is env-only; no UI to inspect what's enabled
- Auth policy UI at scale — works for basics, but per-org override surfacing weak
- Notify Suppressions + Scheduled Sends + Channel Fallback + Analytics — backend shipped, UI depth uneven
- SIEM export destinations — backend shipped, admin UI status unknown

**Phases:**
- **34** — Audit gaps: walk every feature, enumerate pages vs backend capabilities, produce a coverage matrix with severity (critical / nice-to-have)
- **35** — Build the critical-severity missing pages (whichever surface from 34 blocks day-to-day admin work)
- **36** — Polish + nav: unified sidebar per role (portal views from original 23R Phase 27 carry forward here), consistent table/filter/action components, loading + empty + error states standardized

**Constraints:**
- All admin pages dogfood the unified SDK (no direct fetch; use `@tennetctl/sdk`)
- Design tokens + component library consistent across all pages
- Every page authenticated via permission (from 23R unified role model)
- Playwright MCP verification required per page

---

## ☐ v0.1.8 — Runtime Hardening

**Focus:** Close pre-OSS audit gaps. DX + auth hardening + NCP v1 maturity.

**Phases:**
- **37** — DX + catalog hot-reload (watchdog in dev mode, handler class caching, pre-commit linter wiring)
- **38** — Auth hardening (rate limiting per-IP + per-email, HIBP breach check, passkey hardening + device revocation + attestation, 2FA-required policy enforcement)
- **39** — NCP v1 maturity (§9 + §11 doc sync, `get_many` bulk pattern, v1→v2 node migration demo, `pool` promoted to first-class NodeContext field)

---

## ☐ v0.3.0 — Monitoring Alerting + SLOs

**Focus:** Finish Phase 13 (paused at 13-07). Alerting end-to-end + SLO tracking + dashboard sharing. (Monitoring SDK already shipped in v0.2.2.)

**Phases:**
- **40** — Alerting (rule designer UI + evaluator worker + silences + Notify critical integration + alerts UI + pg_cron partition manager verified)
- **41** — SLO tracking (error-budget calc + burn-rate rendering) + saved queries + query history + signed dashboard share links

---

## ☐ v0.4.0 — Canvas + Visual Flow Viewer

**Focus:** The long-promised React Flow canvas. Read-only v1. Canvas consumes the same `client.catalog` surface external apps do.

**Phases:**
- **42** — Flow schema + backend (`fct_flows`, `fct_flow_nodes`, `lnk_flow_edges` active; manifest-driven flow registration; DAG validation; read-path endpoints)
- **43** — Canvas renderer (React Flow DAG render, typed ports per node, node detail drawer, virtualization spike for >200-node flows)
- **44** — Trace overlay + search (select trace_id, canvas animates node activation with timing; search flows by node/feature/kind; permalink per flow)
