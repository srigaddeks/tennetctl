-- =============================================================================
-- Migration:   20260410_030_kdemo_schema.sql
-- Module:      kdemo
-- Sequence:    030
-- Depends on:  none (standalone schema, no tennetctl dependency)
-- Description: Create the kdemo schema for the kbio demo site.
--              Standalone — no tennetctl IAM, no kbio EAV, no Valkey.
--              Tables: dim_user_statuses, fct_users, dtl_security_questions.
--              JWT is issued at login; sessions are stateless.
-- =============================================================================

-- UP =========================================================================

CREATE SCHEMA IF NOT EXISTS kdemo;

COMMENT ON SCHEMA kdemo IS
    'Demo site users for the kbio SDK demo. Standalone — no tennetctl dependency. '
    'Auth is JWT-based (stateless). Tables own all user fields directly.';

GRANT USAGE ON SCHEMA kdemo TO tennetctl_read;
GRANT USAGE ON SCHEMA kdemo TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- dim_user_statuses
-- ---------------------------------------------------------------------------
CREATE TABLE kdemo.dim_user_statuses (
    id            SMALLINT  GENERATED ALWAYS AS IDENTITY,
    code          TEXT      NOT NULL,
    label         TEXT      NOT NULL,
    description   TEXT,

    CONSTRAINT pk_kdemo_dim_user_statuses      PRIMARY KEY (id),
    CONSTRAINT uq_kdemo_dim_user_statuses_code UNIQUE (code)
);

COMMENT ON TABLE  kdemo.dim_user_statuses IS 'Lifecycle status for demo site users.';
COMMENT ON COLUMN kdemo.dim_user_statuses.code IS 'Machine-readable status code.';

INSERT INTO kdemo.dim_user_statuses (code, label, description) VALUES
    ('active',    'Active',    'User can sign in.'),
    ('locked',    'Locked',    'Temporarily locked after repeated failures.'),
    ('suspended', 'Suspended', 'Manually disabled. Login blocked.');

GRANT SELECT ON kdemo.dim_user_statuses TO tennetctl_read;
GRANT SELECT ON kdemo.dim_user_statuses TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- fct_users  (all core fields stored directly — no EAV for these)
-- ---------------------------------------------------------------------------
CREATE TABLE kdemo.fct_users (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    username        TEXT        NOT NULL,
    email           TEXT        NOT NULL,
    password_hash   TEXT        NOT NULL,
    phone_number    TEXT,
    mpin_hash       TEXT,
    status_id       SMALLINT    NOT NULL DEFAULT 1,
    deleted_at      TIMESTAMP,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kdemo_fct_users          PRIMARY KEY (id),
    CONSTRAINT uq_kdemo_fct_users_username UNIQUE (username),
    CONSTRAINT uq_kdemo_fct_users_email    UNIQUE (email),
    CONSTRAINT fk_kdemo_fct_users_status   FOREIGN KEY (status_id)
        REFERENCES kdemo.dim_user_statuses (id)
);

COMMENT ON TABLE  kdemo.fct_users IS 'Demo site user accounts. One row per registered user.';
COMMENT ON COLUMN kdemo.fct_users.id            IS 'UUID primary key.';
COMMENT ON COLUMN kdemo.fct_users.username      IS 'Unique login handle.';
COMMENT ON COLUMN kdemo.fct_users.email         IS 'Unique email address.';
COMMENT ON COLUMN kdemo.fct_users.password_hash IS 'bcrypt hash of the login password.';
COMMENT ON COLUMN kdemo.fct_users.phone_number  IS 'Optional mobile/phone number.';
COMMENT ON COLUMN kdemo.fct_users.mpin_hash     IS 'bcrypt hash of the 4–6 digit MPIN.';
COMMENT ON COLUMN kdemo.fct_users.status_id     IS 'FK → dim_user_statuses. 1 = active.';
COMMENT ON COLUMN kdemo.fct_users.deleted_at    IS 'Soft-delete timestamp. NULL = not deleted.';

GRANT SELECT, INSERT, UPDATE ON kdemo.fct_users TO tennetctl_write;
GRANT SELECT                  ON kdemo.fct_users TO tennetctl_read;

-- ---------------------------------------------------------------------------
-- dtl_security_questions  (EAV-style detail table, one row per Q+A per user)
-- ---------------------------------------------------------------------------
CREATE TABLE kdemo.dtl_security_questions (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL,
    position        SMALLINT    NOT NULL,   -- 1, 2, 3
    question        TEXT        NOT NULL,
    answer_hash     TEXT        NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kdemo_dtl_security_questions         PRIMARY KEY (id),
    CONSTRAINT uq_kdemo_dtl_security_questions_pos     UNIQUE (user_id, position),
    CONSTRAINT fk_kdemo_dtl_security_questions_user    FOREIGN KEY (user_id)
        REFERENCES kdemo.fct_users (id) ON DELETE CASCADE,
    CONSTRAINT ck_kdemo_dtl_security_questions_pos     CHECK (position BETWEEN 1 AND 3)
);

COMMENT ON TABLE  kdemo.dtl_security_questions IS
    'Security questions for demo users. Exactly 3 rows per user (positions 1–3). '
    'answer_hash is bcrypt. Used for identity challenge flows in the kbio SDK demo.';
COMMENT ON COLUMN kdemo.dtl_security_questions.position  IS '1-based slot; enforced unique per user.';
COMMENT ON COLUMN kdemo.dtl_security_questions.answer_hash IS 'bcrypt hash of the lowercased trimmed answer.';

GRANT SELECT, INSERT, UPDATE, DELETE ON kdemo.dtl_security_questions TO tennetctl_write;
GRANT SELECT                          ON kdemo.dtl_security_questions TO tennetctl_read;

-- ---------------------------------------------------------------------------
-- v_users  — convenience read view (no password/mpin hashes exposed)
-- ---------------------------------------------------------------------------
CREATE VIEW kdemo.v_users AS
SELECT
    u.id,
    u.username,
    u.email,
    u.phone_number,
    s.code  AS status,
    u.deleted_at,
    u.created_at,
    u.updated_at
FROM kdemo.fct_users u
JOIN kdemo.dim_user_statuses s ON s.id = u.status_id
WHERE u.deleted_at IS NULL;

COMMENT ON VIEW kdemo.v_users IS
    'Safe read view of demo users. Excludes password_hash and mpin_hash.';

GRANT SELECT ON kdemo.v_users TO tennetctl_read;
GRANT SELECT ON kdemo.v_users TO tennetctl_write;

-- DOWN =======================================================================

DROP VIEW  IF EXISTS kdemo.v_users;
DROP TABLE IF EXISTS kdemo.dtl_security_questions;
DROP TABLE IF EXISTS kdemo.fct_users;
DROP TABLE IF EXISTS kdemo.dim_user_statuses;
DROP SCHEMA IF EXISTS kdemo;
