-- Migration 038: Send API idempotency
--
-- Adds idempotency_key TEXT NULL + partial unique index on
-- (org_id, idempotency_key) WHERE idempotency_key IS NOT NULL.
--
-- Semantics: callers of POST /v1/notify/send can pass Idempotency-Key header.
-- The send service stores it on the delivery row. A repeat request with the
-- same (org_id, idempotency_key) returns the same delivery_id instead of
-- creating a second row. Existing worker + campaign deliveries don't set
-- the key, so their idempotency paths (subscription_id + audit_outbox_id +
-- channel_id) are unchanged.
--
-- View recreated to expose the column. No dependent views need rebuild
-- since v_notify_deliveries has no downstream views.

-- UP ====

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    ADD COLUMN idempotency_key TEXT NULL;

COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".idempotency_key IS
    'Caller-provided Idempotency-Key header on POST /v1/notify/send. Partial unique on (org_id, idempotency_key) — repeat sends return existing delivery.';

CREATE UNIQUE INDEX uq_notify_deliveries_idem
    ON "06_notify"."15_fct_notify_deliveries" (org_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

COMMENT ON INDEX "06_notify"."uq_notify_deliveries_idem" IS
    'Idempotency guard for transactional Send API. Partial so worker/campaign rows (no key) are unaffected.';

DROP VIEW IF EXISTS "06_notify"."v_notify_deliveries";

CREATE VIEW "06_notify"."v_notify_deliveries" AS
SELECT
    d.id, d.org_id, d.subscription_id, d.template_id,
    d.recipient_user_id,
    d.channel_id, ch.code AS channel_code, ch.label AS channel_label,
    d.priority_id, pr.code AS priority_code, pr.label AS priority_label,
    d.status_id, st.code AS status_code, st.label AS status_label,
    d.resolved_variables, d.deep_link, d.audit_outbox_id,
    d.idempotency_key,
    d.attempt_count, d.max_attempts, d.next_retry_at,
    d.failure_reason, d.scheduled_at, d.attempted_at, d.delivered_at,
    d.created_at, d.updated_at
FROM "06_notify"."15_fct_notify_deliveries" d
JOIN "06_notify"."01_dim_notify_channels"   ch ON ch.id = d.channel_id
JOIN "06_notify"."04_dim_notify_priorities" pr ON pr.id = d.priority_id
JOIN "06_notify"."03_dim_notify_statuses"   st ON st.id = d.status_id;

COMMENT ON VIEW "06_notify"."v_notify_deliveries" IS
    'Read path for deliveries: joins channel/priority/status dims. Includes deep_link + retry + idempotency_key.';

-- DOWN ====
DROP VIEW IF EXISTS "06_notify"."v_notify_deliveries";

CREATE VIEW "06_notify"."v_notify_deliveries" AS
SELECT
    d.id, d.org_id, d.subscription_id, d.template_id,
    d.recipient_user_id,
    d.channel_id, ch.code AS channel_code, ch.label AS channel_label,
    d.priority_id, pr.code AS priority_code, pr.label AS priority_label,
    d.status_id, st.code AS status_code, st.label AS status_label,
    d.resolved_variables, d.deep_link, d.audit_outbox_id,
    d.attempt_count, d.max_attempts, d.next_retry_at,
    d.failure_reason, d.scheduled_at, d.attempted_at, d.delivered_at,
    d.created_at, d.updated_at
FROM "06_notify"."15_fct_notify_deliveries" d
JOIN "06_notify"."01_dim_notify_channels"   ch ON ch.id = d.channel_id
JOIN "06_notify"."04_dim_notify_priorities" pr ON pr.id = d.priority_id
JOIN "06_notify"."03_dim_notify_statuses"   st ON st.id = d.status_id;

DROP INDEX IF EXISTS "06_notify"."uq_notify_deliveries_idem";

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    DROP COLUMN IF EXISTS idempotency_key;
