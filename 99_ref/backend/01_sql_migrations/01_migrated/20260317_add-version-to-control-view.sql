-- ============================================================================
-- Add version column to 41_vw_control_detail view
-- ============================================================================
-- The version INTEGER column was added to 13_fct_controls in migration
-- 20260316_add-version-numbers.sql but was not included in the view.
-- This migration recreates the view with version exposed.
-- ============================================================================

DROP VIEW IF EXISTS "05_grc_library"."41_vw_control_detail";
CREATE VIEW "05_grc_library"."41_vw_control_detail" AS
SELECT
    c.id,
    c.framework_id,
    c.requirement_id,
    c.tenant_key,
    c.control_code,
    c.control_category_code,
    cat.name                    AS category_name,
    c.criticality_code,
    crit.name                   AS criticality_name,
    c.control_type,
    c.automation_potential,
    c.sort_order,
    c.version,
    c.is_active,
    c.is_deleted,
    c.created_at,
    c.updated_at,
    -- EAV properties flattened
    p_name.property_value       AS name,
    p_desc.property_value       AS description,
    p_guid.property_value       AS guidance,
    p_impl.property_value       AS implementation_notes,
    -- Framework info
    f.framework_code,
    fw_name.property_value      AS framework_name,
    -- Requirement info
    r.requirement_code,
    rq_name.property_value      AS requirement_name,
    -- Test count
    (SELECT COUNT(*)
     FROM "05_grc_library"."30_lnk_test_control_mappings" m
     WHERE m.control_id = c.id) AS test_count
FROM "05_grc_library"."13_fct_controls" c
LEFT JOIN "05_grc_library"."04_dim_control_categories" cat
    ON cat.code = c.control_category_code
LEFT JOIN "05_grc_library"."05_dim_control_criticalities" crit
    ON crit.code = c.criticality_code
LEFT JOIN "05_grc_library"."10_fct_frameworks" f
    ON f.id = c.framework_id
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fw_name
    ON fw_name.framework_id = f.id AND fw_name.property_key = 'name'
LEFT JOIN "05_grc_library"."12_fct_requirements" r
    ON r.id = c.requirement_id
LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" rq_name
    ON rq_name.requirement_id = r.id AND rq_name.property_key = 'name'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
    ON p_name.control_id = c.id AND p_name.property_key = 'name'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_desc
    ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_guid
    ON p_guid.control_id = c.id AND p_guid.property_key = 'guidance'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_impl
    ON p_impl.control_id = c.id AND p_impl.property_key = 'implementation_notes'
WHERE c.is_deleted = FALSE;
