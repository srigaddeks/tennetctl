-- ─────────────────────────────────────────────────────────────────────────────
-- GRC WORKSPACE ROLES, GROUPS, AND APPROVAL WORKFLOW PERMISSIONS
--
-- Seeds:
--   1. GRC workspace type
--   2. New permission action codes (submit, review, publish, complete, respond, close)
--   3. Task workflow permissions (tasks.submit/review/approve/publish/complete)
--   4. Finding workflow permissions (findings.respond, findings.close)
--   5. 7 GRC workspace-level roles
--   6. Role → permission assignments per role
--
-- UUID ranges used:
--   Action codes:      00000000-0000-0000-0000-000000005030 – 5035
--   GRC roles:         00000000-0000-0000-0000-000000005100 – 5106
--   Task permissions:  00000000-0000-0000-0000-000000008001 – 8007
-- ─────────────────────────────────────────────────────────────────────────────

-- ═════════════════════════════════════════════════════════════════════════════
-- UP =========================================================================
-- ═════════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. GRC workspace type
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."33_dim_workspace_types"
    (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
SELECT
    '00000000-0000-0000-0000-000000001408',
    'grc',
    'GRC',
    'Governance, Risk and Compliance workspace for compliance programs and audit engagements.',
    80,
    FALSE,
    TIMESTAMP '2026-03-30 00:00:00',
    TIMESTAMP '2026-03-30 00:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."33_dim_workspace_types" WHERE code = 'grc'
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. New permission action codes
--    Note: 'approve' already exists from AI permissions seed.
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions"
    (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000005030', 'submit',   'Submit',   'Submit item for review.',               40, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005031', 'review',   'Review',   'Review a submitted item.',              45, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005032', 'publish',  'Publish',  'Publish item to an external party.',    55, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005033', 'complete', 'Complete', 'Mark item as fully complete.',          60, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005034', 'respond',  'Respond',  'Respond to or dispute an item.',        65, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005035', 'close',    'Close',    'Close, accept, or escalate an item.',   70, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Task workflow permissions
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000008001', 'tasks.submit',   'submit',   'task_management', 'Submit Task Evidence',    'Submit task evidence for internal review.',             NOW(), NOW()),
    ('00000000-0000-0000-0000-000000008002', 'tasks.review',   'review',   'task_management', 'Review Task Evidence',    'Review submitted task evidence as control owner.',      NOW(), NOW()),
    ('00000000-0000-0000-0000-000000008003', 'tasks.approve',  'approve',  'task_management', 'Approve Task Evidence',   'Approve reviewed evidence (GRC Lead only).',            NOW(), NOW()),
    ('00000000-0000-0000-0000-000000008004', 'tasks.publish',  'publish',  'task_management', 'Publish Task Evidence',   'Publish approved evidence to the audit engagement.',    NOW(), NOW()),
    ('00000000-0000-0000-0000-000000008005', 'tasks.complete', 'complete', 'task_management', 'Complete Task',           'Mark evidence task as fully complete.',                 NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Finding workflow permissions
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000008006', 'findings.respond', 'respond', 'findings', 'Respond to Finding',  'Submit remediation response or dispute a finding.',   NOW(), NOW()),
    ('00000000-0000-0000-0000-000000008007', 'findings.close',   'close',   'findings', 'Close Finding',       'Close, accept, or escalate a finding.',               NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. GRC workspace-level roles
--    role_level_code = 'workspace' so these are scoped per workspace, not platform-wide
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."16_fct_roles"
    (id, tenant_key, role_level_code, code, name, description,
     scope_org_id, scope_workspace_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
VALUES
    ('00000000-0000-0000-0000-000000005100', '__platform__', 'workspace', 'grc_lead',
     'GRC Lead',
     'Full GRC compliance program ownership: framework activation, evidence approval, task management, and org posture.',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),

    ('00000000-0000-0000-0000-000000005101', '__platform__', 'workspace', 'grc_sme',
     'GRC SME',
     'Compliance specialist: contributes evidence, assigns tasks, views live test results, responds to findings.',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),

    ('00000000-0000-0000-0000-000000005102', '__platform__', 'workspace', 'grc_engineer',
     'Engineer',
     'Remediation only: completes assigned tasks and submits evidence for controls they own.',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),

    ('00000000-0000-0000-0000-000000005103', '__platform__', 'workspace', 'grc_ciso',
     'CISO / Exec',
     'Executive read-only access: posture dashboard, risk register, and framework status.',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),

    ('00000000-0000-0000-0000-000000005104', '__platform__', 'workspace', 'grc_lead_auditor',
     'Lead Auditor',
     'External audit lead: engagement-scoped view of controls and published evidence, raises findings, assigns tasks.',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),

    ('00000000-0000-0000-0000-000000005105', '__platform__', 'workspace', 'grc_staff_auditor',
     'Staff Auditor',
     'External audit staff: engagement-scoped read and internal annotation, findings go to lead for sign-off.',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),

    ('00000000-0000-0000-0000-000000005106', '__platform__', 'workspace', 'grc_vendor',
     'Vendor',
     'Vendor questionnaire access only: no compliance program visibility.',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL)
ON CONFLICT (tenant_key, role_level_code, code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. Role → permission assignments
-- ─────────────────────────────────────────────────────────────────────────────

-- ── 6a. grc_lead — full compliance program + all approval workflow permissions
--    Inherits all 20 GRC core permissions from grc_compliance_lead, plus:
--    assessments/findings (view/create/update/delete) + new workflow codes

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000005100',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    -- GRC core (mirrors grc_compliance_lead)
    'frameworks.view', 'frameworks.create', 'frameworks.update', 'frameworks.delete',
    'controls.view',   'controls.create',   'controls.update',   'controls.delete',
    'tests.view',      'tests.create',      'tests.update',      'tests.delete',
    'risks.view',      'risks.create',      'risks.update',      'risks.delete',
    'tasks.view',      'tasks.create',      'tasks.update',      'tasks.assign',
    -- Assessments & findings
    'assessments.view', 'assessments.create', 'assessments.update', 'assessments.delete',
    'findings.view',    'findings.create',    'findings.update',    'findings.delete',
    -- New workflow
    'tasks.submit', 'tasks.review', 'tasks.approve', 'tasks.publish', 'tasks.complete',
    'findings.respond', 'findings.close'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000005100'
      AND lnk.feature_permission_id = fp.id
);

-- ── 6b. grc_sme — contribute, assign, submit/review, respond to findings

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000005101',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'frameworks.view',
    'controls.view',   'controls.update',
    'tests.view',      'tests.create',   'tests.update',
    'risks.view',      'risks.create',   'risks.update',
    'tasks.view',      'tasks.create',   'tasks.update',  'tasks.assign',
    'tasks.submit',    'tasks.review',
    'assessments.view',
    'findings.view',   'findings.respond'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000005101'
      AND lnk.feature_permission_id = fp.id
);

-- ── 6c. grc_engineer — remediation only (own controls filtered at service layer)

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000005102',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'frameworks.view',
    'controls.view',
    'tests.view',
    'risks.view',
    'tasks.view',    'tasks.update',   'tasks.submit'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000005102'
      AND lnk.feature_permission_id = fp.id
);

-- ── 6d. grc_ciso — executive read-only (no test results, no task operations)

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000005103',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'frameworks.view',
    'controls.view',
    'risks.view',
    'tasks.view',
    'assessments.view'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000005103'
      AND lnk.feature_permission_id = fp.id
);

-- ── 6e. grc_lead_auditor — engagement-scoped (further filtered at service layer)
--    Can see controls/tests/published evidence, assign and complete tasks, raise/close findings

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000005104',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'frameworks.view',
    'controls.view',
    'tests.view',
    'tasks.view',    'tasks.create',   'tasks.assign',  'tasks.complete',
    'assessments.view', 'assessments.create',
    'findings.view', 'findings.create', 'findings.update', 'findings.close'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000005104'
      AND lnk.feature_permission_id = fp.id
);

-- ── 6f. grc_staff_auditor — read + annotate (findings go to lead for sign-off)

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000005105',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'frameworks.view',
    'controls.view',
    'tests.view',
    'tasks.view',
    'assessments.view',
    'findings.view', 'findings.create'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000005105'
      AND lnk.feature_permission_id = fp.id
);

-- ── 6g. grc_vendor — no permissions (questionnaire access handled separately)
--    No INSERT needed — vendor gets zero feature permissions in v1.


-- ═════════════════════════════════════════════════════════════════════════════
-- DOWN =======================================================================
-- ═════════════════════════════════════════════════════════════════════════════

-- -- Remove role-permission links for all 7 GRC workspace roles
-- DELETE FROM "03_auth_manage"."20_lnk_role_feature_permissions"
-- WHERE role_id IN (
--     '00000000-0000-0000-0000-000000005100',
--     '00000000-0000-0000-0000-000000005101',
--     '00000000-0000-0000-0000-000000005102',
--     '00000000-0000-0000-0000-000000005103',
--     '00000000-0000-0000-0000-000000005104',
--     '00000000-0000-0000-0000-000000005105',
--     '00000000-0000-0000-0000-000000005106'
-- );

-- -- Remove GRC workspace roles
-- DELETE FROM "03_auth_manage"."16_fct_roles"
-- WHERE id IN (
--     '00000000-0000-0000-0000-000000005100',
--     '00000000-0000-0000-0000-000000005101',
--     '00000000-0000-0000-0000-000000005102',
--     '00000000-0000-0000-0000-000000005103',
--     '00000000-0000-0000-0000-000000005104',
--     '00000000-0000-0000-0000-000000005105',
--     '00000000-0000-0000-0000-000000005106'
-- );

-- -- Remove new task and finding permissions
-- DELETE FROM "03_auth_manage"."15_dim_feature_permissions"
-- WHERE id IN (
--     '00000000-0000-0000-0000-000000008001',
--     '00000000-0000-0000-0000-000000008002',
--     '00000000-0000-0000-0000-000000008003',
--     '00000000-0000-0000-0000-000000008004',
--     '00000000-0000-0000-0000-000000008005',
--     '00000000-0000-0000-0000-000000008006',
--     '00000000-0000-0000-0000-000000008007'
-- );

-- -- Remove new permission action codes
-- DELETE FROM "03_auth_manage"."12_dim_feature_permission_actions"
-- WHERE id IN (
--     '00000000-0000-0000-0000-000000005030',
--     '00000000-0000-0000-0000-000000005031',
--     '00000000-0000-0000-0000-000000005032',
--     '00000000-0000-0000-0000-000000005033',
--     '00000000-0000-0000-0000-000000005034',
--     '00000000-0000-0000-0000-000000005035'
-- );

-- -- Remove GRC workspace type (only if no workspaces use it)
-- DELETE FROM "03_auth_manage"."33_dim_workspace_types"
-- WHERE id = '00000000-0000-0000-0000-000000001408';
