-- =============================================================================
-- staging_cleanup.sql
-- Removes test/dev data from staging (and prod before go-live).
-- Keeps: system admin user, system org, system workspaces, all roles/groups/flags.
-- Removes: robot test users, all dev test orgs/workspaces and their data.
-- Safe to re-run (WHERE guards prevent double-deletes).
-- =============================================================================

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- Collect IDs to delete
-- ─────────────────────────────────────────────────────────────────────────────

-- Keep these real user emails
CREATE TEMP TABLE _keep_emails (email text);
INSERT INTO _keep_emails VALUES
    ('admin@kreesalis.com'),
    ('sri.gadde@kreesalis.com'),
    ('sak@kreesalis.com'),
    ('saklesh@kreesalis.com'),
    ('saaigoud8@gmail.com');

-- Users to delete (not system, not in keep list)
CREATE TEMP TABLE _del_users AS
SELECT u.id
FROM "03_auth_manage"."03_fct_users" u
WHERE u.is_system = FALSE
  AND u.id NOT IN (
      SELECT user_id FROM "03_auth_manage"."05_dtl_user_properties"
      WHERE property_key = 'email' AND property_value IN (SELECT email FROM _keep_emails)
  );

-- Non-system orgs to delete
CREATE TEMP TABLE _del_orgs AS
SELECT id FROM "03_auth_manage"."29_fct_orgs" WHERE is_system = FALSE;

-- Non-system workspaces to delete
CREATE TEMP TABLE _del_ws AS
SELECT id FROM "03_auth_manage"."34_fct_workspaces" WHERE is_system = FALSE;

-- ─────────────────────────────────────────────────────────────────────────────
-- Delete user dependents (FK order: deepest first)
-- ─────────────────────────────────────────────────────────────────────────────

-- Notification tables
DELETE FROM "03_notifications"."17_lnk_user_notification_preferences" WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_notifications"."13_fct_web_push_subscriptions"        WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_notifications"."23_trx_inactivity_snapshots"          WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_notifications"."20_trx_notification_queue"            WHERE user_id IN (SELECT id FROM _del_users);

-- Auth tables (old schema)
DELETE FROM "03_auth_manage"."12_trx_auth_challenges" WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."11_trx_login_attempts"  WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."10_trx_auth_sessions"   WHERE user_id IN (SELECT id FROM _del_users) OR impersonator_user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."21_trx_access_context_events" WHERE user_id IN (SELECT id FROM _del_users);

-- Auth tables (new passwordless schema)
DELETE FROM "03_auth_manage"."08_trx_auth_challenges" WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."07_trx_login_attempts"  WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."06_trx_auth_sessions"   WHERE user_id IN (SELECT id FROM _del_users);

-- Account properties then accounts
DELETE FROM "03_auth_manage"."09_dtl_user_account_properties"
WHERE user_account_id IN (
    SELECT id FROM "03_auth_manage"."08_dtl_user_accounts" WHERE user_id IN (SELECT id FROM _del_users)
);
DELETE FROM "03_auth_manage"."08_dtl_user_accounts" WHERE user_id IN (SELECT id FROM _del_users);

-- User properties, identities, credentials
DELETE FROM "03_auth_manage"."05_dtl_user_properties"  WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."04_dtl_user_identities"  WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."05_dtl_user_credentials" WHERE user_id IN (SELECT id FROM _del_users);

-- API keys
DELETE FROM "03_auth_manage"."46_fct_api_keys" WHERE user_id IN (SELECT id FROM _del_users);

-- Memberships
DELETE FROM "03_auth_manage"."26_lnk_product_memberships"  WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."36_lnk_workspace_memberships" WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."31_lnk_org_memberships"       WHERE user_id IN (SELECT id FROM _del_users);
DELETE FROM "03_auth_manage"."18_lnk_group_memberships"     WHERE user_id IN (SELECT id FROM _del_users);

-- GRC role assignments
DELETE FROM "03_auth_manage"."48_lnk_grc_access_grants"
WHERE grc_role_assignment_id IN (
    SELECT id FROM "03_auth_manage"."47_lnk_grc_role_assignments"
    WHERE user_id IN (SELECT id FROM _del_users)
);
DELETE FROM "03_auth_manage"."47_lnk_grc_role_assignments" WHERE user_id IN (SELECT id FROM _del_users);

-- Invitations (by email)
DELETE FROM "03_auth_manage"."44_trx_invitations"
WHERE email IN (
    SELECT property_value FROM "03_auth_manage"."05_dtl_user_properties"
    WHERE property_key = 'email'
      AND user_id IN (
          SELECT id FROM "03_auth_manage"."03_fct_users"
          WHERE is_system = FALSE
            AND id NOT IN (
                SELECT user_id FROM "03_auth_manage"."05_dtl_user_properties"
                WHERE property_key = 'email' AND property_value IN (SELECT email FROM _keep_emails)
            )
      )
);

-- Users
DELETE FROM "03_auth_manage"."03_fct_users" WHERE id IN (SELECT id FROM _del_users);

-- ─────────────────────────────────────────────────────────────────────────────
-- Delete org/workspace dependents
-- ─────────────────────────────────────────────────────────────────────────────

-- Engagement data
DO $$
DECLARE _eng uuid[];
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='12_engagements' AND table_name='10_fct_audit_engagements') THEN
        SELECT ARRAY_AGG(id) INTO _eng FROM "12_engagements"."10_fct_audit_engagements"
        WHERE org_id IN (SELECT id FROM _del_orgs);
        IF _eng IS NOT NULL THEN
            DELETE FROM "12_engagements"."21_trx_auditor_verifications" WHERE engagement_id = ANY(_eng);
            DELETE FROM "12_engagements"."22_lnk_engagement_controls"   WHERE engagement_id = ANY(_eng);
            DELETE FROM "12_engagements"."23_dtl_engagement_properties" WHERE engagement_id = ANY(_eng);
            DELETE FROM "12_engagements"."11_fct_audit_access_tokens"   WHERE engagement_id = ANY(_eng);
            DELETE FROM "12_engagements"."10_fct_audit_engagements"     WHERE id = ANY(_eng);
        END IF;
    END IF;
END $$;

-- Tasks
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='08_tasks' AND table_name='01_fct_tasks') THEN
        DELETE FROM "08_tasks"."01_fct_tasks" WHERE org_id IN (SELECT id FROM _del_orgs);
    END IF;
END $$;

-- Comments (uses tenant_key, not org_id — delete all non-default tenant data)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='08_comments' AND table_name='01_fct_comments') THEN
        DELETE FROM "08_comments"."01_fct_comments" WHERE tenant_key <> 'default' OR is_deleted = TRUE;
    END IF;
END $$;

-- Attachments (uses tenant_key)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='09_attachments' AND table_name='01_fct_attachments') THEN
        DELETE FROM "09_attachments"."01_fct_attachments" WHERE tenant_key <> 'default' OR is_deleted = TRUE;
    END IF;
END $$;

-- GRC role assignments (org-level)
DELETE FROM "03_auth_manage"."48_lnk_grc_access_grants"
WHERE grc_role_assignment_id IN (
    SELECT id FROM "03_auth_manage"."47_lnk_grc_role_assignments"
    WHERE org_id IN (SELECT id FROM _del_orgs)
);
DELETE FROM "03_auth_manage"."47_lnk_grc_role_assignments" WHERE org_id IN (SELECT id FROM _del_orgs);

-- GRC library data (frameworks, control tests scoped to these orgs/workspaces)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='05_grc_library' AND table_name='10_fct_frameworks') THEN
        -- Null out workspace/org scope on frameworks (they are global library items, just unscope them)
        UPDATE "05_grc_library"."10_fct_frameworks"
        SET scope_workspace_id = NULL, scope_org_id = NULL
        WHERE scope_workspace_id IN (SELECT id FROM _del_ws)
           OR scope_org_id IN (SELECT id FROM _del_orgs);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='05_grc_library' AND table_name='14_fct_control_tests') THEN
        UPDATE "05_grc_library"."14_fct_control_tests"
        SET scope_workspace_id = NULL, scope_org_id = NULL
        WHERE scope_workspace_id IN (SELECT id FROM _del_ws)
           OR scope_org_id IN (SELECT id FROM _del_orgs);
    END IF;
END $$;

-- Tasks (08_tasks uses both org_id and workspace_id)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='08_tasks' AND table_name='10_fct_tasks') THEN
        DELETE FROM "08_tasks"."10_fct_tasks"
        WHERE org_id IN (SELECT id FROM _del_orgs)
           OR workspace_id IN (SELECT id FROM _del_ws);
    END IF;
    -- Old task table name
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='08_tasks' AND table_name='01_fct_tasks') THEN
        DELETE FROM "08_tasks"."01_fct_tasks"
        WHERE org_id IN (SELECT id FROM _del_orgs);
    END IF;
END $$;

-- Risk registry
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='14_risk_registry' AND table_name='10_fct_risks') THEN
        DELETE FROM "14_risk_registry"."41_fct_risk_questionnaire_responses"
        WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
        WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "14_risk_registry"."10_fct_risks"
        WHERE org_id IN (SELECT id FROM _del_orgs);
    END IF;
END $$;

-- Sandbox (org-scoped)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='15_sandbox' AND table_name='20_fct_connector_instances') THEN
        DELETE FROM "15_sandbox"."20_fct_connector_instances" WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "15_sandbox"."21_fct_datasets"            WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "15_sandbox"."22_fct_signals"             WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "15_sandbox"."23_fct_threat_types"        WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "15_sandbox"."24_fct_policies"            WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "15_sandbox"."28_fct_live_sessions"       WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "15_sandbox"."29_fct_libraries"           WHERE org_id IN (SELECT id FROM _del_orgs);
        DELETE FROM "15_sandbox"."70_fct_ssf_streams"         WHERE org_id IN (SELECT id FROM _del_orgs);
    END IF;
END $$;

-- AI builder sessions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='20_ai' AND table_name='60_fct_builder_sessions') THEN
        DELETE FROM "20_ai"."60_fct_builder_sessions"
        WHERE scope_org_id IN (SELECT id FROM _del_orgs)
           OR scope_workspace_id IN (SELECT id FROM _del_ws);
    END IF;
END $$;

-- Roles scoped to these orgs/workspaces (workspace-level GRC roles from old pattern)
UPDATE "03_auth_manage"."16_fct_roles"
SET scope_org_id = NULL, scope_workspace_id = NULL
WHERE scope_org_id IN (SELECT id FROM _del_orgs)
   OR scope_workspace_id IN (SELECT id FROM _del_ws);

-- Workspace memberships and settings
DELETE FROM "03_auth_manage"."36_lnk_workspace_memberships" WHERE workspace_id IN (SELECT id FROM _del_ws);
DELETE FROM "03_auth_manage"."35_dtl_workspace_settings"    WHERE workspace_id IN (SELECT id FROM _del_ws);

-- Org memberships and settings
DELETE FROM "03_auth_manage"."31_lnk_org_memberships" WHERE org_id IN (SELECT id FROM _del_orgs);
DELETE FROM "03_auth_manage"."30_dtl_org_settings"    WHERE org_id IN (SELECT id FROM _del_orgs);

-- Pending invitations for these orgs
DELETE FROM "03_auth_manage"."44_trx_invitations" WHERE org_id IN (SELECT id FROM _del_orgs);

-- Hard-delete scoped user groups for these orgs/workspaces (old per-org UUID-prefix groups)
-- These were already soft-deleted by the reconcile migration; remove FKs so orgs/workspaces can be deleted
DELETE FROM "03_auth_manage"."18_lnk_group_memberships"
WHERE group_id IN (
    SELECT id FROM "03_auth_manage"."17_fct_user_groups"
    WHERE scope_workspace_id IN (SELECT id FROM _del_ws)
       OR scope_org_id IN (SELECT id FROM _del_orgs)
);
DELETE FROM "03_auth_manage"."19_lnk_group_role_assignments"
WHERE group_id IN (
    SELECT id FROM "03_auth_manage"."17_fct_user_groups"
    WHERE scope_workspace_id IN (SELECT id FROM _del_ws)
       OR scope_org_id IN (SELECT id FROM _del_orgs)
);
DELETE FROM "03_auth_manage"."17_fct_user_groups"
WHERE scope_workspace_id IN (SELECT id FROM _del_ws)
   OR scope_org_id IN (SELECT id FROM _del_orgs);

-- Workspaces then orgs
DELETE FROM "03_auth_manage"."34_fct_workspaces" WHERE id IN (SELECT id FROM _del_ws);
DELETE FROM "03_auth_manage"."29_fct_orgs"       WHERE id IN (SELECT id FROM _del_orgs);

-- ─────────────────────────────────────────────────────────────────────────────
-- Clear remaining test noise
-- ─────────────────────────────────────────────────────────────────────────────

-- Robot test invitations
DELETE FROM "03_auth_manage"."44_trx_invitations" WHERE email LIKE '%@example.com';

-- Notification queue
DELETE FROM "03_notifications"."20_trx_notification_queue";

-- AI job queue and reports
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='20_ai' AND table_name='45_fct_job_queue') THEN
        DELETE FROM "20_ai"."45_fct_job_queue";
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='20_ai' AND table_name='50_fct_reports') THEN
        DELETE FROM "20_ai"."50_fct_reports";
    END IF;
END $$;

DROP TABLE _del_ws;
DROP TABLE _del_orgs;
DROP TABLE _del_users;
DROP TABLE _keep_emails;

-- ─────────────────────────────────────────────────────────────────────────────
-- Summary
-- ─────────────────────────────────────────────────────────────────────────────
SELECT 'users remaining'      as entity, COUNT(*) as count FROM "03_auth_manage"."03_fct_users"      WHERE is_deleted = FALSE
UNION ALL
SELECT 'orgs remaining',                 COUNT(*)           FROM "03_auth_manage"."29_fct_orgs"       WHERE deleted_at IS NULL
UNION ALL
SELECT 'workspaces remaining',           COUNT(*)           FROM "03_auth_manage"."34_fct_workspaces" WHERE deleted_at IS NULL
UNION ALL
SELECT 'roles',                          COUNT(*)           FROM "03_auth_manage"."16_fct_roles"      WHERE is_deleted = FALSE
UNION ALL
SELECT 'groups',                         COUNT(*)           FROM "03_auth_manage"."17_fct_user_groups" WHERE is_deleted = FALSE
UNION ALL
SELECT 'feature_flags',                  COUNT(*)           FROM "03_auth_manage"."14_dim_feature_flags";

COMMIT;
