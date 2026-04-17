-- Migration 029: IAM magic-link tokens
-- Sub-feature: 11_magic_link
-- Scope: 03_iam schema

-- UP ====

CREATE TABLE IF NOT EXISTS "03_iam"."19_fct_iam_magic_link_tokens" (
    id              VARCHAR(36)  NOT NULL,
    user_id         VARCHAR(36)  NOT NULL
        CONSTRAINT fk_magic_link_user_id
            REFERENCES "03_iam"."12_fct_users"(id),
    email           TEXT         NOT NULL,
    token_hash      TEXT         NOT NULL,
    expires_at      TIMESTAMP    NOT NULL,
    consumed_at     TIMESTAMP    NULL,
    ip_address      TEXT         NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_magic_link_tokens PRIMARY KEY (id),
    CONSTRAINT uq_magic_link_token_hash UNIQUE (token_hash)
);

COMMENT ON TABLE  "03_iam"."19_fct_iam_magic_link_tokens"
    IS 'Single-use HMAC-signed tokens for magic-link email sign-in. Consumed on first use; expired tokens are never valid.';
COMMENT ON COLUMN "03_iam"."19_fct_iam_magic_link_tokens".token_hash
    IS 'HMAC-SHA256 hex digest of the raw token (stored; never store raw token).';
COMMENT ON COLUMN "03_iam"."19_fct_iam_magic_link_tokens".consumed_at
    IS 'Set when the token is exchanged for a session. NULL = unused.';

CREATE INDEX IF NOT EXISTS idx_magic_link_email_created
    ON "03_iam"."19_fct_iam_magic_link_tokens" (email, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_magic_link_user_id
    ON "03_iam"."19_fct_iam_magic_link_tokens" (user_id);

-- DOWN ====

DROP INDEX IF EXISTS "03_iam"."idx_magic_link_email_created";
DROP INDEX IF EXISTS "03_iam"."idx_magic_link_user_id";
DROP TABLE IF EXISTS "03_iam"."19_fct_iam_magic_link_tokens";
