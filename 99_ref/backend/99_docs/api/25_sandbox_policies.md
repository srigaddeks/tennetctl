# Sandbox Policy Engine API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Permissions:** `sandbox.view`, `sandbox.create`, `sandbox.execute`, `sandbox.promote`
**Multi-tenant:** All endpoints require `org_id` as a query parameter. `tenant_key` is derived from the authenticated user's active organization.

---

## Overview

Policies define what happens when a threat type triggers. Each policy is attached to exactly one threat type and contains an ordered list of actions to execute. When the execution engine evaluates a threat type and finds it triggered, it looks for enabled policies attached to that threat type and fires their action lists.

**Action execution model:**
- Actions execute in array order
- If one action fails, the failure is recorded but subsequent actions still run (fail-open per action)
- The overall policy execution outcome reflects whether all, some, or no actions succeeded
- Policies in cooldown are skipped entirely — no actions fire

**Cooldown:** After a policy fires, it will not fire again until `cooldown_minutes` have elapsed since the last execution. This prevents alert storms from repeated triggers on the same dataset within a short window.

**Cascade delete guard:** A threat type cannot be deleted while any policy attached to it is enabled. Disable or delete the policy first.

**Versioning:** Every PATCH creates a new version snapshot. The `version` field on the fact record always reflects the current version number.

---

## Architecture

- **Fact table:** `15_sandbox.24_fct_policies` — lean row with threat_type FK, actions JSONB array, cooldown_minutes, version, is_enabled
- **Properties:** `15_sandbox.47_dtl_policy_properties` — EAV key-value pairs (name, description, owner, escalation_path, sla_notes, tags)
- **Executions:** `15_sandbox.27_fct_policy_executions` — execution audit trail (outcome, actions_executed JSONB, policy_version)
- **Library link:** `15_sandbox.51_lnk_library_policies` — optional library associations

**EAV property keys:**

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | Display name |
| `description` | string | What this policy does and when it fires |
| `owner` | string | Team or person responsible for this policy |
| `escalation_path` | string | Human-readable escalation chain |
| `sla_notes` | string | Response time SLA expectations |
| `tags` | string | Comma-separated tags |

---

## Actions Config Format

The `actions` field is a JSONB array on `24_fct_policies`. Each element has an `action_type` (FK to `09_dim_policy_action_types`) and a freeform `config` object whose schema is action-type specific. Actions execute in array order.

**Per-action-type config schemas:**

```json
[
  {
    "action_type": "notification",
    "config": {
      "channel": "slack",
      "slack_webhook_url": "https://hooks.slack.com/...",
      "severity": "critical",
      "template": "insider_threat_alert",
      "mention_group": "@security-oncall"
    }
  },
  {
    "action_type": "evidence_report",
    "config": {
      "template": "security_incident",
      "include_datasets": true,
      "include_signal_details": true,
      "recipients": ["security-lead@example.com"]
    }
  },
  {
    "action_type": "rca_agent",
    "config": {
      "agent_type": "standard",
      "max_depth": 3,
      "include_timeline": true
    }
  },
  {
    "action_type": "escalate",
    "config": {
      "escalation_group": "soc_tier2",
      "timeout_minutes": 15,
      "fallback_group": "security_manager"
    }
  },
  {
    "action_type": "create_task",
    "config": {
      "task_type": "control_remediation",
      "priority": "critical",
      "assignee_group": "identity-team",
      "due_in_hours": 4
    }
  },
  {
    "action_type": "webhook",
    "config": {
      "url": "https://siem.example.com/api/v1/ingest",
      "method": "POST",
      "headers": { "X-Source": "kcontrol", "Authorization": "Bearer ${SIEM_TOKEN}" },
      "body_template": "default_threat_payload"
    }
  },
  {
    "action_type": "disable_access",
    "config": {
      "scope": "session",
      "reason": "automated_threat_response",
      "notify_user": true
    }
  },
  {
    "action_type": "quarantine",
    "config": {
      "resource_type": "pod",
      "network_policy": "deny_all_egress",
      "duration_minutes": 60
    }
  }
]
```

---

## Cache Behavior

| Cache Key | TTL | Populated By | Invalidated By |
|-----------|-----|--------------|----------------|
| `sb:policies:{org_id}` | 5 min | GET /policies | POST, PATCH, DELETE /policies, POST /policies/{id}/enable, POST /policies/{id}/disable |
| `sb:policy:{id}` | 5 min | GET /policies/{id} | PATCH /policies/{id}, enable, disable |
| `sb:policy:{id}:versions` | 10 min | GET /policies/{id}/versions | PATCH /policies/{id} |
| `sb:policy:{id}:executions` | 2 min | GET /policies/{id}/executions | (populated by execution engine) |

---

## Dimension Endpoints

### GET /api/v1/sb/dimensions/policy-action-types

Returns all policy action type dimension records.

**Permission:** `sandbox.view`

**Response** `200 OK`

```json
[
  {
    "code": "notification",
    "name": "Notification",
    "description": "Send alert via channel (Slack, email, PagerDuty, etc.)",
    "sort_order": 1
  },
  {
    "code": "evidence_report",
    "name": "Evidence Report",
    "description": "Generate a structured evidence or incident report",
    "sort_order": 2
  },
  {
    "code": "rca_agent",
    "name": "RCA Agent",
    "description": "Trigger automated root cause analysis agent",
    "sort_order": 3
  },
  {
    "code": "escalate",
    "name": "Escalate",
    "description": "Escalate to a designated responder group",
    "sort_order": 4
  },
  {
    "code": "create_task",
    "name": "Create Task",
    "description": "Create a remediation task in the task tracker",
    "sort_order": 5
  },
  {
    "code": "webhook",
    "name": "Webhook",
    "description": "Fire an outbound HTTP webhook to an external system (SIEM, SOAR, etc.)",
    "sort_order": 6
  },
  {
    "code": "disable_access",
    "name": "Disable Access",
    "description": "Revoke user or session access automatically",
    "sort_order": 7
  },
  {
    "code": "quarantine",
    "name": "Quarantine",
    "description": "Isolate the affected resource from the network",
    "sort_order": 8
  }
]
```

**DB table:** `15_sandbox.09_dim_policy_action_types`

---

## Policy Endpoints

### GET /api/v1/sb/policies

List policies for the authenticated tenant. Returns metadata and selected EAV properties. Does not include the full `actions` array — use the detail endpoint for that.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `org_id` | UUID | Yes | — | Organization scope |
| `workspace_id` | UUID | No | — | Filter to a specific workspace |
| `threat_type_id` | UUID | No | — | Filter to policies for a specific threat type |
| `is_enabled` | boolean | No | — | Filter enabled (`true`) or disabled (`false`) policies |
| `search` | string | No | — | Substring match on `name` or `description` EAV properties |
| `sort_by` | string | No | `created_at` | `created_at`, `name` |
| `sort_dir` | string | No | `desc` | `asc` or `desc` |
| `limit` | integer | No | `100` | 1–500 |
| `offset` | integer | No | `0` | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "policy_code": "POL-001",
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
      "version": 2,
      "is_enabled": true,
      "cooldown_minutes": 60,
      "action_count": 3,
      "last_executed_at": "2026-03-16T02:06:00Z",
      "created_at": "2026-03-10T00:00:00Z",
      "updated_at": "2026-03-14T08:00:00Z",
      "name": "Insider Threat Response",
      "description": "Automated response when insider threat is detected",
      "owner": "security-ops",
      "tags": "insider,response,automated"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "policy_code": "POL-003",
      "threat_type_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
      "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
      "version": 1,
      "is_enabled": true,
      "cooldown_minutes": 30,
      "action_count": 2,
      "last_executed_at": null,
      "created_at": "2026-03-14T10:00:00Z",
      "updated_at": "2026-03-14T10:00:00Z",
      "name": "Security Hygiene Policy",
      "description": "Response to credential hygiene violations",
      "owner": "identity-team",
      "tags": "hygiene,credentials"
    }
  ],
  "total": 7
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` |
| `422` | Malformed UUID in filter params |
| `500` | Unexpected server error |

---

### GET /api/v1/sb/policies/{id}

Get a single policy with the full `actions` array and all EAV properties.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Policy ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "policy_code": "POL-001",
  "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "version": 2,
  "is_enabled": true,
  "cooldown_minutes": 60,
  "actions": [
    {
      "action_type": "notification",
      "config": {
        "channel": "slack",
        "severity": "critical",
        "template": "insider_threat_alert",
        "mention_group": "@security-oncall"
      }
    },
    {
      "action_type": "evidence_report",
      "config": {
        "template": "security_incident",
        "include_datasets": true,
        "include_signal_details": true
      }
    },
    {
      "action_type": "create_task",
      "config": {
        "task_type": "control_remediation",
        "priority": "critical",
        "due_in_hours": 4
      }
    }
  ],
  "name": "Insider Threat Response",
  "description": "Automated response when insider threat is detected. Notifies SOC, generates evidence report, and creates a remediation task.",
  "owner": "security-ops",
  "escalation_path": "SOC Lead → CISO → VP Engineering",
  "sla_notes": "Acknowledge within 15 minutes. Resolve within 4 hours.",
  "tags": "insider,response,automated",
  "last_executed_at": "2026-03-16T02:06:00Z",
  "created_at": "2026-03-10T00:00:00Z",
  "updated_at": "2026-03-14T08:00:00Z"
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or policy belongs to different org |
| `404` | Policy ID not found |
| `422` | `id` is not a valid UUID |
| `500` | Unexpected server error |

---

### POST /api/v1/sb/policies

Create a new policy. Initial `version` is 1. The policy is created in a **disabled** state — call `POST .../enable` to activate it.

**Permission:** `sandbox.create`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body**

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `policy_code` | string | Yes | Unique per org, 2–20 chars, `[A-Z0-9-]` | Human-readable code (e.g., `POL-003`) |
| `workspace_id` | UUID | Yes | Must exist within org | Workspace assignment |
| `threat_type_id` | UUID | Yes | Must exist within org | The threat type that triggers this policy |
| `cooldown_minutes` | integer | No | 0–10080 (0 = no cooldown, max 7 days) | Minimum time between executions in minutes |
| `actions` | array | Yes | At least one action; each must have valid `action_type` | Ordered list of actions to execute |
| `name` | string | Yes | Non-empty | Display name |
| `description` | string | No | — | What this policy does and when it fires |
| `owner` | string | No | — | Responsible team or person |
| `escalation_path` | string | No | — | Human-readable escalation chain |
| `sla_notes` | string | No | — | Response time expectations |
| `tags` | string | No | — | Comma-separated tags |

```json
{
  "policy_code": "POL-003",
  "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "threat_type_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "cooldown_minutes": 30,
  "actions": [
    {
      "action_type": "notification",
      "config": {
        "channel": "email",
        "template": "hygiene_alert",
        "recipients": ["identity-team@example.com"]
      }
    },
    {
      "action_type": "create_task",
      "config": {
        "task_type": "user_remediation",
        "priority": "medium",
        "assignee_group": "identity-team",
        "due_in_hours": 24
      }
    }
  ],
  "name": "Security Hygiene Policy",
  "description": "Response to credential hygiene violations — notifies identity team and creates remediation task",
  "owner": "identity-team",
  "escalation_path": "Identity Lead → Security Manager",
  "sla_notes": "Resolve within 24 hours",
  "tags": "hygiene,credentials"
}
```

**Response** `201 Created` — Full policy object (same schema as GET detail)

```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "policy_code": "POL-003",
  "threat_type_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "version": 1,
  "is_enabled": false,
  "cooldown_minutes": 30,
  "actions": [...],
  "name": "Security Hygiene Policy",
  "description": "Response to credential hygiene violations...",
  "owner": "identity-team",
  "escalation_path": "Identity Lead → Security Manager",
  "sla_notes": "Resolve within 24 hours",
  "tags": "hygiene,credentials",
  "last_executed_at": null,
  "created_at": "2026-03-16T11:30:00Z",
  "updated_at": "2026-03-16T11:30:00Z"
}
```

**Business rules:**
- New policies are always created disabled (`is_enabled: false`)
- `cooldown_minutes: 0` means no cooldown — the policy can fire on every trigger
- Multiple policies can be attached to the same threat type; all enabled policies fire when the threat triggers

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | `actions` array is empty |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` |
| `404` | `workspace_id` or `threat_type_id` not found within org |
| `409` | `policy_code` already exists within this org |
| `422` | Invalid `action_type` in actions array, `cooldown_minutes` out of range, or malformed UUID |
| `429` | Rate limit exceeded |
| `500` | Unexpected server error |

---

### PATCH /api/v1/sb/policies/{id}

Update a policy. Creates a **new version** — `version` increments and a snapshot of the previous state is stored in version history. All fields are optional; only supplied fields are changed.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Policy ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body** (all fields optional)

| Field | Type | Description |
|-------|------|-------------|
| `threat_type_id` | UUID | Reassign to a different threat type |
| `cooldown_minutes` | integer | Updated cooldown window |
| `actions` | array | Fully replaced actions list |
| `name` | string | Updated display name |
| `description` | string | Updated description |
| `owner` | string | Updated owner |
| `escalation_path` | string | Updated escalation chain |
| `sla_notes` | string | Updated SLA notes |
| `tags` | string | Updated tags |

```json
{
  "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "cooldown_minutes": 120,
  "actions": [
    {
      "action_type": "notification",
      "config": { "channel": "slack", "template": "hygiene_alert_v2", "mention_group": "@identity-team" }
    },
    {
      "action_type": "escalate",
      "config": { "escalation_group": "identity_lead", "timeout_minutes": 30 }
    },
    {
      "action_type": "create_task",
      "config": { "task_type": "user_remediation", "priority": "high", "due_in_hours": 8 }
    }
  ],
  "description": "Updated: escalation added after SLA miss analysis",
  "owner": "identity-team",
  "sla_notes": "Acknowledge within 30 minutes. Resolve within 8 hours."
}
```

**Response** `200 OK` — Updated policy object with incremented `version`

**Business rules:**
- Patching an enabled policy takes effect immediately on the next execution; in-progress executions use the previous version
- Replacing `threat_type_id` reassigns the policy to a different threat — use with caution if the policy is currently enabled
- `actions` in the request body fully replaces the existing actions list — omitting it leaves actions unchanged

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | `actions` array is provided but empty |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or policy belongs to different org |
| `404` | Policy ID or new `threat_type_id` not found |
| `422` | Invalid `action_type`, `cooldown_minutes` out of range, or malformed UUID |
| `500` | Unexpected server error |

---

### DELETE /api/v1/sb/policies/{id}

Soft-delete a policy. Sets `is_active = false`. Fails if the policy is currently enabled.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Policy ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `204 No Content`

**Business rules:**
- Disable the policy first (`POST .../disable`), then delete
- Execution history is preserved after deletion

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or policy belongs to different org |
| `404` | Policy ID not found |
| `409` | Policy is enabled — disable it first |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

## Enable / Disable

### POST /api/v1/sb/policies/{id}/enable

Enable a policy. Once enabled, the policy's actions will fire the next time its linked threat type triggers and the cooldown has elapsed.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Policy ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body:** None required.

**Response** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "policy_code": "POL-001",
  "is_enabled": true,
  "updated_at": "2026-03-16T11:45:00Z"
}
```

**Business rules:**
- Enabling is idempotent — enabling an already-enabled policy returns `200` with `is_enabled: true`
- The policy's threat type must exist and be active; the API does not require signals referenced by the threat type to be `promoted`, but the execution engine will only evaluate `promoted` signals at runtime

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or policy belongs to different org |
| `404` | Policy ID not found |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

### POST /api/v1/sb/policies/{id}/disable

Disable a policy without deleting it. Disabled policies are skipped during execution. The policy configuration and history are preserved.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Policy ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body:** None required.

**Response** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "policy_code": "POL-001",
  "is_enabled": false,
  "updated_at": "2026-03-16T11:50:00Z"
}
```

**Business rules:**
- Disabling is idempotent — disabling an already-disabled policy returns `200` with `is_enabled: false`
- Disabling a policy is required before deleting it and before deleting its linked threat type

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or policy belongs to different org |
| `404` | Policy ID not found |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

## Dry Run

### POST /api/v1/sb/policies/{id}/test

Simulate policy execution. Evaluates the threat type expression tree against provided signal results and determines which actions would fire. Does **not** execute any actions and does **not** write any records to `27_fct_policy_executions`. This is a pure read-only simulation.

**Permission:** `sandbox.execute`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Policy ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body** (optional — override signal results for the linked threat type)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signal_results` | object | No | Map of `signal_code` to result; if omitted, the most recent actual signal run results for the linked dataset are used |

```json
{
  "signal_results": {
    "mfa_disabled": "fail",
    "stale_credentials": "fail"
  }
}
```

**Response** `200 OK` — Threat triggers, cooldown not active

```json
{
  "policy_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "policy_code": "POL-003",
  "policy_version": 1,
  "threat_type_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "threat_triggered": true,
  "is_enabled": true,
  "cooldown_active": false,
  "cooldown_remaining_minutes": 0,
  "last_executed_at": null,
  "actions_that_would_execute": [
    {
      "action_type": "notification",
      "config": { "channel": "email", "template": "hygiene_alert" },
      "status": "would_execute"
    },
    {
      "action_type": "create_task",
      "config": { "task_type": "user_remediation", "priority": "medium" },
      "status": "would_execute"
    }
  ]
}
```

**Response** `200 OK` — Policy is in cooldown

```json
{
  "policy_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "policy_code": "POL-001",
  "policy_version": 2,
  "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "threat_triggered": true,
  "is_enabled": true,
  "cooldown_active": true,
  "cooldown_remaining_minutes": 18,
  "last_executed_at": "2026-03-16T12:00:00Z",
  "actions_that_would_execute": []
}
```

**Response** `200 OK` — Threat does not trigger

```json
{
  "policy_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "policy_code": "POL-001",
  "policy_version": 2,
  "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "threat_triggered": false,
  "is_enabled": true,
  "cooldown_active": false,
  "cooldown_remaining_minutes": 0,
  "last_executed_at": null,
  "actions_that_would_execute": []
}
```

**Business rules:**
- If `signal_results` is not provided and no recent signal runs exist for the linked threat type, a `409` is returned asking for explicit `signal_results`
- If the policy is disabled, `actions_that_would_execute` will still be returned as if it were enabled, with a note that `is_enabled: false` means nothing would actually fire in production
- The simulation uses the current version of both the policy actions and the threat type expression tree

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | `signal_results` values are not `pass`, `fail`, or `warning` |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.execute` or policy belongs to different org |
| `404` | Policy ID not found |
| `409` | No `signal_results` provided and no recent signal runs found for this threat type |
| `422` | A `signal_code` referenced in the expression tree is missing from `signal_results`, or malformed UUID |
| `500` | Unexpected server error |

---

## Version History

### GET /api/v1/sb/policies/{id}/versions

List all versions of a policy, newest first. Each version is an immutable snapshot captured on every PATCH, including the full `actions` list and property values at that point in time.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Policy ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `limit` | integer | No | 1–100 (default: 50) |
| `offset` | integer | No | >= 0 (default: 0) |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "policy_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "version": 2,
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "cooldown_minutes": 60,
      "actions": [
        { "action_type": "notification", "config": { "channel": "slack", "severity": "critical" } },
        { "action_type": "evidence_report", "config": { "template": "security_incident" } },
        { "action_type": "create_task", "config": { "task_type": "control_remediation", "priority": "critical" } }
      ],
      "properties_snapshot": {
        "name": "Insider Threat Response",
        "description": "Automated response when insider threat is detected",
        "owner": "security-ops",
        "escalation_path": "SOC Lead → CISO → VP Engineering",
        "sla_notes": "Acknowledge within 15 minutes. Resolve within 4 hours."
      },
      "changed_by": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "created_at": "2026-03-14T08:00:00Z"
    },
    {
      "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "policy_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "version": 1,
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "cooldown_minutes": 30,
      "actions": [
        { "action_type": "notification", "config": { "channel": "email", "template": "insider_alert_v1" } }
      ],
      "properties_snapshot": {
        "name": "Insider Threat Response",
        "description": "Initial version — email notification only",
        "owner": "security-ops"
      },
      "changed_by": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "created_at": "2026-03-10T00:00:00Z"
    }
  ],
  "total": 2
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or policy belongs to different org |
| `404` | Policy ID not found |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

## Execution History

### GET /api/v1/sb/policies/{id}/executions

List policy executions for this policy. Execution records are written by the execution engine when a threat triggers and the policy fires. Stored in ClickHouse and surfaced here.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Policy ID |

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `org_id` | UUID | Yes | — | Organization scope |
| `outcome` | string | No | — | Filter: `succeeded`, `partial_failure`, `failed`, `skipped_cooldown` |
| `limit` | integer | No | `100` | 1–500 |
| `offset` | integer | No | `0` | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "policy_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "threat_evaluation_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "outcome": "succeeded",
      "policy_version": 2,
      "cooldown_was_active": false,
      "actions_executed": [
        {
          "action_type": "notification",
          "status": "succeeded",
          "duration_ms": 120,
          "detail": "Slack message delivered to #security-oncall"
        },
        {
          "action_type": "evidence_report",
          "status": "succeeded",
          "duration_ms": 450,
          "detail": "Report generated: incident-2026-03-16-001.pdf"
        },
        {
          "action_type": "create_task",
          "status": "succeeded",
          "duration_ms": 80,
          "detail": "Task created: TASK-4421"
        }
      ],
      "total_duration_ms": 650,
      "created_at": "2026-03-16T02:06:05Z"
    },
    {
      "id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
      "policy_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "threat_evaluation_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "outcome": "skipped_cooldown",
      "policy_version": 2,
      "cooldown_was_active": true,
      "actions_executed": [],
      "total_duration_ms": 0,
      "created_at": "2026-03-16T02:10:00Z"
    },
    {
      "id": "a7b8c9d0-e1f2-3456-abcd-567890123456",
      "policy_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "threat_evaluation_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "outcome": "partial_failure",
      "policy_version": 2,
      "cooldown_was_active": false,
      "actions_executed": [
        {
          "action_type": "notification",
          "status": "succeeded",
          "duration_ms": 95,
          "detail": "Slack message delivered"
        },
        {
          "action_type": "evidence_report",
          "status": "failed",
          "duration_ms": 5000,
          "detail": "Report generation timed out after 5000ms"
        },
        {
          "action_type": "create_task",
          "status": "succeeded",
          "duration_ms": 88,
          "detail": "Task created: TASK-4435"
        }
      ],
      "total_duration_ms": 5183,
      "created_at": "2026-03-15T14:00:05Z"
    }
  ],
  "total": 18
}
```

**Outcome values:**

| Value | Description |
|-------|-------------|
| `succeeded` | All actions completed successfully |
| `partial_failure` | Some actions failed, others succeeded |
| `failed` | All actions failed |
| `skipped_cooldown` | Policy was in cooldown period; no actions fired |

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Invalid `outcome` filter value |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or policy belongs to different org |
| `404` | Policy ID not found |
| `422` | Malformed UUID |
| `500` | ClickHouse query error |

---

## Related Endpoints

- **Threat types:** `GET /api/v1/sb/threat-types/{id}` — view the expression tree a policy fires on
- **Simulate threat:** `POST /api/v1/sb/threat-types/{id}/simulate` — test signal combination before attaching a policy
- **Signal runs:** `GET /api/v1/sb/signals/{id}/runs` — see the signal results that feed into threat evaluations
- **Policy dry-run:** `POST /api/v1/sb/policies/{id}/test` — test the full threat-to-policy chain before enabling

## DB Tables Reference

| Table | Schema | Purpose |
|-------|--------|---------|
| `09_dim_policy_action_types` | `15_sandbox` | Action type dimension (notification, escalate, webhook, etc.) |
| `24_fct_policies` | `15_sandbox` | Policy fact table (code, threat_type FK, actions JSONB, cooldown, version, is_enabled) |
| `47_dtl_policy_properties` | `15_sandbox` | EAV properties (name, description, owner, escalation_path, sla_notes, tags) |
| `27_fct_policy_executions` | `15_sandbox` | Execution audit trail (outcome, actions_executed JSONB, policy_version) |
| `51_lnk_library_policies` | `15_sandbox` | Optional library associations |

Execution records are stored in ClickHouse for analytics; summary records are also written to `27_fct_policy_executions` in PostgreSQL.

All mutations are audited via the unified audit system (`40_aud_events` + `41_dtl_audit_event_properties`).
