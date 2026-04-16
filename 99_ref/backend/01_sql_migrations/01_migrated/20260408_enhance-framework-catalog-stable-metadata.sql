-- =============================================================================
-- Migration: Enhance framework catalog with stable published metadata
-- =============================================================================
-- This migration updates the framework catalog view to provide fallback
-- stable metadata (name, description, etc.) from the latest published version.
-- This allows the library to show consistent information even when a framework
-- is currently being edited or is in a pending review state.
-- =============================================================================

CREATE OR REPLACE VIEW "05_grc_library"."40_vw_framework_catalog" AS
WITH latest_published AS (
    SELECT 
        v.framework_id, 
        v.id as version_id, 
        v.version_code, 
        v.control_count,
        ROW_NUMBER() OVER (PARTITION BY v.framework_id ORDER BY v.created_at DESC) as rnk
    FROM "05_grc_library"."11_fct_framework_versions" v
    WHERE v.lifecycle_state = 'published' AND v.is_deleted = FALSE
)
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
    -- Live/Draft EAV properties
    p_name.property_value           AS name,
    p_desc.property_value           AS description,
    p_short.property_value          AS short_description,
    p_pub_type.property_value       AS publisher_type,
    p_pub_name.property_value       AS publisher_name,
    p_logo.property_value           AS logo_url,
    p_docs.property_value           AS documentation_url,
    
    -- Stable Metadata (from latest published version properties)
    p_vname.property_value          AS published_name,
    p_vdesc.property_value          AS published_description,
    p_vshort.property_value         AS published_short_description,
    p_vpub_type.property_value      AS published_publisher_type,
    p_vpub_name.property_value      AS published_publisher_name,
    p_vlogo.property_value          AS published_logo_url,
    p_vdocs.property_value          AS published_documentation_url,

    -- Latest published version code
    lp.version_code                 AS latest_version_code,
    
    -- control_count: use the published version's stored count.
    -- Fall back to raw control count for frameworks that have never been published yet.
    COALESCE(
        lp.control_count,
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

-- Live Property Joins
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

-- Stable/Published Metadata Joins
LEFT JOIN latest_published lp ON lp.framework_id = f.id AND lp.rnk = 1
LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vname
    ON p_vname.framework_version_id = lp.version_id AND p_vname.property_key = 'name'
LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vdesc
    ON p_vdesc.framework_version_id = lp.version_id AND p_vdesc.property_key = 'description'
LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vshort
    ON p_vshort.framework_version_id = lp.version_id AND p_vshort.property_key = 'short_description'
LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vpub_type
    ON p_vpub_type.framework_version_id = lp.version_id AND p_vpub_type.property_key = 'publisher_type'
LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vpub_name
    ON p_vpub_name.framework_version_id = lp.version_id AND p_vpub_name.property_key = 'publisher_name'
LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vlogo
    ON p_vlogo.framework_version_id = lp.version_id AND p_vlogo.property_key = 'logo_url'
LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vdocs
    ON p_vdocs.framework_version_id = lp.version_id AND p_vdocs.property_key = 'documentation_url'

WHERE f.is_deleted = FALSE;
