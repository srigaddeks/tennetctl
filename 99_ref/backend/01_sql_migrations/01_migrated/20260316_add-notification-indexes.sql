-- ─────────────────────────────────────────────────────────────────────────
-- NOTIFICATION SYSTEM: Performance indexes for queue, delivery, and tracking
-- ─────────────────────────────────────────────────────────────────────────

-- Queue processor: status + scheduled_at for batch fetch
CREATE INDEX IF NOT EXISTS idx_20_trx_queue_status_scheduled
    ON "03_notifications"."20_trx_notification_queue" (status_code, scheduled_at)
    WHERE status_code IN ('queued', 'failed');

-- User history + tenant scoped queries
CREATE INDEX IF NOT EXISTS idx_20_trx_queue_tenant_user
    ON "03_notifications"."20_trx_notification_queue" (tenant_key, user_id, created_at DESC);

-- Audit event correlation
CREATE INDEX IF NOT EXISTS idx_20_trx_queue_audit_event
    ON "03_notifications"."20_trx_notification_queue" (source_audit_event_id)
    WHERE source_audit_event_id IS NOT NULL;

-- Delivery log: time-range analytics
CREATE INDEX IF NOT EXISTS idx_21_trx_delivery_log_occurred
    ON "03_notifications"."21_trx_delivery_log" (occurred_at DESC);

-- Tracking events: time-range analytics
CREATE INDEX IF NOT EXISTS idx_22_trx_tracking_events_occurred
    ON "03_notifications"."22_trx_tracking_events" (occurred_at DESC);

-- Broadcasts: tenant list queries
CREATE INDEX IF NOT EXISTS idx_12_fct_broadcasts_tenant
    ON "03_notifications"."12_fct_broadcasts" (tenant_key, created_at DESC)
    WHERE is_deleted = FALSE;

-- Rules: event dispatch lookup
CREATE INDEX IF NOT EXISTS idx_11_fct_rules_event_type
    ON "03_notifications"."11_fct_notification_rules" (tenant_key, source_event_type)
    WHERE is_deleted = FALSE AND is_active = TRUE;

-- Releases: timeline
CREATE INDEX IF NOT EXISTS idx_25_fct_releases_date
    ON "03_notifications"."25_fct_releases" (release_date DESC NULLS LAST)
    WHERE is_deleted = FALSE;

-- Incidents: timeline
CREATE INDEX IF NOT EXISTS idx_26_fct_incidents_started
    ON "03_notifications"."26_fct_incidents" (started_at DESC)
    WHERE is_deleted = FALSE;

-- Preferences: bulk scope queries
CREATE INDEX IF NOT EXISTS idx_17_lnk_prefs_tenant_scope
    ON "03_notifications"."17_lnk_user_notification_preferences" (tenant_key, scope_level);
