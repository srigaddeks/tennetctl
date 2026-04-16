-- =============================================================================
-- Migration: 20260406_sync-full-env-parity.sql
-- Description:
--   Brings dev, staging, and prod into complete schema parity.
--   All statements are idempotent — safe to run on any environment.
--
--   Dev → staging/prod:
--     1. 9 notification indexes (03_notifications)
--     2. 2 sandbox FK constraints (fk_25_trx_sandbox_runs_dataset, _session)
--     3. Strengthen fk_46_fct_api_keys_user_id + _status_id to ON DELETE RESTRICT
--
--   Staging/prod → dev:
--     4. idx_46_fct_api_keys_user_tenant index
--     5. idx_12_fct_task_criteria_task index (already in prev migration, re-stated for safety)
--     6. ck_25_trx_runs_exec_time CHECK constraint
--     7. 19_fct_attachments_status_code_check CHECK constraint (20_ai schema)
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Notification indexes (dev → staging/prod)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_12_fct_broadcasts_tenant
    ON "03_notifications"."12_fct_broadcasts" USING btree (tenant_key, created_at DESC)
    WHERE (is_deleted = false);

CREATE INDEX IF NOT EXISTS idx_17_lnk_prefs_tenant_scope
    ON "03_notifications"."17_lnk_user_notification_preferences" USING btree (tenant_key, scope_level);

CREATE INDEX IF NOT EXISTS idx_20_trx_queue_audit_event
    ON "03_notifications"."20_trx_notification_queue" USING btree (source_audit_event_id)
    WHERE (source_audit_event_id IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_20_trx_queue_status_scheduled
    ON "03_notifications"."20_trx_notification_queue" USING btree (status_code, scheduled_at)
    WHERE (status_code IN ('queued', 'failed'));

CREATE INDEX IF NOT EXISTS idx_20_trx_queue_tenant_user
    ON "03_notifications"."20_trx_notification_queue" USING btree (tenant_key, user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_21_trx_delivery_log_occurred
    ON "03_notifications"."21_trx_delivery_log" USING btree (occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_22_trx_tracking_events_occurred
    ON "03_notifications"."22_trx_tracking_events" USING btree (occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_25_fct_releases_date
    ON "03_notifications"."25_fct_releases" USING btree (release_date DESC NULLS LAST)
    WHERE (is_deleted = false);

CREATE INDEX IF NOT EXISTS idx_26_fct_incidents_started
    ON "03_notifications"."26_fct_incidents" USING btree (started_at DESC)
    WHERE (is_deleted = false);


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Sandbox FK constraints (dev → staging/prod)
--    DO block checks pg_constraint to avoid duplicate FK errors.
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_25_trx_sandbox_runs_dataset'
          AND conrelid = '"15_sandbox"."25_trx_sandbox_runs"'::regclass
    ) THEN
        ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
            ADD CONSTRAINT fk_25_trx_sandbox_runs_dataset
            FOREIGN KEY (dataset_id) REFERENCES "15_sandbox"."21_fct_datasets"(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_25_trx_sandbox_runs_session'
          AND conrelid = '"15_sandbox"."25_trx_sandbox_runs"'::regclass
    ) THEN
        ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
            ADD CONSTRAINT fk_25_trx_sandbox_runs_session
            FOREIGN KEY (live_session_id) REFERENCES "15_sandbox"."28_fct_live_sessions"(id);
    END IF;
END
$$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Strengthen API key FKs to ON DELETE RESTRICT (dev → staging/prod)
--    Drop plain FK, re-add with RESTRICT. Idempotent via IF EXISTS + NOT EXISTS.
-- ─────────────────────────────────────────────────────────────────────────────

-- 3a. fk_46_fct_api_keys_user_id
DO $$
DECLARE
    v_confdeltype char;
BEGIN
    SELECT confdeltype INTO v_confdeltype
    FROM pg_constraint
    WHERE conname = 'fk_46_fct_api_keys_user_id'
      AND conrelid = '"03_auth_manage"."46_fct_api_keys"'::regclass;

    -- 'r' = RESTRICT, 'a' = NO ACTION (default)
    IF v_confdeltype IS NOT NULL AND v_confdeltype <> 'r' THEN
        ALTER TABLE "03_auth_manage"."46_fct_api_keys"
            DROP CONSTRAINT fk_46_fct_api_keys_user_id;
        ALTER TABLE "03_auth_manage"."46_fct_api_keys"
            ADD CONSTRAINT fk_46_fct_api_keys_user_id
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id)
            ON DELETE RESTRICT;
    END IF;
END
$$;

-- 3b. fk_46_fct_api_keys_status_id
DO $$
DECLARE
    v_confdeltype char;
BEGIN
    SELECT confdeltype INTO v_confdeltype
    FROM pg_constraint
    WHERE conname = 'fk_46_fct_api_keys_status_id'
      AND conrelid = '"03_auth_manage"."46_fct_api_keys"'::regclass;

    IF v_confdeltype IS NOT NULL AND v_confdeltype <> 'r' THEN
        ALTER TABLE "03_auth_manage"."46_fct_api_keys"
            DROP CONSTRAINT fk_46_fct_api_keys_status_id;
        ALTER TABLE "03_auth_manage"."46_fct_api_keys"
            ADD CONSTRAINT fk_46_fct_api_keys_status_id
            FOREIGN KEY (status_id) REFERENCES "03_auth_manage"."45_dim_api_key_statuses"(id)
            ON DELETE RESTRICT;
    END IF;
END
$$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Missing index on dev (staging/prod → dev)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_46_fct_api_keys_user_tenant
    ON "03_auth_manage"."46_fct_api_keys" USING btree (user_id, tenant_key);

-- Re-stated for safety (was in previous migration but may not have applied to dev)
CREATE INDEX IF NOT EXISTS idx_12_fct_task_criteria_task
    ON "08_tasks"."12_fct_task_criteria" USING btree (task_id)
    WHERE (is_deleted = false);


-- ─────────────────────────────────────────────────────────────────────────────
-- 5. Missing CHECK constraints on dev (staging/prod → dev)
-- ─────────────────────────────────────────────────────────────────────────────

-- 5a. ck_25_trx_runs_exec_time on 15_sandbox.25_trx_sandbox_runs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_25_trx_runs_exec_time'
          AND conrelid = '"15_sandbox"."25_trx_sandbox_runs"'::regclass
    ) THEN
        ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
            ADD CONSTRAINT ck_25_trx_runs_exec_time
            CHECK (execution_time_ms IS NULL OR execution_time_ms >= 0);
    END IF;
END
$$;

-- 5b. 19_fct_attachments_status_code_check on 20_ai.19_fct_attachments
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = '19_fct_attachments_status_code_check'
          AND conrelid = '"20_ai"."19_fct_attachments"'::regclass
    ) THEN
        ALTER TABLE "20_ai"."19_fct_attachments"
            ADD CONSTRAINT "19_fct_attachments_status_code_check"
            CHECK (status_code IN ('pending', 'processing', 'ready', 'failed'));
    END IF;
END
$$;
