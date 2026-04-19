# ADR-030: Audit vs Product Event Streams

**Status:** Accepted
**Date:** 2026-04-19
**Related:** ADR-026 (minimum surface principle), Phase 3 Plan 03 (audit scope triple-defense), Phase 10 (audit analytics — funnels/retention on `evt_audit`), Phase 13 (monitoring telemetry pillars).

---

## Context

Phase 10 shipped a PostHog-class analytics surface — typed taxonomy, query API, funnels, retention, saved views, real-time tail — over the `evt_audit` event stream. The natural next question: "can we point this at marketing/product analytics too?" (UTM attribution, anonymous visitor tracking, link-click events, referral conversions.)

Two paths were considered:

1. **Single stream** — store product/marketing events in `evt_audit`, gate them with a new `audit_category` (`product`) and a soft scope contract that allows `user_id IS NULL`.
2. **Two streams** — keep `evt_audit` as the server-side compliance trail it is today; introduce a separate `evt_product_events` stream with its own privacy contract, partitioning, and retention.

We pick option 2.

---

## Decision

Treat **server-side audit** and **client-side product telemetry** as two distinct event streams with two distinct contracts. Share the **query/funnel/retention engine** across them; do not share the **write path** or the **scope contract**.

| Aspect | `evt_audit` | `evt_product_events` |
|---|---|---|
| Source | Backend services + nodes | Browser SDK + server-side SDK `.product.track()` |
| Scope contract | `user_id + session_id + org_id + workspace_id` mandatory (DB CHECK + Pydantic + handler triple-defense). Bypasses: `setup` category, `failure` outcome. | `visitor_id` mandatory; `user_id`, `session_id`, `org_id`, `workspace_id` all optional (anonymous-first). `workspace_id` resolved from project key at ingest. |
| Identity | IAM-identified actors only | Anonymous visitor (cookie UUID v7) + optional alias graph to IAM users via `lnk_visitor_aliases` |
| Mutability | Append-only, immutable | Append-only, immutable |
| Cardinality | Bounded by IAM action set + features (~10²–10³ event keys per workspace) | Caller-defined event names; capped at 500 distinct/workspace/day default (operator-tunable). UTM values capped at 256 chars at SDK. |
| Privacy contract | Compliance trail; PII allowed when business-justified | Privacy-first: IP truncated by default, `email`/`phone` props hashed unless workspace opts in, DNT respected, GDPR consent gate |
| Write path | `audit.events.emit` node, `tx=caller` (atomic with caller's tx) | `product.events.ingest` node, `tx=own`, batched via `POST /v1/track` |
| Audit-of-itself | N/A (it is the audit) | Each ingest batch emits one `audit.events.emit("product.events.ingested", {batch_size, workspace_id})` summary row — NOT one audit per event (audit amplification; vault hot-path bypass precedent) |
| Partitioning | Single table, retention via vacuum | Daily range partitions + `pg_cron` rollups + retention tiers (Phase 13 monitoring precedent) |
| Schema | `04_audit` | `10_product_ops` |

The query/funnel/retention engine (Phase 10) is **generalized in Phase 48** to take a target table parameter (`audit.events.funnel` → `events.funnel(table=..., filters=..., steps=...)`) so the same UI can render funnels over either stream.

---

## Why not a single stream

**Scope contract incompatibility.** The audit triple-defense (DB CHECK + Pydantic + handler) treats missing `user_id`/`session_id`/`org_id`/`workspace_id` as a validation failure with two narrow bypasses (setup, failure). Anonymous browser visitors **always** miss `user_id` and `session_id` and **frequently** miss `org_id`/`workspace_id`. To accept product events into `evt_audit`, we'd need a permanent third bypass that swallows ~99% of writes — at which point the constraint is no longer load-bearing and the compliance guarantee is gone.

**Cardinality + retention shape.** Audit is low-cardinality, high-value, long-retention (often forever for compliance). Product events are high-cardinality, low-individual-value, short/tiered retention (rollups for old data, raw for recent). Mixing them forces compromise on indexes, partition strategy, and storage tier. Phase 13 monitoring already established the pattern of "telemetry pillar gets its own evt_*"; product events follow the same precedent.

**Privacy contract divergence.** Compliance audit must capture full actor identity. Product analytics must default to **least PII** (truncated IP, hashed PII props, opt-in raw). Sharing a table means the lower bar wins for everything stored together, weakening compliance guarantees without strengthening privacy.

---

## What is shared

- **Query DSL shape** (Phase 10's typed filter tree + cursor + timerange) — both streams use the same client-side query builder and same backend compiler.
- **Funnel / retention / cohort engine** — generalized to take a target table parameter in Phase 48.
- **Saved views** — workspace-scoped, can target either stream.
- **Live tail UI component** — reuses the audit explorer's LISTEN/NOTIFY tail, parametrized on table.
- **Outbox** — both streams emit to the same outbox channel with a `stream` discriminator, so downstream consumers (Notify, webhooks, exports) can subscribe to either or both.

---

## What is different

- **Write nodes** are separate: `audit.events.emit` (compliance) vs `product.events.ingest` (telemetry).
- **Read views** are separate: `v_audit_events` vs `v_product_events`. Each does its own EAV pivot and FK hiding.
- **Schema** is separate: `04_audit` stays for compliance; `10_product_ops` is new.
- **Module gate** is separate: `audit` is always on (`core+iam+audit` mandatory); `product_ops` is optional (off by default).
- **Endpoints** are separate: `/v1/audit/*` for audit reads; `/v1/track` for product ingest, `/v1/product/*` for product reads.

---

## Consequences

**Positive:**
- Compliance audit guarantee remains absolute (no permanent bypass).
- Product analytics gets a privacy-first contract from day one.
- Each stream can evolve its partition/retention strategy independently.
- The audit module stays small and shippable in `core+iam+audit` minimum deployments. Product analytics stays optional.
- Funnel UI, query DSL, and outbox machinery are reused — no duplication of the analytics engine.

**Negative:**
- Two `evt_*` tables to learn instead of one. Mitigated by shared query DSL: end users see one funnel UI, one event explorer shape.
- A "registered user signs up after clicking a referral link" journey crosses both streams: the referral click is a product event, the signup is an audit event. Funnels that span both streams require a UNION-view in Phase 48 (`v_unified_events`) or workspace-scoped joining at query time. Documented as future work, not a v0.5.0 blocker.
- Operators running `product_ops` need to size Postgres for higher write rates (mitigated: optional module, daily partitions, pg_cron rollup precedent from Phase 13).

---

## Alternatives Considered

1. **Single `evt_unified` table with discriminator column** — rejected: forces audit triple-defense to relax for the common case, breaking compliance guarantee.
2. **Push product events to NATS → ClickHouse** — rejected for v1: violates self-host-friendly constraint (would require ClickHouse in docker-compose). Postgres + partitions + pg_cron is sufficient for the scale Mixpanel/PostHog free-tier targets serve. Revisit at v0.6+ if data volume forces it.
3. **Re-use `evt_monitoring_*` from Phase 13** — rejected: monitoring is OTel-shaped (logs/metrics/spans) and resource-interned (Phase 13 `fct_monitoring_resources`); product events are visitor-shaped and event-named. Different fact-table identity, different attributes-fan, different consumers (ops vs growth).

---

## Future Work

- **`v_unified_events` view** for cross-stream funnels (audit signup conversion + product click attribution in one funnel) — Phase 48 follow-up if user demand surfaces.
- **Person-merge worker** if SDK adoption shows that the simple `lnk_visitor_aliases` many-to-one model loses cross-device journeys (PostHog-style person-merge). Default plan: Mixpanel-style alias graph is enough.
- **Multi-touch attribution models** (linear, time-decay, position-based) — v0.5.x once first/last-touch data validates the storage shape.
