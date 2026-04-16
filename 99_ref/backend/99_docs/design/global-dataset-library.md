# Global Dataset Library — Design Spec

## Problem

Super admins build datasets in the sandbox (e.g. "GitHub Branch Protection Rules" for the `github` connector type). These datasets are currently org-scoped — they can't be reused across orgs or workspaces. End users who configure a GitHub connector in K-Control have no way to discover and use pre-built datasets; they must build everything from scratch.

## Goal

Allow super admins to **publish** sandbox datasets to a **Global Dataset Library**. End users can **browse** the library filtered by their connector type, **pull** a dataset template into their workspace, and use it to build signals and control tests.

## Scope

**In scope:** Dataset publish, browse, pull, versioning.
**Out of scope (future phases):** Global signal library, global control test library, global risk library.

---

## Architecture

### Data Flow

```
Super Admin (Sandbox)                    Global Dataset Library                End User (K-Control)
─────────────────────                    ──────────────────────                ────────────────────
Build dataset in sandbox  ──publish──►   Platform-scoped catalog   ◄──browse── Browse by connector type
  - name, description                      - connector_type_code               Pull into workspace
  - connector_type_code                    - json_schema                         - Creates local dataset
  - json_schema                            - sample_payload                      - Linked to their connector
  - sample_payload                         - collection_query                    - Ready for signal authoring
  - collection_query                       - version history
  - records (as sample)                    - download_count
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage | New `15_sandbox.80_fct_global_datasets` table | Follows existing fact+EAV pattern, avoids polluting org-scoped tables |
| Scoping | `tenant_key = '__platform__'` | Same pattern as platform-managed frameworks |
| Versioning | `(global_code, version_number)` unique | Matches existing dataset versioning pattern |
| Pull mechanism | Copy template metadata + schema, NOT data rows | User's own connector populates the data |
| Collection query | Optional SQL/config stored in properties | Tells the system how to populate from a connector |
| Permissions | `sandbox.promote` to publish, no permission needed to browse/pull | Aligns with existing promotion permissions |

---

## Database Schema

### New Tables

```sql
-- ═══════════════════════════════════════════════════════════════════════════════
-- GLOBAL DATASET LIBRARY (80-82) — Platform-scoped dataset templates
-- Published by super admins from sandbox, consumed by all orgs/workspaces.
-- ═══════════════════════════════════════════════════════════════════════════════

-- 80_fct_global_datasets — Lean fact table (versioned)
CREATE TABLE IF NOT EXISTS "15_sandbox"."80_fct_global_datasets" (
    id                   UUID          NOT NULL DEFAULT gen_random_uuid(),
    global_code          VARCHAR(100)  NOT NULL,           -- unique human-readable code
    connector_type_code  VARCHAR(50)   NOT NULL,           -- which connector type this is for
    version_number       INTEGER       NOT NULL DEFAULT 1, -- immutable per version
    source_dataset_id    UUID          NULL,               -- FK → 21_fct_datasets (original)
    source_org_id        UUID          NULL,               -- org that published it

    json_schema          JSONB         NOT NULL DEFAULT '{}',  -- expected record structure
    sample_payload       JSONB         NOT NULL DEFAULT '[]',  -- example records for preview
    record_count         INTEGER       NOT NULL DEFAULT 0,     -- count of sample records

    publish_status       VARCHAR(20)   NOT NULL DEFAULT 'published',  -- draft | published | deprecated
    is_featured          BOOLEAN       NOT NULL DEFAULT FALSE,
    download_count       INTEGER       NOT NULL DEFAULT 0,

    published_by         UUID          NULL,               -- user who published
    published_at         TIMESTAMPTZ   NULL,
    is_active            BOOLEAN       NOT NULL DEFAULT TRUE,
    is_deleted           BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_80_fct_global_datasets          PRIMARY KEY (id),
    CONSTRAINT uq_80_fct_global_datasets_version  UNIQUE (global_code, version_number),
    CONSTRAINT fk_80_fct_global_datasets_type     FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code)
);

CREATE INDEX IF NOT EXISTS idx_80_global_datasets_type
    ON "15_sandbox"."80_fct_global_datasets" (connector_type_code)
    WHERE is_active AND NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_80_global_datasets_status
    ON "15_sandbox"."80_fct_global_datasets" (publish_status)
    WHERE is_active AND NOT is_deleted;


-- 81_dtl_global_dataset_properties — EAV for descriptive fields
CREATE TABLE IF NOT EXISTS "15_sandbox"."81_dtl_global_dataset_properties" (
    id              UUID          NOT NULL DEFAULT gen_random_uuid(),
    dataset_id      UUID          NOT NULL,
    property_key    VARCHAR(100)  NOT NULL,
    property_value  TEXT          NOT NULL DEFAULT '',

    CONSTRAINT pk_81_dtl_global_dataset_properties      PRIMARY KEY (id),
    CONSTRAINT uq_81_dtl_global_dataset_properties      UNIQUE (dataset_id, property_key),
    CONSTRAINT fk_81_dtl_global_dataset_properties_ds   FOREIGN KEY (dataset_id)
        REFERENCES "15_sandbox"."80_fct_global_datasets" (id) ON DELETE CASCADE
);

-- Property keys:
--   name              — display name (e.g. "GitHub Branch Protection Rules")
--   description       — detailed description with usage guidance
--   tags              — comma-separated (e.g. "security,github,branch-protection")
--   collection_query  — SQL or config to populate from connector (optional)
--   category          — grouping (e.g. "access_control", "encryption", "compliance")
--   compatible_asset_types — JSON array of asset type codes this works with
--   changelog         — what changed in this version


-- 82_trx_global_dataset_pulls — Track who pulled what (for analytics + version pinning)
CREATE TABLE IF NOT EXISTS "15_sandbox"."82_trx_global_dataset_pulls" (
    id                    UUID          NOT NULL DEFAULT gen_random_uuid(),
    global_dataset_id     UUID          NOT NULL,
    pulled_version        INTEGER       NOT NULL,
    target_org_id         UUID          NOT NULL,
    target_workspace_id   UUID          NULL,
    target_dataset_id     UUID          NULL,     -- FK → 21_fct_datasets (the local copy)
    pulled_by             UUID          NOT NULL,
    pulled_at             TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_82_trx_global_dataset_pulls        PRIMARY KEY (id),
    CONSTRAINT fk_82_trx_global_dataset_pulls_gd     FOREIGN KEY (global_dataset_id)
        REFERENCES "15_sandbox"."80_fct_global_datasets" (id)
);

CREATE INDEX IF NOT EXISTS idx_82_pulls_org
    ON "15_sandbox"."82_trx_global_dataset_pulls" (target_org_id);

CREATE INDEX IF NOT EXISTS idx_82_pulls_global
    ON "15_sandbox"."82_trx_global_dataset_pulls" (global_dataset_id);
```

### Detail View

```sql
CREATE OR REPLACE VIEW "15_sandbox"."83_vw_global_dataset_detail" AS
SELECT
    gd.id,
    gd.global_code,
    gd.connector_type_code,
    ct.name                    AS connector_type_name,
    gd.version_number,
    gd.json_schema,
    gd.sample_payload,
    gd.record_count,
    gd.publish_status,
    gd.is_featured,
    gd.download_count,
    gd.published_by,
    gd.published_at,
    gd.is_active,
    gd.created_at,
    gd.updated_at,
    -- Flattened EAV properties
    MAX(CASE WHEN p.property_key = 'name'        THEN p.property_value END) AS name,
    MAX(CASE WHEN p.property_key = 'description'  THEN p.property_value END) AS description,
    MAX(CASE WHEN p.property_key = 'tags'          THEN p.property_value END) AS tags,
    MAX(CASE WHEN p.property_key = 'category'      THEN p.property_value END) AS category,
    MAX(CASE WHEN p.property_key = 'collection_query' THEN p.property_value END) AS collection_query,
    MAX(CASE WHEN p.property_key = 'compatible_asset_types' THEN p.property_value END) AS compatible_asset_types,
    MAX(CASE WHEN p.property_key = 'changelog'     THEN p.property_value END) AS changelog
FROM "15_sandbox"."80_fct_global_datasets" gd
LEFT JOIN "15_sandbox"."81_dtl_global_dataset_properties" p ON p.dataset_id = gd.id
LEFT JOIN "15_sandbox"."03_dim_connector_types" ct ON ct.code = gd.connector_type_code
WHERE NOT gd.is_deleted
GROUP BY gd.id, ct.name;
```

---

## Backend Module

### New Module: `backend/10_sandbox/22_global_datasets/`

```
22_global_datasets/
├── __init__.py
├── models.py          # GlobalDatasetRecord, GlobalDatasetPullRecord (frozen dataclasses)
├── schemas.py         # PublishGlobalDatasetRequest, GlobalDatasetResponse, PullDatasetRequest, etc.
├── repository.py      # SQL queries against 80/81/82 tables + 83 view
├── service.py         # GlobalDatasetService — publish, list, get, pull, deprecate
├── dependencies.py    # FastAPI dependency injection
└── router.py          # API routes at /api/v1/sb/global-datasets
```

### API Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/sb/global-datasets/publish` | `sandbox.promote` | Publish a sandbox dataset to global library |
| GET | `/api/v1/sb/global-datasets` | JWT only | List global datasets (filter by connector_type, category, search) |
| GET | `/api/v1/sb/global-datasets/{id}` | JWT only | Get global dataset detail + sample payload |
| GET | `/api/v1/sb/global-datasets/{id}/versions` | JWT only | List all versions of a global dataset |
| PATCH | `/api/v1/sb/global-datasets/{id}` | `sandbox.promote` | Update metadata (name, description, tags, featured) |
| POST | `/api/v1/sb/global-datasets/{id}/deprecate` | `sandbox.promote` | Mark as deprecated (still visible, flagged) |
| POST | `/api/v1/sb/global-datasets/{id}/pull` | JWT only | Pull into user's org/workspace as a local dataset |
| GET | `/api/v1/sb/global-datasets/stats` | JWT only | Category counts, connector type counts |

### Publish Flow (Super Admin)

```python
async def publish_dataset(
    source_dataset_id: str,     # existing sandbox dataset UUID
    global_code: str,           # e.g. "github_branch_protection"
    org_id: str,                # publishing org
    user_id: str,               # publishing user
    properties: dict,           # name, description, tags, category, collection_query
) -> GlobalDatasetRecord:
    # 1. Load source dataset + records from 21_fct_datasets / 43_dtl_dataset_records
    # 2. Extract json_schema from source dataset properties
    # 3. Extract connector_type_code from source dataset's connector_instance
    # 4. Build sample_payload from first N records (max 10, sanitized)
    # 5. Check if global_code already exists:
    #    - YES: create new version (version_number = max + 1)
    #    - NO: create version 1
    # 6. Insert into 80_fct_global_datasets + 81_dtl_global_dataset_properties
    # 7. Return GlobalDatasetRecord
```

### Pull Flow (End User)

```python
async def pull_dataset(
    global_dataset_id: str,     # which global dataset to pull
    org_id: str,                # target org
    workspace_id: str | None,   # target workspace (optional)
    connector_instance_id: str | None,  # link to user's connector (optional)
    user_id: str,
) -> DatasetRecord:
    # 1. Load global dataset from 80_fct_global_datasets
    # 2. Generate dataset_code: "{global_code}_v{version}" or let user customize
    # 3. Create local dataset in 21_fct_datasets:
    #    - org_id = target org
    #    - workspace_id = target workspace
    #    - connector_instance_id = user's connector (if provided)
    #    - dataset_source_code = 'global_library'
    #    - Copy json_schema, sample records as initial data
    # 4. Copy properties (name, description, tags) to 42_dtl_dataset_properties
    #    - Add property: global_dataset_id = source UUID
    #    - Add property: global_dataset_version = version number
    # 5. Record pull in 82_trx_global_dataset_pulls
    # 6. Increment download_count on 80_fct_global_datasets
    # 7. Return the new local DatasetRecord
```

---

## Frontend

### Admin Page: `/admin/dataset-library`

Super admin page to manage the global dataset library.

**Layout:**
- Stats bar: Total datasets, By connector type, Featured count
- Table/card list with search, filter by connector type, filter by category
- Each card shows: name, connector type icon, version, download count, tags
- Actions: Edit metadata, Deprecate, View versions

**Publish dialog** (accessed from sandbox datasets page):
- Select source dataset
- Set global_code (auto-generated from name)
- Set category, tags
- Preview json_schema and sample payload
- Publish button

### Sandbox Enhancement: Publish Button on Datasets Page

Add a "Publish to Library" button on each dataset card in `/sandbox/datasets`. Opens a dialog:
- Global code (auto-slugified from dataset name)
- Category dropdown (access_control, encryption, compliance, network, identity, custom)
- Tags input
- Preview of what will be published (schema + sample records)
- Publish / Update Version buttons

### K-Control Page: Dataset Library Browser

New section in `/assets` or new page `/datasets` accessible to end users:
- Filtered by connector types the user has configured
- Card grid showing available datasets with:
  - Name, description, connector type badge
  - Version, download count
  - "Pull" button → opens dialog:
    - Select target workspace
    - Select connector instance (pre-filtered to matching type)
    - Pull button
- After pull: redirects to the new local dataset in sandbox for signal authoring

---

## Schemas (Pydantic)

```python
# ── Request models ────────────────────────────────────────────────────────────

class PublishGlobalDatasetRequest(BaseModel):
    source_dataset_id: str
    global_code: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    properties: dict[str, str]  # name, description, tags, category, collection_query

class UpdateGlobalDatasetRequest(BaseModel):
    properties: dict[str, str] | None = None
    is_featured: bool | None = None

class PullGlobalDatasetRequest(BaseModel):
    org_id: str
    workspace_id: str | None = None
    connector_instance_id: str | None = None
    custom_dataset_code: str | None = None  # override auto-generated code

# ── Response models ───────────────────────────────────────────────────────────

class GlobalDatasetResponse(BaseModel):
    id: str
    global_code: str
    connector_type_code: str
    connector_type_name: str | None = None
    version_number: int
    json_schema: dict
    sample_payload: list[dict]
    record_count: int
    publish_status: str
    is_featured: bool
    download_count: int
    published_by: str | None = None
    published_at: str | None = None
    created_at: str
    updated_at: str
    # Flattened EAV
    name: str | None = None
    description: str | None = None
    tags: str | None = None
    category: str | None = None
    collection_query: str | None = None
    compatible_asset_types: str | None = None
    changelog: str | None = None

class GlobalDatasetListResponse(BaseModel):
    items: list[GlobalDatasetResponse]
    total: int

class GlobalDatasetVersionResponse(BaseModel):
    version_number: int
    publish_status: str
    record_count: int
    published_at: str | None = None
    changelog: str | None = None

class GlobalDatasetStatsResponse(BaseModel):
    total: int
    by_connector_type: dict[str, int]
    by_category: dict[str, int]
    featured_count: int

class PullResultResponse(BaseModel):
    local_dataset_id: str
    dataset_code: str
    version_number: int
    global_source_code: str
    global_source_version: int
```

---

## Dataset Source Codes

Add new value to existing `05_dim_dataset_sources`:

```sql
INSERT INTO "15_sandbox"."05_dim_dataset_sources" (code, name, sort_order)
VALUES ('global_library', 'Global Library', 6)
ON CONFLICT (code) DO NOTHING;
```

---

## Cache Keys

| Key | TTL | Invalidated By |
|-----|-----|----------------|
| `sb:global_datasets:list` | 10 min | publish, update, deprecate |
| `sb:global_datasets:list:{connector_type}` | 10 min | publish, update, deprecate |
| `sb:global_datasets:{id}` | 10 min | update, deprecate |
| `sb:global_datasets:stats` | 10 min | publish, deprecate |

---

## Implementation Order

1. **Migration** — Create tables 80, 81, 82 + view 83 + seed `global_library` source code
2. **Backend module** — `22_global_datasets/` with models, schemas, repository, service, router
3. **Wire router** — Add to `backend/10_sandbox/router.py`
4. **Sandbox UI** — "Publish to Library" button on datasets page
5. **Admin UI** — `/admin/dataset-library` management page
6. **K-Control UI** — Dataset library browser (pull flow)
7. **Tests** — Robot Framework API tests for publish/list/pull

---

## Example: GitHub Branch Protection Dataset

**Published as:**
```json
{
  "global_code": "github_branch_protection",
  "connector_type_code": "github",
  "name": "GitHub Branch Protection Rules",
  "description": "Collects branch protection settings for all repos in a GitHub organization. Useful for compliance signals checking enforce-admins, required reviews, status checks.",
  "category": "access_control",
  "tags": "security,github,branch-protection,compliance",
  "json_schema": {
    "type": "object",
    "properties": {
      "repo_name": { "type": "string" },
      "branch": { "type": "string" },
      "enforce_admins": { "type": "boolean" },
      "required_pull_request_reviews": { "type": "integer" },
      "require_status_checks": { "type": "boolean" },
      "dismiss_stale_reviews": { "type": "boolean" }
    }
  },
  "sample_payload": [
    {
      "repo_name": "acme-api",
      "branch": "main",
      "enforce_admins": true,
      "required_pull_request_reviews": 2,
      "require_status_checks": true,
      "dismiss_stale_reviews": true
    }
  ],
  "collection_query": "SELECT repository_full_name, name, enforce_admins, required_pull_request_reviews, require_status_checks_before_merging, dismiss_stale_reviews FROM github_branch_protection"
}
```

**End user pulls it:**
1. Sees "GitHub Branch Protection Rules" in library (filtered because they have a GitHub connector)
2. Clicks Pull → selects workspace + connector
3. Local dataset created with `dataset_code = "github_branch_protection_v1"`
4. User can now run collection to populate with real data from their GitHub org
5. User creates a signal: `def evaluate(dataset): ...` checking `enforce_admins == True`
6. Promotes signal to control test → appears in their /tests page
