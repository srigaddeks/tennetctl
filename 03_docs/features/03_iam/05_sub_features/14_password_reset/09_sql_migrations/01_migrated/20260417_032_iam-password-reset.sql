-- UP ====
-- Migration 032: Password reset tokens table

CREATE TABLE IF NOT EXISTS "03_iam"."27_fct_iam_password_reset_tokens" (
    id          VARCHAR(36)  NOT NULL,
    user_id     VARCHAR(36)  NOT NULL,
    email       TEXT         NOT NULL,
    token_hash  TEXT         NOT NULL,
    ip_address  TEXT         NULL,
    expires_at  TIMESTAMP    NOT NULL,
    consumed_at TIMESTAMP    NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_password_reset_tokens PRIMARY KEY (id),
    CONSTRAINT fk_iam_password_reset_tokens_user FOREIGN KEY (user_id) REFERENCES "03_iam"."12_fct_users" (id)
);

COMMENT ON TABLE "03_iam"."27_fct_iam_password_reset_tokens" IS 'HMAC-signed password reset tokens. Consumed once, 15-min TTL.';
COMMENT ON COLUMN "03_iam"."27_fct_iam_password_reset_tokens".token_hash IS 'HMAC-SHA256 of the raw token using a vault signing key.';

CREATE INDEX idx_iam_pw_reset_email_rate ON "03_iam"."27_fct_iam_password_reset_tokens" (email, created_at DESC);

-- DOWN ====
DROP INDEX IF EXISTS "03_iam"."idx_iam_pw_reset_email_rate";
DROP TABLE IF EXISTS "03_iam"."27_fct_iam_password_reset_tokens";
