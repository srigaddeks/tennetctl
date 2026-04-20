-- Migration: GDPR DSAR — Export + Delete Job Tracking
-- Phase: 45-01
-- Date: 2026-04-21
-- Purpose: Audit-tracked export and delete operations for GDPR/CCPA compliance.
--          Immutable event table for job lifecycle; users can request account export/delete via operator.

-- Table: evt_dsar_jobs
-- Append-only event table tracking DSAR (Data Subject Access Request) operations.
-- job_type: export | delete
-- status: requested | in_progress | completed | failed
-- result_location: vault key (e.g., iam.dsar.{job_id}) where export JSON is stored
CREATE TABLE 03_iam.evt_dsar_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL CHECK (job_type IN ('export', 'delete')),
    actor_user_id UUID NOT NULL REFERENCES 03_iam.fct_users(user_id),
    subject_user_id UUID NOT NULL REFERENCES 03_iam.fct_users(user_id),
    org_id UUID NOT NULL REFERENCES 03_iam.fct_orgs(org_id),
    status TEXT NOT NULL DEFAULT 'requested' CHECK (status IN ('requested', 'in_progress', 'completed', 'failed')),
    row_counts JSONB DEFAULT NULL,  -- {"user": 1, "org": 3, "audit_events": 127, ...}
    error_message TEXT DEFAULT NULL,
    result_location TEXT DEFAULT NULL,  -- vault key for export, null for delete
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT NULL,
    created_by UUID NOT NULL REFERENCES 03_iam.fct_users(user_id),
    is_test BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_evt_dsar_jobs_subject_user_id ON 03_iam.evt_dsar_jobs(subject_user_id);
CREATE INDEX idx_evt_dsar_jobs_org_id ON 03_iam.evt_dsar_jobs(org_id);
CREATE INDEX idx_evt_dsar_jobs_status ON 03_iam.evt_dsar_jobs(status);
CREATE INDEX idx_evt_dsar_jobs_created_at ON 03_iam.evt_dsar_jobs(created_at);

-- View: v_dsar_jobs
-- Org-scoped view of DSAR jobs with actor display name resolved.
CREATE VIEW 03_iam.v_dsar_jobs AS
SELECT
    j.job_id,
    j.job_type,
    j.actor_user_id,
    COALESCE(MAX(actor.display_name) FILTER (WHERE ad_actor.code = 'display_name'), 'unknown') AS actor_display_name,
    j.subject_user_id,
    COALESCE(MAX(subject.display_name) FILTER (WHERE ad_subject.code = 'display_name'), 'unknown') AS subject_display_name,
    j.org_id,
    j.status,
    j.row_counts,
    j.error_message,
    j.result_location,
    j.created_at,
    j.completed_at,
    j.is_test
FROM 03_iam.evt_dsar_jobs j
LEFT JOIN 03_iam.fct_users actor ON j.actor_user_id = actor.user_id
LEFT JOIN 03_iam.dtl_user_attrs actor_attr ON actor.user_id = actor_attr.user_id AND actor_attr.key_text = 'display_name'
LEFT JOIN 03_iam.dim_attr_defs ad_actor ON actor_attr.attr_def_id = ad_actor.attr_def_id
LEFT JOIN 03_iam.fct_users subject ON j.subject_user_id = subject.user_id
LEFT JOIN 03_iam.dtl_user_attrs subject_attr ON subject.user_id = subject_attr.user_id AND subject_attr.key_text = 'display_name'
LEFT JOIN 03_iam.dim_attr_defs ad_subject ON subject_attr.attr_def_id = ad_subject.attr_def_id
GROUP BY j.job_id, actor.user_id, subject.user_id;

-- Seed: dim_dsar_job_statuses
INSERT INTO 03_iam.dim_dsar_job_statuses (status_id, code, display_name, description) VALUES
(1, 'requested', 'Requested', 'DSAR job request received'),
(2, 'in_progress', 'In Progress', 'Job is being processed'),
(3, 'completed', 'Completed', 'Job completed successfully'),
(4, 'failed', 'Failed', 'Job failed with error')
ON CONFLICT DO NOTHING;
