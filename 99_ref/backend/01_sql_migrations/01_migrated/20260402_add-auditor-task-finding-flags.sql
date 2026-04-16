-- Auditor task and finding feature-flag rollout
-- Seeds the remaining auditor-workspace feature flags and permissions
-- for engagement-scoped task and finding workflows.

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state,
    initial_audience, env_dev, env_staging, env_prod, created_at, updated_at
)
VALUES
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9005',
        'audit_workspace_auditor_tasks',
        'Audit Workspace Auditor Tasks',
        'Allows engagement-scoped auditor task creation and task access.',
        'access',
        'permissioned',
        'draft',
        'internal',
        TRUE, FALSE, FALSE,
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9006',
        'audit_workspace_auditor_findings',
        'Audit Workspace Auditor Findings',
        'Allows engagement-scoped auditor finding workflows when engagement linkage is ready.',
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
        'ec07be31-5506-4a09-8f9f-7d3d402f9031',
        'audit_workspace_auditor_tasks.view',
        'audit_workspace_auditor_tasks',
        'view',
        'Audit Workspace Auditor Tasks View',
        'View engagement-scoped tasks through the auditor workspace.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9032',
        'audit_workspace_auditor_tasks.create',
        'audit_workspace_auditor_tasks',
        'create',
        'Audit Workspace Auditor Tasks Create',
        'Create engagement-scoped auditor tasks.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9033',
        'audit_workspace_auditor_tasks.assign',
        'audit_workspace_auditor_tasks',
        'assign',
        'Audit Workspace Auditor Tasks Assign',
        'Assign engagement-scoped auditor tasks to active engagement participants.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9034',
        'audit_workspace_auditor_tasks.update',
        'audit_workspace_auditor_tasks',
        'update',
        'Audit Workspace Auditor Tasks Update',
        'Update engagement-scoped auditor tasks.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9041',
        'audit_workspace_auditor_findings.view',
        'audit_workspace_auditor_findings',
        'view',
        'Audit Workspace Auditor Findings View',
        'View engagement-scoped auditor findings.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9042',
        'audit_workspace_auditor_findings.create',
        'audit_workspace_auditor_findings',
        'create',
        'Audit Workspace Auditor Findings Create',
        'Create engagement-scoped auditor findings.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9043',
        'audit_workspace_auditor_findings.update',
        'audit_workspace_auditor_findings',
        'update',
        'Audit Workspace Auditor Findings Update',
        'Update engagement-scoped auditor findings.',
        now(), now()
    )
ON CONFLICT (code) DO NOTHING;
