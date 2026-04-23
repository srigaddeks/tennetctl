-- UP ====
-- dim_monitoring_dashboard_share_scope — lookup table for share scopes (internal_user=1, public_token=2).
-- fct_monitoring_dashboard_shares — dashboard grant records.
-- dtl_monitoring_dashboard_share_token — token metadata (hash, key_version, passphrase hash, view count).
-- v_monitoring_dashboard_shares — read model combining scope, grantee identity, token meta, status.

-- Dimension table: share scopes
CREATE TABLE IF NOT EXISTS "05_monitoring"."01_dim_monitoring_dashboard_share_scope" (
    id          SMALLINT NOT NULL,
    code        TEXT NOT NULL,
    label       TEXT NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP NULL,
    CONSTRAINT pk_dim_monitoring_dashboard_share_scope PRIMARY KEY (id),
    CONSTRAINT uq_dim_monitoring_dashboard_share_scope_code UNIQUE (code)
);

COMMENT ON TABLE  "05_monitoring"."01_dim_monitoring_dashboard_share_scope" IS 'Lookup: internal_user | public_token.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_dashboard_share_scope".id IS 'SMALLINT PK.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_dashboard_share_scope".code IS 'internal_user or public_token.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_dashboard_share_scope".label IS 'Human-readable label.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_dashboard_share_scope".description IS 'Usage description.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_dashboard_share_scope".deprecated_at IS 'Soft-deprecation marker.';

CREATE INDEX idx_dim_monitoring_dashboard_share_scope_code
    ON "05_monitoring"."01_dim_monitoring_dashboard_share_scope" (code);

-- Fact table: dashboard shares/grants
CREATE TABLE IF NOT EXISTS "05_monitoring"."12_fct_monitoring_dashboard_shares" (
    id                  VARCHAR(36) NOT NULL,
    org_id              VARCHAR(36) NOT NULL,
    dashboard_id        VARCHAR(36) NOT NULL,
    scope_id            SMALLINT NOT NULL,
    granted_by_user_id  VARCHAR(36) NOT NULL,
    granted_to_user_id  VARCHAR(36) NULL,
    recipient_email     TEXT NULL,
    expires_at          TIMESTAMP NULL,
    revoked_at          TIMESTAMP NULL,
    revoked_by_user_id  VARCHAR(36) NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at          TIMESTAMP NULL,
    CONSTRAINT pk_fct_monitoring_dashboard_shares PRIMARY KEY (id),
    CONSTRAINT fk_fct_monitoring_dashboard_shares_org
        FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_fct_monitoring_dashboard_shares_dashboard
        FOREIGN KEY (dashboard_id)
        REFERENCES "05_monitoring"."10_fct_monitoring_dashboards"(id),
    CONSTRAINT fk_fct_monitoring_dashboard_shares_scope
        FOREIGN KEY (scope_id)
        REFERENCES "05_monitoring"."01_dim_monitoring_dashboard_share_scope"(id),
    CONSTRAINT fk_fct_monitoring_dashboard_shares_granted_by
        FOREIGN KEY (granted_by_user_id)
        REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_fct_monitoring_dashboard_shares_granted_to
        FOREIGN KEY (granted_to_user_id)
        REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_fct_monitoring_dashboard_shares_revoked_by
        FOREIGN KEY (revoked_by_user_id)
        REFERENCES "03_iam"."12_fct_users"(id)
);

COMMENT ON TABLE  "05_monitoring"."12_fct_monitoring_dashboard_shares" IS 'Dashboard share grants: internal users or public tokens.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".id IS 'UUID v7 PK.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".org_id IS 'Org that owns the dashboard.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".dashboard_id IS 'FK -> fct_monitoring_dashboards(id).';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".scope_id IS 'FK -> dim_monitoring_dashboard_share_scope: 1=internal_user, 2=public_token.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".granted_by_user_id IS 'User who created the grant.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".granted_to_user_id IS 'FK -> fct_users; NULL for public_token scope.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".recipient_email IS 'Email captured from public token minting; used for audit and future email delivery.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".expires_at IS 'Share expiry time; NULL = no expiry.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".revoked_at IS 'When grant was revoked; NULL = active.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".revoked_by_user_id IS 'User who revoked the grant; NULL if not yet revoked.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".created_at IS 'Creation timestamp (UTC).';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".updated_at IS 'Last update timestamp (UTC).';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_dashboard_shares".deleted_at IS 'Soft-delete marker.';

-- Unique index: internal-user grants (one per user per dashboard, active only)
CREATE UNIQUE INDEX uq_fct_monitoring_dashboard_shares_internal_user
    ON "05_monitoring"."12_fct_monitoring_dashboard_shares" (dashboard_id, granted_to_user_id)
    WHERE scope_id = 1 AND revoked_at IS NULL AND deleted_at IS NULL;

CREATE INDEX idx_fct_monitoring_dashboard_shares_org
    ON "05_monitoring"."12_fct_monitoring_dashboard_shares" (org_id)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_fct_monitoring_dashboard_shares_dashboard
    ON "05_monitoring"."12_fct_monitoring_dashboard_shares" (dashboard_id)
    WHERE deleted_at IS NULL AND revoked_at IS NULL;

CREATE INDEX idx_fct_monitoring_dashboard_shares_granted_to
    ON "05_monitoring"."12_fct_monitoring_dashboard_shares" (granted_to_user_id)
    WHERE scope_id = 1 AND deleted_at IS NULL AND revoked_at IS NULL;

-- Detail table: token metadata (hashes, passphrases, view counts)
CREATE TABLE IF NOT EXISTS "05_monitoring"."22_dtl_monitoring_dashboard_share_token" (
    share_id        VARCHAR(36) NOT NULL,
    token_hash      CHAR(64) NOT NULL,
    key_version     SMALLINT NOT NULL DEFAULT 1,
    passphrase_hash TEXT NULL,
    view_count      INT NOT NULL DEFAULT 0,
    last_viewed_at  TIMESTAMP NULL,
    CONSTRAINT pk_dtl_monitoring_dashboard_share_token PRIMARY KEY (share_id),
    CONSTRAINT fk_dtl_monitoring_dashboard_share_token_share
        FOREIGN KEY (share_id)
        REFERENCES "05_monitoring"."12_fct_monitoring_dashboard_shares"(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_dtl_monitoring_dashboard_share_token_hash UNIQUE (token_hash)
);

COMMENT ON TABLE  "05_monitoring"."22_dtl_monitoring_dashboard_share_token" IS 'Token metadata for public shares: hash (plaintext never stored), key version, passphrase hash, view tracking.';
COMMENT ON COLUMN "05_monitoring"."22_dtl_monitoring_dashboard_share_token".share_id IS 'PK = share_id (FK -> fct_monitoring_dashboard_shares).';
COMMENT ON COLUMN "05_monitoring"."22_dtl_monitoring_dashboard_share_token".token_hash IS 'SHA256(token); token plaintext NEVER stored.';
COMMENT ON COLUMN "05_monitoring"."22_dtl_monitoring_dashboard_share_token".key_version IS 'Vault signing key version for token rotation.';
COMMENT ON COLUMN "05_monitoring"."22_dtl_monitoring_dashboard_share_token".passphrase_hash IS 'bcrypt(passphrase) if passphrase-protected; NULL if no passphrase.';
COMMENT ON COLUMN "05_monitoring"."22_dtl_monitoring_dashboard_share_token".view_count IS 'Cumulative view count.';
COMMENT ON COLUMN "05_monitoring"."22_dtl_monitoring_dashboard_share_token".last_viewed_at IS 'Timestamp of most recent view.';

CREATE INDEX idx_dtl_monitoring_dashboard_share_token_hash
    ON "05_monitoring"."22_dtl_monitoring_dashboard_share_token" (token_hash);

-- Read model view combining scope, grantee identity, token meta, and computed status
CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_dashboard_shares" AS
SELECT
    s.id,
    s.org_id,
    s.dashboard_id,
    s.scope_id,
    ds.code AS scope_code,
    s.granted_by_user_id,
    s.granted_to_user_id,
    COALESCE(u.display_name, u.email) AS grantee_display,
    s.recipient_email,
    s.expires_at,
    CASE
        WHEN s.revoked_at IS NOT NULL THEN 'revoked'::TEXT
        WHEN s.expires_at IS NOT NULL AND s.expires_at < CURRENT_TIMESTAMP THEN 'expired'::TEXT
        ELSE 'active'::TEXT
    END AS status,
    t.token_hash,
    t.key_version,
    t.passphrase_hash IS NOT NULL AS has_passphrase,
    t.view_count,
    t.last_viewed_at,
    s.revoked_at,
    s.revoked_by_user_id,
    s.created_at,
    s.updated_at
FROM "05_monitoring"."12_fct_monitoring_dashboard_shares" s
LEFT JOIN "05_monitoring"."01_dim_monitoring_dashboard_share_scope" ds
    ON ds.id = s.scope_id
LEFT JOIN "03_iam"."v_users" u
    ON u.id = s.granted_to_user_id
LEFT JOIN "05_monitoring"."22_dtl_monitoring_dashboard_share_token" t
    ON t.share_id = s.id
WHERE s.deleted_at IS NULL;

COMMENT ON VIEW "05_monitoring"."v_monitoring_dashboard_shares" IS 'Read model: dashboard shares with scope, grantee identity, token metadata, and computed status.';

-- DOWN ====
DROP VIEW IF EXISTS "05_monitoring"."v_monitoring_dashboard_shares";
DROP INDEX IF EXISTS "05_monitoring"."idx_dtl_monitoring_dashboard_share_token_hash";
DROP TABLE IF EXISTS "05_monitoring"."22_dtl_monitoring_dashboard_share_token";
DROP INDEX IF EXISTS "05_monitoring"."idx_fct_monitoring_dashboard_shares_granted_to";
DROP INDEX IF EXISTS "05_monitoring"."idx_fct_monitoring_dashboard_shares_dashboard";
DROP INDEX IF EXISTS "05_monitoring"."idx_fct_monitoring_dashboard_shares_org";
DROP INDEX IF EXISTS "05_monitoring"."uq_fct_monitoring_dashboard_shares_internal_user";
DROP TABLE IF EXISTS "05_monitoring"."12_fct_monitoring_dashboard_shares";
DROP INDEX IF EXISTS "05_monitoring"."idx_dim_monitoring_dashboard_share_scope_code";
DROP TABLE IF EXISTS "05_monitoring"."01_dim_monitoring_dashboard_share_scope";
