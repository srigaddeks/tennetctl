-- =============================================================================
-- Migration: Fix framework catalog control_count and correct existing data
-- =============================================================================
-- Root causes fixed:
--
-- BUG 1 (backend): update_lifecycle_state() in versions/repository.py was
--   overwriting control_count with COUNT(*) of ALL framework controls, undoing
--   the selective snapshot count that update_version_control_count() had just
--   set correctly. Fixed in Python code: update_lifecycle_state no longer
--   touches control_count at all.
--
-- BUG 2 (view): 40_vw_framework_catalog was computing control_count from
--   13_fct_controls (all framework controls) instead of the published version's
--   stored control_count. Fixed below: view now reads v.control_count from
--   the latest published version row (which reflects the selective snapshot).
--
-- DATA FIX: Correct existing published version rows whose control_count was
--   corrupted by BUG 1. Recalculates from 31_lnk_framework_version_controls
--   (the actual snapshot link table) which was inserted correctly.
-- =============================================================================

-- Step 1: Correct existing corrupted control_count on published version rows.
-- Uses the actual link table count, which was always written correctly by
-- snapshot_controls_to_version().
UPDATE "05_grc_library"."11_fct_framework_versions" v
SET control_count = (
    SELECT COUNT(*)
    FROM "05_grc_library"."31_lnk_framework_version_controls" lnk
    WHERE lnk.framework_version_id = v.id
)
WHERE v.lifecycle_state = 'published'
  AND v.is_deleted = FALSE;

-- Step 2: Replace the catalog view so control_count is sourced from the
-- version's stored count (correct after Step 1 and correct for all future
-- approvals after the Python bug-fix).
CREATE OR REPLACE VIEW "05_grc_library"."40_vw_framework_catalog" AS
SELECT
    f.id,
    f.tenant_key,
    f.framework_code,
    f.framework_type_code,
    ft.name                         AS type_name,
    f.framework_category_code,
    fc.name                         AS category_name,
    f.scope_org_id,
    f.scope_workspace_id,
    f.approval_status,
    f.is_marketplace_visible,
    f.is_active,
    f.is_deleted,
    f.created_at,
    f.updated_at,
    f.created_by,
    -- EAV properties flattened
    p_name.property_value           AS name,
    p_desc.property_value           AS description,
    p_short.property_value          AS short_description,
    p_pub_type.property_value       AS publisher_type,
    p_pub_name.property_value       AS publisher_name,
    p_logo.property_value           AS logo_url,
    p_docs.property_value           AS documentation_url,
    -- Latest published version code
    (SELECT v.version_code
     FROM "05_grc_library"."11_fct_framework_versions" v
     WHERE v.framework_id = f.id
       AND v.lifecycle_state = 'published'
       AND v.is_deleted = FALSE
     ORDER BY v.created_at DESC
     LIMIT 1)                       AS latest_version_code,
    -- control_count: use the published version's stored count (reflects
    -- selective snapshots). Fall back to raw control count for frameworks
    -- that have never been published yet.
    COALESCE(
        (SELECT v.control_count
         FROM "05_grc_library"."11_fct_framework_versions" v
         WHERE v.framework_id = f.id
           AND v.lifecycle_state = 'published'
           AND v.is_deleted = FALSE
         ORDER BY v.created_at DESC
         LIMIT 1),
        (SELECT COUNT(*)
         FROM "05_grc_library"."13_fct_controls" c
         WHERE c.framework_id = f.id
           AND c.is_deleted = FALSE)
    )                               AS control_count
FROM "05_grc_library"."10_fct_frameworks" f
LEFT JOIN "05_grc_library"."02_dim_framework_types" ft
    ON ft.code = f.framework_type_code
LEFT JOIN "05_grc_library"."03_dim_framework_categories" fc
    ON fc.code = f.framework_category_code
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
    ON p_name.framework_id = f.id AND p_name.property_key = 'name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_desc
    ON p_desc.framework_id = f.id AND p_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_short
    ON p_short.framework_id = f.id AND p_short.property_key = 'short_description'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_pub_type
    ON p_pub_type.framework_id = f.id AND p_pub_type.property_key = 'publisher_type'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_pub_name
    ON p_pub_name.framework_id = f.id AND p_pub_name.property_key = 'publisher_name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_logo
    ON p_logo.framework_id = f.id AND p_logo.property_key = 'logo_url'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_docs
    ON p_docs.framework_id = f.id AND p_docs.property_key = 'documentation_url'
WHERE f.is_deleted = FALSE;