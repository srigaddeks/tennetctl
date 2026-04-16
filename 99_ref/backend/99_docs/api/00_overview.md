# kcontrol API Overview

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via `POST /api/v1/auth/local/login`. Access tokens are short-lived JWTs with a `kid` header. Refresh tokens support rotation with reuse detection.

## Permission Model

Permissions follow this chain:

```
user → group_membership → user_group → group_role_assignment → role → role_feature_permission → feature_permission
```

Feature permissions are coded as `{feature_flag_code}.{action_code}` (e.g., `org_management.create`).

Available actions: `view`, `create`, `update`, `delete`, `assign`, `revoke`, `enable`, `disable`

Scope inheritance (additive):
- **Platform** — groups with no `scope_org_id` or `scope_workspace_id`
- **Org** — platform groups + groups scoped to that org
- **Workspace** — platform + org + workspace groups

## Common Error Responses

All errors follow this structure:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable message"
  },
  "request_id": "uuid"
}
```

| Status | Code                    | Description                |
|--------|-------------------------|----------------------------|
| 401    | `authentication_failed` | Missing or invalid token   |
| 403    | `authorization_failed`  | Insufficient permissions   |
| 404    | `not_found`             | Resource not found         |
| 409    | `conflict`              | Duplicate resource         |
| 422    | (Pydantic validation)   | Request validation failed  |
| 500    | `internal_error`        | Server error               |

## API Modules

| # | Module | Base Path | Doc |
|---|--------|-----------|-----|
| 1 | Auth (local password) | `/api/v1/auth/local` | [01_auth.md](01_auth.md) |
| 2 | Feature Flags | `/api/v1/am/features` | [02_feature_flags.md](02_feature_flags.md) |
| 3 | Roles | `/api/v1/am/roles` | [03_roles.md](03_roles.md) |
| 4 | User Groups | `/api/v1/am/groups` | [04_user_groups.md](04_user_groups.md) |
| 5 | Access Context | `/api/v1/am/access` | [05_access_context.md](05_access_context.md) |
| 6 | Organizations | `/api/v1/am/orgs` | [06_orgs.md](06_orgs.md) |
| 7 | Workspaces | `/api/v1/am/orgs/{org_id}/workspaces` | [07_workspaces.md](07_workspaces.md) |
| 8 | Invitations | `/api/v1/am/invitations` | [08_invitations.md](08_invitations.md) |
| 9 | Impersonation | `/api/v1/am/impersonation` | [09_impersonation.md](09_impersonation.md) |
| 10 | Admin | `/api/v1/am/admin` | [10_admin.md](10_admin.md) |
| 11 | Auth Enhancements | `/api/v1/auth/local` | [11_enhancements.md](11_enhancements.md) |
| 12 | Entity Settings | `/api/v1/am/settings/{type}/{id}` | [12_entity_settings.md](12_entity_settings.md) |
| 13 | API Keys | `/api/v1/am/api-keys` | [13_api_keys.md](13_api_keys.md) |
| 14 | Notifications | `/api/v1/notifications` | [14_notifications.md](14_notifications.md) |
| 15 | License Profiles | `/api/v1/am/license-profiles` | [15_license_profiles.md](15_license_profiles.md) |
| 16 | Tasks | `/api/v1/tk` | [16_tasks.md](16_tasks.md) |
| 17 | GRC Library (frameworks, controls, tests, versions, deployments) | `/api/v1/fr` | [17_grc_library.md](17_grc_library.md) |
| 18 | Risk Registry | `/api/v1/rr` | [18_risk_registry.md](18_risk_registry.md) |
| 19 | Comments | `/api/v1/comments` | [19_comments.md](19_comments.md) |
| 20 | Attachments | `/api/v1/attachments` | [20_attachments.md](20_attachments.md) |
| 21 | Sandbox: Dimensions, Connectors (org-scoped) | `/api/v1/sandbox/connectors` | [21_sandbox_connectors.md](21_sandbox_connectors.md) |
| 22 | Sandbox: Datasets (manual, template, composite, live) | `/api/v1/sandbox/datasets` | [22_sandbox_datasets.md](22_sandbox_datasets.md) |
| 23 | Sandbox: Signals (Python `evaluate()` functions, versioned) | `/api/v1/sandbox/signals` | [23_sandbox_signals.md](23_sandbox_signals.md) |
| 24 | Sandbox: Threat Types (AND/OR/NOT expression trees) | `/api/v1/sandbox/threat-types` | [24_sandbox_threat_types.md](24_sandbox_threat_types.md) |
| 25 | Sandbox: Policies (actions JSONB, cooldowns, dry-run) | `/api/v1/sandbox/policies` | [25_sandbox_policies.md](25_sandbox_policies.md) |
| 26 | Sandbox: Execution Engine (RestrictedPython + subprocess, dual-write) | `/api/v1/sandbox/execution` | [26_sandbox_execution.md](26_sandbox_execution.md) |
| 27 | Sandbox: Live Sessions (ClickHouse, cursor-based streaming) | `/api/v1/sandbox/live-sessions` | [27_sandbox_live_sessions.md](27_sandbox_live_sessions.md) |
| 28 | Sandbox: Control Libraries + Promotions | `/api/v1/sandbox/libraries` | [28_sandbox_libraries.md](28_sandbox_libraries.md) |
| 29 | Sandbox: SSF/CAEP/RISC Transmitter | `/api/v1/sandbox/ssf` | [29_sandbox_ssf_transmitter.md](29_sandbox_ssf_transmitter.md) |
| 30 | Sandbox: LangGraph AI Signal Generation Agent | `/api/v1/sandbox/ai-agent` | [30_sandbox_ai_agent.md](30_sandbox_ai_agent.md) |

## Endpoint Summary

### Auth (16 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 1 | POST | `/auth/local/register` | No | — |
| 2 | POST | `/auth/local/login` | No | — |
| 3 | POST | `/auth/local/refresh` | No | — |
| 4 | POST | `/auth/local/forgot-password` | No | — |
| 5 | POST | `/auth/local/reset-password` | No | — |
| 6 | POST | `/auth/local/logout` | Yes | — |
| 7 | GET | `/auth/local/me` | Yes | — |
| 8 | GET | `/auth/local/me/properties` | Yes | — |
| 9 | PUT | `/auth/local/me/properties` (batch) | Yes | — |
| 10 | GET | `/auth/local/me/property-keys` | No | — |
| 11 | PUT | `/auth/local/me/properties/{key}` | Yes | — |
| 12 | DELETE | `/auth/local/me/properties/{key}` | Yes | — |
| 13 | PUT | `/auth/local/me/password` | Yes | — |
| 14 | POST | `/auth/local/me/verify-email/request` | Yes | — |
| 15 | POST | `/auth/local/me/verify-email` | No | — |
| 16 | GET | `/auth/local/me/accounts` | Yes | — |

### Feature Flags (4 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 17 | GET | `/am/features` | Yes | `feature_flag_registry.view` |
| 17b | GET | `/am/features/org-available` | Yes | — (any authenticated user) |
| 18 | POST | `/am/features` | Yes | `feature_flag_registry.create` |
| 19 | PATCH | `/am/features/{code}` | Yes | `feature_flag_registry.update` |

### Roles (5 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 20 | GET | `/am/roles` | Yes | `access_governance_console.view` |
| 21 | POST | `/am/roles` | Yes | `group_access_assignment.assign` |
| 22 | PATCH | `/am/roles/{role_id}` | Yes | `group_access_assignment.assign` |
| 23 | POST | `/am/roles/{role_id}/permissions` | Yes | `access_governance_console.assign` |
| 24 | DELETE | `/am/roles/{role_id}/permissions/{id}` | Yes | `access_governance_console.assign` |

### User Groups (7 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 25 | GET | `/am/groups` | Yes | `group_access_assignment.view` |
| 26 | POST | `/am/groups` | Yes | `group_access_assignment.assign` |
| 27 | PATCH | `/am/groups/{group_id}` | Yes | `group_access_assignment.assign` |
| 28 | POST | `/am/groups/{group_id}/members` | Yes | `group_access_assignment.assign` |
| 29 | DELETE | `/am/groups/{group_id}/members/{user_id}` | Yes | `group_access_assignment.revoke` |
| 30 | POST | `/am/groups/{group_id}/roles` | Yes | `group_access_assignment.assign` |
| 31 | DELETE | `/am/groups/{group_id}/roles/{role_id}` | Yes | `group_access_assignment.revoke` |

### Access Context (1 endpoint)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 32 | GET | `/am/access` | Yes | — |

### Organizations (8 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 33 | GET | `/am/org-types` | No | — |
| 34 | GET | `/am/orgs` | Yes | `org_management.view` |
| 35 | POST | `/am/orgs` | Yes | `org_management.create` |
| 36 | PATCH | `/am/orgs/{org_id}` | Yes | `org_management.update` |
| 37 | GET | `/am/orgs/{org_id}/members` | Yes | `org_management.view` |
| 38 | POST | `/am/orgs/{org_id}/members` | Yes | `org_management.assign` |
| 38b | PATCH | `/am/orgs/{org_id}/members/{user_id}` | Yes | `org_management.assign` |
| 39 | DELETE | `/am/orgs/{org_id}/members/{user_id}` | Yes | `org_management.revoke` |

### Workspaces (8 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 40 | GET | `/am/workspace-types` | No | — |
| 41 | GET | `/am/orgs/{org_id}/workspaces` | Yes | `workspace_management.view` |
| 42 | POST | `/am/orgs/{org_id}/workspaces` | Yes | `workspace_management.create` |
| 43 | PATCH | `/am/orgs/{org_id}/workspaces/{ws_id}` | Yes | `workspace_management.update` |
| 44 | GET | `/am/orgs/{org_id}/workspaces/{ws_id}/members` | Yes | `workspace_management.view` |
| 45 | POST | `/am/orgs/{org_id}/workspaces/{ws_id}/members` | Yes | `workspace_management.assign` |
| 45b | PATCH | `/am/orgs/{org_id}/workspaces/{ws_id}/members/{uid}` | Yes | `workspace_management.assign` |
| 46 | DELETE | `/am/orgs/{org_id}/workspaces/{ws_id}/members/{uid}` | Yes | `workspace_management.revoke` |

### Invitations (6 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 47 | POST | `/am/invitations` | Yes | `org_management.assign` |
| 48 | GET | `/am/invitations` | Yes | `org_management.view` |
| 49 | GET | `/am/invitations/stats` | Yes | `org_management.view` |
| 50 | GET | `/am/invitations/{invitation_id}` | Yes | `org_management.view` |
| 51 | PATCH | `/am/invitations/{invitation_id}/revoke` | Yes | `org_management.revoke` |
| 52 | POST | `/am/invitations/accept` | Yes | — |

### Impersonation (3 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 53 | POST | `/am/impersonation/start` | Yes | `user_impersonation.enable` |
| 54 | POST | `/am/impersonation/end` | Yes | — |
| 55 | GET | `/am/impersonation/status` | Yes | — |

### Admin (6 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 56 | GET | `/am/admin/users` | Yes | `admin_console.view` |
| 57 | GET | `/am/admin/users/{user_id}/sessions` | Yes | `admin_console.view` |
| 58 | DELETE | `/am/admin/users/{user_id}/sessions/{session_id}` | Yes | `admin_console.update` |
| 59 | GET | `/am/admin/audit` | Yes | `admin_console.view` |
| 60 | GET | `/am/admin/impersonation/history` | Yes | `admin_console.view` |
| 61 | GET | `/am/admin/me/features` | Yes | — |

### Entity Settings (5 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 62 | GET | `/am/settings/{entity_type}/{entity_id}` | Yes | `{entity}_management.view` |
| 63 | GET | `/am/settings/{entity_type}/{entity_id}/keys` | Yes | `{entity}_management.view` |
| 64 | PUT | `/am/settings/{entity_type}/{entity_id}/{key}` | Yes | `{entity}_management.update` |
| 65 | PUT | `/am/settings/{entity_type}/{entity_id}` (batch) | Yes | `{entity}_management.update` |
| 66 | DELETE | `/am/settings/{entity_type}/{entity_id}/{key}` | Yes | `{entity}_management.update` |

### API Keys (6 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 67 | POST | `/am/api-keys` | JWT only | `api_key_management.create` |
| 68 | GET | `/am/api-keys` | JWT only | `api_key_management.view` |
| 69 | GET | `/am/api-keys/{key_id}` | JWT only | `api_key_management.view` |
| 70 | POST | `/am/api-keys/{key_id}/rotate` | JWT only | `api_key_management.update` |
| 71 | PATCH | `/am/api-keys/{key_id}/revoke` | JWT only | `api_key_management.revoke` |
| 72 | DELETE | `/am/api-keys/{key_id}` | JWT only | `api_key_management.revoke` |

### License Profiles (5 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 73 | GET | `/am/license-profiles` | Yes | `feature_flag_registry.view` |
| 74 | POST | `/am/license-profiles` | Yes | `feature_flag_registry.create` |
| 75 | PATCH | `/am/license-profiles/{code}` | Yes | `feature_flag_registry.update` |
| 76 | PUT | `/am/license-profiles/{code}/settings/{key}` | Yes | `feature_flag_registry.update` |
| 77 | DELETE | `/am/license-profiles/{code}/settings/{key}` | Yes | `feature_flag_registry.update` |

### Tasks (~15 endpoints)

| Method | Path | Permission |
|--------|------|------------|
| GET | `/tk/task-types` | — |
| GET | `/tk/task-priorities` | — |
| GET | `/tk/task-statuses` | — |
| GET | `/tk/tasks` | `tasks.view` |
| GET | `/tk/tasks/summary` | `tasks.view` |
| GET | `/tk/tasks/export` | `tasks.view` |
| POST | `/tk/tasks/bulk-update` | `tasks.update` |
| GET/POST/PATCH/DELETE | `/tk/tasks/{id}` | `tasks.*` |
| GET/POST/DELETE | `/tk/tasks/{id}/assignments` | `tasks.*` |
| GET/POST/DELETE | `/tk/tasks/{id}/dependencies` | `tasks.*` |
| GET/POST | `/tk/tasks/{id}/events` | `tasks.*` |

### GRC Library (~50 endpoints)

| Method | Path | Permission |
|--------|------|------------|
| GET | `/fr/framework-types`, `/fr/framework-categories`, `/fr/control-categories`, `/fr/control-criticalities`, `/fr/test-types`, `/fr/test-result-statuses` | `frameworks.view` |
| GET/POST/PATCH/DELETE | `/fr/frameworks` | `frameworks.*` |
| POST | `/fr/frameworks/{id}/submit` | `frameworks.update` |
| POST | `/fr/frameworks/{id}/approve` | `frameworks.update` |
| POST | `/fr/frameworks/{id}/reject` | `frameworks.update` |
| GET/PUT/DELETE | `/fr/frameworks/{id}/settings/{key}` | `frameworks.*` |
| GET/POST | `/fr/frameworks/{id}/versions` | `frameworks.*` |
| POST | `/fr/frameworks/{id}/versions/{vid}/publish` | `frameworks.update` |
| POST | `/fr/frameworks/{id}/versions/{vid}/deprecate` | `frameworks.update` |
| POST | `/fr/frameworks/{id}/versions/{vid}/restore` | `frameworks.update` |
| GET/POST/PATCH/DELETE | `/fr/frameworks/{id}/requirements` | `frameworks.*` |
| GET/POST/PATCH/DELETE | `/fr/frameworks/{id}/controls` | `frameworks.*` |
| GET/POST/PATCH/DELETE | `/fr/controls`, `/fr/tests` | `frameworks.*` |
| GET/POST/DELETE | `/fr/tests/{id}/controls` | `tests.*` |
| GET/POST/PATCH | `/fr/test-executions` | `tests.*` |
| GET/POST/PATCH/DELETE | `/fr/deployments` | `frameworks.*` |

### Risk Registry (~25 endpoints)

| Method | Path | Permission |
|--------|------|------------|
| GET | `/rr/risk-categories`, `/rr/risk-levels`, `/rr/treatment-types` | — |
| GET/POST/PATCH/DELETE | `/rr/risks` | `risks.*` |
| GET/POST/DELETE | `/rr/risks/{id}/assessments` | `risks.*` |
| GET/POST/PATCH/DELETE | `/rr/risks/{id}/treatment-plans` | `risks.*` |
| GET/POST/DELETE | `/rr/risks/{id}/control-mappings` | `risks.*` |
| GET/POST/DELETE | `/rr/risks/{id}/group-assignments` | `risks.*` |
| GET/POST | `/rr/risks/{id}/events` | `risks.*` |
| GET/PUT | `/rr/risks/{id}/review-schedule` | `risks.*` |
| POST | `/rr/risks/{id}/reviews` | `risks.*` |
| GET/PUT | `/rr/risk-appetite` | `risks.*` |
| GET | `/rr/risks/heat-map`, `/rr/risks/overdue-reviews` | `risks.view` |

### Notifications — Public Read (2 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 78 | GET | `/notifications/releases/public` | Yes | — (any authenticated user) |
| 79 | GET | `/notifications/incidents/active` | Yes | — (any authenticated user) |

### Org-Scoped Broadcasts (3 endpoints)

| # | Method | Path | Auth | Permission |
|---|--------|------|------|------------|
| 80 | GET | `/am/orgs/{org_id}/broadcasts` | Yes | Org membership |
| 81 | POST | `/am/orgs/{org_id}/broadcasts` | Yes | Org membership |
| 82 | POST | `/am/orgs/{org_id}/broadcasts/{id}/send` | Yes | Org membership |
