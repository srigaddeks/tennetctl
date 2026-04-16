# ADR-025: Multi-Tenant by Default, Single-Tenant via TENNETCTL_SINGLE_TENANT

**Status:** Accepted
**Date:** 2026-04-13

---

## Context

TennetCTL is designed to be self-hosted by many different teams at different scales:

- A solo developer on a $20 VPS who just wants an all-in-one control plane for their own product
- A 10-person startup with one internal team
- A 500-person enterprise with dozens of teams, orgs, and workspaces

The multi-tenancy model affects every layer: the data schema (`org_id` scoping), the IAM system (org creation, user invitation), the onboarding UX (org selection vs direct landing), and deployment configuration.

The question: should tennetctl be multi-tenant first with single-tenant as a simplification, or single-tenant first with multi-tenant as an upgrade?

---

## Decision

**TennetCTL is multi-tenant by default. Single-tenant mode is enabled via `TENNETCTL_SINGLE_TENANT=true`.**

In single-tenant mode, the container creates a default org at first boot and all users are automatically placed in it. There is no org selection UX, no invitation flow, and no org management interface — the operator manages everything through the super admin panel.

---

## Multi-Tenant Mode (default)

The default deployment:

- Org creation requires super admin action or an invitation flow
- Users belong to one or more orgs; each org has its own workspace(s)
- Every data record is scoped to an `org_id` (enforced at the application layer and optionally at the RLS layer in Postgres)
- The IAM module manages org lifecycle: create, invite, configure, delete

Target users: SaaS products built on tennetctl that serve multiple customers as separate orgs, or enterprise deployments with multiple internal teams.

---

## Single-Tenant Mode (`TENNETCTL_SINGLE_TENANT=true`)

When this env var is set at container start:

1. The bootstrap process checks if a default org exists in the database
2. If not, it creates one (`slug: "default"`, `name: "Default Organisation"`)
3. All user registrations are automatically assigned to this org
4. The org selection and creation UX is hidden in the frontend
5. The org management section of IAM is hidden (users can't create or manage orgs)

The data model is identical to multi-tenant mode — `org_id` is still present on every record. The difference is purely in bootstrap behavior and UX.

**Why keep the same data model:**
Switching from single-tenant to multi-tenant mode later (when a team grows) is a configuration change, not a migration. No data needs restructuring; just add orgs and assign existing users.

---

## Hierarchy

```
Platform (Super Admin)
  └── Org (Tenant)
        └── Workspace (Scope boundary within org)
              └── Members, roles, flags, resources
```

- **Platform:** Super admin managed. Inherited platform-wide settings.
- **Org:** The primary tenant boundary. Data is isolated per org at the application layer.
- **Workspace:** A grouping within an org for policy config, feature flags, and resource scoping.

---

## Environment Variable

```bash
# Multi-tenant (default — no variable needed)
# TENNETCTL_SINGLE_TENANT=false

# Single-tenant — creates default org on first boot
TENNETCTL_SINGLE_TENANT=true
```

The variable is read once at startup by the bootstrap process. Changing it after first boot has no effect — the org structure is already established. To switch from single to multi-tenant, an operator creates additional orgs via the super admin panel.

---

## Consequences

- Every data table that is org-scoped carries `org_id VARCHAR(36)` with no FK constraint (cross-schema isolation, same as `created_by`).
- The IAM module must handle both modes: org creation is a super admin action in multi-tenant mode; it is invisible in single-tenant mode.
- The frontend reads `/api/v1/system/config` on load to determine tenant mode and adjusts navigation accordingly.
- Single-tenant deployments get the same security model as multi-tenant — RLS, audit, and IAM are all active. Single-tenant is not a security relaxation; it is a UX simplification.
- Backup and restore work identically in both modes — the data model is the same.
