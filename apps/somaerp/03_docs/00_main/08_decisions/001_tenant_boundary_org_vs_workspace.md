# ADR-001: Tenant boundary — workspace, not a new tenants table
Status: ACCEPTED
Date: 2026-04-24

## Context

somaerp is a multi-tenant ERP from day 1. Every row in every domain table must be scoped to a tenant. tennetctl already provides a two-level identity hierarchy (org → workspace) via `03_iam`, with RBAC, sessions, and audit scope already wired. The decision is whether somaerp introduces a parallel `somaerp.tenants` table (its own identity layer) or reuses an existing tennetctl identity (org or workspace) as the tenant boundary. Getting this wrong locks in a duplicate identity layer that fights the audit-scope rule and the multi-tenant sharding strategy.

## Decision

**The somaerp tenant_id is the tennetctl workspace_id.** No `somaerp.tenants` table is created. Every `fct_*` and `evt_*` row in somaerp carries `tenant_id UUID NOT NULL` whose value is `tennetctl.03_iam.workspaces.id`. The tennetctl org represents the platform owner; the workspace represents a customer of the platform; somaerp scopes all data at workspace level. RBAC, audit scope, vault scope, and notify templates are scoped at workspace level via existing tennetctl primitives. Soma Delights = workspace #1.

## Consequences

- **Easier:** zero new identity code in somaerp. RBAC, sessions, audit scope, vault, notify all work out-of-the-box because they already understand workspace_id. Future apps (somacrm) repeat the pattern with zero additional plumbing.
- **Easier:** future shard-by-tenant strategy has a natural shard key (tenant_id = workspace_id), already on every row.
- **Harder:** somaerp depends on a tennetctl primitive existing before any somaerp data can be created. Bootstrap order is fixed: tennetctl workspace first, then somaerp tenant config seed.
- **Harder:** cross-tenant data sharing (e.g. a shared raw materials catalog across workspaces) requires explicit duplication or a future "shared library" feature. Out of scope for v0.9.0.
- **Constrains:** ADR-008 (somaerp never reimplements IAM); cross-tenant FKs are forbidden; audit emission must always carry workspace_id.

## Alternatives Considered

- **New `somaerp.tenants` table.** Gives somaerp a parallel identity registry it controls. Rejected: duplicates tennetctl, breaks the audit-scope rule (which already expects workspace_id), and creates two sources of truth for "who is this tenant."
- **Use tennetctl org as the tenant.** Treats every customer as a top-level platform owner. Rejected: in the multi-tenant deployment shape, all customer workspaces share one platform org; using org as the tenant boundary collapses all customers into one.
- **Tenant-per-database (separate Postgres per customer).** Strongest isolation but operational nightmare at v0.9.0. Rejected for now; documented as a v1.0 enterprise option in the scaling doc.

## References

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md` (Open Question #2)
- `apps/somaerp/03_docs/00_main/02_tenant_model.md`
- Memory: `feedback_shared_org_workspace.md`, `project_kbio_kprotect.md`
- `.claude/rules/common/database.md`
