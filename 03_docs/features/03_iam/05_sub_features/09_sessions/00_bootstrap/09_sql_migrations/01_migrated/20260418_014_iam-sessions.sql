-- UP ====

-- iam.sessions sub-feature: fct_sessions.
-- Opaque, HMAC-signed session tokens. The token itself is `{session_id}.{sig}`
-- where sig = HMAC-SHA256(signing_key_v1, session_id) base64url-encoded. Signing
-- key is fetched from vault (auth.session.signing_key_v1) and SWR-cached for 60s.
--
-- expires_at + revoked_at carry the session state — no dim_session_status table.
-- A session is valid iff (deleted_at IS NULL AND revoked_at IS NULL AND expires_at > now()).
--
-- Phase 8 (auth) creates rows via signin/signup. Middleware validates every
-- inbound request against this table.

CREATE TABLE "03_iam"."16_fct_sessions" (
    id             VARCHAR(36) NOT NULL,
    user_id        VARCHAR(36) NOT NULL,
    org_id         VARCHAR(36),
    workspace_id   VARCHAR(36),
    expires_at     TIMESTAMP NOT NULL,
    revoked_at     TIMESTAMP,
    is_active      BOOLEAN NOT NULL DEFAULT true,
    is_test        BOOLEAN NOT NULL DEFAULT false,
    deleted_at     TIMESTAMP,
    created_by     VARCHAR(36) NOT NULL,
    updated_by     VARCHAR(36) NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_sessions PRIMARY KEY (id),
    CONSTRAINT fk_iam_fct_sessions_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users"(id) ON DELETE CASCADE
);
CREATE INDEX idx_iam_fct_sessions_user      ON "03_iam"."16_fct_sessions" (user_id);
CREATE INDEX idx_iam_fct_sessions_expires   ON "03_iam"."16_fct_sessions" (expires_at);

COMMENT ON TABLE  "03_iam"."16_fct_sessions" IS 'Opaque HMAC-signed user sessions. Valid iff deleted_at IS NULL AND revoked_at IS NULL AND expires_at > now().';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".id IS 'UUID v7. Embedded in the opaque token.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".user_id IS 'FK fct_users.id.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".org_id IS 'Optional active org context for the session.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".workspace_id IS 'Optional active workspace context for the session.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".expires_at IS 'Hard expiry timestamp. Default 7 days from create unless overridden via vault config auth.session.ttl_days.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".revoked_at IS 'Set on signout. Once non-null the session is permanently invalid.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".is_active IS 'Soft-disable flag (admin can disable without revoke).';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".is_test IS 'Marks test/staging sessions.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".created_by IS 'UUID of user that created the session (= user_id, except for impersonation).';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".updated_at IS 'Last-update timestamp (set by app).';

-- ── v_sessions: flat read shape ────────────────────────────────────

CREATE VIEW "03_iam"."v_sessions" AS
SELECT
    s.id,
    s.user_id,
    s.org_id,
    s.workspace_id,
    s.expires_at,
    s.revoked_at,
    s.is_active,
    s.is_test,
    s.deleted_at,
    s.created_by,
    s.updated_by,
    s.created_at,
    s.updated_at,
    (s.deleted_at IS NULL
     AND s.revoked_at IS NULL
     AND s.is_active = true
     AND s.expires_at > CURRENT_TIMESTAMP) AS is_valid
FROM "03_iam"."16_fct_sessions" s;

COMMENT ON VIEW "03_iam"."v_sessions" IS 'Flat read shape for sessions — derives is_valid from (not deleted, not revoked, active, not expired).';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_sessions";
DROP TABLE IF EXISTS "03_iam"."16_fct_sessions";
