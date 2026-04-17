-- Migration 030: IAM OTP codes + TOTP credentials
-- Sub-feature: 12_otp

-- UP ====

-- Email OTP codes: 6-digit codes with attempt counter
CREATE TABLE IF NOT EXISTS "03_iam"."23_fct_iam_otp_codes" (
    id              VARCHAR(36)  NOT NULL,
    user_id         VARCHAR(36)  NOT NULL
        CONSTRAINT fk_otp_codes_user
            REFERENCES "03_iam"."12_fct_users"(id),
    email           TEXT         NOT NULL,
    code_hash       TEXT         NOT NULL,
    attempts        SMALLINT     NOT NULL DEFAULT 0,
    expires_at      TIMESTAMP    NOT NULL,
    consumed_at     TIMESTAMP    NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_otp_codes PRIMARY KEY (id)
);

COMMENT ON TABLE  "03_iam"."23_fct_iam_otp_codes"
    IS '6-digit email OTP codes. Consumed on verify; 3-attempt limit enforced in service.';

CREATE INDEX IF NOT EXISTS idx_otp_codes_email_created
    ON "03_iam"."23_fct_iam_otp_codes" (email, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_otp_codes_user_id
    ON "03_iam"."23_fct_iam_otp_codes" (user_id);

-- TOTP credentials: RFC 6238 authenticator app secrets per device
CREATE TABLE IF NOT EXISTS "03_iam"."24_fct_iam_totp_credentials" (
    id              VARCHAR(36)  NOT NULL,
    user_id         VARCHAR(36)  NOT NULL
        CONSTRAINT fk_totp_user
            REFERENCES "03_iam"."12_fct_users"(id),
    device_name     TEXT         NOT NULL DEFAULT 'Authenticator',
    secret_ciphertext TEXT       NOT NULL,
    secret_dek      TEXT         NOT NULL,
    secret_nonce    TEXT         NOT NULL,
    secret_version  INTEGER      NOT NULL DEFAULT 1,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    last_used_at    TIMESTAMP    NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP    NULL,

    CONSTRAINT pk_totp_credentials PRIMARY KEY (id)
);

COMMENT ON TABLE  "03_iam"."24_fct_iam_totp_credentials"
    IS 'TOTP secrets per device. Secret envelope-encrypted via vault root key. One row per enrolled authenticator.';

CREATE INDEX IF NOT EXISTS idx_totp_creds_user_id
    ON "03_iam"."24_fct_iam_totp_credentials" (user_id)
    WHERE deleted_at IS NULL;

-- DOWN ====

DROP INDEX IF EXISTS "03_iam"."idx_otp_codes_email_created";
DROP INDEX IF EXISTS "03_iam"."idx_otp_codes_user_id";
DROP TABLE IF EXISTS "03_iam"."23_fct_iam_otp_codes";
DROP INDEX IF EXISTS "03_iam"."idx_totp_creds_user_id";
DROP TABLE IF EXISTS "03_iam"."24_fct_iam_totp_credentials";
