# Phase 60 — GDPR DSAR Flows

**Milestone:** v0.8.0 Product Analytics Completion
**Status:** CONTEXT (awaiting PLAN)
**Created:** 2026-04-20

## Goal

Legal blocker closure. EU customers cannot self-host a product analytics platform without DSAR (Data Subject Access Request) primitives: export-all + delete-all per visitor/user.

## Success Criteria

- [ ] `POST /v1/product-visitors/{id}/export` — returns JSON dump of visitor profile + all events + all aliases + all touches + all redemptions + all group memberships. Async for > 10k rows (returns job_id, polls at `/jobs/{id}`).
- [ ] `DELETE /v1/product-visitors/{id}?cascade=true` — soft-delete visitor + HARD-delete all evt_product_events + evt_attribution_touches + evt_promo_redemptions + dtl_visitor_attrs + lnk_visitor_aliases for that visitor_id. Returns 204 + audit row.
- [ ] Cascade is truly hard-delete (not soft) — GDPR requires actual erasure
- [ ] Every DSAR export + delete writes a `dsar.exported` / `dsar.deleted` audit row with actor_user_id + visitor_id + row_counts_by_table
- [ ] Rate-limited: max 10 DSAR ops per workspace per hour (prevents abuse)
- [ ] Admin page `/product/dsar` — operator UI for triggering + viewing DSAR history

## Approach

- New sub-feature `product_ops.dsar`
- Export: SQL-driven, concat-streams JSON to response (chunked for large sets)
- Delete: single tx across all product_ops tables for the visitor_id; idempotent
- Background job table `evt_dsar_jobs` for async exports

## Dependencies

- Phase 45 (evt_product_events) — shipped
- Phase 10 (audit) — shipped
- Phase 49 (profiles) — shipped
- Phase 57 (group memberships) — upstream dep (DSAR must clean group links too)

## Out of Scope

- Cross-feature DSAR (IAM users, billing records, etc.) — defer to v1.0.0 platform-wide DSAR epic
- Automated DSAR (triggered by user self-service UI) — defer; operator-triggered only in v1

## Plans

- 60-01 — export + delete + audit + rate limit + admin UI

## Open Questions

- Export format: raw JSON vs CSV-per-table in ZIP? (leaning JSON single file for simplicity)
- Retention for DSAR audit rows: forever, or 7-year legal minimum? (leaning forever)
