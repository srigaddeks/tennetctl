-- =============================================================================
-- Migration:   20260409_029_kprotect_signal_selections.sql
-- Module:      11_kprotect
-- Sub-feature: 00_bootstrap
-- Sequence:    029
-- Depends on:  027 (11_kprotect/00_bootstrap views)
-- Description: Add signal selection entity type, attr defs for signal selections
--              and policy selections (threat-type attrs), the signal selections
--              fact table, a v_signal_selections view, and update
--              v_policy_selections to include the new threat-type attrs.
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- 1. Register the kp_signal_selection entity type in 04_dim_entity_types
-- ---------------------------------------------------------------------------
INSERT INTO "11_kprotect"."04_dim_entity_types" (code, label, description) VALUES
    ('kp_signal_selection', 'Signal Selection', 'An org''s enabled signal with optional config overrides.');

-- ---------------------------------------------------------------------------
-- 2. Register attr defs for kp_signal_selection in 05_dim_attr_defs
-- ---------------------------------------------------------------------------
INSERT INTO "11_kprotect"."05_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('kp_signal_selection', 'signal_code', 'Signal Code',
     'Code of the signal from the kbio signal catalog. Text reference — no FK to allow decoupled catalog updates.',
     'key_text'),
    ('kp_signal_selection', 'config_overrides', 'Config Overrides',
     'JSON object of per-signal threshold overrides applied on top of the catalog default config.',
     'key_jsonb'),
    ('kp_signal_selection', 'notes', 'Notes',
     'Free-text admin notes about why this signal was enabled or how it was configured.',
     'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "11_kprotect"."04_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- 3. Register additional attr defs for existing kp_policy_selection entity
--    (threat-type-related attrs)
-- ---------------------------------------------------------------------------
INSERT INTO "11_kprotect"."05_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('kp_policy_selection', 'threat_type_code', 'Threat Type Code',
     'Code of the threat type from the kbio threat catalog. Text reference — no FK to allow decoupled catalog updates.',
     'key_text'),
    ('kp_policy_selection', 'signal_overrides', 'Signal Overrides',
     'JSON object of per-signal threshold overrides within this policy selection.',
     'key_jsonb'),
    ('kp_policy_selection', 'action_override', 'Action Override',
     'Override the threat type''s default action for this policy selection.',
     'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "11_kprotect"."04_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- 4. 13_fct_signal_selections
--    An org's enabled signal for evaluation.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."13_fct_signal_selections" (
    id          VARCHAR(36)   NOT NULL,
    org_id      VARCHAR(36)   NOT NULL,
    is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
    is_test     BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at  TIMESTAMP,
    created_by  VARCHAR(36)   NOT NULL,
    updated_by  VARCHAR(36)   NOT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kp_fct_signal_selections      PRIMARY KEY (id)
);

CREATE INDEX idx_kp_fct_signal_selections_org_id
    ON "11_kprotect"."13_fct_signal_selections" (org_id);
CREATE INDEX idx_kp_fct_signal_selections_created_at
    ON "11_kprotect"."13_fct_signal_selections" (created_at DESC);

COMMENT ON TABLE  "11_kprotect"."13_fct_signal_selections" IS
    'An org''s enabled signal for evaluation. Each row represents one org enabling '
    'a specific signal from the kbio signal catalog for use in policy evaluation. '
    'Signal code, config overrides, and notes are stored in 20_dtl_attrs via the '
    'kp_signal_selection entity type.';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".id IS
    'UUID v7 primary key.';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".org_id IS
    'Org that owns this signal selection. Scopes the row to the tennetctl IAM org.';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".is_active IS
    'FALSE when the signal selection is disabled but not deleted.';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".is_test IS
    'TRUE for test/sandbox signal selections excluded from production analytics.';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".deleted_at IS
    'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".created_by IS
    'UUID of the actor or service that created this row.';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".updated_by IS
    'UUID of the actor or service that last updated this row.';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".created_at IS
    'Row creation timestamp (UTC).';
COMMENT ON COLUMN "11_kprotect"."13_fct_signal_selections".updated_at IS
    'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "11_kprotect"."13_fct_signal_selections" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "11_kprotect"."13_fct_signal_selections" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 5. v_signal_selections — signal selection EAV pivot view
--    Pivots EAV attrs: signal_code (key_text), config_overrides (key_jsonb),
--    notes (key_text).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "11_kprotect".v_signal_selections AS
SELECT
    f.id,
    f.org_id,
    MAX(CASE WHEN ad.code = 'signal_code'       THEN a.key_text  END) AS signal_code,
    MAX(CASE WHEN ad.code = 'config_overrides'  THEN a.key_jsonb END) AS config_overrides,
    MAX(CASE WHEN ad.code = 'notes'             THEN a.key_text  END) AS notes,
    f.is_active,
    (f.deleted_at IS NOT NULL)                                        AS is_deleted,
    f.created_by,
    f.updated_by,
    f.created_at,
    f.updated_at
FROM "11_kprotect"."13_fct_signal_selections" f
LEFT JOIN "11_kprotect"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "11_kprotect"."04_dim_entity_types" WHERE code = 'kp_signal_selection')
      AND a.entity_id = f.id
LEFT JOIN "11_kprotect"."05_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    f.id, f.org_id,
    f.is_active, f.deleted_at,
    f.created_by, f.updated_by, f.created_at, f.updated_at;

COMMENT ON VIEW "11_kprotect".v_signal_selections IS
    'Signal selections with EAV attrs pivoted. signal_code is the kbio signal '
    'catalog reference — no string pattern matching. Pivots: signal_code (text), '
    'config_overrides (jsonb), notes (text). is_deleted from deleted_at.';

GRANT SELECT ON "11_kprotect".v_signal_selections TO tennetctl_read;
GRANT SELECT ON "11_kprotect".v_signal_selections TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 6. Update v_policy_selections — add threat_type_code, signal_overrides,
--    action_override pivots. DROP and recreate since ALTER VIEW cannot add
--    columns.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS "11_kprotect".v_policy_selections;

CREATE OR REPLACE VIEW "11_kprotect".v_policy_selections AS
SELECT
    ps.id,
    ps.org_id,
    ps.predefined_policy_code,
    -- Original EAV pivots
    MAX(CASE WHEN ad.code = 'policy_category'    THEN a.key_text  END) AS policy_category,
    MAX(CASE WHEN ad.code = 'policy_name'        THEN a.key_text  END) AS policy_name,
    ps.priority,
    ps.is_active,
    (ps.deleted_at IS NOT NULL)                                        AS is_deleted,
    MAX(CASE WHEN ad.code = 'config_overrides'   THEN a.key_jsonb END) AS config_overrides,
    MAX(CASE WHEN ad.code = 'notes'              THEN a.key_text  END) AS notes,
    -- New threat-type pivots
    MAX(CASE WHEN ad.code = 'threat_type_code'   THEN a.key_text  END) AS threat_type_code,
    MAX(CASE WHEN ad.code = 'signal_overrides'   THEN a.key_jsonb END) AS signal_overrides,
    MAX(CASE WHEN ad.code = 'action_override'    THEN a.key_text  END) AS action_override,
    ps.created_by,
    ps.updated_by,
    ps.created_at,
    ps.updated_at
FROM "11_kprotect"."10_fct_policy_selections" ps
LEFT JOIN "11_kprotect"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "11_kprotect"."04_dim_entity_types" WHERE code = 'kp_policy_selection')
      AND a.entity_id = ps.id
LEFT JOIN "11_kprotect"."05_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    ps.id, ps.org_id, ps.predefined_policy_code,
    ps.priority, ps.is_active, ps.deleted_at,
    ps.created_by, ps.updated_by, ps.created_at, ps.updated_at;

COMMENT ON VIEW "11_kprotect".v_policy_selections IS
    'Policy selections with EAV attrs pivoted. policy_category and policy_name '
    'are copied from kbio predefined policy catalog at selection time — no '
    'string pattern matching. Pivots: policy_category, policy_name, '
    'config_overrides (jsonb), notes (text), threat_type_code (text), '
    'signal_overrides (jsonb), action_override (text). is_deleted from deleted_at.';

GRANT SELECT ON "11_kprotect".v_policy_selections TO tennetctl_read;
GRANT SELECT ON "11_kprotect".v_policy_selections TO tennetctl_write;

-- DOWN =======================================================================

-- 1. Drop the new signal selections view
DROP VIEW IF EXISTS "11_kprotect".v_signal_selections;

-- 2. Drop the signal selections fact table
DROP TABLE IF EXISTS "11_kprotect"."13_fct_signal_selections";

-- 3. Remove attr defs added for kp_signal_selection
DELETE FROM "11_kprotect"."05_dim_attr_defs"
WHERE entity_type_id = (SELECT id FROM "11_kprotect"."04_dim_entity_types" WHERE code = 'kp_signal_selection');

-- 4. Remove the new attr defs added for kp_policy_selection
DELETE FROM "11_kprotect"."05_dim_attr_defs"
WHERE entity_type_id = (SELECT id FROM "11_kprotect"."04_dim_entity_types" WHERE code = 'kp_policy_selection')
  AND code IN ('threat_type_code', 'signal_overrides', 'action_override');

-- 5. Remove the kp_signal_selection entity type
DELETE FROM "11_kprotect"."04_dim_entity_types"
WHERE code = 'kp_signal_selection';

-- 6. Recreate original v_policy_selections without the threat-type columns
DROP VIEW IF EXISTS "11_kprotect".v_policy_selections;

CREATE OR REPLACE VIEW "11_kprotect".v_policy_selections AS
SELECT
    ps.id,
    ps.org_id,
    ps.predefined_policy_code,
    MAX(CASE WHEN ad.code = 'policy_category'  THEN a.key_text  END) AS policy_category,
    MAX(CASE WHEN ad.code = 'policy_name'      THEN a.key_text  END) AS policy_name,
    ps.priority,
    ps.is_active,
    (ps.deleted_at IS NOT NULL)                                      AS is_deleted,
    MAX(CASE WHEN ad.code = 'config_overrides'  THEN a.key_jsonb END) AS config_overrides,
    MAX(CASE WHEN ad.code = 'notes'             THEN a.key_text  END) AS notes,
    ps.created_by,
    ps.updated_by,
    ps.created_at,
    ps.updated_at
FROM "11_kprotect"."10_fct_policy_selections" ps
LEFT JOIN "11_kprotect"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "11_kprotect"."04_dim_entity_types" WHERE code = 'kp_policy_selection')
      AND a.entity_id = ps.id
LEFT JOIN "11_kprotect"."05_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    ps.id, ps.org_id, ps.predefined_policy_code,
    ps.priority, ps.is_active, ps.deleted_at,
    ps.created_by, ps.updated_by, ps.created_at, ps.updated_at;

COMMENT ON VIEW "11_kprotect".v_policy_selections IS
    'Policy selections with EAV attrs pivoted. policy_category and policy_name '
    'are copied from kbio predefined policy catalog at selection time — no '
    'string pattern matching. Pivots: policy_category, policy_name, '
    'config_overrides (jsonb), notes (text). is_deleted from deleted_at.';

GRANT SELECT ON "11_kprotect".v_policy_selections TO tennetctl_read;
GRANT SELECT ON "11_kprotect".v_policy_selections TO tennetctl_write;
