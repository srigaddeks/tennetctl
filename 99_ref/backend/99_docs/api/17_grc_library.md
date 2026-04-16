# GRC Library API

Base path: `/api/v1/fr`
Auth: Bearer JWT required on all endpoints

---

## Dimensions

### GET /api/v1/fr/framework-types
Returns all framework type dimension records.

**Response** `200 OK` — `DimensionResponse[]`
```json
[
  { "code": "compliance_standard", "name": "Compliance Standard", "description": "...", "sort_order": 1 }
]
```

### GET /api/v1/fr/framework-categories
Returns all framework category dimension records.

### GET /api/v1/fr/control-categories
Returns all control category dimension records (14 entries: access_control, change_management, ...).

### GET /api/v1/fr/control-criticalities
Returns all control criticality levels: critical, high, medium, low.

### GET /api/v1/fr/test-types
Returns test type dimension records: automated, manual, semi_automated.

### GET /api/v1/fr/test-result-statuses
Returns test result status records: pass, fail, partial, unknown, error.

---

## Frameworks

### GET /api/v1/fr/frameworks
List frameworks for the authenticated tenant.

**Query params**
| Param | Type | Description |
|-------|------|-------------|
| framework_type_code | string | Filter by type (compliance_standard, security_framework, ...) |
| framework_category_code | string | Filter by category |
| approval_status | string | draft, pending_review, approved, rejected, suspended |
| is_active | boolean | Filter by active status |
| sort_by | string | created_at, framework_code, approval_status |
| sort_dir | string | asc, desc (default: desc) |
| limit | int | 1–500 (default: 100) |
| offset | int | ≥0 (default: 0) |

**Response** `200 OK`
```json
{
  "items": [ { "id": "...", "framework_code": "soc2", "framework_type_code": "compliance_standard", ... } ],
  "total": 42
}
```

### GET /api/v1/fr/frameworks/{framework_id}
Get single framework with all EAV properties.

**Response** `200 OK` — `FrameworkResponse`
```json
{
  "id": "...", "framework_code": "soc2", "framework_type_code": "compliance_standard",
  "framework_category_code": "compliance", "approval_status": "approved",
  "is_marketplace_visible": true, "is_active": true,
  "name": "SOC 2", "description": "...", "publisher_type": "official",
  "publisher_name": "AICPA", "documentation_url": "https://..."
}
```

### POST /api/v1/fr/frameworks
Create a new framework.

**Request body**
```json
{
  "framework_code": "my-framework",
  "framework_type_code": "compliance_standard",
  "framework_category_code": "compliance",
  "name": "My Framework",
  "description": "Optional description",
  "publisher_type": "internal",
  "publisher_name": "Acme Corp",
  "approval_status": "draft",
  "is_marketplace_visible": false
}
```

### PATCH /api/v1/fr/frameworks/{framework_id}
Update a framework's mutable fields.

**Request body** (all optional)
```json
{
  "framework_type_code": "security_framework",
  "framework_category_code": "security",
  "approval_status": "approved",
  "is_marketplace_visible": true,
  "is_active": true,
  "name": "Updated Name",
  "description": "Updated description"
}
```

### DELETE /api/v1/fr/frameworks/{framework_id}
Soft-delete a framework. Returns `204 No Content`.

---

## Framework Settings

### GET /api/v1/fr/frameworks/{framework_id}/settings
List all settings for a framework.

**Response** `200 OK` — `FrameworkSettingResponse[]`
```json
[
  { "id": "...", "framework_id": "...", "setting_key": "auto_publish", "setting_value": "false" }
]
```

### PUT /api/v1/fr/frameworks/{framework_id}/settings/{key}
Upsert a framework setting.

**Request body**
```json
{ "setting_value": "true" }
```

### DELETE /api/v1/fr/frameworks/{framework_id}/settings/{key}
Delete a framework setting. Returns `204 No Content`.

---

## Framework Versions

### GET /api/v1/fr/frameworks/{framework_id}/versions
List versions for a framework ordered by created_at DESC.

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...", "framework_id": "...", "version_code": "2.0",
      "lifecycle_state": "published", "change_severity": "major",
      "control_count": 47, "previous_version_id": "..."
    }
  ],
  "total": 3
}
```

**Lifecycle states:** `draft` → `published` → `deprecated` → `archived`

### POST /api/v1/fr/frameworks/{framework_id}/versions
Create a new version (starts as draft).

**Request body**
```json
{
  "version_code": "2.0",
  "change_severity": "major",
  "release_notes": "Major restructuring of access control requirements",
  "change_summary": "Added 12 new controls, removed 3 deprecated"
}
```

### PATCH /api/v1/fr/frameworks/{framework_id}/versions/{version_id}
Update version (e.g., publish it).

**Request body**
```json
{ "lifecycle_state": "published" }
```

---

## Requirements

### GET /api/v1/fr/frameworks/{framework_id}/requirements
List requirements for a framework (hierarchical — use `parent_requirement_id` to build tree).

### POST /api/v1/fr/frameworks/{framework_id}/requirements
Create a requirement under a framework.

**Request body**
```json
{
  "requirement_code": "CC6",
  "name": "Logical and Physical Access Controls",
  "description": "...",
  "parent_requirement_id": null,
  "sort_order": 6
}
```

### PATCH /api/v1/fr/frameworks/{framework_id}/requirements/{requirement_id}
Update a requirement.

### DELETE /api/v1/fr/frameworks/{framework_id}/requirements/{requirement_id}
Soft-delete. Returns `204 No Content`.

---

## Controls

### GET /api/v1/fr/controls
Global cross-framework control list (all controls for tenant).

**Query params**
| Param | Type | Description |
|-------|------|-------------|
| search | string | Full-text search on name/description |
| framework_id | UUID | Filter to one framework |
| control_category_code | string | access_control, change_management, ... |
| criticality_code | string | critical, high, medium, low |
| control_type | string | preventive, detective, corrective, compensating |
| automation_potential | string | full, partial, manual |
| sort_by | string | name, control_code, sort_order, created_at, criticality_code |
| sort_dir | string | asc, desc |
| limit | int | 1–500 (default: 100) |
| offset | int | ≥0 (default: 0) |

### GET /api/v1/fr/frameworks/{framework_id}/controls
List controls scoped to a specific framework (same filter params as global).

### GET /api/v1/fr/frameworks/{framework_id}/controls/{control_id}
Get single control with all EAV properties.

**Response** `200 OK` — `ControlResponse`
```json
{
  "id": "...", "framework_id": "...", "control_code": "CC6.1",
  "control_category_code": "access_control", "criticality_code": "high",
  "control_type": "preventive", "automation_potential": "partial",
  "name": "Logical Access", "description": "...",
  "guidance": "...", "implementation_notes": "...",
  "test_count": 3
}
```

### POST /api/v1/fr/frameworks/{framework_id}/controls
Create a control.

**Request body**
```json
{
  "control_code": "CC6.1",
  "control_category_code": "access_control",
  "criticality_code": "high",
  "control_type": "preventive",
  "automation_potential": "partial",
  "requirement_id": null,
  "sort_order": 1,
  "name": "Logical Access Controls",
  "description": "...",
  "guidance": "...",
  "implementation_notes": "..."
}
```

### PATCH /api/v1/fr/frameworks/{framework_id}/controls/{control_id}
Update a control.

### DELETE /api/v1/fr/frameworks/{framework_id}/controls/{control_id}
Soft-delete. Returns `204 No Content`.

---

## Control Tests

### GET /api/v1/fr/tests
List all control tests for the tenant.

**Query params**
| Param | Type | Description |
|-------|------|-------------|
| search | string | Search on name/description |
| test_type_code | string | automated, manual, semi_automated |
| is_platform_managed | boolean | Platform-managed tests only |
| monitoring_frequency | string | realtime, hourly, daily, weekly, manual |
| sort_by | string | name, test_code, created_at, test_type_code |
| sort_dir | string | asc, desc |
| limit | int | 1–500 (default: 100) |
| offset | int | ≥0 (default: 0) |

### GET /api/v1/fr/tests/{test_id}
Get single test with EAV properties.

### POST /api/v1/fr/tests
Create a control test.

**Request body**
```json
{
  "test_code": "MFA-CHECK",
  "test_type_code": "automated",
  "monitoring_frequency": "daily",
  "integration_type": "aws_config",
  "is_platform_managed": true,
  "name": "MFA Enforcement Check",
  "description": "Verifies MFA is enabled for all IAM users",
  "evaluation_rule": "{\"type\":\"aws_config_rule\",\"rule\":\"mfa-enabled-for-iam-console-access\"}",
  "signal_type": "compliance_check",
  "integration_guide": "Configure AWS Config rule..."
}
```

### PATCH /api/v1/fr/tests/{test_id}
Update a test.

### DELETE /api/v1/fr/tests/{test_id}
Soft-delete. Returns `204 No Content`.

---

## Test–Control Mappings

### GET /api/v1/fr/tests/{test_id}/controls
List controls mapped to a test.

**Response** `200 OK`
```json
{
  "items": [
    { "id": "...", "control_test_id": "...", "control_id": "...", "is_primary": true, "sort_order": 0 }
  ],
  "total": 2
}
```

### POST /api/v1/fr/tests/{test_id}/controls
Add a control mapping.

**Request body**
```json
{ "control_id": "...", "is_primary": true, "sort_order": 0 }
```

### DELETE /api/v1/fr/tests/{test_id}/controls/{mapping_id}
Remove a control mapping. Returns `204 No Content`.

---

## Cross-Framework Equivalences

### GET /api/v1/fr/controls/{control_id}/equivalences
List equivalences where this control is the source.

### POST /api/v1/fr/controls/{control_id}/equivalences
Create an equivalence mapping.

**Request body**
```json
{
  "target_control_id": "...",
  "equivalence_type": "equivalent",
  "confidence": "high"
}
```

**equivalence_type:** `equivalent`, `partial`, `related`
**confidence:** `high`, `medium`, `low`

### DELETE /api/v1/fr/controls/{control_id}/equivalences/{equivalence_id}
Remove an equivalence. Returns `204 No Content`.

---

## Framework Approval Workflow

Frameworks go through an approval state machine before they become marketplace-visible.

**States:** `draft` → `pending_review` → `approved` | `rejected` → (re-submit from `rejected`)

### POST /api/v1/fr/frameworks/{framework_id}/submit
Submit a draft or rejected framework for admin review. Transitions to `pending_review`.

**Permission required:** `frameworks.update`

**Response** `200 OK` — `FrameworkResponse`

### POST /api/v1/fr/frameworks/{framework_id}/approve
Approve a pending framework. Sets status to `approved` and `is_marketplace_visible = true`.

**Permission required:** `frameworks.update` (super admin)

**Response** `200 OK` — `FrameworkResponse`

### POST /api/v1/fr/frameworks/{framework_id}/reject
Reject a pending framework with optional reason.

**Query param:** `reason` (optional string)

**Permission required:** `frameworks.update` (super admin)

**Response** `200 OK` — `FrameworkResponse`

---

## Framework Versions — Lifecycle

### POST /api/v1/fr/frameworks/{framework_id}/versions
Create a new version. `version_code` is **auto-generated** as the next sequential integer (1, 2, 3...).

**Request body**
```json
{
  "source_version_id": "...",   // optional: copy controls from this version
  "change_severity": "major"    // minor | major | patch
}
```

### POST /api/v1/fr/frameworks/{framework_id}/versions/{version_id}/publish
Publish a draft version. Returns `200 OK` — `VersionResponse`.

### POST /api/v1/fr/frameworks/{framework_id}/versions/{version_id}/deprecate
Deprecate a published version. Returns `200 OK` — `VersionResponse`.

### POST /api/v1/fr/frameworks/{framework_id}/versions/{version_id}/restore
Create a new published version from a deprecated/archived source. Generates the next sequential version number.

**Response** `200 OK` — `VersionResponse`

---

## Test Executions

Track the results of control test runs.

### GET /api/v1/fr/test-executions
List test executions.

**Query params**
| Param | Type | Description |
|-------|------|-------------|
| control_test_id | UUID | Filter by test |
| control_id | UUID | Filter by control |
| result_status | string | pending, pass, fail, partial, not_applicable, error |
| limit | int | default 100 |
| offset | int | default 0 |

### GET /api/v1/fr/test-executions/{execution_id}
Get a single test execution.

### POST /api/v1/fr/test-executions
Create a test execution record.

**Request body**
```json
{
  "control_test_id": "...",
  "control_id": "...",           // optional: specific control being tested
  "result_status": "pass",       // pending | pass | fail | partial | not_applicable | error
  "execution_type": "manual",    // manual | automated | scheduled
  "notes": "All checks passed",
  "evidence_summary": "Screenshots attached",
  "score": 100                   // 0–100
}
```

### PATCH /api/v1/fr/test-executions/{execution_id}
Update a test execution (e.g., update result status).

---

## Framework Deployments (Marketplace)

Orgs install (deploy) approved marketplace frameworks to track which version they're on and receive update notifications.

**Table:** `05_grc_library.16_fct_framework_deployments`
**View:** `05_grc_library.44_vw_framework_deployments` — includes `has_update` flag (true when a newer published version exists)

### GET /api/v1/fr/deployments
List all active deployments for an org.

**Query params**
| Param | Type | Description |
|-------|------|-------------|
| org_id | UUID | **Required.** The org to list deployments for |
| has_update | boolean | Filter to only deployments with updates available |

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...", "org_id": "...", "framework_id": "...",
      "deployed_version_id": "...", "deployed_version_code": "2",
      "deployment_status": "active",
      "framework_name": "SOC 2", "publisher_name": "AICPA",
      "latest_version_code": "3", "has_update": true
    }
  ],
  "total": 5
}
```

### GET /api/v1/fr/deployments/{deployment_id}
Get a single deployment.

### POST /api/v1/fr/deployments
Install a framework for an org. Conflicts (already installed) return `409`.

**Query param:** `org_id` (required)

**Request body**
```json
{
  "framework_id": "...",
  "version_id": "...",       // published version to deploy
  "workspace_id": "..."      // optional: scope to a workspace
}
```

**Response** `201 Created` — `FrameworkDeploymentResponse`

### PATCH /api/v1/fr/deployments/{deployment_id}
Update a deployment (upgrade version or pause/resume).

**Request body** (all optional)
```json
{
  "version_id": "...",            // upgrade to this version
  "deployment_status": "paused"   // active | paused | removed
}
```

**Response** `200 OK` — `FrameworkDeploymentResponse`

### DELETE /api/v1/fr/deployments/{deployment_id}
Remove (uninstall) a deployment. Sets `deployment_status = 'removed'`. Returns `204 No Content`.

---

## Auto-Task Creation

The following cross-module behaviors trigger automatic task creation:

### On test–control mapping
When `POST /api/v1/fr/tests/{test_id}/controls` is called with `auto_create_evidence_task: true`, an `evidence_collection` task is automatically created linked to the control (`entity_type=control, entity_id=control_id`).

**Extra fields on CreateTestMappingRequest:**
```json
{
  "control_id": "...",
  "auto_create_evidence_task": true,
  "org_id": "...",
  "workspace_id": "..."
}
```

### On high/critical risk creation
When a risk is created with `risk_level_code` of `high` or `critical`, a `risk_mitigation` task is automatically created linked to the risk (`entity_type=risk, entity_id=risk_id`). Priority is set to `critical` or `high` to match.

No opt-in required — this happens automatically.
