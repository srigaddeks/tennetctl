-- Migration: Audit Event Retention Policies
-- Phase: v0.1.8 Compliance
-- Date: 2026-04-21
-- Purpose: Enable regulated organizations to enforce automatic retention/purge of audit logs.
--          Supports configurable retention periods (7 days to 7 years) with critical event carve-out.

-- Table: fct_audit_retention_policies
-- Org-level retention policy defining how long audit events are kept before purge.
CREATE TABLE 04_audit.fct_audit_retention_policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL UNIQUE REFERENCES 03_iam.fct_orgs(org_id),
    retention_days INTEGER NOT NULL DEFAULT 365 CHECK (retention_days >= 7 AND retention_days <= 2555),
    auto_purge_enabled BOOLEAN NOT NULL DEFAULT true,
    exclude_critical BOOLEAN NOT NULL DEFAULT true,  -- Never purge category IN ('security', 'compliance')
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    last_purge_at TIMESTAMP DEFAULT NULL,
    next_purge_scheduled_at TIMESTAMP DEFAULT NULL,
    purge_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL REFERENCES 03_iam.fct_users(user_id),
    is_test BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_audit_retention_policies_org_id ON 04_audit.fct_audit_retention_policies(org_id);
CREATE INDEX idx_audit_retention_policies_status ON 04_audit.fct_audit_retention_policies(status);

-- Table: evt_audit_purge_jobs
-- Append-only log of purge jobs (either manual trigger or automatic nightly).
CREATE TABLE 04_audit.evt_audit_purge_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES 04_audit.fct_audit_retention_policies(policy_id),
    status TEXT NOT NULL DEFAULT 'requested' CHECK (status IN ('requested', 'in_progress', 'completed', 'failed')),
    rows_purged INTEGER DEFAULT NULL,
    error_message TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT NULL,
    created_by UUID NOT NULL REFERENCES 03_iam.fct_users(user_id),
    is_test BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_audit_purge_jobs_policy_id ON 04_audit.evt_audit_purge_jobs(policy_id);
CREATE INDEX idx_audit_purge_jobs_status ON 04_audit.evt_audit_purge_jobs(status);
CREATE INDEX idx_audit_purge_jobs_created_at ON 04_audit.evt_audit_purge_jobs(created_at);

-- View: v_audit_retention_policies
-- Org-scoped view with human-readable status.
CREATE VIEW 04_audit.v_audit_retention_policies AS
SELECT
    p.policy_id,
    p.org_id,
    p.retention_days,
    p.auto_purge_enabled,
    p.exclude_critical,
    p.status,
    p.last_purge_at,
    p.next_purge_scheduled_at,
    p.purge_count,
    p.created_at,
    p.updated_at,
    COALESCE(MAX(u.email) FILTER (WHERE EXISTS (SELECT 1 FROM 03_iam.fct_users)), 'system') AS created_by_email
FROM 04_audit.fct_audit_retention_policies p
LEFT JOIN 03_iam.fct_users u ON p.created_by = u.user_id
GROUP BY p.policy_id;

-- View: v_audit_purge_jobs
-- Job history with counts.
CREATE VIEW 04_audit.v_audit_purge_jobs AS
SELECT
    j.job_id,
    j.policy_id,
    p.org_id,
    j.status,
    j.rows_purged,
    j.error_message,
    j.created_at,
    j.completed_at
FROM 04_audit.evt_audit_purge_jobs j
LEFT JOIN 04_audit.fct_audit_retention_policies p ON j.policy_id = p.policy_id;

-- Seed default policies (permissive: 1 year retention, auto-purge disabled by default).
-- Orgs can override at any time.
INSERT INTO 04_audit.fct_audit_retention_policies
(org_id, retention_days, auto_purge_enabled, exclude_critical, status, created_by)
SELECT DISTINCT org_id, 365, false, true, 'active', (SELECT MIN(user_id) FROM 03_iam.fct_users)
FROM 03_iam.fct_orgs
ON CONFLICT (org_id) DO NOTHING;
