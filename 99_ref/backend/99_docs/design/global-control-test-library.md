# Global Control Test Library — Phase 2 Design Spec

## Problem

Super admins build signals, threat types, and policies in the sandbox. These are org/workspace-scoped. End users who want to run compliance checks against their connectors must build everything from scratch. There's no way to share proven signal+threat+policy bundles across organizations.

## Goal

Allow super admins to **publish** complete control test bundles (signal + threat type + policy) to a **Global Control Test Library**. End users can **browse** by connector type, **pull** a bundle into their workspace, and it creates all the necessary entities (signal, threat type, policy) locally — ready to run.

## Scope

**In scope:** Publish signal bundles, browse, pull/deploy to workspace, provenance tracking.
**Built on:** Phase 1 Global Dataset Library (done).

---

## Architecture

### What Gets Published (Bundle)

A **Global Control Test** is a self-contained bundle:

```json
{
  "global_code": "github_branch_protection_check",
  "connector_type_code": "github",
  "name": "GitHub Branch Protection Check",
  "description": "Checks all repos have branch protection enabled with required reviews",
  "category": "access_control",
  "tags": "github, branch-protection, compliance",

  "signals": [
    {
      "signal_code": "gh_branch_protection_reviewers",
      "name": "Branch Protection Reviewers Check",
      "description": "Checks repos require at least 2 reviewers",
      "python_source": "def evaluate(dataset: dict) -> dict: ...",
      "connector_type_codes": ["github"],
      "timeout_ms": 5000,
      "max_memory_mb": 128
    }
  ],

  "threat_type": {
    "threat_code": "unprotected_branches",
    "name": "Unprotected Branch Threat",
    "severity_code": "high",
    "expression_tree": {"type": "signal", "signal_code": "gh_branch_protection_reviewers", "expected_result": "fail"},
    "description": "Branches without adequate protection"
  },

  "policy": {
    "policy_code": "enforce_branch_protection",
    "name": "Enforce Branch Protection Policy",
    "actions": [{"action_type": "alert", "config": {"severity": "high"}}],
    "cooldown_minutes": 60,
    "description": "Alert when branches lack protection"
  },

  "linked_dataset_code": "github_org_assets"
}
```

### Database Schema

```sql
-- 84_fct_global_control_tests — Versioned global control test bundles
CREATE TABLE IF NOT EXISTS "15_sandbox"."84_fct_global_control_tests" (
    id                   UUID          NOT NULL DEFAULT gen_random_uuid(),
    global_code          VARCHAR(100)  NOT NULL,
    connector_type_code  VARCHAR(50)   NOT NULL,
    version_number       INTEGER       NOT NULL DEFAULT 1,

    -- The full bundle as JSONB
    bundle               JSONB         NOT NULL DEFAULT '{}',

    -- Source tracking
    source_signal_id     UUID          NULL,
    source_policy_id     UUID          NULL,
    source_library_id    UUID          NULL,
    source_org_id        UUID          NULL,
    linked_dataset_code  VARCHAR(100)  NULL,    -- global dataset code this works with

    -- Metadata
    publish_status       VARCHAR(20)   NOT NULL DEFAULT 'published',
    is_featured          BOOLEAN       NOT NULL DEFAULT FALSE,
    download_count       INTEGER       NOT NULL DEFAULT 0,
    signal_count         INTEGER       NOT NULL DEFAULT 0,

    published_by         UUID          NULL,
    published_at         TIMESTAMPTZ   NULL,
    is_active            BOOLEAN       NOT NULL DEFAULT TRUE,
    is_deleted           BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_84_fct_global_control_tests          PRIMARY KEY (id),
    CONSTRAINT uq_84_fct_global_control_tests_version  UNIQUE (global_code, version_number),
    CONSTRAINT fk_84_fct_global_control_tests_type     FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code)
);

-- 85_dtl_global_control_test_properties — EAV
CREATE TABLE IF NOT EXISTS "15_sandbox"."85_dtl_global_control_test_properties" (
    id              UUID          NOT NULL DEFAULT gen_random_uuid(),
    test_id         UUID          NOT NULL,
    property_key    VARCHAR(100)  NOT NULL,
    property_value  TEXT          NOT NULL DEFAULT '',

    CONSTRAINT pk_85_dtl_props      PRIMARY KEY (id),
    CONSTRAINT uq_85_dtl_props      UNIQUE (test_id, property_key),
    CONSTRAINT fk_85_dtl_props_test FOREIGN KEY (test_id)
        REFERENCES "15_sandbox"."84_fct_global_control_tests" (id) ON DELETE CASCADE
);

-- 86_trx_global_control_test_pulls — Track deployments
CREATE TABLE IF NOT EXISTS "15_sandbox"."86_trx_global_control_test_pulls" (
    id                     UUID          NOT NULL DEFAULT gen_random_uuid(),
    global_test_id         UUID          NOT NULL,
    pulled_version         INTEGER       NOT NULL,
    target_org_id          UUID          NOT NULL,
    target_workspace_id    UUID          NULL,
    deploy_type            VARCHAR(20)   NOT NULL DEFAULT 'workspace',  -- 'workspace' | 'promoted'
    created_signal_ids     UUID[]        NULL,    -- signals created in target workspace
    created_threat_id      UUID          NULL,    -- threat type created
    created_policy_id      UUID          NULL,    -- policy created
    pulled_by              UUID          NOT NULL,
    pulled_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_86_trx_pulls        PRIMARY KEY (id),
    CONSTRAINT fk_86_trx_pulls_test   FOREIGN KEY (global_test_id)
        REFERENCES "15_sandbox"."84_fct_global_control_tests" (id)
);
```

### API Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/sb/global-tests/publish` | sandbox.promote | Publish signal/policy chain to global library |
| GET | `/api/v1/sb/global-tests` | JWT | List global control tests |
| GET | `/api/v1/sb/global-tests/{id}` | JWT | Get bundle detail |
| PATCH | `/api/v1/sb/global-tests/{id}` | sandbox.promote | Update metadata |
| POST | `/api/v1/sb/global-tests/{id}/deprecate` | sandbox.promote | Deprecate |
| POST | `/api/v1/sb/global-tests/{id}/deploy` | JWT | Deploy to workspace (creates signal+threat+policy) |
| GET | `/api/v1/sb/global-tests/stats` | JWT | Category/type counts |

### Publish Flow

```python
async def publish_control_test(signal_id, org_id, user_id, properties):
    # 1. Load signal + properties + connector types
    # 2. Load linked threat type (if any) + expression tree
    # 3. Load linked policy (if any) + actions
    # 4. Build bundle JSONB with full chain
    # 5. Extract connector_type from signal connector types
    # 6. Determine version (max + 1 for same global_code)
    # 7. Insert into 84_fct_global_control_tests
    # 8. Set properties (name, description, tags, category)
```

### Deploy Flow (Pull to Workspace)

```python
async def deploy_to_workspace(global_test_id, org_id, workspace_id, user_id):
    # 1. Load global test bundle
    # 2. For each signal in bundle:
    #    a. Create signal in 22_fct_signals with new UUID
    #    b. Copy all EAV properties to 45_dtl_signal_properties
    #    c. Link connector types in 50_lnk_signal_connector_types
    #    d. Set status to 'validated'
    # 3. If threat_type in bundle:
    #    a. Create threat type in 23_fct_threat_types
    #    b. Copy expression_tree (update signal_code refs to new codes if needed)
    #    c. Copy EAV properties
    # 4. If policy in bundle:
    #    a. Create policy in 24_fct_policies with threat_type_id
    #    b. Copy actions JSONB
    #    c. Copy EAV properties
    # 5. Record deployment in 86_trx_global_control_test_pulls
    # 6. Increment download_count
    # 7. Return created entity IDs
```

### Provenance

Each created entity gets an EAV property:
- `global_test_id` — UUID of the global test
- `global_test_code` — code of the global test
- `global_test_version` — version number
- `deploy_source` — 'global_library' or 'sandbox_direct'

This lets us trace where any signal/threat/policy came from.
