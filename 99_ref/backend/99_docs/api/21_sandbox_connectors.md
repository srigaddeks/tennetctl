# Sandbox Connector Management API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Permissions:** `sandbox.view`, `sandbox.create`, `sandbox.execute`
**Multi-tenant:** All endpoints require `org_id` as a query parameter. `tenant_key` is derived from the authenticated user's active organization.

---

## Overview

Connector instances are the integration layer between kcontrol and external systems. Each instance stores the connection configuration and encrypted credentials for a specific tool (e.g., a particular GitHub org, an Azure storage account). Instances are **org-scoped** — they are not tied to individual workspaces. Multiple instances of the same connector type are supported (e.g., two separate GitHub orgs).

**Data collection chain:**
`Connector Instance → POST /collect → CollectionRun (Steampipe substrate) → Asset Inventory → Datasets → Signals → Threat Types → Policies → Actions`

**Collection engine:** All asset collection is performed via [Steampipe](https://steampipe.io/) — there are no custom provider drivers. Steampipe is called as a subprocess with a temporary HCL config generated from decrypted DB credentials. Credentials are never stored on disk persistently.

**New endpoints since initial release:**

- `GET /connectors/{id}/properties` — fetch EAV properties for form pre-population
- `PATCH /connectors/{id}/credentials` — returns `204 No Content` (was `200 OK`)
- `POST /connectors/{id}/collect` → returns `CollectionRunResponse` (was `CollectResponse`)
- Collection run history: `GET /collection-runs`, `GET /collection-runs/{id}`, `POST /collection-runs/{id}/cancel`

---

## Architecture

- **Fact table:** `15_sandbox.20_fct_connector_instances` — lean row with FK columns, health status, schedule
- **Properties:** `15_sandbox.40_dtl_connector_instance_properties` — EAV key-value pairs (name, description, base_url, region, project_id, org_name, repo_list, tags, notes)
- **Credentials:** `15_sandbox.41_dtl_connector_credentials` — encrypted at rest, never returned in any response
- **Dimension tables:** `15_sandbox.02_dim_connector_categories`, `15_sandbox.03_dim_connector_types`, `15_sandbox.11_dim_asset_versions`
- **Dataset templates:** `15_sandbox.07_dim_dataset_templates`, `15_sandbox.12_lnk_template_asset_versions`
- **Advisory locks** are used during credential updates to prevent concurrent overwrites

---

## Cache Behavior

| Cache Key | TTL | Populated By | Invalidated By |
|-----------|-----|--------------|----------------|
| `sb:connectors:{org_id}` | 5 min | GET /connectors | POST, PATCH, DELETE /connectors |
| `sb:connector:{id}` | 5 min | GET /connectors/{id} | PATCH, DELETE /connectors/{id} |
| `sb:dimensions:connector-categories` | 1 hour | GET /dimensions/connector-categories | (static) |
| `sb:dimensions:connector-types` | 1 hour | GET /dimensions/connector-types | (static) |
| `sb:dimensions:asset-versions` | 1 hour | GET /dimensions/asset-versions | (static) |

---

## Dimension Endpoints

Dimension endpoints are read-only reference data. No write operations are supported. All dimension endpoints require `sandbox.view`.

### GET /api/v1/sb/dimensions/connector-categories

Returns all connector category records ordered by `sort_order`.

**Permission:** `sandbox.view`

**Query params:** none

**Response** `200 OK`
```json
[
  {
    "code": "cloud_infrastructure",
    "name": "Cloud Infrastructure",
    "description": "Cloud platform and IaaS providers",
    "sort_order": 1
  },
  {
    "code": "identity_provider",
    "name": "Identity Provider",
    "description": "IAM and SSO systems (Okta, Azure AD, Google Workspace)",
    "sort_order": 2
  },
  {
    "code": "source_control",
    "name": "Source Control",
    "description": "Git repository hosting platforms",
    "sort_order": 3
  },
  {
    "code": "endpoint_security",
    "name": "Endpoint Security",
    "description": "EDR and device management platforms",
    "sort_order": 4
  },
  {
    "code": "siem",
    "name": "SIEM / Log Management",
    "description": "Security information and event management systems",
    "sort_order": 5
  }
]
```

**DB table:** `15_sandbox.02_dim_connector_categories`

---

### GET /api/v1/sb/dimensions/connector-types

Returns connector type records, optionally filtered by category.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `category_code` | string | No | Filter to a specific category (e.g., `cloud_infrastructure`) |

**Response** `200 OK`
```json
[
  {
    "code": "kubernetes",
    "name": "Kubernetes",
    "category_code": "cloud_infrastructure",
    "description": "Kubernetes cluster via kubeconfig or in-cluster service account",
    "logo_url": "https://assets.kcontrol.io/connectors/kubernetes.svg",
    "sort_order": 1
  },
  {
    "code": "aws",
    "name": "AWS",
    "category_code": "cloud_infrastructure",
    "description": "Amazon Web Services via IAM role or access key",
    "logo_url": "https://assets.kcontrol.io/connectors/aws.svg",
    "sort_order": 2
  },
  {
    "code": "gcp",
    "name": "Google Cloud",
    "category_code": "cloud_infrastructure",
    "description": "Google Cloud Platform via service account JSON",
    "logo_url": "https://assets.kcontrol.io/connectors/gcp.svg",
    "sort_order": 3
  },
  {
    "code": "okta",
    "name": "Okta",
    "category_code": "identity_provider",
    "description": "Okta Identity Platform via API token",
    "logo_url": "https://assets.kcontrol.io/connectors/okta.svg",
    "sort_order": 1
  },
  {
    "code": "github",
    "name": "GitHub",
    "category_code": "source_control",
    "description": "GitHub organization via GitHub App or personal access token",
    "logo_url": "https://assets.kcontrol.io/connectors/github.svg",
    "sort_order": 1
  }
]
```

**DB table:** `15_sandbox.03_dim_connector_types`

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | `category_code` provided but not recognized |

---

### GET /api/v1/sb/dimensions/asset-versions

Returns asset version records — the supported runtime versions for a connector type (e.g., Kubernetes 1.29, 1.30, 1.31).

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `connector_type_code` | string | No | Filter to a specific connector type (e.g., `kubernetes`) |

**Response** `200 OK`
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "connector_type_code": "kubernetes",
    "version_code": "1.31",
    "name": "Kubernetes 1.31",
    "is_active": true,
    "sort_order": 1
  },
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "connector_type_code": "kubernetes",
    "version_code": "1.30",
    "name": "Kubernetes 1.30",
    "is_active": true,
    "sort_order": 2
  },
  {
    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "connector_type_code": "kubernetes",
    "version_code": "1.29",
    "name": "Kubernetes 1.29 (EOL)",
    "is_active": false,
    "sort_order": 3
  }
]
```

**DB table:** `15_sandbox.11_dim_asset_versions`

---

### GET /api/v1/sb/dimensions/dataset-templates

Returns dataset template records for populating collection configurations. Filter by connector type and/or asset version to narrow results.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `connector_type_code` | string | No | Filter by connector type |
| `asset_version_code` | string | No | Filter by specific version (e.g., `1.31`) |

**Response** `200 OK`
```json
[
  {
    "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
    "template_code": "k8s-full-cluster",
    "connector_type_code": "kubernetes",
    "asset_version_code": "1.31",
    "name": "Full Cluster Snapshot",
    "description": "Complete K8s cluster state: pods, services, deployments, RBAC, network policies, PVCs",
    "schema_fingerprint": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
    "is_active": true
  },
  {
    "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
    "template_code": "k8s-rbac-only",
    "connector_type_code": "kubernetes",
    "asset_version_code": "1.31",
    "name": "RBAC Configuration Only",
    "description": "Cluster roles, role bindings, service accounts — no workload data",
    "schema_fingerprint": "sha256:b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3",
    "is_active": true
  }
]
```

**DB tables:** `15_sandbox.07_dim_dataset_templates`, `15_sandbox.12_lnk_template_asset_versions`

---

### GET /api/v1/sb/dimensions/recommended-libraries

Returns library codes recommended for a connector type. Used by the frontend to pre-populate library selection when creating signals.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `connector_type_code` | string | Yes | Connector type to get recommendations for |

**Response** `200 OK`
```json
[
  {
    "library_code": "k8s-rbac-helpers",
    "library_name": "K8s RBAC Helpers",
    "library_type_code": "signal_helper",
    "description": "Common functions for RBAC analysis in Kubernetes datasets",
    "version": "1.2.0"
  },
  {
    "library_code": "k8s-network-policy-utils",
    "library_name": "K8s Network Policy Utils",
    "library_type_code": "signal_helper",
    "description": "Utilities for evaluating Kubernetes NetworkPolicy configurations",
    "version": "1.0.3"
  }
]
```

---

### GET /api/v1/sb/dimensions/signal-statuses

Returns all signal status dimension records in lifecycle order.

**Response** `200 OK`
```json
[
  { "code": "draft",     "name": "Draft",     "description": "Initial authoring state",                     "sort_order": 1 },
  { "code": "testing",   "name": "Testing",   "description": "Golden tests running or pending review",      "sort_order": 2 },
  { "code": "validated", "name": "Validated", "description": "All golden tests pass",                       "sort_order": 3 },
  { "code": "promoted",  "name": "Promoted",  "description": "Active in production evaluations",            "sort_order": 4 },
  { "code": "archived",  "name": "Archived",  "description": "Retired — no longer in use",                 "sort_order": 5 }
]
```

---

### GET /api/v1/sb/dimensions/dataset-sources

Returns all dataset source dimension records.

**Response** `200 OK`
```json
[
  { "code": "manual_json",    "name": "Manual JSON",    "description": "Paste or upload raw JSON directly",               "sort_order": 1 },
  { "code": "manual_upload",  "name": "Manual Upload",  "description": "Upload a JSON file via multipart form",           "sort_order": 2 },
  { "code": "live_capture",   "name": "Live Capture",   "description": "Captured from a running connector",               "sort_order": 3 },
  { "code": "connector_pull", "name": "Connector Pull", "description": "On-demand pull from a configured connector",      "sort_order": 4 },
  { "code": "template",       "name": "Template",       "description": "Generated from a dataset template definition",    "sort_order": 5 },
  { "code": "composite",      "name": "Composite",      "description": "Template base with selective manual overrides",   "sort_order": 6 }
]
```

---

### GET /api/v1/sb/dimensions/execution-statuses

Returns all execution status codes used by dataset collection and signal/policy run tracking.

**Response** `200 OK`
```json
[
  { "code": "pending",     "name": "Pending",     "description": "Queued, not yet started",                "sort_order": 1 },
  { "code": "in_progress", "name": "In Progress", "description": "Actively running",                       "sort_order": 2 },
  { "code": "succeeded",   "name": "Succeeded",   "description": "Completed successfully",                 "sort_order": 3 },
  { "code": "failed",      "name": "Failed",      "description": "Completed with a terminal error",        "sort_order": 4 },
  { "code": "cancelled",   "name": "Cancelled",   "description": "Cancelled by user or system",            "sort_order": 5 },
  { "code": "timeout",     "name": "Timeout",     "description": "Exceeded maximum execution duration",    "sort_order": 6 }
]
```

---

### GET /api/v1/sb/dimensions/threat-severities

Returns all threat severity dimension records.

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

---

### GET /api/v1/sb/dimensions/policy-action-types

Returns all policy action type dimension records.

**Response** `200 OK`
```json
[
  { "code": "notification",    "name": "Notification",    "description": "Send alert via channel (Slack, email, webhook)",   "sort_order": 1 },
  { "code": "evidence_report", "name": "Evidence Report", "description": "Generate evidence or incident report",             "sort_order": 2 },
  { "code": "rca_agent",       "name": "RCA Agent",       "description": "Trigger automated root cause analysis agent",      "sort_order": 3 },
  { "code": "escalate",        "name": "Escalate",        "description": "Escalate to designated responder group",           "sort_order": 4 },
  { "code": "create_task",     "name": "Create Task",     "description": "Create a remediation task in task tracker",        "sort_order": 5 },
  { "code": "webhook",         "name": "Webhook",         "description": "Fire an outbound HTTP webhook to external system", "sort_order": 6 },
  { "code": "disable_access",  "name": "Disable Access",  "description": "Revoke user or session access automatically",      "sort_order": 7 },
  { "code": "quarantine",      "name": "Quarantine",      "description": "Isolate the affected resource from the network",   "sort_order": 8 }
]
```

---

### GET /api/v1/sb/dimensions/library-types

Returns all library type dimension records.

**Response** `200 OK`
```json
[
  { "code": "signal_helper",    "name": "Signal Helper",    "description": "Utility functions shared across multiple signals", "sort_order": 1 },
  { "code": "connector_driver", "name": "Connector Driver", "description": "Collection adapter for a connector type",          "sort_order": 2 },
  { "code": "schema_validator", "name": "Schema Validator", "description": "Dataset schema validation functions",              "sort_order": 3 }
]
```

---

## Connector Instance Endpoints

Connector instances are **org-scoped**. Multiple instances per connector type are supported (e.g., two AWS accounts, three Kubernetes clusters). All descriptive data is stored as EAV properties. Credentials are stored encrypted in a separate table and are **never returned** in any response.

### GET /api/v1/sb/connectors

List connector instances for the authenticated org. Returns a paginated list with basic metadata and EAV properties `name` and `description`.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `org_id` | UUID | Yes | — | Organization scope |
| `connector_type_code` | string | No | — | Filter by type (e.g., `kubernetes`, `aws`) |
| `category_code` | string | No | — | Filter by category (e.g., `cloud_infrastructure`) |
| `health_status` | string | No | — | Filter: `healthy`, `degraded`, `error`, `unchecked` |
| `is_active` | boolean | No | `true` | Include inactive instances when `false` |
| `sort_by` | string | No | `created_at` | `created_at`, `instance_code`, `health_status` |
| `sort_dir` | string | No | `desc` | `asc` or `desc` |
| `limit` | integer | No | `100` | 1–500 |
| `offset` | integer | No | `0` | >= 0 |

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
      "instance_code": "aws-prod-us-east",
      "connector_type_code": "aws",
      "category_code": "cloud_infrastructure",
      "asset_version_id": null,
      "collection_schedule": "0 */6 * * *",
      "health_status": "healthy",
      "last_tested_at": "2026-03-16T08:00:00Z",
      "is_active": true,
      "created_at": "2026-01-10T14:30:00Z",
      "updated_at": "2026-03-16T08:00:05Z",
      "name": "AWS Production — US East 1",
      "description": "Primary production AWS account in us-east-1",
      "tags": "production,aws,us-east-1"
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "instance_code": "k8s-prod-cluster",
      "connector_type_code": "kubernetes",
      "category_code": "cloud_infrastructure",
      "asset_version_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "collection_schedule": "0 2 * * *",
      "health_status": "healthy",
      "last_tested_at": "2026-03-15T22:00:00Z",
      "is_active": true,
      "created_at": "2026-01-15T09:00:00Z",
      "updated_at": "2026-03-15T22:00:03Z",
      "name": "Production Kubernetes Cluster",
      "description": "EKS 1.31 — production workloads",
      "tags": "production,kubernetes,eks"
    }
  ],
  "total": 5
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Invalid filter value (unknown `health_status`, negative `limit`) |
| `401` | Missing or expired JWT |
| `403` | JWT present but lacks `sandbox.view` permission |
| `422` | Malformed UUID in filter params |
| `500` | Unexpected server error |

---

### GET /api/v1/sb/connectors/{connector_id}

Get a single connector instance with all EAV properties. Credentials are **never** included in any response.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `connector_id` | UUID | Connector instance ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `200 OK`
```json
{
  "id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "instance_code": "aws-prod-us-east",
  "connector_type_code": "aws",
  "category_code": "cloud_infrastructure",
  "asset_version_id": null,
  "collection_schedule": "0 */6 * * *",
  "health_status": "healthy",
  "last_tested_at": "2026-03-16T08:00:00Z",
  "is_active": true,
  "created_at": "2026-01-10T14:30:00Z",
  "updated_at": "2026-03-16T08:00:05Z",
  "name": "AWS Production — US East 1",
  "description": "Primary production AWS account in us-east-1",
  "base_url": "https://us-east-1.console.aws.amazon.com",
  "region": "us-east-1",
  "project_id": "123456789012",
  "org_name": null,
  "repo_list": null,
  "tags": "production,aws,us-east-1",
  "notes": "Owned by platform-infra team. Rotate keys every 90 days."
}
```

**Notes on EAV properties:** `base_url`, `region`, `project_id`, `org_name`, `repo_list`, `tags`, and `notes` are populated from `40_dtl_connector_instance_properties`. Properties that have not been set are returned as `null`.

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or connector belongs to different org |
| `404` | Connector ID not found |
| `422` | `connector_id` is not a valid UUID |
| `500` | Unexpected server error |

---

### POST /api/v1/sb/connectors

Create a new connector instance including its descriptive properties and credentials. Credentials are encrypted at rest immediately after write; the plaintext is not stored.

**Permission:** `sandbox.create`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body**

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `instance_code` | string | Yes | Unique per org, 3–80 chars, `[a-z0-9-]` | Stable machine-readable identifier |
| `connector_type_code` | string | Yes | Must exist in `03_dim_connector_types` | Connector type |
| `asset_version_id` | UUID | No | Must exist in `11_dim_asset_versions` and match the connector type | Runtime version, null = type default |
| `collection_schedule` | string | No | Valid cron expression | Automated collection schedule (UTC) |
| `properties` | object | No | — | EAV properties: `name`, `description`, `base_url`, `region`, `project_id`, `org_name`, `repo_list`, `tags`, `notes` |
| `credentials` | object | No | Key-value pairs of credential fields | Encrypted at rest, type-specific fields |

```json
{
  "instance_code": "aws-prod-us-east",
  "connector_type_code": "aws",
  "asset_version_id": null,
  "collection_schedule": "0 */6 * * *",
  "properties": {
    "name": "AWS Production — US East 1",
    "description": "Primary production AWS account in us-east-1",
    "base_url": "https://us-east-1.console.aws.amazon.com",
    "region": "us-east-1",
    "project_id": "123456789012",
    "tags": "production,aws,us-east-1",
    "notes": "IAM role assumed via STS. Minimum read-only permissions."
  },
  "credentials": {
    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "assume_role_arn": "arn:aws:iam::123456789012:role/KControlReadOnly"
  }
}
```

**Response** `201 Created`

Returns the full connector instance object (same schema as GET detail). Credentials are **not** included in the response.

```json
{
  "id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "instance_code": "aws-prod-us-east",
  "connector_type_code": "aws",
  "category_code": "cloud_infrastructure",
  "asset_version_id": null,
  "collection_schedule": "0 */6 * * *",
  "health_status": "unchecked",
  "last_tested_at": null,
  "is_active": true,
  "created_at": "2026-03-16T10:00:00Z",
  "updated_at": "2026-03-16T10:00:00Z",
  "name": "AWS Production — US East 1",
  "description": "Primary production AWS account in us-east-1",
  "base_url": "https://us-east-1.console.aws.amazon.com",
  "region": "us-east-1",
  "project_id": "123456789012",
  "org_name": null,
  "repo_list": null,
  "tags": "production,aws,us-east-1",
  "notes": "IAM role assumed via STS. Minimum read-only permissions."
}
```

**Business rules:**
- `health_status` is set to `unchecked` on creation; use POST `.../test` to update it
- `instance_code` must be unique within the org
- Unknown property keys in `properties` are silently ignored
- Credentials are optional at creation time; add them later via PATCH `.../credentials`

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Invalid `collection_schedule` cron expression |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` |
| `404` | `asset_version_id` not found or does not match the connector type |
| `409` | `instance_code` already exists within this org |
| `422` | `connector_type_code` is unknown, missing required fields, or malformed UUID |
| `429` | Rate limit exceeded |
| `500` | Unexpected server error |

---

### PATCH /api/v1/sb/connectors/{connector_id}

Update connector instance metadata and/or EAV properties. Partial updates are supported — only supplied fields are changed. To clear a property, set it explicitly to `null`.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `connector_id` | UUID | Connector instance ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body** (all fields optional)

| Field | Type | Description |
|-------|------|-------------|
| `asset_version_id` | UUID or null | Update the runtime version reference |
| `collection_schedule` | string or null | New cron expression, null to disable scheduling |
| `is_active` | boolean | Enable or disable the instance |
| `properties` | object | Partial property update — supplied keys are upserted, omitted keys are unchanged |

```json
{
  "asset_version_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "collection_schedule": "0 */4 * * *",
  "is_active": true,
  "properties": {
    "name": "AWS Production — US East 1 (updated)",
    "notes": "Updated IAM role ARN after rotation."
  }
}
```

**Response** `200 OK` — Full updated connector instance object (same schema as GET detail)

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Invalid cron expression |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or connector belongs to different org |
| `404` | Connector ID not found |
| `422` | Malformed UUID or invalid field value |
| `500` | Unexpected server error |

---

### DELETE /api/v1/sb/connectors/{connector_id}

Soft-delete a connector instance. Sets `is_active = false` and `deleted_at` timestamp. Associated datasets, credentials, and collection history are preserved for audit purposes.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `connector_id` | UUID | Connector instance ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `204 No Content`

**Business rules:**
- Deleting a connector does not delete datasets that were collected from it; `connector_instance_id` on datasets is nullable
- Scheduled collection jobs for the instance are cancelled

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or connector belongs to different org |
| `404` | Connector ID not found |
| `409` | Connector is currently running a collection job; retry after job completes |
| `500` | Unexpected server error |

---

## Credentials

Credentials are stored encrypted in `15_sandbox.41_dtl_connector_credentials`. They are written once per credential key; existing keys are overwritten atomically using an advisory lock. Credentials are **never returned** in any API response.

### PATCH /api/v1/sb/connectors/{connector_id}/credentials

Update or replace credentials for a connector instance. Existing credential keys not present in the request body are **not** deleted — they are preserved. To fully replace all credentials, provide every required key. This endpoint uses an advisory lock to prevent concurrent overwrites.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `connector_id` | UUID | Connector instance ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body** — Key-value pairs of credential fields. Field names are connector-type specific.

Example (AWS):
```json
{
  "access_key_id": "AKIAIOSFODNN7EXAMPLE",
  "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "assume_role_arn": "arn:aws:iam::123456789012:role/KControlReadOnly"
}
```

Example (Kubernetes):
```json
{
  "kubeconfig": "apiVersion: v1\nclusters:\n- cluster:\n    server: https://k8s.example.com\n  name: prod\n..."
}
```

Example (Okta):
```json
{
  "api_token": "00abc123...",
  "org_url": "https://yourorg.okta.com"
}
```

**Response** `200 OK`
```json
{
  "message": "Credentials updated",
  "connector_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "updated_at": "2026-03-16T10:15:00Z"
}
```

**Business rules:**
- After a successful credential update, `health_status` is reset to `unchecked` to ensure the new credentials are verified before next use
- Plaintext credentials are never logged

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or connector belongs to different org |
| `404` | Connector ID not found |
| `422` | Empty credentials object |
| `500` | Encryption failure or DB error |

---

## Get Connector Properties

### GET /api/v1/sb/connectors/{connector_id}/properties

Return all EAV properties stored for a connector instance as a flat key-value map. Used by the Edit Connector dialog to pre-populate form fields before saving.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `connector_id` | UUID | Connector instance ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `200 OK`
```json
{
  "name": "Kreesalis GitHub Org",
  "description": "Primary GitHub organization connector",
  "org_name": "kreesalis",
  "token_type": "classic_pat",
  "tags": "github,production"
}
```

**Notes:**
- Credentials are **never** included in this response
- Properties not yet set are absent from the map
- Use alongside `GET /connectors/{id}` to pre-populate the Edit Connector dialog

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or connector belongs to different org |
| `404` | Connector ID not found |
| `422` | Malformed UUID |

---

## Test Connection

### POST /api/v1/sb/connectors/{connector_id}/test

Test connectivity to the connector's target system using its stored credentials. Executes a lightweight probe (e.g., list S3 buckets, GET `/api/v1` on Kubernetes). Updates `health_status` and `last_tested_at` on the instance.

**Permission:** `sandbox.execute`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `connector_id` | UUID | Connector instance ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body:** None required.

**Response** `200 OK`
```json
{
  "connector_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "health_status": "healthy",
  "tested_at": "2026-03-16T10:30:00Z",
  "latency_ms": 245,
  "message": "Successfully authenticated and listed 14 IAM policies",
  "checks": [
    { "name": "credentials_valid",   "status": "pass", "detail": "STS AssumeRole succeeded" },
    { "name": "permissions_sufficient", "status": "pass", "detail": "ReadOnlyAccess policy confirmed" },
    { "name": "network_reachable",    "status": "pass", "detail": "Latency 245ms" }
  ]
}
```

**Degraded example:**
```json
{
  "connector_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "health_status": "degraded",
  "tested_at": "2026-03-16T10:30:00Z",
  "latency_ms": 1820,
  "message": "Authentication succeeded but some permission checks failed",
  "checks": [
    { "name": "credentials_valid",      "status": "pass", "detail": "STS AssumeRole succeeded" },
    { "name": "permissions_sufficient", "status": "fail", "detail": "Missing ec2:DescribeInstances" },
    { "name": "network_reachable",      "status": "pass", "detail": "Latency 1820ms (elevated)" }
  ]
}
```

**Health status values:**

| Value | Description |
|-------|-------------|
| `healthy` | All connectivity checks pass |
| `degraded` | Authentication succeeded but some permissions are missing |
| `error` | Cannot connect or credentials invalid |
| `unchecked` | Test has never been run |

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.execute` or connector belongs to different org |
| `404` | Connector ID not found |
| `409` | Connector has no credentials configured |
| `500` | Probe execution failed unexpectedly |

---

## Trigger Data Collection

### POST /api/v1/sb/connectors/{connector_id}/collect

Trigger an immediate on-demand asset collection from the connector via Steampipe. Creates a `CollectionRun` record immediately and executes collection asynchronously in a background task. Returns `202 Accepted` with the run record.

**Permission:** `sandbox.execute`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `connector_id` | UUID | Connector instance ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connector_instance_id` | UUID | Yes | Must match `connector_id` path param |
| `asset_types` | string[] | No | Limit to specific asset types (e.g., `["github_repo"]`). Null = collect all types for the provider |

```json
{
  "connector_instance_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "asset_types": ["github_repo", "github_org_member"]
}
```

**Response** `202 Accepted` — `CollectionRunResponse`
```json
{
  "id": "a9b0c1d2-e3f4-5678-abcd-901234567890",
  "tenant_key": "kreesalis",
  "org_id": "11223344-5566-7788-99aa-bbccddeeff00",
  "connector_instance_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "status": "queued",
  "trigger_type": "manual",
  "started_at": null,
  "completed_at": null,
  "assets_discovered": 0,
  "assets_updated": 0,
  "assets_deleted": 0,
  "logs_ingested": 0,
  "error_message": null,
  "triggered_by": "user:abc12345-0000-0000-0000-000000000000",
  "created_at": "2026-03-17T10:00:00Z",
  "updated_at": "2026-03-17T10:00:00Z",
  "duration_seconds": null
}
```

**Business rules:**

- Only one active run per connector instance at a time; a second request while `status = running` returns `409`
- Run status transitions: `queued` → `running` → `succeeded` | `failed` | `cancelled`
- Credentials are decrypted from DB, written to a temp HCL file, used by Steampipe, then deleted — never persisted on disk
- Assets are upserted into `15_sandbox.55_fct_assets` + `54_dtl_asset_properties`
- Poll `GET /collection-runs?connector_id=...` to track progress

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.execute` or connector belongs to different org |
| `404` | Connector ID not found |
| `409` | A collection run is already active for this connector |
| `422` | `connector_instance_id` mismatch or malformed UUID |
| `500` | Steampipe binary not found or unexpected server error |

---

## Related Endpoints

- **Datasets:** `GET /api/v1/sb/datasets?connector_instance_id={id}` — list datasets produced by this connector
- **Signals:** `GET /api/v1/sb/signals?connector_type_code={type}` — list signals compatible with this connector type
- **Libraries:** `GET /api/v1/sb/dimensions/recommended-libraries?connector_type_code={type}` — get recommended helper libraries

## DB Tables Reference

| Table | Schema | Purpose |
|-------|--------|---------|
| `02_dim_connector_categories` | `15_sandbox` | Category dimension (cloud_infrastructure, identity_provider, etc.) |
| `03_dim_connector_types` | `15_sandbox` | Connector type dimension (kubernetes, aws, okta, github, etc.) |
| `11_dim_asset_versions` | `15_sandbox` | Runtime versions per connector type |
| `07_dim_dataset_templates` | `15_sandbox` | Collection template definitions |
| `12_lnk_template_asset_versions` | `15_sandbox` | Template-to-version compatibility mapping |
| `20_fct_connector_instances` | `15_sandbox` | Connector instance fact table |
| `40_dtl_connector_instance_properties` | `15_sandbox` | EAV properties for instances |
| `41_dtl_connector_credentials` | `15_sandbox` | Encrypted credential key-value pairs |

All mutations (create, update, delete, test, collect) are audited via the unified audit system (`40_aud_events` + `41_dtl_audit_event_properties`).
