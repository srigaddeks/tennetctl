# Sandbox Collection Runs API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Permissions:** `sandbox.execute`, `sandbox.view`
**Multi-tenant:** All endpoints require `org_id` as a query parameter.

---

## Overview

Collection runs represent discrete Steampipe-powered asset collection executions triggered against a connector instance. Each run discovers assets from the external system (e.g., GitHub org, Azure storage), stores them in the asset inventory, and records structured status/metrics for audit and observability.

**Collection chain:**
```
POST /connectors/{id}/collect
  → CollectionRunService.trigger_collection()
    → SteampipeSubstrate.collect_assets()
      → steampipe binary (subprocess, temp HCL credentials)
        → External API (GitHub, Azure, etc.)
          → 15_sandbox.55_fct_assets + 54_dtl_asset_properties
```

**Key behaviors:**
- Collection runs asynchronously in a background task; the `collect` endpoint returns `202 Accepted` immediately
- Only one active run per connector instance at a time (enforced at DB level)
- Credentials are decrypted from DB, written to a temp HCL file, and cleaned up after each run — never stored on disk persistently
- Assets are upserted (discovered/updated/deleted counts tracked on the run record)
- `duration_seconds` is computed from `started_at` / `completed_at`

---

## Architecture

- **Fact table:** `15_sandbox.25_fct_sandbox_runs` — one row per collection run
- **Assets:** `15_sandbox.55_fct_assets` + `15_sandbox.54_dtl_asset_properties` (EAV)
- **Steampipe substrate:** `backend/10_sandbox/19_steampipe/steampipe.py` — query execution via subprocess
- **Provider HCL:** generated per-run from decrypted credentials, cleaned up after execution
- **Steampipe binary:** resolved at `~/bin/steampipe` (install dir: `~/.steampipe`)

---

## Steampipe Integration

Collection uses [Steampipe](https://steampipe.io/) as the sole data collection mechanism — no custom provider drivers. Steampipe is called as a subprocess with a temporary install dir containing symlinked plugins and a generated HCL connection config.

### Supported Providers

| Provider Code | Steampipe Plugin | Asset Types Collected |
|--------------|------------------|-----------------------|
| `github` | `turbot/github` v1.7+ | `github_org`, `github_repo`, `github_org_member`, `github_workflow` |
| `azure_storage` | `turbot/azure` | `azure_storage_account`, `azure_blob_container` |

### GitHub Collection Queries

| Asset Type | Steampipe Table | Notes |
|-----------|----------------|-------|
| `github_org` | `github_my_organization` | 1 row (the authenticated org) |
| `github_repo` | `github_my_repository` | All repos (archived included) |
| `github_org_member` | `github_organization_member` | Requires `org_name` property |
| `github_workflow` | `github_workflow` | Filters to non-archived repos |

> `github_team` is currently omitted from the Steampipe collection query set because the installed GitHub plugin version errors on the `github_team` table. Team coverage can be reintroduced once that plugin path is stable.

**GitHub PAT requirements:** Classic Personal Access Token (not fine-grained). Required OAuth scopes: `read:org`, `repo`, `admin:org`, `read:user`. Fine-grained PATs do not support Steampipe's GraphQL-based queries.

### Credential Flow

1. Credentials retrieved from `41_dtl_connector_credentials` (AES-256-GCM encrypted)
2. Temp directory created with symlinks to `~/.steampipe/{plugins,internal,db}`
3. Provider HCL written to `<temp_dir>/config/<provider>.spc` with plaintext credentials
4. `steampipe query <sql> --install-dir <temp_dir> --output json` executed
5. Temp directory deleted after each query (success or failure)

---

## Endpoints Summary

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | POST | `/connectors/{id}/collect` | `sandbox.execute` | Trigger collection run |
| 2 | GET | `/collection-runs` | `sandbox.view` | List collection runs |
| 3 | GET | `/collection-runs/{run_id}` | `sandbox.view` | Get single run |
| 4 | POST | `/collection-runs/{run_id}/cancel` | `sandbox.execute` | Cancel in-progress run |

---

## POST /api/v1/sb/connectors/{connector_id}/collect

Trigger an immediate on-demand asset collection from the connector using Steampipe. Creates a run record immediately and executes collection asynchronously in a background task.

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
| `connector_instance_id` | UUID | Yes | Must match `connector_id` in path |
| `asset_types` | string[] | No | Filter to specific asset types (e.g., `["github_repo", "github_team"]`). Null = collect all types for this provider |

```json
{
  "connector_instance_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "asset_types": ["github_repo", "github_org_member"]
}
```

**Response** `202 Accepted`

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
- `status` transitions: `queued` → `running` → `succeeded` | `failed` | `cancelled`
- Steampipe binary must be installed at `~/bin/steampipe` or on `PATH`
- Connector must have credentials configured (`health_status` need not be `healthy`)
- Background task updates the run record atomically as each asset type completes

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.execute` or connector belongs to different org |
| `404` | Connector ID not found |
| `409` | Collection already in progress for this connector |
| `422` | `connector_instance_id` mismatch or malformed UUID |
| `500` | Steampipe binary not found, or unexpected server error |

---

## GET /api/v1/sb/collection-runs

List collection runs for an org, optionally filtered by connector or status.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `org_id` | UUID | Yes | — | Organization scope |
| `connector_id` | UUID | No | — | Filter to runs for a specific connector instance |
| `status` | string | No | — | Filter: `queued`, `running`, `succeeded`, `failed`, `cancelled` |
| `limit` | integer | No | `20` | 1–100 |
| `offset` | integer | No | `0` | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "a9b0c1d2-e3f4-5678-abcd-901234567890",
      "tenant_key": "kreesalis",
      "org_id": "11223344-5566-7788-99aa-bbccddeeff00",
      "connector_instance_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
      "status": "succeeded",
      "trigger_type": "manual",
      "started_at": "2026-03-17T10:00:05Z",
      "completed_at": "2026-03-17T10:04:52Z",
      "assets_discovered": 73,
      "assets_updated": 12,
      "assets_deleted": 0,
      "logs_ingested": 0,
      "error_message": null,
      "triggered_by": "user:abc12345-0000-0000-0000-000000000000",
      "created_at": "2026-03-17T10:00:00Z",
      "updated_at": "2026-03-17T10:04:52Z",
      "duration_seconds": 287
    },
    {
      "id": "b0c1d2e3-f4a5-6789-bcde-012345678901",
      "tenant_key": "kreesalis",
      "org_id": "11223344-5566-7788-99aa-bbccddeeff00",
      "connector_instance_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
      "status": "failed",
      "trigger_type": "manual",
      "started_at": "2026-03-16T09:30:00Z",
      "completed_at": "2026-03-16T09:30:45Z",
      "assets_discovered": 0,
      "assets_updated": 0,
      "assets_deleted": 0,
      "logs_ingested": 0,
      "error_message": "Authentication failed: token does not have required scopes",
      "triggered_by": "user:abc12345-0000-0000-0000-000000000000",
      "created_at": "2026-03-16T09:30:00Z",
      "updated_at": "2026-03-16T09:30:45Z",
      "duration_seconds": 45
    }
  ],
  "total": 8
}
```

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` |
| `422` | Malformed UUID |

---

## GET /api/v1/sb/collection-runs/{run_id}

Get a single collection run by ID.

**Permission:** `sandbox.view`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `run_id` | UUID | Collection run ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `200 OK` — Same schema as items in the list response.

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.view` or run belongs to different org |
| `404` | Run ID not found |
| `422` | Malformed UUID |

---

## POST /api/v1/sb/collection-runs/{run_id}/cancel

Cancel an in-progress or queued collection run. Has no effect if the run has already completed.

**Permission:** `sandbox.execute`

**Path params**

| Param | Type | Description |
|-------|------|-------------|
| `run_id` | UUID | Collection run ID |

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |

**Response** `200 OK` — Updated run record with `status: "cancelled"`.

**Error codes**

| Status | Condition |
|--------|-----------|
| `401` | Missing or expired JWT |
| `403` | JWT lacks `sandbox.execute` or run belongs to different org |
| `404` | Run ID not found |
| `422` | Malformed UUID |

---

## Run Status Reference

| Status | Description |
|--------|-------------|
| `queued` | Run created, background task not yet started |
| `running` | Steampipe queries executing |
| `succeeded` | All queries completed, assets upserted |
| `failed` | Terminal error (auth failure, binary not found, query error) |
| `cancelled` | Cancelled by user or system |

---

## Run Metrics Fields

| Field | Description |
|-------|-------------|
| `assets_discovered` | Total assets returned by Steampipe queries |
| `assets_updated` | Assets upserted (new or changed) in `55_fct_assets` |
| `assets_deleted` | Assets marked deleted (no longer returned by Steampipe) |
| `logs_ingested` | Reserved for ClickHouse live session log count (always 0 for collection runs) |
| `duration_seconds` | Computed: `(completed_at - started_at).total_seconds()`. Null if run is still active |

---

## DB Tables Reference

| Table | Schema | Purpose |
|-------|--------|---------|
| `25_fct_sandbox_runs` | `15_sandbox` | Collection run fact rows |
| `55_fct_assets` | `15_sandbox` | Asset inventory fact rows |
| `54_dtl_asset_properties` | `15_sandbox` | EAV properties per asset |
| `20_fct_connector_instances` | `15_sandbox` | Connector instances (org-scoped) |
| `41_dtl_connector_credentials` | `15_sandbox` | Encrypted credentials |

All collection trigger events are audited via the unified audit system (`40_aud_events`).

---

## Frontend Integration Notes

- Poll `GET /collection-runs?connector_id=...` every 5 seconds while any run has `status: queued | running`
- `CollectionHistoryPanel` component auto-refreshes for in-progress runs
- "View Assets" → `GET /assets?connector_instance_id=...` (asset inventory endpoints)
- "Send to Dataset" picker → `POST /datasets` with selected asset records from the run
- Route prefix on frontend: `/api/v1/sb/collection-runs` (via Next.js `/api/proxy`)
