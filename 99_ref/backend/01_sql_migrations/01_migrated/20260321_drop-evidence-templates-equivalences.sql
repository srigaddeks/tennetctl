-- Drop evidence templates and cross-framework equivalences tables.
-- These features are deferred — evidence collection belongs to a future
-- compliance operations module, and equivalences have no consumer yet.

DROP TABLE IF EXISTS "05_grc_library"."26_dtl_evidence_template_properties" CASCADE;
DROP TABLE IF EXISTS "05_grc_library"."15_fct_evidence_templates" CASCADE;
DROP TABLE IF EXISTS "05_grc_library"."32_lnk_cross_framework_equivalences" CASCADE;

-- Recreate the test detail view without evidence_template_count
DROP VIEW IF EXISTS "05_grc_library"."42_vw_test_detail";
CREATE VIEW "05_grc_library"."42_vw_test_detail" AS
SELECT
    t.id,
    t.tenant_key,
    t.test_code,
    t.test_type_code,
    tt.name                         AS test_type_name,
    t.integration_type,
    t.monitoring_frequency,
    t.is_platform_managed,
    t.is_active,
    t.is_deleted,
    t.created_at,
    t.updated_at,
    t.scope_org_id,
    t.scope_workspace_id,
    p_name.property_value           AS name,
    p_desc.property_value           AS description,
    p_rule.property_value           AS evaluation_rule,
    p_sig.property_value            AS signal_type,
    p_guide.property_value          AS integration_guide,
    (SELECT COUNT(*)
     FROM "05_grc_library"."30_lnk_test_control_mappings" m
     WHERE m.control_test_id = t.id) AS mapped_control_count
FROM "05_grc_library"."14_fct_control_tests" t
LEFT JOIN "05_grc_library"."07_dim_test_types" tt
    ON tt.code = t.test_type_code
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_name
    ON p_name.test_id = t.id AND p_name.property_key = 'name'
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_desc
    ON p_desc.test_id = t.id AND p_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_rule
    ON p_rule.test_id = t.id AND p_rule.property_key = 'evaluation_rule'
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_sig
    ON p_sig.test_id = t.id AND p_sig.property_key = 'signal_type'
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_guide
    ON p_guide.test_id = t.id AND p_guide.property_key = 'integration_guide'
WHERE t.is_deleted = FALSE;
