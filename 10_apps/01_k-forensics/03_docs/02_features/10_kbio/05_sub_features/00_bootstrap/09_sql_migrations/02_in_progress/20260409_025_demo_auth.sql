-- =============================================================================
-- Migration:   20260409_025_demo_auth.sql
-- Module:      10_kbio
-- Sub-feature: 00_bootstrap
-- Sequence:    025
-- Depends on:  020 (10_kbio/00_bootstrap), 021 (10_kbio/tables)
-- Description: Demo authentication system for the kbio demo site. Adds dim
--              tables for demo user statuses and identity challenge types,
--              a fact table for demo users, new EAV attr defs, and a read view.
--              This is demo-only — not production IAM.
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- 09_dim_demo_user_statuses
-- Lifecycle states for demo site user accounts.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."09_dim_demo_user_statuses" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_demo_user_statuses       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_demo_user_statuses_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."09_dim_demo_user_statuses" IS
    'Lifecycle status for demo site user accounts. active = can log in; '
    'locked = temporarily locked after failed challenges; suspended = '
    'manually disabled by admin.';
COMMENT ON COLUMN "10_kbio"."09_dim_demo_user_statuses".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."09_dim_demo_user_statuses".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."09_dim_demo_user_statuses".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."09_dim_demo_user_statuses".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."09_dim_demo_user_statuses".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."09_dim_demo_user_statuses" (code, label, description) VALUES
    ('active',    'Active',    'User account is active and can authenticate.'),
    ('locked',    'Locked',    'Account temporarily locked due to repeated failed identity challenges.'),
    ('suspended', 'Suspended', 'Account suspended by an administrator. Login is blocked.');

GRANT SELECT ON "10_kbio"."09_dim_demo_user_statuses" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."09_dim_demo_user_statuses" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 09_dim_identity_challenge_types
-- Types of knowledge-based identity challenges that can be issued.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."09_dim_identity_challenge_types" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_identity_challenge_types       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_identity_challenge_types_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."09_dim_identity_challenge_types" IS
    'Registry of knowledge-based identity challenge types. These are '
    'separate from behavioral TOTP challenges — they verify identity via '
    'something the user knows (MPIN, security answers, mobile code).';
COMMENT ON COLUMN "10_kbio"."09_dim_identity_challenge_types".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."09_dim_identity_challenge_types".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."09_dim_identity_challenge_types".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."09_dim_identity_challenge_types".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."09_dim_identity_challenge_types".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."09_dim_identity_challenge_types" (code, label, description) VALUES
    ('mpin',                'MPIN',                'User enters their 4–6 digit personal identification number.'),
    ('mobile_verify',       'Mobile Verification', 'User enters a code sent to their registered mobile number (demo: code is always 123456).'),
    ('security_question_1', 'Security Question 1', 'User answers their first registered security question.'),
    ('security_question_2', 'Security Question 2', 'User answers their second registered security question.'),
    ('security_question_3', 'Security Question 3', 'User answers their third registered security question.');

GRANT SELECT ON "10_kbio"."09_dim_identity_challenge_types" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."09_dim_identity_challenge_types" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- New entity type: kbio_demo_user (id=8)
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."06_dim_entity_types" (code, label, description) VALUES
    ('kbio_demo_user', 'kBio Demo User', 'A demo site user account with credentials and identity challenge secrets.');

-- ---------------------------------------------------------------------------
-- 17_fct_demo_users — Demo site user accounts
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."17_fct_demo_users" (
    id          VARCHAR(36)   NOT NULL,
    user_hash   VARCHAR(64)   NOT NULL,
    status_id   SMALLINT      NOT NULL DEFAULT 1,
    is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
    is_test     BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at  TIMESTAMP,
    created_by  VARCHAR(36)   NOT NULL,
    updated_by  VARCHAR(36)   NOT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kbio_fct_demo_users              PRIMARY KEY (id),
    CONSTRAINT uq_kbio_fct_demo_users_user_hash    UNIQUE (user_hash),
    CONSTRAINT fk_kbio_fct_demo_users_status       FOREIGN KEY (status_id)
                                                    REFERENCES "10_kbio"."09_dim_demo_user_statuses" (id)
);

CREATE INDEX idx_kbio_fct_demo_users_created_at ON "10_kbio"."17_fct_demo_users" (created_at DESC);

COMMENT ON TABLE  "10_kbio"."17_fct_demo_users" IS
    'Demo site user accounts. user_hash is SHA-256(username) consistent with '
    'kbio behavioral tracking. Credentials and challenge secrets stored in EAV. '
    'This is demo-only — not production IAM.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".id          IS 'UUID v7 primary key.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".user_hash   IS 'SHA-256 hash of the username. Scope/routing column for fast lookup.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".status_id   IS 'FK → 09_dim_demo_user_statuses. Account lifecycle state.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".is_active   IS 'FALSE when account is deactivated.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".is_test     IS 'TRUE for synthetic test accounts.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".deleted_at  IS 'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".created_by  IS 'UUID of the actor that created this row.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".updated_by  IS 'UUID of the actor that last updated this row.';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".created_at  IS 'Row creation timestamp (UTC).';
COMMENT ON COLUMN "10_kbio"."17_fct_demo_users".updated_at  IS 'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "10_kbio"."17_fct_demo_users" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "10_kbio"."17_fct_demo_users" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- New attr_defs for kbio_demo_user (entity_type_id resolved via JOIN)
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."07_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('kbio_demo_user', 'username',               'Username',               'Plaintext display username.',                                            'key_text'),
    ('kbio_demo_user', 'email',                  'Email',                  'Email address for the demo account.',                                    'key_text'),
    ('kbio_demo_user', 'password_hash',          'Password Hash',          'bcrypt hash of the user password.',                                      'key_text'),
    ('kbio_demo_user', 'mobile_number',          'Mobile Number',          'Registered mobile number for mobile verification challenge.',             'key_text'),
    ('kbio_demo_user', 'mpin_hash',              'MPIN Hash',              'bcrypt hash of the 4–6 digit MPIN.',                                     'key_text'),
    ('kbio_demo_user', 'security_q1',            'Security Question 1',    'Text of the first security question.',                                   'key_text'),
    ('kbio_demo_user', 'security_a1_hash',       'Security Answer 1 Hash', 'bcrypt hash of the first security answer (lowercased, trimmed).',        'key_text'),
    ('kbio_demo_user', 'security_q2',            'Security Question 2',    'Text of the second security question.',                                  'key_text'),
    ('kbio_demo_user', 'security_a2_hash',       'Security Answer 2 Hash', 'bcrypt hash of the second security answer (lowercased, trimmed).',       'key_text'),
    ('kbio_demo_user', 'security_q3',            'Security Question 3',    'Text of the third security question.',                                   'key_text'),
    ('kbio_demo_user', 'security_a3_hash',       'Security Answer 3 Hash', 'bcrypt hash of the third security answer (lowercased, trimmed).',        'key_text'),
    ('kbio_demo_user', 'failed_challenge_count', 'Failed Challenge Count', 'Rolling count of failed identity challenges since last reset.',           'key_text'),
    ('kbio_demo_user', 'last_challenge_at',      'Last Challenge At',      'ISO-8601 timestamp of the last identity challenge issued to this user.', 'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "10_kbio"."06_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- New attr_defs for kbio_challenge (identity challenge extensions)
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."07_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('kbio_challenge', 'challenge_category',       'Challenge Category',       'Distinguishes behavioral vs identity challenges.',                     'key_text'),
    ('kbio_challenge', 'identity_challenge_type',  'Identity Challenge Type',  'Which identity challenge type was issued (mpin, mobile_verify, etc.).','key_text'),
    ('kbio_challenge', 'attempts_remaining',       'Attempts Remaining',       'Countdown of verification attempts left (starts at 3).',               'key_text'),
    ('kbio_challenge', 'challenge_approved',       'Challenge Approved',       'Boolean string — whether identity was confirmed (true/false).',        'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "10_kbio"."06_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- v_demo_users — Read view with EAV pivots and status resolution
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
    'security_q1–q3, security_a1_hash–a3_hash, failed_challenge_count, last_challenge_at.';

GRANT SELECT ON "10_kbio".v_demo_users TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_demo_users TO tennetctl_write;

-- DOWN =======================================================================

DROP VIEW  IF EXISTS "10_kbio".v_demo_users;
DROP TABLE IF EXISTS "10_kbio"."17_fct_demo_users";

-- Remove EAV attr defs for kbio_demo_user
DELETE FROM "10_kbio"."07_dim_attr_defs"
WHERE entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_demo_user');

-- Remove identity challenge attr defs
DELETE FROM "10_kbio"."07_dim_attr_defs"
WHERE entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_challenge')
  AND code IN ('challenge_category', 'identity_challenge_type', 'attempts_remaining', 'challenge_approved');

-- Remove entity type
DELETE FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_demo_user';

DROP TABLE IF EXISTS "10_kbio"."09_dim_identity_challenge_types";
DROP TABLE IF EXISTS "10_kbio"."09_dim_demo_user_statuses";
