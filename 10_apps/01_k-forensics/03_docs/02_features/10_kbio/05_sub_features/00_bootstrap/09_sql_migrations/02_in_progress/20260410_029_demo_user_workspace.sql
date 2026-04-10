-- =============================================================================
-- Migration:   20260410_029_demo_user_workspace.sql
-- Module:      10_kbio
-- Sub-feature: 00_bootstrap
-- Sequence:    029
-- Depends on:  025 (demo_auth)
-- Description: Add workspace_id and api_key_id EAV attr defs to kbio_demo_user
--              so each demo user can own a dedicated workspace and API key.
--              Also updates v_demo_users view to pivot these two new columns.
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- New attr_defs for kbio_demo_user
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."07_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('kbio_demo_user', 'workspace_id', 'Workspace ID', 'UUID of the kbio workspace owned by this demo user.', 'key_text'),
    ('kbio_demo_user', 'api_key_id',   'API Key ID',   'UUID of the kbio API key created for this demo user.',  'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "10_kbio"."06_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- Rebuild v_demo_users with new pivoted columns
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_demo_users AS
SELECT
    u.id,
    u.user_hash,
    u.status_id,
    st.code                                                               AS status,
    u.is_active,
    (u.deleted_at IS NOT NULL)                                            AS is_deleted,
    MAX(CASE WHEN ad.code = 'username'               THEN a.key_text END) AS username,
    MAX(CASE WHEN ad.code = 'email'                  THEN a.key_text END) AS email,
    MAX(CASE WHEN ad.code = 'password_hash'          THEN a.key_text END) AS password_hash,
    MAX(CASE WHEN ad.code = 'mobile_number'          THEN a.key_text END) AS mobile_number,
    MAX(CASE WHEN ad.code = 'mpin_hash'              THEN a.key_text END) AS mpin_hash,
    MAX(CASE WHEN ad.code = 'security_q1'            THEN a.key_text END) AS security_q1,
    MAX(CASE WHEN ad.code = 'security_a1_hash'       THEN a.key_text END) AS security_a1_hash,
    MAX(CASE WHEN ad.code = 'security_q2'            THEN a.key_text END) AS security_q2,
    MAX(CASE WHEN ad.code = 'security_a2_hash'       THEN a.key_text END) AS security_a2_hash,
    MAX(CASE WHEN ad.code = 'security_q3'            THEN a.key_text END) AS security_q3,
    MAX(CASE WHEN ad.code = 'security_a3_hash'       THEN a.key_text END) AS security_a3_hash,
    MAX(CASE WHEN ad.code = 'failed_challenge_count' THEN a.key_text END) AS failed_challenge_count,
    MAX(CASE WHEN ad.code = 'last_challenge_at'      THEN a.key_text END) AS last_challenge_at,
    MAX(CASE WHEN ad.code = 'workspace_id'           THEN a.key_text END) AS workspace_id,
    MAX(CASE WHEN ad.code = 'api_key_id'             THEN a.key_text END) AS api_key_id,
    u.created_by,
    u.updated_by,
    u.created_at,
    u.updated_at
FROM "10_kbio"."17_fct_demo_users" u
LEFT JOIN "10_kbio"."09_dim_demo_user_statuses" st ON st.id = u.status_id
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_demo_user')
      AND a.entity_id = u.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    u.id, u.user_hash, u.status_id, st.code,
    u.is_active, u.deleted_at,
    u.created_by, u.updated_by, u.created_at, u.updated_at;

COMMENT ON VIEW "10_kbio".v_demo_users IS
    'Demo site users with status dim code resolved and EAV attrs pivoted. '
    'Pivots: username, email, password_hash, mobile_number, mpin_hash, '
    'security_q1–q3, security_a1_hash–a3_hash, failed_challenge_count, '
    'last_challenge_at, workspace_id, api_key_id.';

-- DOWN =======================================================================

-- Revert view to previous shape (without workspace_id / api_key_id pivots)
CREATE OR REPLACE VIEW "10_kbio".v_demo_users AS
SELECT
    u.id,
    u.user_hash,
    u.status_id,
    st.code                                                               AS status,
    u.is_active,
    (u.deleted_at IS NOT NULL)                                            AS is_deleted,
    MAX(CASE WHEN ad.code = 'username'               THEN a.key_text END) AS username,
    MAX(CASE WHEN ad.code = 'email'                  THEN a.key_text END) AS email,
    MAX(CASE WHEN ad.code = 'password_hash'          THEN a.key_text END) AS password_hash,
    MAX(CASE WHEN ad.code = 'mobile_number'          THEN a.key_text END) AS mobile_number,
    MAX(CASE WHEN ad.code = 'mpin_hash'              THEN a.key_text END) AS mpin_hash,
    MAX(CASE WHEN ad.code = 'security_q1'            THEN a.key_text END) AS security_q1,
    MAX(CASE WHEN ad.code = 'security_a1_hash'       THEN a.key_text END) AS security_a1_hash,
    MAX(CASE WHEN ad.code = 'security_q2'            THEN a.key_text END) AS security_q2,
    MAX(CASE WHEN ad.code = 'security_a2_hash'       THEN a.key_text END) AS security_a2_hash,
    MAX(CASE WHEN ad.code = 'security_q3'            THEN a.key_text END) AS security_q3,
    MAX(CASE WHEN ad.code = 'security_a3_hash'       THEN a.key_text END) AS security_a3_hash,
    MAX(CASE WHEN ad.code = 'failed_challenge_count' THEN a.key_text END) AS failed_challenge_count,
    MAX(CASE WHEN ad.code = 'last_challenge_at'      THEN a.key_text END) AS last_challenge_at,
    u.created_by,
    u.updated_by,
    u.created_at,
    u.updated_at
FROM "10_kbio"."17_fct_demo_users" u
LEFT JOIN "10_kbio"."09_dim_demo_user_statuses" st ON st.id = u.status_id
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_demo_user')
      AND a.entity_id = u.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    u.id, u.user_hash, u.status_id, st.code,
    u.is_active, u.deleted_at,
    u.created_by, u.updated_by, u.created_at, u.updated_at;

DELETE FROM "10_kbio"."07_dim_attr_defs"
WHERE entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_demo_user')
  AND code IN ('workspace_id', 'api_key_id');
