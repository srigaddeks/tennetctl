-- ─────────────────────────────────────────────────────────────────────────────
-- Risk Registry Enhancements: group assignment, appetite, review scheduling
-- ─────────────────────────────────────────────────────────────────────────────

-- Responsible group assignment for risks (RACI model)
CREATE TABLE IF NOT EXISTS "14_risk_registry"."34_lnk_risk_group_assignments" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID NOT NULL,
    group_id UUID NOT NULL,
    role TEXT NOT NULL DEFAULT 'responsible',
    assigned_by UUID NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_34_risk_group_risk FOREIGN KEY (risk_id)
        REFERENCES "14_risk_registry"."10_fct_risks" (id) ON DELETE CASCADE,
    CONSTRAINT ck_34_risk_group_role
        CHECK (role IN ('responsible', 'accountable', 'consulted', 'informed')),
    CONSTRAINT uq_34_risk_group UNIQUE (risk_id, group_id, role)
);

CREATE INDEX IF NOT EXISTS idx_34_risk_group_risk
    ON "14_risk_registry"."34_lnk_risk_group_assignments" (risk_id);
CREATE INDEX IF NOT EXISTS idx_34_risk_group_group
    ON "14_risk_registry"."34_lnk_risk_group_assignments" (group_id);

-- Risk appetite / tolerance thresholds per org
CREATE TABLE IF NOT EXISTS "14_risk_registry"."35_fct_risk_appetite" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key TEXT NOT NULL,
    org_id UUID NOT NULL,
    risk_category_code TEXT NOT NULL,
    appetite_level_code TEXT NOT NULL DEFAULT 'medium',
    tolerance_threshold INT NOT NULL DEFAULT 15,
    max_acceptable_score INT NOT NULL DEFAULT 10,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_by UUID,
    CONSTRAINT ck_35_appetite_level
        CHECK (appetite_level_code IN ('low', 'medium', 'high', 'very_high')),
    CONSTRAINT ck_35_tolerance
        CHECK (tolerance_threshold BETWEEN 1 AND 25),
    CONSTRAINT ck_35_max_score
        CHECK (max_acceptable_score BETWEEN 1 AND 25),
    CONSTRAINT uq_35_org_category UNIQUE (org_id, risk_category_code)
);

CREATE INDEX IF NOT EXISTS idx_35_risk_appetite_org
    ON "14_risk_registry"."35_fct_risk_appetite" (org_id, is_active);

-- Scheduled risk reviews
CREATE TABLE IF NOT EXISTS "14_risk_registry"."36_trx_scheduled_reviews" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID NOT NULL,
    tenant_key TEXT NOT NULL,
    review_frequency TEXT NOT NULL DEFAULT 'quarterly',
    next_review_date DATE NOT NULL,
    last_reviewed_at TIMESTAMPTZ,
    last_reviewed_by UUID,
    assigned_reviewer_id UUID,
    is_overdue BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    CONSTRAINT fk_36_review_risk FOREIGN KEY (risk_id)
        REFERENCES "14_risk_registry"."10_fct_risks" (id) ON DELETE CASCADE,
    CONSTRAINT ck_36_review_frequency
        CHECK (review_frequency IN ('monthly', 'quarterly', 'semi_annual', 'annual', 'custom')),
    CONSTRAINT uq_36_risk_review UNIQUE (risk_id)
);

CREATE INDEX IF NOT EXISTS idx_36_scheduled_reviews_risk
    ON "14_risk_registry"."36_trx_scheduled_reviews" (risk_id);
CREATE INDEX IF NOT EXISTS idx_36_scheduled_reviews_due
    ON "14_risk_registry"."36_trx_scheduled_reviews" (next_review_date)
    WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_36_scheduled_reviews_overdue
    ON "14_risk_registry"."36_trx_scheduled_reviews" (is_overdue)
    WHERE is_active = TRUE AND is_overdue = TRUE;

-- Recreate risk detail view with version column (added by 20260316_add-version-numbers.sql)
DROP VIEW IF EXISTS "14_risk_registry"."40_vw_risk_detail";
CREATE VIEW "14_risk_registry"."40_vw_risk_detail" AS
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
