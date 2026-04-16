-- ============================================================================
-- Notification system enhancements:
--   1. Add marketing + product_updates categories
--   2. Add category_code to templates table
--   3. Add read_at + is_read to queue for user inbox
--   4. Add dispatch_immediately flag to notification types
--   5. Index for inbox queries
-- ============================================================================

-- 1. New notification categories
INSERT INTO "03_notifications"."03_dim_notification_categories"
    (id, code, name, description, is_mandatory, sort_order, created_at, updated_at)
VALUES
    ('b0000000-0000-0000-0000-000000000007', 'marketing',       'Marketing',       'Promotional content, offers, and newsletters',            FALSE, 7, NOW(), NOW()),
    ('b0000000-0000-0000-0000-000000000008', 'product_updates', 'Product Updates',  'Feature announcements, changelogs, and product news',     FALSE, 8, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Add category_code to templates (allows categorising templates independently of notification type)
ALTER TABLE "03_notifications"."10_fct_templates"
    ADD COLUMN IF NOT EXISTS category_code VARCHAR(50) NULL
    REFERENCES "03_notifications"."03_dim_notification_categories" (code)
    ON DELETE SET NULL;

-- 3a. Add read_at and is_read to notification queue (user inbox tracking)
ALTER TABLE "03_notifications"."20_trx_notification_queue"
    ADD COLUMN IF NOT EXISTS read_at        TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS is_read        BOOLEAN     NOT NULL DEFAULT FALSE;

-- 3b. Index for fast inbox queries per user
CREATE INDEX IF NOT EXISTS idx_notif_queue_user_inbox
    ON "03_notifications"."20_trx_notification_queue" (user_id, created_at DESC);

-- Index for unread count queries
CREATE INDEX IF NOT EXISTS idx_notif_queue_user_unread
    ON "03_notifications"."20_trx_notification_queue" (user_id, is_read)
    WHERE is_read = FALSE;

-- 4. Add dispatch_immediately flag to notification types
--    When TRUE: queue processor treats these as priority=critical and scheduled_at=NOW() regardless of rule delay
ALTER TABLE "03_notifications"."04_dim_notification_types"
    ADD COLUMN IF NOT EXISTS dispatch_immediately BOOLEAN NOT NULL DEFAULT FALSE;

-- Mark security + transactional types as immediate
UPDATE "03_notifications"."04_dim_notification_types"
SET dispatch_immediately = TRUE
WHERE category_code IN ('security', 'transactional');

-- 5. Update priority weights so critical gets much higher weight (processed first in every batch)
UPDATE "03_notifications"."06_dim_notification_priorities"
SET weight = 1000
WHERE code = 'critical';

UPDATE "03_notifications"."06_dim_notification_priorities"
SET weight = 100
WHERE code = 'high';

UPDATE "03_notifications"."06_dim_notification_priorities"
SET weight = 10
WHERE code = 'normal';

UPDATE "03_notifications"."06_dim_notification_priorities"
SET weight = 1
WHERE code = 'low';
