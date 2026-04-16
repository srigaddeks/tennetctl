-- ============================================================================
-- 20260409_normalize-check-constraints.sql
-- Normalizes CHECK constraint text representation across all environments.
-- pg_dump serializes ARRAY casts differently depending on PG minor version.
-- Drop + re-add with consistent syntax to eliminate false-positive diffs.
-- Fully idempotent.
-- ============================================================================


-- ── 03_notifications.12_fct_broadcasts ──────────────────────────────────────

ALTER TABLE "03_notifications"."12_fct_broadcasts"
    DROP CONSTRAINT IF EXISTS ck_12_fct_broadcasts_severity;
ALTER TABLE "03_notifications"."12_fct_broadcasts"
    ADD CONSTRAINT ck_12_fct_broadcasts_severity
        CHECK (severity IS NULL OR severity::text = ANY (ARRAY[
            'critical'::text, 'high'::text, 'medium'::text,
            'low'::text, 'info'::text
        ]));


-- ── 05_grc_library.32_lnk_cross_framework_equivalences ─────────────────────

ALTER TABLE "05_grc_library"."32_lnk_cross_framework_equivalences"
    DROP CONSTRAINT IF EXISTS ck_32_lnk_cross_fw_equivalences_conf;
ALTER TABLE "05_grc_library"."32_lnk_cross_framework_equivalences"
    ADD CONSTRAINT ck_32_lnk_cross_fw_equivalences_conf
        CHECK (confidence::text = ANY (ARRAY[
            'high'::text, 'medium'::text, 'low'::text
        ]));

ALTER TABLE "05_grc_library"."32_lnk_cross_framework_equivalences"
    DROP CONSTRAINT IF EXISTS ck_32_lnk_cross_fw_equivalences_type;
ALTER TABLE "05_grc_library"."32_lnk_cross_framework_equivalences"
    ADD CONSTRAINT ck_32_lnk_cross_fw_equivalences_type
        CHECK (equivalence_type::text = ANY (ARRAY[
            'equivalent'::text, 'partial'::text, 'related'::text
        ]));


-- ── 14_risk_registry.41_fct_risk_questionnaire_responses ────────────────────

ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    DROP CONSTRAINT IF EXISTS ck_41_fct_risk_questionnaire_responses_status;
ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    ADD CONSTRAINT ck_41_fct_risk_questionnaire_responses_status
        CHECK (response_status::text = ANY (ARRAY[
            'draft'::text, 'completed'::text
        ]));


-- ── 15_sandbox.80_fct_global_libraries ──────────────────────────────────────

ALTER TABLE "15_sandbox"."80_fct_global_libraries"
    DROP CONSTRAINT IF EXISTS chk_publish_status;
ALTER TABLE "15_sandbox"."80_fct_global_libraries"
    ADD CONSTRAINT chk_publish_status
        CHECK (publish_status::text = ANY (ARRAY[
            'draft'::text, 'review'::text,
            'published'::text, 'deprecated'::text
        ]));


-- ── 20_ai.19_fct_attachments ────────────────────────────────────────────────

ALTER TABLE "20_ai"."19_fct_attachments"
    DROP CONSTRAINT IF EXISTS "19_fct_attachments_status_code_check";
ALTER TABLE "20_ai"."19_fct_attachments"
    ADD CONSTRAINT "19_fct_attachments_status_code_check"
        CHECK (status_code::text = ANY (ARRAY[
            'pending'::text, 'processing'::text,
            'ready'::text, 'failed'::text
        ]));


-- ── 03_notifications.20_trx_notification_queue (index) ──────────────────────
-- The index WHERE clause also has the casting difference.

DROP INDEX IF EXISTS "03_notifications".idx_20_trx_queue_status_scheduled;
CREATE INDEX idx_20_trx_queue_status_scheduled
    ON "03_notifications"."20_trx_notification_queue"
    USING btree (status_code, scheduled_at)
    WHERE status_code::text = ANY (ARRAY['queued'::text, 'failed'::text]);


-- ── 08_tasks.80_vw_task_health ──────────────────────────────────────────────
-- ARRAY cast + parenthesization diff between PG versions. Re-create to normalize.

DROP VIEW IF EXISTS "08_tasks"."80_vw_task_health";
CREATE VIEW "08_tasks"."80_vw_task_health" AS
 SELECT org_id,
    workspace_id,
    tenant_key,
    count(*) FILTER (WHERE (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
           FROM "08_tasks"."04_dim_task_statuses"
          WHERE ("04_dim_task_statuses".is_terminal = true))))) AS total_open_tasks,
    count(*) FILTER (WHERE ((due_date < now()) AND (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
           FROM "08_tasks"."04_dim_task_statuses"
          WHERE ("04_dim_task_statuses".is_terminal = true)))))) AS overdue_count,
    count(*) FILTER (WHERE ((assignee_user_id IS NULL) AND ((priority_code)::text = ANY (ARRAY['critical'::text, 'high'::text])) AND (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
           FROM "08_tasks"."04_dim_task_statuses"
          WHERE ("04_dim_task_statuses".is_terminal = true)))))) AS unassigned_critical_count,
    count(*) FILTER (WHERE ((due_date >= now()) AND (due_date <= (now() + '7 days'::interval)) AND (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
           FROM "08_tasks"."04_dim_task_statuses"
          WHERE ("04_dim_task_statuses".is_terminal = true)))))) AS due_this_week_count,
    round(avg(
        CASE
            WHEN ((due_date < now()) AND (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
               FROM "08_tasks"."04_dim_task_statuses"
              WHERE ("04_dim_task_statuses".is_terminal = true))))) THEN (EXTRACT(epoch FROM (now() - (due_date)::timestamp with time zone)) / (86400)::numeric)
            ELSE NULL::numeric
        END), 1) AS avg_days_overdue,
    jsonb_build_object('critical', count(*) FILTER (WHERE (((priority_code)::text = 'critical'::text) AND (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
           FROM "08_tasks"."04_dim_task_statuses"
          WHERE "04_dim_task_statuses".is_terminal))))), 'high', count(*) FILTER (WHERE (((priority_code)::text = 'high'::text) AND (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
           FROM "08_tasks"."04_dim_task_statuses"
          WHERE "04_dim_task_statuses".is_terminal))))), 'medium', count(*) FILTER (WHERE (((priority_code)::text = 'medium'::text) AND (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
           FROM "08_tasks"."04_dim_task_statuses"
          WHERE "04_dim_task_statuses".is_terminal))))), 'low', count(*) FILTER (WHERE (((priority_code)::text = 'low'::text) AND (NOT ((status_code)::text IN ( SELECT "04_dim_task_statuses".code
           FROM "08_tasks"."04_dim_task_statuses"
          WHERE "04_dim_task_statuses".is_terminal)))))) AS open_by_priority
   FROM "08_tasks"."10_fct_tasks" t
  WHERE (NOT is_deleted)
  GROUP BY org_id, workspace_id, tenant_key;
