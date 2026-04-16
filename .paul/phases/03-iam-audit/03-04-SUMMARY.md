---
phase: 03-iam-audit
plan: 04
subsystem: database
tags: [views, eav, dim-attr-defs, read-path, v_orgs, v_workspaces, v_users]

requires:
  - phase: 03-iam-audit-01
    provides: "03_iam" schema + fct tables + EAV tables
  - phase: 03-iam-audit-02
    provides: IAM feature manifest (owns.tables declarations)
provides:
  - 5 seeded dim_attr_defs rows (org.display_name, workspace.display_name, user.email/display_name/avatar_url)
  - v_orgs — flat read shape with display_name pivot
  - v_workspaces — flat read shape with display_name pivot + org_id
  - v_users — flat read shape with account_type dim resolution + email/display_name/avatar_url pivot
  - 3 pytest smoke tests proving view correctness
affects: [Phase 4 Orgs/Workspaces repositories, Phase 5 Users repository, all future repos that SELECT * FROM v_*]

tech-stack:
  added: []
  patterns:
    - "EAV pivot via `MAX(key_text) FILTER (WHERE ad.code = '<attr>')` — scales as attrs grow, single GROUP BY per view"
    - "LEFT JOIN pattern for attrs — entities without any dtl_attrs still appear with NULL attr columns"
    - "Hide internal FK columns in views (v_users exposes account_type TEXT, not account_type_id SMALLINT)"
    - "View migration per sub-feature under its own 00_bootstrap — orgs/workspaces/users each own their view SQL"

key-files:
  created:
    - 03_docs/features/03_iam/00_bootstrap/09_sql_migrations/seeds/05_dim_attr_defs.yaml
    - 03_docs/features/03_iam/05_sub_features/01_orgs/00_bootstrap/09_sql_migrations/01_migrated/20260416_002_iam-orgs-view.sql
    - 03_docs/features/03_iam/05_sub_features/02_workspaces/00_bootstrap/09_sql_migrations/01_migrated/20260416_003_iam-workspaces-view.sql
    - 03_docs/features/03_iam/05_sub_features/03_users/00_bootstrap/09_sql_migrations/01_migrated/20260416_004_iam-users-view.sql
    - tests/test_iam_views.py
  modified: []

key-decisions:
  - "attr_defs uses GENERATED ALWAYS AS IDENTITY on PK; seed omits id field; migrator auto-generates. Uniqueness via (entity_type_id, code) makes re-seed idempotent"
  - "View resolves account_type via JOIN to dim_account_types, exposes TEXT code not SMALLINT id — hides internal FK"
  - "MAX(...) FILTER (WHERE ad.code = '...') aggregation chosen over LATERAL subqueries — scales better as more attrs are added per view"

patterns-established:
  - "Pattern: feature-level shared dim seeds (like dim_attr_defs, but only the attrs; attr values go in dtl_attrs via sub-features)"
  - "Pattern: GROUP BY every non-aggregated column explicitly, even though Postgres accepts shorthand"
  - "Pattern: LEFT JOIN dtl_attrs + LEFT JOIN attr_defs chain for EAV pivots"

duration: ~10min
started: 2026-04-16T13:45:00Z
completed: 2026-04-16T13:55:00Z
---

# Phase 3 Plan 04: Views + EAV Attr Registration — Summary

**IAM read paths live: `v_orgs`, `v_workspaces`, `v_users` views pivot EAV rows into flat shape; 5 dim_attr_defs seeded. Phase 4+ repositories can now `SELECT * FROM "03_iam"."v_{entity}"` instead of hand-writing EAV joins.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~10min |
| Tasks | 3 auto + 1 checkpoint (self-verified) |
| Migrations applied | 3 views |
| Seed rows added | 5 attr_defs |
| Tests passing | 19/19 (3 new + 16 prior) |

## Acceptance Criteria Results

| Criterion | Status | Evidence |
|-----------|--------|----------|
| AC-1: dim_attr_defs seeded | Pass | 5 rows: org.display_name, workspace.display_name, user.{email, display_name, avatar_url} |
| AC-2: v_orgs exposes display_name | Pass | `test_v_orgs_surfaces_display_name` — named org returns "Named Corp"; attr-less org returns NULL |
| AC-3: v_workspaces exposes org_id + slug + display_name | Pass | `test_v_workspaces_surfaces_display_name` — 4 columns populated |
| AC-4: v_users resolves account_type + exposes email/display_name/avatar_url | Pass | `test_v_users_resolves_account_type_and_attrs` — account_type='email_password' resolved from dim; account_type_id hidden |
| AC-5: pytest suite green | Pass | pytest 19/19, zero regressions |

## Accomplishments

- **Read paths for Phase 4** — no repo in future verticals needs to write EAV join boilerplate; they just SELECT from the view.
- **Hidden internal FKs** — v_users exposes `account_type` TEXT, `account_type_id` SMALLINT is invisible. Future refactors of dim_account_types don't break API consumers.
- **EAV pivot pattern locked in** — every future attr added to dim_attr_defs just needs one extra `MAX(...) FILTER` line in the view, no schema change.

## Files Created/Modified

See key-files frontmatter above. 4 new SQL/YAML files + 1 new test file; no existing files modified.

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| GENERATED IDENTITY PK on dim_attr_defs + seed omits id | Attrs grow dynamically as features expand; (entity_type_id, code) uniqueness provides stable upsert semantics | Re-seed is idempotent; new attrs simply get next auto-id |
| FILTER-based EAV pivot (not LATERAL) | Single GROUP BY scales; adding 10th attr is one more FILTER line | Every IAM view uses this pattern |
| account_type_id hidden in v_users | Consumers see semantic code, not FK id; internal refactors invisible | Set precedent: hide internal FKs in views; expose resolved dim codes |

## Deviations from Plan

None — plan executed exactly as written. No spec corrections, no scope additions, no deferred items. All 5 ACs pass on first attempt.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- Phase 4 Plan 01 (Org sub-feature) can immediately write `SELECT * FROM "03_iam"."v_orgs" WHERE id = $1` in its repository.
- All 6 IAM sub-feature directories have `00_bootstrap/` present; Phase 4+ adds view migrations for roles/groups/applications as each vertical ships.
- Every future node calls `run_node("audit.events.emit", ctx, {...})` after mutation; audit scope propagates automatically.

**Concerns:**
- Views use `GROUP BY` on every non-aggregated column — boilerplate grows as fct_* tables add columns. Acceptable for v1; if it becomes unwieldy, consider materialized views or JOIN LATERAL alternatives in v0.1.5.
- No role/group/application views yet — deferred to their respective Phase 6 plans.

**Blockers:**
- None. Phase 3 complete. Ready for Phase 4 transition.

---
*Phase: 03-iam-audit, Plan: 04*
*Completed: 2026-04-16*
