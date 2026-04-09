-- =============================================================================
-- Migration:   20260409_027_kprotect_views.sql
-- Module:      11_kprotect
-- Sub-feature: 00_bootstrap
-- Sequence:    027
-- Depends on:  026 (11_kprotect/00_bootstrap tables)
-- Description: Create read-only views for kprotect entities. Views resolve
--              dimension codes, pivot EAV attributes, and derive computed
--              columns. All repository reads go through views, never raw tables.
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- 1. v_policy_selections
-- Pivots EAV attrs: config_overrides (key_jsonb), notes (key_text),
-- policy_category (key_text), policy_name (key_text).
-- Category and name are copied from kbio at selection time — no string
-- pattern matching, no cross-database FK.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "11_kprotect".v_policy_selections AS
SELECT
    ps.id,
    ps.org_id,
    ps.predefined_policy_code,
    -- Category stored as EAV attr (copied from kbio when policy is selected)
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

-- ---------------------------------------------------------------------------
-- 2. v_policy_sets
-- Pivots EAV attrs: code, name, description, evaluation_mode.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "11_kprotect".v_policy_sets AS
SELECT
    pset.id,
    pset.org_id,
    pset.is_default,
    pset.is_active,
    (pset.deleted_at IS NOT NULL)                                       AS is_deleted,
    -- EAV pivots (entity_type_id = 2 = kp_policy_set)
    MAX(CASE WHEN ad.code = 'code'             THEN a.key_text END)     AS code,
    MAX(CASE WHEN ad.code = 'name'             THEN a.key_text END)     AS name,
    MAX(CASE WHEN ad.code = 'description'      THEN a.key_text END)     AS description,
    MAX(CASE WHEN ad.code = 'evaluation_mode'  THEN a.key_text END)     AS evaluation_mode,
    pset.created_by,
    pset.updated_by,
    pset.created_at,
    pset.updated_at
FROM "11_kprotect"."11_fct_policy_sets" pset
LEFT JOIN "11_kprotect"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "11_kprotect"."04_dim_entity_types" WHERE code = 'kp_policy_set')
      AND a.entity_id = pset.id
LEFT JOIN "11_kprotect"."05_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    pset.id, pset.org_id, pset.is_default,
    pset.is_active, pset.deleted_at,
    pset.created_by, pset.updated_by, pset.created_at, pset.updated_at;

COMMENT ON VIEW "11_kprotect".v_policy_sets IS
    'Policy sets with EAV attrs pivoted. Pivots: code, name, description, '
    'evaluation_mode. is_deleted derived from deleted_at IS NOT NULL.';

GRANT SELECT ON "11_kprotect".v_policy_sets TO tennetctl_read;
GRANT SELECT ON "11_kprotect".v_policy_sets TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 3. v_api_keys
-- Pivots EAV attrs: key_prefix, label, expires_at. Excludes key_hash from view
-- (never exposed to the read path).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "11_kprotect".v_api_keys AS
SELECT
    k.id,
    k.org_id,
    k.is_active,
    (k.deleted_at IS NOT NULL)                                      AS is_deleted,
    -- EAV pivots (entity_type_id = 3 = kp_api_key)
    -- key_hash intentionally excluded — never returned via API
    MAX(CASE WHEN ad.code = 'key_prefix'  THEN a.key_text END)      AS key_prefix,
    MAX(CASE WHEN ad.code = 'label'       THEN a.key_text END)      AS label,
    MAX(CASE WHEN ad.code = 'expires_at'  THEN a.key_text END)      AS expires_at,
    k.created_by,
    k.updated_by,
    k.created_at,
    k.updated_at
FROM "11_kprotect"."12_fct_api_keys" k
LEFT JOIN "11_kprotect"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "11_kprotect"."04_dim_entity_types" WHERE code = 'kp_api_key')
      AND a.entity_id = k.id
LEFT JOIN "11_kprotect"."05_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    k.id, k.org_id, k.is_active, k.deleted_at,
    k.created_by, k.updated_by, k.created_at, k.updated_at;

COMMENT ON VIEW "11_kprotect".v_api_keys IS
    'API keys with EAV attrs pivoted. key_hash is intentionally excluded — it is '
    'never returned via the API. Pivots: key_prefix, label, expires_at. '
    'is_deleted derived from deleted_at IS NOT NULL.';

GRANT SELECT ON "11_kprotect".v_api_keys TO tennetctl_read;
GRANT SELECT ON "11_kprotect".v_api_keys TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 4. v_decisions
-- Resolves outcome and action dim codes from 60_evt_decisions.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "11_kprotect".v_decisions AS
SELECT
    d.id,
    d.org_id,
    d.session_id,
    d.user_hash,
    d.device_uuid,
    d.policy_set_id,
    d.outcome_id,
    o.code                          AS outcome,
    d.action_id,
    at.code                         AS action,
    d.total_latency_ms,
    d.kbio_latency_ms,
    d.policy_latency_ms,
    d.metadata,
    d.actor_id,
    d.created_at
FROM "11_kprotect"."60_evt_decisions" d
LEFT JOIN "11_kprotect"."02_dim_decision_outcomes" o  ON o.id  = d.outcome_id
LEFT JOIN "11_kprotect"."01_dim_action_types"      at ON at.id = d.action_id;

COMMENT ON VIEW "11_kprotect".v_decisions IS
    'Decision events with outcome and action dim codes resolved. '
    'outcome resolves 02_dim_decision_outcomes.code. '
    'action resolves 01_dim_action_types.code.';

GRANT SELECT ON "11_kprotect".v_decisions TO tennetctl_read;
GRANT SELECT ON "11_kprotect".v_decisions TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 5. v_decision_details
-- Resolves action dim code from 61_evt_decision_details.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "11_kprotect".v_decision_details AS
SELECT
    dd.id,
    dd.org_id,
    dd.decision_id,
    dd.policy_selection_id,
    dd.action_id,
    at.code                         AS action,
    dd.reason,
    dd.execution_ms,
    dd.error_message,
    dd.metadata,
    dd.actor_id,
    dd.created_at
FROM "11_kprotect"."61_evt_decision_details" dd
LEFT JOIN "11_kprotect"."01_dim_action_types" at ON at.id = dd.action_id;

COMMENT ON VIEW "11_kprotect".v_decision_details IS
    'Per-policy decision detail rows with action dim code resolved. '
    'action resolves 01_dim_action_types.code.';

GRANT SELECT ON "11_kprotect".v_decision_details TO tennetctl_read;
GRANT SELECT ON "11_kprotect".v_decision_details TO tennetctl_write;

-- DOWN =======================================================================

DROP VIEW IF EXISTS "11_kprotect".v_decision_details;
DROP VIEW IF EXISTS "11_kprotect".v_decisions;
DROP VIEW IF EXISTS "11_kprotect".v_api_keys;
DROP VIEW IF EXISTS "11_kprotect".v_policy_sets;
DROP VIEW IF EXISTS "11_kprotect".v_policy_selections;
