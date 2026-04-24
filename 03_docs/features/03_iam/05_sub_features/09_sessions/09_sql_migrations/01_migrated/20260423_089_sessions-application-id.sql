-- UP ====
-- Add application_id to sessions so every token is bound to the originating
-- SaaS app. NULL = platform / admin console (browser without x-application-id
-- header). Non-null = registered app (mobile SDK, partner SaaS, etc.).

ALTER TABLE "03_iam"."16_fct_sessions"
    ADD COLUMN IF NOT EXISTS application_id VARCHAR(36)
        REFERENCES "03_iam"."15_fct_applications"(id)
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_iam_fct_sessions_application
    ON "03_iam"."16_fct_sessions"(application_id)
    WHERE application_id IS NOT NULL;

COMMENT ON COLUMN "03_iam"."16_fct_sessions".application_id IS
    'App that originated this session. NULL = platform console or admin UI. Non-null = registered SaaS/mobile app.';

-- Rebuild v_sessions to expose application_id.
DROP VIEW IF EXISTS "03_iam".v_sessions;
CREATE VIEW "03_iam".v_sessions AS
    SELECT
        id,
        user_id,
        org_id,
        workspace_id,
        application_id,
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
    FROM "03_iam"."16_fct_sessions";

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
        last_activity_at,
        user_agent,
        ip_address,
        (deleted_at IS NULL
            AND revoked_at IS NULL
            AND is_active = true
            AND expires_at > CURRENT_TIMESTAMP) AS is_valid
    FROM "03_iam"."16_fct_sessions";

DROP INDEX IF EXISTS "03_iam".idx_iam_fct_sessions_application;
ALTER TABLE "03_iam"."16_fct_sessions" DROP COLUMN IF EXISTS application_id;
