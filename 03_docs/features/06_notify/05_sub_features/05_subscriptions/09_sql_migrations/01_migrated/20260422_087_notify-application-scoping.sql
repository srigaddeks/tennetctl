-- UP ====

-- Tag every notification delivery with the SaaS application that triggered it.
-- Same rationale as 086_audit-application-scoping: solsocial and future apps
-- stamp their application_id; platform-internal notifications leave it NULL.

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    ADD COLUMN application_id VARCHAR(36);

COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".application_id IS
    'Foreign ref to 03_iam.15_fct_applications. Set when the send originated '
    'from a SaaS application. NULL = platform-internal send.';

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    ADD CONSTRAINT fk_fct_notify_deliveries_application
        FOREIGN KEY (application_id)
        REFERENCES "03_iam"."15_fct_applications" (id);

CREATE INDEX idx_fct_notify_deliveries_application
    ON "06_notify"."15_fct_notify_deliveries" (application_id)
    WHERE application_id IS NOT NULL;

-- DOWN ====

DROP INDEX IF EXISTS "06_notify".idx_fct_notify_deliveries_application;
ALTER TABLE "06_notify"."15_fct_notify_deliveries" DROP CONSTRAINT IF EXISTS fk_fct_notify_deliveries_application;
ALTER TABLE "06_notify"."15_fct_notify_deliveries" DROP COLUMN IF EXISTS application_id;
