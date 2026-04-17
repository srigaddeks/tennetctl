# Plan 18-01 Summary — Per-Template Analytics

**Status:** COMPLETE
**Date:** 2026-04-17

## What Was Built

### Backend
- `03_templates/repository.get_template_analytics(conn, template_id)` — aggregates two queries against `v_notify_deliveries` (status breakdown) and `v_notify_delivery_events` (event-type breakdown). Returns `{by_status, by_event_type, total_deliveries}`.
- `GET /v1/notify/templates/{id}/analytics` — session-required; returns the aggregate envelope.

### Frontend
- Type: `NotifyTemplateAnalytics`.
- Hook: `useTemplateAnalytics(id)`.
- Template detail page (`/notify/templates/[id]`): inline Analytics strip between the top toolbar and the body editor. Shows Total / Sent / Delivered / Opened / Clicked / Bounced / Failed cards. Only rendered when `total_deliveries > 0` (avoids empty-state noise on fresh templates). Bounced + Failed cards get red tone.

## Acceptance criteria

| AC | Status |
|---|---|
| AC-1: GET /v1/notify/templates/{id}/analytics returns counts + funnel | ✅ |
| AC-2: Template detail page shows counts | ✅ |

## Files

Backend: `03_templates/repository.py`, `03_templates/routes.py`.

Frontend: `types/api.ts`, `features/notify/hooks/use-templates.ts`, `app/(dashboard)/notify/templates/[id]/page.tsx` (+ `AnalyticsCard` helper).
