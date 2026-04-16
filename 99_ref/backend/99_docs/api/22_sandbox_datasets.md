# Sandbox Dataset Engine API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Permissions:** `sandbox.view`, `sandbox.create`
**Multi-tenant:** All endpoints require `org_id` as a query parameter. `tenant_key` is derived from the authenticated user's active organization.

---

## Overview

Datasets are the simulation inputs for the sandbox pipeline. A dataset is a structured JSON snapshot representing the state of an external system at a point in time (e.g., a Kubernetes cluster's full RBAC configuration, an AWS IAM inventory, an Okta user list). Signals run against datasets; policies fire based on what signals find.

**Dataset sources:**

| Source | How created | Typical use |
|--------|-------------|-------------|
| `manual_json` | Pasted directly in the UI | Quick one-off tests |
| `manual_upload` | JSON file upload | Importing exports from external tools |
| `live_capture` | Captured from a running connector | Real-time monitoring baselines |
| `connector_pull` | On-demand pull via POST /connectors/{id}/collect | Weekly snapshots, scheduled baselines |
| `template` | Generated from a dimension template | Synthetic reference datasets |
| `composite` | Template base with selective field overrides | What-if analysis, controlled variation |

**Storage split:** Dataset metadata and EAV properties live in PostgreSQL. JSON payloads are stored in `43_dtl_dataset_payloads` (also PostgreSQL, but fetched separately for performance). Live log data from connectors flows to ClickHouse and is not managed by this API.

**Versioning:** Each `dataset_code` within an org can have multiple versions. `version_number` auto-increments per code per org. Updating a dataset via PATCH creates a new version record rather than mutating the existing one. The latest version is always returned by default.

---

## Architecture

- **Fact table:** `15_sandbox.21_fct_datasets` — lean row with FK columns, lock status, version, schema fingerprint
- **Properties:** `15_sandbox.42_dtl_dataset_properties` — EAV key-value pairs (name, description, tags, notes)
- **Payloads:** `15_sandbox.43_dtl_dataset_payloads` — full JSON stored separately; fetched only on explicit request
- **Field overrides:** `15_sandbox.44_dtl_dataset_field_overrides` — per-field JSON path overrides for composite datasets
- **Dimension tables:** `15_sandbox.05_dim_dataset_sources`, `15_sandbox.07_dim_dataset_templates`, `15_sandbox.12_lnk_template_asset_versions`
- **Schema fingerprint:** SHA-256 hash of the sorted top-level JSON keys of the payload; used for schema drift detection

---

## Cache Behavior

| Cache Key | TTL | Populated By | Invalidated By |
|-----------|-----|--------------|----------------|
| `sb:datasets:{org_id}` | 5 min | GET /datasets | POST, PATCH, DELETE /datasets, POST /datasets/{id}/lock, POST /datasets/{id}/clone |
| `sb:dataset:{id}` | 5 min | GET /datasets/{id} | PATCH /datasets/{id}, POST /datasets/{id}/lock |
| `sb:dataset:{id}:payload` | 10 min | GET /datasets/{id}/payload | PATCH /datasets/{id} |
| `sb:dataset:{id}:fields` | 5 min | GET /datasets/{id}/fields | PATCH /datasets/{id}/fields |

---

## Dimension Endpoints

### GET /api/v1/sb/dimensions/dataset-sources

Returns all dataset source dimension records.

**Permission:** `sandbox.view`

**Response** `200 OK`

```json
[
  {
    "code": "manual_json",
    "name": "Manual JSON",
    "description": "Paste or upload raw JSON directly in the UI",
    "sort_order": 1
  },
  {
    "code": "manual_upload",
    "name": "Manual Upload",
    "description": "Upload a JSON file via multipart form",
    "sort_order": 2
  },
  {
    "code": "live_capture",
    "name": "Live Capture",
    "description": "Captured automatically from a running connector",
    "sort_order": 3
  },
  {
    "code": "connector_pull",
    "name": "Connector Pull",
    "description": "Pulled on-demand or on schedule from a configured connector",
    "sort_order": 4
  },
  {
    "code": "template",
    "name": "Template",
    "description": "Generated from a dataset template definition",
    "sort_order": 5
  },
  {
    "code": "composite",
    "name": "Composite",
    "description": "Template base with selective manual field overrides",
    "sort_order": 6
  }
]
```

**DB table:** `15_sandbox.05_dim_dataset_sources`

---

### GET /api/v1/sb/dimensions/dataset-templates

Returns dataset template dimension records, optionally filtered by connector type and/or asset version. Templates define the expected schema structure of a collected dataset.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `connector_type_code` | string | No | Filter by connector type (e.g., `kubernetes`, `aws`) |
| `asset_version_code` | string | No | Filter by version string (e.g., `1.31`, `2024.1`) |

**Response** `200 OK`

```json
[
  {
    "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
    "template_code": "k8s-full-cluster",
    "connector_type_code": "kubernetes",
    "asset_version_code": "1.31",
    "name": "Full Cluster Snapshot",
    "description": "Complete K8s cluster state: pods, services, deployments, RBAC, network policies, PVCs, config maps",
    "schema_fingerprint": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
    "is_active": true
  },
  {
    "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
    "template_code": "k8s-rbac-only",
    "connector_type_code": "kubernetes",
    "asset_version_code": "1.31",
    "name": "RBAC Configuration Only",
    "description": "Cluster roles, role bindings, and service accounts — no workload data",
    "schema_fingerprint": "sha256:b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3",
    "is_active": true
  },
  {
    "id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
    "template_code": "aws-iam-snapshot",
    "connector_type_code": "aws",
    "asset_version_code": null,
    "name": "AWS IAM Snapshot",
    "description": "IAM users, groups, roles, policies, and trust relationships",
    "schema_fingerprint": "sha256:c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4",
    "is_active": true
  }
]
```

**DB tables:** `15_sandbox.07_dim_dataset_templates`, `15_sandbox.12_lnk_template_asset_versions`

---

## Dataset Endpoints

### GET /api/v1/sb/datasets

List datasets for the authenticated tenant. Returns metadata and EAV properties `name`, `description`, `tags`. Does not include JSON payload — use `GET /datasets/{id}/payload` for that.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `org_id` | UUID | Yes | — | Organization scope |
| `workspace_id` | UUID | No | — | Filter to a specific workspace |
| `connector_instance_id` | UUID | No | — | Filter datasets produced by a specific connector |
| `dataset_source_code` | string | No | — | Filter by source: `manual_json`, `manual_upload`, `live_capture`, `connector_pull`, `template`, `composite` |
| `is_locked` | boolean | No | — | Filter locked (`true`) or unlocked (`false`) datasets |
| `search` | string | No | — | Substring match on `dataset_code` or `name` property |
| `sort_by` | string | No | `created_at` | `created_at`, `dataset_code`, `version_number` |
| `sort_dir` | string | No | `desc` | `asc` or `desc` |
| `limit` | integer | No | `100` | 1–500 |
| `offset` | integer | No | `0` | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "a9b0c1d2-e3f4-5678-abcd-901234567890",
      "dataset_code": "prod-cluster-2026-03",
      "version_number": 3,
      "dataset_source_code": "connector_pull",
      "connector_instance_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
      "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "template_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "schema_fingerprint": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "is_locked": true,
      "is_active": true,
      "created_at": "2026-03-16T02:00:00Z",
      "updated_at": "2026-03-16T02:05:00Z",
      "name": "Production Cluster — March 2026",
      "description": "Weekly RBAC snapshot from EKS production cluster",
      "tags": "production,kubernetes,rbac,weekly"
    },
    {
      "id": "b0c1d2e3-f4a5-6789-bcde-012345678901",
      "dataset_code": "what-if-admin-removal",
      "version_number": 1,
      "dataset_source_code": "composite",
      "connector_instance_id": null,
      "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "template_id": null,
      "schema_fingerprint": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "is_locked": false,
      "is_active": true,
      "created_at": "2026-03-16T10:30:00Z",
      "updated_at": "2026-03-16T10:30:00Z",
      "name": "What-If: Remove Admin ClusterRoleBinding",
      "description": "Simulate removing the cluster-admin binding and re-run RBAC signals",
      "tags": "what-if,rbac,analysis"
    }
  ],
  "total": 42
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Invalid `dataset_source_code` value |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` |
| `422` | Malformed UUID in filter params |
| `500` | Unexpected server error |

---

### GET /api/v1/sb/datasets/{dataset_id}

Get a single dataset with all metadata and EAV properties. Does **not** include the JSON payload body — use the `/payload` endpoint for that to avoid large response bodies in list-style UIs.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `dataset_id` | UUID | Dataset ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `200 OK`

```json
{
  "id": "a9b0c1d2-e3f4-5678-abcd-901234567890",
  "dataset_code": "prod-cluster-2026-03",
  "version_number": 3,
  "dataset_source_code": "connector_pull",
  "connector_instance_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "template_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "schema_fingerprint": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "is_locked": true,
  "is_active": true,
  "created_at": "2026-03-16T02:00:00Z",
  "updated_at": "2026-03-16T02:05:00Z",
  "name": "Production Cluster — March 2026",
  "description": "Weekly RBAC snapshot from EKS production cluster",
  "tags": "production,kubernetes,rbac,weekly",
  "notes": "Collected via scheduled pull. Locked after successful validation.",
  "field_override_count": 0
}
```

**Notes on EAV properties:** `name`, `description`, `tags`, and `notes` are loaded from `42_dtl_dataset_properties`. `field_override_count` is derived from the count of rows in `44_dtl_dataset_field_overrides` for this dataset.

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or dataset belongs to different org |
| `404` | Dataset ID not found |
| `422` | `dataset_id` is not a valid UUID |
| `500` | Unexpected server error |

---

### GET /api/v1/sb/datasets/{dataset_id}/payload

Retrieve the full JSON payload for a dataset. Stored separately in `43_dtl_dataset_payloads` for performance. For composite datasets, the returned payload is the effective merged result (base payload with field overrides applied).

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `dataset_id` | UUID | Dataset ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `raw` | boolean | No | If `true`, return the raw base payload without applying field overrides (composite datasets only) |

**Response** `200 OK`

```json
{
  "dataset_id": "a9b0c1d2-e3f4-5678-abcd-901234567890",
  "dataset_code": "prod-cluster-2026-03",
  "version_number": 3,
  "payload": {
    "cluster": {
      "name": "prod-eks-us-east-1",
      "version": "1.31.2",
      "node_count": 12,
      "region": "us-east-1"
    },
    "namespaces": ["default", "kube-system", "monitoring", "apps", "ingress"],
    "rbac": {
      "cluster_roles": [
        {
          "name": "cluster-admin",
          "rules": [{"apiGroups": ["*"], "resources": ["*"], "verbs": ["*"]}]
        }
      ],
      "cluster_role_bindings": [
        {
          "name": "cluster-admin-binding",
          "role_ref": "cluster-admin",
          "subjects": [{"kind": "User", "name": "sre-lead@example.com"}]
        }
      ],
      "service_accounts": [
        {"name": "default", "namespace": "default"},
        {"name": "kube-dns", "namespace": "kube-system"}
      ]
    },
    "pods": [
      {
        "name": "api-server-7d9f4b8c6-xkp2m",
        "namespace": "apps",
        "security_context": {"run_as_user": 1000, "run_as_non_root": true}
      }
    ]
  },
  "payload_size_bytes": 524288,
  "schema_fingerprint": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
}
```

**Business rules:**
- For `composite` datasets, the payload is computed by taking the base dataset payload and applying all field overrides in order
- Pass `raw=true` to retrieve the unmerged base payload for composite datasets
- Payloads can be very large (up to several MB for full cluster snapshots); clients should handle streaming

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or dataset belongs to different org |
| `404` | Dataset ID not found or payload not yet available (collection in progress) |
| `422` | `dataset_id` is not a valid UUID |
| `500` | Payload decompression or merge error |

---

### POST /api/v1/sb/datasets

Create a new dataset. The `dataset_source_code` determines the creation flow and which additional fields are required.

**Permission:** `sandbox.create`

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body — common fields**

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `dataset_code` | string | Yes | Unique per org, 3–80 chars, `[a-z0-9-]` | Stable machine-readable identifier |
| `dataset_source_code` | string | Yes | Must be a valid source code | Source type (determines other required fields) |
| `workspace_id` | UUID | No | Must exist within org | Workspace assignment |
| `properties` | object | No | — | EAV properties: `name`, `description`, `tags`, `notes` |

**Additional fields by source:**

| Source | Extra required fields |
|--------|-----------------------|
| `manual_json` | `payload` (JSON object) |
| `manual_upload` | `payload` (JSON object parsed from uploaded file) |
| `live_capture` | `connector_instance_id` |
| `connector_pull` | `connector_instance_id`, optionally `template_id` |
| `template` | `template_id` |
| `composite` | `base_dataset_id`, optionally `field_overrides` |

**Example: manual_json**

```json
{
  "dataset_code": "test-rbac-wildcard",
  "dataset_source_code": "manual_json",
  "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "properties": {
    "name": "RBAC Wildcard Test Scenario",
    "description": "Manually crafted dataset with a wildcard ClusterRoleBinding for signal testing",
    "tags": "test,rbac,wildcard,manual"
  },
  "payload": {
    "cluster": {"name": "test-cluster", "version": "1.31.0"},
    "rbac": {
      "cluster_role_bindings": [
        {
          "name": "wildcard-admin",
          "role_ref": "cluster-admin",
          "subjects": [{"kind": "ServiceAccount", "name": "ci-runner", "namespace": "ci"}]
        }
      ]
    }
  }
}
```

**Example: connector_pull**

```json
{
  "dataset_code": "prod-cluster-snapshot",
  "dataset_source_code": "connector_pull",
  "connector_instance_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "template_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "properties": {
    "name": "Production Cluster — March 2026",
    "tags": "production,kubernetes,snapshot"
  }
}
```

**Example: composite**

```json
{
  "dataset_code": "what-if-admin-removal",
  "dataset_source_code": "composite",
  "base_dataset_id": "a9b0c1d2-e3f4-5678-abcd-901234567890",
  "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "properties": {
    "name": "What-If: Remove Admin ClusterRoleBinding",
    "description": "Test scenario: remove cluster-admin binding and verify RBAC signals pass"
  },
  "field_overrides": [
    {
      "json_path": "$.rbac.cluster_role_bindings[0].subjects",
      "override_value": "[]",
      "reason": "Simulating removal of wildcard admin binding"
    }
  ]
}
```

**Response** `201 Created` — Full dataset object (same schema as GET detail, payload not included)

```json
{
  "id": "b0c1d2e3-f4a5-6789-bcde-012345678901",
  "dataset_code": "what-if-admin-removal",
  "version_number": 1,
  "dataset_source_code": "composite",
  "connector_instance_id": null,
  "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "template_id": null,
  "schema_fingerprint": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "is_locked": false,
  "is_active": true,
  "created_at": "2026-03-16T10:30:00Z",
  "updated_at": "2026-03-16T10:30:00Z",
  "name": "What-If: Remove Admin ClusterRoleBinding",
  "description": "Test scenario: remove cluster-admin binding and verify RBAC signals pass",
  "tags": null,
  "notes": null,
  "field_override_count": 1
}
```

**Business rules:**
- `version_number` is set to 1 on creation
- `schema_fingerprint` is computed as SHA-256 of the sorted top-level JSON keys of the effective payload
- `is_locked` is `false` on creation unless `dataset_source_code` is `connector_pull` and collection completes synchronously
- For `composite` datasets, `base_dataset_id` must reference a locked dataset to ensure a stable base

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Payload is not valid JSON |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` |
| `404` | `workspace_id`, `connector_instance_id`, `template_id`, or `base_dataset_id` not found within org |
| `409` | `dataset_code` already exists within this org |
| `422` | Invalid `dataset_source_code`, required source-specific fields missing, or `base_dataset_id` references an unlocked dataset |
| `429` | Rate limit exceeded |
| `500` | Unexpected server error |

---

### PATCH /api/v1/sb/datasets/{dataset_id}

Update dataset metadata and/or payload. Creates a **new version** — `version_number` auto-increments. The previous version record is preserved in history. Fails with `409` if the dataset is locked.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `dataset_id` | UUID | Dataset ID (refers to the current latest version) |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body** (all fields optional)

| Field | Type | Description |
|-------|------|-------------|
| `properties` | object | Partial property update — provided keys are upserted, omitted keys are unchanged |
| `payload` | object | Replace the full payload; triggers `schema_fingerprint` recalculation |

```json
{
  "properties": {
    "name": "Production Cluster — March 2026 (rev 2)",
    "description": "Updated after adding two new service accounts to the snapshot",
    "tags": "production,kubernetes,rbac,weekly,rev2"
  },
  "payload": {
    "cluster": {"name": "prod-eks-us-east-1", "version": "1.31.2", "node_count": 12},
    "rbac": {
      "cluster_role_bindings": [],
      "service_accounts": [
        {"name": "default", "namespace": "default"},
        {"name": "kube-dns", "namespace": "kube-system"},
        {"name": "monitoring-agent", "namespace": "monitoring"},
        {"name": "log-shipper", "namespace": "monitoring"}
      ]
    }
  }
}
```

**Response** `200 OK` — Updated dataset object with incremented `version_number`

**Business rules:**
- If only `properties` are updated (no `payload`), the `schema_fingerprint` does not change
- Updating the payload on a `composite` dataset replaces the effective merged payload and clears all `field_overrides`
- `version_number` increments even for properties-only updates

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Payload is not valid JSON |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or dataset belongs to different org |
| `404` | Dataset ID not found |
| `409` | Dataset is locked — clone it first to make edits |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

### POST /api/v1/sb/datasets/{dataset_id}/lock

Lock a dataset to make it immutable. Locked datasets cannot be updated or deleted. They can be cloned. Locking is a one-way operation — there is no unlock endpoint; use clone instead.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `dataset_id` | UUID | Dataset ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body:** None required.

**Response** `200 OK`

```json
{
  "id": "a9b0c1d2-e3f4-5678-abcd-901234567890",
  "dataset_code": "prod-cluster-2026-03",
  "version_number": 3,
  "is_locked": true,
  "locked_at": "2026-03-16T11:00:00Z",
  "locked_by": "c1d2e3f4-a5b6-7890-cdef-123456789012"
}
```

**Business rules:**
- Signals that reference this dataset will always operate on the locked version, ensuring reproducible results
- Composite datasets whose `base_dataset_id` is this dataset remain valid and stable
- Locking is idempotent — locking an already-locked dataset returns `200` with `is_locked: true`

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or dataset belongs to different org |
| `404` | Dataset ID not found |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

### POST /api/v1/sb/datasets/{dataset_id}/clone

Clone a dataset to create an unlocked, editable copy. The clone starts at `version_number: 1` with a new `dataset_code`. The source dataset does not need to be locked to be cloned, but cloning is the primary workflow for editing locked datasets.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `dataset_id` | UUID | Source dataset ID to clone from |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body** (optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dataset_code` | string | No | Code for the cloned dataset; auto-generated as `{source_code}-copy` if omitted |
| `workspace_id` | UUID | No | Workspace for the clone; defaults to the source dataset's workspace |
| `properties` | object | No | Override properties on the clone; unspecified properties are copied from the source |

```json
{
  "dataset_code": "prod-cluster-2026-03-edit",
  "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "properties": {
    "name": "Production Cluster March 2026 — Edit Copy",
    "description": "Unlocked clone for adding new service account scenarios"
  }
}
```

**Response** `201 Created` — New dataset object

```json
{
  "id": "c1d2e3f4-a5b6-7890-cdef-123456789012",
  "dataset_code": "prod-cluster-2026-03-edit",
  "version_number": 1,
  "dataset_source_code": "manual_json",
  "connector_instance_id": null,
  "workspace_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
  "template_id": null,
  "schema_fingerprint": "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "is_locked": false,
  "is_active": true,
  "created_at": "2026-03-16T11:05:00Z",
  "updated_at": "2026-03-16T11:05:00Z",
  "name": "Production Cluster March 2026 — Edit Copy",
  "description": "Unlocked clone for adding new service account scenarios",
  "tags": "production,kubernetes,rbac,weekly",
  "notes": null,
  "field_override_count": 0
}
```

**Business rules:**
- The clone's `dataset_source_code` is set to `manual_json` regardless of the source's type, since the payload is now static
- `connector_instance_id` and `template_id` are not copied to the clone
- Field overrides from composite source datasets are flattened into the cloned payload; the clone is not composite

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or source dataset belongs to different org |
| `404` | Source dataset ID not found |
| `409` | Provided `dataset_code` already exists within this org |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

### PATCH /api/v1/sb/datasets/{dataset_id}/fields

Add, update, or replace field overrides on a composite dataset. Each override specifies a JSON path into the merged payload, a new value to substitute, and an optional reason. This enables targeted what-if analysis without touching the base dataset.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `dataset_id` | UUID | Dataset ID (must be `composite` source type and unlocked) |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Request body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `field_overrides` | array | Yes | Array of field override objects; replaces all existing overrides |
| `field_overrides[].json_path` | string | Yes | JSONPath expression (e.g., `$.rbac.cluster_role_bindings[0].subjects`) |
| `field_overrides[].override_value` | string | Yes | Replacement value as a JSON-serialized string |
| `field_overrides[].reason` | string | No | Human-readable explanation of the override |

```json
{
  "field_overrides": [
    {
      "json_path": "$.rbac.cluster_role_bindings[0].subjects",
      "override_value": "[]",
      "reason": "Simulate removal of all subjects from the cluster-admin binding"
    },
    {
      "json_path": "$.cluster.node_count",
      "override_value": "3",
      "reason": "Simulate a smaller cluster to test resource contention signals"
    },
    {
      "json_path": "$.rbac.service_accounts",
      "override_value": "[{\"name\": \"minimal-sa\", \"namespace\": \"default\"}]",
      "reason": "Reduce to a single service account to isolate signal behavior"
    }
  ]
}
```

**Response** `200 OK`

```json
{
  "dataset_id": "b0c1d2e3-f4a5-6789-bcde-012345678901",
  "dataset_code": "what-if-admin-removal",
  "field_override_count": 3,
  "overrides": [
    {
      "id": "d2e3f4a5-b6c7-8901-defa-234567890123",
      "json_path": "$.rbac.cluster_role_bindings[0].subjects",
      "override_value": "[]",
      "reason": "Simulate removal of all subjects from the cluster-admin binding",
      "created_at": "2026-03-16T11:10:00Z"
    },
    {
      "id": "e3f4a5b6-c7d8-9012-efab-345678901234",
      "json_path": "$.cluster.node_count",
      "override_value": "3",
      "reason": "Simulate a smaller cluster to test resource contention signals",
      "created_at": "2026-03-16T11:10:00Z"
    },
    {
      "id": "f4a5b6c7-d8e9-0123-fabc-456789012345",
      "json_path": "$.rbac.service_accounts",
      "override_value": "[{\"name\": \"minimal-sa\", \"namespace\": \"default\"}]",
      "reason": "Reduce to a single service account to isolate signal behavior",
      "created_at": "2026-03-16T11:10:00Z"
    }
  ]
}
```

**Business rules:**
- This endpoint **replaces all existing overrides** — it is not additive. To keep existing overrides, include them in the request alongside new ones
- `override_value` must be a valid JSON-serialized string (e.g., a JSON array must be a string like `"[...]"`, not a raw array)
- The effective merged payload (base + overrides) is recomputed on GET `/payload` at read time, not stored separately
- The `schema_fingerprint` is not updated when overrides change — it reflects the base payload schema only

**Error codes**

| Status | Condition |
|--------|-----------|
| `400` | Invalid `json_path` expression or `override_value` is not valid JSON |
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or dataset belongs to different org |
| `404` | Dataset ID not found |
| `409` | Dataset is locked or is not `composite` type |
| `422` | Malformed UUID or empty `field_overrides` array |
| `500` | Unexpected server error |

---

### DELETE /api/v1/sb/datasets/{dataset_id}

Soft-delete a dataset. Sets `is_active = false`. Fails if the dataset is locked.

**Permission:** `sandbox.create`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `dataset_id` | UUID | Dataset ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `204 No Content`

**Business rules:**
- Locked datasets cannot be deleted; unlock by cloning if removal is needed
- Composite datasets referencing this dataset as `base_dataset_id` will lose their base; the system will return `409` on delete if active composite datasets reference this one
- Signal run history referencing this dataset is preserved in ClickHouse for audit purposes

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.create` or dataset belongs to different org |
| `404` | Dataset ID not found |
| `409` | Dataset is locked, or is referenced as `base_dataset_id` by one or more active composite datasets |
| `422` | Malformed UUID |
| `500` | Unexpected server error |

---

## Related Endpoints

- **Connectors:** `POST /api/v1/sb/connectors/{id}/collect` — trigger collection, which creates a dataset automatically
- **Signals:** `POST /api/v1/sb/signals/{id}/validate` — run signal against a dataset
- **Signal run history:** `GET /api/v1/sb/signals/{id}/runs` — browse runs that reference a dataset

## DB Tables Reference

| Table | Schema | Purpose |
|-------|--------|---------|
| `05_dim_dataset_sources` | `15_sandbox` | Source dimension (manual_json, connector_pull, composite, etc.) |
| `07_dim_dataset_templates` | `15_sandbox` | Template definitions used for structured collection |
| `12_lnk_template_asset_versions` | `15_sandbox` | Template-to-version compatibility mapping |
| `21_fct_datasets` | `15_sandbox` | Dataset fact table (code, version, source FK, lock status, fingerprint) |
| `42_dtl_dataset_properties` | `15_sandbox` | EAV properties (name, description, tags, notes) |
| `43_dtl_dataset_payloads` | `15_sandbox` | Full JSON payloads stored separately for performance |
| `44_dtl_dataset_field_overrides` | `15_sandbox` | Per-field JSON path overrides for composite datasets |

All mutations are audited via the unified audit system (`40_aud_events` + `41_dtl_audit_event_properties`).
