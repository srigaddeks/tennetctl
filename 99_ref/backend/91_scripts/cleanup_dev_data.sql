-- =============================================================================
-- DEV DATA CLEANUP SCRIPT (non-transactional, handles FK chains)
-- Purpose: Remove all robot/test/example data from the dev database.
-- =============================================================================

-- 1. Identify test data
CREATE TEMP TABLE _test_user_ids AS
SELECT DISTINCT u.id AS user_id
FROM "03_auth_manage"."03_fct_users" u
JOIN "03_auth_manage"."05_dtl_user_properties" p
  ON p.user_id = u.id AND p.property_key = 'email'
WHERE p.property_value LIKE 'robot_%'
   OR p.property_value LIKE 'robot-%'
   OR p.property_value LIKE '%@example.com'
   OR p.property_value LIKE 'collector.%@%';

CREATE TEMP TABLE _test_org_ids AS
SELECT id AS org_id FROM "03_auth_manage"."29_fct_orgs"
WHERE name LIKE 'Robot%' OR name LIKE 'robot%';

CREATE TEMP TABLE _test_ws_ids AS
SELECT id AS ws_id FROM "03_auth_manage"."34_fct_workspaces"
WHERE org_id IN (SELECT org_id FROM _test_org_ids);

-- 2. Clean user-related data
DELETE FROM "03_auth_manage"."10_trx_auth_sessions" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."11_trx_login_attempts" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."12_trx_auth_challenges" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."21_trx_access_context_events" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."18_lnk_group_memberships" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."36_lnk_workspace_memberships" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."31_lnk_org_memberships" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."48_lnk_grc_access_grants" WHERE grc_role_assignment_id IN (SELECT id FROM "03_auth_manage"."47_lnk_grc_role_assignments" WHERE user_id IN (SELECT user_id FROM _test_user_ids));
DELETE FROM "03_auth_manage"."47_lnk_grc_role_assignments" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."09_dtl_user_account_properties" WHERE user_account_id IN (SELECT id FROM "03_auth_manage"."08_dtl_user_accounts" WHERE user_id IN (SELECT user_id FROM _test_user_ids));
DELETE FROM "03_auth_manage"."08_dtl_user_accounts" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."05_dtl_user_properties" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."41_dtl_audit_event_properties" WHERE event_id IN (SELECT id FROM "03_auth_manage"."40_aud_events" WHERE actor_id IN (SELECT user_id FROM _test_user_ids));
DELETE FROM "03_auth_manage"."40_aud_events" WHERE actor_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."44_trx_invitations" WHERE invited_by IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."44_trx_invitations" WHERE email IN (SELECT p.property_value FROM "03_auth_manage"."05_dtl_user_properties" p WHERE p.user_id IN (SELECT user_id FROM _test_user_ids) AND p.property_key = 'email');
DELETE FROM "03_notifications"."20_trx_notification_queue" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."46_fct_api_keys" WHERE user_id IN (SELECT user_id FROM _test_user_ids);
DELETE FROM "03_auth_manage"."45_fct_invite_campaigns" WHERE created_by IN (SELECT user_id FROM _test_user_ids);

-- 3. Clean tasks referencing test users or test workspaces
DELETE FROM "08_tasks"."32_lnk_task_dependencies" WHERE task_id IN (SELECT id FROM "08_tasks"."10_fct_tasks" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids) OR reporter_user_id IN (SELECT user_id FROM _test_user_ids));
DELETE FROM "08_tasks"."31_lnk_task_assignments" WHERE task_id IN (SELECT id FROM "08_tasks"."10_fct_tasks" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids) OR reporter_user_id IN (SELECT user_id FROM _test_user_ids));
DELETE FROM "08_tasks"."30_trx_task_events" WHERE task_id IN (SELECT id FROM "08_tasks"."10_fct_tasks" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids) OR reporter_user_id IN (SELECT user_id FROM _test_user_ids));
DELETE FROM "08_tasks"."20_dtl_task_properties" WHERE task_id IN (SELECT id FROM "08_tasks"."10_fct_tasks" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids) OR reporter_user_id IN (SELECT user_id FROM _test_user_ids));
DELETE FROM "08_tasks"."10_fct_tasks" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids) OR reporter_user_id IN (SELECT user_id FROM _test_user_ids);

-- 4. Clean risk registry in test workspaces
DELETE FROM "14_risk_registry"."41_fct_risk_questionnaire_responses" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids);
DELETE FROM "14_risk_registry"."39_lnk_risk_questionnaire_assignments" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids);
DELETE FROM "14_risk_registry"."11_fct_risk_treatment_plans" WHERE risk_id IN (SELECT id FROM "14_risk_registry"."10_fct_risks" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids));
DELETE FROM "14_risk_registry"."10_fct_risks" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids);

-- 5. Clean frameworks/builder sessions scoped to test workspaces
UPDATE "05_grc_library"."10_fct_frameworks" SET scope_workspace_id = NULL WHERE scope_workspace_id IN (SELECT ws_id FROM _test_ws_ids);
UPDATE "05_grc_library"."14_fct_control_tests" SET scope_workspace_id = NULL WHERE scope_workspace_id IN (SELECT ws_id FROM _test_ws_ids);
UPDATE "03_auth_manage"."16_fct_roles" SET scope_workspace_id = NULL WHERE scope_workspace_id IN (SELECT ws_id FROM _test_ws_ids);
DELETE FROM "20_ai"."60_fct_builder_sessions" WHERE scope_workspace_id IN (SELECT ws_id FROM _test_ws_ids);

-- 6. Delete test users
DELETE FROM "03_auth_manage"."03_fct_users" WHERE id IN (SELECT user_id FROM _test_user_ids);

-- 7. Clean test org workspace data
DELETE FROM "03_auth_manage"."19_lnk_group_role_assignments" WHERE group_id IN (SELECT id FROM "03_auth_manage"."17_fct_user_groups" WHERE scope_workspace_id IN (SELECT ws_id FROM _test_ws_ids));
DELETE FROM "03_auth_manage"."18_lnk_group_memberships" WHERE group_id IN (SELECT id FROM "03_auth_manage"."17_fct_user_groups" WHERE scope_workspace_id IN (SELECT ws_id FROM _test_ws_ids));
DELETE FROM "03_auth_manage"."17_fct_user_groups" WHERE scope_workspace_id IN (SELECT ws_id FROM _test_ws_ids);
DELETE FROM "03_auth_manage"."19_lnk_group_role_assignments" WHERE group_id IN (SELECT id FROM "03_auth_manage"."17_fct_user_groups" WHERE scope_org_id IN (SELECT org_id FROM _test_org_ids));
DELETE FROM "03_auth_manage"."18_lnk_group_memberships" WHERE group_id IN (SELECT id FROM "03_auth_manage"."17_fct_user_groups" WHERE scope_org_id IN (SELECT org_id FROM _test_org_ids));
DELETE FROM "03_auth_manage"."17_fct_user_groups" WHERE scope_org_id IN (SELECT org_id FROM _test_org_ids);
DELETE FROM "03_auth_manage"."35_dtl_workspace_settings" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids);
DELETE FROM "03_auth_manage"."36_lnk_workspace_memberships" WHERE workspace_id IN (SELECT ws_id FROM _test_ws_ids);
DELETE FROM "03_auth_manage"."48_lnk_grc_access_grants" WHERE grc_role_assignment_id IN (SELECT id FROM "03_auth_manage"."47_lnk_grc_role_assignments" WHERE org_id IN (SELECT org_id FROM _test_org_ids));
DELETE FROM "03_auth_manage"."47_lnk_grc_role_assignments" WHERE org_id IN (SELECT org_id FROM _test_org_ids);
DELETE FROM "03_auth_manage"."34_fct_workspaces" WHERE org_id IN (SELECT org_id FROM _test_org_ids);
DELETE FROM "03_auth_manage"."30_dtl_org_settings" WHERE org_id IN (SELECT org_id FROM _test_org_ids);
DELETE FROM "03_auth_manage"."31_lnk_org_memberships" WHERE org_id IN (SELECT org_id FROM _test_org_ids);
DELETE FROM "03_auth_manage"."26_lnk_product_memberships" WHERE org_id IN (SELECT org_id FROM _test_org_ids);
DELETE FROM "03_auth_manage"."44_trx_invitations" WHERE org_id IN (SELECT org_id FROM _test_org_ids);
DELETE FROM "03_auth_manage"."29_fct_orgs" WHERE id IN (SELECT org_id FROM _test_org_ids);

-- 8. Clean robot groups
DELETE FROM "03_auth_manage"."19_lnk_group_role_assignments" WHERE group_id IN (SELECT id FROM "03_auth_manage"."17_fct_user_groups" WHERE name LIKE 'Robot%' OR name LIKE 'robot%');
DELETE FROM "03_auth_manage"."18_lnk_group_memberships" WHERE group_id IN (SELECT id FROM "03_auth_manage"."17_fct_user_groups" WHERE name LIKE 'Robot%' OR name LIKE 'robot%');
DELETE FROM "03_auth_manage"."17_fct_user_groups" WHERE name LIKE 'Robot%' OR name LIKE 'robot%';

-- 9. Clean test invitations
DELETE FROM "03_auth_manage"."44_trx_invitations" WHERE email LIKE 'robot%' OR email LIKE '%@example.com';

-- 10. Clean test/debug notification templates
-- Step 1: Identify test template IDs
CREATE TEMP TABLE _test_template_ids AS
SELECT id FROM "03_notifications"."10_fct_templates"
WHERE is_system = FALSE
  AND (
      code LIKE 'robot\_%'       ESCAPE '\'
      OR code LIKE 'robot\_debug\_%' ESCAPE '\'
      OR code LIKE 'Email\_%'    ESCAPE '\'
  );

-- Step 2: Remove version FK reference before deleting versions
UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = NULL
WHERE id IN (SELECT id FROM _test_template_ids);

-- Step 3: Hard-delete template versions
DELETE FROM "03_notifications"."14_dtl_template_versions"
WHERE template_id IN (SELECT id FROM _test_template_ids);

-- Step 4: Hard-delete the templates themselves
DELETE FROM "03_notifications"."10_fct_templates"
WHERE id IN (SELECT id FROM _test_template_ids);

DROP TABLE IF EXISTS _test_template_ids;

-- 11. Summary
SELECT 'remaining_users' AS entity, COUNT(*) FROM "03_auth_manage"."03_fct_users";
SELECT 'remaining_orgs' AS entity, COUNT(*) FROM "03_auth_manage"."29_fct_orgs" WHERE is_deleted = FALSE;
SELECT 'remaining_groups' AS entity, COUNT(*) FROM "03_auth_manage"."17_fct_user_groups" WHERE is_deleted = FALSE;

DROP TABLE IF EXISTS _test_user_ids;
DROP TABLE IF EXISTS _test_org_ids;
DROP TABLE IF EXISTS _test_ws_ids;
