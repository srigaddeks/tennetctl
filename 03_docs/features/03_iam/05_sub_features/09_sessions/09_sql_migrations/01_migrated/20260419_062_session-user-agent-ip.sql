-- UP ====
-- Capture user_agent + ip_address on session create so the Account Sessions
-- admin UI can show "Chrome on macOS from 10.0.0.4" instead of a raw UUID.
--
-- Both fields are optional — existing rows remain NULL; the signin path will
-- populate going forward.

ALTER TABLE "03_iam"."16_fct_sessions"
    ADD COLUMN IF NOT EXISTS user_agent VARCHAR(512),
    ADD COLUMN IF NOT EXISTS ip_address VARCHAR(64);

COMMENT ON COLUMN "03_iam"."16_fct_sessions".user_agent IS
    'HTTP User-Agent captured at session create. NULL on sessions issued before this migration. Truncated to 512 chars.';
COMMENT ON COLUMN "03_iam"."16_fct_sessions".ip_address IS
    'Client IP captured at session create (respects X-Forwarded-For when behind a proxy). IPv4 dotted or IPv6 colon form.';

-- Rebuild v_sessions to expose the new columns.
DROP VIEW IF EXISTS "03_iam".v_sessions;
CREATE VIEW "03_iam".v_sessions AS
    SELECT
        id,
        user_id,
        org_id,
        workspace_id,
        expires_at,
        revoked_at,
        is_active,
        is_test,
        deleted_at,
        created_by,
        updated_by,
        created_at,
        updated_at,
        last_activity_at,
        user_agent,
        ip_address,
        (deleted_at IS NULL
            AND revoked_at IS NULL
            AND is_active = true
            AND expires_at > CURRENT_TIMESTAMP) AS is_valid
    FROM "03_iam"."16_fct_sessions" s;

-- DOWN ====
DROP VIEW IF EXISTS "03_iam".v_sessions;
CREATE VIEW "03_iam".v_sessions AS
    SELECT
        id,
        user_id,
        org_id,
        workspace_id,
        expires_at,
        revoked_at,
        is_active,
        is_test,
        deleted_at,
        created_by,
        updated_by,
        created_at,
        updated_at,
        (deleted_at IS NULL
            AND revoked_at IS NULL
            AND is_active = true
            AND expires_at > CURRENT_TIMESTAMP) AS is_valid
    FROM "03_iam"."16_fct_sessions" s;

ALTER TABLE "03_iam"."16_fct_sessions"
    DROP COLUMN IF EXISTS ip_address,
    DROP COLUMN IF EXISTS user_agent;
