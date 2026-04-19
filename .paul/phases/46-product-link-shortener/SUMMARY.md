# Phase 46 — Link Shortener — SUMMARY

**Status:** APPLY complete (single-plan vertical).
**Date:** 2026-04-19

## What was built

### Schema (1 migration, NNN=060)

- `10_fct_short_links` — slug + target_url + UTM preset (FK to dim_attribution_sources). UNIQUE per (workspace_id, slug). Standard fct_* mandatory columns + soft-delete.
- `v_short_links` view — resolves utm_source FK → TEXT, derives is_deleted.

### Backend sub-feature (`product_ops.links`)

- `schemas.py` — Pydantic v2: CreateShortLinkBody (slug regex, target_url, optional UTM preset), UpdateShortLinkBody, ShortLinkOut
- `repository.py` — insert/get-by-slug/get-by-id/list/update/soft_delete
- `service.py` — create_link (auto-mint slug with retry on collision; emits audit), resolve_redirect (slug → target + writes click event + UTM touch directly to evt_product_events; click is hot-path, no audit), update_link, delete_link
- `routes.py` — public `GET /l/{slug}` redirect (302) + admin CRUD (5-endpoint shape per ADR-026): list, create, get, patch, delete

### Manifest

- New sub-feature `product_ops.links` registered with 6 routes + 0 nodes (intentional — links are pure CRUD; no cross-feature run_node calls needed)

### Frontend

- `types/api.ts`: ShortLink, ShortLinkListResponse, CreateShortLinkBody
- `features/product-ops/hooks/use-short-links.ts`: useShortLinks, useCreateShortLink, useDeleteShortLink (TanStack mutations)
- `app/(dashboard)/product/links/page.tsx`: list + inline create form + delete-with-confirm; sidebar entry `/product/links`

## Verification

| Check | Result |
|---|---|
| Backend imports clean | ✅ |
| Manifest validates (2 sub-features now: events + links) | ✅ |
| Frontend `npx tsc --noEmit` clean | ✅ |
| Live migrator + smoke test | ⚠ DEFERRED — operator runs |

## Files

- New: 6 (SQL migration, 4 backend files, 2 frontend files)
- Modified: 4 (manifest, top-level routes.py, types/api.ts, features.ts)
- ~900 new lines

## Decisions

- **Click events written directly to evt_product_events from links service** (not via product_ops.events.ingest node). Reason: ingest node requires project_key resolution via vault; links already know their workspace_id. Direct repo write is faster and decoupled. Audit-of-clicks intentionally skipped (hot path, vault precedent).
- **Slug auto-mint** uses `secrets.choice` over base32 alphabet (excludes 0/1/l for legibility); 8 chars; retry on UNIQUE collision up to 5 times.
- **Slug regex** allows `[A-Za-z0-9_-]{2,64}` — operator can supply human-friendly slugs.
- **Sub-feature `product_ops.links` has 0 nodes** — intentional. No cross-feature callers in v1; the redirect is HTTP-only. Phase 47 (referrals) will introduce a node when it needs to call link creation programmatically.
