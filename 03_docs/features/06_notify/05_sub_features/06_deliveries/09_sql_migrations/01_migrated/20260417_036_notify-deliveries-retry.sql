-- Migration 036: Retry / backoff on deliveries
--
-- Adds attempt_count, max_attempts, next_retry_at to deliveries so email
-- and webpush senders can retry transient failures with exponential backoff
-- before giving up with status=failed.
--
-- Semantics:
--   • attempt_count — how many times we've tried to send. Incremented on each
--     attempt (success or failure).
--   • max_attempts  — per-delivery cap. Defaults to 3.
--   • next_retry_at — when the next attempt is allowed. NULL for a first
--     attempt or a terminal success. Senders pick up deliveries where
--     status=queued AND (next_retry_at IS NULL OR next_retry_at <= NOW()).
--
-- Recreates v_notify_deliveries to expose the new columns.

-- UP ====

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    ADD COLUMN attempt_count INT       NOT NULL DEFAULT 0,
    ADD COLUMN max_attempts  INT       NOT NULL DEFAULT 3,
    ADD COLUMN next_retry_at TIMESTAMP NULL;

COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".attempt_count IS
    'Number of send attempts so far. Incremented on each attempt (success or retryable error).';
COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".max_attempts IS
    'Per-delivery retry cap. Sender marks status=failed once attempt_count reaches this.';
COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".next_retry_at IS
    'When the next send attempt may run. NULL means eligible now. Populated after a retryable failure using exponential backoff.';

CREATE INDEX idx_notify_deliveries_next_retry
    ON "06_notify"."15_fct_notify_deliveries" (channel_id, status_id, next_retry_at)
    WHERE status_id = 2;

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

COMMENT ON VIEW "06_notify"."v_notify_deliveries" IS
    'Read path for deliveries: joins channel/priority/status dims. Includes deep_link + retry tracking.';

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
    d.failure_reason, d.scheduled_at, d.attempted_at, d.delivered_at,
    d.created_at, d.updated_at
FROM "06_notify"."15_fct_notify_deliveries" d
JOIN "06_notify"."01_dim_notify_channels"   ch ON ch.id = d.channel_id
JOIN "06_notify"."04_dim_notify_priorities" pr ON pr.id = d.priority_id
JOIN "06_notify"."03_dim_notify_statuses"   st ON st.id = d.status_id;

DROP INDEX IF EXISTS "06_notify"."idx_notify_deliveries_next_retry";

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    DROP COLUMN IF EXISTS attempt_count,
    DROP COLUMN IF EXISTS max_attempts,
    DROP COLUMN IF EXISTS next_retry_at;
