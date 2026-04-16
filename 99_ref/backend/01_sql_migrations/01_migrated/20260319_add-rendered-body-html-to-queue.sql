-- Add rendered_body_html column to notification queue for separate HTML storage
-- rendered_body stores plain text fallback, rendered_body_html stores full HTML email

ALTER TABLE "03_notifications"."20_trx_notification_queue"
  ADD COLUMN IF NOT EXISTS rendered_body_html TEXT NULL;
