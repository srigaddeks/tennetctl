-- Schema created in 20260313_a_create-all-schemas.sql

-- ─────────────────────────────────────────────────────────────────────────
-- DIMENSION TABLES  (02, 04, 06, 07)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."02_dim_challenge_types" (
    id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_02_dim_challenge_types PRIMARY KEY (id),
    CONSTRAINT uq_02_dim_challenge_types_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."04_dim_user_property_keys" (
    id UUID NOT NULL,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    data_type VARCHAR(30) NOT NULL DEFAULT 'string',
    is_pii BOOLEAN NOT NULL DEFAULT FALSE,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_04_dim_user_property_keys PRIMARY KEY (id),
    CONSTRAINT uq_04_dim_user_property_keys_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."06_dim_account_types" (
    id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_06_dim_account_types PRIMARY KEY (id),
    CONSTRAINT uq_06_dim_account_types_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."07_dim_account_property_keys" (
    id UUID NOT NULL,
    account_type_code VARCHAR(50) NOT NULL,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    is_secret BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_07_dim_account_property_keys PRIMARY KEY (id),
    CONSTRAINT fk_07_dim_account_property_keys_account_type FOREIGN KEY (account_type_code)
        REFERENCES "03_auth_manage"."06_dim_account_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT uq_07_dim_account_property_keys_type_code UNIQUE (account_type_code, code)
);

-- ─────────────────────────────────────────────────────────────────────────
-- FACT TABLE  (03)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."03_fct_users" (
    id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    user_code VARCHAR(64) NOT NULL,
    account_status VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_test BOOLEAN NOT NULL DEFAULT FALSE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    deleted_at TIMESTAMP NULL,
    deleted_by UUID NULL,
    last_login_at TIMESTAMP NULL,
    CONSTRAINT pk_03_fct_users PRIMARY KEY (id),
    CONSTRAINT uq_03_fct_users_user_code UNIQUE (user_code)
);

-- ─────────────────────────────────────────────────────────────────────────
-- DETAIL / EAV TABLES  (05, 08, 09)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."05_dtl_user_properties" (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    property_key VARCHAR(80) NOT NULL,
    property_value TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    CONSTRAINT pk_05_dtl_user_properties PRIMARY KEY (id),
    CONSTRAINT fk_05_dtl_user_properties_user_id FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_05_dtl_user_properties_property_key FOREIGN KEY (property_key)
        REFERENCES "03_auth_manage"."04_dim_user_property_keys" (code)
        ON DELETE RESTRICT,
    CONSTRAINT uq_05_dtl_user_properties_user_key UNIQUE (user_id, property_key)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."08_dtl_user_accounts" (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    account_type_code VARCHAR(50) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    deleted_at TIMESTAMP NULL,
    deleted_by UUID NULL,
    CONSTRAINT pk_08_dtl_user_accounts PRIMARY KEY (id),
    CONSTRAINT fk_08_dtl_user_accounts_user_id FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_08_dtl_user_accounts_account_type FOREIGN KEY (account_type_code)
        REFERENCES "03_auth_manage"."06_dim_account_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT uq_08_dtl_user_accounts_user_type UNIQUE (user_id, account_type_code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."09_dtl_user_account_properties" (
    id UUID NOT NULL,
    user_account_id UUID NOT NULL,
    property_key VARCHAR(80) NOT NULL,
    property_value TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_09_dtl_user_account_properties PRIMARY KEY (id),
    CONSTRAINT fk_09_dtl_user_account_properties_account FOREIGN KEY (user_account_id)
        REFERENCES "03_auth_manage"."08_dtl_user_accounts" (id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_09_dtl_user_account_properties_account_key UNIQUE (user_account_id, property_key)
);

-- ─────────────────────────────────────────────────────────────────────────
-- TRANSACTION TABLES  (10, 11, 12)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."10_trx_auth_sessions" (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    refresh_token_hash VARCHAR(128) NOT NULL,
    refresh_token_expires_at TIMESTAMP NOT NULL,
    rotated_at TIMESTAMP NULL,
    revoked_at TIMESTAMP NULL,
    revocation_reason VARCHAR(100) NULL,
    client_ip VARCHAR(64) NULL,
    user_agent VARCHAR(512) NULL,
    rotation_counter INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_10_trx_auth_sessions PRIMARY KEY (id),
    CONSTRAINT fk_10_trx_auth_sessions_user_id FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."11_trx_login_attempts" (
    id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    normalized_identifier VARCHAR(320) NOT NULL,
    identity_type_code VARCHAR(50) NULL,
    user_id UUID NULL,
    outcome VARCHAR(50) NOT NULL,
    failure_reason VARCHAR(100) NULL,
    client_ip VARCHAR(64) NULL,
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_11_trx_login_attempts PRIMARY KEY (id),
    CONSTRAINT fk_11_trx_login_attempts_user_id FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."12_trx_auth_challenges" (
    id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    user_id UUID NULL,
    challenge_type_code VARCHAR(50) NOT NULL,
    target_value VARCHAR(320) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    consumed_at TIMESTAMP NULL,
    requested_ip VARCHAR(64) NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_12_trx_auth_challenges PRIMARY KEY (id),
    CONSTRAINT fk_12_trx_auth_challenges_user_id FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT
);

-- ─────────────────────────────────────────────────────────────────────────
-- SEED DATA
-- ─────────────────────────────────────────────────────────────────────────

-- Challenge types
INSERT INTO "03_auth_manage"."02_dim_challenge_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000011', 'password_reset', 'Password Reset', 'One-time password reset challenge', 10, TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."02_dim_challenge_types" WHERE code = 'password_reset');

INSERT INTO "03_auth_manage"."02_dim_challenge_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000012', 'email_verification', 'Email Verification', 'One-time email verification challenge', 20, TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."02_dim_challenge_types" WHERE code = 'email_verification');

-- User property keys
INSERT INTO "03_auth_manage"."04_dim_user_property_keys" (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
SELECT v.id::UUID, v.code, v.name, v.description, v.data_type, v.is_pii, v.is_required, v.sort_order, TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
FROM (VALUES
    ('00000000-0000-0000-0001-000000000001', 'email',          'Email Address',   'Primary email identifier',                'email',   TRUE,  TRUE,  10),
    ('00000000-0000-0000-0001-000000000002', 'username',       'Username',        'Optional alternate display identifier',   'string',  FALSE, FALSE, 20),
    ('00000000-0000-0000-0001-000000000003', 'display_name',   'Display Name',    'User display name',                       'string',  FALSE, FALSE, 30),
    ('00000000-0000-0000-0001-000000000004', 'email_verified', 'Email Verified',  'Whether the email has been verified',     'boolean', FALSE, FALSE, 40),
    ('00000000-0000-0000-0001-000000000005', 'timezone',       'Timezone',        'Preferred IANA timezone',                 'string',  FALSE, FALSE, 50),
    ('00000000-0000-0000-0001-000000000006', 'locale',         'Locale',          'Preferred locale code',                   'string',  FALSE, FALSE, 60),
    ('00000000-0000-0000-0001-000000000007', 'avatar_url',     'Avatar URL',      'Profile avatar image URL',                'url',     FALSE, FALSE, 70),
    ('00000000-0000-0000-0001-000000000008', 'phone',          'Phone Number',    'Contact phone number',                    'phone',   TRUE,  FALSE, 80),
    ('00000000-0000-0000-0001-000000000009', 'bio',            'Biography',       'Short biography or description',          'string',  FALSE, FALSE, 90)
) AS v(id, code, name, description, data_type, is_pii, is_required, sort_order)
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."04_dim_user_property_keys" WHERE code = v.code);

-- Account types
INSERT INTO "03_auth_manage"."06_dim_account_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT v.id::UUID, v.code, v.name, v.description, v.sort_order, TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
FROM (VALUES
    ('00000000-0000-0000-0002-000000000001', 'local_password', 'Local Password',   'Username and password authentication',   10),
    ('00000000-0000-0000-0002-000000000002', 'google',         'Google OAuth',     'Google OAuth 2.0 authentication',        20),
    ('00000000-0000-0000-0002-000000000003', 'github',         'GitHub OAuth',     'GitHub OAuth 2.0 authentication',        30),
    ('00000000-0000-0000-0002-000000000004', 'microsoft',      'Microsoft OAuth',  'Microsoft Entra ID authentication',      40),
    ('00000000-0000-0000-0002-000000000005', 'saml',           'SAML SSO',         'SAML 2.0 single sign-on',               50),
    ('00000000-0000-0000-0002-000000000006', 'api_key',        'API Key',          'Programmatic API key authentication',    60)
) AS v(id, code, name, description, sort_order)
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."06_dim_account_types" WHERE code = v.code);

-- Account property keys
INSERT INTO "03_auth_manage"."07_dim_account_property_keys" (id, account_type_code, code, name, description, is_secret, sort_order, created_at, updated_at)
SELECT v.id::UUID, v.account_type_code, v.code, v.name, v.description, v.is_secret, v.sort_order, TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
FROM (VALUES
    ('00000000-0000-0000-0003-000000000001', 'local_password', 'password_hash',       'Password Hash',       'Argon2 password hash',                    TRUE,  10),
    ('00000000-0000-0000-0003-000000000002', 'local_password', 'password_version',    'Password Version',    'Credential version for rotation tracking', FALSE, 20),
    ('00000000-0000-0000-0003-000000000003', 'local_password', 'password_changed_at', 'Password Changed At', 'Timestamp of last password change',        FALSE, 30),
    ('00000000-0000-0000-0003-000000000004', 'google',         'google_id',           'Google ID',           'Google account unique identifier',         FALSE, 10),
    ('00000000-0000-0000-0003-000000000005', 'google',         'google_email',        'Google Email',        'Email from Google profile',                FALSE, 20),
    ('00000000-0000-0000-0003-000000000006', 'github',         'github_id',           'GitHub ID',           'GitHub account unique identifier',         FALSE, 10),
    ('00000000-0000-0000-0003-000000000007', 'github',         'github_username',     'GitHub Username',     'GitHub username',                          FALSE, 20)
) AS v(id, account_type_code, code, name, description, is_secret, sort_order)
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."07_dim_account_property_keys" WHERE account_type_code = v.account_type_code AND code = v.code);

-- ─────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_05_dtl_user_properties_user_id
    ON "03_auth_manage"."05_dtl_user_properties" (user_id);

CREATE INDEX IF NOT EXISTS idx_05_dtl_user_properties_key_value
    ON "03_auth_manage"."05_dtl_user_properties" (property_key, property_value);

CREATE UNIQUE INDEX IF NOT EXISTS uq_05_dtl_user_properties_email
    ON "03_auth_manage"."05_dtl_user_properties" (property_value)
    WHERE property_key = 'email';

CREATE UNIQUE INDEX IF NOT EXISTS uq_05_dtl_user_properties_username
    ON "03_auth_manage"."05_dtl_user_properties" (property_value)
    WHERE property_key = 'username';

CREATE INDEX IF NOT EXISTS idx_08_dtl_user_accounts_user_id
    ON "03_auth_manage"."08_dtl_user_accounts" (user_id);

CREATE INDEX IF NOT EXISTS idx_09_dtl_user_account_properties_account_id
    ON "03_auth_manage"."09_dtl_user_account_properties" (user_account_id);

CREATE INDEX IF NOT EXISTS idx_10_trx_auth_sessions_user_revoked
    ON "03_auth_manage"."10_trx_auth_sessions" (user_id, revoked_at);

CREATE INDEX IF NOT EXISTS idx_11_trx_login_attempts_lookup
    ON "03_auth_manage"."11_trx_login_attempts" (tenant_key, normalized_identifier, occurred_at);

-- ─────────────────────────────────────────────────────────────────────────
-- COMMENTS
-- ─────────────────────────────────────────────────────────────────────────

COMMENT ON SCHEMA "03_auth_manage" IS 'Ordered local authentication schema for self-hosted account and session management.';

COMMENT ON TABLE "03_auth_manage"."02_dim_challenge_types" IS 'Reference values for supported one-time auth challenge types.';
COMMENT ON TABLE "03_auth_manage"."03_fct_users" IS 'Canonical user fact table with UUID, tenant scope, and status flags only.';
COMMENT ON TABLE "03_auth_manage"."04_dim_user_property_keys" IS 'Dimension table defining all valid user property keys for the EAV user properties table.';
COMMENT ON TABLE "03_auth_manage"."05_dtl_user_properties" IS 'EAV user properties: flexible key-value storage for user attributes.';
COMMENT ON TABLE "03_auth_manage"."06_dim_account_types" IS 'Dimension table of supported authentication account types.';
COMMENT ON TABLE "03_auth_manage"."07_dim_account_property_keys" IS 'Dimension table defining valid property keys per account type with secret flag.';
COMMENT ON TABLE "03_auth_manage"."08_dtl_user_accounts" IS 'Maps users to authentication account types. One row per user per account type.';
COMMENT ON TABLE "03_auth_manage"."09_dtl_user_account_properties" IS 'EAV properties for user accounts: key-value storage for account-type-specific data.';
COMMENT ON TABLE "03_auth_manage"."10_trx_auth_sessions" IS 'Refresh-token-backed auth sessions for local authentication.';
COMMENT ON TABLE "03_auth_manage"."11_trx_login_attempts" IS 'Immutable login attempt evidence for brute-force protection and audit review.';
COMMENT ON TABLE "03_auth_manage"."12_trx_auth_challenges" IS 'One-time auth challenges for password reset and email verification.';
