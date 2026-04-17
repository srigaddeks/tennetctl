-- Migration 039: Notify suppression list
--
-- Email addresses that must never be sent to again (hard bounces, user
-- unsubscribes, manual admin blocks). Email sender and transactional Send
-- both consult this list before each send. RFC 8058 one-click unsubscribe
-- + the bounce webhook both write here.
--
-- Scoped to org_id — different orgs may suppress the same address for
-- different reasons, and suppression in one org must not bleed into another.

-- UP ====

CREATE TABLE "06_notify"."17_fct_notify_suppressions" (
    id          VARCHAR(36) NOT NULL,
    org_id      VARCHAR(36) NOT NULL,
    email       TEXT        NOT NULL,
    reason_code TEXT        NOT NULL,
    delivery_id VARCHAR(36) NULL,
    notes       TEXT        NULL,
    created_by  VARCHAR(36) NOT NULL,
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notify_suppressions         PRIMARY KEY (id),
    CONSTRAINT uq_notify_suppressions_org_em  UNIQUE (org_id, email),
    CONSTRAINT chk_notify_suppressions_reason CHECK (
        reason_code IN ('hard_bounce','complaint','manual','unsubscribe')
    )
);

COMMENT ON TABLE  "06_notify"."17_fct_notify_suppressions" IS 'Addresses auto-skipped by the email sender. Populated by bounce webhooks + user unsubscribes + admin blocks.';
COMMENT ON COLUMN "06_notify"."17_fct_notify_suppressions".reason_code IS 'Why the address is suppressed: hard_bounce | complaint | manual | unsubscribe';
COMMENT ON COLUMN "06_notify"."17_fct_notify_suppressions".delivery_id IS 'The delivery that triggered the suppression (null for manual adds and user-initiated unsubscribes).';

CREATE INDEX idx_notify_suppressions_org_email_lower
    ON "06_notify"."17_fct_notify_suppressions" (org_id, lower(email));

CREATE VIEW "06_notify"."v_notify_suppressions" AS
SELECT id, org_id, email, reason_code, delivery_id, notes, created_by, created_at
FROM "06_notify"."17_fct_notify_suppressions";

COMMENT ON VIEW "06_notify"."v_notify_suppressions" IS 'Read path for notify suppressions.';

-- DOWN ====
DROP VIEW  IF EXISTS "06_notify"."v_notify_suppressions";
DROP INDEX IF EXISTS "06_notify"."idx_notify_suppressions_org_email_lower";
DROP TABLE IF EXISTS "06_notify"."17_fct_notify_suppressions";
