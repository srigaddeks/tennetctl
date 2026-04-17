-- Migration 034: Drop campaigns from notify
--
-- Campaigns moved out of the core notify feature — they'll be built as a
-- separate app that consumes the notify API. Drops:
--   • v_notify_campaigns view
--   • 18_fct_notify_campaigns table + indexes
--   • 05_dim_notify_campaign_statuses table
--   • campaign_id column + its partial unique index on 15_fct_notify_deliveries
--   • recreates v_notify_deliveries without campaign_id

-- UP ====

DROP VIEW  IF EXISTS "06_notify"."v_notify_campaigns";
DROP VIEW  IF EXISTS "06_notify"."v_notify_deliveries";

-- Partial unique index that depended on campaign_id.
DROP INDEX IF EXISTS "06_notify"."uq_notify_deliveries_campaign_user_channel";

-- Drop the campaigns tables.
DROP TABLE IF EXISTS "06_notify"."18_fct_notify_campaigns";
DROP TABLE IF EXISTS "06_notify"."05_dim_notify_campaign_statuses";

-- Drop the FK column on deliveries.
ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    DROP COLUMN IF EXISTS campaign_id;

-- Recreate v_notify_deliveries without campaign_id.
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
JOIN "06_notify"."01_dim_notify_channels" ch ON ch.id = d.channel_id
JOIN "06_notify"."04_dim_notify_priorities" pr ON pr.id = d.priority_id
JOIN "06_notify"."03_dim_notify_statuses" st ON st.id = d.status_id;

COMMENT ON VIEW "06_notify"."v_notify_deliveries" IS
    'Read path for deliveries: joins channel/priority/status dims. Includes deep_link. Campaigns removed from core notify.';

-- DOWN ====
-- Irreversible for data: restoring the campaigns table would re-create the
-- schema but not the rows. Intentionally no-op since campaigns are out of
-- scope for core notify going forward.
--
-- To restore the schema (empty tables only), re-run migration 028.

SELECT 1;
