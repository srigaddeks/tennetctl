# Roadmap: TennetCTL

## Overview

TennetCTL is built milestone-by-milestone from core infrastructure through enterprise IAM. Every phase after foundation is a full vertical slice: schema → repo → service → routes → nodes → UI → Playwright live verification. Nothing ships without being tested in a real browser.

**Architectural spine:** Node Catalog Protocol v1 (see `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`). Every feature vertical (Phase 3+) uses it.

## Current Milestone

**v0.1 Foundation + IAM** (v0.1.0)
Status: In progress
Phases: 2 of 7 complete (Phase 3 starting — IAM & Audit schema)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with [INSERTED])

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Infrastructure | 3 | ✅ Complete | 2026-04-13 |
| 2 | Catalog Foundation | 3 | ✅ Complete | 2026-04-16 |
| 3 | IAM & Audit Schema | 4 | Not started | - |
| 4 | Orgs & Workspaces (vertical) | TBD | Not started | - |
| 5 | Users & Account Types (vertical) | TBD | Not started | - |
| 6 | Roles, Groups, Scopes & Applications (vertical) | TBD | Not started | - |
| 7 | Auth Config & Feature Flags (vertical) | TBD | Not started | - |

## Phase Details

### Phase 1: Core Infrastructure

**Goal:** Running backend + frontend shells with database, migrations, node registry skeleton, and Playwright test harness — everything needed before any feature vertical.
**Depends on:** Nothing (first phase)

**Plans:**
- [x] 01-01: Docker Compose (tennetctl_v2) + enterprise SQL migrator
- [x] 01-02: Python backend scaffold (FastAPI app, core modules, node registry)
- [x] 01-03: Next.js frontend shell + Playwright test harness

### Phase 2: Catalog Foundation

**Goal:** The Node Catalog Protocol (NCP v1) is implemented end-to-end: manifest loader, catalog DB, node runner with execution primitives. From here, every cross-sub-feature call goes through `run_node`; direct imports across sub-features are lint-blocked.
**Depends on:** Phase 1 (database + migrator + backend scaffold)
**Research:** None (protocol is specified in `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`)

**Scope:**
- `01_catalog` schema: dim_modules, dim_node_kinds, dim_tx_modes, dim_entity_types, fct_features, fct_sub_features, fct_nodes, dtl_attr_defs, dtl_attrs
- NCP v1 protocol doc published
- ADR-027 Catalog + Runner decision recorded
- `backend/01_catalog/` Python module: manifest loader, boot upsert, validator (incl. cross-import linter), `Node` base class, `NodeContext`, `run_node` runner
- Execution policy enforcement: timeout, retry on `TransientError`, tx modes (caller/own/none), authorization hook
- `/tnt` Claude skill (single skill) explaining the pattern

**Plans:**
- [x] 02-01: NCP v1 protocol doc + ADR-027 + catalog DB schema
- [x] 02-02: Manifest loader + boot upsert + validator + `/tnt` skill
- [x] 02-03: Node runner (execution policy, NodeContext, authorization hook)

### Phase 3: IAM & Audit Schema

**Goal:** All IAM + audit database tables migrated, IAM registered in the catalog via its `feature.manifest.yaml`, audit service cross-cutting pattern established, `emit_audit` node operational and callable from any sub-feature via `run_node`.
**Depends on:** Phase 2 (catalog must exist so IAM can register against it)

**Scope:**
- `03_iam` schema: dim tables (account_types, scopes, roles, groups), fct tables (orgs, workspaces, users, applications), dtl tables (attr_defs, attrs), lnk tables (user-org, user-workspace, user-role, user-group), views
- `04_audit` schema: evt_audit table, audit service, `emit_audit` node (first real cross-cutting node)
- `backend/02_features/03_iam/feature.manifest.yaml` — first real consumer of NCP v1
- EAV foundation: dim_attr_defs + dtl_attrs pattern
- All views for read paths (`v_orgs`, `v_workspaces`, `v_users`, etc.)

**Plans:**
- [ ] 03-01: IAM schema migrations (relocated from old 02-01; depends on Phase 2)
- [ ] 03-02: IAM feature.manifest.yaml + catalog registration verification
- [ ] 03-03: Audit schema + audit service + `emit_audit` node
- [ ] 03-04: Views and EAV refinement

### Phase 4: Orgs & Workspaces (vertical)

**Goal:** Full vertical: create/list/update/delete orgs and workspaces with EAV attrs, audit trail, nodes, UI pages, Playwright live verification. Every cross-sub-feature call goes through `run_node`.
**Depends on:** Phase 3 (schema + audit + catalog wiring must exist)

**Scope:**
- Org repo → service → routes → nodes (registered in manifest)
- Workspace repo → service → routes → nodes (scoped under org)
- UI: org list, create org, org detail, workspace list, create workspace
- Audit on every mutating action via `run_node("audit.emit", ...)`
- Playwright live test: create org → create workspace → verify

**Plans:**
- [ ] 04-01: Org sub-feature (schemas/repo/service/routes + nodes + manifest entry)
- [ ] 04-02: Workspace sub-feature (schemas/repo/service/routes + nodes + manifest entry)
- [ ] 04-03: Org & Workspace UI + Playwright live verification

### Phase 5: Users & Account Types (vertical)

**Goal:** Full vertical: user CRUD, account type management (email/password, magic link, Gmail/OAuth), user-org-workspace membership, UI, Playwright verification.
**Depends on:** Phase 4 (orgs + workspaces must exist for membership)

**Scope:**
- User sub-feature (repo/service/routes/nodes + manifest)
- Account type management (dim_account_types driving auth options)
- User-org and user-workspace membership via lnk tables, invoked via `run_node`
- UI: user list, create user, user detail, account type display, membership management
- Playwright live test: create user → assign to org/workspace → verify membership

**Plans:**
- [ ] 05-01: User sub-feature (repo, service, routes, nodes, account types, audit)
- [ ] 05-02: User membership (lnk tables, org/workspace assignment)
- [ ] 05-03: User UI + Playwright live verification

### Phase 6: Roles, Groups, Scopes & Applications (vertical)

**Goal:** Full vertical: role/group CRUD, scope management (global/org), application/product CRUD, assignment link tables, UI, Playwright verification.
**Depends on:** Phase 5 (users must exist for role/group assignment)

**Scope:**
- Role/group sub-features
- Scope management (global + org level now, workspace future)
- Application/product CRUD
- Assignment: user-role, user-group via lnk tables
- UI: role management, group management, scope config, application list
- Playwright live test: create role → assign to user → verify scope resolution

**Plans:**
- [ ] 06-01: Roles, groups & scopes sub-features (repo, service, routes, nodes, audit)
- [ ] 06-02: Applications sub-feature + scope assignment
- [ ] 06-03: Roles/Groups/Scopes/Applications UI + Playwright live verification

### Phase 7: Auth Config & Feature Flags (vertical)

**Goal:** Full vertical: auth config with global defaults + org-level overrides, feature flag management scoped to org/workspace, UI, Playwright verification.
**Depends on:** Phase 6 (roles/scopes needed for config context)
**Research:** Likely (auth config override resolution strategy)
**Research topics:** Override merge strategy (deep merge vs replace), config inheritance model, feature flag evaluation engine

**Scope:**
- Auth config: global defaults + org-level overrides (which account types enabled, session TTL, MFA policy)
- Feature flag management: create/toggle flags, scope to org/workspace
- Auth config nodes + feature flag nodes
- UI: auth config editor (global view + org override), feature flag dashboard
- Playwright live test: set global config → override at org level → toggle flag → verify resolution

**Plans:**
- [ ] 07-01: Auth config sub-feature (repo, service, routes, nodes, override resolution)
- [ ] 07-02: Feature flags sub-feature (repo, service, routes, nodes, scope evaluation)
- [ ] 07-03: Auth Config & Feature Flags UI + Playwright live verification

---

## Future Milestones (post-v0.1)

### v0.1.5 Runtime Hardening (before v0.2)
Gaps surfaced during gap analysis (2026-04-16). Close before wider adoption:
- Versioning operationalized (v1 → v2 migration pattern working in practice)
- Async effect dispatch via NATS JetStream wired to effect nodes
- Gateway sync: request-kind nodes propagated to APISIX config
- Dev hot-reload of catalog on manifest change (not just restart)
- Bulk operation patterns documented (`get_many` alongside every `get`)

### v0.2 Platform Access Layer
- **MCP Integration** — `inspect / search / scaffold / validate / run` generic tools (ADR-024) over the catalog
- Scaffolder CLI — template-driven feature/sub-feature/node creation
- Agent indices — `_index.yaml` generated alongside manifests if the simple pattern proves insufficient
- Flow composition tables (`fct_flows`, `fct_flow_nodes`, `lnk_flow_edges`) activated — required before visual canvas

### v0.3 Canvas + Monitoring
- React Flow read-only canvas reads catalog + flows, renders DAG
- Monitoring feature vertical (traces, metrics, logs via NATS)

### v1.0 Enterprise
- Feature flag evaluation at gateway
- Multi-region catalog replication
- Visual flow editor (writeable canvas)

---
*Roadmap created: 2026-04-12*
*Last updated: 2026-04-16 — Phase 2 (Catalog Foundation) complete; NCP v1 operational; Phase 3 (IAM & Audit) starting*
