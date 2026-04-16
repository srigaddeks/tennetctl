# Sandbox Control Test Libraries API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Multi-tenant:** `org_id` query parameter required on all endpoints

---

## Overview

Libraries are versioned bundles of policies grouped by asset type. They provide a reusable, publishable collection of security checks that can be shared across workspaces within an organisation. A library tracks its version history via `version_number` (auto-incremented on every PATCH), can be published org-wide, cloned for modification, and promoted to the GRC control test library.

### Library Structure

```text
Library: "AWS Security Baseline v2.1"
├── Policy: IAM MFA Enforcement      → Threat: mfa_disabled
├── Policy: Root Account Usage       → Threat: root_access_detected
├── Policy: Access Key Rotation      → Threat: stale_access_keys
├── Policy: S3 Public Access Block   → Threat: public_s3_bucket
└── ... (up to N policies, ordered by sort_order)
```

---

## DB Tables

| Table | Schema | Type | Description |
| --- | --- | --- | --- |
| `10_dim_library_types` | `15_sandbox` | Dimension | Library type codes: asset_security, compliance, operational, custom |
| `29_fct_libraries` | `15_sandbox` | Fact | Library records with library_code, version_number, is_published |
| `48_dtl_library_properties` | `15_sandbox` | Detail (EAV) | name, description, target_asset_type, compliance_frameworks, tags, owner, release_notes |
| `51_lnk_library_policies` | `15_sandbox` | Link | Policies assigned to a library with sort_order |
| `13_lnk_library_connector_types` | `15_sandbox` | Link | Maps libraries to connector types and optional asset version codes |
| `30_fct_promotions` | `15_sandbox` | Fact | Promotion lineage records (sandbox artifact → GRC control test) |

### Key columns — `29_fct_libraries`

| Column | Type | Description |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `tenant_key` | TEXT | Tenant isolation |
| `org_id` | UUID FK | Owning organisation |
| `workspace_id` | UUID FK | Owning workspace |
| `library_code` | TEXT | Stable identifier across versions; unique per tenant |
| `library_type_code` | TEXT FK → `10_dim_library_types` | asset_security / compliance / operational / custom |
| `version_number` | INT | Auto-incremented on each PATCH; starts at 1 |
| `is_published` | BOOL | Whether the library is published to the org |
| `is_deleted` | BOOL | Soft-delete flag |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

### EAV properties — `48_dtl_library_properties`

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | TEXT | yes | Human-readable library name |
| `description` | TEXT | no | Full description |
| `target_asset_type` | TEXT | no | Asset type this library targets (e.g. `aws`, `k8s`, `github`) |
| `compliance_frameworks` | TEXT | no | Comma-separated list (e.g. `SOC2, CIS AWS Benchmark 1.5`) |
| `tags` | TEXT | no | Comma-separated tags for search |
| `owner` | TEXT | no | Owning team or person |
| `release_notes` | TEXT | no | What changed in this version |

---

## Dimensions

### GET /api/v1/sb/dimensions/library-types

Returns all library type dimension records. No authentication required.

**Response** `200 OK`

```json
[
  { "code": "asset_security", "name": "Asset Security", "description": "Security checks for specific asset types", "sort_order": 1 },
  { "code": "compliance",     "name": "Compliance",     "description": "Regulatory compliance policy bundles",   "sort_order": 2 },
  { "code": "operational",    "name": "Operational",    "description": "Operational health and best practices", "sort_order": 3 },
  { "code": "custom",         "name": "Custom",         "description": "User-defined library type",             "sort_order": 4 }
]
```

---

### GET /api/v1/sb/dimensions/recommended-libraries

Returns libraries recommended for a given connector type and optional asset version, based on `13_lnk_library_connector_types` mappings. Only published libraries are returned.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |
| `connector_type_code` | string | yes | e.g. `aws`, `kubernetes`, `github` |
| `asset_version_code` | string | no | e.g. `1.31`, `2024` — filters by mapped version |

**Response** `200 OK`

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "library_code": "aws_security_baseline",
    "version_number": 3,
    "library_type_code": "asset_security",
    "is_published": true,
    "name": "AWS Security Baseline",
    "description": "Comprehensive security checks for AWS infrastructure aligned with CIS AWS Benchmark 1.5",
    "target_asset_type": "aws",
    "policy_count": 19,
    "compliance_frameworks": "SOC2, CIS AWS Benchmark 1.5",
    "tags": "aws, iam, s3, cloudtrail, security"
  },
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "library_code": "aws_compliance_fedramp",
    "version_number": 2,
    "library_type_code": "compliance",
    "is_published": true,
    "name": "AWS FedRAMP Moderate",
    "description": "FedRAMP Moderate control checks for AWS workloads",
    "target_asset_type": "aws",
    "policy_count": 34,
    "compliance_frameworks": "FedRAMP Moderate",
    "tags": "aws, fedramp, compliance"
  }
]
```

---

## Libraries

### GET /api/v1/sb/libraries

List libraries with optional filtering. Returns all non-deleted libraries in the tenant scope.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `workspace_id` | UUID | no | — | Filter by owning workspace |
| `library_type_code` | string | no | — | asset_security / compliance / operational / custom |
| `is_published` | boolean | no | — | `true` for published only, `false` for unpublished only |
| `connector_type_code` | string | no | — | Filter by linked connector type |
| `search` | string | no | — | Full-text search on name and description |
| `sort_by` | string | no | `created_at` | created_at / library_code / version_number |
| `sort_dir` | string | no | `desc` | asc / desc |
| `limit` | int | no | 100 | 1–500 |
| `offset` | int | no | 0 | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "library_code": "aws_security_baseline",
      "version_number": 3,
      "library_type_code": "asset_security",
      "is_published": true,
      "name": "AWS Security Baseline",
      "description": "Comprehensive security checks for AWS infrastructure",
      "target_asset_type": "aws",
      "tags": "aws, iam, s3, cloudtrail, security",
      "policy_count": 19,
      "created_at": "2026-03-10T08:00:00Z",
      "updated_at": "2026-03-15T12:00:00Z"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "library_code": "k8s_cis_benchmark",
      "version_number": 1,
      "library_type_code": "compliance",
      "is_published": false,
      "name": "Kubernetes CIS Benchmark 1.9",
      "description": "CIS Kubernetes Benchmark 1.9 control checks",
      "target_asset_type": "kubernetes",
      "tags": "k8s, cis, compliance",
      "policy_count": 7,
      "created_at": "2026-03-14T10:00:00Z",
      "updated_at": "2026-03-14T10:00:00Z"
    }
  ],
  "total": 12
}
```

---

### GET /api/v1/sb/libraries/{id}

Get full library detail including all bundled policies, EAV properties, and linked connector types.

**Permission:** `sandbox.view`

Path parameters:

| Param | Type | Description |
| --- | --- | --- |
| `id` | UUID | Library ID |

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "library_code": "aws_security_baseline",
  "version_number": 3,
  "library_type_code": "asset_security",
  "is_published": true,
  "name": "AWS Security Baseline",
  "description": "Comprehensive security checks for AWS infrastructure aligned with CIS AWS Benchmark 1.5",
  "target_asset_type": "aws",
  "compliance_frameworks": "SOC2, CIS AWS Benchmark 1.5",
  "tags": "aws, iam, s3, cloudtrail, security",
  "owner": "platform-security-team",
  "release_notes": "v3: Added S3 encryption checks and CloudTrail multi-region validation",
  "policies": [
    {
      "policy_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "policy_code": "iam_mfa_enforcement",
      "policy_name": "IAM MFA Enforcement",
      "sort_order": 1
    },
    {
      "policy_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "policy_code": "root_account_usage",
      "policy_name": "Root Account Usage Detection",
      "sort_order": 2
    },
    {
      "policy_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "policy_code": "access_key_rotation",
      "policy_name": "Access Key Rotation Check",
      "sort_order": 3
    },
    {
      "policy_id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
      "policy_code": "s3_public_access_block",
      "policy_name": "S3 Public Access Block",
      "sort_order": 4
    }
  ],
  "connector_types": [
    { "connector_type_code": "aws", "asset_version_code": "2024" }
  ],
  "created_at": "2026-03-10T08:00:00Z",
  "updated_at": "2026-03-15T12:00:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 401 | Missing or invalid Bearer token |
| 403 | Missing `sandbox.view` permission |
| 404 | Library not found or soft-deleted |

---

### POST /api/v1/sb/libraries

Create a new library. Initialises at `version_number = 1`, `is_published = false`.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `library_code` | string | yes | Unique per tenant; lowercase, underscores | Stable identifier across versions |
| `library_type_code` | string | yes | Must exist in `10_dim_library_types` | Library type |
| `workspace_id` | UUID | yes | Must exist within org | Owning workspace |
| `properties.name` | string | yes | max 200 chars | Display name |
| `properties.description` | string | no | max 2000 chars | Description |
| `properties.target_asset_type` | string | no | — | e.g. `aws`, `k8s`, `github` |
| `properties.compliance_frameworks` | string | no | — | Comma-separated framework names |
| `properties.tags` | string | no | — | Comma-separated tags |
| `properties.owner` | string | no | — | Owning team or person |

```json
{
  "library_code": "aws_security_baseline",
  "library_type_code": "asset_security",
  "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "properties": {
    "name": "AWS Security Baseline",
    "description": "Comprehensive security checks for AWS infrastructure",
    "target_asset_type": "aws",
    "compliance_frameworks": "SOC2, CIS AWS Benchmark 1.5",
    "tags": "aws, iam, s3, security",
    "owner": "platform-security-team"
  }
}
```

**Response** `201 Created` — full library object (same shape as `GET /libraries/{id}`, `policies: []`)

Error responses:

| Status | Description |
| --- | --- |
| 400 | Malformed request body |
| 401 | Missing or invalid Bearer token |
| 403 | Missing `sandbox.create` permission |
| 409 | `library_code` already exists in tenant |
| 422 | `library_type_code` not found |

---

### PATCH /api/v1/sb/libraries/{id}

Update a library. Any PATCH automatically increments `version_number`. All fields are optional.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body (all fields optional):

```json
{
  "library_type_code": "compliance",
  "properties": {
    "name": "AWS Security Baseline (Updated)",
    "release_notes": "v4: Updated IAM checks to reflect 2026 CIS benchmarks; removed deprecated S3 ACL checks"
  }
}
```

**Response** `200 OK` — full library object with incremented `version_number`

Business rules: Only the properties included in the `properties` object are updated; omitted keys are left unchanged. `version_number` increments on every PATCH regardless of how many fields change. Published libraries can be patched; the `is_published` flag is not affected by PATCH.

Error responses:

| Status | Description |
| --- | --- |
| 403 | Missing `sandbox.create` permission |
| 404 | Library not found |

---

### DELETE /api/v1/sb/libraries/{id}

Soft-delete a library. Sets `is_deleted = true`. The library record is preserved for audit purposes.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `204 No Content`

Business rules: Published libraries cannot be deleted. Unpublish or clone first, then delete the clone. Deleting a library does not affect the policies bundled within it.

Error responses:

| Status | Description |
| --- | --- |
| 403 | Missing `sandbox.create` permission |
| 404 | Library not found |
| 409 | Library is published — must clone and delete the clone instead |

---

## Library Policies

### POST /api/v1/sb/libraries/{id}/policies

Add a policy to a library by inserting a row into `51_lnk_library_policies`. Policies from any workspace within the org can be bundled.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `policy_id` | UUID | yes | Policy to add |
| `sort_order` | int | yes | Display order within the library (1-based) |

```json
{
  "policy_id": "f6a7b8c9-d0e1-2345-fabc-678901234568",
  "sort_order": 5
}
```

**Response** `200 OK`

```json
{
  "library_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "policy_id": "f6a7b8c9-d0e1-2345-fabc-678901234568",
  "policy_code": "s3_encryption_check",
  "sort_order": 5,
  "added_at": "2026-03-16T10:00:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 404 | Library or policy not found |
| 409 | Policy already in this library |

---

### DELETE /api/v1/sb/libraries/{id}/policies/{policy_id}

Remove a policy from a library. Deletes the row from `51_lnk_library_policies`.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `204 No Content`

Error responses:

| Status | Description |
| --- | --- |
| 404 | Library not found or policy not attached |

---

## Library Actions

### POST /api/v1/sb/libraries/{id}/publish

Publish a library to the org. Sets `is_published = true`, making it visible and usable by all workspaces in the org. At least one policy must be bundled before publishing.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "library_code": "aws_security_baseline",
  "is_published": true,
  "version_number": 3,
  "published_at": "2026-03-16T10:00:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 404 | Library not found |
| 409 | Library is already published |
| 422 | Library has no policies — add at least one before publishing |

---

### POST /api/v1/sb/libraries/{id}/clone

Clone a library. Creates a new library with `version_number = 1`, `is_published = false`, copying all policies and EAV properties. The clone belongs to the specified workspace.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `library_code` | string | yes | New library code for the clone |
| `workspace_id` | UUID | yes | Target workspace for the clone |

```json
{
  "library_code": "aws_security_baseline_custom",
  "workspace_id": "d4e5f6a7-b8c9-0123-defa-234567890124"
}
```

**Response** `201 Created` — full library object of the new clone (same shape as `GET /libraries/{id}`)

Error responses:

| Status | Description |
| --- | --- |
| 404 | Source library not found |
| 409 | `library_code` already exists in tenant |

---

### POST /api/v1/sb/libraries/{id}/connector-types

Map a library to a connector type and optional asset version. Used to populate `GET /dimensions/recommended-libraries` results.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `connector_type_code` | string | yes | e.g. `aws`, `kubernetes`, `github` |
| `asset_version_code` | string | no | e.g. `2024`, `1.31` |

```json
{
  "connector_type_code": "aws",
  "asset_version_code": "2024"
}
```

**Response** `200 OK`

```json
{
  "library_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "connector_type_code": "aws",
  "asset_version_code": "2024",
  "mapped_at": "2026-03-16T10:00:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 404 | Library not found |
| 409 | Connector type mapping already exists |

---

## Promotions

Promotion pushes validated sandbox artifacts into the GRC control test library (`05_grc_library`). Each promotion creates a record in `30_fct_promotions` for lineage tracking.

### Promotion Field Mapping

| Sandbox Field | GRC Control Test Field |
| --- | --- |
| `signal.python_source` | `test.evaluation_rule` |
| `signal.signal_code` | `test.test_code` (prefixed `sb_`) |
| `connector_type_code` | `test.signal_type` |
| `source_prompt` | `test.integration_guide` |
| `collection_schedule` | `test.monitoring_frequency` |

---

### POST /api/v1/sb/signals/{signal_id}/promote

Promote a single signal to a GRC control test. Requires the signal to have at least one passing execution in its history.

**Permission:** `sandbox.promote`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `target_framework_id` | UUID | yes | GRC framework to attach the test to |
| `control_id` | UUID | yes | GRC control the test belongs to |
| `notes` | string | no | Promotion rationale or validation notes |

```json
{
  "target_framework_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "control_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "notes": "Validated against production AWS for 30 days with zero false positives"
}
```

**Response** `201 Created`

```json
{
  "promotion_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "source_type": "signal",
  "source_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "source_code": "iam_mfa_disabled_check",
  "source_version": 4,
  "target_type": "control_test",
  "target_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
  "target_test_code": "sb_iam_mfa_disabled_check",
  "target_framework_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "promoted_at": "2026-03-16T10:00:00Z",
  "promoted_by": "f6a7b8c9-d0e1-2345-fabc-678901234567"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 403 | Missing `sandbox.promote` permission |
| 404 | Signal, framework, or control not found |
| 422 | Signal has no passing execution history — must run and validate first |

---

### POST /api/v1/sb/policies/{policy_id}/promote

Promote a policy (and its linked signal) to a GRC control test.

**Permission:** `sandbox.promote`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields (same as signal promote):

```json
{
  "target_framework_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "control_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "notes": "Policy validated in staging environment for 14 days"
}
```

**Response** `201 Created` — same shape as signal promotion, with `source_type: "policy"`

---

### POST /api/v1/sb/libraries/{id}/promote

Promote an entire library to a GRC control test suite. Creates one `control_test` per policy in the library.

**Permission:** `sandbox.promote`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `target_framework_id` | UUID | yes | GRC framework to attach the test suite to |
| `notes` | string | no | Promotion rationale |

```json
{
  "target_framework_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "notes": "Full library promotion for SOC2 Type II compliance evidence"
}
```

**Response** `201 Created`

```json
{
  "promotion_id": "c3d4e5f6-a7b8-9012-cdef-123456789013",
  "source_type": "library",
  "source_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "source_code": "aws_security_baseline",
  "source_version": 3,
  "target_type": "control_test_suite",
  "target_framework_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tests_created": 19,
  "test_ids": [
    "e5f6a7b8-c9d0-1234-efab-567890123456",
    "f6a7b8c9-d0e1-2345-fabc-678901234567"
  ],
  "promoted_at": "2026-03-16T10:00:00Z",
  "promoted_by": "a1b2c3d4-e5f6-7890-abcd-ef1234567891"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 403 | Missing `sandbox.promote` permission |
| 404 | Library or framework not found |
| 422 | Library has no policies |
| 422 | One or more policies have unvalidated signals |

---

### GET /api/v1/sb/promotions

List promotion records.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `source_type` | string | no | — | signal / policy / library |
| `source_id` | UUID | no | — | Filter by specific source entity |
| `target_framework_id` | UUID | no | — | Filter by target GRC framework |
| `sort_by` | string | no | `promoted_at` | promoted_at |
| `sort_dir` | string | no | `desc` | asc / desc |
| `limit` | int | no | 50 | 1–100 |
| `offset` | int | no | 0 | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "promotion_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "source_type": "signal",
      "source_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "source_code": "iam_mfa_disabled_check",
      "source_version": 4,
      "target_type": "control_test",
      "target_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "target_framework_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "promoted_at": "2026-03-16T10:00:00Z",
      "promoted_by": "f6a7b8c9-d0e1-2345-fabc-678901234567",
      "notes": "Validated against production AWS for 30 days"
    }
  ],
  "total": 8
}
```

---

### GET /api/v1/sb/promotions/{id}

Get full promotion detail including the field mapping snapshot.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "promotion_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "source_type": "signal",
  "source_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "source_code": "iam_mfa_disabled_check",
  "source_version": 4,
  "target_type": "control_test",
  "target_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
  "target_test_code": "sb_iam_mfa_disabled_check",
  "target_framework_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "promoted_at": "2026-03-16T10:00:00Z",
  "promoted_by": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "notes": "Validated against production AWS for 30 days with zero false positives",
  "field_mapping": {
    "python_source": "evaluation_rule",
    "signal_code": "sb_iam_mfa_disabled_check",
    "connector_type_code": "signal_type",
    "source_prompt": "integration_guide",
    "collection_schedule": "monitoring_frequency"
  }
}
```

---

## Audit Events

All library mutations are written to the unified audit system (`40_aud_events` + `41_dtl_audit_event_properties`).

| Event Type | Entity | Key Properties |
| --- | --- | --- |
| `library_created` | `library` | library_code, library_type_code, workspace_id |
| `library_updated` | `library` | library_code, version_number |
| `library_deleted` | `library` | library_code |
| `library_published` | `library` | library_code, org_id |
| `library_cloned` | `library` | source_library_id, new_library_code, workspace_id |
| `library_policy_added` | `library` | library_id, policy_id, sort_order |
| `library_policy_removed` | `library` | library_id, policy_id |
| `library_connector_mapped` | `library` | library_id, connector_type_code, asset_version_code |
| `signal_promoted` | `promotion` | signal_id, source_version, target_test_id, target_framework_id |
| `policy_promoted` | `promotion` | policy_id, target_test_id, target_framework_id |
| `library_promoted` | `promotion` | library_id, source_version, tests_created, target_framework_id |

---

## Cross-References

| Related Resource | Endpoint |
| --- | --- |
| Policy management | `GET /api/v1/sb/policies/{id}` — see `24_sandbox_policies.md` |
| Signal management | `GET /api/v1/sb/signals/{id}` — see `22_sandbox_signals.md` |
| Connector type dimensions | `GET /api/v1/sb/dimensions/connector-types` — see `20_sandbox_connectors.md` |
| Execution history for validation | `GET /api/v1/sb/runs/history` — see `26_sandbox_execution.md` |
