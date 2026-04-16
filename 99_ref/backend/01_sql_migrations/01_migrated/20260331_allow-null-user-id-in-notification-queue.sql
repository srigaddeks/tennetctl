-- =============================================================================
-- Migration: 20260331_allow-null-user-id-in-notification-queue.sql
-- Module:    03_notifications
-- Description: Allow NULL user_id in notification queue for external recipients
--              (e.g. invitation emails sent to addresses without an account yet)
-- =============================================================================

-- UP ==========================================================================

-- Drop the NOT NULL constraint on user_id so dispatch_to_email() can queue
-- notifications for email addresses that don't yet have a platform account.
ALTER TABLE "03_notifications"."20_trx_notification_queue"
    ALTER COLUMN user_id DROP NOT NULL;

COMMENT ON COLUMN "03_notifications"."20_trx_notification_queue".user_id
    IS 'Platform user UUID. NULL for external recipients (e.g. invite emails) who do not yet have an account.';

-- DOWN ========================================================================

-- Re-applying NOT NULL would fail if any rows have user_id = NULL, so
-- in a real rollback you would need to DELETE those rows first.
-- ALTER TABLE "03_notifications"."20_trx_notification_queue"
--     ALTER COLUMN user_id SET NOT NULL;
