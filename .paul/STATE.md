# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-16)

**Core value:** Any team can self-host one platform that replaces PostHog, Unleash, GrowthBook, Windmill, and their entire SaaS toolchain — building and running products as visual node workflows with enterprise capabilities built in.
**Current focus:** v0.1.9 IAM Enterprise — Phase 22 (7 plans). OIDC SSO complete. Next: SAML 2.0 SSO. Testing: pytest + Playwright MCP (Robot Framework removed).

## Current Position

Milestone: v0.1.9 IAM Enterprise — 🚧 In Progress
Phase: 22 of 22 (IAM Enterprise) — 1 of 7 plans complete
Plan: 22-01 COMPLETE. Ready for 22-02 (SAML 2.0 SSO).
Status: 22-01 APPLY+UNIFY done. 11/11 tests green. UI verified.
Previously: 13-06c COMPLETE — 4 Robot E2E suites, 19/19 tests green. Backend fix: LogsConsumer + SpansConsumer org_id now resolves real single-tenant UUID from IAM. Summaries at .paul/phases/13-monitoring/13-06c-SUMMARY.md and 13-06-SUMMARY.md (consolidated).
Previously: 13-06b COMPLETE — Monitoring frontend: 6 TanStack Query hooks, 9 components, 7 pages. recharts + react-grid-layout v2.
Previously: 13-06a COMPLETE — Monitoring backend dashboards/panels + SSE live-tail. 139/139 pytest green.
14-01 COMPLETE + UNIFIED — IAM API keys (argon2id-hashed, nk_*.* token format, scopes) + Bearer auth in SessionMiddleware + require_scope helper + notify send idempotency (Idempotency-Key header, partial unique index). 7 new tests, 240 passed full regression. Migrations 037+038. Frontend /account/api-keys page. Summary at .paul/phases/14-notify-api-keys-idempotency/14-01-SUMMARY.md.
Last activity: 2026-04-17 — v0.1.6 IAM Hardening for OSS milestone created. Phase 20 with 5 plans drafted in ROADMAP. Phase directory .paul/phases/20-iam-hardening-for-oss/ created.
Next action: /paul:plan for 20-01 — Auth policy config layer (vault-backed iam.policy.* keys, AuthPolicy service with SWR cache, bootstrap seed of safe defaults).

Progress:
- v0.1.5 Observability: Phase 13 plans 13-01 through 13-08 drafted; 13-01…13-07 APPLY complete (13-06 = a+b+c, 19/19 E2E green; 13-07 157/157 pytest green); 13-08 not started
- v0.1.7 Notify production: Phase 14-01 COMPLETE + UNIFIED. Phases 15–18 each have PLAN + SUMMARY on disk (status to audit); Phase 19 has SUMMARY only (ad-hoc APPLY — retroactive plan optional).
- Milestone v0.1: [██████████] 100% (All 12 phases complete — v0.1 Foundation + IAM milestone done)
- IAM auth backend (basics): 3 sub-features / 26 tests / 4 catalog nodes / session middleware / OAuth monkeypatched — IAM security completion (magic link/OTP/passkeys) deferred to Phase 12
- Audit write path: evt_audit table + emit node (Phase 3 Plan 03); read path + UI + outbox now planned as Phase 10
- Notify (Phase 11, 12 plans): dim tables with critical category + priority fan-out; template groups keyed to SMTP configs; static + dynamic-SQL variables (safelisted, parameterized by audit event); template designer UI; pure `POST /v1/notify/send` transactional API
- IAM Security Completion (Phase 12, 4 plans): magic link + OTP (email + TOTP) + passkeys + password reset — depends on Notify for delivery

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✅       ✅       ✅    [22-01 COMPLETE — ready for 22-02 PLAN]
```

Phase 22 (v0.1.9 — IAM Enterprise) — 7 plans (simplified for Keycloak/Zitadel/Clerk parity):
  1. ✅ 22-01 — OIDC SSO (authlib + PKCE + per-org + JIT user) COMPLETE
  2. ▶ 22-02 — SAML 2.0 SSO (python3-saml + per-org + JIT user)
  3.   22-03 — SCIM 2.0 provisioning (RFC 7644, Okta/Azure)
  4.   22-04 — Admin impersonation (dual-actor audit + red banner)
  5.   22-05 — MFA enforcement policy (per-org/role require 2FA gate)
  6.   22-06 — IP allowlisting per org (CIDRs + middleware)
  7.   22-07 — Audit SIEM export (webhook/S3/Splunk outbox worker)

## Performance Metrics

**Velocity:**
- Total plans completed: 17
- Average duration: ~27 min
- Total execution time: ~477 min

**By Phase:**

| Phase | Plans | Total Time | Avg/Plan |
|-------|-------|------------|----------|
| 01-core-infrastructure | 3/3 ✅ | ~60min | ~20min |
| 02-catalog-foundation | 3/3 ✅ | ~95min | ~32min |
| 03-iam-audit | 4/4 ✅ | ~85min | ~21min |
| 04-orgs-workspaces | 2/3 🟡 backend done, UI remains | ~40min | ~20min |
| 05-users | 2/2 ✅ backend complete | ~25min | ~13min |
| 06-roles-groups-apps | 1/1 ✅ backend complete | ~35min | ~35min |
| 07-vault | 2/2 ✅ full-stack complete | ~90min | ~45min |
| 08-auth | 2/2 ✅ full-stack complete (08-02 closed retroactively) | ~15min | ~15min |
| 10-audit-analytics | 4/4 ✅ full-stack complete (explorer + analytics + outbox) | ~182min | ~46min |
| 11-notify | 12/12 ✅ complete | ~4 sessions | — |

## Accumulated Context

### Decisions
| Decision | Phase | Impact |
|----------|-------|--------|
| Raw SQL with asyncpg, PG-specific features allowed | Init | No ORM |
| Audit in 04_audit schema, cross-cutting | Planning | All features write evt_audit |
| Every phase is a vertical slice | Planning | Schema → repo → service → routes → nodes → UI → Playwright |
| Custom SQL migrator (asyncpg-only, UP/DOWN, rollback, history) | Phase 1 | — |
| Postgres on port 5434; Frontend port 51735 | Phase 1 | Non-standard; avoids conflicts |
| importlib everywhere for numeric dirs | Phase 1 | — |
| Distributed migrations in 09_sql_migrations/; seeds as YAML | Phase 1 refactor | Migrator rglobs |
| fct_* tables have NO business columns (except identity slugs) | Planning | All attrs in dtl_attrs via EAV |
| NCP v1 — sub-features communicate only via `run_node` | Phase 2 | Enforced by lint |
| Catalog DB in `01_catalog`; fct_* use SMALLINT identity PKs | Phase 2 | Documented deviation from UUID v7 rule |
| Effect-must-emit-audit: triple defense (DB CHECK + Pydantic + runner) | Phase 2 | — |
| Pydantic models ARE the manifest schema | Phase 2 | Single source of truth |
| feature.key == metadata.module in NCP v1 | Phase 2 | One feature per module |
| Linter parses both `from X` + `import_module("X")` Call nodes | Phase 2 | — |
| `Any` typing for dynamically-imported modules | Phase 2 | Pyright can't follow importlib |
| NodeContext propagates audit scope + tracing | Phase 2 | — |
| Execution policy per node (timeout/retries/tx modes) | Phase 2 | — |
| Idempotency check before Pydantic validation | Phase 2 Plan 03 | — |
| TransientError is the only retryable exception class | Phase 2 Plan 03 | — |
| Cross-import validator enforces sub-feature boundaries | Phase 2 | Pre-commit hook |
| MCP + scaffolder CLI deferred to v0.2 | Phase 2 | — |
| Per-sub-feature migration layout — each sub-feature owns its SQL | Phase 3 Plan 03 | Scales to 10-30 sub-features |
| Node keys require 3+ segments (feature.sub.action) | Phase 3 Plan 03 | `audit.emit` → `audit.events.emit` |
| Default authz bypasses user_id for audit_category in (system, setup) | Phase 3 Plan 03 | — |
| JSONB codec registered on pool init | Phase 3 Plan 03 | dict⇄JSONB transparent |
| Audit scope triple-defense with setup/failure bypasses | Phase 3 Plan 03 | — |
| Views use MAX(...) FILTER for EAV pivot; hide internal FKs | Phase 3 Plan 04 | Scales; internal refactors invisible |
| Pool propagation via NodeContext.extras['pool'] | Phase 4 Plan 01 | Route stashes pool; downstream nodes emit audit via run_node without extending frozen NodeContext |
| Service mutation fns take (pool, conn, ctx) | Phase 4 Plan 01 | Audit emission is an explicit dep, not hidden in ctx |
| iam.orgs.get kind=control (read-only DB ops widening) | Phase 4 Plan 01 | Control nodes may read; NCP §11 doc sync deferred to v0.1.5 |
| Route paths with {id} must be quoted in YAML manifests | Phase 4 Plan 01 | Sidesteps flow-mapping parser; convention for future route lists |
| Option B for EAV description on fct_vault_entries | Phase 7 Plan 01 | Pure-EAV rule preserved; description lives in 02_vault.dtl_attrs via dim_attr_defs entry |
| AES-256-GCM envelope encryption via PyCA cryptography | Phase 7 Plan 01 | Per-secret DEK + 12-byte nonces + GCM auth tag; root key in TENNETCTL_VAULT_ROOT_KEY (32 bytes base64) |
| Env-var allowlist (5 TENNETCTL_* vars) enforced at startup | Phase 7 Plan 01 | Any stray TENNETCTL_*_SECRET / TOKEN / PASSWORD / KEY blocks boot — secrets belong in vault |
| VaultClient SWR cache 60s + invalidate on rotate/delete | Phase 7 Plan 01 | Hot-path secret reads near-zero latency; rotate/delete invalidate inside same tx |
| Audit HTTP reads but not node reads for vault | Phase 7 Plan 01 | HTTP GET /v1/vault/{key} audits; vault.secrets.get node does not — hot path bypass |
| Item path keyed on {key} not {id} for vault | Phase 7 Plan 01 | Operators + backend code reference secrets by stable user-supplied name |
| Seed filenames must be globally unique | Phase 7 Plan 01 (discovered) | Seeder tracks by filename across features; use feature-prefixed names (e.g. 02vault_*.yaml) |
| Reveal-once UI uses useRef + unmount | Phase 7 Plan 02 | Plaintext held in ref (not state / not TanStack cache); dialog returns null when closed → textarea detached from DOM. Page reload cannot recover the value. |
| Row-scoped testids for per-row dialogs | Phase 7 Plan 02 | Playwright Browser library strict mode rejects duplicate selectors; suffix with ${key} on any form/button inside a row-mounted dialog. |
| dim_* tables: plain SMALLINT PK (not IDENTITY) when statically seeded; IDENTITY when dynamically populated | Phase 10 Plan 01 | Convention-fix: seeder uses `OVERRIDING SYSTEM VALUE=no`, so GENERATED ALWAYS blocks explicit-id YAML seeds. dim_audit_categories (static) is SMALLINT; dim_audit_event_keys (dynamic) is IDENTITY |
| Audit taxonomy joins evt_audit by TEXT code (no FK on evt_audit) | Phase 10 Plan 01 | Preserves emit_audit backward compat (CHECK + text column unchanged); v_audit_events LEFT JOINs dim_audit_categories.code + dim_audit_event_keys.key |
| Audit HTTP reads emit `audit.events.queried` fire-and-forget from separate conn | Phase 10 Plan 01 | Audit-of-reads contract (vault precedent); never couples to read tx, never fails the read |
| Node tx=caller is the default for control nodes (not tx=none) | Phase 10 Plan 01 | Matches featureflags.flags.get; nodes need ctx.conn to read. tx=none is for pure compute / request-path nodes only |
| Cross-org audit query authz at HTTP layer (fail-closed + filter auto-injection) | Phase 10 Plan 01 | Service stays composable for admin surfaces; HTTP route rejects with 403 when session org ≠ filter org, auto-injects session org when filter omitted |
| Every backend sub-feature = full vertical (backend + frontend + Robot E2E in one plan) | User directive (2026-04-16, mid 10-01) | No more backend-only plans from Plan 10-02 onward. Phase 11 + 12 plans already structured as full verticals in ROADMAP |
| Monitoring fct_* tables are catalog/registry — exempt from pure-EAV rule | Phase 13 Plan 01 | Precedent = 01_catalog fct_features/fct_sub_features/fct_nodes. Monitoring `fct_monitoring_metrics` (key/kind/buckets/cardinality) and `fct_monitoring_resources` (hashed service identity) store type-critical metadata used at ingest hot path; EAV pivot would break OTel attribute-fan performance. Documented exception, not general relaxation. |
| Monitoring fct_* use IDENTITY PKs (SMALLINT metrics, BIGINT resources) — not UUID v7 | Phase 13 Plan 01 | Registry-identity tables at hot path. Metric ID used as FK in every evt_monitoring_metric_points row (billions/day); SMALLINT = 2 bytes vs UUID = 16 bytes. Resource ID same rationale on BIGINT. Catalog precedent. |
| Monitoring evt_* use first-class OTel top-level columns, not pure-JSONB metadata | Phase 13 Plan 01 | trace_id/span_id/severity/service_name are universal OTel fields with typed indexes; relegating to JSONB blocks GIN path optimization + partition pruning. JSONB `attributes` still carries caller-specific fan-out. Event taxonomy per pillar, not generic evt_audit. |
| TIMESTAMP (UTC) used on monitoring tables — override AC-1's TIMESTAMPTZ | Phase 13 Plan 01 | Follows project-wide convention in .claude/rules/common/database.md — app always passes UTC; TIMESTAMP aligns with every other evt_*/fct_* table in the codebase. Plan text predated convention pin. |
| Monitoring fct_* skip is_test/created_by/updated_by | Phase 13 Plan 01 | No human actor on instrumentation-emitted rows. fct_monitoring_metrics is operator-registered so keeps created_at/updated_at; fct_monitoring_resources is machine-interned so keeps only created_at. |
| Ingest-path nodes skip emit_audit (hot-path audit bypass) | Phase 13 Plan 01 | Audit-of-ingest would double write amplification on telemetry. Precedent = vault.secrets.get hot-path bypass (Phase 7). 13-01 has no ingest nodes yet; carve-out recorded for 13-02/13-03. |
| Monitoring NATS JetStream bootstrap is best-effort (warning + continue on failure) | Phase 13 Plan 01 | Monitoring module is optional; NATS is a soft dependency. Backend boot must not hard-fail when NATS is absent. DLQ stream added at bootstrap so 13-04 doesn't re-migrate. |

### Git State
Last commit: c1ff157 — docs(04-orgs-workspaces): draft Plan 04-01 — Org backend (schemas/repo/service/routes + 2 nodes)
Branch: feat/pivot
Plan 07-01 + 07-02 complete — vault full-stack. 33 new files + 5 modified, ~2490 new lines (backend + frontend + E2E). Ready for full vault commit. Pre-existing uncommitted work from phases 4-6 + 9 left in place. Migrator-test drift + core Robot drift remain (pre-existing; unchanged by this session).

### Deferred Issues
None.

### Blockers/Concerns
None.

### Known Gap Closures (complete for v0.1 foundation)
- Node execution policy — Plan 02-03 ✓
- NodeContext contract — Plan 02-03 ✓
- Authorization hook (with setup bypass) — Plan 02-03 + 03-03 ✓
- Cross-import validator — Plan 02-02 ✓
- Trace propagation — Plan 02-03 ✓
- Audit scope enforcement (triple-defense) — Plan 03-03 ✓
- IAM read-path views — Plan 03-04 ✓
- First IAM vertical (iam.orgs backend) — Plan 04-01 ✓
- Vault foundation (envelope encryption, bootstrap secrets, env-var contract) — Plan 07-01 ✓
- Vault UI + reveal-once enforcement + Robot E2E — Plan 07-02 ✓
- Auth backend (credentials/sessions/auth) wiring + 26 tests green — Plan 08-01 ✓
- Audit taxonomy + query API + `audit.events.query` control node + 21 tests green — Plan 10-01 ✓

### Deferred Gaps (v0.1.5 Runtime Hardening milestone)
- Versioning operational (v1 → v2 migration pattern)
- Async effect dispatch via NATS JetStream
- APISIX gateway sync for request nodes
- Dev hot-reload of catalog on manifest change
- Bulk operation pattern documentation
- Pre-commit hook wiring for linter
- Handler class caching in runner
- NCP v1 §9 doc sync (setup bypass update)
- NCP v1 §11 doc sync (control nodes may do read-only DB ops — Plan 04-01 widening)
- Materialized views consideration if aggregation costs grow
- Refresh test_migrator.py — 11 pre-existing failures from Phase 1 refactor drift
- Consider `pool` as first-class NodeContext field (currently via extras['pool'])

## Session Continuity

Last session: 2026-04-17
Stopped at: v0.1.9 IAM Enterprise milestone created. Phase 22 directory initialized. Robot Framework removed — Playwright MCP is now the UI verification method.
Next action: /paul:plan for 22-01 — SAML 2.0 SSO
Resume file: .paul/phases/22-iam-enterprise/

---
*STATE.md — Updated after every significant action*
