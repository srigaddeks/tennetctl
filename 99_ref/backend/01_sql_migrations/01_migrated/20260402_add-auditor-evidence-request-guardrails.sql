-- Auditor evidence request guardrails
-- Seeds control/evidence feature flags and adds uniqueness protection
-- for open auditor evidence requests.

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state,
    initial_audience, env_dev, env_staging, env_prod, created_at, updated_at
)
VALUES
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9003',
        'audit_workspace_control_access',
        'Audit Workspace Control Access',
        'Allows assigned auditors to view engagement-scoped control metadata.',
        'access',
        'permissioned',
        'draft',
        'internal',
        TRUE, FALSE, FALSE,
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9004',
        'audit_workspace_evidence_requests',
        'Audit Workspace Evidence Requests',
        'Allows auditors to request evidence and internal teams to review those requests.',
        'access',
        'permissioned',
        'draft',
        'internal',
        TRUE, FALSE, FALSE,
        now(), now()
    )
ON CONFLICT (code) DO NOTHING;

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
VALUES
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9021',
        'audit_workspace_control_access.view',
        'audit_workspace_control_access',
        'view',
        'Audit Workspace Control Access View',
        'View engagement-scoped controls in the auditor workspace.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9022',
        'audit_workspace_evidence_requests.view',
        'audit_workspace_evidence_requests',
        'view',
        'Audit Workspace Evidence Requests View',
        'View auditor evidence requests in the engagement workflow.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9023',
        'audit_workspace_evidence_requests.create',
        'audit_workspace_evidence_requests',
        'create',
        'Audit Workspace Evidence Requests Create',
        'Create engagement-scoped auditor evidence requests.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9024',
        'audit_workspace_evidence_requests.approve',
        'audit_workspace_evidence_requests',
        'approve',
        'Audit Workspace Evidence Requests Approve',
        'Approve or fulfill auditor evidence requests.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9025',
        'audit_workspace_evidence_requests.revoke',
        'audit_workspace_evidence_requests',
        'revoke',
        'Audit Workspace Evidence Requests Revoke',
        'Revoke or dismiss auditor evidence requests.',
        now(), now()
    )
ON CONFLICT (code) DO NOTHING;

CREATE UNIQUE INDEX IF NOT EXISTS uq_20_trx_auditor_requests_open_control_request
    ON "12_engagements"."20_trx_auditor_requests" (engagement_id, requested_by_token_id, control_id)
    WHERE request_status = 'open'
      AND is_deleted = FALSE
      AND control_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_20_trx_auditor_requests_open_general_request
    ON "12_engagements"."20_trx_auditor_requests" (engagement_id, requested_by_token_id)
    WHERE request_status = 'open'
      AND is_deleted = FALSE
      AND control_id IS NULL;
