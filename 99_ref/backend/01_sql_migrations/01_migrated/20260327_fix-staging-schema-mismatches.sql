-- Fix schema mismatches between dev and staging
-- 1. Add missing columns to 08_dim_template_variable_keys (notifications config)
-- 2. Add workspace_id to promoted_tests table + recreate view
-- 3. Recreate risk detail view with version column

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Notification template variable keys: add preview_default, static_value,
--    query_id, is_user_defined columns
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE "03_notifications"."08_dim_template_variable_keys"
    ADD COLUMN IF NOT EXISTS preview_default  TEXT         NULL,
    ADD COLUMN IF NOT EXISTS static_value     TEXT         NULL,
    ADD COLUMN IF NOT EXISTS query_id         UUID         NULL,
    ADD COLUMN IF NOT EXISTS is_user_defined  BOOLEAN      NOT NULL DEFAULT FALSE;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Promoted tests: add workspace_id column + recreate view
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE "15_sandbox"."35_fct_promoted_tests"
    ADD COLUMN IF NOT EXISTS workspace_id UUID NULL;

DROP VIEW IF EXISTS "15_sandbox"."66_vw_promoted_test_detail";
CREATE VIEW "15_sandbox"."66_vw_promoted_test_detail" AS
SELECT
    t.id::text,
    t.tenant_key,
    t.org_id::text,
    t.workspace_id::text,
    t.promotion_id::text,
    t.source_signal_id::text,
    t.source_policy_id::text,
    t.source_library_id::text,
    t.source_pack_id::text,
    t.test_code,
    t.test_type_code,
    t.monitoring_frequency,
    t.linked_asset_id::text,
    t.version_number,
    t.is_active,
    t.promoted_by::text,
    t.promoted_at::text,
    t.is_deleted,
    t.created_at::text,
    t.updated_at::text,
    ci.connector_type_code,
    cip.property_value AS connector_name,
    pr.target_test_id::text AS control_test_id,
    MAX(CASE WHEN p.property_key = 'name'              THEN p.property_value END) AS name,
    MAX(CASE WHEN p.property_key = 'description'       THEN p.property_value END) AS description,
    MAX(CASE WHEN p.property_key = 'evaluation_rule'   THEN p.property_value END) AS evaluation_rule,
    MAX(CASE WHEN p.property_key = 'signal_type'       THEN p.property_value END) AS signal_type,
    MAX(CASE WHEN p.property_key = 'integration_guide' THEN p.property_value END) AS integration_guide
FROM "15_sandbox"."35_fct_promoted_tests" t
LEFT JOIN "15_sandbox"."36_dtl_promoted_test_properties" p
    ON p.test_id = t.id
LEFT JOIN "15_sandbox"."20_fct_connector_instances" ci
    ON ci.id = t.linked_asset_id
LEFT JOIN "15_sandbox"."40_dtl_connector_instance_properties" cip
    ON cip.connector_instance_id = ci.id AND cip.property_key = 'name'
LEFT JOIN "15_sandbox"."30_trx_promotions" pr
    ON pr.id = t.promotion_id
WHERE t.is_deleted = FALSE
GROUP BY
    t.id, t.tenant_key, t.org_id, t.workspace_id, t.promotion_id,
    t.source_signal_id, t.source_policy_id, t.source_library_id, t.source_pack_id,
    t.test_code, t.test_type_code, t.monitoring_frequency,
    t.linked_asset_id, t.version_number, t.is_active,
    t.promoted_by, t.promoted_at, t.is_deleted,
    t.created_at, t.updated_at,
    ci.connector_type_code, cip.property_value, pr.target_test_id;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Risk detail view: recreate with version column
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "14_risk_registry"."40_vw_risk_detail" AS
SELECT
    r.id,
    r.tenant_key,
    r.risk_code,
    r.org_id,
    r.workspace_id,
    r.risk_category_code,
    rc.name                         AS category_name,
    r.risk_level_code,
    rl.name                         AS risk_level_name,
    rl.color_hex                    AS risk_level_color,
    r.treatment_type_code,
    rt.name                         AS treatment_type_name,
    r.source_type,
    r.risk_status,
    r.is_active,
    r.is_deleted,
    r.created_at,
    r.updated_at,
    r.created_by,
    r.version,
    -- EAV properties flattened
    p_title.property_value          AS title,
    p_desc.property_value           AS description,
    p_notes.property_value          AS notes,
    p_owner.property_value          AS owner_user_id,
    p_impact.property_value         AS business_impact,
    -- Latest inherent score
    (SELECT ra.risk_score
     FROM "14_risk_registry"."32_trx_risk_assessments" ra
     WHERE ra.risk_id = r.id AND ra.assessment_type = 'inherent'
     ORDER BY ra.assessed_at DESC LIMIT 1)  AS inherent_risk_score,
    -- Latest residual score
    (SELECT ra.risk_score
     FROM "14_risk_registry"."32_trx_risk_assessments" ra
     WHERE ra.risk_id = r.id AND ra.assessment_type = 'residual'
     ORDER BY ra.assessed_at DESC LIMIT 1)  AS residual_risk_score,
    -- Linked control count
    (SELECT COUNT(*)
     FROM "14_risk_registry"."30_lnk_risk_control_mappings" m
     WHERE m.risk_id = r.id)        AS linked_control_count,
    -- Treatment plan status
    (SELECT tp.plan_status
     FROM "14_risk_registry"."11_fct_risk_treatment_plans" tp
     WHERE tp.risk_id = r.id AND tp.is_deleted = FALSE
     LIMIT 1)                       AS treatment_plan_status,
    -- Treatment plan target date
    (SELECT tp.target_date::text
     FROM "14_risk_registry"."11_fct_risk_treatment_plans" tp
     WHERE tp.risk_id = r.id AND tp.is_deleted = FALSE
     LIMIT 1)                       AS treatment_plan_target_date
FROM "14_risk_registry"."10_fct_risks" r
LEFT JOIN "14_risk_registry"."02_dim_risk_categories" rc
    ON rc.code = r.risk_category_code
LEFT JOIN "14_risk_registry"."04_dim_risk_levels" rl
    ON rl.code = r.risk_level_code
LEFT JOIN "14_risk_registry"."03_dim_risk_treatment_types" rt
    ON rt.code = r.treatment_type_code
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_title
    ON p_title.risk_id = r.id AND p_title.property_key = 'title'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_desc
    ON p_desc.risk_id = r.id AND p_desc.property_key = 'description'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_notes
    ON p_notes.risk_id = r.id AND p_notes.property_key = 'notes'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_owner
    ON p_owner.risk_id = r.id AND p_owner.property_key = 'owner_user_id'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_impact
    ON p_impact.risk_id = r.id AND p_impact.property_key = 'business_impact'
WHERE r.is_deleted = FALSE;
