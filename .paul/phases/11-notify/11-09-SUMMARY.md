---
phase: 11-notify
plan: 09
type: summary
status: complete
---

# Summary — Plan 11-09: Template Designer UI

## What Was Built

### Backend
- `TestSendRequest` Pydantic schema in `schemas.py` (`to_email`, `context` fields)
- `send_test_email(conn, *, template_id, to_email, context, vault)` in `service.py`:
  - Loads template + email body (channel_id=1)
  - Resolves template group → SMTP config → vault password
  - Resolves template variables via `var_service.resolve_variables`
  - Renders subject + body via Jinja2 (no tracking pixels — test send)
  - Sends via `aiosmtplib`, returns `to_email`
- `POST /v1/notify/templates/{template_id}/test-send` route in `routes.py`
  - Reads vault from `request.app.state.vault`; returns 503 if vault not configured
  - Returns `{ ok: true, data: { sent_to: email } }`

### Frontend Types (api.ts)
- `NotifyPriorityCode`, `NotifyTemplateBody`, `NotifyTemplate`, `NotifyTemplateListResponse`
- `NotifyTemplateCreate`, `NotifyTemplatePatch`
- `NotifyVarType`, `NotifyTemplateVariable`, `NotifyTemplateVariableCreate`, `NotifyTemplateVariableListResponse`
- `NotifyTemplateGroup`, `NotifyTemplateGroupListResponse`

### Frontend Hooks
- `use-templates.ts` — `useTemplates`, `useTemplate`, `useCreateTemplate`, `usePatchTemplate`, `useUpsertBodies`, `useTemplateGroups`, `useTestSend`
- `use-template-variables.ts` — `useTemplateVariables`, `useCreateTemplateVariable`, `useResolveVariables`

### Nav
- `config/features.ts` — Templates nav entry added before Campaigns

### Template List Page (`/notify/templates`)
- Table: key (monospace), group, subject, priority badge, active status
- "New Template" button → Modal dialog (key, group select, subject, priority)
- On create → navigates to designer page at `/notify/templates/[id]`
- Row click → opens designer

### Template Designer Page (`/notify/templates/[id]`)
- 2-column layout (55/45 split, full viewport height)
- **Left panel:**
  - Back link + template key in header bar
  - Metadata grid: subject, reply-to, group, priority — each saves on blur via `usePatchTemplate`
  - Body tabs: Email active; Web Push + In-app disabled with "Coming soon"
  - HTML textarea + plain-text textarea (both tracked with ref for cursor insertion)
  - "Save body" → `useUpsertBodies` (channel_id=1)
- **Right panel:**
  - Preview pane — "Preview" button calls `useResolveVariables` then client-side Jinja substitution regex, renders via `dangerouslySetInnerHTML`
  - Variables panel (toggle via "Variables (N)" button):
    - Lists all variables as clickable pills — `{{ name }}` badge + type badge
    - Click inserts `{{ name }}` at cursor in active textarea via `insertVariable()`
    - "+ Add" expands `AddVariableForm` (name, type radio, static value or SQL template, description)
  - Test Send dialog: email input → `useTestSend` → shows confirmation

### Campaign Create Unblocked
- `campaigns/page.tsx` — `NewCampaignDialog` added with template picker (fetches `useTemplates`)
- "+ New campaign" button enabled (was disabled since 11-08)
- Dialog: name, template select, channel, optional schedule, throttle

### Robot E2E
- `tests/e2e/notify/11_template_designer.robot` — 2 test cases:
  - "Templates page loads and nav entry is visible"
  - "New template dialog opens" — verifies dialog fields render

## Key Decisions Made

1. **No DOMPurify server-side** — preview rendered via `dangerouslySetInnerHTML` directly; HTML comes from our own DB so XSS surface is developer-controlled. DOMPurify skipped for simplicity.
2. **Client-side Jinja substitution** — simple regex (`/\{\{\s*(\w+)\s*\}\}/g`) replaces variable tokens without a JS Jinja engine dependency. Sufficient for preview.
3. **`useUpsertBodies` orgId param removed** — bodies endpoint invalidates by template id only; orgId parameter was unused, replaced with optional `_orgId`.
4. **`FormEvent` deprecation** — warning only (★), not a build error. Not fixed to avoid unnecessary churn.
5. **Version history deferred** — needs new DB migration + version table; noted in plan scope limits.

## Files Created/Modified

**Created:**
- `frontend/src/features/notify/hooks/use-templates.ts`
- `frontend/src/features/notify/hooks/use-template-variables.ts`
- `frontend/src/app/(dashboard)/notify/templates/page.tsx`
- `frontend/src/app/(dashboard)/notify/templates/[id]/page.tsx`
- `tests/e2e/notify/11_template_designer.robot`

**Modified:**
- `backend/02_features/06_notify/sub_features/03_templates/schemas.py` (TestSendRequest)
- `backend/02_features/06_notify/sub_features/03_templates/service.py` (send_test_email)
- `backend/02_features/06_notify/sub_features/03_templates/routes.py` (test-send route)
- `frontend/src/types/api.ts` (template + variable + group types)
- `frontend/src/config/features.ts` (Templates nav entry)
- `frontend/src/app/(dashboard)/notify/campaigns/page.tsx` (create dialog unblocked)

## Verification Results
- `npm run build` → clean (25 routes)
- `pytest tests/test_notify_campaigns_api.py` → 13/13 ✓
- `pytest tests/test_notify_preferences_api.py` → 15/15 ✓
- Full suite: 345 pass, 11 fail (all pre-existing migrator drift — unchanged)
