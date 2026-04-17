-- UP ====
-- Migration 056: Email verification tokens table + email_verified_at attr def

-- Register attr_def for email_verified_at on user entity (entity_type_id=3)
INSERT INTO "03_iam"."20_dtl_attr_defs"
    (entity_type_id, code, label, value_type, description)
VALUES
    (3, 'email_verified_at', 'Email Verified At', 'text',
     'ISO-8601 UTC timestamp when the user verified their email address. NULL = unverified.')
ON CONFLICT (entity_type_id, code) DO NOTHING;

-- Email verification tokens
CREATE TABLE IF NOT EXISTS "03_iam"."29_fct_iam_email_verifications" (
    id          VARCHAR(36)  NOT NULL,
    user_id     VARCHAR(36)  NOT NULL,
    token_hash  TEXT         NOT NULL,
    ttl_at      TIMESTAMP    NOT NULL,
    consumed_at TIMESTAMP    NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_email_verifications PRIMARY KEY (id),
    CONSTRAINT fk_iam_email_verifications_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users" (id)
);

COMMENT ON TABLE  "03_iam"."29_fct_iam_email_verifications" IS 'HMAC-SHA256 email verification tokens. Consumed once, 24-hour TTL.';
COMMENT ON COLUMN "03_iam"."29_fct_iam_email_verifications".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."29_fct_iam_email_verifications".token_hash IS 'HMAC-SHA256 of the raw token using vault signing key.';
COMMENT ON COLUMN "03_iam"."29_fct_iam_email_verifications".ttl_at IS 'Token expiry timestamp (CURRENT_TIMESTAMP + 24h).';
COMMENT ON COLUMN "03_iam"."29_fct_iam_email_verifications".consumed_at IS 'Non-null after token is used successfully.';

CREATE INDEX idx_iam_email_verif_user ON "03_iam"."29_fct_iam_email_verifications" (user_id, consumed_at);

-- DOWN ====
DROP INDEX IF EXISTS "03_iam"."idx_iam_email_verif_user";
DROP TABLE IF EXISTS "03_iam"."29_fct_iam_email_verifications";
DELETE FROM "03_iam"."20_dtl_attr_defs"
    WHERE entity_type_id = 3 AND code = 'email_verified_at';
