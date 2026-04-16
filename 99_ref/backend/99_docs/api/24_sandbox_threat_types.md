# Sandbox Threat Type Composer API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Permissions:** `sandbox.view`, `sandbox.create`, `sandbox.execute`
**Multi-tenant:** All endpoints require `org_id` as a query parameter. `tenant_key` is derived from the authenticated user's active organization.

---

## Overview

Threat types are boolean compositions of signals. Rather than writing a new signal for every threat scenario, you express how existing signals combine to indicate a threat using an AND/OR/NOT expression tree. The execution engine evaluates the tree against actual signal run results and records whether the threat was triggered.

**Examples of signal composition:**

| Threat | Expression |
|--------|-----------|
| Insider Threat — Privileged Access | `privileged_access_detected` AND (`unusual_login_time` OR `geo_anomaly`) |
| Security Hygiene Violation | `mfa_disabled` AND `stale_credentials` |
| Account Takeover | `geo_anomaly` AND `impossible_travel` AND NOT `known_vpn_exit` |
| Credential Compromise | `credential_stuffing_pattern` OR (`login_failed_burst` AND `geo_anomaly`) |

**Cascade delete guard:** A threat type cannot be deleted while it is referenced by an enabled policy. Disable or delete the policy first.

**Versioning:** Every PATCH creates a new version snapshot. The `version` field on the fact record always reflects the current version number. Version history is stored in `26_fct_threat_type_versions` (or equivalent version table).

---

## Architecture

- **Fact table:** `15_sandbox.23_fct_threat_types` — lean row with FK columns, severity, expression_tree (JSONB), version, is_active
- **Properties:** `15_sandbox.46_dtl_threat_type_properties` — EAV key-value pairs (name, description, mitigation_guidance, compliance_references, tags, caep_event_type, risc_event_type)
- **Evaluations:** `15_sandbox.26_fct_threat_evaluations` — evaluation records written by the execution engine
- **Severity dimension:** `15_sandbox.08_dim_threat_severities`

**EAV property keys:**

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | Display name |
| `description` | string | What threat scenario this represents |
| `mitigation_guidance` | string | Recommended response steps |
| `compliance_references` | string | Relevant compliance controls (e.g., NIST AC-6, ISO 27001 A.9.2.3) |
| `tags` | string | Comma-separated tags |
| `caep_event_type` | string | Corresponding CAEP event type code |
| `risc_event_type` | string | Corresponding RISC event type code |

---

## Cache Behavior

| Cache Key | TTL | Populated By | Invalidated By |
|-----------|-----|--------------|----------------|
| `sb:threat-types:{org_id}` | 5 min | GET /threat-types | POST, PATCH, DELETE /threat-types |
| `sb:threat-type:{id}` | 5 min | GET /threat-types/{id} | PATCH /threat-types/{id} |
| `sb:threat-type:{id}:versions` | 10 min | GET /threat-types/{id}/versions | PATCH /threat-types/{id} |
| `sb:threat-type:{id}:evaluations` | 2 min | GET /threat-types/{id}/evaluations | (populated by execution engine) |

---

## Expression Tree Format

The `expression_tree` field is a JSONB column on `23_fct_threat_types`. It encodes a recursive boolean tree. Signal codes reference `signal_code` values from `22_fct_signals`.

### Leaf node — signal condition

```json
{
  "signal_code": "mfa_disabled",
  "expected_result": "fail"
}
```

`expected_result` must be `"pass"`, `"fail"`, or `"warning"`. The leaf evaluates to `true` when the signal's actual result matches `expected_result`.

### Branch node — AND / OR

```json
{
  "operator": "AND",
  "conditions": [
    { "signal_code": "mfa_disabled", "expected_result": "fail" },
    { "signal_code": "stale_credentials", "expected_result": "fail" }
  ]
}
```

`AND` requires all conditions to be `true`. `OR` requires at least one. `conditions` must have at least two children for `AND`/`OR`.

### NOT node — negation

```json
{
  "operator": "NOT",
  "conditions": [
    { "signal_code": "known_vpn_exit", "expected_result": "pass" }
  ]
}
```

`NOT` inverts the evaluation of its single child. `conditions` must have exactly one child.

### Full nested example

```json
{
  "operator": "AND",
  "conditions": [
    { "signal_code": "privileged_access_detected", "expected_result": "fail" },
    {
      "operator": "OR",
      "conditions": [
        { "signal_code": "unusual_login_time", "expected_result": "fail" },
        { "signal_code": "geo_anomaly_detected", "expected_result": "fail" }
      ]
    },
    {
      "operator": "NOT",
      "conditions": [
        { "signal_code": "known_vpn_exit", "expected_result": "pass" }
      ]
    }
  ]
}
```

**Validation rules:**

- Every `signal_code` referenced must exist within the org and be in `validated` or `promoted` status
- `operator` must be `AND`, `OR`, or `NOT` (case-sensitive)
- `NOT` must have exactly one child in `conditions`
- `AND` and `OR` must have at least two children
- Circular references are not possible (tree structure enforced at parse time)
- Maximum tree depth: 10 levels

---

## Dimension Endpoints

### GET /api/v1/sb/dimensions/threat-severities

Returns all threat severity dimension records ordered by severity (most severe first).

**Permission:** `sandbox.view`

**Response** `200 OK`

```json
[
  { "code": "critical", "name": "Critical", "color_hex": "#ef4444", "sort_order": 1 },
  { "code": "high",     "name": "High",     "color_hex": "#f97316", "sort_order": 2 },
  { "code": "medium",   "name": "Medium",   "color_hex": "#eab308", "sort_order": 3 },
  { "code": "low",      "name": "Low",      "color_hex": "#3b82f6", "sort_order": 4 },
  { "code": "info",     "name": "Info",     "color_hex": "#6b7280", "sort_order": 5 }
]
```

**DB table:** `15_sandbox.08_dim_threat_severities`

---

## Threat Type Endpoints

### GET /api/v1/sb/threat-types

List threat types for the authenticated tenant. Returns metadata and selected EAV properties. Does not include the full expression tree — use the detail endpoint for that.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `org_id` | UUID | Yes | — | Organization scope |
| `workspace_id` | UUID | No | — | Filter to a specific workspace |
| `severity_code` | string | No | — | Filter: `critical`, `high`, `medium`, `low`, `info` |
| `is_active` | boolean | No | `true` | Include inactive threat types when `false` |
| `search` | string | No | — | Substring match on `name` or `description` EAV properties |
| `sort_by` | string | No | `created_at` | `created_at`, `severity_code`, `name` |
| `sort_dir` | string | No | `desc` | `asc` or `desc` |
| `limit` | integer | No | `100` | 1–500 |
| `offset` | integer | No | `0` | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "threat_code": "TH-001",
      "severity_code": "critical",
      "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
      "version": 3,
      "is_active": true,
      "created_at": "2026-03-10T00:00:00Z",
      "updated_at": "2026-03-15T12:30:00Z",
      "name": "Insider Threat — Privileged Access Abuse",
      "description": "Privileged user accessing resources outside normal patterns without MFA",
      "tags": "insider,access,mfa,privileged",
      "policy_count": 2
    },
    {
      "id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
      "threat_code": "TH-005",
      "severity_code": "high",
      "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
      "version": 1,
      "is_active": true,
      "created_at": "2026-03-14T10:00:00Z",
      "updated_at": "2026-03-14T10:00:00Z",
      "name": "Security Hygiene Violation",
      "description": "User accounts with disabled MFA and stale credentials",
      "tags": "hygiene,credentials,mfa",
      "policy_count": 1
    }
  ],
  "total": 14
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Invalid `severity_code` value |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` |
| `422` | Malformed UUID in filter params |
| `500` | Unexpected server error |

---

### GET /api/v1/sb/threat-types/{id}

Get a single threat type with the full expression tree and all EAV properties.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Threat type ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `200 OK`

```json
{
  "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "threat_code": "TH-001",
  "severity_code": "critical",
  "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "version": 3,
  "is_active": true,
  "created_at": "2026-03-10T00:00:00Z",
  "updated_at": "2026-03-15T12:30:00Z",
  "expression_tree": {
    "operator": "AND",
    "conditions": [
      { "signal_code": "mfa_disabled", "expected_result": "fail" },
      {
        "operator": "OR",
        "conditions": [
          { "signal_code": "unusual_login_time", "expected_result": "fail" },
          { "signal_code": "geo_anomaly_detected", "expected_result": "fail" }
        ]
      }
    ]
  },
  "name": "Insider Threat — Privileged Access Abuse",
  "description": "Privileged user accessing resources outside normal patterns without MFA",
  "mitigation_guidance": "Enforce MFA for all privileged accounts. Restrict access to business hours unless VPN-approved. Alert SOC on any geo anomaly for privileged users.",
  "compliance_references": "NIST AC-6, NIST IA-5, ISO 27001 A.9.2.3, SOC2 CC6.3",
  "tags": "insider,access,mfa,privileged",
  "caep_event_type": "session-revoked",
  "risc_event_type": "credential-compromise"
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or threat type belongs to different org |
| `404` | Threat type ID not found |
| `422` | `id` is not a valid UUID |
| `500` | Unexpected server error |

---

### POST /api/v1/sb/threat-types

Create a new threat type. Initial `version` is 1.

**Permission:** `sandbox.create`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body**

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `threat_code` | string | Yes | Unique per org, 2–20 chars, `[A-Z0-9-]` | Human-readable code (e.g., `TH-005`) |
| `workspace_id` | UUID | Yes | Must exist within org | Workspace assignment |
| `severity_code` | string | Yes | Must be a valid severity code | Severity level |
| `expression_tree` | object | Yes | Valid expression tree (see format section) | Boolean signal composition |
| `name` | string | Yes | Via `properties.name` | Display name |
| `description` | string | No | Via `properties.description` | Human-readable explanation |
| `mitigation_guidance` | string | No | Via `properties.mitigation_guidance` | Recommended response steps |
| `compliance_references` | string | No | Via `properties.compliance_references` | Compliance control references |
| `tags` | string | No | Via `properties.tags` | Comma-separated tags |
| `caep_event_type` | string | No | Via `properties.caep_event_type` | CAEP event type code |
| `risc_event_type` | string | No | Via `properties.risc_event_type` | RISC event type code |

```json
{
  "threat_code": "TH-005",
  "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "severity_code": "high",
  "expression_tree": {
    "operator": "AND",
    "conditions": [
      { "signal_code": "mfa_disabled", "expected_result": "fail" },
      { "signal_code": "stale_credentials", "expected_result": "fail" }
    ]
  },
  "name": "Security Hygiene Violation",
  "description": "User accounts with both MFA disabled and credentials older than 90 days",
  "mitigation_guidance": "Enforce credential rotation policy. Require MFA enrollment within 24 hours of detection. Suspend accounts that remain non-compliant after 48 hours.",
  "compliance_references": "NIST IA-5, SOC2 CC6.1, CIS Control 5",
  "tags": "hygiene,credentials,mfa",
  "caep_event_type": null,
  "risc_event_type": "account-credential-change-required"
}
```

**Response** `201 Created` — Full threat type object (same schema as GET detail)

```json
{
  "id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "threat_code": "TH-005",
  "severity_code": "high",
  "workspace_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "version": 1,
  "is_active": true,
  "created_at": "2026-03-16T11:30:00Z",
  "updated_at": "2026-03-16T11:30:00Z",
  "expression_tree": {
    "operator": "AND",
    "conditions": [
      { "signal_code": "mfa_disabled", "expected_result": "fail" },
      { "signal_code": "stale_credentials", "expected_result": "fail" }
    ]
  },
  "name": "Security Hygiene Violation",
  "description": "User accounts with both MFA disabled and credentials older than 90 days",
  "mitigation_guidance": "Enforce credential rotation policy...",
  "compliance_references": "NIST IA-5, SOC2 CC6.1, CIS Control 5",
  "tags": "hygiene,credentials,mfa",
  "caep_event_type": null,
  "risc_event_type": "account-credential-change-required"
}
```

**Business rules:**
- All `signal_code` values in the expression tree must exist within the org; they are not required to be `validated` or `promoted` at creation time (to allow building threat types while signals are still in testing), but the execution engine will skip evaluation if any referenced signal is not `promoted`
- Advisory lock is acquired per `threat_code` + `org_id` to prevent duplicate creation under concurrent requests

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Expression tree structure is invalid (wrong operator, NOT with multiple children, leaf missing `signal_code`) |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` |
| `404` | `workspace_id` not found or a `signal_code` in the expression tree not found within org |
| `409` | `threat_code` already exists within this org |
| `422` | Invalid `severity_code`, missing required fields, malformed UUID, or expression tree exceeds max depth |
| `429` | Rate limit exceeded |
| `500` | Unexpected server error |

---

### PATCH /api/v1/sb/threat-types/{id}

Update a threat type. Creates a **new version** — `version` increments and a snapshot of the previous state is stored in version history. All fields are optional; only supplied fields are changed.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Threat type ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body** (all fields optional)

| Field | Type | Description |
|-------|------|-------------|
| `severity_code` | string | Updated severity level |
| `expression_tree` | object | Fully replaced expression tree |
| `name` | string | Updated display name |
| `description` | string | Updated description |
| `mitigation_guidance` | string | Updated mitigation guidance |
| `compliance_references` | string | Updated compliance references |
| `tags` | string | Updated tags |
| `caep_event_type` | string | Updated CAEP event type |
| `risc_event_type` | string | Updated RISC event type |

```json
{
  "severity_code": "critical",
  "expression_tree": {
    "operator": "AND",
    "conditions": [
      { "signal_code": "mfa_disabled", "expected_result": "fail" },
      { "signal_code": "stale_credentials", "expected_result": "fail" },
      { "signal_code": "inactive_account_active", "expected_result": "fail" }
    ]
  },
  "description": "Updated: now also detects dormant accounts reactivated without remediation",
  "tags": "hygiene,credentials,mfa,dormant-accounts"
}
```

**Response** `200 OK` — Updated threat type object with incremented `version`

**Business rules:**
- Updating the `expression_tree` does not affect active policies — existing enabled policies continue to fire against the new expression tree immediately
- Version history captures the full `expression_tree` snapshot so evaluations can be traced back to the expression in effect at the time

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Expression tree structure is invalid |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or threat type belongs to different org |
| `404` | Threat type ID not found or a `signal_code` in updated expression tree not found |
| `422` | Invalid `severity_code` or malformed UUID |
| `500` | Unexpected server error |

---

### DELETE /api/v1/sb/threat-types/{id}

Soft-delete a threat type. Sets `is_active = false`. Fails if the threat type is referenced by one or more enabled policies.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Threat type ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `204 No Content`

**Business rules:**
- To delete a threat type that has enabled policies, first disable or delete each policy, then delete the threat type
- Evaluation history (`26_fct_threat_evaluations`) referencing this threat type is preserved
- Inactive threat types are excluded from new policy targets but remain visible in version history

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or threat type belongs to different org |
| `404` | Threat type ID not found |
| `409` | One or more enabled policies reference this threat type — disable or delete the policies first |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

## Simulation

### POST /api/v1/sb/threat-types/{id}/simulate

Evaluate the threat type's expression tree against a set of mock signal results. This is a dry-run that does not execute any actual signals, does not write any records, and does not affect any policy. Returns the boolean evaluation result and a step-by-step trace of the tree evaluation.

**Permission:** `sandbox.execute`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Threat type ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signal_results` | object | Yes | Map of `signal_code` to result string (`"pass"`, `"fail"`, or `"warning"`) |

```json
{
  "signal_results": {
    "mfa_disabled": "fail",
    "unusual_login_time": "pass",
    "geo_anomaly_detected": "fail"
  }
}
```

**Response** `200 OK`

```json
{
  "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "threat_code": "TH-001",
  "threat_version": 3,
  "triggered": true,
  "evaluation_trace": [
    {
      "node": "root",
      "operator": "AND",
      "result": true,
      "short_circuit": false
    },
    {
      "node": "root.0",
      "signal_code": "mfa_disabled",
      "expected_result": "fail",
      "actual_result": "fail",
      "match": true
    },
    {
      "node": "root.1",
      "operator": "OR",
      "result": true,
      "short_circuit": true
    },
    {
      "node": "root.1.0",
      "signal_code": "unusual_login_time",
      "expected_result": "fail",
      "actual_result": "pass",
      "match": false
    },
    {
      "node": "root.1.1",
      "signal_code": "geo_anomaly_detected",
      "expected_result": "fail",
      "actual_result": "fail",
      "match": true
    }
  ]
}
```

**Not triggered example:**

```json
{
  "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "threat_code": "TH-001",
  "threat_version": 3,
  "triggered": false,
  "evaluation_trace": [
    {
      "node": "root",
      "operator": "AND",
      "result": false,
      "short_circuit": true
    },
    {
      "node": "root.0",
      "signal_code": "mfa_disabled",
      "expected_result": "fail",
      "actual_result": "pass",
      "match": false
    }
  ]
}
```

**Trace node fields:**

| Field | Description |
|-------|-------------|
| `node` | Dot-path position in the tree (e.g., `root.1.0`) |
| `operator` | Present on branch nodes: `AND`, `OR`, `NOT` |
| `signal_code` | Present on leaf nodes: the signal being evaluated |
| `expected_result` | Present on leaf nodes: what was expected |
| `actual_result` | Present on leaf nodes: what was provided in `signal_results` |
| `match` | Present on leaf nodes: `true` if `actual_result == expected_result` |
| `result` | Present on branch nodes: boolean result of this subtree |
| `short_circuit` | `true` if evaluation stopped early (AND after first false, OR after first true) |

**Business rules:**
- All `signal_code` values referenced in the expression tree must be present in `signal_results` — missing signals return `422`
- Extra keys in `signal_results` that are not referenced in the tree are silently ignored
- This endpoint uses the current version of the expression tree, not a historical version

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | `signal_results` values are not `pass`, `fail`, or `warning` |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.execute` or threat type belongs to different org |
| `404` | Threat type ID not found |
| `422` | A `signal_code` referenced in the expression tree is missing from `signal_results`, or malformed UUID |
| `500` | Unexpected server error |

---

## Version History

### GET /api/v1/sb/threat-types/{id}/versions

List all versions of a threat type, newest first. Each version is an immutable snapshot captured on every PATCH, including the full expression tree and property values at that point in time.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Threat type ID |

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
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "version": 3,
      "severity_code": "critical",
      "expression_tree": {
        "operator": "AND",
        "conditions": [
          { "signal_code": "mfa_disabled", "expected_result": "fail" },
          {
            "operator": "OR",
            "conditions": [
              { "signal_code": "unusual_login_time", "expected_result": "fail" },
              { "signal_code": "geo_anomaly_detected", "expected_result": "fail" }
            ]
          }
        ]
      },
      "properties_snapshot": {
        "name": "Insider Threat — Privileged Access Abuse",
        "description": "Privileged user accessing resources outside normal patterns without MFA",
        "mitigation_guidance": "Enforce MFA for all privileged accounts...",
        "compliance_references": "NIST AC-6, NIST IA-5",
        "tags": "insider,access,mfa,privileged"
      },
      "changed_by": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "created_at": "2026-03-15T12:30:00Z"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "version": 2,
      "severity_code": "high",
      "expression_tree": {
        "operator": "AND",
        "conditions": [
          { "signal_code": "mfa_disabled", "expected_result": "fail" },
          { "signal_code": "unusual_login_time", "expected_result": "fail" }
        ]
      },
      "properties_snapshot": {
        "name": "Insider Threat — Privileged Access Abuse",
        "description": "Original description (pre-geo anomaly signal)",
        "mitigation_guidance": "...",
        "tags": "insider,access,mfa"
      },
      "changed_by": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "created_at": "2026-03-12T09:00:00Z"
    }
  ],
  "total": 3
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or threat type belongs to different org |
| `404` | Threat type ID not found |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

## Evaluation History

### GET /api/v1/sb/threat-types/{id}/evaluations

List threat evaluations for this threat type. Evaluation records are written by the execution engine each time it processes a batch run and evaluates the expression tree against actual signal results. Results are stored in ClickHouse and surfaced here.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `id` | UUID | Threat type ID |

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `org_id` | UUID | Yes | — | Organization scope |
| `triggered` | boolean | No | — | Filter to triggered (`true`) or not triggered (`false`) evaluations |
| `limit` | integer | No | `100` | 1–500 |
| `offset` | integer | No | `0` | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "dataset_id": "a9b0c1d2-e3f4-5678-abcd-901234567890",
      "triggered": true,
      "signal_results": {
        "mfa_disabled": "fail",
        "unusual_login_time": "fail",
        "geo_anomaly_detected": "pass"
      },
      "threat_type_version": 3,
      "policy_executions_triggered": 1,
      "created_at": "2026-03-16T02:06:00Z"
    },
    {
      "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "dataset_id": "b0c1d2e3-f4a5-6789-bcde-012345678901",
      "triggered": false,
      "signal_results": {
        "mfa_disabled": "pass",
        "unusual_login_time": "pass",
        "geo_anomaly_detected": "pass"
      },
      "threat_type_version": 3,
      "policy_executions_triggered": 0,
      "created_at": "2026-03-15T02:06:00Z"
    }
  ],
  "total": 42
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or threat type belongs to different org |
| `404` | Threat type ID not found |
| `422` | Malformed UUID |
| `500` | ClickHouse query error |

---

## Related Endpoints

- **Signals:** `GET /api/v1/sb/signals` — browse available signals to use in expression trees
- **Policies:** `GET /api/v1/sb/policies?threat_type_id={id}` — list policies attached to this threat type
- **Simulate:** `POST /api/v1/sb/threat-types/{id}/simulate` — test expression tree without executing signals
- **Policy dry-run:** `POST /api/v1/sb/policies/{id}/test` — test the full threat-to-policy chain

## DB Tables Reference

| Table | Schema | Purpose |
|-------|--------|---------|
| `08_dim_threat_severities` | `15_sandbox` | Severity dimension (info through critical) |
| `23_fct_threat_types` | `15_sandbox` | Threat type fact table (code, severity FK, expression_tree JSONB, version, is_active) |
| `46_dtl_threat_type_properties` | `15_sandbox` | EAV properties (name, description, mitigation_guidance, compliance_references, tags, event types) |
| `26_fct_threat_evaluations` | `15_sandbox` | Evaluation records written by execution engine |

Version snapshots are stored in a separate version table linked to `23_fct_threat_types`.

All mutations are audited via the unified audit system (`40_aud_events` + `41_dtl_audit_event_properties`).
