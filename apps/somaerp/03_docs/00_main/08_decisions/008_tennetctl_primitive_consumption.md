# ADR-008: somaerp consumes tennetctl primitives via proxy; never reimplements
Status: ACCEPTED
Date: 2026-04-24

## Context

tennetctl already ships authentication, IAM (orgs/workspaces/users/roles/sessions), audit emission with mandatory four-tuple scope, vault for secrets (and blobs in extension), notify for templated notifications, flows/canvas for multi-step workflows, and a billing stub. solsocial proves the thin-app-on-tennetctl pattern works in production via `apps/solsocial/backend/01_core/tennetctl_client.py`. The empire thesis (no external SaaS dependencies, ever) demands that somaerp NOT pull in any third-party identity provider, payment processor, transactional-email service, or SMS gateway. The risk is that somaerp engineers, under deadline pressure, reach for a "lightweight inline implementation" of one of these primitives and create drift between somaerp's identity model and tennetctl's.

## Decision

**somaerp NEVER reimplements authentication, IAM, audit, vault, notify, or workflow execution. Every cross-cutting concern is consumed via `apps/somaerp/backend/01_core/tennetctl_client.py`, modeled directly on the solsocial precedent. The somaerp backend has zero user/session/role/audit/vault/notify tables. End-user identity is resolved by forwarding the user's session bearer token to tennetctl `/v1/auth/me`. System-to-system calls (audit emission, notify send, vault read/write, flag evaluation) use a service API key minted in tennetctl and stored in `SOMAERP_TENNETCTL_KEY_FILE`. Every audit emission carries the four-tuple (user_id, session_id, org_id, workspace_id) per the project-wide rule. somaerp registers itself as a tennetctl application (`code = somaerp`) at boot via `resolve_application(code, org_id)` and stamps every outbound call with `application_id`.** The specific tennetctl endpoints consumed by somaerp v0.9.0:

- `GET  /v1/auth/me` — resolve session token to user + workspace context
- `GET  /v1/applications?code=somaerp&org_id=...` — boot-time application lookup
- `GET  /v1/roles?application_id=...&workspace_id=...` — RBAC scope lookup
- `GET  /v1/flags?application_id=...` — feature flag listing
- `POST /v1/evaluate` — feature flag evaluation per request
- `POST /v1/audit-events` — audit emission for every mutation
- `POST /v1/notify/send` — customer/operator notifications
- `GET  /v1/vault`, `POST /v1/vault`, `POST /v1/vault/{key}/reveal`, `POST /v1/vault/{key}/rotate`, `DELETE /v1/vault/{key}` — secrets and blobs

## Consequences

- **Easier:** zero new identity / audit / notify / vault code in somaerp; bug fixes in tennetctl primitives propagate automatically; security review surface stays inside tennetctl.
- **Easier:** future apps (somacrm, others) repeat the proxy pattern with zero new tennetctl work.
- **Easier:** the empire thesis is enforceable at code-review time (any external SaaS SDK in `apps/somaerp/backend/requirements.txt` is a flagged violation).
- **Harder:** somaerp depends on tennetctl being reachable. A tennetctl outage degrades somaerp; mitigated by deploying both as the same Docker image and process group on a self-host.
- **Harder:** every cross-primitive call is an HTTP hop, not an in-process function call. For Soma Delights volume this is irrelevant; for high-volume audit emission it may need batching (deferred to v1.0).
- **Constrains:** ADR-001 (tenant_id = workspace_id, because IAM is delegated); ADR-002 (no per-tenant configurable identity, because IAM is fixed); the integration docs (`04_integration/00_..05_*.md`); the proxy client implementation in plan 56-02.

## Alternatives Considered

- **Embed a thin auth/IAM module inside somaerp.** Avoids the HTTP hop. Rejected: violates the empire thesis premise that all primitives live in tennetctl, creates two sources of truth for user/session, breaks audit-scope consistency.
- **Use any external SaaS for auth, payments, email, or SMS.** Faster initial ship. Rejected outright: explicit user constraint (no external SaaS, ever) and the entire reason tennetctl exists.
- **Hybrid: cache user/role data inside somaerp with tennetctl as upstream.** Faster reads. Rejected as v0.9.0 scope; revisit only if measured latency from the HTTP hop is a real problem.

## References

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`
- `apps/solsocial/README.md`
- `apps/solsocial/backend/01_core/tennetctl_client.py`
- `apps/somaerp/03_docs/04_integration/00_tennetctl_proxy_pattern.md`
- `apps/somaerp/03_docs/00_main/02_tenant_model.md`
- Memory: `project_saas_empire_thesis.md`, `feedback_audit_scope_mandatory.md`
