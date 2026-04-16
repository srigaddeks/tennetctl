-- Enable auditor workspace capabilities in production.
-- Safe to re-run: only updates the targeted flags and leaves other environments unchanged.

UPDATE "03_auth_manage"."14_dim_feature_flags"
SET env_prod = TRUE,
    updated_at = NOW()
WHERE code IN (
    'audit_workspace_auditor_portfolio',
    'audit_workspace_engagement_membership',
    'audit_workspace_control_access',
    'audit_workspace_evidence_requests',
    'audit_workspace_auditor_tasks',
    'audit_workspace_auditor_findings'
)
  AND env_prod = FALSE;
