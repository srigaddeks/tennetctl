-- Add source_env column to notification queue so each environment's processor
-- only picks up notifications it created. Prevents duplicate sends when
-- multiple environments (local, dev, staging) share the same database.

ALTER TABLE "03_notifications"."20_trx_notification_queue"
    ADD COLUMN IF NOT EXISTS source_env VARCHAR(50) NULL;

COMMENT ON COLUMN "03_notifications"."20_trx_notification_queue".source_env
    IS 'Environment that created this notification (development, staging, production). Processor only picks up matching env.';

-- Index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_20_trx_queue_source_env
    ON "03_notifications"."20_trx_notification_queue" (source_env)
    WHERE status_code IN ('queued', 'failed');
