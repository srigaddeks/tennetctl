-- UP ====
-- Plan 20-06: TOTP backup codes — one-time recovery codes for users who lose their TOTP device.

CREATE TABLE IF NOT EXISTS "03_iam"."28_fct_totp_backup_codes" (
    id              VARCHAR(36)  NOT NULL,
    user_id         VARCHAR(36)  NOT NULL REFERENCES "03_iam"."12_fct_users" (id),
    code_hash       TEXT         NOT NULL,
    consumed_at     TIMESTAMP    NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_28_fct_totp_backup_codes PRIMARY KEY (id)
);

COMMENT ON TABLE  "03_iam"."28_fct_totp_backup_codes" IS 'Argon2id-hashed one-time backup codes for TOTP-enrolled users. Consumed on use; regeneration deletes all old rows and inserts 10 new ones.';
COMMENT ON COLUMN "03_iam"."28_fct_totp_backup_codes".id IS 'UUID v7 primary key.';
COMMENT ON COLUMN "03_iam"."28_fct_totp_backup_codes".user_id IS 'FK to 12_fct_users.';
COMMENT ON COLUMN "03_iam"."28_fct_totp_backup_codes".code_hash IS 'Argon2id hash of the plaintext backup code. Plaintext is returned ONCE at enrollment.';
COMMENT ON COLUMN "03_iam"."28_fct_totp_backup_codes".consumed_at IS 'NULL until the code is used; set on first use. Cannot be reused.';
COMMENT ON COLUMN "03_iam"."28_fct_totp_backup_codes".created_at IS 'When the code was generated.';

CREATE INDEX IF NOT EXISTS idx_28_fct_totp_backup_codes_user
    ON "03_iam"."28_fct_totp_backup_codes" (user_id)
    WHERE consumed_at IS NULL;

-- DOWN ====
DROP INDEX IF EXISTS "03_iam".idx_28_fct_totp_backup_codes_user;
DROP TABLE IF EXISTS "03_iam"."28_fct_totp_backup_codes";
