# Dataset Composition + Schema Drift Detection

**Priority:** P2 — needed for real-world datasets
**Status:** New endpoints
**Module:** `backend/10_sandbox/03_datasets/`
**Base path:** `/api/v1/sb`

---

## Overview

Datasets are composed by selecting which collected asset properties to include. Users pick assets from the inventory (e.g., "all postgres_role assets from this connector") and the system builds a structured JSON dataset. Schema drift detection alerts when collected data no longer matches the dataset structure (e.g., PostgreSQL version upgrade added new columns).

---

## Compose Dataset

### POST `/api/v1/sb/datasets/compose`

**Permission:** `sandbox.create`
**Query params:** `org_id` (required)

**Request:**

```json
{
  "name": "PG Production Roles + Activity",
  "description": "PostgreSQL roles and recent activity for dormant account checks",
  "workspace_id": "uuid or null",
  "sources": [
    {
      "source_type": "asset_properties",
      "connector_instance_id": "uuid",
      "asset_type_filter": "postgres_role"
    },
    {
      "source_type": "asset_properties",
      "connector_instance_id": "uuid",
      "asset_type_filter": "postgres_stat_activity"
    },
    {
      "source_type": "asset_snapshot",
      "snapshot_id": "uuid"
    }
  ]
}
```

**Source types:**

| Type | What it fetches |
|------|----------------|
| `asset_properties` | Current properties for all assets matching the filter. Filter by `connector_instance_id` + optional `asset_type_filter` or `asset_id`. |
| `asset_snapshot` | Properties from a specific historical snapshot (versioned, reproducible). |

**Response:** `201 Created`

```json
{
  "dataset_id": "uuid",
  "dataset_code": "pg_production_roles_activity_v1",
  "version_number": 1,
  "dataset_source_code": "composite",
  "schema_fingerprint": "sha256:a1b2c3...",
  "row_count": 1,
  "record_preview": {
    "postgres_roles": [
      {"rolname": "admin", "rolcanlogin": true, "rolsuper": true, "...": "..."}
    ],
    "postgres_stat_activity": [
      {"usename": "admin", "state": "active", "state_change": "2026-03-20T08:00:00Z"}
    ]
  }
}
```

**How composition works:**

1. For each source, fetch asset properties from `54_dtl_asset_properties`
2. Group by `asset_type_code` → each type becomes a top-level key in the dataset JSON
3. Within each type, collect all assets as array items
4. Compute `schema_fingerprint` = SHA-256 of sorted top-level keys + nested key structure
5. Store as single payload record in `43_dtl_dataset_payloads`

---

## Schema Drift Detection

### GET `/api/v1/sb/datasets/{id}/schema-drift`

**Permission:** `sandbox.view`

Compare the dataset's stored schema against what would be collected NOW from the same sources.

**Response:** `200 OK`

```json
{
  "dataset_id": "uuid",
  "has_drift": true,
  "original_fingerprint": "sha256:a1b2c3...",
  "current_fingerprint": "sha256:d4e5f6...",
  "changes": {
    "added_fields": [
      {"path": "postgres_roles[].rolbypassrls", "type": "boolean"}
    ],
    "removed_fields": [],
    "type_changes": [
      {"path": "postgres_roles[].rolvaliduntil", "was": "string", "now": "timestamp"}
    ]
  },
  "recommendation": "Dataset schema has changed. Create a new version to update signal specs."
}
```

**Use case:** PostgreSQL upgraded from v14 to v16, added `rolbypassrls` column. Drift detection catches this and recommends dataset refresh → signal spec update → signal regeneration.

---

## Files to Create/Modify

| File | Change |
|------|--------|
| `backend/10_sandbox/03_datasets/schemas.py` | Add `ComposeDatasetRequest`, `DatasetSourceRef`, `SchemaDriftResponse` |
| `backend/10_sandbox/03_datasets/service.py` | Add `compose_dataset()`, `check_schema_drift()` |
| `backend/10_sandbox/03_datasets/repository.py` | Add methods to fetch asset properties by connector/type/snapshot |
| `backend/10_sandbox/03_datasets/router.py` | Add `POST /datasets/compose`, `GET /datasets/{id}/schema-drift` |

---

## Verification

1. Collect PG assets → compose dataset selecting postgres_role + postgres_stat_activity → verify JSON structure
2. Verify schema_fingerprint computed correctly
3. Simulate schema change (add column to asset properties) → verify drift detected
4. Frontend: dataset compose dialog with connector/asset type picker
