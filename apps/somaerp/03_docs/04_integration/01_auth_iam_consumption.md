# Auth / IAM Consumption

> How somaerp delegates every identity, session, and RBAC question to tennetctl 03_iam. Per ADR-008, somaerp NEVER reimplements any of this.

## Two distinct identity worlds — keep them separate

somaerp talks about two completely different kinds of "person":

| Identity world | Lives in | Purpose | Auth path |
| --- | --- | --- | --- |
| **Operators / staff / admins** (the people who run a tenant's ERP) | tennetctl `03_iam.fct_users` | Logging into the somaerp UI, recording who did each action | tennetctl session bearer token |
| **Customers** (the juice-buyers Soma Delights serves) | somaerp `fct_customers` (08_customers data layer) | Subscriptions, deliveries, preferences | NOT iam users; not authenticated by tennetctl |

This separation is critical. A customer in Soma Delights' subscriber base is not a tennetctl user. They never log in to anything. They are a record in the tenant's CRM-style customer table. The opposite is also true: a tennetctl user is an actor in the system (Sri the founder, a kitchen helper, a delivery rider), never a payable account.

If a customer ever does need to log in (a future self-serve subscriber portal), that becomes a separate iam user with a `lnk_iam_user_to_somaerp_customer` linkage row. Out of v0.9.0 scope.

## End-user identity resolution (operators)

Per `00_tennetctl_proxy_pattern.md`, the somaerp middleware resolves every request's actor via tennetctl `whoami`:

```text
incoming HTTP to apps/somaerp
  ├── middleware reads Authorization: Bearer <session_token>
  ├── middleware calls client.whoami(session_token)
  │      → tennetctl GET /v1/auth/me
  │      → returns {user, session, org, workspace}
  ├── middleware attaches user_id, session_id, org_id, workspace_id
  │     to request.state for the downstream service layer
  └── route handler runs
```

The session bearer token forwarded to `whoami` is the only place the session token is used. All subsequent service-to-service calls (audit, notify, vault) use the somaerp service API key plus explicit user/workspace context per call.

## Workspace context = somaerp tenant scope

`request.state.workspace_id` IS the somaerp `tenant_id`. The repo layer always injects:

```text
WHERE tenant_id = $request.state.workspace_id
```

A user who is a member of multiple workspaces switches workspaces via tennetctl iam (`POST /v1/sessions/{id}/switch-workspace`). After a switch, every subsequent somaerp request scopes to the new workspace's data automatically — no somaerp logic needed.

## RBAC scopes — somaerp registers, tennetctl enforces

Per ADR-008 and `02_tenant_model.md`, somaerp registers its application + role keys in tennetctl at boot:

```text
client.resolve_application(code="somaerp", org_id=PLATFORM_ORG_ID)
  → tennetctl GET /v1/applications?code=somaerp&org_id=...
  → returns the somaerp application_id
```

The role keys somaerp declares (and which the tenant's admin grants per workspace member):

| Role key | Grants | Used by |
| --- | --- | --- |
| `somaerp.geography.read` | view kitchens, locations, capacity | All operators |
| `somaerp.geography.write` | create/edit kitchens, capacity | Admin, ops_lead |
| `somaerp.catalog.read` / `.write` | products, product lines | Admin |
| `somaerp.recipes.read` / `.write` | recipes, kitchen overrides | Admin, head_juicer |
| `somaerp.production.read` / `.write` | batches, batch logs | All production staff |
| `somaerp.qc.read` / `.write` / `.sign_off` | QC checks; sign_off needed for FSSAI sign-off | QC lead, ops_lead |
| `somaerp.raw_materials.read` / `.write` | raw material catalog | Admin, procurement_lead |
| `somaerp.suppliers.read` / `.write` | supplier directory | Admin, procurement_lead |
| `somaerp.procurement.read` / `.write` | procurement runs, inventory movements | Procurement_lead |
| `somaerp.customers.read` / `.write` | customer profiles, subscriptions | Customer_success, admin |
| `somaerp.delivery.read` / `.write` / `.dispatch` | routes, runs, stops; dispatch starts a run | Delivery_lead, riders (read+dispatch only) |
| `somaerp.admin` | super-role; grants every other key | Tenant owner |

Each scope is checked at the route layer:

```text
@require_scope("somaerp.production.write")
async def create_batch(...): ...
```

`require_scope` calls `client.list_my_roles()` (cached per-request) and looks for the key. List of roles ships from tennetctl, scoped to `(application_id=somaerp, workspace_id=request.state.workspace_id)`.

## Service API key for system-to-system calls

Workers, scheduled tasks, and inter-service calls use the somaerp service API key (per `00_tennetctl_proxy_pattern.md` deployment config — `SOMAERP_TENNETCTL_KEY_FILE`). When a worker performs a mutation on behalf of a system trigger (e.g. nightly subscription billing), the audit emission carries:

```text
emit_audit(
    event_key="somaerp.customers.subscriptions.billed",
    actor_user_id=None,             # no user; system action
    org_id=PLATFORM_ORG_ID,
    workspace_id=tenant_workspace_id,
    metadata={"category": "system", ...}
)
```

The `category=system` is the documented bypass for "no user_id" on a non-setup, non-failure path. Per `02_audit_emission.md`.

## What somaerp never does

- Never stores user passwords. Never has a users table. Never has a sessions table.
- Never issues JWTs. Never validates JWTs. tennetctl handles all token issuance and validation.
- Never invents its own RBAC engine. The check is always "does this iam role exist for this user in this workspace for this somaerp application?"
- Never queries iam tables directly. Always via the proxy client.
- Never caches user role data across requests. Each request re-resolves via `whoami` + `list_my_roles`. (A v1.0 caching layer is documented in `00_tennetctl_proxy_pattern.md` deferral.)

## Customer entities are NOT iam users

Restating the opening point because it is the most-confused decision: `fct_customers` (the people who pay for juice subscriptions) live in the somaerp data layer, not in tennetctl iam. They have no login, no session, no RBAC.

When the data_model `08_customers` doc (Task 2) defines the customer table, it carries:

- `id` UUID v7 (somaerp-owned, not an iam user_id)
- `tenant_id` UUID NOT NULL (tennetctl workspace_id)
- `properties` JSONB (extension)
- name, address, contact info, preferences, allergies — all somaerp-owned

A customer being "deleted" in somaerp is a soft-delete on the `fct_customers` row. It has no effect on tennetctl iam. A user being deleted in tennetctl iam has no effect on `fct_customers` rows that user may have created — the `created_by_user_id` reference becomes a tombstone but the customer record persists.

When (someday) a self-serve customer portal exists, the link is via `lnk_iam_user_to_somaerp_customer (iam_user_id, customer_id)` — explicit, optional, not on the critical path for v0.9.0.

## Bootstrap order

Per ADR-001, the tennetctl workspace must exist before any somaerp tenant data can be created:

1. Operator provisions a tennetctl workspace via `POST /v1/workspaces`.
2. Operator runs the somaerp tenant bootstrap (plan 56-02 onwards) which seeds `fct_locations`, `fct_kitchens`, `fct_products`, etc. for that workspace.
3. Operator grants the appropriate iam roles to the tenant's first user(s).
4. The tenant is live.

Bootstrap mutations emit audit events with `category=setup` to bypass the user_id requirement (per `02_audit_emission.md`).

## Related documents

- `00_tennetctl_proxy_pattern.md` — the proxy client mechanics
- `02_audit_emission.md` — how the iam-resolved scope flows into audit events
- `../00_main/02_tenant_model.md` — the tenant_id = workspace_id decision
- `../00_main/08_decisions/001_tenant_boundary_org_vs_workspace.md`
- `../00_main/08_decisions/008_tennetctl_primitive_consumption.md`
- `apps/solsocial/backend/01_core/tennetctl_client.py` — reference proxy implementation
