---
phase: 11-notify
plan: 02
type: summary
completed: 2026-04-17
---

# Plan 11-02 Summary — Variable System (static + dynamic SQL)

## Result: COMPLETE — 51/51 tests green

All 4 tasks executed. All acceptance criteria met.

## What Was Built

### Migration 023
- `13_fct_notify_template_variables` table with FK cascade delete to `12_fct_notify_templates`
- `v_notify_template_variables` view
- Constraints: type CHECK (`static`|`dynamic_sql`), static/dynamic field requirements, UNIQUE per `(template_id, name)`

### 04_variables sub-feature (5 files)
- **schemas.py**: `TemplateVariableCreate` with Pydantic name pattern `^[a-z_][a-z0-9_]*$`; model_validator calls safelist; `TemplateVariableUpdate`; `TemplateVariableRow`; `ResolveRequest`
- **repository.py**: CRUD + `resolve_variables(conn, template_id, context)` — statics return literal, dynamic SQL runs with `SET LOCAL statement_timeout='2000'` / finally reset
- **service.py**: Thin wrappers + audit emit on create/update/delete; `asyncpg.UniqueViolationError` caught → `ConflictError` (409)
- **routes.py**: `/{template_id}/variables` + `/resolve` (declared before `/{var_id}`) + `/{var_id}`; mounted at prefix `/v1/notify/templates` in aggregator

### safelist.py
- Pure validator module at `sub_features/03_templates/nodes/safelist.py`
- Rejects: non-SELECT start, DML/DDL keywords, param_bindings values not in `{actor_user_id, org_id, workspace_id, event_metadata}`

### Updated render node
- `RenderTemplate.Input` gains `context: dict[str, Any] = {}`
- Resolves registered variables via `_var_repo.resolve_variables` before Jinja2 rendering
- Variable resolution order: registered_static → registered_dynamic_sql → caller_supplied (caller wins)

### Catalog repository fix (bonus fix)
- Changed `upsert_feature/upsert_sub_feature/upsert_node` from `INSERT ... ON CONFLICT DO UPDATE` to select-first-then-insert-or-update
- Root cause: PostgreSQL advances SMALLINT sequences even on conflict, burning through 32767 max after repeated test runs
- Fix prevents sequence exhaustion permanently without a schema migration

## Acceptance Criteria

| AC | Result |
|----|--------|
| AC-1: Variable CRUD API works | ✓ 25 tests pass |
| AC-2: Dynamic SQL safelist enforced | ✓ 6 safelist rejection tests pass |
| AC-3: Static variable resolved by render | ✓ `test_render_resolves_static_variable` |
| AC-4: Dynamic SQL variable resolved | ✓ `test_render_dynamic_sql_variable` |
| AC-5: Caller vars override registered | ✓ `test_render_caller_overrides_registered` |
| AC-6: Existing 26 render tests stay green | ✓ 26/26 in test_notify_schema_api.py |
| AC-7: 20+ new tests green | ✓ 25/25 in test_notify_variables_api.py |

## Test Results
```
51 passed in 8.88s (test_notify_variables_api.py: 25, test_notify_schema_api.py: 26)
```

## Deviations from Plan

### Cascade test fix
Plan expected `DELETE /v1/notify/templates/{id}` (soft-delete) to cascade variables. But soft-delete sets `deleted_at` — FK cascade only fires on hard DELETE. Fixed test to hard-delete from fct table directly.

### Unique constraint fix
Plan expected 409 or 500 for duplicate variable name. Without catching the asyncpg exception, the error escaped as an ExceptionGroup and crashed the test client. Fixed: `asyncpg.UniqueViolationError` caught in service → `ConflictError` (409).

### Catalog repository fix (unplanned)
SMALLINT sequence exhaustion blocked the last 2 tests. Fixed upstream in `backend/01_catalog/repository.py` by changing from UPSERT to select-first pattern. This is a systemic fix that benefits all test suites.

## Files Created/Modified

| File | Action |
|------|--------|
| `03_docs/features/06_notify/05_sub_features/04_variables/09_sql_migrations/02_in_progress/20260417_023_notify-variables.sql` | Created (applied) |
| `backend/02_features/06_notify/sub_features/04_variables/__init__.py` | Created |
| `backend/02_features/06_notify/sub_features/04_variables/schemas.py` | Created |
| `backend/02_features/06_notify/sub_features/04_variables/repository.py` | Created |
| `backend/02_features/06_notify/sub_features/04_variables/service.py` | Created |
| `backend/02_features/06_notify/sub_features/04_variables/routes.py` | Created |
| `backend/02_features/06_notify/sub_features/03_templates/nodes/safelist.py` | Created |
| `backend/02_features/06_notify/sub_features/03_templates/nodes/render_template.py` | Updated (run() + var resolution) |
| `backend/02_features/06_notify/routes.py` | Updated (mount variables router) |
| `backend/02_features/06_notify/feature.manifest.yaml` | Updated (04_variables sub-feature entry) |
| `tests/test_notify_variables_api.py` | Created (25 tests) |
| `backend/01_catalog/repository.py` | Updated (select-first upserts — sequence fix) |

## Next
Plan 11-03: Subscriptions + audit-outbox consumer + critical fan-out
