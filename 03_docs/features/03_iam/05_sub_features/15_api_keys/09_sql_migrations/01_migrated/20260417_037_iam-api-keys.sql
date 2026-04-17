-- Migration 037: IAM API keys
--
-- Scoped API keys that allow backend-to-backend calls into tennetctl without
-- a browser session cookie. Token format: "nk_<key_id>.<secret>" where
-- key_id is a 12-char lowercase base32 public prefix and secret is a 32-byte
-- base64url random string hashed with argon2id before storage.
--
-- Scopes are stored as TEXT[] so a single key can be granted multiple scopes
-- (e.g., notify:send + notify:read). Enforced in routes via require_scope().
--
-- Revocation is soft: revoked_at IS NOT NULL invalidates the key immediately
-- but keeps history for audit. deleted_at is a second soft-delete layer used
-- by the standard tennetctl lifecycle.

-- UP ====

CREATE TABLE "03_iam"."28_fct_iam_api_keys" (
    id             VARCHAR(36) NOT NULL,
    org_id         VARCHAR(36) NOT NULL,
    user_id        VARCHAR(36) NOT NULL,
    key_id         TEXT        NOT NULL,
    secret_hash    TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    scopes         TEXT[]      NOT NULL DEFAULT '{}',
    last_used_at   TIMESTAMP   NULL,
    expires_at     TIMESTAMP   NULL,
    revoked_at     TIMESTAMP   NULL,
    is_active      BOOLEAN     NOT NULL DEFAULT TRUE,
    is_test        BOOLEAN     NOT NULL DEFAULT FALSE,
    deleted_at     TIMESTAMP   NULL,
    created_by     VARCHAR(36) NOT NULL,
    updated_by     VARCHAR(36) NOT NULL,
    created_at     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_api_keys        PRIMARY KEY (id),
    CONSTRAINT uq_iam_api_keys_key_id UNIQUE (key_id)
);

COMMENT ON TABLE  "03_iam"."28_fct_iam_api_keys" IS 'Scoped API keys for machine-to-machine authentication. Secret stored as argon2id hash; full token only shown once at create time.';
COMMENT ON COLUMN "03_iam"."28_fct_iam_api_keys".key_id       IS 'Public 12-char base32 prefix after "nk_". Used for fast lookup before argon2 verify.';
COMMENT ON COLUMN "03_iam"."28_fct_iam_api_keys".secret_hash  IS 'argon2id hash of the secret half of the token. Never returned by the API.';
COMMENT ON COLUMN "03_iam"."28_fct_iam_api_keys".scopes       IS 'Permission scopes granted to this key, e.g. {"notify:send","notify:read"}.';
COMMENT ON COLUMN "03_iam"."28_fct_iam_api_keys".last_used_at IS 'Updated best-effort (no transaction cost) by the Bearer-auth middleware on successful auth.';
COMMENT ON COLUMN "03_iam"."28_fct_iam_api_keys".revoked_at   IS 'When the key was revoked. Any non-null value invalidates auth immediately.';

CREATE INDEX idx_iam_api_keys_user ON "03_iam"."28_fct_iam_api_keys" (org_id, user_id)
    WHERE revoked_at IS NULL AND deleted_at IS NULL;

-- Read view: excludes secret_hash, filters soft-deleted rows.
CREATE VIEW "03_iam"."v_iam_api_keys" AS
SELECT
    id, org_id, user_id, key_id, label, scopes,
    last_used_at, expires_at, revoked_at,
    is_active, is_test,
    created_by, updated_by, created_at, updated_at
FROM "03_iam"."28_fct_iam_api_keys"
WHERE deleted_at IS NULL;

COMMENT ON VIEW "03_iam"."v_iam_api_keys" IS 'Read path for API keys. secret_hash never leaves the DB via this view.';

-- DOWN ====
DROP VIEW  IF EXISTS "03_iam"."v_iam_api_keys";
DROP INDEX IF EXISTS "03_iam"."idx_iam_api_keys_user";
DROP TABLE IF EXISTS "03_iam"."28_fct_iam_api_keys";
