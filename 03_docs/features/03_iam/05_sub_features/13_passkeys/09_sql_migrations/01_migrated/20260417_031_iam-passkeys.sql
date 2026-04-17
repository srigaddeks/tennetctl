-- UP ====
-- Migration 031: WebAuthn passkey credentials + challenges tables

-- Short-lived challenge store (registration + authentication ceremonies)
CREATE TABLE IF NOT EXISTS "03_iam"."25_fct_iam_passkey_challenges" (
    id          VARCHAR(36) NOT NULL,
    user_id     VARCHAR(36) NULL,         -- NULL for usernameless auth begin
    challenge   TEXT        NOT NULL,      -- base64url-encoded
    purpose     TEXT        NOT NULL,      -- 'registration' | 'authentication'
    expires_at  TIMESTAMP   NOT NULL,
    consumed_at TIMESTAMP   NULL,
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_passkey_challenges PRIMARY KEY (id),
    CONSTRAINT chk_iam_passkey_challenges_purpose CHECK (purpose IN ('registration', 'authentication'))
);

COMMENT ON TABLE "03_iam"."25_fct_iam_passkey_challenges" IS 'Short-lived WebAuthn ceremony challenges. Consumed once and discarded.';
COMMENT ON COLUMN "03_iam"."25_fct_iam_passkey_challenges".challenge IS 'base64url-encoded challenge bytes sent to client.';
COMMENT ON COLUMN "03_iam"."25_fct_iam_passkey_challenges".purpose IS 'Ceremony type: registration or authentication.';

CREATE INDEX idx_iam_passkey_challenges_user ON "03_iam"."25_fct_iam_passkey_challenges" (user_id, created_at DESC)
    WHERE consumed_at IS NULL;
CREATE INDEX idx_iam_passkey_challenges_expiry ON "03_iam"."25_fct_iam_passkey_challenges" (expires_at)
    WHERE consumed_at IS NULL;

-- Stored WebAuthn credentials (one user may have multiple passkeys)
CREATE TABLE IF NOT EXISTS "03_iam"."26_fct_iam_passkey_credentials" (
    id              VARCHAR(36) NOT NULL,
    user_id         VARCHAR(36) NOT NULL,
    credential_id   TEXT        NOT NULL,  -- base64url-encoded credential ID from authenticator
    public_key      TEXT        NOT NULL,  -- base64url-encoded COSE public key
    aaguid          TEXT        NOT NULL DEFAULT '',
    sign_count      INTEGER     NOT NULL DEFAULT 0,
    device_name     TEXT        NOT NULL DEFAULT 'Passkey',
    last_used_at    TIMESTAMP   NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP   NULL,
    CONSTRAINT pk_iam_passkey_credentials PRIMARY KEY (id),
    CONSTRAINT fk_iam_passkey_credentials_user FOREIGN KEY (user_id) REFERENCES "03_iam"."12_fct_users" (id),
    CONSTRAINT uq_iam_passkey_credentials_cred_id UNIQUE (credential_id)
);

COMMENT ON TABLE "03_iam"."26_fct_iam_passkey_credentials" IS 'WebAuthn/FIDO2 passkey credentials. Multiple per user, device-named.';
COMMENT ON COLUMN "03_iam"."26_fct_iam_passkey_credentials".credential_id IS 'base64url-encoded opaque handle from authenticator.';
COMMENT ON COLUMN "03_iam"."26_fct_iam_passkey_credentials".public_key IS 'base64url-encoded COSE key (stored by py_webauthn as bytes).';
COMMENT ON COLUMN "03_iam"."26_fct_iam_passkey_credentials".sign_count IS 'Monotonic counter for clone detection.';

CREATE INDEX idx_iam_passkey_credentials_user ON "03_iam"."26_fct_iam_passkey_credentials" (user_id, created_at DESC)
    WHERE deleted_at IS NULL;

-- DOWN ====
DROP INDEX IF EXISTS "03_iam"."idx_iam_passkey_credentials_user";
DROP INDEX IF EXISTS "03_iam"."idx_iam_passkey_challenges_expiry";
DROP INDEX IF EXISTS "03_iam"."idx_iam_passkey_challenges_user";
DROP TABLE IF EXISTS "03_iam"."26_fct_iam_passkey_credentials";
DROP TABLE IF EXISTS "03_iam"."25_fct_iam_passkey_challenges";
