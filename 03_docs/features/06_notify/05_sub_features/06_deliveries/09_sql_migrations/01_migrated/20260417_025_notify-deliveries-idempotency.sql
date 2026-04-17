-- Migration 025: Delivery idempotency constraint
--
-- Partial unique index on (subscription_id, audit_outbox_id, channel_id) for
-- subscription-driven deliveries. Prevents duplicate deliveries if the worker
-- processes the same event twice (e.g., LISTEN + poll both fire, or worker
-- restarts mid-batch).
--
-- channel_id is included because critical-category templates fan out across
-- multiple channels for a single (subscription, outbox_event) pair. The index
-- allows one delivery per channel per event — blocking true duplicates while
-- permitting the intended fan-out.
--
-- Partial (WHERE NOT NULL): transactional deliveries (subscription_id IS NULL)
-- and on-demand sends are not constrained by this index.

-- UP ====

CREATE UNIQUE INDEX uq_notify_deliveries_sub_outbox
    ON "06_notify"."15_fct_notify_deliveries" (subscription_id, audit_outbox_id, channel_id)
    WHERE subscription_id IS NOT NULL AND audit_outbox_id IS NOT NULL;

COMMENT ON INDEX "06_notify"."uq_notify_deliveries_sub_outbox" IS
    'Idempotency guard: one delivery per (subscription, outbox_event, channel) triple. Allows ON CONFLICT DO NOTHING for safe re-processing while permitting critical fan-out across multiple channels.';

-- DOWN ====

DROP INDEX IF EXISTS "06_notify"."uq_notify_deliveries_sub_outbox";
