---
phase: 11-notify
plan: 08
type: summary
status: complete
---

# Summary — Plan 11-08: Campaigns + Audience DSL + Scheduler

## What Was Built

### Database (Migration 028)
- `05_dim_notify_campaign_statuses` — lifecycle dim: draft(1), scheduled(2), running(3), paused(4), completed(5), cancelled(6), failed(7)
- `18_fct_notify_campaigns` — campaign records: name, template_id, channel_id, audience_query JSONB, scheduled_at, throttle_per_minute, status_id. Indexes on org+status, scheduled_at+status.
- ALTER TABLE `15_fct_notify_deliveries` ADD COLUMN `campaign_id VARCHAR(36)`. Index + partial unique index `(campaign_id, recipient_user_id, channel_id) WHERE campaign_id IS NOT NULL` for idempotent runner restarts.
- Recreated `v_notify_deliveries` to include `campaign_id`.
- New view `v_notify_campaigns` joining channel + status dims.
- Seed: `06notify_05_dim_campaign_statuses.yaml` (7 rows)

### Deliveries service + repository updated
- `create_delivery(... campaign_id=None)` — optional campaign_id propagated through service → repo
- INSERT now includes campaign_id column

### Sub-feature 10_campaigns (5 files)
- `schemas.py` — `AudienceQuery`, `CampaignCreate`, `CampaignPatch`, `CampaignRow`
- `repository.py`:
  - CRUD: list, get, create, update, delete (soft)
  - `poll_scheduled_campaigns()` — status=2 AND scheduled_at <= NOW()
  - `update_campaign_status()` — runner status transitions
  - `get_audience_user_ids()` — cross-schema query against `03_iam.40_lnk_user_orgs` + `03_iam.v_users`
  - `_parse_ts()` — ISO 8601 string → datetime for asyncpg
- `service.py`:
  - `create_campaign()` — resolves channel_code → channel_id; sets draft/scheduled status based on scheduled_at presence
  - `update_campaign()` — validates mutable status; schedule/cancel transitions; rejects running/completed/failed edits
  - `delete_campaign()` — rejects running campaigns
  - `resolve_audience()` — delegates to repo audience query
- `routes.py` — 5 routes (GET list, POST, GET one, PATCH, DELETE 204)

### Campaign runner (campaign_runner.py)
- Polls every 60s for scheduled campaigns with scheduled_at <= NOW()
- Per-campaign: scheduled → running → creates deliveries per audience user → completed (or failed on error)
- Respects preference opt-out via `pref_service.is_opted_in()` per channel×category
- Critical templates fan out to all 3 channels
- Throttle: batches of min(throttle_per_minute, 100) per iteration; sleeps 60s between batches
- Idempotent: partial unique index on deliveries prevents double-send on runner restart

### Main.py
- Added `_notify_campaign_task` — started and cancelled in lifespan block
- `start_campaign_runner(pool)` called after webpush sender

### Feature manifest + routes aggregator updated
- Campaign sub-feature (number 10) added to `feature.manifest.yaml`
- `_campaigns.router` added to `routes.py`

### Frontend
- `frontend/src/types/api.ts` — `Campaign`, `CampaignListResponse`, `CampaignCreate`, `CampaignPatch`, `CampaignStatusCode`, `AudienceQuery`
- `frontend/src/features/notify/hooks/use-campaigns.ts` — `useCampaigns`, `useCampaign`, `useCreateCampaign`, `useUpdateCampaign`, `useDeleteCampaign`
- `frontend/src/app/(dashboard)/notify/campaigns/page.tsx` — campaign list with status badge, scheduled_at, throttle, cancel/delete actions
- `frontend/src/config/features.ts` — Campaigns sub-feature added to notify nav

## Test Results

13/13 tests green (`tests/test_notify_campaigns_api.py`):
- Service (7): draft creation, scheduled creation, schedule from draft, cancel scheduled, reject running edit, soft-delete, empty audience
- HTTP (6): POST auth guard, POST creates (201), GET list, GET one, PATCH name, DELETE 204

Combined (37/37): preferences + campaigns + deliveries-patch all green.
TypeScript: clean compile.

## Key Decisions Made

1. **campaign_id on deliveries** — added nullable column + partial unique index for idempotency. No FK constraint (avoids cross-plan ordering risk); comment documents the intent.
2. **Audience DSL minimal** — `{}` = all org users; `{account_type_codes:[...]}` = filter by type. More complex filters (workspace, custom attributes) deferred to later.
3. **Campaign runner serial** — processes one campaign at a time to keep DB load predictable. Parallel execution would complicate throttle accounting.
4. **throttle_per_minute** — batch size = min(throttle, 100); 60s sleep between batches. Simple and observable.
5. **`+ New campaign` button disabled** — campaign creation UI requires template picker (Plan 11-09 designer). Button is present but disabled with tooltip explaining the dependency.

## Files Created/Modified

**Created:**
- `03_docs/features/06_notify/05_sub_features/10_campaigns/09_sql_migrations/02_in_progress/20260417_028_notify-campaigns.sql` (→ 01_migrated)
- `03_docs/features/06_notify/05_sub_features/10_campaigns/09_sql_migrations/seeds/06notify_05_dim_campaign_statuses.yaml`
- `backend/02_features/06_notify/sub_features/10_campaigns/__init__.py`
- `backend/02_features/06_notify/sub_features/10_campaigns/schemas.py`
- `backend/02_features/06_notify/sub_features/10_campaigns/repository.py`
- `backend/02_features/06_notify/sub_features/10_campaigns/service.py`
- `backend/02_features/06_notify/sub_features/10_campaigns/routes.py`
- `backend/02_features/06_notify/campaign_runner.py`
- `frontend/src/features/notify/hooks/use-campaigns.ts`
- `frontend/src/app/(dashboard)/notify/campaigns/page.tsx`
- `tests/test_notify_campaigns_api.py`

**Modified:**
- `backend/02_features/06_notify/sub_features/06_deliveries/service.py` (campaign_id param)
- `backend/02_features/06_notify/sub_features/06_deliveries/repository.py` (campaign_id in INSERT)
- `backend/02_features/06_notify/routes.py` (include campaigns router)
- `backend/02_features/06_notify/feature.manifest.yaml` (campaigns sub-feature)
- `backend/main.py` (campaign runner lifespan)
- `frontend/src/types/api.ts` (Campaign types)
- `frontend/src/config/features.ts` (notify nav campaigns link)
