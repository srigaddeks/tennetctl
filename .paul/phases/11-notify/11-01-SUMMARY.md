---
phase: 11-notify
plan: 01
subsystem: api
tags: [notify, jinja2, smtp, templates, asyncpg, fastapi, pytest]

requires:
  - phase: 03-iam-audit
    provides: audit emit infrastructure + evt_audit schema
  - phase: 07-vault
    provides: VaultClient for smtp auth_vault_key reference pattern

provides:
  - "06_notify schema with 4 dim + 3 fct + 1 dtl tables + 4 views"
  - "SMTP configs CRUD (POST/GET/PATCH/DELETE /v1/notify/smtp-configs)"
  - "Template groups CRUD (POST/GET/PATCH/DELETE /v1/notify/template-groups)"
  - "Templates CRUD + body upsert (POST/GET/PATCH/DELETE /v1/notify/templates + PUT bodies)"
  - "notify.templates.render node (Jinja2 StrictUndefined, control, tx=caller)"
  - "Feature manifest registered in catalog"
  - "26 pytest tests green"

affects: [11-notify-plans-02-12, 12-iam-security-completion]

tech-stack:
  added: [jinja2]
  patterns:
    - "json_agg bodies aggregation in v_notify_templates — asyncpg returns as string, must json.loads()"
    - "ON CONFLICT DO UPDATE for template body upsert per (template_id, channel_id)"
    - "Node.run() + Pydantic inner Input/Output classes — required by catalog runner"
    - "Function-scoped live_app fixture with lifespan context — avoids cross-loop asyncpg issues"
    - "Self-contained tests with helper functions (_create_smtp, _create_group, _create_template)"

key-files:
  created:
    - backend/02_features/06_notify/feature.manifest.yaml
    - backend/02_features/06_notify/routes.py
    - backend/02_features/06_notify/sub_features/01_smtp_configs/ (5 files)
    - backend/02_features/06_notify/sub_features/02_template_groups/ (5 files)
    - backend/02_features/06_notify/sub_features/03_templates/ (5 files + nodes/render_template.py)
    - tests/test_notify_schema_api.py (26 tests)
    - 4 migration SQL files (019–022, all applied)
    - 4 dim seed YAML files (channels/categories/statuses/priorities, all applied)
  modified:
    - backend/main.py (notify in MODULE_ROUTERS)
    - backend/01_core/config.py (_DEFAULT_MODULES includes notify)
    - .env (TENNETCTL_MODULES includes notify)

key-decisions:
  - "Node uses run(ctx, inputs) + Pydantic inner Input/Output classes — not handle() with dataclasses"
  - ".env must be updated when adding modules (overrides _DEFAULT_MODULES in config.py)"
  - "json_agg in v_notify_templates returns string from asyncpg — json.loads() required in _row_to_dict"
  - "Function-scoped live_app fixture required — module-scoped causes cross-event-loop asyncpg errors"
  - "Static subject in test_render_with_static_variables — avoids StrictUndefined firing on subject"

patterns-established:
  - "Notify sub-features: 5-file pattern (schemas/repo/service/routes/__init__)"
  - "Template bodies: separate dtl table with ON CONFLICT upsert; fetched via json_agg in view"
  - "render node: control kind, tx=caller, Jinja2 StrictUndefined, raises ValueError on missing template/channel"

duration: ~2 sessions (split across context boundary)
started: 2026-04-17T00:00:00Z
completed: 2026-04-17T00:00:00Z
---

# Phase 11 Plan 01: Notify Schema + SMTP + Template Groups + Templates Summary

**Notify foundational backend: 4 migrations applied, 3 backend sub-features with full CRUD, Jinja2 render node, 26 pytest tests green.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~2 sessions |
| Tasks | 13 completed |
| Files created | ~25 |
| Files modified | 3 |
| Tests | 26 passed |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: 06_notify schema + 4 dim + 3 fct + 1 dtl + 4 views migrated | Pass | Migrations 019–022 applied |
| AC-2: Dim seeds applied (channels/categories/statuses/priorities) | Pass | 4 YAML seed files applied |
| AC-3: SMTP configs CRUD works | Pass | 6 tests green |
| AC-4: Template groups CRUD works | Pass | 5 tests green |
| AC-5: Templates CRUD + body management works | Pass | 9 tests green (incl. upsert + idempotent) |
| AC-6: notify.templates.render renders Jinja2 + StrictUndefined | Pass | 5 render tests green |
| AC-7: Feature registered in catalog | Pass | feature.manifest.yaml + MODULE_ROUTERS |
| AC-8: 20+ pytest tests green | Pass | 26 tests green |

## Accomplishments

- Full `06_notify` schema: dim tables (channels/categories/statuses/priorities), fct_notify_smtp_configs, fct_notify_template_groups, fct_notify_templates + dtl_notify_template_bodies, 4 views with aggregations
- 3 backend sub-features (smtp_configs, template_groups, templates) following 5-file pattern with audit emission on every mutation
- `notify.templates.render` node using Jinja2 StrictUndefined — raises on missing variables, fetches from DB, renders subject + html + text body
- `notify` module enabled in `.env`, `config.py`, `main.py`, and `feature.manifest.yaml`

## Deviations from Plan

| Type | Detail |
|------|--------|
| Auto-fix | Node class used `handle()` + `@dataclass` I/O instead of `run()` + Pydantic inner classes — fixed to match catalog runner contract |
| Auto-fix | `.env` not updated initially → notify routes never mounted; required explicit edit to TENNETCTL_MODULES |
| Auto-fix | Module-scoped `live_app` fixture caused cross-event-loop asyncpg errors → changed to function-scoped |
| Auto-fix | Sequential test dependencies broken by function-scoped fixture → rewrote all tests as self-contained with helper functions |
| Auto-fix | `test_render_with_static_variables` used subject `"Hello {{ name }}!"` without `name` variable → fixed to use static subject |

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Node base class uses `run(ctx, inputs)` not `handle(ctx, config, inputs)` | Rewrote RenderTemplate to use `run()` + Pydantic inner `Input`/`Output` |
| `asyncpg json_agg` returns Python string not parsed JSON | Added `json.loads()` in `_row_to_dict` in templates repository |
| `.env` TENNETCTL_MODULES overrides `_DEFAULT_MODULES` — notify not loaded | Updated `.env` to include `notify` |
| `pytest-asyncio` cross-loop error with module-scoped fixture | Function-scoped `live_app` fixture with lifespan context |

## Next Phase Readiness

**Ready:**
- Notify schema and dim tables are the foundation for all subsequent notify plans
- SMTP config CRUD is the dependency for email delivery (Plan 11-04)
- Template system (groups + templates + render node) is the foundation for all channel delivery plans
- `notify.templates.render` node tested and working — Plan 11-10 transactional API can call it directly

**Concerns:**
- None blocking

**Blockers:**
- None

---
*Phase: 11-notify, Plan: 01*
*Completed: 2026-04-17*
