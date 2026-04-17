-- UP ====

-- iam.credentials sub-feature: dtl_credentials.
-- Fixed-schema dtl table (NOT EAV) — one row per user holding the argon2id
-- password hash. Pepper is fetched from the vault (auth.argon2.pepper) at
-- hash + verify time; we never store the pepper here.
--
-- Why a fixed table instead of dtl_attrs? Password hash needs strict access
-- control (no SELECT path through v_users), explicit FK cascade on user delete,
-- and a single mutation point. EAV would scatter that across attr_def lookups.
--
-- Phase 8 (auth) consumes this via iam.credentials service. No HTTP routes.

CREATE TABLE "03_iam"."22_dtl_credentials" (
    user_id        VARCHAR(36) NOT NULL,
    password_hash  TEXT NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_dtl_credentials PRIMARY KEY (user_id),
    CONSTRAINT fk_iam_dtl_credentials_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users"(id) ON DELETE CASCADE
);

COMMENT ON TABLE  "03_iam"."22_dtl_credentials" IS 'Argon2id password hashes for email_password users. One row per user. Pepper applied at hash + verify time, fetched from vault key auth.argon2.pepper.';
COMMENT ON COLUMN "03_iam"."22_dtl_credentials".user_id IS 'FK fct_users.id. PK — at most one credential per user.';
COMMENT ON COLUMN "03_iam"."22_dtl_credentials".password_hash IS 'PHC-encoded argon2id hash. Includes algorithm + parameters + salt.';
COMMENT ON COLUMN "03_iam"."22_dtl_credentials".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."22_dtl_credentials".updated_at IS 'Last update timestamp (set by app on password change).';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."22_dtl_credentials";
