-- Enhance framework deployments view to include latest version metadata
-- for update notifications (release notes, change severity, change summary).

CREATE OR REPLACE VIEW "05_grc_library"."44_vw_framework_deployments" AS
SELECT
    d.id,
    d.tenant_key,
    d.org_id::text,
    d.framework_id::text,
    d.deployed_version_id::text,
    d.deployment_status,
    d.workspace_id::text,
    d.is_active,
    d.created_at::text,
    d.updated_at::text,
    d.created_by::text,
    -- framework fields
    f.framework_code,
    f.approval_status,
    f.is_marketplace_visible,
    -- framework properties
    fp_name.property_value        AS framework_name,
    fp_desc.property_value        AS framework_description,
    fp_pub.property_value         AS publisher_name,
    fp_logo.property_value        AS logo_url,
    -- deployed version
    v.version_code                AS deployed_version_code,
    v.lifecycle_state             AS deployed_lifecycle_state,
    -- latest published version for update detection
    latest.id::text               AS latest_version_id,
    latest.version_code           AS latest_version_code,
    (latest.id IS DISTINCT FROM d.deployed_version_id) AS has_update,
    -- latest version metadata for notification display
    latest_notes.property_value   AS latest_release_notes,
    latest_severity.property_value AS latest_change_severity,
    latest_summary.property_value AS latest_change_summary
FROM "05_grc_library"."16_fct_framework_deployments" d
JOIN "05_grc_library"."10_fct_frameworks" f
    ON f.id = d.framework_id
    AND f.is_deleted = FALSE
JOIN "05_grc_library"."11_fct_framework_versions" v
    ON v.id = d.deployed_version_id
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp_name
    ON fp_name.framework_id = f.id AND fp_name.property_key = 'name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp_desc
    ON fp_desc.framework_id = f.id AND fp_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp_pub
    ON fp_pub.framework_id = f.id AND fp_pub.property_key = 'publisher_name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp_logo
    ON fp_logo.framework_id = f.id AND fp_logo.property_key = 'logo_url'
LEFT JOIN LATERAL (
    SELECT id, version_code
    FROM "05_grc_library"."11_fct_framework_versions"
    WHERE framework_id = d.framework_id
      AND lifecycle_state = 'published'
      AND is_deleted = FALSE
    ORDER BY (version_code ~ '^[0-9]+$')::int DESC, version_code DESC, created_at DESC
    LIMIT 1
) latest ON TRUE
-- Latest version metadata for update notifications
LEFT JOIN "05_grc_library"."21_dtl_version_properties" latest_notes
    ON latest_notes.framework_version_id = latest.id
    AND latest_notes.property_key = 'release_notes'
LEFT JOIN "05_grc_library"."21_dtl_version_properties" latest_severity
    ON latest_severity.framework_version_id = latest.id
    AND latest_severity.property_key = 'change_severity_label'
LEFT JOIN "05_grc_library"."21_dtl_version_properties" latest_summary
    ON latest_summary.framework_version_id = latest.id
    AND latest_summary.property_key = 'change_summary';
