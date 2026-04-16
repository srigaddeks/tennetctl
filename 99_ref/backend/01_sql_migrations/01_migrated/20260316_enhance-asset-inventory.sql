-- =============================================================================
-- Migration: 20260316_enhance-asset-inventory.sql
-- Description: Enhancements to asset inventory tables
--   1. Asset version tracking on assets and snapshots
--   2. Consecutive failures on connector instances for health degradation
--   3. auth_failed health status allowed on connector instances
--   4. collection_schedule allowed on connector instances (already exists, widen CHECK)
--   5. Provider current_api_version field
--   6. last_collected_at on assets (set after each run)
-- Date: 2026-03-16
-- =============================================================================


-- =============================================================================
-- SECTION 1: Asset version tracking
-- Assets record which API version produced them — prevents schema mismatch
-- when a provider updates its API (e.g. GitHub API 2022-11-28 → 2024-xx-xx).
-- =============================================================================

ALTER TABLE "15_sandbox"."33_fct_assets"
    ADD COLUMN IF NOT EXISTS asset_api_version VARCHAR(50) NULL;

ALTER TABLE "15_sandbox"."34_fct_asset_snapshots"
    ADD COLUMN IF NOT EXISTS asset_api_version VARCHAR(50) NULL;

COMMENT ON COLUMN "15_sandbox"."33_fct_assets".asset_api_version
    IS 'API/schema version used when this asset was last collected (e.g. "2022-11-28", "2023-01-01"). NULL = version-agnostic provider.';

COMMENT ON COLUMN "15_sandbox"."34_fct_asset_snapshots".asset_api_version
    IS 'API/schema version used when this snapshot was collected. Lets callers detect schema drift between snapshots.';


-- =============================================================================
-- SECTION 2: Provider current API version
-- Providers declare their current API version; drivers use this as default.
-- Individual connector instances can pin to a specific version via provider_version_code.
-- =============================================================================

ALTER TABLE "15_sandbox"."16_dim_provider_definitions"
    ADD COLUMN IF NOT EXISTS current_api_version VARCHAR(50) NULL;

COMMENT ON COLUMN "15_sandbox"."16_dim_provider_definitions".current_api_version
    IS 'Default API version used by the driver when no version is pinned on the connector instance.';

-- Seed current API versions for existing providers
UPDATE "15_sandbox"."16_dim_provider_definitions"
    SET current_api_version = '2022-11-28'
    WHERE code = 'github' AND current_api_version IS NULL;

UPDATE "15_sandbox"."16_dim_provider_definitions"
    SET current_api_version = '2023-01-01'
    WHERE code = 'azure_storage' AND current_api_version IS NULL;


-- =============================================================================
-- SECTION 3: Connector instance health enhancements
-- Add consecutive_failures for degradation tracking, and allow auth_failed
-- health status (missing from the original CHECK constraint).
-- =============================================================================

ALTER TABLE "15_sandbox"."20_fct_connector_instances"
    ADD COLUMN IF NOT EXISTS consecutive_failures INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS cooldown_until TIMESTAMPTZ NULL;

COMMENT ON COLUMN "15_sandbox"."20_fct_connector_instances".consecutive_failures
    IS 'Number of consecutive collection failures. Drives health_status transitions: 1=degraded, 3+=error.';

COMMENT ON COLUMN "15_sandbox"."20_fct_connector_instances".cooldown_until
    IS 'When set, the scheduler skips this connector until this timestamp (used after auth_failed).';

-- Widen the health_status CHECK constraint to include auth_failed
-- PostgreSQL requires DROP + re-ADD for CHECK constraints
ALTER TABLE "15_sandbox"."20_fct_connector_instances"
    DROP CONSTRAINT IF EXISTS ck_20_fct_connector_instances_health;

ALTER TABLE "15_sandbox"."20_fct_connector_instances"
    ADD CONSTRAINT ck_20_fct_connector_instances_health
    CHECK (health_status IN ('healthy', 'degraded', 'error', 'auth_failed', 'unchecked'));


-- =============================================================================
-- SECTION 4: last_collected_at on assets (set after each run)
-- Already exists in the CREATE migration — just ensure the column is present.
-- =============================================================================

-- (last_collected_at already defined in create migration — no-op guard)
ALTER TABLE "15_sandbox"."33_fct_assets"
    ADD COLUMN IF NOT EXISTS last_collected_at TIMESTAMPTZ NULL;


-- =============================================================================
-- SECTION 5: Update 66_vw_asset_detail to include asset_api_version
-- =============================================================================

DROP VIEW IF EXISTS "15_sandbox"."66_vw_asset_detail";
CREATE VIEW "15_sandbox"."66_vw_asset_detail" AS
SELECT
    a.id,
    a.tenant_key,
    a.org_id,
    a.workspace_id,
    a.connector_instance_id,
    a.provider_code,
    a.asset_type_code,
    a.asset_external_id,
    a.parent_asset_id,
    a.status_code,
    a.current_snapshot_id,
    a.last_collected_at,
    a.consecutive_misses,
    a.asset_api_version,
    a.created_by,
    a.created_at,
    a.updated_at,
    a.is_deleted,
    pd.name                 AS provider_name,
    pd.supports_steampipe,
    pd.supports_log_collection,
    pd.current_api_version  AS provider_current_api_version,
    at.name                 AS asset_type_name,
    s.name                  AS status_name
FROM "15_sandbox"."33_fct_assets" a
LEFT JOIN "15_sandbox"."16_dim_provider_definitions" pd ON pd.code = a.provider_code
LEFT JOIN "15_sandbox"."14_dim_asset_types"          at ON at.code = a.asset_type_code
LEFT JOIN "15_sandbox"."15_dim_asset_statuses"        s ON s.code = a.status_code
WHERE a.is_deleted = FALSE;


-- =============================================================================
-- SECTION 6: Index on cooldown_until for scheduler queries
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_20_fct_connector_cooldown
    ON "15_sandbox"."20_fct_connector_instances"(cooldown_until)
    WHERE cooldown_until IS NOT NULL AND is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_33_fct_assets_api_version
    ON "15_sandbox"."33_fct_assets"(provider_code, asset_api_version)
    WHERE is_deleted = FALSE;
