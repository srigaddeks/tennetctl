-- Migration 033: Deep link column on deliveries
--
-- Adds `deep_link` TEXT NULL to fct_notify_deliveries. This is the canonical
-- URL a user should land on when they click the notification (bell icon,
-- webpush notification, email CTA). Templates populate it at render time, or
-- the transactional send caller passes it explicitly.
--
-- Channels use it as follows:
--   • in_app   — frontend router.push(deep_link) on bell item click
--   • webpush  — service worker reads payload.url; webpush sender injects deep_link
--   • email    — template body wraps its main CTA link; pytracking still wraps
--                for click tracking + redirects to deep_link
--
-- Recreates v_notify_deliveries to expose the column.

-- UP ====

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    ADD COLUMN deep_link TEXT NULL;

COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".deep_link IS
    'Canonical URL the recipient should navigate to when they open the notification. Optional.';

-- Recreate v_notify_deliveries to include deep_link.
DROP VIEW IF EXISTS "06_notify"."v_notify_deliveries";

CREATE VIEW "06_notify"."v_notify_deliveries" AS
SELECT
    d.id, d.org_id, d.subscription_id, d.campaign_id, d.template_id,
    d.recipient_user_id,
    d.channel_id, ch.code AS channel_code, ch.label AS channel_label,
    d.priority_id, pr.code AS priority_code, pr.label AS priority_label,
    d.status_id, st.code AS status_code, st.label AS status_label,
    d.resolved_variables, d.deep_link, d.audit_outbox_id,
    d.failure_reason, d.scheduled_at, d.attempted_at, d.delivered_at,
    d.created_at, d.updated_at
FROM "06_notify"."15_fct_notify_deliveries" d
JOIN "06_notify"."01_dim_notify_channels" ch ON ch.id = d.channel_id
JOIN "06_notify"."04_dim_notify_priorities" pr ON pr.id = d.priority_id
JOIN "06_notify"."03_dim_notify_statuses" st ON st.id = d.status_id;

COMMENT ON VIEW "06_notify"."v_notify_deliveries" IS
    'Read path for deliveries: joins channel/priority/status dims. Includes campaign_id + deep_link.';

-- DOWN ====

DROP VIEW IF EXISTS "06_notify"."v_notify_deliveries";

CREATE VIEW "06_notify"."v_notify_deliveries" AS
SELECT
    d.id, d.org_id, d.subscription_id, d.campaign_id, d.template_id,
    d.recipient_user_id,
    d.channel_id, ch.code AS channel_code, ch.label AS channel_label,
    d.priority_id, pr.code AS priority_code, pr.label AS priority_label,
    d.status_id, st.code AS status_code, st.label AS status_label,
    d.resolved_variables, d.audit_outbox_id,
    d.failure_reason, d.scheduled_at, d.attempted_at, d.delivered_at,
    d.created_at, d.updated_at
FROM "06_notify"."15_fct_notify_deliveries" d
JOIN "06_notify"."01_dim_notify_channels" ch ON ch.id = d.channel_id
JOIN "06_notify"."04_dim_notify_priorities" pr ON pr.id = d.priority_id
JOIN "06_notify"."03_dim_notify_statuses" st ON st.id = d.status_id;

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    DROP COLUMN IF EXISTS deep_link;
