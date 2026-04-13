# Roadmap: TennetCTL

## Overview

TennetCTL is built milestone-by-milestone from core infrastructure through enterprise IAM. Every phase after foundation is a full vertical slice: schema → repo → service → routes → nodes → UI → Playwright live verification. Nothing ships without being tested in a real browser.

## Current Milestone

**v0.1 Foundation + IAM** (v0.1.0)
Status: In progress
Phases: 1 of 6 complete (Phase 2 starting)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with [INSERTED])

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Infrastructure | 3 | ✅ Complete | 2026-04-13 |
| 2 | Schema & Audit Foundation | TBD | Not started | - |
| 3 | Orgs & Workspaces | TBD | Not started | - |
| 4 | Users & Account Types | TBD | Not started | - |
| 5 | Roles, Groups, Scopes & Applications | TBD | Not started | - |
| 6 | Auth Config & Feature Flags | TBD | Not started | - |

## Phase Details

### Phase 1: Core Infrastructure

**Goal:** Running backend + frontend shells with database, migrations, node registry skeleton, and Playwright test harness — everything needed before any feature vertical.
**Depends on:** Nothing (first phase)
**Research:** Unlikely (standard patterns)

**Scope:**
- Python 3.13 project scaffold with FastAPI app
- asyncpg database pool module (`backend/01_core/database.py`)
- Config/env loading with module gating (`backend/01_core/config.py`)
- UUID v7 id module (`backend/01_core/id.py`)
- Response envelope helper (`backend/01_core/response.py`)
- Error handling (`backend/01_core/errors.py`)
- SQL migrator script (`scripts/migrator/`)
- `00_schema_migrations` tracking table
- Next.js app shell with Tailwind CSS
- Node registry skeleton (`backend/01_core/node_registry.py`)
- Robot Framework + Playwright Browser test harness (`tests/e2e/`)
- Docker Compose for local dev (Postgres, optional Valkey)

**Plans:**
- [x] 01-01: Docker Compose (tennetctl_v2) + enterprise SQL migrator
- [x] 01-02: Python backend scaffold (FastAPI app, core modules, node registry)
- [ ] 01-03: Next.js frontend shell + Playwright test harness

### Phase 2: Schema & Audit Foundation

**Goal:** All IAM + audit database tables migrated and audit service cross-cutting pattern established. Audit node (`emit_audit`) operational.
**Depends on:** Phase 1 (database + migrator must exist)
**Research:** Unlikely (table type system defined in CLAUDE.md)

**Scope:**
- `03_iam` schema: dim tables (account_types, scopes, roles, groups), fct tables (orgs, workspaces, users, applications), dtl tables (attr_defs, attrs), lnk tables (user-org, user-workspace, user-role, user-group), views
- `04_audit` schema: evt_audit table, audit service, emit_audit node
- EAV foundation: dim_attr_defs + dtl_attrs pattern
- All views for read paths (`v_orgs`, `v_workspaces`, `v_users`, etc.)

**Plans:**
- [ ] 02-01: IAM schema migrations (dim + fct + dtl + lnk tables)
- [ ] 02-02: Audit schema + audit service + emit_audit node
- [ ] 02-03: Views and EAV foundation

### Phase 3: Orgs & Workspaces (vertical)

**Goal:** Full vertical: create/list/update/delete orgs and workspaces with EAV attrs, audit trail, nodes, UI pages, Playwright live verification.
**Depends on:** Phase 2 (schema + audit must exist)
**Research:** Unlikely (CRUD + EAV pattern established)

**Scope:**
- Org repo → service → routes → nodes
- Workspace repo → service → routes → nodes (scoped under org)
- UI: org list, create org, org detail, workspace list, create workspace
- Audit on every mutating action
- Playwright live test: create org → create workspace → verify

**Plans:**
- [ ] 03-01: Org backend (repo, service, routes, nodes, audit)
- [ ] 03-02: Workspace backend (repo, service, routes, nodes, audit)
- [ ] 03-03: Org & Workspace UI + Playwright live verification

### Phase 4: Users & Account Types (vertical)

**Goal:** Full vertical: user CRUD, account type management (email/password, magic link, Gmail/OAuth), user-org-workspace membership, UI, Playwright verification.
**Depends on:** Phase 3 (orgs + workspaces must exist for membership)
**Research:** Unlikely (patterns from Phase 3)

**Scope:**
- User repo → service → routes → nodes
- Account type management (dim_account_types driving auth options)
- User-org and user-workspace membership via lnk tables
- UI: user list, create user, user detail, account type display, membership management
- Playwright live test: create user → assign to org/workspace → verify membership

**Plans:**
- [ ] 04-01: User backend (repo, service, routes, nodes, account types, audit)
- [ ] 04-02: User membership (lnk tables, org/workspace assignment)
- [ ] 04-03: User UI + Playwright live verification

### Phase 5: Roles, Groups, Scopes & Applications (vertical)

**Goal:** Full vertical: role/group CRUD, scope management (global/org), application/product CRUD, assignment link tables, UI, Playwright verification.
**Depends on:** Phase 4 (users must exist for role/group assignment)
**Research:** Unlikely (link table patterns established)

**Scope:**
- Role/group repo → service → routes → nodes
- Scope management (global + org level now, workspace future)
- Application/product CRUD
- Assignment: user-role, user-group via lnk tables
- UI: role management, group management, scope config, application list
- Playwright live test: create role → assign to user → verify scope resolution

**Plans:**
- [ ] 05-01: Roles, groups & scopes backend (repo, service, routes, nodes, audit)
- [ ] 05-02: Applications backend + scope assignment
- [ ] 05-03: Roles/Groups/Scopes/Applications UI + Playwright live verification

### Phase 6: Auth Config & Feature Flags (vertical)

**Goal:** Full vertical: auth config with global defaults + org-level overrides, feature flag management scoped to org/workspace, UI, Playwright verification.
**Depends on:** Phase 5 (roles/scopes needed for config context)
**Research:** Likely (auth config override resolution strategy)
**Research topics:** Override merge strategy (deep merge vs replace), config inheritance model, feature flag evaluation engine

**Scope:**
- Auth config: global defaults + org-level overrides (which account types enabled, session TTL, MFA policy)
- Feature flag management: create/toggle flags, scope to org/workspace
- Auth config nodes + feature flag nodes
- UI: auth config editor (global view + org override), feature flag dashboard
- Playwright live test: set global config → override at org level → toggle flag → verify resolution

**Plans:**
- [ ] 06-01: Auth config backend (repo, service, routes, nodes, override resolution)
- [ ] 06-02: Feature flags backend (repo, service, routes, nodes, scope evaluation)
- [ ] 06-03: Auth Config & Feature Flags UI + Playwright live verification

---
*Roadmap created: 2026-04-12*
*Last updated: 2026-04-13*
