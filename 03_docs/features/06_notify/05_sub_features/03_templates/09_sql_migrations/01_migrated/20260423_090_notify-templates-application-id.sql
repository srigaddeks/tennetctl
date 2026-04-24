-- UP ====
-- Scope notify templates to a specific application.
-- NULL = org-wide template (all apps can use it).
-- Non-null = template belongs exclusively to that app (e.g. "welcome_to_solsocial").

ALTER TABLE "06_notify"."12_fct_notify_templates"
    ADD COLUMN IF NOT EXISTS application_id VARCHAR(36)
        REFERENCES "03_iam"."15_fct_applications"(id)
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_fct_notify_templates_application
    ON "06_notify"."12_fct_notify_templates"(application_id)
    WHERE application_id IS NOT NULL;

COMMENT ON COLUMN "06_notify"."12_fct_notify_templates".application_id IS
    'Restricts this template to a specific app. NULL = available to all apps in the org.';

-- DOWN ====
DROP INDEX IF EXISTS "06_notify".idx_fct_notify_templates_application;
ALTER TABLE "06_notify"."12_fct_notify_templates" DROP COLUMN IF EXISTS application_id;
