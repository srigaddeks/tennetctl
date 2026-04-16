-- OTP codes table for time-limited one-time passwords
-- Used for: email OTP login, SMS OTP (future), 2FA flows
-- Separate from auth challenges (which are token-based) — OTP codes are short numeric/alphanumeric

CREATE TABLE IF NOT EXISTS "03_auth_manage"."12_trx_otp_codes" (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key      TEXT        NOT NULL DEFAULT 'default',
    user_id         UUID        NULL,          -- NULL for pre-auth (email not yet looked up)
    channel         TEXT        NOT NULL,      -- 'email' | 'sms' | 'authenticator'
    purpose         TEXT        NOT NULL,      -- 'login' | 'verify_email' | 'verify_phone' | '2fa' | 'password_reset'
    target_value    TEXT        NOT NULL,      -- email address or phone number
    code_hash       TEXT        NOT NULL,      -- argon2/bcrypt hash of the OTP code
    expires_at      TIMESTAMPTZ NOT NULL,
    consumed_at     TIMESTAMPTZ NULL,          -- set when successfully used
    invalidated_at  TIMESTAMPTZ NULL,          -- set when explicitly cancelled (new code issued)
    attempt_count   INTEGER     NOT NULL DEFAULT 0,
    max_attempts    INTEGER     NOT NULL DEFAULT 5,
    client_ip       TEXT        NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookup by target + purpose (pre-auth path where user_id is unknown)
CREATE INDEX IF NOT EXISTS idx_otp_codes_target_purpose
    ON "03_auth_manage"."12_trx_otp_codes" (target_value, purpose, tenant_key)
    WHERE consumed_at IS NULL AND invalidated_at IS NULL;

-- Index for user-id lookup (post-auth 2FA path)
CREATE INDEX IF NOT EXISTS idx_otp_codes_user_purpose
    ON "03_auth_manage"."12_trx_otp_codes" (user_id, purpose)
    WHERE user_id IS NOT NULL AND consumed_at IS NULL AND invalidated_at IS NULL;

-- Index for expiry cleanup
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires_at
    ON "03_auth_manage"."12_trx_otp_codes" (expires_at)
    WHERE consumed_at IS NULL AND invalidated_at IS NULL;

COMMENT ON TABLE "03_auth_manage"."12_trx_otp_codes" IS
    'Short-lived OTP codes for email/SMS verification and login flows. '
    'Expiry is configurable via OTP_EXPIRY_MINUTES env var (default 10 min). '
    'Max attempts enforced to prevent brute force. Invalidated when a new code is issued.';
