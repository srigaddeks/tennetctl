-- =============================================================================
-- Migration:   20260409_022_kbio_views.sql
-- Module:      10_kbio
-- Sub-feature: 00_bootstrap
-- Sequence:    022
-- Depends on:  021 (10_kbio/00_bootstrap tables)
-- Description: Create read-only views for kbio entities. Views resolve dimension
--              codes, pivot key EAV attributes, and derive computed columns.
--              All repository reads go through views, never raw tables.
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- 1. v_sessions — behavioral session read view
--    Resolves status / trust_level / baseline_quality dim codes.
--    Pivots all 9 EAV attrs registered for kbio_session (entity_type_id = 1).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_sessions AS
SELECT
    s.id,
    s.sdk_session_id,
    s.user_hash,
    s.device_uuid,
    s.status_id,
    st.code                                                                        AS status,
    s.trust_level_id,
    tl.code                                                                        AS trust_level,
    s.baseline_quality_id,
    bq.code                                                                        AS baseline_quality,
    s.is_active,
    (s.deleted_at IS NOT NULL)                                                     AS is_deleted,
    -- EAV pivots (entity_type_id = 1 = kbio_session)
    MAX(CASE WHEN ad.code = 'ip_address'          THEN a.key_text  END)            AS ip_address,
    MAX(CASE WHEN ad.code = 'user_agent'          THEN a.key_text  END)            AS user_agent,
    MAX(CASE WHEN ad.code = 'sdk_version'         THEN a.key_text  END)            AS sdk_version,
    MAX(CASE WHEN ad.code = 'sdk_platform'        THEN a.key_text  END)            AS sdk_platform,
    MAX(CASE WHEN ad.code = 'total_pulses'        THEN a.key_text  END)            AS total_pulses,
    MAX(CASE WHEN ad.code = 'max_drift_score'     THEN a.key_text  END)            AS max_drift_score,
    MAX(CASE WHEN ad.code = 'current_drift_score' THEN a.key_text  END)            AS current_drift_score,
    MAX(CASE WHEN ad.code = 'end_reason'          THEN a.key_text  END)            AS end_reason,
    MAX(CASE WHEN ad.code = 'critical_actions'    THEN a.key_jsonb END)            AS critical_actions,
    s.created_by,
    s.updated_by,
    s.created_at,
    s.updated_at
FROM "10_kbio"."10_fct_sessions" s
LEFT JOIN "10_kbio"."01_dim_session_statuses"  st ON st.id = s.status_id
LEFT JOIN "10_kbio"."03_dim_trust_levels"      tl ON tl.id = s.trust_level_id
LEFT JOIN "10_kbio"."05_dim_baseline_qualities" bq ON bq.id = s.baseline_quality_id
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_session')
      AND a.entity_id = s.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    s.id, s.sdk_session_id, s.user_hash, s.device_uuid,
    s.status_id, st.code,
    s.trust_level_id, tl.code,
    s.baseline_quality_id, bq.code,
    s.is_active, s.deleted_at,
    s.created_by, s.updated_by, s.created_at, s.updated_at;

COMMENT ON VIEW "10_kbio".v_sessions IS
    'Behavioral sessions with dim codes resolved and EAV attrs pivoted. '
    'Pivots: ip_address, user_agent, sdk_version, sdk_platform, total_pulses, '
    'max_drift_score, current_drift_score, end_reason, critical_actions.';

GRANT SELECT ON "10_kbio".v_sessions TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_sessions TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 2. v_devices — device fingerprint read view
--    Pivots all 7 EAV attrs registered for kbio_device (entity_type_id = 2).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_devices AS
SELECT
    d.id,
    d.user_hash,
    d.is_active,
    (d.deleted_at IS NOT NULL)                                                     AS is_deleted,
    -- EAV pivots (entity_type_id = 2 = kbio_device)
    MAX(CASE WHEN ad.code = 'fingerprint_hash'  THEN a.key_text  END)             AS fingerprint_hash,
    MAX(CASE WHEN ad.code = 'first_seen_at'     THEN a.key_text  END)             AS first_seen_at,
    MAX(CASE WHEN ad.code = 'last_seen_at'      THEN a.key_text  END)             AS last_seen_at,
    MAX(CASE WHEN ad.code = 'platform'          THEN a.key_text  END)             AS platform,
    MAX(CASE WHEN ad.code = 'screen_profile'    THEN a.key_jsonb END)             AS screen_profile,
    MAX(CASE WHEN ad.code = 'gpu_profile'       THEN a.key_jsonb END)             AS gpu_profile,
    MAX(CASE WHEN ad.code = 'automation_risk'   THEN a.key_text  END)             AS automation_risk,
    d.created_by,
    d.updated_by,
    d.created_at,
    d.updated_at
FROM "10_kbio"."11_fct_devices" d
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_device')
      AND a.entity_id = d.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    d.id, d.user_hash,
    d.is_active, d.deleted_at,
    d.created_by, d.updated_by, d.created_at, d.updated_at;

COMMENT ON VIEW "10_kbio".v_devices IS
    'Device fingerprint records with EAV attrs pivoted. '
    'Pivots: fingerprint_hash, first_seen_at, last_seen_at, platform, '
    'screen_profile, gpu_profile, automation_risk.';

GRANT SELECT ON "10_kbio".v_devices TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_devices TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 3. v_user_profiles — per-user behavioral baseline read view
--    Resolves baseline_quality dim code.
--    Pivots all 7 EAV attrs registered for kbio_user_profile (entity_type_id = 3).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_user_profiles AS
SELECT
    up.id,
    up.user_hash,
    up.baseline_quality_id,
    bq.code                                                                        AS baseline_quality,
    up.is_active,
    (up.deleted_at IS NOT NULL)                                                    AS is_deleted,
    -- EAV pivots (entity_type_id = 3 = kbio_user_profile)
    MAX(CASE WHEN ad.code = 'centroids'               THEN a.key_jsonb END)        AS centroids,
    MAX(CASE WHEN ad.code = 'zone_transition_matrix'  THEN a.key_jsonb END)        AS zone_transition_matrix,
    MAX(CASE WHEN ad.code = 'credential_profiles'     THEN a.key_jsonb END)        AS credential_profiles,
    MAX(CASE WHEN ad.code = 'profile_maturity'        THEN a.key_text  END)        AS profile_maturity,
    MAX(CASE WHEN ad.code = 'total_sessions'          THEN a.key_text  END)        AS total_sessions,
    MAX(CASE WHEN ad.code = 'last_genuine_session_at' THEN a.key_text  END)        AS last_genuine_session_at,
    MAX(CASE WHEN ad.code = 'encoder_version'         THEN a.key_text  END)        AS encoder_version,
    up.created_by,
    up.updated_by,
    up.created_at,
    up.updated_at
FROM "10_kbio"."12_fct_user_profiles" up
LEFT JOIN "10_kbio"."05_dim_baseline_qualities" bq ON bq.id = up.baseline_quality_id
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_user_profile')
      AND a.entity_id = up.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    up.id, up.user_hash,
    up.baseline_quality_id, bq.code,
    up.is_active, up.deleted_at,
    up.created_by, up.updated_by, up.created_at, up.updated_at;

COMMENT ON VIEW "10_kbio".v_user_profiles IS
    'Per-user behavioral baseline with baseline_quality dim code resolved and '
    'EAV attrs pivoted. Pivots: centroids, zone_transition_matrix, '
    'credential_profiles, profile_maturity, total_sessions, '
    'last_genuine_session_at, encoder_version.';

GRANT SELECT ON "10_kbio".v_user_profiles TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_user_profiles TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 4. v_trusted_entities — trusted entity allowlist read view
--    Resolves entity_type_code from 09_dim_trusted_entity_types.
--    Pivots all 4 EAV attrs registered for kbio_trusted_entity (entity_type_id = 4).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_trusted_entities AS
SELECT
    te.id,
    te.user_hash,
    te.trusted_entity_type_id,
    tet.code                                                                       AS entity_type,
    te.is_active,
    (te.deleted_at IS NOT NULL)                                                    AS is_deleted,
    -- EAV pivots (entity_type_id = 4 = kbio_trusted_entity)
    MAX(CASE WHEN ad.code = 'entity_value'  THEN a.key_text END)                  AS entity_value,
    MAX(CASE WHEN ad.code = 'trust_reason'  THEN a.key_text END)                  AS trust_reason,
    MAX(CASE WHEN ad.code = 'trusted_by'    THEN a.key_text END)                  AS trusted_by,
    MAX(CASE WHEN ad.code = 'expires_at'    THEN a.key_text END)                  AS expires_at,
    te.created_by,
    te.updated_by,
    te.created_at,
    te.updated_at
FROM "10_kbio"."13_fct_trusted_entities" te
LEFT JOIN "10_kbio"."09_dim_trusted_entity_types" tet ON tet.id = te.trusted_entity_type_id
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_trusted_entity')
      AND a.entity_id = te.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    te.id, te.user_hash,
    te.trusted_entity_type_id, tet.code,
    te.is_active, te.deleted_at,
    te.created_by, te.updated_by, te.created_at, te.updated_at;

COMMENT ON VIEW "10_kbio".v_trusted_entities IS
    'Trusted entity allowlist with entity_type dim code resolved and EAV attrs '
    'pivoted. Pivots: entity_value, trust_reason, trusted_by, expires_at.';

GRANT SELECT ON "10_kbio".v_trusted_entities TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_trusted_entities TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 5. v_challenges — behavioral challenge read view
--    Pivots all 10 EAV attrs registered for kbio_challenge (entity_type_id = 5).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_challenges AS
SELECT
    c.id,
    c.session_id,
    c.user_hash,
    c.is_active,
    (c.deleted_at IS NOT NULL)                                                     AS is_deleted,
    -- EAV pivots (entity_type_id = 5 = kbio_challenge)
    MAX(CASE WHEN ad.code = 'purpose'                  THEN a.key_text  END)       AS purpose,
    MAX(CASE WHEN ad.code = 'phrase'                   THEN a.key_text  END)       AS phrase,
    MAX(CASE WHEN ad.code = 'phrase_hash'              THEN a.key_text  END)       AS phrase_hash,
    MAX(CASE WHEN ad.code = 'expected_zone_sequence'   THEN a.key_jsonb END)       AS expected_zone_sequence,
    MAX(CASE WHEN ad.code = 'discriminative_pairs'     THEN a.key_jsonb END)       AS discriminative_pairs,
    MAX(CASE WHEN ad.code = 'pair_weights'             THEN a.key_jsonb END)       AS pair_weights,
    MAX(CASE WHEN ad.code = 'expires_at'               THEN a.key_text  END)       AS expires_at,
    MAX(CASE WHEN ad.code = 'used'                     THEN a.key_text  END)       AS used,
    MAX(CASE WHEN ad.code = 'result_passed'            THEN a.key_text  END)       AS result_passed,
    MAX(CASE WHEN ad.code = 'result_drift_score'       THEN a.key_text  END)       AS result_drift_score,
    c.created_by,
    c.updated_by,
    c.created_at,
    c.updated_at
FROM "10_kbio"."14_fct_challenges" c
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_challenge')
      AND a.entity_id = c.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    c.id, c.session_id, c.user_hash,
    c.is_active, c.deleted_at,
    c.created_by, c.updated_by, c.created_at, c.updated_at;

COMMENT ON VIEW "10_kbio".v_challenges IS
    'Behavioral challenges with EAV attrs pivoted. '
    'Pivots: purpose, phrase, phrase_hash, expected_zone_sequence, '
    'discriminative_pairs, pair_weights, expires_at, used, '
    'result_passed, result_drift_score.';

GRANT SELECT ON "10_kbio".v_challenges TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_challenges TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 6. v_predefined_policies — predefined policy library read view
--    Resolves category_code from 06_dim_policy_categories and
--    default_action_code from 04_dim_drift_actions.
--    Pivots all 7 EAV attrs registered for kbio_predefined_policy (entity_type_id = 6).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_predefined_policies AS
SELECT
    pp.id,
    pp.policy_category_id,
    pc.code                                                                        AS category,
    pp.default_action_id,
    da.code                                                                        AS default_action,
    pp.is_active,
    (pp.deleted_at IS NOT NULL)                                                    AS is_deleted,
    -- EAV pivots (entity_type_id = 6 = kbio_predefined_policy)
    MAX(CASE WHEN ad.code = 'code'            THEN a.key_text  END)                AS code,
    MAX(CASE WHEN ad.code = 'name'            THEN a.key_text  END)                AS name,
    MAX(CASE WHEN ad.code = 'description'     THEN a.key_text  END)                AS description,
    MAX(CASE WHEN ad.code = 'conditions'      THEN a.key_jsonb END)                AS conditions,
    MAX(CASE WHEN ad.code = 'default_config'  THEN a.key_jsonb END)                AS default_config,
    MAX(CASE WHEN ad.code = 'tags'            THEN a.key_text  END)                AS tags,
    MAX(CASE WHEN ad.code = 'version'         THEN a.key_text  END)                AS version,
    pp.created_by,
    pp.updated_by,
    pp.created_at,
    pp.updated_at
FROM "10_kbio"."15_fct_predefined_policies" pp
LEFT JOIN "10_kbio"."06_dim_policy_categories" pc ON pc.id = pp.policy_category_id
LEFT JOIN "10_kbio"."04_dim_drift_actions"     da ON da.id = pp.default_action_id
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_predefined_policy')
      AND a.entity_id = pp.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    pp.id,
    pp.policy_category_id, pc.code,
    pp.default_action_id, da.code,
    pp.is_active, pp.deleted_at,
    pp.created_by, pp.updated_by, pp.created_at, pp.updated_at;

COMMENT ON VIEW "10_kbio".v_predefined_policies IS
    'Predefined policy library with category and default_action dim codes resolved '
    'and EAV attrs pivoted. Pivots: code, name, description, conditions, '
    'default_config, tags, version.';

GRANT SELECT ON "10_kbio".v_predefined_policies TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_predefined_policies TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 7. v_score_events — drift score events with batch_type and drift_action
--    dim codes resolved. No EAV — all signal lives in metadata JSONB.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_score_events AS
SELECT
    e.id,
    e.session_id,
    e.user_hash,
    e.batch_id,
    e.batch_type_id,
    bt.code                                                                        AS batch_type,
    e.drift_action_id,
    da.code                                                                        AS drift_action,
    e.metadata,
    e.created_by,
    e.created_at
FROM "10_kbio"."60_evt_score_events" e
LEFT JOIN "10_kbio"."02_dim_batch_types"  bt ON bt.id = e.batch_type_id
LEFT JOIN "10_kbio"."04_dim_drift_actions" da ON da.id = e.drift_action_id;

COMMENT ON VIEW "10_kbio".v_score_events IS
    'Drift score events with batch_type and drift_action dim codes resolved. '
    'Payload detail lives in metadata JSONB on the underlying evt table.';

GRANT SELECT ON "10_kbio".v_score_events TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_score_events TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 8. v_anomaly_events — anomaly detection events with severity dim code
--    resolved. No EAV — all signal lives in metadata JSONB.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_anomaly_events AS
SELECT
    e.id,
    e.session_id,
    e.user_hash,
    e.alert_severity_id,
    sev.code                                                                       AS severity,
    e.metadata,
    e.created_by,
    e.created_at
FROM "10_kbio"."61_evt_anomaly_events" e
LEFT JOIN "10_kbio"."08_dim_alert_severities" sev ON sev.id = e.alert_severity_id;

COMMENT ON VIEW "10_kbio".v_anomaly_events IS
    'Anomaly detection events with severity dim code resolved. '
    'Anomaly detail lives in metadata JSONB on the underlying evt table.';

GRANT SELECT ON "10_kbio".v_anomaly_events TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_anomaly_events TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 9. v_bot_detection_events — bot signal events passthrough view.
--    No dim joins or EAV — all signal captured directly in metadata JSONB.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_bot_detection_events AS
SELECT
    e.id,
    e.session_id,
    e.user_hash,
    e.metadata,
    e.created_by,
    e.created_at
FROM "10_kbio"."62_evt_bot_detection_events" e;

COMMENT ON VIEW "10_kbio".v_bot_detection_events IS
    'Bot detection events passthrough view. All signal lives in metadata JSONB '
    'on the underlying evt table. No dim codes to resolve.';

GRANT SELECT ON "10_kbio".v_bot_detection_events TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_bot_detection_events TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 10. v_device_fingerprint_events — device fingerprint events passthrough view.
--     No dim joins or EAV — all signal captured directly in metadata JSONB.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_device_fingerprint_events AS
SELECT
    e.id,
    e.session_id,
    e.user_hash,
    e.device_uuid,
    e.metadata,
    e.created_by,
    e.created_at
FROM "10_kbio"."63_evt_device_fingerprint_events" e;

COMMENT ON VIEW "10_kbio".v_device_fingerprint_events IS
    'Device fingerprint events passthrough view. All signal lives in metadata JSONB '
    'on the underlying evt table. No dim codes to resolve.';

GRANT SELECT ON "10_kbio".v_device_fingerprint_events TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_device_fingerprint_events TO tennetctl_write;

-- DOWN =======================================================================
DROP VIEW IF EXISTS "10_kbio".v_device_fingerprint_events;
DROP VIEW IF EXISTS "10_kbio".v_bot_detection_events;
DROP VIEW IF EXISTS "10_kbio".v_anomaly_events;
DROP VIEW IF EXISTS "10_kbio".v_score_events;
DROP VIEW IF EXISTS "10_kbio".v_predefined_policies;
DROP VIEW IF EXISTS "10_kbio".v_challenges;
DROP VIEW IF EXISTS "10_kbio".v_trusted_entities;
DROP VIEW IF EXISTS "10_kbio".v_user_profiles;
DROP VIEW IF EXISTS "10_kbio".v_devices;
DROP VIEW IF EXISTS "10_kbio".v_sessions;
