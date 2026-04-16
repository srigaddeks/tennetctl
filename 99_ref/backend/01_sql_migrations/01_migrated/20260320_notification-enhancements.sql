-- Notification system enhancements
-- 1. is_archived column for inbox retention
-- 2. Webhook channel seed
-- 3. Notification preferences category_code index

-- ── 1. Add is_archived to notification queue ──────────────────────────────────

ALTER TABLE "03_notifications"."20_trx_notification_queue"
  ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_notif_queue_archived
  ON "03_notifications"."20_trx_notification_queue" (is_archived, completed_at)
  WHERE is_archived = FALSE;

-- ── 2. Seed webhook channel ──────────────────────────────────────────────────

INSERT INTO "03_notifications"."02_dim_notification_channels" (id, code, name, description, is_available, sort_order, created_at, updated_at)
VALUES ('a0000000-0000-0000-0000-000000000006', 'webhook', 'Webhook', 'HTTP POST to a user-configured endpoint with HMAC signature', FALSE, 50, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ── 3. Index on user_id + tenant_key + is_read for fast unread count ──────────

CREATE INDEX IF NOT EXISTS idx_notif_queue_unread
  ON "03_notifications"."20_trx_notification_queue" (user_id, tenant_key, is_read)
  WHERE status_code IN ('sent', 'delivered', 'opened', 'clicked') AND is_read = FALSE;

-- ── 4. Index on web_push_subscriptions endpoint for 410 deactivation ─────────

CREATE INDEX IF NOT EXISTS idx_web_push_subs_endpoint
  ON "03_notifications"."13_fct_web_push_subscriptions" (endpoint)
  WHERE is_active = TRUE;

-- ── 5. Index on preferences (skipped — table does not exist yet) ─────────
