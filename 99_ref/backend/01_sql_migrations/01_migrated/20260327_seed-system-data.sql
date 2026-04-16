-- ═══════════════════════════════════════════════════════════════════════════
-- KCONTROL SYSTEM SEED DATA
-- Generated: 2026-03-27T14:16:41.750126
-- Source DB: kcontrol_dev @ ks-prod-cin-psql-02.postgres.database.azure.com
-- Categories: auth, notifications, ai, sandbox, grc, agent_sandbox, tasks, issues, feedback, docs, engagements, risk_registry, assessments, steampipe
-- 
-- Idempotent: all INSERTs use ON CONFLICT DO NOTHING.
-- Safe to re-run in any environment.
-- ═══════════════════════════════════════════════════════════════════════════

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: AUTH
-- Extracted: 2026-03-27T14:16:41.750143
-- ═════════════════════════════════════════════════════════════════════════════

-- 03_auth_manage.01_dim_identity_types (2 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."01_dim_identity_types" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000000001', 'email', 'Email', 'Primary email identifier', 10, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000002', 'username', 'Username', 'Optional alternate identifier', 20, '2026-03-13T00:00:00', '2026-03-13T00:00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.02_dim_challenge_types (4 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."02_dim_challenge_types" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000000011', 'password_reset', 'Password Reset', 'One-time password reset challenge', 10, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000012', 'email_verification', 'Email Verification', 'One-time email verification challenge', 20, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000013', 'magic_link', 'Magic Link', 'One-time passwordless login challenge sent via email', 30, '2026-03-17T15:38:38.202488', '2026-03-17T15:38:38.202488'),
      ('00000000-0000-0000-0000-000000000014', 'magic_link_assignee', 'Magic Link (Assignee)', 'One-time assignee portal login challenge sent via email', 31, '2026-03-19T07:59:20.607399', '2026-03-19T07:59:20.607399')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.04_dim_user_property_keys (16 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."04_dim_user_property_keys" (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0001-000000000001', 'email', 'Email Address', 'Primary email identifier', 'email', TRUE, TRUE, 10, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000002', 'username', 'Username', 'Optional alternate display identifier', 'string', FALSE, FALSE, 20, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000003', 'display_name', 'Display Name', 'User display name', 'string', FALSE, FALSE, 30, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000004', 'email_verified', 'Email Verified', 'Whether the email has been verified', 'boolean', FALSE, FALSE, 40, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000005', 'timezone', 'Timezone', 'Preferred IANA timezone', 'string', FALSE, FALSE, 50, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000006', 'locale', 'Locale', 'Preferred locale code', 'string', FALSE, FALSE, 60, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000007', 'avatar_url', 'Avatar URL', 'Profile avatar image URL', 'url', FALSE, FALSE, 70, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000008', 'phone', 'Phone Number', 'Contact phone number', 'phone', TRUE, FALSE, 80, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000009', 'bio', 'Biography', 'Short biography or description', 'string', FALSE, FALSE, 90, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000010', 'first_name', 'First Name', 'User''s given / first name', 'string', TRUE, FALSE, 100, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000011', 'last_name', 'Last Name', 'User''s family / last name', 'string', TRUE, FALSE, 110, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000012', 'default_org_id', 'Default Org ID', 'UUID of the user''s default organization', 'string', FALSE, FALSE, 120, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000013', 'default_workspace_id', 'Default Workspace ID', 'UUID of the user''s default workspace', 'string', FALSE, FALSE, 130, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000014', 'onboarding_complete', 'Onboarding Complete', 'Set to true once the setup wizard is finished', 'boolean', FALSE, FALSE, 140, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0001-000000000020', 'user_category_source', 'User Category Source', 'Indicates how the user''s category was determined (e.g. magic_link_invite, manual)', 'string', FALSE, FALSE, 200, '2026-03-17T15:38:38.244809', '2026-03-17T15:38:38.244809'),
      ('b48ad71f-d3c7-45cb-90c3-b3b788c1d67e', 'otp_verified', 'OTP Verified', 'Whether the user has completed OTP verification during onboarding', 'boolean', FALSE, FALSE, 15, '2026-03-20T03:39:16.988004', '2026-03-20T03:39:16.988004')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_pii = EXCLUDED.is_pii, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.06_dim_account_types (7 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."06_dim_account_types" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0002-000000000001', 'local_password', 'Local Password', 'Username and password authentication', 10, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0002-000000000002', 'google', 'Google OAuth', 'Google OAuth 2.0 authentication', 20, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0002-000000000003', 'github', 'GitHub OAuth', 'GitHub OAuth 2.0 authentication', 30, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0002-000000000004', 'microsoft', 'Microsoft OAuth', 'Microsoft Entra ID authentication', 40, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0002-000000000005', 'saml', 'SAML SSO', 'SAML 2.0 single sign-on', 50, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0002-000000000006', 'api_key', 'API Key', 'Programmatic API key authentication', 60, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0002-000000000007', 'magic_link', 'Magic Link', 'Passwordless authentication via one-time email link', 70, '2026-03-17T15:38:38.159084', '2026-03-17T15:38:38.159084')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.07_dim_account_property_keys (7 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."07_dim_account_property_keys" (id, account_type_code, code, name, description, is_secret, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0003-000000000001', 'local_password', 'password_hash', 'Password Hash', 'Argon2 password hash', TRUE, 10, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0003-000000000002', 'local_password', 'password_version', 'Password Version', 'Credential version for rotation tracking', FALSE, 20, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0003-000000000003', 'local_password', 'password_changed_at', 'Password Changed At', 'Timestamp of last password change', FALSE, 30, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0003-000000000004', 'google', 'google_id', 'Google ID', 'Google account unique identifier', FALSE, 10, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0003-000000000005', 'google', 'google_email', 'Google Email', 'Email from Google profile', FALSE, 20, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0003-000000000006', 'github', 'github_id', 'GitHub ID', 'GitHub account unique identifier', FALSE, 10, '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0003-000000000007', 'github', 'github_username', 'GitHub Username', 'GitHub username', FALSE, 20, '2026-03-14T00:00:00', '2026-03-14T00:00:00')
  ON CONFLICT (account_type_code, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_secret = EXCLUDED.is_secret, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.11_dim_feature_flag_categories (11 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000000101', 'auth', 'Auth', 'Feature flags related to sign-in methods and auth capabilities.', 10, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000102', 'policy', 'Policy', 'Feature flags related to policy lifecycle capabilities.', 20, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000103', 'access', 'Access', 'Feature flags related to access resolution and session context.', 30, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000104', 'admin', 'Admin', 'Feature flags related to privileged administrative consoles.', 40, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001501', 'product', 'Product', 'Product catalog administration.', 50, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001502', 'org', 'Organization', 'Org management capabilities.', 60, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001503', 'workspace', 'Workspace', 'Workspace management capabilities.', 70, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000003000', 'grc', 'GRC', 'Governance, Risk, and Compliance features', 10, '2026-03-15T18:21:18.065224', '2026-03-15T18:21:18.065224'),
      ('606316da-a36d-4889-9ff6-6de92d26114d', 'ai', 'AI', 'AI and agent platform features', 11, '2026-03-22T15:09:38.603393', '2026-03-22T15:09:38.603393'),
      ('87383cea-18d3-412f-aee7-0ba316331f36', 'governance', 'Access Governance', 'Access governance features', 1, '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('a9037964-8245-4749-8657-08775716c20b', 'audit_logs', 'Audit Logs', 'Have access to audit logs', 100, '2026-03-16T06:07:13.319385', '2026-03-16T06:07:13.319385')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.12_dim_feature_permission_actions (14 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000000099', 'submit', 'Submit', 'Submit an entity for review or approval.', 11, '2026-03-18T18:11:13.597558', '2026-03-18T18:11:13.597558'),
      ('00000000-0000-0000-0000-000000000201', 'view', 'View', 'Read-only visibility of a feature or console area.', 10, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000202', 'create', 'Create', 'Create feature-managed state.', 20, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000203', 'update', 'Update', 'Update feature-managed state.', 30, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000204', 'enable', 'Enable', 'Enable a feature or rollout-controlled capability.', 40, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000205', 'disable', 'Disable', 'Disable a feature or rollout-controlled capability.', 50, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000206', 'assign', 'Assign', 'Assign groups, roles, or feature actions.', 60, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000207', 'revoke', 'Revoke', 'Revoke groups, roles, or feature actions.', 70, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000005001', 'execute', 'Execute', 'Execute a control test or sandbox run.', 80, '2026-03-16T11:40:41.803856', '2026-03-16T11:40:41.803856'),
      ('00000000-0000-0000-0000-000000005002', 'promote', 'Promote', 'Promote a sandbox artifact to production.', 90, '2026-03-16T11:40:41.803856', '2026-03-16T11:40:41.803856'),
      ('00000000-0000-0000-0000-000000006001', 'collect', 'Collect', 'Trigger or cancel asset collection runs.', 85, '2026-03-16T11:39:10.95114', '2026-03-16T11:39:10.95114'),
      ('00000000-0000-0000-0000-000000007001', 'manage', 'Manage', 'Full management access including approvals and registry.', 100, '2026-03-22T15:08:27.826789', '2026-03-22T15:08:27.826789'),
      ('33367e59-652c-452f-9b7d-29d26d19ee65', 'approve', 'Approve', 'Approve pending operations or requests', 12, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('8d50c71a-51df-4ecc-a06f-950930ff2c89', 'delete', 'Delete', 'Delete', 1, '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.13_dim_role_levels (4 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."13_dim_role_levels" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000000301', 'super_admin', 'Super Admin', 'Platform-wide access scope.', 10, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000302', 'org', 'Organization', 'Organization-scoped access scope.', 20, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000303', 'workspace', 'Workspace', 'Workspace-scoped access scope.', 30, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('c8cf96bb-85e7-4f77-94e2-2818bf1101cf', 'platform', 'Platform', 'Platform', 1, '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.14_dim_feature_flags (50 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."14_dim_feature_flags" (id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at, feature_scope, product_id)
  VALUES
      ('00000000-0000-0000-0000-000000000401', 'auth_password_login', 'Password Login', 'Availability of local password login endpoints.', 'auth', 'public', 'active', 'all_users', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-15T06:23:04.335842', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000402', 'auth_google_login', 'Google Login', 'Availability of Google login when implemented.', 'auth', 'public', 'planned', 'all_users', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000403', 'policy_management', 'Policy Management', 'Policy creation and lifecycle controls.', 'policy', 'permissioned', 'active', 'org_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-24T11:31:45.102346', 'org', NULL),
      ('00000000-0000-0000-0000-000000000404', 'access_governance_console', 'Access Governance Console', 'Privileged access governance console.', 'access', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000405', 'feature_flag_registry', 'Feature Flag Registry', 'Feature catalog and rollout management.', 'admin', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000406', 'group_access_assignment', 'Group Access Assignment', 'Group membership and role assignment administration.', 'admin', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000407', 'access_audit_timeline', 'Access Audit Timeline', 'Audit timeline visibility for feature and access changes.', 'admin', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000408', 'invitation_management', 'Invitation Management', 'User invitation creation and lifecycle management.', 'admin', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000410', 'user_impersonation', 'User Impersonation', 'Allow privileged admins to impersonate other users for support and debugging.', 'admin', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-14T00:00:00', '2026-03-14T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000420', 'admin_console', 'Admin Console', 'Access to the platform admin console', 'admin', 'permissioned', 'active', 'internal', TRUE, TRUE, TRUE, '2026-03-15T07:01:10.571982', '2026-03-15T07:01:10.571982', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000540', 'feedback', 'Feedback & Support', 'User feedback submission and support ticket management', 'admin', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-17T07:49:17.035753', '2026-03-17T07:49:17.035753', 'platform', NULL),
      ('00000000-0000-0000-0000-000000000550', 'docs', 'Document Library', 'Global and org-scoped document library for policies, frameworks, and RAG knowledge base', 'admin', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-17T08:28:44.736028', '2026-03-24T11:25:56.299386', 'org', NULL),
      ('00000000-0000-0000-0000-000000001601', 'product_management', 'Product Management', 'Product catalog and environment controls.', 'product', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000001602', 'org_management', 'Org Management', 'Organization creation and membership administration.', 'org', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'platform', NULL),
      ('00000000-0000-0000-0000-000000001603', 'workspace_management', 'Workspace Management', 'Workspace creation and membership administration.', 'workspace', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'org', NULL),
      ('00000000-0000-0000-0000-000000001801', 'kc_data_pipeline', 'Data Pipeline Management', 'Controls access to data pipeline creation and execution within K-Control workspaces.', 'admin', 'permissioned', 'active', 'workspace_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'product', '00000000-0000-0000-0000-000000001201'),
      ('00000000-0000-0000-0000-000000001802', 'kc_report_builder', 'Report Builder', 'Controls access to the visual report builder within K-Control workspaces.', 'admin', 'permissioned', 'active', 'workspace_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'product', '00000000-0000-0000-0000-000000001201'),
      ('00000000-0000-0000-0000-000000001803', 'kcsb_sandbox_reset', 'Sandbox Reset', 'Allows resetting workspace data to the sandbox baseline state.', 'admin', 'permissioned', 'active', 'workspace_admin', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', 'product', '00000000-0000-0000-0000-000000001202'),
      ('00000000-0000-0000-0000-000000003001', 'framework_management', 'Framework Management', 'Framework library, controls, tests, versions', 'grc', 'permissioned', 'active', 'all', TRUE, FALSE, FALSE, '2026-03-15T18:21:18.101612', '2026-03-23T05:41:57.042003', 'org', NULL),
      ('00000000-0000-0000-0000-000000003002', 'risk_registry', 'Risk Registry', 'Risk register, assessments, treatment plans', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-15T18:21:18.101612', '2026-03-15T18:21:18.101612', 'platform', NULL),
      ('00000000-0000-0000-0000-000000003003', 'control_test_library', 'Control Test Library', 'Reusable control test library and evidence templates', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-15T18:21:18.101612', '2026-03-24T05:26:22.2738', 'org', NULL),
      ('00000000-0000-0000-0000-000000003004', 'task_management', 'Task Management', 'GRC task management with dependencies and assignments', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-15T18:21:18.101612', '2026-03-15T18:21:18.101612', 'platform', NULL),
      ('00000000-0000-0000-0000-000000003005', 'control_management', 'Control Management', 'Control library within frameworks', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-15T18:23:58.939376', '2026-03-15T18:23:58.939376', 'platform', NULL),
      ('00000000-0000-0000-0000-000000003006', 'comments', 'Comments', 'Collaborative comments on GRC entities', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-17T06:58:39.624125', '2026-03-17T06:58:39.624125', 'platform', NULL),
      ('00000000-0000-0000-0000-000000003007', 'attachments', 'Attachments', 'File attachments on GRC entities', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-17T06:58:39.624125', '2026-03-24T10:39:29.495998', 'org', NULL),
      ('00000000-0000-0000-0000-000000005010', 'sandbox', 'Sandbox', 'Control test sandbox environment for building, testing, and promoting runtime compliance checks', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-16T11:40:41.828854', '2026-03-16T11:40:41.828854', 'platform', NULL),
      ('00000000-0000-0000-0000-000000006010', 'asset_inventory', 'Asset Inventory', 'Asset discovery and log ingestion from external providers (GitHub, Azure Storage, etc.) for compliance evidence collection', 'grc', 'permissioned', 'active', 'all', TRUE, FALSE, FALSE, '2026-03-16T11:39:10.976041', '2026-03-16T16:36:16.530972', 'platform', NULL),
      ('00000000-0000-0000-0000-000000007010', 'agent_sandbox', 'Agent Sandbox', 'Build, test, and deploy autonomous AI agents from the UI', 'ai', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-22T15:08:53.827441', '2026-03-22T15:08:53.827441', 'platform', NULL),
      ('1e24ec36-b51c-4f6b-b576-37b6c0116663', 'robot_flag_1773993113', 'Robot Flag 1773993113 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-20T07:51:58.409719', '2026-03-20T07:52:01.537678', 'platform', NULL),
      ('29b3f390-9cf2-4237-9ec7-bae56bb08ac1', 'findings', 'Findings', 'Finding management within assessments', 'grc', 'permissioned', 'active', 'platform_super_admin', TRUE, TRUE, FALSE, '2026-03-18T03:12:15.766767', '2026-03-18T03:12:15.766767', 'platform', NULL),
      ('2d4478ff-762c-42ce-99ce-a1f6f29e1ee5', 'ai_evidence_checker', 'AI Evidence Checker', 'Auto-evaluate task attachments against acceptance criteria using AI multi-agent evaluation', 'grc', 'permissioned', 'general_availability', 'all_users', TRUE, TRUE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', 'workspace', NULL),
      ('2faadf57-e83e-4a6a-8a17-1a4b26729cd6', 'robot_flag_1774253280', 'Robot Flag 1774253280 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-23T08:08:05.224211', '2026-03-23T08:08:07.851418', 'platform', NULL),
      ('30ddfe78-8e2b-4772-94e1-22de0eaa182d', 'notification_broadcasts', 'Notification Broadcasts', 'Notification Broadcasts feature flag', 'admin', 'permissioned', 'active', '100', TRUE, FALSE, FALSE, '2026-03-14T08:44:04.851727', '2026-03-16T10:41:51.538604', 'platform', NULL),
      ('368fbfe8-9d35-413f-bdf7-5d4772af082e', 'robot_flag_1773993218', 'Robot Flag 1773993218 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-20T07:53:43.696271', '2026-03-20T07:53:46.648902', 'platform', NULL),
      ('39b95e7d-13ff-4eba-a155-faff7118f7bc', 'reports', 'GRC Reports', 'AI-generated compliance and audit reports', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-18T14:23:34.216589', '2026-03-18T14:23:34.216589', 'platform', NULL),
      ('4564781a-422c-404b-9774-4dfc76edd7e7', 'robot_flag_1774247096', 'Robot Flag 1774247096 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-23T06:25:01.011912', '2026-03-23T06:25:03.584803', 'platform', NULL),
      ('4bfe3b8e-9800-4caa-ac80-cc6f58c8d9e8', 'robot_flag_1774430079', 'Robot Flag 1774430079 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-25T09:14:46.895288', '2026-03-25T09:14:50.804298', 'platform', NULL),
      ('58148945-4ed2-47a6-875b-d9607bc72325', 'notification_system', 'Notification System', 'Notification System feature flag', 'admin', 'permissioned', 'active', '100', TRUE, FALSE, FALSE, '2026-03-14T08:44:04.68572', '2026-03-16T10:41:29.435077', 'platform', NULL),
      ('644b34f9-3b54-4517-bb0b-612e3a3e6fca', 'assessments', 'Assessments', 'Assessment & Findings module', 'grc', 'permissioned', 'active', 'platform_super_admin', TRUE, TRUE, FALSE, '2026-03-18T03:12:15.766767', '2026-03-18T03:12:15.766767', 'platform', NULL),
      ('654993d9-4cbe-464a-bd00-77b7dcfc337d', 'global_risk_library', 'Global Risk Library', 'Platform-level global risk registry', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-17T09:56:03.279507', '2026-03-17T09:56:03.279507', 'platform', NULL),
      ('6570385e-d510-4382-b359-d6f50ef5ac85', 'robot_flag_1774247134', 'Robot Flag 1774247134 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-23T06:25:39.041772', '2026-03-23T06:25:41.545705', 'platform', NULL),
      ('6f930219-3272-4bfb-b1a2-f44acc0956f2', 'test_flag_1773424174', 'Test Flag 1773424174', 'Test flag', 'auth', 'permissioned', 'planned', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-13T17:49:38.980155', '2026-03-13T17:49:38.980155', 'platform', NULL),
      ('922a518b-b607-4be7-9c21-e2bdbc394a02', 'test_feature', 'Test Feature Updated', 'Updated description', 'governance', 'permissioned', 'active', 'internal', TRUE, FALSE, FALSE, '2026-03-13T17:34:50.20983', '2026-03-13T17:34:51.464961', 'platform', NULL),
      ('93dc3e9f-b487-463b-be82-a9fdfd126f90', 'robot_flag_1773988220', 'Robot Flag 1773988220 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-20T06:30:26.163644', '2026-03-20T06:30:29.279814', 'platform', NULL),
      ('99efdb95-b7a6-4a0a-821f-912ee337ca96', 'notification_preferences', 'Notification Preferences', 'Notification Preferences feature flag', 'admin', 'authenticated', 'active', '100', TRUE, FALSE, FALSE, '2026-03-14T08:44:04.921379', '2026-03-16T10:41:44.390144', 'platform', NULL),
      ('b12d6d5d-7032-455b-9059-ab41ca688ecf', 'notification_templates', 'Notification Templates', 'Notification Templates feature flag', 'admin', 'permissioned', 'active', '100', TRUE, FALSE, FALSE, '2026-03-14T08:44:04.78462', '2026-03-16T10:41:09.801996', 'platform', NULL),
      ('baad3c1d-ccd5-4452-b9bb-9c960dc5e192', 'robot_flag_1774405724', 'Robot Flag 1774405724 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-25T02:28:50.433102', '2026-03-25T02:28:53.782948', 'platform', NULL),
      ('d3176581-03ba-4b4b-8f72-d847f56092b4', 'robot_flag_1773732626', 'Robot Flag 1773732626 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-03-17T07:30:31.335997', '2026-03-17T07:30:33.924714', 'platform', NULL),
      ('d63d053d-5060-4186-b097-8d1e374e559e', 'ai_copilot', 'AI Copilot Platform', 'Enterprise AI copilot, MCP tools, approval workflows, agent swarm', 'admin', 'permissioned', 'active', 'platform_super_admin', TRUE, TRUE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', 'platform', NULL),
      ('de32a051-928d-485b-84e0-fc737eda4106', 'audit_logs_access', 'Org Audit logs', 'Organization level audit logs visibility', 'audit_logs', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-16T06:08:56.715018', '2026-03-16T10:13:58.896856', 'org', NULL)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, feature_flag_category_code = EXCLUDED.feature_flag_category_code, access_mode = EXCLUDED.access_mode, lifecycle_state = EXCLUDED.lifecycle_state, initial_audience = EXCLUDED.initial_audience, env_dev = EXCLUDED.env_dev, env_staging = EXCLUDED.env_staging, env_prod = EXCLUDED.env_prod, updated_at = EXCLUDED.updated_at, feature_scope = EXCLUDED.feature_scope, product_id = EXCLUDED.product_id;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.15_dim_feature_permissions (157 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000000421', 'admin_console.view', 'admin_console', 'view', 'Admin Console View', 'View admin console', '2026-03-15T07:01:10.571982', '2026-03-15T07:01:10.571982'),
      ('00000000-0000-0000-0000-000000000422', 'admin_console.update', 'admin_console', 'update', 'Admin Console Update', 'Manage users via admin console', '2026-03-15T07:01:10.571982', '2026-03-15T07:01:10.571982'),
      ('00000000-0000-0000-0000-000000000501', 'auth_password_login.enable', 'auth_password_login', 'enable', 'Enable Password Login', 'Enable local password login.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000502', 'auth_password_login.disable', 'auth_password_login', 'disable', 'Disable Password Login', 'Disable local password login.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000503', 'auth_google_login.enable', 'auth_google_login', 'enable', 'Enable Google Login', 'Enable Google login when implemented.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000504', 'auth_google_login.disable', 'auth_google_login', 'disable', 'Disable Google Login', 'Disable Google login when implemented.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000505', 'policy_management.create', 'policy_management', 'create', 'Create Policies', 'Create policies.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000506', 'policy_management.enable', 'policy_management', 'enable', 'Enable Policies', 'Enable policy-managed behavior.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000507', 'policy_management.disable', 'policy_management', 'disable', 'Disable Policies', 'Disable policy-managed behavior.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000508', 'access_governance_console.view', 'access_governance_console', 'view', 'View Access Governance Console', 'View access governance console pages.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000509', 'access_governance_console.assign', 'access_governance_console', 'assign', 'Assign Access Governance Actions', 'Assign feature permissions to roles.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-00000000050a', 'feature_flag_registry.view', 'feature_flag_registry', 'view', 'View Feature Registry', 'View feature catalog and rollout state.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-00000000050b', 'feature_flag_registry.create', 'feature_flag_registry', 'create', 'Create Feature Flags', 'Create feature flag entries.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-00000000050c', 'feature_flag_registry.update', 'feature_flag_registry', 'update', 'Update Feature Flags', 'Update feature metadata.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-00000000050d', 'feature_flag_registry.enable', 'feature_flag_registry', 'enable', 'Enable Feature Flags', 'Enable feature rollout in an environment.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-00000000050e', 'feature_flag_registry.disable', 'feature_flag_registry', 'disable', 'Disable Feature Flags', 'Disable feature rollout in an environment.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-00000000050f', 'group_access_assignment.view', 'group_access_assignment', 'view', 'View Group Access Assignment', 'View groups, members, and role assignments.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000510', 'group_access_assignment.assign', 'group_access_assignment', 'assign', 'Assign Group Access', 'Assign group members or group roles.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000511', 'group_access_assignment.revoke', 'group_access_assignment', 'revoke', 'Revoke Group Access', 'Revoke group members or group roles.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000512', 'access_audit_timeline.view', 'access_audit_timeline', 'view', 'View Access Audit Timeline', 'View access audit events.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000513', 'invitation_management.view', 'invitation_management', 'view', 'View Invitations', 'View invitation list and statistics.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000514', 'invitation_management.create', 'invitation_management', 'create', 'Create Invitations', 'Create and send user invitations.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000515', 'invitation_management.update', 'invitation_management', 'update', 'Update Invitations', 'Update invitation details.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000516', 'invitation_management.revoke', 'invitation_management', 'revoke', 'Revoke Invitations', 'Revoke pending invitations.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000000520', 'user_impersonation.enable', 'user_impersonation', 'enable', 'Start Impersonation', 'Start impersonating another user.', '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0000-000000000521', 'user_impersonation.view', 'user_impersonation', 'view', 'View Impersonation Sessions', 'View active impersonation sessions.', '2026-03-14T00:00:00', '2026-03-14T00:00:00'),
      ('00000000-0000-0000-0000-000000000541', 'feedback.view', 'feedback', 'view', 'View Feedback Tickets', 'View own submitted feedback tickets', '2026-03-17T07:49:17.073045', '2026-03-17T07:49:17.073045'),
      ('00000000-0000-0000-0000-000000000542', 'feedback.create', 'feedback', 'create', 'Submit Feedback', 'Submit new feedback or support tickets', '2026-03-17T07:49:17.073045', '2026-03-17T07:49:17.073045'),
      ('00000000-0000-0000-0000-000000000543', 'feedback.update', 'feedback', 'update', 'Update Feedback', 'Edit own open feedback tickets', '2026-03-17T07:49:17.073045', '2026-03-17T07:49:17.073045'),
      ('00000000-0000-0000-0000-000000000544', 'feedback.delete', 'feedback', 'delete', 'Delete Feedback', 'Delete own open feedback tickets', '2026-03-17T07:49:17.073045', '2026-03-17T07:49:17.073045'),
      ('00000000-0000-0000-0000-000000000545', 'feedback.manage', 'feedback', 'assign', 'Manage Feedback Queue', 'Triage, assign, change status on any ticket', '2026-03-17T07:49:17.073045', '2026-03-17T07:49:17.073045'),
      ('00000000-0000-0000-0000-000000000551', 'docs.view', 'docs', 'view', 'View Documents', 'Browse and download documents', '2026-03-17T08:28:44.772754', '2026-03-17T08:28:44.772754'),
      ('00000000-0000-0000-0000-000000000552', 'docs.create', 'docs', 'create', 'Upload Documents', 'Upload new documents', '2026-03-17T08:28:44.772754', '2026-03-17T08:28:44.772754'),
      ('00000000-0000-0000-0000-000000000553', 'docs.update', 'docs', 'update', 'Update Documents', 'Edit document metadata', '2026-03-17T08:28:44.772754', '2026-03-17T08:28:44.772754'),
      ('00000000-0000-0000-0000-000000000554', 'docs.delete', 'docs', 'delete', 'Delete Documents', 'Delete documents', '2026-03-17T08:28:44.772754', '2026-03-17T08:28:44.772754'),
      ('00000000-0000-0000-0000-000000000555', 'docs.manage', 'docs', 'assign', 'Manage Library', 'Manage global library (super admin only)', '2026-03-17T08:28:44.772754', '2026-03-17T08:28:44.772754'),
      ('00000000-0000-0000-0000-000000001701', 'product_management.view', 'product_management', 'view', 'View Products', 'View product catalog.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001702', 'product_management.create', 'product_management', 'create', 'Create Products', 'Create new product instances.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001703', 'product_management.update', 'product_management', 'update', 'Update Products', 'Update product metadata.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001704', 'product_management.assign', 'product_management', 'assign', 'Assign Product Members', 'Add users to a product.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001705', 'product_management.revoke', 'product_management', 'revoke', 'Revoke Product Members', 'Remove users from a product.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001711', 'org_management.view', 'org_management', 'view', 'View Orgs', 'View organization list.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001712', 'org_management.create', 'org_management', 'create', 'Create Orgs', 'Create new organizations.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001713', 'org_management.update', 'org_management', 'update', 'Update Orgs', 'Update org details.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001714', 'org_management.assign', 'org_management', 'assign', 'Assign Org Members', 'Add users to an organization.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001715', 'org_management.revoke', 'org_management', 'revoke', 'Revoke Org Members', 'Remove users from an organization.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001721', 'workspace_management.view', 'workspace_management', 'view', 'View Workspaces', 'View workspace list.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001722', 'workspace_management.create', 'workspace_management', 'create', 'Create Workspaces', 'Create new workspaces.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001723', 'workspace_management.update', 'workspace_management', 'update', 'Update Workspaces', 'Update workspace details.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001724', 'workspace_management.assign', 'workspace_management', 'assign', 'Assign Workspace Members', 'Add users to a workspace.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001725', 'workspace_management.revoke', 'workspace_management', 'revoke', 'Revoke Workspace Members', 'Remove users from a workspace.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001811', 'kc_data_pipeline.view', 'kc_data_pipeline', 'view', 'View Pipelines', 'View data pipeline list.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001812', 'kc_data_pipeline.create', 'kc_data_pipeline', 'create', 'Create Pipelines', 'Create new data pipelines.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001813', 'kc_data_pipeline.update', 'kc_data_pipeline', 'update', 'Update Pipelines', 'Update pipeline configuration.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001814', 'kc_data_pipeline.enable', 'kc_data_pipeline', 'enable', 'Enable Pipelines', 'Enable a data pipeline.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001815', 'kc_data_pipeline.disable', 'kc_data_pipeline', 'disable', 'Disable Pipelines', 'Disable a data pipeline.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001816', 'kc_report_builder.view', 'kc_report_builder', 'view', 'View Reports', 'View saved reports.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001817', 'kc_report_builder.create', 'kc_report_builder', 'create', 'Create Reports', 'Create new reports.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001818', 'kc_report_builder.update', 'kc_report_builder', 'update', 'Update Reports', 'Edit report configuration.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001819', 'kcsb_sandbox_reset.enable', 'kcsb_sandbox_reset', 'enable', 'Enable Sandbox Reset', 'Enable sandbox reset capability.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-00000000181a', 'kcsb_sandbox_reset.disable', 'kcsb_sandbox_reset', 'disable', 'Disable Sandbox Reset', 'Disable sandbox reset capability.', '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000003010', 'frameworks.view', 'framework_management', 'view', 'View Frameworks', 'View framework library', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003011', 'frameworks.create', 'framework_management', 'create', 'Create Frameworks', 'Create frameworks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003012', 'frameworks.update', 'framework_management', 'update', 'Update Frameworks', 'Update frameworks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003013', 'frameworks.delete', 'framework_management', 'delete', 'Delete Frameworks', 'Delete frameworks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003015', 'frameworks.submit', 'framework_management', 'submit', 'Submit Frameworks for Approval', 'Can push a framework to pending_review for marketplace approval. Restricted to super admins — regular org users cannot submit to the global library.', '2026-03-18T18:11:13.628205', '2026-03-18T18:11:13.628205'),
      ('00000000-0000-0000-0000-000000003020', 'controls.view', 'control_management', 'view', 'View Controls', 'View controls', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003021', 'controls.create', 'control_management', 'create', 'Create Controls', 'Create controls', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003022', 'controls.update', 'control_management', 'update', 'Update Controls', 'Update controls', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003023', 'controls.delete', 'control_management', 'delete', 'Delete Controls', 'Delete controls', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003030', 'tests.view', 'control_test_library', 'view', 'View Tests', 'View test library', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003031', 'tests.create', 'control_test_library', 'create', 'Create Tests', 'Create tests', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003032', 'tests.update', 'control_test_library', 'update', 'Update Tests', 'Update tests', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003033', 'tests.delete', 'control_test_library', 'delete', 'Delete Tests', 'Delete tests', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003040', 'risks.view', 'risk_registry', 'view', 'View Risks', 'View risks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003041', 'risks.create', 'risk_registry', 'create', 'Create Risks', 'Create risks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003042', 'risks.update', 'risk_registry', 'update', 'Update Risks', 'Update risks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003043', 'risks.delete', 'risk_registry', 'delete', 'Delete Risks', 'Delete risks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003050', 'tasks.view', 'task_management', 'view', 'View Tasks', 'View tasks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003051', 'tasks.create', 'task_management', 'create', 'Create Tasks', 'Create tasks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003052', 'tasks.update', 'task_management', 'update', 'Update Tasks', 'Update tasks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003053', 'tasks.assign', 'task_management', 'assign', 'Assign Tasks', 'Assign tasks', '2026-03-15T18:23:59.223013', '2026-03-15T18:23:59.223013'),
      ('00000000-0000-0000-0000-000000003060', 'comments.view', 'comments', 'view', 'View Comments', 'Can view comments on any entity', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000003061', 'comments.create', 'comments', 'create', 'Create Comments', 'Can create comments', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000003062', 'comments.update', 'comments', 'update', 'Edit Comments', 'Can edit own comments', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000003063', 'comments.delete', 'comments', 'delete', 'Delete Comments', 'Can delete comments', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000003064', 'comments.manage', 'comments', 'assign', 'Manage Comments', 'Can pin, lock, moderate', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000003065', 'comments.resolve', 'comments', 'revoke', 'Resolve Comments', 'Can resolve threads', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000003070', 'attachments.view', 'attachments', 'view', 'View Attachments', 'Can view and download', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000003071', 'attachments.create', 'attachments', 'create', 'Upload Attachments', 'Can upload attachments', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000003072', 'attachments.delete', 'attachments', 'delete', 'Delete Attachments', 'Can delete attachments', '2026-03-17T06:59:02.434379', '2026-03-17T06:59:02.434379'),
      ('00000000-0000-0000-0000-000000005020', 'sandbox.view', 'sandbox', 'view', 'View Sandbox', 'Can view sandbox environments and test runs', '2026-03-16T11:40:41.853488', '2026-03-16T11:40:41.853488'),
      ('00000000-0000-0000-0000-000000005021', 'sandbox.create', 'sandbox', 'create', 'Create Sandbox', 'Can create new sandbox environments and test definitions', '2026-03-16T11:40:41.853488', '2026-03-16T11:40:41.853488'),
      ('00000000-0000-0000-0000-000000005022', 'sandbox.update', 'sandbox', 'update', 'Update Sandbox', 'Can update sandbox configurations and test parameters', '2026-03-16T11:40:41.853488', '2026-03-16T11:40:41.853488'),
      ('00000000-0000-0000-0000-000000005023', 'sandbox.delete', 'sandbox', 'delete', 'Delete Sandbox', 'Can delete sandbox environments and test runs', '2026-03-16T11:40:41.853488', '2026-03-16T11:40:41.853488'),
      ('00000000-0000-0000-0000-000000005024', 'sandbox.execute', 'sandbox', 'execute', 'Execute Sandbox', 'Can execute control tests in the sandbox', '2026-03-16T11:40:41.853488', '2026-03-16T11:40:41.853488'),
      ('00000000-0000-0000-0000-000000005025', 'sandbox.promote', 'sandbox', 'promote', 'Promote Sandbox', 'Can promote sandbox artifacts to production', '2026-03-16T11:40:41.853488', '2026-03-16T11:40:41.853488'),
      ('00000000-0000-0000-0000-000000006020', 'asset_inventory.view', 'asset_inventory', 'view', 'View Asset Inventory', 'View asset inventory, providers, connectors, discovered assets', '2026-03-16T11:39:11.002548', '2026-03-16T11:39:11.002548'),
      ('00000000-0000-0000-0000-000000006021', 'asset_inventory.create', 'asset_inventory', 'create', 'Create Asset Inventory', 'Create connector instances and configure log sources', '2026-03-16T11:39:11.002548', '2026-03-16T11:39:11.002548'),
      ('00000000-0000-0000-0000-000000006022', 'asset_inventory.update', 'asset_inventory', 'update', 'Update Asset Inventory', 'Update connector configuration and credentials', '2026-03-16T11:39:11.002548', '2026-03-16T11:39:11.002548'),
      ('00000000-0000-0000-0000-000000006023', 'asset_inventory.delete', 'asset_inventory', 'delete', 'Delete Asset Inventory', 'Delete connectors and assets', '2026-03-16T11:39:11.002548', '2026-03-16T11:39:11.002548'),
      ('00000000-0000-0000-0000-000000006024', 'asset_inventory.collect', 'asset_inventory', 'collect', 'Collect Asset Inventory', 'Trigger manual collection runs and test connections', '2026-03-16T11:39:11.002548', '2026-03-16T11:39:11.002548'),
      ('00000000-0000-0000-0000-000000007020', 'agent_sandbox.view', 'agent_sandbox', 'view', 'View Agent Sandbox', 'Can view agents, tools, and execution runs', '2026-03-22T15:08:53.860583', '2026-03-22T15:08:53.860583'),
      ('00000000-0000-0000-0000-000000007021', 'agent_sandbox.create', 'agent_sandbox', 'create', 'Create Agent Sandbox', 'Can create and update agents, tools, and test scenarios', '2026-03-22T15:08:53.860583', '2026-03-22T15:08:53.860583'),
      ('00000000-0000-0000-0000-000000007022', 'agent_sandbox.execute', 'agent_sandbox', 'execute', 'Execute Agent Sandbox', 'Can execute agents and test scenarios', '2026-03-22T15:08:53.860583', '2026-03-22T15:08:53.860583'),
      ('00000000-0000-0000-0000-000000007023', 'agent_sandbox.manage', 'agent_sandbox', 'manage', 'Manage Agent Sandbox', 'Can manage tool registry and approve agent runs', '2026-03-22T15:08:53.860583', '2026-03-22T15:08:53.860583'),
      ('01dfab3e-59e2-4e79-b514-d57b4de19c65', 'notification_system.view', 'notification_system', 'view', 'notification_system view', 'Permission to view notification_system', '2026-03-14T08:44:05.018473', '2026-03-14T08:44:05.018473'),
      ('03728caf-974b-4a70-941b-ddae4a319f4d', 'notification_system.delete', 'notification_system', 'delete', 'notification_system delete', 'Permission to delete notification_system', '2026-03-14T08:44:05.251235', '2026-03-14T08:44:05.251235'),
      ('03dba1fa-5bdf-45a6-aa0a-aa6117fe6285', 'global_risk_library.delete', 'global_risk_library', 'delete', 'Delete Global Risks', 'Delete global risks', '2026-03-17T09:56:03.320987', '2026-03-17T09:56:03.320987'),
      ('08e2ccca-5d32-49e0-b4e5-062fb0177f81', 'notification_broadcasts.delete', 'notification_broadcasts', 'delete', 'notification_broadcasts delete', 'Permission to delete notification_broadcasts', '2026-03-14T08:44:05.762885', '2026-03-14T08:44:05.762885'),
      ('0abe68aa-b4ac-4335-8189-24ab0cb4e460', 'notification_system.create', 'notification_system', 'create', 'notification_system create', 'Permission to create notification_system', '2026-03-14T08:44:05.119831', '2026-03-14T08:44:05.119831'),
      ('10c9c4e1-dc73-4ddd-a86d-944875232bda', 'global_risk_library.create', 'global_risk_library', 'create', 'Create Global Risks', 'Create global risks', '2026-03-17T09:56:03.320987', '2026-03-17T09:56:03.320987'),
      ('11582d29-77d4-49ed-b8a4-ef7a1c3c540f', 'feature_flag_registry.assign', 'feature_flag_registry', 'assign', 'feature_flag_registry.assign', 'feature_flag_registry.assign', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('13fd0ba4-d66e-4223-8f0e-76b0ec002d39', 'notification_system.update', 'notification_system', 'update', 'notification_system update', 'Permission to update notification_system', '2026-03-14T08:44:05.184259', '2026-03-14T08:44:05.184259'),
      ('18e15e8f-21d4-4206-aac9-a7d116129277', 'access_governance_console.create', 'access_governance_console', 'create', 'access_governance_console.create', 'access_governance_console.create', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('20dfe0b5-3990-4bb4-bc02-6f93b8673e36', 'findings.delete', 'findings', 'delete', 'Delete Findings', 'Delete findings', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('32c6f06d-fdcd-4a67-9a0c-9f1596978659', 'notification_templates.create', 'notification_templates', 'create', 'notification_templates create', 'Permission to create notification_templates', '2026-03-14T08:44:05.379413', '2026-03-14T08:44:05.379413'),
      ('340ab0cd-3506-4c40-b2f8-87397ffd5d69', 'assessments.create', 'assessments', 'create', 'Create Assessments', 'Create assessment sessions', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('3d7daef7-175b-4aba-959c-e22517a883e8', 'access_governance_console.delete', 'access_governance_console', 'delete', 'access_governance_console.delete', 'access_governance_console.delete', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('418d753c-aa97-4551-abb6-b703d54f8f96', 'reports.enable', 'reports', 'enable', 'Reports — Enable', 'Permission to enable reports.', '2026-03-24T11:17:26.475614', '2026-03-24T11:17:26.475614'),
      ('4c0e311e-01ef-487a-9136-b0be8bf85412', 'ai_copilot.view', 'ai_copilot', 'view', 'View AI Copilot', 'Access conversations, memory, tool history, agent runs', '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('4db67994-51ad-4dde-93b1-3abd1842da4d', 'org_management.delete', 'org_management', 'delete', 'org_management.delete', 'org_management.delete', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('4de88a99-cf77-4391-b8c5-97d3dcb9d7f6', 'reports.create', 'reports', 'create', 'Create Reports', 'Generate GRC reports', '2026-03-18T14:23:34.277884', '2026-03-18T14:23:34.277884'),
      ('55963948-87ca-47e7-9de7-ddd7f3dc675f', 'global_risk_library.view', 'global_risk_library', 'view', 'View Global Risk Library', 'View global risks', '2026-03-17T09:56:03.320987', '2026-03-17T09:56:03.320987'),
      ('5e57eaaf-2427-467a-8170-b0c605c5c61d', 'reports.view', 'reports', 'view', 'View Reports', 'View GRC reports', '2026-03-18T14:23:34.277884', '2026-03-18T14:23:34.277884'),
      ('619affe6-e90d-4fac-a1bc-c6364653041a', 'docs.enable', 'docs', 'enable', 'Docs — Enable', 'Permission to enable docs.', '2026-03-24T11:24:24.306498', '2026-03-24T11:24:24.306498'),
      ('64bf9716-617e-426f-b9ca-80b1cbec466c', 'access_governance_console.update', 'access_governance_console', 'update', 'access_governance_console.update', 'access_governance_console.update', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('6732df5a-2522-4447-bd3f-5c33ebd61696', 'findings.update', 'findings', 'update', 'Update Findings', 'Update finding status and respond', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('73f7950d-7163-4467-837d-b6907dd0abcf', 'notification_templates.delete', 'notification_templates', 'delete', 'notification_templates delete', 'Permission to delete notification_templates', '2026-03-14T08:44:05.5074', '2026-03-14T08:44:05.5074'),
      ('74f334d2-f078-4752-a2fd-2f4af1e360cf', 'assessments.delete', 'assessments', 'delete', 'Delete Assessments', 'Delete assessments', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('7764d393-4513-4068-a119-d30230b1da5c', 'assessments.update', 'assessments', 'update', 'Update Assessments', 'Update assessments and complete them', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('7e356f13-71b2-4447-95e5-b1d9284f26e1', 'assessments.view', 'assessments', 'view', 'View Assessments', 'View assessments and findings', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('7f9057c2-d375-4517-98ec-84956a68343b', 'admin_console.delete', 'admin_console', 'delete', 'Admin Console — Delete', 'Permission to delete admin console.', '2026-03-16T13:55:43.276752', '2026-03-16T13:55:43.276752'),
      ('82ea4262-c4f8-4ccb-aa94-466fc3fde999', 'notification_templates.view', 'notification_templates', 'view', 'notification_templates view', 'Permission to view notification_templates', '2026-03-14T08:44:05.315403', '2026-03-14T08:44:05.315403'),
      ('90547321-261e-4d52-a79c-dc2e6f441e0b', 'ai_evidence_checker.view', 'ai_evidence_checker', 'view', 'View Evidence Check Reports', 'Read evidence check reports', '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391'),
      ('91dd81b2-8d4a-41ac-94a5-1106d459a0be', 'notification_broadcasts.create', 'notification_broadcasts', 'create', 'notification_broadcasts create', 'Permission to create notification_broadcasts', '2026-03-14T08:44:05.635405', '2026-03-14T08:44:05.635405'),
      ('96f825f4-8b6d-48ea-914f-15afe230fbc8', 'notification_broadcasts.view', 'notification_broadcasts', 'view', 'notification_broadcasts view', 'Permission to view notification_broadcasts', '2026-03-14T08:44:05.571505', '2026-03-14T08:44:05.571505'),
      ('97bf4a0a-7afd-47cb-bc1f-974c8d7cb3d6', 'policy_management.view', 'policy_management', 'view', 'Policy Management — View', 'Permission to view policy management.', '2026-03-24T11:16:10.615645', '2026-03-24T11:16:10.615645'),
      ('a14daddc-fb26-4f71-9e4c-fb60dc2a8c9a', 'group_access_assignment.delete', 'group_access_assignment', 'delete', 'group_access_assignment.delete', 'group_access_assignment.delete', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('a59a9d62-3e75-47ae-b485-11b0d6c8669e', 'group_access_assignment.update', 'group_access_assignment', 'update', 'group_access_assignment.update', 'group_access_assignment.update', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('a722cf91-835e-4616-8caf-f56a8451d70e', 'ai_evidence_checker.trigger', 'ai_evidence_checker', 'create', 'Trigger Evidence Check', 'Manually trigger AI evidence evaluation', '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391'),
      ('b536b3c5-d955-441b-a439-4a57243b049a', 'global_risk_library.update', 'global_risk_library', 'update', 'Update Global Risks', 'Update global risks', '2026-03-17T09:56:03.320987', '2026-03-17T09:56:03.320987'),
      ('b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', 'ai_copilot.execute', 'ai_copilot', 'execute', 'Execute AI Agents', 'Send messages, trigger agent runs, invoke read tools', '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('ba30a1c3-d974-4d81-8f2d-28bfccb4bf6b', 'reports.delete', 'reports', 'delete', 'Delete Reports', 'Delete GRC reports', '2026-03-18T14:23:34.277884', '2026-03-18T14:23:34.277884'),
      ('bc922db4-d4f5-4a10-83be-cc92b6af097a', 'audit_logs_access.view', 'audit_logs_access', 'view', 'View privilege', 'Read-only visibility of a feature or console area.', '2026-03-16T10:13:58.896856', '2026-03-16T10:13:58.896856'),
      ('c20bad33-1a4a-46fc-9157-9e7ecab76ee4', 'policy_management.assign', 'policy_management', 'assign', 'Policy Management — Assign', 'Permission to assign policy management.', '2026-03-24T11:16:59.147417', '2026-03-24T11:16:59.147417'),
      ('c47e6c29-5556-4b4c-a1b2-14a02fcec5de', 'findings.create', 'findings', 'create', 'Create Findings', 'Create findings in an assessment', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('cd7ac714-d579-4380-93d4-83e1c6dbc17b', 'ai_copilot.admin', 'ai_copilot', 'assign', 'AI Admin', 'View all users conversations, manage budgets, configure guardrails, kill agents', '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('d0f29e6c-218e-4deb-8d6d-956db7fb12bf', 'ai_copilot.create', 'ai_copilot', 'create', 'Create AI Conversations', 'Start new conversations, archive, manage own history', '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('dc8b435a-6aea-432e-8504-191a78bf53dc', 'notification_broadcasts.update', 'notification_broadcasts', 'update', 'notification_broadcasts update', 'Permission to update notification_broadcasts', '2026-03-14T08:44:05.698225', '2026-03-14T08:44:05.698225'),
      ('e18a4b59-eb37-4df3-9c09-263cf74ea33a', 'findings.view', 'findings', 'view', 'View Findings', 'View finding details and responses', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('e6be427a-3f30-4fee-af22-cf8cc215da4e', 'workspace_management.delete', 'workspace_management', 'delete', 'workspace_management.delete', 'workspace_management.delete', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('ea89e772-4707-4117-9306-bd047278cb2c', 'notification_templates.update', 'notification_templates', 'update', 'notification_templates update', 'Permission to update notification_templates', '2026-03-14T08:44:05.44338', '2026-03-14T08:44:05.44338'),
      ('ebbeba6f-b172-4038-a2a3-384060a1ec43', 'feature_flag_registry.delete', 'feature_flag_registry', 'delete', 'feature_flag_registry.delete', 'feature_flag_registry.delete', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('edcd40a1-d791-4ca0-9955-4766088115f1', 'ai_copilot.approve', 'ai_copilot', 'approve', 'Approve AI Actions', 'Approve or reject pending write tool approval requests', '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('ee241772-1028-47fe-813c-04377db03e20', 'group_access_assignment.create', 'group_access_assignment', 'create', 'group_access_assignment.create', 'group_access_assignment.create', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('f70226ef-a1da-4e9c-8115-2388b7436e9a', 'frameworks.approve', 'framework_management', 'approve', 'Approve Frameworks', 'Approve and publish frameworks to the marketplace', '2026-03-18T13:47:14.553559', '2026-03-18T13:47:14.553559')
  ON CONFLICT (code) DO UPDATE SET feature_flag_code = EXCLUDED.feature_flag_code, permission_action_code = EXCLUDED.permission_action_code, name = EXCLUDED.name, description = EXCLUDED.description, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.21_dim_feature_flag_setting_keys (7 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."21_dim_feature_flag_setting_keys" (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
  VALUES
      ('06cf8b88-7897-4a45-ab6a-b8b45df44db2', 'owner_team', 'Owner Team', 'Team responsible for this flag', 'string', FALSE, FALSE, 30, '2026-03-14T05:39:34.091812', '2026-03-14T05:39:34.091812'),
      ('33946021-e7a2-4144-be8b-d12e38700c6d', 'org_visibility', 'Org Admin Visibility', 'Controls whether org admins can see and/or toggle this flag: hidden, locked, or unlocked', 'string', FALSE, FALSE, 5, '2026-03-15T06:22:00.095762', '2026-03-15T06:22:00.095762'),
      ('7fa48dfa-315f-49b5-a0b4-37aea83acfc9', 'notes', 'Notes', 'Internal notes about this flag', 'string', FALSE, FALSE, 50, '2026-03-14T05:39:34.091812', '2026-03-14T05:39:34.091812'),
      ('b0c3e5fd-6be0-43a0-ae2b-9748ee222491', 'rollout_percentage', 'Rollout Percentage', 'Percentage of users who see this flag', 'integer', FALSE, FALSE, 10, '2026-03-14T05:39:34.091812', '2026-03-14T05:39:34.091812'),
      ('e2e03e50-4a95-4c69-88dc-4aa64134d618', 'jira_ticket', 'Jira Ticket', 'Linked Jira/issue tracker ticket', 'string', FALSE, FALSE, 40, '2026-03-14T05:39:34.091812', '2026-03-14T05:39:34.091812'),
      ('f1a2f46e-bf62-4f4e-a8e1-ae3fc2fb291e', 'sunset_date', 'Sunset Date', 'Planned removal date (ISO 8601)', 'string', FALSE, FALSE, 20, '2026-03-14T05:39:34.091812', '2026-03-14T05:39:34.091812'),
      ('ffdac139-e578-418a-b09a-9d836cd9c801', 'required_license', 'Required License Tier', 'Minimum license tier required to use this feature: free, pro, or internal. Empty = available to all.', 'string', FALSE, FALSE, 6, '2026-03-15T06:22:00.095762', '2026-03-15T06:22:00.095762')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_pii = EXCLUDED.is_pii, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.22_dim_role_setting_keys (5 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."22_dim_role_setting_keys" (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
  VALUES
      ('187af94f-133e-488a-a1c7-919abc148e23', 'color', 'Color', 'Role badge color (hex)', 'string', FALSE, FALSE, 10, '2026-03-14T05:39:33.994205', '2026-03-14T05:39:33.994205'),
      ('2233297d-89d1-4fcc-903a-9429bb20ba82', 'max_assignments', 'Max Assignments', 'Maximum users that can hold this role', 'integer', FALSE, FALSE, 50, '2026-03-14T05:39:33.994205', '2026-03-14T05:39:33.994205'),
      ('6bdb9cea-80d7-4864-afb5-3f9c3765698f', 'icon', 'Icon', 'Role icon name', 'string', FALSE, FALSE, 20, '2026-03-14T05:39:33.994205', '2026-03-14T05:39:33.994205'),
      ('9cf7902c-55ae-4b2c-867b-d78783890445', 'priority', 'Priority', 'Role display priority (lower = first)', 'integer', FALSE, FALSE, 30, '2026-03-14T05:39:33.994205', '2026-03-14T05:39:33.994205'),
      ('d91a440e-f884-4002-8779-f123ab5272e9', 'description_long', 'Long Description', 'Extended role description', 'string', FALSE, FALSE, 40, '2026-03-14T05:39:33.994205', '2026-03-14T05:39:33.994205')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_pii = EXCLUDED.is_pii, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.23_dim_product_types (7 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."23_dim_product_types" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000001101', 'saas_platform', 'SaaS Platform', 'Full SaaS product instance.', 10, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001102', 'sandbox', 'Sandbox', 'Sandboxed testing or preview instance.', 20, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001103', 'developer_tool', 'Developer Tool', 'Developer tooling product.', 30, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001104', 'data_platform', 'Data Platform', 'Data and analytics product.', 40, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('130d0980-cb24-4c0b-a627-1f27b1ea813b', 'saas', 'SaaS', 'SaaS', 1, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446'),
      ('19bc6898-0c50-4178-bb15-a9660c13a4ef', 'platform', 'Platform', 'Platform', 1, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446'),
      ('513f988b-130b-43e2-bf3e-9aab89371181', 'api', 'API', 'API', 1, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.26_dim_product_setting_keys (6 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."26_dim_product_setting_keys" (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
  VALUES
      ('18763ebe-37d9-49db-a5d4-8a572ef52c99', 'support_email', 'Support Email', 'Product support email', 'email', FALSE, FALSE, 60, '2026-03-14T05:39:33.94556', '2026-03-14T05:39:33.94556'),
      ('8344c79d-08a0-4225-a832-015210b1a24a', 'tier', 'Tier', 'Product tier (free, pro, enterprise)', 'string', FALSE, FALSE, 10, '2026-03-14T05:39:33.94556', '2026-03-14T05:39:33.94556'),
      ('a8a9f9af-6cd8-498c-a527-c442bdebe88c', 'pricing_model', 'Pricing Model', 'Pricing model (per_seat, flat, usage)', 'string', FALSE, FALSE, 20, '2026-03-14T05:39:33.94556', '2026-03-14T05:39:33.94556'),
      ('ca8f5dde-7491-4f1a-b45c-a9428d1d9e0d', 'trial_days', 'Trial Days', 'Number of trial days', 'integer', FALSE, FALSE, 30, '2026-03-14T05:39:33.94556', '2026-03-14T05:39:33.94556'),
      ('e15f6a55-e668-4821-bebb-43a763122ddb', 'logo_url', 'Logo URL', 'Product logo URL', 'url', FALSE, FALSE, 50, '2026-03-14T05:39:33.94556', '2026-03-14T05:39:33.94556'),
      ('fa2f647b-1825-4d47-8164-7fffa95c2e7a', 'max_users', 'Max Users', 'Maximum users per subscription', 'integer', FALSE, FALSE, 40, '2026-03-14T05:39:33.94556', '2026-03-14T05:39:33.94556')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_pii = EXCLUDED.is_pii, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.27_dim_group_setting_keys (5 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."27_dim_group_setting_keys" (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
  VALUES
      ('273d3057-db66-40f7-a885-74c15d91c2d9', 'description_long', 'Long Description', 'Extended group description', 'string', FALSE, FALSE, 40, '2026-03-14T05:39:34.043043', '2026-03-14T05:39:34.043043'),
      ('8866856c-93d0-4669-9c98-274654e6ddd0', 'max_members', 'Max Members', 'Maximum member count', 'integer', FALSE, FALSE, 30, '2026-03-14T05:39:34.043043', '2026-03-14T05:39:34.043043'),
      ('91feb90d-2d98-45ad-b4b1-16117356b190', 'auto_join', 'Auto Join', 'Automatically join new users', 'boolean', FALSE, FALSE, 50, '2026-03-14T05:39:34.043043', '2026-03-14T05:39:34.043043'),
      ('c3505ebf-75d4-4c48-9396-a845209bc0d9', 'color', 'Color', 'Group badge color (hex)', 'string', FALSE, FALSE, 10, '2026-03-14T05:39:34.043043', '2026-03-14T05:39:34.043043'),
      ('fef6a32e-f97b-4ab8-957c-21b64fbfe013', 'icon', 'Icon', 'Group icon name', 'string', FALSE, FALSE, 20, '2026-03-14T05:39:34.043043', '2026-03-14T05:39:34.043043')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_pii = EXCLUDED.is_pii, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.28_dim_org_types (7 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."28_dim_org_types" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000001301', 'company', 'Company', 'Commercial company or enterprise.', 10, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001302', 'community', 'Community', 'Open community or non-profit.', 20, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001303', 'personal', 'Personal', 'Personal org for solo users.', 30, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001304', 'partner', 'Partner', 'Partner or reseller organization.', 40, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001305', 'internal', 'Internal', 'Internal team or department.', 50, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('464685e6-a147-4457-91fe-58659325e940', 'enterprise', 'Enterprise', 'Enterprise', 1, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446'),
      ('dfe12e9f-c8be-433f-96a3-50c0b074e9e8', 'startup', 'Startup', 'Startup', 1, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.31_dim_org_setting_keys (15 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."31_dim_org_setting_keys" (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
  VALUES
      ('02f7443b-a76b-4b21-a37b-be551534c24d', 'max_users', 'Max Users', 'Maximum number of users allowed', 'integer', FALSE, FALSE, 3, '2026-03-15T06:22:00.095762', '2026-03-15T06:22:00.095762'),
      ('2b6f6624-7302-4672-9c4a-3a83d94298fa', 'license_profile', 'License Profile', 'Code of the license profile assigned to this organization (determines tier + defaults)', 'string', FALSE, FALSE, 2, '2026-03-15T06:52:28.73803', '2026-03-15T06:52:28.73803'),
      ('3bc3ee35-5519-4d60-8ed0-080acde88ef2', 'logo_url', 'Logo URL', 'Organization logo image URL', 'url', FALSE, FALSE, 10, '2026-03-14T05:39:33.848187', '2026-03-14T05:39:33.848187'),
      ('45ed3781-8d79-4551-8a74-db4146656340', 'industry', 'Industry', 'Industry or sector', 'string', FALSE, FALSE, 30, '2026-03-14T05:39:33.848187', '2026-03-14T05:39:33.848187'),
      ('4bd2402a-2e02-4618-a2a2-55557342d347', 'country', 'Country', 'Country code (ISO 3166-1 alpha-2)', 'string', FALSE, FALSE, 80, '2026-03-14T05:39:33.848187', '2026-03-14T05:39:33.848187'),
      ('5829e6ee-a618-45e1-a1a6-3c6c01113da9', 'license_tier', 'License Tier', 'Organization license tier: free, pro, pro_trial, or internal', 'string', FALSE, FALSE, 1, '2026-03-15T06:22:00.095762', '2026-03-15T06:22:00.095762'),
      ('65ee9917-858a-4f9a-9b92-0c19c8aadd9d', 'website', 'Website', 'Organization website URL', 'url', FALSE, FALSE, 20, '2026-03-14T05:39:33.848187', '2026-03-14T05:39:33.848187'),
      ('7da21a01-aa88-492d-a764-3ac40633465d', 'tax_id', 'Tax ID', 'Tax identification number', 'string', TRUE, FALSE, 60, '2026-03-14T05:39:33.848187', '2026-03-14T05:39:33.848187'),
      ('87eb8eb7-6916-4274-bf78-71e2c877ed21', 'license_expires_at', 'License Expiry', 'ISO 8601 date when pro_trial expires', 'string', FALSE, FALSE, 2, '2026-03-15T06:22:00.095762', '2026-03-15T06:22:00.095762'),
      ('8bf87e75-5b34-4f2e-b237-0eaa45bd059a', 'enabled_features', 'Enabled Features', 'JSON array of feature flag codes enabled for this organization', 'json', FALSE, FALSE, 5, '2026-03-15T06:22:00.095762', '2026-03-15T06:22:00.095762'),
      ('95b10dc9-9cc1-41e9-96dd-0f1d4ba70953', 'max_frameworks', 'Max Frameworks', 'Maximum number of compliance frameworks', 'integer', FALSE, FALSE, 6, '2026-03-15T06:22:00.095762', '2026-03-15T06:22:00.095762'),
      ('9d1907c2-d6f8-4c5d-adf4-32b3069bc902', 'phone', 'Phone', 'Organization phone number', 'phone', TRUE, FALSE, 50, '2026-03-14T05:39:33.848187', '2026-03-14T05:39:33.848187'),
      ('a8cb5b2c-2fd1-4f3d-af0e-9e5b04913d81', 'max_workspaces', 'Max Workspaces', 'Maximum number of workspaces allowed', 'integer', FALSE, FALSE, 4, '2026-03-15T06:22:00.095762', '2026-03-15T06:22:00.095762'),
      ('b53afdb0-cded-4bde-8da5-446cb7e3ca34', 'address', 'Address', 'Primary business address', 'string', TRUE, FALSE, 40, '2026-03-14T05:39:33.848187', '2026-03-14T05:39:33.848187'),
      ('df970605-f5f2-4b14-8dc6-a2f9bd9d96b1', 'description', 'Description', 'Organization description', 'string', FALSE, FALSE, 70, '2026-03-14T05:39:33.848187', '2026-03-14T05:39:33.848187')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_pii = EXCLUDED.is_pii, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.33_dim_workspace_types (10 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."33_dim_workspace_types" (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000001401', 'project', 'Project', 'A software project or product initiative.', 10, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001402', 'team', 'Team', 'A team collaboration workspace.', 20, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001403', 'environment_dev', 'Dev Environment', 'Development deployment environment.', 30, TRUE, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001404', 'environment_staging', 'Staging Environment', 'Pre-production staging environment.', 40, TRUE, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001405', 'environment_prod', 'Prod Environment', 'Production deployment environment.', 50, TRUE, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001406', 'sandbox', 'Sandbox', 'Sandbox or experimental workspace.', 60, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001407', 'shared', 'Shared Resources', 'Shared cross-team resources workspace.', 70, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('04015f0f-2283-4dd7-97de-a03673c81782', 'staging', 'Staging', 'Staging', 1, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446'),
      ('a9240c2b-43c1-4f93-94ad-0ca247166ec0', 'development', 'Development', 'Development', 1, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446'),
      ('f5c9c1c3-1730-4e86-b777-35b4e21bde95', 'production', 'Production', 'Production', 1, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_infrastructure_type = EXCLUDED.is_infrastructure_type, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.36_dim_workspace_setting_keys (6 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."36_dim_workspace_setting_keys" (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
  VALUES
      ('34c2ee5d-f2fd-4969-9138-e01fd61c2b86', 'notification_email', 'Notification Email', 'Email for workspace notifications', 'email', FALSE, FALSE, 60, '2026-03-14T05:39:33.896316', '2026-03-14T05:39:33.896316'),
      ('6959f321-ddfe-49b8-a674-d1c42fa78e94', 'color', 'Color', 'Workspace accent color (hex)', 'string', FALSE, FALSE, 10, '2026-03-14T05:39:33.896316', '2026-03-14T05:39:33.896316'),
      ('88283c3d-0ac9-4f15-97e0-7f6bb3c8c8b7', 'max_members', 'Max Members', 'Maximum member count', 'integer', FALSE, FALSE, 40, '2026-03-14T05:39:33.896316', '2026-03-14T05:39:33.896316'),
      ('b3d23c2b-490e-4fb2-8e87-5d8ca864922e', 'timezone', 'Timezone', 'Workspace default timezone (IANA)', 'string', FALSE, FALSE, 50, '2026-03-14T05:39:33.896316', '2026-03-14T05:39:33.896316'),
      ('b71674d8-014a-42e5-8b1a-0c394f9ea10f', 'icon', 'Icon', 'Workspace icon name or URL', 'string', FALSE, FALSE, 20, '2026-03-14T05:39:33.896316', '2026-03-14T05:39:33.896316'),
      ('be02e94d-7072-4fda-9024-95e4a562aaa5', 'description', 'Description', 'Workspace description', 'string', FALSE, FALSE, 30, '2026-03-14T05:39:33.896316', '2026-03-14T05:39:33.896316')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_pii = EXCLUDED.is_pii, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.43_dim_invite_statuses (5 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."43_dim_invite_statuses" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('00000000-0000-0000-0000-000000001001', 'pending', 'Pending', 'Invitation sent and awaiting response.', 10, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001002', 'accepted', 'Accepted', 'Invitation accepted by the invitee.', 20, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001003', 'revoked', 'Revoked', 'Invitation revoked by the inviter.', 30, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001004', 'expired', 'Expired', 'Invitation expired before acceptance.', 40, '2026-03-13T00:00:00', '2026-03-13T00:00:00'),
      ('00000000-0000-0000-0000-000000001005', 'declined', 'Declined', 'Invitation declined by the invitee.', 50, '2026-03-13T00:00:00', '2026-03-13T00:00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.24_fct_products (2 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."24_fct_products" (id, tenant_key, product_type_code, code, name, description, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
  VALUES
      ('00000000-0000-0000-0000-000000001201', 'default', 'saas_platform', 'kcontrol', 'K-Control', 'Primary K-Control SaaS platform.', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001202', 'default', 'sandbox', 'kcontrol_sandbox', 'K-Control Sandbox', 'Sandboxed testing instance of K-Control.', TRUE, FALSE, FALSE, TRUE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL)
  ON CONFLICT (tenant_key, code) DO UPDATE SET product_type_code = EXCLUDED.product_type_code, name = EXCLUDED.name, description = EXCLUDED.description, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.21_dtl_feature_flag_settings (5 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."21_dtl_feature_flag_settings" (id, feature_flag_id, setting_key, setting_value, created_at, updated_at, created_by, updated_by)
  VALUES
      ('33277d8a-a38c-415d-9045-ed96a8e9beac', '00000000-0000-0000-0000-000000003007', 'org_visibility', 'unlocked', '2026-03-24T10:39:29.739066', '2026-03-24T10:39:29.739066', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('3a7240d9-7bdd-424d-a497-8a40b0e58b1a', '00000000-0000-0000-0000-000000000403', 'org_visibility', 'unlocked', '2026-03-24T11:18:36.808359', '2026-03-24T11:31:45.310486', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('6b0f83fa-42be-46e4-adb0-26aa5dce36da', '00000000-0000-0000-0000-000000000550', 'org_visibility', 'unlocked', '2026-03-24T11:25:56.525666', '2026-03-24T11:25:56.525666', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('bb2d62ac-b155-4ad8-855d-10ec3e8f7221', '00000000-0000-0000-0000-000000003003', 'org_visibility', 'unlocked', '2026-03-24T05:26:22.727209', '2026-03-24T05:26:22.727209', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('dc9d9c64-b533-4f67-8cce-5b325948c08d', '00000000-0000-0000-0000-000000003001', 'org_visibility', 'unlocked', '2026-03-21T14:25:36.854519', '2026-03-23T05:41:57.242253', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223')
  ON CONFLICT (feature_flag_id, setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.37_fct_license_profiles (6 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."37_fct_license_profiles" (id, code, name, description, tier, is_active, sort_order, created_at, updated_at)
  VALUES
      ('4971ef98-3fd0-4140-821a-eea64612d659', 'enterprise_default', 'Enterprise', 'Enterprise tier with custom limits.', 'enterprise', TRUE, 40, '2026-03-15T06:52:28.64039', '2026-03-15T06:52:28.64039'),
      ('7c0e2de3-0daf-4fd8-9cf5-eb0f85049077', 'free_default', 'Free', 'Default free tier profile with basic limits.', 'free', TRUE, 10, '2026-03-15T06:52:28.64039', '2026-03-15T06:52:28.64039'),
      ('8ce47bb5-702b-4627-ad7e-1b6befa82aa5', 'internal_default', 'Internal', 'Kreesalis internal organizations. No limits.', 'internal', TRUE, 60, '2026-03-15T06:52:28.64039', '2026-03-15T06:52:28.64039'),
      ('92f7328a-2e37-4a06-b1c1-e9bd5eb49e74', 'pro_default', 'Pro', 'Default pro tier profile with advanced limits.', 'pro', TRUE, 20, '2026-03-15T06:52:28.64039', '2026-03-15T06:52:28.64039'),
      ('c028e224-5113-43d5-89a3-6f25ac491d7c', 'partner_default', 'Partner', 'Partner organizations with special access.', 'partner', TRUE, 50, '2026-03-15T06:52:28.64039', '2026-03-15T06:52:28.64039'),
      ('dd3e7ec6-872c-4fbc-a2e7-2dee6fbd5c8e', 'pro_trial_default', 'Pro Trial', 'Temporary pro access for evaluation.', 'pro_trial', TRUE, 30, '2026-03-15T06:52:28.64039', '2026-03-15T06:52:28.64039')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, tier = EXCLUDED.tier, is_active = EXCLUDED.is_active, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.38_dtl_license_profile_settings (12 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings" (id, profile_id, setting_key, setting_value, created_at, updated_at)
  VALUES
      ('0284ee84-de09-4d57-bbe6-fe4ca8dbdc68', '92f7328a-2e37-4a06-b1c1-e9bd5eb49e74', 'max_users', '50', '2026-03-15T06:52:28.707231', '2026-03-15T06:52:28.707231'),
      ('058965cd-8a91-43fc-a358-35b4607ed2ca', '7c0e2de3-0daf-4fd8-9cf5-eb0f85049077', 'max_workspaces', '2', '2026-03-15T06:52:28.673884', '2026-03-15T06:52:28.673884'),
      ('064d0f25-93ef-4dbb-ab00-b1cacbf9243e', '92f7328a-2e37-4a06-b1c1-e9bd5eb49e74', 'max_frameworks', '10', '2026-03-15T06:52:28.707231', '2026-03-15T06:52:28.707231'),
      ('12948e72-a93c-45cb-8df1-c22feb2a9192', 'dd3e7ec6-872c-4fbc-a2e7-2dee6fbd5c8e', 'max_external_users', '100', '2026-03-17T15:38:38.542632', '2026-03-17T15:38:38.542632'),
      ('2a7cade8-4f29-4a95-8fa3-cc2f3f2cd6a6', '4971ef98-3fd0-4140-821a-eea64612d659', 'max_external_users', '500', '2026-03-17T15:38:38.583209', '2026-03-17T15:38:38.583209'),
      ('53ba97ca-a66d-4968-b320-d7cbcc9b1939', '8ce47bb5-702b-4627-ad7e-1b6befa82aa5', 'max_external_users', '999999', '2026-03-17T15:38:38.67027', '2026-03-17T15:38:38.67027'),
      ('69bf7a68-8161-4fa5-ad16-457cc444c51f', '92f7328a-2e37-4a06-b1c1-e9bd5eb49e74', 'max_external_users', '100', '2026-03-17T15:38:38.501734', '2026-03-17T15:38:38.501734'),
      ('86e79020-f8f7-46d0-aed2-34934355656e', '7c0e2de3-0daf-4fd8-9cf5-eb0f85049077', 'max_users', '5', '2026-03-15T06:52:28.673884', '2026-03-15T06:52:28.673884'),
      ('b42f0394-dda2-4d18-8f94-d04a05d295fa', '92f7328a-2e37-4a06-b1c1-e9bd5eb49e74', 'max_workspaces', '20', '2026-03-15T06:52:28.707231', '2026-03-15T06:52:28.707231'),
      ('b6853e3e-722a-4457-8eee-ad3914331cbb', '7c0e2de3-0daf-4fd8-9cf5-eb0f85049077', 'max_external_users', '10', '2026-03-17T15:38:38.459673', '2026-03-17T15:38:38.459673'),
      ('ca98deae-10a7-41f1-9070-b7639ea24245', '7c0e2de3-0daf-4fd8-9cf5-eb0f85049077', 'max_frameworks', '1', '2026-03-15T06:52:28.673884', '2026-03-15T06:52:28.673884'),
      ('d9f8f798-9ab0-4405-a22a-69102fdf0b98', 'c028e224-5113-43d5-89a3-6f25ac491d7c', 'max_external_users', '50', '2026-03-17T15:38:38.627844', '2026-03-17T15:38:38.627844')
  ON CONFLICT (license_profile_id, setting_key) DO UPDATE SET profile_id = EXCLUDED.profile_id, setting_value = EXCLUDED.setting_value, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.16_fct_roles (13 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."16_fct_roles" (id, tenant_key, role_level_code, code, name, description, scope_org_id, scope_workspace_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
  VALUES
      ('00000000-0000-0000-0000-000000000601', 'default', 'super_admin', 'platform_super_admin', 'Platform Super Admin', 'System role for full platform feature governance control.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000002001', 'default', 'platform', 'basic_user', 'Basic User', 'Default role granted to every registered user. Allows onboarding setup.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T00:00:00', '2026-03-14T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000003100', '__platform__', 'platform', 'grc_compliance_lead', 'GRC Compliance Lead', 'Full access to all GRC features', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-15T18:22:50.558202', '2026-03-15T18:22:50.558202', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000003101', '__platform__', 'platform', 'grc_control_owner', 'GRC Control Owner', 'View frameworks, manage controls and tests', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-15T18:22:50.558202', '2026-03-15T18:22:50.558202', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000003102', '__platform__', 'platform', 'grc_risk_manager', 'GRC Risk Manager', 'Full risk management, view frameworks and controls', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-15T18:22:50.558202', '2026-03-15T18:22:50.558202', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004001', 'default', 'org', 'org_admin', 'Org Admin', 'Full administrative control within an organization. Can manage org settings, members, and all workspaces.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.657832', '2026-03-17T06:38:32.657832', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004002', 'default', 'org', 'org_member', 'Org Member', 'Standard organization member. Can view org, interact with all workspaces, but cannot administer the org.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.686831', '2026-03-17T06:38:32.686831', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004003', 'default', 'org', 'org_viewer', 'Org Viewer', 'Read-only organization access. Can view org details but cannot modify anything. No workspace access unless separately granted.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.713382', '2026-03-17T06:38:32.713382', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004011', 'default', 'workspace', 'workspace_admin', 'Workspace Admin', 'Full administrative control within a workspace. Can manage workspace settings and members.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.741419', '2026-03-17T06:38:32.741419', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004012', 'default', 'workspace', 'workspace_contributor', 'Workspace Contributor', 'Can view and contribute to workspace content. Cannot manage members or settings.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.769931', '2026-03-17T06:38:32.769931', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004013', 'default', 'workspace', 'workspace_viewer', 'Workspace Viewer', 'Read-only workspace access. Can view workspace content but cannot modify anything.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.857507', '2026-03-17T06:38:32.857507', NULL, NULL, NULL, NULL),
      ('6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'default', 'platform', 'external_collaborator', 'External Collaborator', 'Limited platform role for external users who authenticate via magic link. Grants read-only access to tasks, comments, and attachments.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T15:38:38.28856', '2026-03-17T15:38:38.28856', NULL, NULL, NULL, NULL),
      ('9441cc00-943f-4469-aef5-7fae7171b2b9', 'default', 'platform', 'super_admin', 'Super Admin', 'Full platform access', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL)
  ON CONFLICT (tenant_key, role_level_code, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, scope_org_id = EXCLUDED.scope_org_id, scope_workspace_id = EXCLUDED.scope_workspace_id, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.17_fct_user_groups (4 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."17_fct_user_groups" (id, tenant_key, role_level_code, code, name, description, scope_org_id, scope_workspace_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by, parent_group_id)
  VALUES
      ('00000000-0000-0000-0000-000000000701', 'default', 'super_admin', 'platform_super_admin', 'Platform Super Admin', 'System group for platform super administrators.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000003001', 'default', 'platform', 'default_users', 'Default Users', 'Every registered user is automatically a member of this group.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T00:00:00', '2026-03-14T00:00:00', NULL, NULL, NULL, NULL, NULL),
      ('0ed8698f-247b-4d00-9155-d12cb2f0be47', 'default', 'platform', 'platform_admins', 'Platform Admins', 'Platform administrators', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL, NULL),
      ('9e4e4815-0123-4ea0-8f46-e6663ee8ca95', 'default', 'platform', 'external_collaborators', 'External Collaborators', 'System group for all external collaborator users. Automatically enrolled when a user authenticates via magic link for the first time.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T15:38:38.329908', '2026-03-17T15:38:38.329908', NULL, NULL, NULL, NULL, NULL)
  ON CONFLICT (tenant_key, role_level_code, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, scope_org_id = EXCLUDED.scope_org_id, scope_workspace_id = EXCLUDED.scope_workspace_id, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by, parent_group_id = EXCLUDED.parent_group_id;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.19_lnk_group_role_assignments (4 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (id, group_id, role_id, assignment_status, effective_from, effective_to, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
  VALUES
      ('00000000-0000-0000-0000-000000000801', '00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000601', 'active', '2026-03-13T00:00:00', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003001', '00000000-0000-0000-0000-000000002001', 'active', '2026-03-14T00:00:00', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T00:00:00', '2026-03-14T00:00:00', NULL, NULL, NULL, NULL),
      ('afeb32b0-fc67-42c2-a418-b6ac64da34f3', '0ed8698f-247b-4d00-9155-d12cb2f0be47', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'active', '2026-03-13T17:33:40.526446', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('c0c87fbc-3e9f-49b7-bbbf-541dbfeaa46e', '9e4e4815-0123-4ea0-8f46-e6663ee8ca95', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'active', '2026-03-17T15:38:38.371545', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T15:38:38.371545', '2026-03-17T15:38:38.371545', NULL, NULL, NULL, NULL)
  ON CONFLICT (group_id, role_id) DO UPDATE SET assignment_status = EXCLUDED.assignment_status, effective_from = EXCLUDED.effective_from, effective_to = EXCLUDED.effective_to, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.20_lnk_role_feature_permissions (514 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
  VALUES
      ('00000000-0000-0000-0000-000000000901', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000508', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000000902', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000509', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000000903', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000000904', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050b', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000000905', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050c', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000000906', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050d', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000000907', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050e', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000000908', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050f', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000000909', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000510', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-00000000090a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000511', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-00000000090b', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000512', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-00000000090c', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000513', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-00000000090d', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000514', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-00000000090e', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000515', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-00000000090f', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000516', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001701', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001701', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001702', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001702', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001703', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001703', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001704', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001704', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001705', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001705', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001711', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001712', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001712', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001713', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001713', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001714', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001714', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001715', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001715', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001721', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001722', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001723', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001724', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001725', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001811', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001811', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001812', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001812', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001813', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001813', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001814', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001814', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001815', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001815', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001816', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001816', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001817', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001817', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001818', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001818', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000001819', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000001819', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-00000000181a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000181a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('0067a526-c306-417b-b0c4-8d5fb2381e40', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('008bf425-619f-40d3-837d-d4c65e7c1cf1', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'e6be427a-3f30-4fee-af22-cf8cc215da4e', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('010c9a41-9ed7-4318-882b-cac4d8534a85', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000006022', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-17T05:29:38.378682', '2026-03-17T05:29:39.525567', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-17T05:29:39.525567', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('02281d1e-ab38-4fe4-891c-8756a60e6963', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000005024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.878099', '2026-03-16T11:40:41.878099', NULL, NULL, NULL, NULL),
      ('024926e6-6998-4240-b733-5805fd6bbee9', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('02aaba78-f3ac-4651-9cb2-81c5cfecf490', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000006020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.082914', '2026-03-16T11:39:11.082914', NULL, NULL, NULL, NULL),
      ('042fa50b-ff9c-4211-9423-88c8b6f43f7f', '00000000-0000-0000-0000-000000003100', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('050d1daa-3d36-4a8d-922e-cf717a4e4278', '00000000-0000-0000-0000-000000000601', 'bc922db4-d4f5-4a10-83be-cc92b6af097a', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('05487684-13ff-4d84-afa0-3e679bd0cc6d', '00000000-0000-0000-0000-000000000601', '55963948-87ca-47e7-9de7-ddd7f3dc675f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:18:16.315393', '2026-03-17T11:18:16.315393', NULL, NULL, NULL, NULL),
      ('06076075-aafc-45a8-8fcc-299f495f6f65', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000509', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('08394d1a-c83f-40e2-bb48-2aab23c1b6b1', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '73f7950d-7163-4467-837d-b6907dd0abcf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.676368', '2026-03-14T08:45:17.676368', NULL, NULL, NULL, NULL),
      ('0856c8fa-9a8e-4298-a12b-e3b970f7e91a', '00000000-0000-0000-0000-000000003102', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('098c9bb5-11b2-4a66-bd74-76992e36b07a', '9441cc00-943f-4469-aef5-7fae7171b2b9', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('0a12fdda-934a-4c82-a1c3-76766ede1984', '00000000-0000-0000-0000-000000003102', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('0aee4b8d-af42-44d5-a010-ffc684a2533d', '9441cc00-943f-4469-aef5-7fae7171b2b9', '11582d29-77d4-49ed-b8a4-ef7a1c3c540f', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('0b1f0d80-4f5c-407c-86a8-a2b1be850c10', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '96f825f4-8b6d-48ea-914f-15afe230fbc8', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.726112', '2026-03-14T08:45:17.726112', NULL, NULL, NULL, NULL),
      ('0be0c367-a78d-46ae-b22c-af071531db93', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003041', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('0c05c774-1ba6-4a54-a96d-58ecd47b3703', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('0c67d4db-ad94-41f9-a72c-170acf9f32cd', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('0d522ad8-c100-4f81-bd4b-13a67a5134ef', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050f', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('0d87e5cf-ad3b-4dd6-b2fc-e87ece76d20a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005024', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('0d88cb48-5bb1-4af3-927d-46b82f334644', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001817', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('0d8c3e4a-d373-47a6-9cd0-e737872266ba', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'a59a9d62-3e75-47ae-b485-11b0d6c8669e', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('0db26608-7a66-475a-83d8-28e329973750', '00000000-0000-0000-0000-000000004011', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('0ddcff5f-cd56-45f7-8d58-bd5a741005da', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('0ecdf057-008e-4de8-965e-e6bfba3c22af', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001713', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('10a36232-fcd7-46ac-8773-6c79aab60be3', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('11e9a2e9-a4fc-4d41-8357-931d1c6c2410', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.991631', '2026-03-14T08:45:15.991631', NULL, NULL, NULL, NULL),
      ('12981856-7a07-4042-b94f-2e9c0956fb8a', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('13ebcdc5-ec85-4282-a230-bae43427232d', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('143f4277-45bc-4e92-a2ec-0001ac7e3b9d', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.905989', '2026-03-14T08:45:14.905989', NULL, NULL, NULL, NULL),
      ('144b878f-4503-4771-8e70-505078935fda', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003033', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('1472ad68-a68d-4f85-8bf3-4cc73f644cd6', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003065', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('156ac245-c214-4ea7-8215-0b709ac274bc', '9441cc00-943f-4469-aef5-7fae7171b2b9', '7f9057c2-d375-4517-98ec-84956a68343b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T13:56:11.417625', '2026-03-16T13:56:11.417625', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('164ddb85-d9c7-474c-a61f-f498976b319b', '00000000-0000-0000-0000-000000003101', '20dfe0b5-3990-4bb4-bc02-6f93b8673e36', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('1683dd05-021d-419f-9537-071af26c0192', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001714', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.697235', '2026-03-14T08:45:15.697235', NULL, NULL, NULL, NULL),
      ('16d22e6b-924c-471c-867a-52e6b26e0a93', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005021', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('16dbf61f-80dc-41f7-882f-ed00a2a46c5c', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000505', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('1738d3fd-266e-4cb1-9009-76ffcdfcd21f', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000007021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.928461', '2026-03-22T15:08:53.928461', NULL, NULL, NULL, NULL),
      ('1750ac00-1ecd-43ae-a819-b1033e7987ea', '00000000-0000-0000-0000-000000002001', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('176ca84b-244b-44d8-96da-4b5173be1057', '00000000-0000-0000-0000-000000000601', '03dba1fa-5bdf-45a6-aa0a-aa6117fe6285', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:18:16.315393', '2026-03-17T11:18:16.315393', NULL, NULL, NULL, NULL),
      ('17826f49-01cc-4437-a21e-d08250d09736', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000555', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('17b1a57a-2273-4332-b404-ed82d0bd2fb8', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('189d4458-baf3-4752-b6bb-94c2c8cd037c', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000541', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('190a59aa-f475-44b0-ac0a-d36d28fb5547', 'e74bdcc5-4baf-47b2-9ab4-5bf00455c2b1', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-17T07:30:59.158594', '2026-03-17T07:31:01.747425', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', '2026-03-17T07:31:01.747425', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('1aeb7c7e-d0ed-4d61-9db0-09459ff03ce4', '00000000-0000-0000-0000-000000002001', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('1b666727-d5d7-4e2a-9ab3-969aba215187', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('1c1af33c-a5d2-4d61-a5a8-ae1dddb76367', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001813', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('1c34216f-405d-42cd-be05-401c6074646a', '65643275-fd73-40ef-b6d8-8069b3b18d52', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-14T01:29:28.118955', '2026-03-14T01:29:29.679819', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', '2026-03-14T01:29:29.679819', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b'),
      ('1c749feb-0d40-4dfd-9ef9-7d2daa08b124', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000504', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('1ce597c7-1625-48bb-a16d-892f97e20242', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000516', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.186953', '2026-03-14T08:45:17.186953', NULL, NULL, NULL, NULL),
      ('1d68a807-56b2-4912-8103-d1c536a38668', '00000000-0000-0000-0000-000000000601', '32c6f06d-fdcd-4a67-9a0c-9f1596978659', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('1d7c088a-2cfb-414a-9fc7-dd596c2d5f1b', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000006020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.057218', '2026-03-16T11:39:11.057218', NULL, NULL, NULL, NULL),
      ('1daebd63-abae-4de1-8ac9-d0ea2c53f263', '00000000-0000-0000-0000-000000000601', '96f825f4-8b6d-48ea-914f-15afe230fbc8', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('1de083f5-2d94-492a-8ba6-412169c60923', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001701', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.3008', '2026-03-14T08:45:15.3008', NULL, NULL, NULL, NULL),
      ('1de3de25-24cf-48e2-9cf7-3b98b23ef8df', '197ae046-a989-418f-99df-ec17310d73a4', '00000000-0000-0000-0000-000000006022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:44.016031', '2026-03-18T12:03:44.016031', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1e467d85-f417-4600-84c7-3c543639d93e', '00000000-0000-0000-0000-000000004012', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('1e481b01-577e-48f5-a5fc-66c96e4c0864', '197ae046-a989-418f-99df-ec17310d73a4', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:40.82988', '2026-03-18T12:03:40.82988', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1e8e0ca5-a179-4463-926d-fc76dafc6f59', '9a2f8bd7-f635-4cfe-9bad-8f640f50fe74', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:02:34.87345', '2026-03-18T12:02:34.87345', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', NULL, NULL),
      ('1ee75e0d-2d17-4c5b-adb9-236c6c1b99e9', 'e74bdcc5-4baf-47b2-9ab4-5bf00455c2b1', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('20066110-3537-45f4-aadd-5cc5cd92588a', '00000000-0000-0000-0000-000000004011', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('201cc15a-4a57-4870-88a1-33379f0f70ba', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003015', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T18:11:13.659325', '2026-03-18T18:11:13.659325', NULL, NULL, NULL, NULL),
      ('2031a183-25d4-4745-9ef3-d5317a3e29d7', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000543', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.10148', '2026-03-17T07:49:17.10148', NULL, NULL, NULL, NULL),
      ('2032fc1c-55ee-497d-bdb6-e67d8530336d', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '32c6f06d-fdcd-4a67-9a0c-9f1596978659', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.577762', '2026-03-14T08:45:17.577762', NULL, NULL, NULL, NULL),
      ('20c12ceb-83a5-4e16-9b6f-fe69c510e16c', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000512', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('20f4466b-356f-4c7e-a17b-5b0c0fa3ece2', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000007022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.961452', '2026-03-22T15:08:53.961452', NULL, NULL, NULL, NULL),
      ('2432a954-38b9-4579-9971-7c7e5fc556b4', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003065', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('252b2c4a-6647-4655-96b3-4f5c307a81f0', '9441cc00-943f-4469-aef5-7fae7171b2b9', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('2675a747-d414-4a59-88b2-c592c0c479a8', '00000000-0000-0000-0000-000000002001', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('274317e6-066f-4853-a52c-eff491b16ab0', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('2743e2c1-7b14-44a9-8849-d0ffa8040d5c', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000514', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.082744', '2026-03-14T08:45:17.082744', NULL, NULL, NULL, NULL),
      ('2847bdd1-4870-4efb-bc1b-c18ecdbb66a5', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('291ca0d0-406e-4b95-aa47-f29901a6b179', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001712', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('2953498c-8b41-4a6d-9742-7d67af0ea590', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('2a2af745-f071-483f-94b2-c8deb38025bd', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('2fb15698-4d81-42d6-a84c-ff77e67e0799', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'b536b3c5-d955-441b-a439-4a57243b049a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:16:43.585605', '2026-03-17T11:16:43.585605', NULL, NULL, NULL, NULL),
      ('2ff9ddfc-927d-47e3-ad88-c190d5bbe340', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.05298', '2026-03-14T08:45:15.05298', NULL, NULL, NULL, NULL),
      ('30321305-3027-4dbb-8f00-0049625c10e6', '00000000-0000-0000-0000-000000003102', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('3088d634-546d-4344-acf8-6f55f28474df', '00000000-0000-0000-0000-000000004011', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('30c4d300-d4d9-4ffa-aad4-f15b04173664', 'ddf8bcb6-6d66-472c-9b29-4c1c0e3a9d3f', '18e15e8f-21d4-4206-aac9-a7d116129277', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-16T12:34:42.823331', '2026-03-16T12:34:46.025535', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-16T12:34:46.025535', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('30d86fe9-d145-4dda-b202-e4e5aa72dbba', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006020', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('30e320e8-4ee4-40f7-8ec2-faeda204f8df', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000509', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.808768', '2026-03-14T08:45:14.808768', NULL, NULL, NULL, NULL),
      ('31bcd588-d358-4536-9138-a0fd8ef7018c', '50194e61-c46b-4b72-b52d-eb3f1aab1a2f', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-23T08:08:41.478535', '2026-03-23T08:08:44.489718', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', '2026-03-23T08:08:44.489718', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('31fc8a51-db6d-4f91-aacd-a9909b3818a6', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003052', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('325be562-5372-494d-be04-b08e2354e2dd', '197ae046-a989-418f-99df-ec17310d73a4', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:42.629382', '2026-03-18T12:03:42.629382', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('329824e0-4fef-40b1-ba5d-37e773c65535', '9441cc00-943f-4469-aef5-7fae7171b2b9', '18e15e8f-21d4-4206-aac9-a7d116129277', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('32b22422-61a7-40e2-b77d-179502394bd7', '00000000-0000-0000-0000-000000003100', '20dfe0b5-3990-4bb4-bc02-6f93b8673e36', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('32b93ad6-ff93-4cbe-863d-fe698f9100d3', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006024', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('32bf7887-709d-4f3a-bbb6-b5bb449111ab', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:13:43.791271', '2026-03-17T07:13:43.791271', NULL, NULL, NULL, NULL),
      ('331503ac-92d0-4590-878d-0a00a28d9e06', '0c45ac3c-8b8b-47f0-b8f6-27f0326c02f2', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('3431844d-98ac-4b1f-a64e-f7854a2b370a', '00000000-0000-0000-0000-000000004001', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('347da524-60bd-49e5-8857-8b682ff29e2f', '00000000-0000-0000-0000-000000003100', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('34a00e7c-b94e-4bd9-994a-c331e12370d3', '00000000-0000-0000-0000-000000004003', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.980336', '2026-03-17T06:38:32.980336', NULL, NULL, NULL, NULL),
      ('354c9e88-5764-429b-bc04-e8b0f116d657', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003011', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('35a45297-ab63-4a13-9573-f6a53774e8c2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003013', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('35cc8c6c-98c3-4fe2-971c-22b135d10877', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003072', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('362efce4-a76c-42e5-867d-f0f16b27ff29', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001812', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('36805922-fa6b-4814-9642-a74ef927efca', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.857642', '2026-03-14T08:45:14.857642', NULL, NULL, NULL, NULL),
      ('37cec61e-7d14-4fe9-8af9-64cf02e1dc75', 'e74bdcc5-4baf-47b2-9ab4-5bf00455c2b1', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('389524db-d531-4a6c-9457-3e9e97735e16', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('38a57f4d-6e50-4c32-9742-a0ff8c2b47df', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001712', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('38de9456-895f-4beb-ab6c-6895bc9fbc72', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001819', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.440764', '2026-03-14T08:45:16.440764', NULL, NULL, NULL, NULL),
      ('39ae4e4a-d66a-48a0-a67a-e39b68049964', '00000000-0000-0000-0000-000000004011', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('39bb5090-2401-4f6c-8ad3-eb91aa9d96bf', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001702', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.351665', '2026-03-14T08:45:15.351665', NULL, NULL, NULL, NULL),
      ('3a0c0c77-4db7-4365-8b91-4eacca1c3945', '00000000-0000-0000-0000-000000000601', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('3a8fc603-16fc-43ed-ad36-b716c6d0ede4', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T05:39:05.819391', '2026-03-23T05:39:05.819391', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('3b0196e9-2ac2-4bd5-98fa-7c4453e51995', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001703', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.40121', '2026-03-14T08:45:15.40121', NULL, NULL, NULL, NULL),
      ('3b8c7d68-0d9e-4771-8832-02efc5c8055a', 'e74bdcc5-4baf-47b2-9ab4-5bf00455c2b1', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('3c3b2640-80e5-4f69-90ab-8e22e1182cb3', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001811', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.040519', '2026-03-14T08:45:16.040519', NULL, NULL, NULL, NULL),
      ('3cc7ca55-0370-4a36-8ab5-60f5fbdfe094', '9441cc00-943f-4469-aef5-7fae7171b2b9', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('3ce3b0fc-4bb5-4797-8f36-a7e2da974828', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000003062', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('3dc8f1aa-f245-4d2a-8717-1b70c20979a9', '00000000-0000-0000-0000-000000003101', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('3e77cb40-6482-4cce-ab10-d886817b75e8', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000507', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('3e86ad2a-edb8-4b94-8975-0215f66111b4', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'dc8b435a-6aea-432e-8504-191a78bf53dc', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.832262', '2026-03-14T08:45:17.832262', NULL, NULL, NULL, NULL),
      ('3ecff9a6-f9d8-4670-b3ed-ca81d4cddbdf', '00000000-0000-0000-0000-000000000601', 'ee241772-1028-47fe-813c-04377db03e20', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('3fa7db33-9fc1-49c8-bf2d-18c648cb9711', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('3fe850de-8441-41f2-ad8f-aaa5962a6f32', '00000000-0000-0000-0000-000000000601', '4db67994-51ad-4dde-93b1-3abd1842da4d', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('401a4a84-547c-4d1b-ad38-43fe483ac89b', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000506', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.661671', '2026-03-14T08:45:14.661671', NULL, NULL, NULL, NULL),
      ('4043f0d5-9d5f-486f-bc80-a28a48a71ffa', '00000000-0000-0000-0000-000000000601', '10c9c4e1-dc73-4ddd-a86d-944875232bda', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:18:16.315393', '2026-03-17T11:18:16.315393', NULL, NULL, NULL, NULL),
      ('4074fb77-18ea-43dd-ac57-a93c79700d83', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T05:38:22.747132', '2026-03-23T05:38:22.747132', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('410c8696-7323-4d87-b743-9b0b4b05f815', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003051', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('417ee135-cd89-4df3-be2a-9d8c42f988d5', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('42f66290-c2c7-4b62-b191-043fa3a71ec4', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000003062', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('434b72a5-a453-4bf6-b94f-31914a5e5df7', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'ea89e772-4707-4117-9306-bd047278cb2c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.62828', '2026-03-14T08:45:17.62828', NULL, NULL, NULL, NULL),
      ('43f5b004-719f-4f36-8ee3-d8cb46c5be83', '9441cc00-943f-4469-aef5-7fae7171b2b9', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('446fd7ae-f7ff-4fa1-9564-65093318bbe8', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'a722cf91-835e-4616-8caf-f56a8451d70e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('448dcb6c-fb96-4d13-a5a6-d851c8d56279', '00000000-0000-0000-0000-000000000601', '3d7daef7-175b-4aba-959c-e22517a883e8', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('44a98042-49df-4e78-b216-a2575d8d53d6', '00000000-0000-0000-0000-000000004012', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('455b02b9-e5a0-42f5-99ef-20b770bb8f6e', '00000000-0000-0000-0000-000000003102', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('45d8a95c-02b6-4e49-9ca5-7c7cd2830bc0', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006021', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('45f8b1b2-6fa7-4640-9089-e586977fc0e3', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001715', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('471f8da8-18b5-4803-81b1-6897aeaae39d', '197ae046-a989-418f-99df-ec17310d73a4', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:41.75624', '2026-03-18T12:03:41.75624', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4746637f-beba-4470-8174-c80c2158aa93', '00000000-0000-0000-0000-000000004012', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('47b1e919-d214-47ae-b0d6-1e0cc2369c22', '00000000-0000-0000-0000-000000003102', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('47e2e008-9e97-4d51-b162-0b533c17fcd2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006023', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('4880e97f-6d43-4255-9d28-1457224be800', '00000000-0000-0000-0000-000000000601', '08e2ccca-5d32-49e0-b4e5-062fb0177f81', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('493b2817-34e1-4830-93a4-37be33f326a7', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001712', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.600161', '2026-03-14T08:45:15.600161', NULL, NULL, NULL, NULL),
      ('49c7e3cc-8aa9-47e9-b68e-250133ad540c', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '03728caf-974b-4a70-941b-ddae4a319f4d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.478904', '2026-03-14T08:45:17.478904', NULL, NULL, NULL, NULL),
      ('4bd32503-9d33-4c0e-a7c0-0412e532a288', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('4bd410c3-2721-4f04-a68e-83ad808f834e', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.55129', '2026-03-14T08:45:15.55129', NULL, NULL, NULL, NULL),
      ('4ccc5cae-1b8e-4b8c-aa1d-b9594973b777', '00000000-0000-0000-0000-000000003100', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('4d833fd8-16c6-4995-ae35-09f9efda82b7', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001815', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('4f054b5a-5b69-4bea-b89b-483e866aa52a', '00000000-0000-0000-0000-000000003100', '03dba1fa-5bdf-45a6-aa0a-aa6117fe6285', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T09:56:03.353694', '2026-03-17T09:56:03.353694', NULL, NULL, NULL, NULL),
      ('4f42f696-7216-43b8-94d5-461400a7ff2b', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000005020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.878099', '2026-03-16T11:40:41.878099', NULL, NULL, NULL, NULL),
      ('4f6909d5-1a60-4553-8dc4-9547daa394d3', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000006024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.028253', '2026-03-16T11:39:11.028253', NULL, NULL, NULL, NULL),
      ('51c1d745-9834-426e-a34e-025cd911abd1', '00000000-0000-0000-0000-000000003100', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('52503a83-0635-4421-874f-9e26df0aa8ae', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000006021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.057218', '2026-03-16T11:39:11.057218', NULL, NULL, NULL, NULL),
      ('52ae626b-eec0-4807-ba1f-862037d9d436', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050b', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('53a0dd58-fc07-4377-bde4-481a74979556', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('544c7ec9-df7a-485c-b87f-58023cfe633d', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('54522269-b5e6-4e8b-be1e-1a1e94745265', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000512', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.251668', '2026-03-14T08:45:15.251668', NULL, NULL, NULL, NULL),
      ('54cf57a7-a747-4686-bbc8-85bf0c6af911', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001704', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.452905', '2026-03-14T08:45:15.452905', NULL, NULL, NULL, NULL),
      ('54f0109a-99da-4740-b3b4-9492dc9c38e9', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003043', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('550c7bb1-75ea-4192-823e-925d5da337f8', '00000000-0000-0000-0000-000000003102', '6732df5a-2522-4447-bd3f-5c33ebd61696', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('57b4706e-2542-4ed0-8048-698844bfbe0b', '00000000-0000-0000-0000-000000004012', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.036277', '2026-03-17T06:38:33.036277', NULL, NULL, NULL, NULL),
      ('57edc87f-d7eb-4bc9-9eda-01cb03168e35', 'ddf8bcb6-6d66-472c-9b29-4c1c0e3a9d3f', '00000000-0000-0000-0000-000000000512', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-16T12:34:41.608231', '2026-03-16T12:34:46.486669', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-16T12:34:46.486669', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('58126db8-14e0-48ef-9113-2d107394e256', '513b472b-5ae1-45b8-91e3-a1402960b8eb', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-13T17:56:25.542936', '2026-03-13T17:56:27.022539', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', '2026-03-13T17:56:27.022539', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b'),
      ('58567ad6-d3d4-4b93-acb6-78198e41c5a8', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000006023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.028253', '2026-03-16T11:39:11.028253', NULL, NULL, NULL, NULL),
      ('58968dc4-5797-451a-970b-69a1eb64e95c', '00000000-0000-0000-0000-000000004013', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.06368', '2026-03-17T06:38:33.06368', NULL, NULL, NULL, NULL),
      ('590771dd-379c-401a-9efb-a0e4a8b094ad', '00000000-0000-0000-0000-000000000601', 'f70226ef-a1da-4e9c-8115-2388b7436e9a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T13:47:14.553559', '2026-03-18T13:47:14.553559', NULL, NULL, NULL, NULL),
      ('5951aa67-9e66-42d8-a425-c1bd5c350f21', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000005021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.878099', '2026-03-16T11:40:41.878099', NULL, NULL, NULL, NULL),
      ('5a4c298f-4317-4926-a37c-c02f2baaa4ab', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'a14daddc-fb26-4f71-9e4c-fb60dc2a8c9a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('5becdcdd-7705-408a-b0aa-4dbdbd47ecf1', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001814', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.187654', '2026-03-14T08:45:16.187654', NULL, NULL, NULL, NULL),
      ('5c5e72c8-c461-4edd-80b7-f350cb7bd0c8', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003012', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('5f68ec10-1bff-40ab-8445-1270a0a06d45', '00000000-0000-0000-0000-000000003102', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('5fea0d25-a8e5-425b-a5aa-cf197229a9b2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000543', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('60f557f2-b0d0-46cc-b07f-a18cd364d4ed', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6197273f-f226-4a71-9183-50d641f09dae', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000005025', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.878099', '2026-03-16T11:40:41.878099', NULL, NULL, NULL, NULL),
      ('619e3e02-9679-4fad-910f-22abd0f47fa2', '00000000-0000-0000-0000-000000000601', '11582d29-77d4-49ed-b8a4-ef7a1c3c540f', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('62c3a05d-cb7e-4176-bf61-650447b385e0', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'e6be427a-3f30-4fee-af22-cf8cc215da4e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.985261', '2026-03-14T08:45:16.985261', NULL, NULL, NULL, NULL),
      ('63b292d7-354a-4ac6-9958-24e0458aa5e5', '00000000-0000-0000-0000-000000000601', '01dfab3e-59e2-4e79-b514-d57b4de19c65', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('63cb5a8f-c13a-408c-be32-3f0f06be9de5', '28f90230-5525-4cb4-82f1-27895b159b06', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-25T09:15:50.178124', '2026-03-25T09:15:58.045737', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', '2026-03-25T09:15:58.045737', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('64680b2e-c73e-4290-8973-ed3a2e41f7cd', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000421', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-15T07:01:10.571982', '2026-03-15T07:01:10.571982', NULL, NULL, NULL, NULL),
      ('65458be8-55c2-4df0-9f31-88cb738654d8', '00000000-0000-0000-0000-000000000601', '97bf4a0a-7afd-47cb-bc1f-974c8d7cb3d6', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-24T11:16:10.615645', '2026-03-24T11:16:10.615645', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6579498a-6d0c-4616-9108-ab2527cd19ce', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('657a048d-76f1-4985-8342-bbc84fd4d15f', '197ae046-a989-418f-99df-ec17310d73a4', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:37.975858', '2026-03-18T12:03:37.975858', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('672d0377-a35d-4629-a885-52ad68347b2e', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000552', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('675cfabe-4dde-4bb8-a9c9-5a43b5074e57', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('67842159-59c5-40f4-9d39-2d9bc86eeeec', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.796016', '2026-03-14T08:45:15.796016', NULL, NULL, NULL, NULL),
      ('67ccaf20-7063-4a8f-9825-28b93a84e2bc', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('67f67bd2-0526-4ac6-87da-119835fabb46', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001702', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('68d2f5ab-d0a9-4f5e-a8ac-7aa70cbc6e2f', '00000000-0000-0000-0000-000000003100', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('696276da-8119-4c2e-b9c1-194d850a48fb', '9441cc00-943f-4469-aef5-7fae7171b2b9', '03dba1fa-5bdf-45a6-aa0a-aa6117fe6285', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:16:43.585605', '2026-03-17T11:16:43.585605', NULL, NULL, NULL, NULL),
      ('69667c37-19f2-42cc-b033-eb011e75c4ab', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000521', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('69c42984-a96a-4bb0-8f62-00b8462b7c95', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000545', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('69f058d6-432d-4871-921e-bde56774f2b1', '00000000-0000-0000-0000-000000000601', '13fd0ba4-d66e-4223-8f0e-76b0ec002d39', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('6a0b4b30-4440-49f8-acee-217765b2fa9f', '00000000-0000-0000-0000-000000003100', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('6b775498-8698-4d7e-bf90-627e5b335a77', '00000000-0000-0000-0000-000000000601', 'a14daddc-fb26-4f71-9e4c-fb60dc2a8c9a', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6c262983-ead5-4ae8-b838-934cc03fcf14', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('6cb4f709-6374-4ae8-b4dd-c42182ee0ccc', '00000000-0000-0000-0000-000000000601', '619affe6-e90d-4fac-a1bc-c6364653041a', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-24T11:24:24.306498', '2026-03-24T11:24:24.306498', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6cc02eaf-6604-4b5a-a532-be43ade3a20c', 'e74bdcc5-4baf-47b2-9ab4-5bf00455c2b1', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('6cfb19f5-4027-42ac-b2ae-aa63198b29be', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('6dcfc708-dd8d-42de-bcc2-e5df787c96db', '00000000-0000-0000-0000-000000003101', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('6dfa01b7-8d76-4607-a046-ab1effb648f2', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000003011', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-23T05:38:24.354442', '2026-03-23T05:38:25.067781', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-23T05:38:25.067781', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('6e8981f9-dd4b-4f67-9bd7-848d155f7b3d', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('6ebaaccb-30aa-479e-b9fa-c443ef404e3e', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006022', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6ec10388-d26b-4c0d-a1fd-e6cd6cc438f2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6f15dabb-db2f-465e-8f66-7740931c20a5', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000007022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.894706', '2026-03-22T15:08:53.894706', NULL, NULL, NULL, NULL),
      ('6f2bbec6-b391-4229-afb2-9152fb2cf8c9', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000502', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.454011', '2026-03-14T08:45:14.454011', NULL, NULL, NULL, NULL),
      ('6f339861-9de2-443c-b011-eca088c1f9f5', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001819', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('6ff668e1-c861-4603-af65-5425e0bd20b2', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001703', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('71b5b0a9-3e92-4358-9484-55e64acaac48', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000005022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.878099', '2026-03-16T11:40:41.878099', NULL, NULL, NULL, NULL),
      ('71e80bd6-59b1-4114-ac1d-ccb96a538576', '9a2f8bd7-f635-4cfe-9bad-8f640f50fe74', '18e15e8f-21d4-4206-aac9-a7d116129277', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:02:32.063695', '2026-03-18T12:02:32.063695', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', NULL, NULL),
      ('725c0583-71d7-4b51-a1ab-dd59ac17be5f', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003023', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('73afb666-4dff-4438-b4e4-4ff17756f67d', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('73e4d186-bc65-4f03-a71e-0e4780eea316', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003062', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('74b06dbc-9899-43ce-bc2b-d3f8ab322f38', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('74eb969e-5445-45a7-8453-b44f388d4879', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000544', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('754f5537-f67b-4196-9b9e-1355ca534c54', '61ac48fb-f2f7-4a6e-b699-1cd26e94dfac', '00000000-0000-0000-0000-000000003010', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-23T16:06:14.557363', '2026-03-23T16:06:19.244999', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-23T16:06:19.244999', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('76882253-5961-41b6-8bf6-1db8f7eefa23', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003012', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('76dbdfb1-fd03-41c8-8f07-7a8a90c2a581', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.892223', '2026-03-14T08:45:15.892223', NULL, NULL, NULL, NULL),
      ('7791f6b2-13a6-4c0d-9dc0-644a0498575f', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000521', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.282463', '2026-03-14T08:45:17.282463', NULL, NULL, NULL, NULL),
      ('779bec7e-04cd-4d3e-91a4-c928046dc946', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000006024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.057218', '2026-03-16T11:39:11.057218', NULL, NULL, NULL, NULL),
      ('77f52b7b-6768-4773-a226-2c40bcfa6e54', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003053', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7815397e-018d-4642-b5be-88858bf80b97', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000503', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('78cb0e57-8e52-4c79-976f-584a45325225', 'dcd71f42-16f3-4147-8023-fc576792e704', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-20T06:30:56.117893', '2026-03-20T06:30:58.982657', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', '2026-03-20T06:30:58.982657', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('79720277-b3ef-4057-b561-4ccd9567ed37', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000505', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.610297', '2026-03-14T08:45:14.610297', NULL, NULL, NULL, NULL),
      ('79b0c4a7-237f-4b47-be2f-4e6a43ab9a6e', '00000000-0000-0000-0000-000000003101', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('79cf7614-ea4c-4e4a-903b-598680d3f4e3', '9441cc00-943f-4469-aef5-7fae7171b2b9', '55963948-87ca-47e7-9de7-ddd7f3dc675f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:16:43.585605', '2026-03-17T11:16:43.585605', NULL, NULL, NULL, NULL),
      ('7a491ede-b5f0-44aa-9b6c-88a1501df3f6', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005022', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7a6d3ecf-2773-4417-a9a4-7f5830b89524', '00000000-0000-0000-0000-000000000601', '82ea4262-c4f8-4ccb-aa94-466fc3fde999', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('7adebe3a-2493-400c-aea6-fa61a2661196', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000507', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('7af2f43a-b8d6-4343-8156-290d1e08bc90', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('7be0cbc5-07d9-43ba-a7c5-a3b148042e22', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005023', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7c490bf5-bf7f-4797-b387-56adb28d68ec', '00000000-0000-0000-0000-000000003101', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('7c69cfa0-e375-4161-93dc-decfc96ca1d8', '0c45ac3c-8b8b-47f0-b8f6-27f0326c02f2', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('7d629857-92b0-4441-a042-de1924257648', '00000000-0000-0000-0000-000000002001', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('7dc55cf7-da6b-40e7-a9d0-fafeeb19223d', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000508', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('7e17c3cb-ac38-415e-8900-2ddf66a69123', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003072', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-17T12:39:05.58981', '2026-03-17T12:39:06.919062', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-17T12:39:06.919062', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('7e4a8ac1-ee71-44e8-9736-ecd15f50c828', '197ae046-a989-418f-99df-ec17310d73a4', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:43.336014', '2026-03-18T12:03:43.336014', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('7ea8e4db-10df-47b7-aba7-0c854e27fa4f', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7eb359a2-f82d-4b0e-9f42-e1ed262e9a89', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003041', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7f2a22bf-ea6b-4811-8085-028b357fa4dd', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('7f50cf8d-4f25-479e-b8b1-0c881cf6fa7f', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('7f715e80-fe78-4f17-bb32-41bea711dadd', '61ac48fb-f2f7-4a6e-b699-1cd26e94dfac', '00000000-0000-0000-0000-000000003012', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-24T04:52:09.178881', '2026-03-24T04:58:56.691818', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-24T04:58:56.691818', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('81b2ac6a-c72b-4bf4-a071-d7e4a22acd3f', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000505', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('822a3165-c104-4403-84de-2ef3dfac31ee', '00000000-0000-0000-0000-000000003102', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('8374fdf1-e171-4ec2-9c93-5c556150928b', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('83e9a2d2-2850-420f-aaea-1497c06ec1f4', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('84126d53-bbd7-4a1b-9fae-61a5feb9b92b', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000003065', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('8414d99a-6da5-4245-8a71-e612dc15b0bc', '00000000-0000-0000-0000-000000000601', 'a59a9d62-3e75-47ae-b485-11b0d6c8669e', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('842fb835-6675-4e02-93a4-20c3fe3606ed', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('8563bf1f-1600-4258-8f30-c2e432ba0569', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000506', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('863639f8-9d7b-497b-a270-e8b84c05dfba', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('865aac2e-accd-4c3b-9092-c215af45b165', '00000000-0000-0000-0000-000000003101', '6732df5a-2522-4447-bd3f-5c33ebd61696', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('8688bd72-31a1-4d1d-8624-63fe96373154', '9a2f8bd7-f635-4cfe-9bad-8f640f50fe74', '00000000-0000-0000-0000-000000000508', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:02:28.684511', '2026-03-18T12:02:28.684511', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', NULL, NULL),
      ('86f6829c-aaf6-4453-846e-22a7198f1531', '00000000-0000-0000-0000-000000004001', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('872ea3c8-720e-4096-bfed-26f0c00f1c43', '00000000-0000-0000-0000-000000000601', '03728caf-974b-4a70-941b-ddae4a319f4d', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('87aae545-7bfd-4f96-8c5c-5a429ebbd2ec', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000504', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('87e83734-f531-476a-982b-dc95925375a5', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('8819bc8c-7722-4ec7-85e9-1cff695de852', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '0abe68aa-b4ac-4335-8189-24ab0cb4e460', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.378744', '2026-03-14T08:45:17.378744', NULL, NULL, NULL, NULL),
      ('8946554c-4374-4e63-a1f5-4f19fd8f1ee8', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001818', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('8a0b6f43-b0f1-49a9-97ed-28985e24d933', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003043', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('8e8a24b4-6afa-4627-b16b-e581cc526dc8', 'd7699d1f-1674-4fa1-99cc-0b1fe04d5c7c', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-23T06:26:08.85279', '2026-03-23T06:26:11.406404', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', '2026-03-23T06:26:11.406404', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('8e8a5151-345c-4960-937c-a8a9eccf3eef', '00000000-0000-0000-0000-000000003100', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('8f029e1b-5e17-44de-9092-8345ed83ec70', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000503', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('8f19c700-7dcb-4c48-b667-3359833b3a7d', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('8f487648-3672-447e-b8b4-d638c7844d19', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'ebbeba6f-b172-4038-a2a3-384060a1ec43', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.54175', '2026-03-14T08:45:16.54175', NULL, NULL, NULL, NULL),
      ('8f48ab68-fea8-4ce7-92ca-a42043480c2d', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '18e15e8f-21d4-4206-aac9-a7d116129277', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.639546', '2026-03-14T08:45:16.639546', NULL, NULL, NULL, NULL),
      ('908ec89d-b790-447b-853a-64f6b745ed06', '00000000-0000-0000-0000-000000004012', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('90ccc5e9-3544-4e95-ad00-fc9a463d7f2a', '61ac48fb-f2f7-4a6e-b699-1cd26e94dfac', '00000000-0000-0000-0000-000000003011', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T16:06:16.746509', '2026-03-24T04:52:07.011257', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('9129ef11-382d-4d94-9093-43e6b506f632', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '91dd81b2-8d4a-41ac-94a5-1106d459a0be', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.780541', '2026-03-14T08:45:17.780541', NULL, NULL, NULL, NULL),
      ('91588361-7ef4-44f4-b808-a339b58ff1a8', '9441cc00-943f-4469-aef5-7fae7171b2b9', '4db67994-51ad-4dde-93b1-3abd1842da4d', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('928eb843-b4c0-470e-a12a-74736de4142b', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000501', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('9379a6e4-02d9-42d6-8ec8-79b364cbe311', '00000000-0000-0000-0000-000000002001', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('93cb6780-2f71-4982-ab20-321653786e19', '00000000-0000-0000-0000-000000000601', '73f7950d-7163-4467-837d-b6907dd0abcf', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('93d980c0-f96a-4545-83b1-f1fc9c457fb4', '9441cc00-943f-4469-aef5-7fae7171b2b9', '10c9c4e1-dc73-4ddd-a86d-944875232bda', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:16:43.585605', '2026-03-17T11:16:43.585605', NULL, NULL, NULL, NULL),
      ('943570ee-bb22-48e8-8e8a-8b69fb45cf58', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001816', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.291281', '2026-03-14T08:45:16.291281', NULL, NULL, NULL, NULL),
      ('943915e6-accd-4234-a677-2103ad1be01c', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000007021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:17:34.637994', '2026-03-22T15:17:34.637994', NULL, NULL, NULL, NULL),
      ('95303513-713e-4212-adfa-b8f6634f3b11', '9441cc00-943f-4469-aef5-7fae7171b2b9', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('959e4541-f8c0-40fd-b1dc-8f5efe302aea', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('961dd377-496a-4134-bfe0-e91b3d0b0d8c', '00000000-0000-0000-0000-000000000601', '91dd81b2-8d4a-41ac-94a5-1106d459a0be', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('9648e2cf-d9c2-4f4f-82ac-9e76e43fd9db', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003062', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('964e543e-d174-407b-9c51-2bf6a1de0957', '0c45ac3c-8b8b-47f0-b8f6-27f0326c02f2', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('96a17d26-4226-414a-827a-1c0dec81f94a', 'e6a1534a-6e9e-49e8-8452-73daf270db13', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-16T10:42:09.281079', '2026-03-16T10:42:11.897059', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', '2026-03-16T10:42:11.897059', '819f347c-e619-4a43-8755-2c80e5fa572e'),
      ('96c9b108-d195-4357-95a5-d4761efe5d54', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('96cf9638-9e68-403f-bb6d-56c0f52b1038', '00000000-0000-0000-0000-000000003102', '20dfe0b5-3990-4bb4-bc02-6f93b8673e36', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('97c2c646-6da9-4a87-8eaa-5b4308193cb5', '00000000-0000-0000-0000-000000004001', 'a722cf91-835e-4616-8caf-f56a8451d70e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('981647d0-9970-4236-98a7-d3f73a326b6b', '0c45ac3c-8b8b-47f0-b8f6-27f0326c02f2', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('98deb589-4a33-428a-befc-978341c8d8d2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('98f488bb-a6e3-4587-a46f-790f29502019', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003032', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('990edc8a-8796-4b46-aee3-98955809fc4a', '00000000-0000-0000-0000-000000000601', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('99371dd1-1b81-432c-bb1f-3af71452fff6', '00000000-0000-0000-0000-000000003102', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('9a64c1a9-9420-4eb9-9c3f-053932364415', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('9acce471-5023-48df-8450-b59be4556d4d', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('9b08e8c1-29f0-4877-a0a0-0fe87ec576c2', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000006020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.028253', '2026-03-16T11:39:11.028253', NULL, NULL, NULL, NULL),
      ('9b4b939a-f2d9-40e3-b053-0cfbf866dc22', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('9bafc7a3-55fb-42fb-b849-7ab0126511eb', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000513', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.032648', '2026-03-14T08:45:17.032648', NULL, NULL, NULL, NULL),
      ('9d2803e7-48c8-4f10-be0c-98b1020b65d9', '00000000-0000-0000-0000-000000004001', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('9d9ceed6-785d-4934-ade4-6489f520105c', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003053', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('9f4653da-4ff9-42ff-b614-0c5d47977d56', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001705', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('9f7f75b9-c075-414d-bdbd-1a34dcc5d3a4', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000006022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.057218', '2026-03-16T11:39:11.057218', NULL, NULL, NULL, NULL),
      ('a0063d32-6aba-4ede-b1d6-c33e357c10c0', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('a017c17f-0d5d-4df5-a181-c8e6cfdd506b', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000007022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.928461', '2026-03-22T15:08:53.928461', NULL, NULL, NULL, NULL),
      ('a0748be9-5baa-4bd5-bbbf-ac4bd2dabeec', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000502', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('a0f4ad05-ae03-4f4e-b01f-a9aabc91b547', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'ee241772-1028-47fe-813c-04377db03e20', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.78465', '2026-03-14T08:45:16.78465', NULL, NULL, NULL, NULL),
      ('a1533a21-6a33-4264-8af7-5a6d7171e209', '9196f27b-03f9-4cd8-b848-72f0390b16d1', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-13T17:36:39.901092', '2026-03-13T17:36:41.079509', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', '2026-03-13T17:36:41.079509', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b'),
      ('a1939e9a-cb0f-4b29-9a24-1d423f37877b', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000506', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('a415255d-6d28-432e-9975-3cabc24177fd', '00000000-0000-0000-0000-000000003102', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('a449e96c-74e2-4045-b295-a2aac3a34d99', '00000000-0000-0000-0000-000000000601', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('a4bd82c1-000c-4162-8d43-6495f75ce91d', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001713', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('a5f5f544-2deb-4831-a623-ac376373c6fc', '00000000-0000-0000-0000-000000000601', '0abe68aa-b4ac-4335-8189-24ab0cb4e460', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('a6ab0a61-b31b-40cf-a7ed-1f4c2bf146cf', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001816', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('a73f61c2-53ab-4000-b5f5-87f23a97c969', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('a774bd93-3cdf-4b9f-893a-eb09fddfc36b', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '13fd0ba4-d66e-4223-8f0e-76b0ec002d39', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.430391', '2026-03-14T08:45:17.430391', NULL, NULL, NULL, NULL),
      ('a796ab17-ed23-43eb-a2e2-ea1fc1be55dc', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003022', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('a85a6aaf-8509-4e0a-8b80-b134bf6b1ab3', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000520', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('a8c57297-365f-43f3-9613-a0abbc2f10d0', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000422', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-15T07:01:10.571982', '2026-03-15T07:01:10.571982', NULL, NULL, NULL, NULL),
      ('a8f9c744-e1c8-4a46-9f7a-3f07c96fe623', '9441cc00-943f-4469-aef5-7fae7171b2b9', '6732df5a-2522-4447-bd3f-5c33ebd61696', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('a9a29198-1159-4b55-9227-123be8c4ca97', '00000000-0000-0000-0000-000000003100', '55963948-87ca-47e7-9de7-ddd7f3dc675f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T09:56:03.353694', '2026-03-17T09:56:03.353694', NULL, NULL, NULL, NULL),
      ('aaf4bc82-3244-4549-80c4-19665d97c615', '5b0e072b-7367-40cf-bc51-fac851892eb6', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-25T02:29:23.739734', '2026-03-25T02:29:27.155581', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', '2026-03-25T02:29:27.155581', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('ab86dc8d-4314-424e-a6cd-f835b252c635', '00000000-0000-0000-0000-000000003100', '10c9c4e1-dc73-4ddd-a86d-944875232bda', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T09:56:03.353694', '2026-03-17T09:56:03.353694', NULL, NULL, NULL, NULL),
      ('abd8bfc2-df26-4673-bb64-ac73aebde638', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003052', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('ac425bff-ed13-4d71-a222-894d30cbf63f', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('acb03b9c-ae4e-41e1-b382-a8a0680d467e', '9441cc00-943f-4469-aef5-7fae7171b2b9', '4de88a99-cf77-4391-b8c5-97d3dcb9d7f6', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T14:23:40.475695', '2026-03-18T14:23:40.475695', NULL, NULL, NULL, NULL),
      ('adb05571-982d-4c95-8d18-232a6851c118', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('ae554d6d-4953-46f5-98bd-cf940a30459f', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000181a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('aeeb9ea6-c71f-4ccb-88e6-417aae0d7f76', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('afe10be2-ae2f-424b-931e-a14719d42168', '00000000-0000-0000-0000-000000000601', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b1337512-22d3-4d6d-af3a-6d9f865f8cb6', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003021', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b166b57f-5aff-43aa-864e-b5539ad4594a', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '01dfab3e-59e2-4e79-b514-d57b4de19c65', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.330141', '2026-03-14T08:45:17.330141', NULL, NULL, NULL, NULL),
      ('b24c0383-400a-4a89-843a-3bddbee4e9e0', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000507', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.710907', '2026-03-14T08:45:14.710907', NULL, NULL, NULL, NULL),
      ('b28e2aee-57ff-4fa1-bc01-c4d7e8a59a42', '00000000-0000-0000-0000-000000003101', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('b290b113-6fd7-4d87-b5d5-647c84a96df4', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000007021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.894706', '2026-03-22T15:08:53.894706', NULL, NULL, NULL, NULL),
      ('b291349a-db22-4b7d-b2b0-d857171aa214', '00000000-0000-0000-0000-000000003100', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('b2987d0b-a3a9-47f7-a020-ac3d46043f5b', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000005024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.903779', '2026-03-16T11:40:41.903779', NULL, NULL, NULL, NULL),
      ('b32a7c29-cae3-4ea8-bf59-925ac296af4b', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '3d7daef7-175b-4aba-959c-e22517a883e8', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.737038', '2026-03-14T08:45:16.737038', NULL, NULL, NULL, NULL),
      ('b3b24228-9a7a-4152-8104-2a8964441af7', '00000000-0000-0000-0000-000000000601', '18e15e8f-21d4-4206-aac9-a7d116129277', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b3e47361-bb4d-4248-91bf-0e78a6f202dc', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('b46bd9f2-c7d4-4486-b3cf-cc133754b433', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000501', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.377651', '2026-03-14T08:45:14.377651', NULL, NULL, NULL, NULL),
      ('b4cf536c-75f6-450e-a604-e74d2c7ab01e', '00000000-0000-0000-0000-000000004011', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('b5129834-da24-445e-aeda-db4075718270', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001713', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.648406', '2026-03-14T08:45:15.648406', NULL, NULL, NULL, NULL),
      ('b535503b-5c1f-4c75-94f1-d4e5dcfe9865', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000005020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.927136', '2026-03-16T11:40:41.927136', NULL, NULL, NULL, NULL),
      ('b5819905-62b4-4d5a-b0ae-bac386910f4f', '00000000-0000-0000-0000-000000000601', '7f9057c2-d375-4517-98ec-84956a68343b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T13:56:12.151696', '2026-03-16T13:56:12.151696', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('b5ba0474-a90c-4662-b113-0faf551148a9', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000006021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.028253', '2026-03-16T11:39:11.028253', NULL, NULL, NULL, NULL),
      ('b5e19ece-eead-486b-8744-165ea6a51978', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003031', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b66bf781-c7bb-4d89-8e1d-15d01f4dd731', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000553', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('b6f9589e-230f-4fa0-9579-e0700b4761fa', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.688113', '2026-03-14T08:45:16.688113', NULL, NULL, NULL, NULL),
      ('b7168979-5b0e-4de7-9b4a-9e5c16b06760', '00000000-0000-0000-0000-000000003101', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('b76a952d-63fc-49b5-9566-c8263b1fc4c8', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003051', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b79fbbaf-8b83-4945-b5d6-7a80342eb1d9', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('b7b3b6ed-9670-4444-8862-2900f76b7c1c', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('b8648846-3b9f-4575-b179-d1c29cd3933f', '00000000-0000-0000-0000-000000000601', 'b536b3c5-d955-441b-a439-4a57243b049a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:18:16.315393', '2026-03-17T11:18:16.315393', NULL, NULL, NULL, NULL),
      ('b88c4c56-2f65-4cf5-b6c8-85ef45e01f30', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000007022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:17:34.637994', '2026-03-22T15:17:34.637994', NULL, NULL, NULL, NULL),
      ('b8cacab9-db2c-418f-8072-cc785841ec3b', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003064', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('baa39e27-2c01-45be-add4-88bf1e582889', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000554', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('bc26b6fd-71b2-4c88-9b65-cca1a1f1aa4f', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '82ea4262-c4f8-4ccb-aa94-466fc3fde999', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.527659', '2026-03-14T08:45:17.527659', NULL, NULL, NULL, NULL),
      ('bc5e819c-2e1d-4e30-93a8-21e3b376b014', '00000000-0000-0000-0000-000000004001', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('bd38bff6-0169-4641-9eb2-644281574b54', '00000000-0000-0000-0000-000000000601', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('bdb234a3-912c-48c7-8273-0e50e9a9e07d', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001817', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.342898', '2026-03-14T08:45:16.342898', NULL, NULL, NULL, NULL),
      ('bdc36fed-72e9-42a7-9448-02c15f508c7d', '00000000-0000-0000-0000-000000003101', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('be82b21d-26bb-43f9-8fbd-2eb25fe3c5a9', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000504', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.555031', '2026-03-14T08:45:14.555031', NULL, NULL, NULL, NULL),
      ('bf110d86-2586-4bc7-b594-e041d5002e6a', '9a2f8bd7-f635-4cfe-9bad-8f640f50fe74', '3d7daef7-175b-4aba-959c-e22517a883e8', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:02:37.476175', '2026-03-18T12:02:37.476175', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', NULL, NULL),
      ('bfb9527a-2141-4104-b0dc-961f58516e40', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050c', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('bfc1be43-8504-47d9-95f6-a777b5a48d8e', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000520', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.23547', '2026-03-14T08:45:17.23547', NULL, NULL, NULL, NULL),
      ('c114d56d-c647-4a05-9cbb-18badc0e571a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000502', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('c118b9d7-3633-45e1-8d1f-2fbad2129d96', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('c30306ac-a15a-4d45-8b48-cb7e8baf3613', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000181a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.489402', '2026-03-14T08:45:16.489402', NULL, NULL, NULL, NULL),
      ('c32d0f28-64ab-4e22-ab9a-1a2516b84342', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('c43125b5-e96c-4b26-a7fb-4664d0c11026', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001811', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('c4a3b016-9953-4ebb-801d-b6c28f660d68', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003011', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('c51cc84d-94f6-438b-9506-66e170c61e83', '00000000-0000-0000-0000-000000000601', 'c20bad33-1a4a-46fc-9157-9e7ecab76ee4', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-24T11:16:59.147417', '2026-03-24T11:16:59.147417', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('c56881c5-bcb5-425f-9e38-bbe55c20f1a2', '00000000-0000-0000-0000-000000003101', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('c60d0f40-8577-4224-bdb8-9d6453fb0dfc', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'a14daddc-fb26-4f71-9e4c-fb60dc2a8c9a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.884653', '2026-03-14T08:45:16.884653', NULL, NULL, NULL, NULL),
      ('c6beacd8-fd2b-4c97-bdf1-826d8c2ece86', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003031', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('c77dc381-81ba-4550-a472-618273d4c8c1', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('c7e71975-d41c-4fdf-9c2a-b154dea95779', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('c7f73f41-0d50-4a70-91ad-512e347c5638', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '11582d29-77d4-49ed-b8a4-ef7a1c3c540f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.590111', '2026-03-14T08:45:16.590111', NULL, NULL, NULL, NULL),
      ('c90172f7-873d-481d-aaf6-e5e0e8fe4035', '00000000-0000-0000-0000-000000000601', 'ebbeba6f-b172-4038-a2a3-384060a1ec43', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('c9191d1f-920a-4d82-b4f2-0d3cba72532a', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001701', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('c9487ad7-4c9c-419d-adb2-9cc7d57e44b9', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.843525', '2026-03-14T08:45:15.843525', NULL, NULL, NULL, NULL),
      ('cba041ee-bbb8-452f-bf2f-b22eef577adc', '00000000-0000-0000-0000-000000000601', 'dc8b435a-6aea-432e-8504-191a78bf53dc', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('cbfce971-b54b-42d9-a7c0-4635697bc95f', '61ac48fb-f2f7-4a6e-b699-1cd26e94dfac', '00000000-0000-0000-0000-000000003013', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-23T16:06:40.341614', '2026-03-23T16:06:42.843983', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-23T16:06:42.843983', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('cc3f69fb-1de7-443a-b439-c90755e60977', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000007020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.894706', '2026-03-22T15:08:53.894706', NULL, NULL, NULL, NULL),
      ('ccc4cee8-007e-4c02-8ff5-26eef34c606e', '00000000-0000-0000-0000-000000000601', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('cd3886bb-d9d0-4c43-9b8a-640007b3d364', '0c45ac3c-8b8b-47f0-b8f6-27f0326c02f2', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('cd622f5c-ca67-4136-a2bd-47898faa429f', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000544', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.10148', '2026-03-17T07:49:17.10148', NULL, NULL, NULL, NULL),
      ('cdb0c6f0-3928-40a1-9f01-741d0ef3a66a', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000006024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.082914', '2026-03-16T11:39:11.082914', NULL, NULL, NULL, NULL),
      ('ceb375b2-2864-47a0-9392-4a1994821f7c', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('ceff55aa-b071-4ee8-90c7-465d9d8a1ea2', '00000000-0000-0000-0000-000000003102', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('cf7e6dc9-3f0e-49f5-9b94-2ff582c42ab1', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('d072b93e-c42d-4c7d-b96b-4f8371c4ecb8', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001815', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.239166', '2026-03-14T08:45:16.239166', NULL, NULL, NULL, NULL),
      ('d08990d3-43a8-436a-8233-8cd0fd11a84e', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003042', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('d1392412-9e3a-499c-8c28-987238e908a9', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('d24dc813-25b5-4ddf-a473-6a0aef406f75', '00000000-0000-0000-0000-000000004012', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.036277', '2026-03-17T06:38:33.036277', NULL, NULL, NULL, NULL),
      ('d2bd6701-0a7b-4c0b-835d-bd3e9cd94b19', '00000000-0000-0000-0000-000000004013', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('d35a4bde-533b-45bc-90d2-3b1d6d06c327', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003013', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('d3f5dc69-b26c-46fa-ad38-24925a020112', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001715', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.747254', '2026-03-14T08:45:15.747254', NULL, NULL, NULL, NULL),
      ('d430a538-ec00-4b66-a928-5c04dc246a5b', '00000000-0000-0000-0000-000000003101', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('d440116b-7745-4234-aaaf-24c18a2ba1c7', '00000000-0000-0000-0000-000000000601', '418d753c-aa97-4551-abb6-b703d54f8f96', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-24T11:17:26.475614', '2026-03-24T11:17:26.475614', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('d4a6fdd6-400f-459b-bd9f-dbfbb8ec7f2c', '9441cc00-943f-4469-aef5-7fae7171b2b9', '5e57eaaf-2427-467a-8170-b0c605c5c61d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T14:23:40.475695', '2026-03-18T14:23:40.475695', NULL, NULL, NULL, NULL),
      ('d4fe54cf-5dc4-4074-99b1-b8cebaca8168', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000006022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:39:11.028253', '2026-03-16T11:39:11.028253', NULL, NULL, NULL, NULL),
      ('d4ff129a-ae5c-48fe-bc01-a95526af0de9', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000511', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('d574390c-8866-4eef-b358-12fe13ab0336', '9441cc00-943f-4469-aef5-7fae7171b2b9', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('d59683ed-99f1-4d98-b902-71e5a448aa54', '9441cc00-943f-4469-aef5-7fae7171b2b9', '3d7daef7-175b-4aba-959c-e22517a883e8', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('d6bee11e-d6ec-4128-84eb-8bbe0ac44463', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001714', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('d77c1c44-44d4-449c-8b9a-1c683e24de6b', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.003882', '2026-03-14T08:45:15.003882', NULL, NULL, NULL, NULL),
      ('d7ebb30c-47b4-4790-bd8f-fe5900fddfa7', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003063', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('d87a6b59-f872-4a31-b6ca-66c2db54d3bf', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000508', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.759542', '2026-03-14T08:45:14.759542', NULL, NULL, NULL, NULL),
      ('d8bee1d7-49e3-4a5a-8f79-96cae7f5a150', '197ae046-a989-418f-99df-ec17310d73a4', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:39.595515', '2026-03-18T12:03:39.595515', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('d8dc73c9-2494-4c7a-a85a-6479ce996045', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005025', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('d962ac5a-bf51-4d76-ac8f-f12fbff2f881', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('db989ffd-9f52-4c1d-95b3-d2e24b6aede2', '9441cc00-943f-4469-aef5-7fae7171b2b9', '20dfe0b5-3990-4bb4-bc02-6f93b8673e36', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('dbd7ecf2-f9aa-4a72-94f7-514e061b2f6f', '00000000-0000-0000-0000-000000003100', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('dbf1d2ba-4211-4cd3-884a-d8231684b083', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000542', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.10148', '2026-03-17T07:49:17.10148', NULL, NULL, NULL, NULL),
      ('dc82d868-7b35-47c9-9c32-2bf056de1473', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('dd9e81e2-5eaa-48fc-a51e-d8f1f5ee1193', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000005021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.903779', '2026-03-16T11:40:41.903779', NULL, NULL, NULL, NULL),
      ('ddfa45a2-7430-4796-b298-123b811827e5', 'b8cf7f37-cbeb-4adb-9032-2cac106bdbd3', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-13T17:34:58.261925', '2026-03-13T17:34:59.534442', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', '2026-03-13T17:34:59.534442', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b'),
      ('de580e78-c27c-4f7b-bb9b-f3b475f5bc21', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000515', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.131499', '2026-03-14T08:45:17.131499', NULL, NULL, NULL, NULL),
      ('de78f3af-0af4-47ba-aba3-886f31c5b91d', '00000000-0000-0000-0000-000000003100', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('deb701f5-d8d6-49d9-8f8e-e55a2c816e2d', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003072', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('def8cd1d-2b8e-4e9a-838f-b2050aeb8731', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001818', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.391916', '2026-03-14T08:45:16.391916', NULL, NULL, NULL, NULL),
      ('df74d992-4613-49dc-a9bf-c87a572a333b', '00000000-0000-0000-0000-000000003100', 'b536b3c5-d955-441b-a439-4a57243b049a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T09:56:03.353694', '2026-03-17T09:56:03.353694', NULL, NULL, NULL, NULL),
      ('e043d4a4-39d3-453b-a995-abf878981f8d', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000007020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.928461', '2026-03-22T15:08:53.928461', NULL, NULL, NULL, NULL),
      ('e05b83d7-805a-4bde-b266-5a75e017e418', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('e0cf2bf7-9344-4003-a673-50382f62aac3', '00000000-0000-0000-0000-000000003101', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('e120ee9e-f027-4f8c-9528-793ffaa4abe2', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '4db67994-51ad-4dde-93b1-3abd1842da4d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.935441', '2026-03-14T08:45:16.935441', NULL, NULL, NULL, NULL),
      ('e1de4363-8d52-460c-ba3b-6de68bbbe42d', '00000000-0000-0000-0000-000000003101', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('e1e10b8a-a37d-4c78-96f2-5613a94ec25c', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.10098', '2026-03-14T08:45:15.10098', NULL, NULL, NULL, NULL),
      ('e230ef4b-8ad0-4e3e-a7cb-d577056f0c98', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001704', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('e2b02110-b240-40ca-9d3d-0a6b3cf959ac', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001715', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('e2bcc890-994b-4493-a4a3-e003f02b216c', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000551', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.853395', '2026-03-17T08:28:44.853395', NULL, NULL, NULL, NULL),
      ('e36487f8-ce10-4e90-b769-e3afa539c8ae', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001705', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.502543', '2026-03-14T08:45:15.502543', NULL, NULL, NULL, NULL),
      ('e39b7092-a3d6-4080-bae1-dc07e7b8cf90', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001814', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('e4306a9e-4190-4848-ad8e-85f9a802cdfb', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ee241772-1028-47fe-813c-04377db03e20', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('e54fc5c4-dfc9-479e-920a-0e95c78fe31a', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001714', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('e6bb2360-6cb4-4f9f-ad55-26474ebc370a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000551', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('e7201346-f90d-4575-b80b-04fca5ed4161', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000007020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:17:34.637994', '2026-03-22T15:17:34.637994', NULL, NULL, NULL, NULL),
      ('e73ee5b6-3463-437d-a4b9-cacff5fea008', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.955133', '2026-03-14T08:45:14.955133', NULL, NULL, NULL, NULL),
      ('e75da2bb-8578-4f85-9c4a-4cef0db792e9', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('e7f089a3-d908-459c-8214-8ad2d581ca06', '00000000-0000-0000-0000-000000003100', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('e8b72ff0-d264-4c1c-a03b-0c4ce5160035', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ebbeba6f-b172-4038-a2a3-384060a1ec43', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('e9785ad0-95d0-4242-aba1-35997cffa77d', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003063', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('e99873c9-7c8a-428a-a43b-b2282d64b580', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000542', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('ea02927d-568c-41d1-9b71-5bc7aad1f408', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000005024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.927136', '2026-03-16T11:40:41.927136', NULL, NULL, NULL, NULL),
      ('eab7690c-228a-43b7-a57d-27db4e150bf1', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T08:13:24.278873', '2026-03-25T08:13:24.278873', NULL, NULL, NULL, NULL),
      ('eb1559c1-fca2-46f2-b336-c46389763ba4', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001813', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.138522', '2026-03-14T08:45:16.138522', NULL, NULL, NULL, NULL),
      ('eb9dee6a-e097-4f49-a372-3692b52547ee', '00000000-0000-0000-0000-000000004012', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('ebed9e15-12ef-48b2-abf1-69e83d55d7dd', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'a59a9d62-3e75-47ae-b485-11b0d6c8669e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.836248', '2026-03-14T08:45:16.836248', NULL, NULL, NULL, NULL),
      ('ec033307-c5fb-465e-90b5-1603b24e233c', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000541', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.10148', '2026-03-17T07:49:17.10148', NULL, NULL, NULL, NULL),
      ('ec3c7982-64c2-40e5-a953-dcc02dd55db7', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000007023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:17:34.637994', '2026-03-22T15:17:34.637994', NULL, NULL, NULL, NULL),
      ('ec73783e-339d-4348-8299-fcb075cd1f51', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000007023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.894706', '2026-03-22T15:08:53.894706', NULL, NULL, NULL, NULL),
      ('eccb3a4e-7a2c-4184-804d-532ee4d7140e', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('ed5b84c0-d023-47ce-8819-9022272c75af', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('ee24723f-2cb2-4d13-8b99-9fa32d740b0b', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000005023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.878099', '2026-03-16T11:40:41.878099', NULL, NULL, NULL, NULL),
      ('ee414272-abb0-4905-b65f-e461f0eed500', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '08e2ccca-5d32-49e0-b4e5-062fb0177f81', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.882259', '2026-03-14T08:45:17.882259', NULL, NULL, NULL, NULL),
      ('f02aaca5-1bc6-4596-9526-57e6d1438b44', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('f0b8464f-471f-4583-8e5b-567ac7c31719', '00000000-0000-0000-0000-000000004001', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('f1f47b6b-92cb-4e1c-bcb3-7715c1c023c5', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005020', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('f204295a-f913-43e0-9c4d-86cb1887aec4', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.942678', '2026-03-14T08:45:15.942678', NULL, NULL, NULL, NULL),
      ('f39e85fe-d0e3-4470-8287-d0a57c0a5530', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000511', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.201558', '2026-03-14T08:45:15.201558', NULL, NULL, NULL, NULL),
      ('f4869db1-5e62-4b34-9f2b-baaf7faa2f01', '00000000-0000-0000-0000-000000003100', '6732df5a-2522-4447-bd3f-5c33ebd61696', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('f4c11584-280a-4d49-bce0-d2d729e9b146', '00000000-0000-0000-0000-000000003102', '00000000-0000-0000-0000-000000007020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:08:53.961452', '2026-03-22T15:08:53.961452', NULL, NULL, NULL, NULL),
      ('f4c505db-9903-4cde-8a84-2e16fade3302', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ba30a1c3-d974-4d81-8f2d-28bfccb4bf6b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T14:23:40.475695', '2026-03-18T14:23:40.475695', NULL, NULL, NULL, NULL),
      ('f4eed880-b868-45c0-b7e2-8dbb83856cf1', '00000000-0000-0000-0000-000000003102', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('f5363954-b168-4959-979a-ce2ce4d52319', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003033', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('f5b3b922-f4e8-490e-a0b0-ae235cb37e52', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('f6f8e5c9-6b90-4898-8cf6-e3f30e3f1246', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003032', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('f84fc570-0690-4513-9353-9239b7cb22f4', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003064', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('f85fd081-eb7f-48b5-9f78-6a97a8fdb2fc', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001812', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.088398', '2026-03-14T08:45:16.088398', NULL, NULL, NULL, NULL),
      ('f89b2ce3-3d2c-4bc5-9cb7-1d6f92deb46e', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000501', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('f8e82d7b-1534-4665-84d0-245a92abdc41', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000005022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.903779', '2026-03-16T11:40:41.903779', NULL, NULL, NULL, NULL),
      ('f93384f0-45f0-41f4-a23e-fc687d18f557', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('fb7f1584-d7c9-4728-a10a-9f186cca7ca1', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000510', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('fb8ed621-0158-436d-bead-90f4014eff58', '00000000-0000-0000-0000-000000000601', 'e6be427a-3f30-4fee-af22-cf8cc215da4e', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('fb8ff7da-3fcc-4f60-9f54-1d9a1fbcc184', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000510', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.152797', '2026-03-14T08:45:15.152797', NULL, NULL, NULL, NULL),
      ('fc1c6bb0-bfea-4794-b9c5-3c0dd2eb01b9', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:13:43.791271', '2026-03-17T07:13:43.791271', NULL, NULL, NULL, NULL),
      ('fc8354e6-b181-4ef6-85e0-1f62e392f6ea', '00000000-0000-0000-0000-000000003100', '00000000-0000-0000-0000-000000003042', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T18:23:59.488163', '2026-03-15T18:23:59.488163', NULL, NULL, NULL, NULL),
      ('fd2a7f88-2cfd-4ec5-965d-eb0d14b44218', '00000000-0000-0000-0000-000000000601', 'ea89e772-4707-4117-9306-bd047278cb2c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('fd528509-1a39-48ce-9e25-a204a554ee04', '00000000-0000-0000-0000-000000003101', '00000000-0000-0000-0000-000000005020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:40:41.903779', '2026-03-16T11:40:41.903779', NULL, NULL, NULL, NULL),
      ('fd744f4a-8747-417f-b963-1b8b77ca4b11', '61ac48fb-f2f7-4a6e-b699-1cd26e94dfac', 'f70226ef-a1da-4e9c-8115-2388b7436e9a', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-23T16:06:55.243593', '2026-03-23T16:07:17.429682', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-23T16:07:17.429682', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('fdd0f673-21f1-4f3d-8e30-8c645b4749cf', 'e74bdcc5-4baf-47b2-9ab4-5bf00455c2b1', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('fe72f0a8-4180-4575-8d8b-458c38911a59', '00000000-0000-0000-0000-000000004011', 'a722cf91-835e-4616-8caf-f56a8451d70e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('ff8d4ab9-5521-4f61-987e-71d595ca552a', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000503', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.506052', '2026-03-14T08:45:14.506052', NULL, NULL, NULL, NULL)
  ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.50_dim_portal_views (6 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."50_dim_portal_views" (id, code, name, description, color, icon, sort_order, is_active, created_at, default_route, updated_at)
  VALUES
      ('51e85cb2-7bcf-49bf-acd3-edd8ce2fb5b4', 'vendor', 'Vendor', 'Vendor portal — questionnaire, document upload, review status', '#06b6d4', 'Building2', 50, TRUE, '2026-03-16T08:51:00.847272+00:00', '/dashboard', '2026-03-17T05:03:53.976966+00:00'),
      ('6c48838a-5586-45b4-9ea4-a077ee65d5ff', 'auditor', 'External Auditor', 'Read-only compliance view — evidence requests, control testing, findings', '#6366f1', 'Search', 20, TRUE, '2026-03-16T08:51:00.847272+00:00', '/framework_library', '2026-03-17T05:03:53.976966+00:00'),
      ('82063d7a-8c17-4423-9f56-2431b7b2e2b2', 'global', 'Global', 'Unrestricted access — all routes and modules visible', '#ef4444', 'Globe', 1, TRUE, '2026-03-17T09:15:03.010065+00:00', '/dashboards', '2026-03-18T09:11:19.865735+00:00'),
      ('b3971f16-c375-4746-ab63-e513251f2a39', 'engineering', 'Engineering', 'Task-focused view — my tasks, evidence to submit, owned controls, test results', '#10b981', 'Wrench', 30, TRUE, '2026-03-16T08:51:00.847272+00:00', '/dashboard', '2026-03-17T05:03:53.976966+00:00'),
      ('cbb4c715-5331-492a-9075-593e40b99713', 'grc', 'GRC Practitioners', 'Full compliance management — frameworks, controls, risks, tasks, tests', '#2878ff', 'ShieldCheck', 10, TRUE, '2026-03-16T08:51:00.847272+00:00', '/dashboard', '2026-03-18T09:13:29.096388+00:00'),
      ('ecfe55ad-2891-4803-8fbc-b789d070160e', 'executive', 'CISO / Executive', 'Board-level read-only view — security posture, risk summary, framework status', '#f59e0b', 'BarChart3', 40, TRUE, '2026-03-16T08:51:00.847272+00:00', '/dashboard', '2026-03-19T05:33:32.781811+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, color = EXCLUDED.color, icon = EXCLUDED.icon, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, default_route = EXCLUDED.default_route, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.51_lnk_role_views (16 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."51_lnk_role_views" (id, role_id, view_code, created_at, created_by)
  VALUES
      ('00757431-f4b4-46d5-b68a-f91ed5587d08', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'auditor', '2026-03-17T04:46:00.007229+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('08a1bf22-e522-4116-a2f8-9825eef03dbe', '00000000-0000-0000-0000-000000000601', 'grc', '2026-03-16T08:51:00.847272+00:00', NULL),
      ('27843940-e52e-46b2-9a8a-da98292eb8a4', '00000000-0000-0000-0000-000000003100', 'grc', '2026-03-16T08:51:00.847272+00:00', NULL),
      ('2eb9b24a-0296-4e98-b2fd-9002add78375', '00000000-0000-0000-0000-000000002001', 'grc', '2026-03-16T08:51:00.847272+00:00', NULL),
      ('4c2e5b25-7d43-4682-93d3-7fddc81aff66', '00000000-0000-0000-0000-000000000601', 'global', '2026-03-17T09:15:03.063422+00:00', NULL),
      ('624834f4-2eb8-4e7c-8440-937701dcc3cc', '00000000-0000-0000-0000-000000002001', 'executive', '2026-03-17T04:54:20.063682+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('7cb14160-1f15-442b-a377-e05b17abec1f', '00000000-0000-0000-0000-000000003101', 'grc', '2026-03-16T08:51:00.847272+00:00', NULL),
      ('87a126dd-658b-49ce-b5e8-1eb62535b35d', '00000000-0000-0000-0000-000000004001', 'grc', '2026-03-17T07:13:40.298205+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('9ea28663-69d9-411b-ac9a-463d692a6efd', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'grc', '2026-03-17T05:19:41.306496+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('a0a55235-8b24-4e0c-adb6-70aaa72a7658', '00000000-0000-0000-0000-000000002001', 'auditor', '2026-03-16T17:40:09.310793+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('b0f00e4a-5ad5-4693-848a-f208249b6ff2', '00000000-0000-0000-0000-000000003102', 'grc', '2026-03-16T08:51:00.847272+00:00', NULL),
      ('bc6f781c-8d52-41ee-9d3f-31e18554b37b', '00000000-0000-0000-0000-000000002001', 'vendor', '2026-03-16T17:38:37.394219+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('c196d0b5-a1ac-4ef0-8d93-b3999a56f5bb', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'executive', '2026-03-16T17:39:50.105427+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('d1e90267-e3b5-445e-8a9b-4f3eaa9315fe', '00000000-0000-0000-0000-000000000601', 'auditor', '2026-03-16T12:12:03.636022+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('f11204f3-5ca2-4ba7-a555-80721c3a5e94', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'vendor', '2026-03-16T17:38:33.431073+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('f220dad5-addb-471b-8fd4-fb9a315b1c18', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'engineering', '2026-03-17T05:25:30.352749+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223')
  ON CONFLICT (role_id, view_code) DO NOTHING;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.52_dtl_view_routes (34 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."52_dtl_view_routes" (id, view_code, route_prefix, is_read_only, sort_order, sidebar_label, sidebar_icon, sidebar_section)
  VALUES
      ('015dec1d-9f46-4a24-ae99-2243ceb6876a', 'auditor', '/reports', FALSE, 60, 'Reports', NULL, NULL),
      ('056731b4-1163-42ff-8702-30a879ff15bd', 'executive', '/dashboard', TRUE, 10, 'Security Posture', 'LayoutDashboard', 'Board View'),
      ('0fc879ff-6aae-4ba2-a907-e7821e115719', 'auditor', '/audit-workspace/auditor', FALSE, 60, 'Auditor Workspace', NULL, 'Auditor Workspace'),
      ('12e5c2b1-3c5c-47d3-9901-622736d73166', 'grc', '/policies', FALSE, 70, 'Policies & Docs', 'BookOpen', 'GRC Platform'),
      ('2234ba69-5101-429d-aa69-7752b5333c4e', 'grc', '/frameworks', FALSE, 20, 'Frameworks', 'Library', 'GRC Platform'),
      ('289ea024-118f-4caa-a8d5-92aafbf6ea86', 'engineering', '/controls', TRUE, 30, 'Controls', 'ShieldCheck', 'Controls I Own'),
      ('30227b0d-f9fc-415e-9536-d3f873af77af', 'grc', '/framework_library', FALSE, 110, 'framework library', NULL, NULL),
      ('37843367-f0af-4b2b-a88f-9c83ab776986', 'grc', '/monitoring', FALSE, 130, 'Live Monitoring', NULL, NULL),
      ('3ea4cd7e-2560-4270-bdb1-7f7a0a7a449d', 'auditor', '/tasks', FALSE, 50, 'Tasks', NULL, NULL),
      ('43bc3b9a-9d04-487c-a38d-4bb77dddd84b', 'grc', '/dashboard', FALSE, 10, 'Dashboard', 'LayoutDashboard', 'Navigate'),
      ('47ff80b6-f563-42a4-b453-7b8b81a5b9ba', 'global', '/*', FALSE, 0, NULL, NULL, NULL),
      ('4b12c55c-16c0-467d-89c1-79a9c6cfc193', 'grc', '/reports', FALSE, 120, 'reports', NULL, NULL),
      ('4c5196e8-0af7-4296-af6d-fd4ac74af0e2', 'executive', '/risks', TRUE, 20, 'Risk Summary', 'ShieldAlert', 'Board View'),
      ('5b640935-554f-4b55-a6a7-e5ed7df917b6', 'grc', '/assets', FALSE, 140, 'Asset Inventory', NULL, NULL),
      ('6443af6a-9e10-4ecb-a2d9-ebac58f7ce11', 'executive', '/frameworks', TRUE, 30, 'Frameworks', 'Library', 'Board View'),
      ('6e4dff03-7334-4624-982b-06adbe538855', 'grc', '/feedback', FALSE, 80, 'Feedback & Support', 'MessageSquarePlus', 'Administration'),
      ('72edf00c-1a96-439e-a4bb-fbc54f69370f', 'grc', '/issues', FALSE, 150, 'Issues', NULL, NULL),
      ('786196a8-5101-4441-8b73-221cf91a66f8', 'vendor', '/tasks', FALSE, 20, 'Tasks', 'CheckSquare', 'My Assessment'),
      ('828c5a4d-e3f0-41eb-9614-7bbb94ee8f9e', 'engineering', '/tests', TRUE, 40, 'Test Results', 'FlaskConical', 'Controls I Own'),
      ('836132c0-5b67-4c15-a45e-41dd55441f60', 'grc', '/workspaces', FALSE, 70, 'Workspaces', 'Layers', 'Administration'),
      ('90a6516b-f97f-4387-b746-e17f70e02a7f', 'executive', '/policies', TRUE, 30, 'Policies & Docs', 'BookOpen', 'GRC Platform'),
      ('9c86455a-5291-4e5b-ab87-3024f54539ee', 'grc', '/tasks', FALSE, 60, 'Tasks', 'CheckSquare', 'GRC Platform'),
      ('9d3f4a58-3a2b-4dbb-946b-af544d7338e2', 'executive', '/framework_library', FALSE, 50, 'framework library', NULL, NULL),
      ('a40fd46c-f56d-46a2-9ea4-a136f11c646f', 'grc', '/tests', FALSE, 40, 'Control Tests', 'FlaskConical', 'GRC Platform'),
      ('b375dde9-565c-4486-a4c3-66726713215f', 'grc', '/risks', FALSE, 50, 'Risk Registry', 'ShieldAlert', 'GRC Platform'),
      ('b5711382-9409-42ca-95c4-535ff892dacd', 'grc', '/audit-workspace/grc', FALSE, 160, 'Audit Management', NULL, NULL),
      ('b723bbf0-04ae-473e-b8a9-ae64542804df', 'auditor', '/controls', TRUE, 30, 'Controls', 'ShieldCheck', 'Compliance'),
      ('b8071296-c721-4318-846f-f037c0e71f29', 'grc', '/sandbox', FALSE, 90, 'K-Control Sandbox', 'FlaskConical', 'Projects'),
      ('c261840f-a580-4eec-a310-27e234d77040', 'engineering', '/tasks', FALSE, 20, 'Tasks', 'CheckSquare', 'My Work'),
      ('d8bce531-0d37-431a-a494-c84d5786cceb', 'engineering', '/dashboard', FALSE, 10, 'Dashboard', 'LayoutDashboard', 'My Work'),
      ('dd819f10-afb5-4fe5-80ea-6070df888e1c', 'grc', '/controls', FALSE, 30, 'Controls', 'ShieldCheck', 'GRC Platform'),
      ('de4758ef-182c-45c0-9861-3863c49311f6', 'vendor', '/dashboard', FALSE, 10, 'Dashboard', 'LayoutDashboard', 'My Assessment'),
      ('e239cdde-23cf-42ef-9f07-f486f1f1b029', 'auditor', '/frameworks', TRUE, 20, 'Frameworks', 'Library', 'Compliance'),
      ('eea82a47-6136-47b8-a023-89ea90abc678', 'auditor', '/framework_library', FALSE, 60, 'framework lirary', NULL, NULL)
  ON CONFLICT (view_code, route_prefix) DO UPDATE SET is_read_only = EXCLUDED.is_read_only, sort_order = EXCLUDED.sort_order, sidebar_label = EXCLUDED.sidebar_label, sidebar_icon = EXCLUDED.sidebar_icon, sidebar_section = EXCLUDED.sidebar_section;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: NOTIFICATIONS
-- Extracted: 2026-03-27T14:17:09.583193
-- ═════════════════════════════════════════════════════════════════════════════

-- 03_notifications.02_dim_notification_channels (6 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."02_dim_notification_channels" (id, code, name, description, is_available, sort_order, created_at, updated_at)
  VALUES
      ('a0000000-0000-0000-0000-000000000001', 'email', 'Email', 'Email notifications via SMTP or API provider', TRUE, 1, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('a0000000-0000-0000-0000-000000000002', 'web_push', 'Web Push', 'Browser push notifications via Web Push API', TRUE, 2, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('a0000000-0000-0000-0000-000000000003', 'whatsapp', 'WhatsApp', 'WhatsApp messaging notifications', FALSE, 3, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('a0000000-0000-0000-0000-000000000004', 'slack', 'Slack', 'Slack workspace notifications', FALSE, 4, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('a0000000-0000-0000-0000-000000000005', 'gchat', 'Google Chat', 'Google Chat notifications', FALSE, 5, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('a0000000-0000-0000-0000-000000000006', 'webhook', 'Webhook', 'HTTP POST to a user-configured endpoint with HMAC signature', FALSE, 50, '2026-03-20T14:14:27.285555', '2026-03-20T14:14:27.285555')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_available = EXCLUDED.is_available, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.03_dim_notification_categories (8 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."03_dim_notification_categories" (id, code, name, description, is_mandatory, sort_order, created_at, updated_at)
  VALUES
      ('b0000000-0000-0000-0000-000000000001', 'security', 'Security', 'Security-related notifications that cannot be disabled', TRUE, 1, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('b0000000-0000-0000-0000-000000000002', 'transactional', 'Transactional', 'Transaction confirmations and mandatory system responses', TRUE, 2, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('b0000000-0000-0000-0000-000000000003', 'system', 'System', 'Platform-wide system notifications and announcements', FALSE, 3, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('b0000000-0000-0000-0000-000000000004', 'org', 'Organization', 'Organization-related notifications', FALSE, 4, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('b0000000-0000-0000-0000-000000000005', 'workspace', 'Workspace', 'Workspace-related notifications', FALSE, 5, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('b0000000-0000-0000-0000-000000000006', 'engagement', 'Engagement', 'User engagement and activity notifications', FALSE, 6, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('b0000000-0000-0000-0000-000000000007', 'marketing', 'Marketing', 'Promotional content, offers, and newsletters', FALSE, 7, '2026-03-19T14:37:29.9215', '2026-03-19T14:37:29.9215'),
      ('b0000000-0000-0000-0000-000000000008', 'product_updates', 'Product Updates', 'Feature announcements, changelogs, and product news', FALSE, 8, '2026-03-19T14:37:29.9215', '2026-03-19T14:37:29.9215')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_mandatory = EXCLUDED.is_mandatory, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.04_dim_notification_types (21 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."04_dim_notification_types" (id, code, name, description, category_code, is_mandatory, is_user_triggered, default_enabled, cooldown_seconds, sort_order, created_at, updated_at, dispatch_immediately)
  VALUES
      ('14e79e2d-69b1-4add-b083-1f3e5c117649', 'magic_link_login', 'Magic Link Login', 'Passwordless login magic link sent to user', 'security', TRUE, TRUE, TRUE, NULL, 5, '2026-03-20T03:54:34.732431', '2026-03-20T03:54:34.732431', FALSE),
      ('c0000000-0000-0000-0000-000000000001', 'password_reset', 'Password Reset', 'Password reset OTP or link notification', 'security', TRUE, TRUE, TRUE, NULL, 1, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', TRUE),
      ('c0000000-0000-0000-0000-000000000002', 'email_verification', 'Email Verification', 'Email verification code or link', 'security', TRUE, TRUE, TRUE, NULL, 2, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', TRUE),
      ('c0000000-0000-0000-0000-000000000003', 'login_from_new_device', 'Login From New Device', 'Alert when login occurs from unrecognized device or IP', 'security', TRUE, TRUE, TRUE, 3600, 3, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', TRUE),
      ('c0000000-0000-0000-0000-000000000004', 'api_key_created', 'API Key Created', 'Notification when a new API key is created for the account', 'security', TRUE, TRUE, TRUE, NULL, 4, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', TRUE),
      ('c0000000-0000-0000-0000-000000000005', 'password_changed', 'Password Changed', 'Confirmation that password was changed', 'transactional', TRUE, TRUE, TRUE, NULL, 5, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', TRUE),
      ('c0000000-0000-0000-0000-000000000006', 'email_verified', 'Email Verified', 'Confirmation that email was verified', 'transactional', TRUE, TRUE, TRUE, NULL, 6, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', TRUE),
      ('c0000000-0000-0000-0000-000000000007', 'org_invite_received', 'Organization Invite Received', 'Notification when user is invited to an organization', 'org', FALSE, FALSE, TRUE, NULL, 7, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-000000000008', 'org_member_added', 'Organization Member Added', 'Notification when a new member joins the organization', 'org', FALSE, FALSE, TRUE, NULL, 8, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-000000000009', 'org_member_removed', 'Organization Member Removed', 'Notification when a member is removed from the organization', 'org', FALSE, FALSE, TRUE, NULL, 9, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-00000000000a', 'org_broadcast', 'Organization Broadcast', 'Admin broadcast to all organization members', 'org', FALSE, FALSE, TRUE, NULL, 10, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-00000000000b', 'workspace_invite_received', 'Workspace Invite Received', 'Notification when user is invited to a workspace', 'workspace', FALSE, FALSE, TRUE, NULL, 11, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-00000000000c', 'workspace_member_added', 'Workspace Member Added', 'Notification when a new member joins the workspace', 'workspace', FALSE, FALSE, TRUE, NULL, 12, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-00000000000d', 'workspace_member_removed', 'Workspace Member Removed', 'Notification when a member is removed from the workspace', 'workspace', FALSE, FALSE, TRUE, NULL, 13, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-00000000000e', 'workspace_broadcast', 'Workspace Broadcast', 'Admin broadcast to all workspace members', 'workspace', FALSE, FALSE, TRUE, NULL, 14, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-00000000000f', 'global_broadcast', 'Global Broadcast', 'Platform-wide broadcast to all users', 'system', FALSE, FALSE, TRUE, NULL, 15, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-000000000010', 'role_changed', 'Role Changed', 'Notification when user role is changed', 'system', FALSE, FALSE, TRUE, NULL, 16, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-000000000011', 'inactivity_reminder', 'Inactivity Reminder', 'Reminder sent when user has not logged in for configured period', 'engagement', FALSE, FALSE, TRUE, 86400, 17, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', FALSE),
      ('c0000000-0000-0000-0000-000000000012', 'platform_release', 'Platform Release', 'New platform version or feature release notification', 'system', FALSE, FALSE, TRUE, NULL, 18, '2026-03-14T09:38:58.376265', '2026-03-14T09:38:58.376265', FALSE),
      ('c0000000-0000-0000-0000-000000000013', 'platform_incident', 'Platform Incident', 'Platform incident or outage notification', 'system', FALSE, FALSE, TRUE, NULL, 19, '2026-03-14T09:38:58.376265', '2026-03-14T09:38:58.376265', FALSE),
      ('c0000000-0000-0000-0000-000000000014', 'platform_maintenance', 'Scheduled Maintenance', 'Scheduled platform maintenance window notification', 'system', FALSE, FALSE, TRUE, NULL, 20, '2026-03-14T09:38:58.376265', '2026-03-14T09:38:58.376265', FALSE)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, category_code = EXCLUDED.category_code, is_mandatory = EXCLUDED.is_mandatory, is_user_triggered = EXCLUDED.is_user_triggered, default_enabled = EXCLUDED.default_enabled, cooldown_seconds = EXCLUDED.cooldown_seconds, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at, dispatch_immediately = EXCLUDED.dispatch_immediately;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.05_dim_notification_statuses (10 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."05_dim_notification_statuses" (id, code, name, description, is_terminal, sort_order, created_at, updated_at)
  VALUES
      ('d0000000-0000-0000-0000-000000000001', 'queued', 'Queued', 'Notification is queued for processing', FALSE, 1, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-000000000002', 'processing', 'Processing', 'Notification is being processed by a worker', FALSE, 2, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-000000000003', 'sent', 'Sent', 'Notification was sent to the provider', FALSE, 3, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-000000000004', 'delivered', 'Delivered', 'Provider confirmed delivery to recipient', TRUE, 4, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-000000000005', 'opened', 'Opened', 'Recipient opened the notification', TRUE, 5, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-000000000006', 'clicked', 'Clicked', 'Recipient clicked a link in the notification', TRUE, 6, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-000000000007', 'failed', 'Failed', 'Delivery attempt failed, may be retried', FALSE, 7, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-000000000008', 'bounced', 'Bounced', 'Email bounced or push endpoint invalid', TRUE, 8, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-000000000009', 'suppressed', 'Suppressed', 'Notification suppressed due to user preference', TRUE, 9, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('d0000000-0000-0000-0000-00000000000a', 'dead_letter', 'Dead Letter', 'All retry attempts exhausted', TRUE, 10, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_terminal = EXCLUDED.is_terminal, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.06_dim_notification_priorities (4 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."06_dim_notification_priorities" (id, code, name, description, weight, max_retry_attempts, retry_base_delay_seconds, sort_order, created_at, updated_at)
  VALUES
      ('e0000000-0000-0000-0000-000000000001', 'critical', 'Critical', 'Highest priority, processed first with maximum retries', 1000, 5, 30, 1, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('e0000000-0000-0000-0000-000000000002', 'high', 'High', 'High priority with elevated retry attempts', 100, 4, 60, 2, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('e0000000-0000-0000-0000-000000000003', 'normal', 'Normal', 'Standard priority for most notifications', 10, 3, 120, 3, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('e0000000-0000-0000-0000-000000000004', 'low', 'Low', 'Low priority for non-urgent notifications', 1, 2, 300, 4, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, weight = EXCLUDED.weight, max_retry_attempts = EXCLUDED.max_retry_attempts, retry_base_delay_seconds = EXCLUDED.retry_base_delay_seconds, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.07_dim_notification_channel_types (33 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."07_dim_notification_channel_types" (id, notification_type_code, channel_code, priority_code, is_default, created_at, updated_at)
  VALUES
      ('2285defc-d71f-4707-87cc-4c0b9845fdfb', 'magic_link_login', 'email', 'critical', TRUE, '2026-03-20T03:54:34.755794', '2026-03-20T03:54:34.755794'),
      ('f0000000-0000-0000-0000-000000000001', 'password_reset', 'email', 'critical', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000002', 'email_verification', 'email', 'critical', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000003', 'login_from_new_device', 'email', 'high', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000004', 'login_from_new_device', 'web_push', 'high', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000005', 'api_key_created', 'email', 'high', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000006', 'password_changed', 'email', 'high', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000007', 'email_verified', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000008', 'org_invite_received', 'email', 'high', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000009', 'org_invite_received', 'web_push', 'high', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-00000000000a', 'org_member_added', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-00000000000b', 'org_member_added', 'web_push', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-00000000000c', 'org_member_removed', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-00000000000d', 'org_broadcast', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-00000000000e', 'org_broadcast', 'web_push', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-00000000000f', 'workspace_invite_received', 'email', 'high', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000010', 'workspace_invite_received', 'web_push', 'high', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000011', 'workspace_member_added', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000012', 'workspace_member_added', 'web_push', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000013', 'workspace_member_removed', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000014', 'workspace_broadcast', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000015', 'workspace_broadcast', 'web_push', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000016', 'global_broadcast', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000017', 'global_broadcast', 'web_push', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000018', 'role_changed', 'email', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-000000000019', 'role_changed', 'web_push', 'normal', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-00000000001a', 'inactivity_reminder', 'email', 'low', TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('f0000000-0000-0000-0000-00000000001b', 'platform_release', 'email', 'normal', TRUE, '2026-03-14T09:38:58.411242', '2026-03-14T09:38:58.411242'),
      ('f0000000-0000-0000-0000-00000000001c', 'platform_release', 'web_push', 'normal', TRUE, '2026-03-14T09:38:58.411242', '2026-03-14T09:38:58.411242'),
      ('f0000000-0000-0000-0000-00000000001d', 'platform_incident', 'email', 'critical', TRUE, '2026-03-14T09:38:58.411242', '2026-03-14T09:38:58.411242'),
      ('f0000000-0000-0000-0000-00000000001e', 'platform_incident', 'web_push', 'critical', TRUE, '2026-03-14T09:38:58.411242', '2026-03-14T09:38:58.411242'),
      ('f0000000-0000-0000-0000-00000000001f', 'platform_maintenance', 'email', 'high', TRUE, '2026-03-14T09:38:58.411242', '2026-03-14T09:38:58.411242'),
      ('f0000000-0000-0000-0000-000000000020', 'platform_maintenance', 'web_push', 'high', TRUE, '2026-03-14T09:38:58.411242', '2026-03-14T09:38:58.411242')
  ON CONFLICT (notification_type_code, channel_code) DO UPDATE SET priority_code = EXCLUDED.priority_code, is_default = EXCLUDED.is_default, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.08_dim_template_variable_keys (142 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."08_dim_template_variable_keys" (id, code, name, description, data_type, example_value, resolution_source, resolution_key, sort_order, created_at, updated_at, preview_default, resolver_config, query_id, static_value, is_user_defined)
  VALUES
      ('0000581e-c61c-4132-803b-d95a98ec0cc5', 'platform.year', 'Platform Year', 'Current year for copyright footers', 'string', '2026', 'settings', 'platform.year', 20, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '2026', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000001', 'user.display_name', 'User Display Name', 'The display name of the recipient user', 'string', 'John Doe', 'user_property', 'display_name', 1, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:58.922409', 'Sri Gadde', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000002', 'user.email', 'User Email', 'The email address of the recipient user', 'email', 'john@example.com', 'user_property', 'email', 2, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:58.945797', 'sri@kreesalis.com', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000003', 'org.name', 'Organization Name', 'The name of the relevant organization', 'string', 'Acme Corp', 'org', 'name', 6, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:59.115147', 'Kreesalis Corp', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000004', 'workspace.name', 'Workspace Name', 'The name of the relevant workspace', 'string', 'Engineering', 'workspace', 'name', 8, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:59.139427', 'K-Control Workspace', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000005', 'action_url', 'Action URL', 'The URL for the primary call-to-action', 'url', 'https://app.example.com/verify?token=abc', 'audit_property', 'action_url', 10, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:59.090101', 'sri@kreesalis.com', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000006', 'token', 'Token', 'A verification or reset token', 'string', 'abc123def456', 'audit_property', 'token', 11, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000007', 'platform.name', 'Platform Name', 'The name of the platform', 'string', 'kcontrol', 'settings', 'notification_from_name', 12, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:58.993319', 'K-Control', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000008', 'expiry_hours', 'Expiry Hours', 'Number of hours until a token or link expires', 'integer', '24', 'audit_property', 'expiry_hours', 13, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000009', 'ip_address', 'IP Address', 'Client IP address associated with the event', 'string', '192.168.1.1', 'audit_property', 'ip_address', 14, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:59.01776', '203.0.113.1', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000000a', 'device_info', 'Device Info', 'User agent or device information', 'string', 'Chrome on macOS', 'audit_property', 'device_info', 15, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:59.042017', 'MacBook Pro / Chrome 120', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000000b', 'timestamp', 'Timestamp', 'Human-readable timestamp of the event', 'string', '2026-03-15 14:30:00 UTC', 'computed', 'event_timestamp', 16, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:59.064997', '16 Mar 2026 09:30', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000000c', 'actor.display_name', 'Actor Display Name', 'The display name of the user who performed the action', 'string', 'Jane Admin', 'actor_property', 'display_name', 17, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000000d', 'role.name', 'Role Name', 'The name of the role being assigned or changed', 'string', 'Workspace Admin', 'audit_property', 'role_name', 19, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000000e', 'api_key.name', 'API Key Name', 'The name/label of the API key', 'string', 'Production Key', 'audit_property', 'api_key_name', 20, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000000f', 'broadcast.title', 'Broadcast Title', 'The title of the broadcast message', 'string', 'Important Update', 'audit_property', 'broadcast_title', 21, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000010', 'broadcast.body', 'Broadcast Body', 'The body content of the broadcast message', 'string', 'Please read this important announcement...', 'audit_property', 'broadcast_body', 22, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000011', 'user.first_name', 'User First Name', 'The first name of the recipient user', 'string', 'John', 'user_property', 'first_name', 3, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:58.869898', 'Sri', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000012', 'user.last_name', 'User Last Name', 'The last name of the recipient user', 'string', 'Doe', 'user_property', 'last_name', 4, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:58.894911', 'Gadde', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000013', 'user.username', 'Username', 'The username of the recipient user', 'string', 'johndoe', 'user_property', 'username', 5, '2026-03-14T08:26:29.738975', '2026-03-16T11:15:58.96984', 'sri.gadde', NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000014', 'org.slug', 'Organization Slug', 'The URL slug of the relevant organization', 'string', 'acme-corp', 'org', 'slug', 7, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000015', 'workspace.slug', 'Workspace Slug', 'The URL slug of the relevant workspace', 'string', 'engineering', 'workspace', 'slug', 9, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000016', 'actor.email', 'Actor Email', 'The email address of the user who performed the action', 'email', 'jane@example.com', 'actor_property', 'email', 18, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000017', 'unsubscribe_url', 'Unsubscribe URL', 'URL for user to manage notification preferences', 'url', 'https://app.example.com/settings/notifications', 'computed', 'unsubscribe_url', 23, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000018', 'group.name', 'User Group Name', 'The name of the user''s primary group', 'string', 'Engineering Team', 'user_group', 'name', 24, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000019', 'group.code', 'User Group Code', 'The code of the user''s primary group', 'string', 'engineering', 'user_group', 'code', 25, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000001a', 'group.description', 'User Group Description', 'The description of the user''s primary group', 'string', 'Platform engineering team', 'user_group', 'description', 26, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000001b', 'tenant.key', 'Tenant Key', 'The tenant identifier', 'string', 'acme', 'tenant', 'tenant_key', 27, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000001c', 'tenant.user_count', 'Tenant User Count', 'Total active users in the tenant', 'integer', '150', 'tenant', 'user_count', 28, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000001d', 'tenant.org_count', 'Tenant Org Count', 'Total active organizations in the tenant', 'integer', '5', 'tenant', 'org_count', 29, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000001e', 'release.version', 'Release Version', 'Version number', 'string', 'v2.1.0', 'audit_property', 'release_version', 30, '2026-03-14T09:38:58.448852', '2026-03-14T09:38:58.448852', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-00000000001f', 'release.title', 'Release Title', 'Title of the release', 'string', 'Perf', 'audit_property', 'release_title', 31, '2026-03-14T09:38:58.448852', '2026-03-14T09:38:58.448852', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000020', 'release.summary', 'Release Summary', 'Brief summary', 'string', 'Bug fixes', 'audit_property', 'release_summary', 32, '2026-03-14T09:38:58.448852', '2026-03-14T09:38:58.448852', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000021', 'release.changelog_url', 'Changelog URL', 'URL to changelog', 'url', 'https://docs.example.com', 'audit_property', 'changelog_url', 33, '2026-03-14T09:38:58.448852', '2026-03-14T09:38:58.448852', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000022', 'incident.title', 'Incident Title', 'Incident title', 'string', 'API Issues', 'audit_property', 'incident_title', 34, '2026-03-14T09:38:58.448852', '2026-03-14T09:38:58.448852', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000023', 'incident.severity', 'Incident Severity', 'Severity', 'string', 'major', 'audit_property', 'incident_severity', 35, '2026-03-14T09:38:58.448852', '2026-03-14T09:38:58.448852', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000024', 'incident.status', 'Incident Status', 'Status', 'string', 'investigating', 'audit_property', 'incident_status', 36, '2026-03-14T09:38:58.448852', '2026-03-14T09:38:58.448852', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000025', 'incident.affected_components', 'Affected Components', 'Components', 'string', 'API', 'audit_property', 'affected_components', 37, '2026-03-14T09:38:58.448852', '2026-03-14T09:38:58.448852', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000050', 'otp_code', 'OTP Code', 'One-time verification code', 'string', '482901', 'audit_property', 'otp_code', 50, '2026-03-20T03:39:16.928164', '2026-03-20T03:39:16.928164', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000051', 'magic_link.url', 'Magic Link URL', 'The magic link URL for passwordless login', 'url', 'https://app.kreesalis.com/magic-link/verify?token=abc123', 'audit_property', 'magic_link_url', 51, '2026-03-20T03:54:34.780647', '2026-03-20T03:54:34.780647', NULL, NULL, NULL, NULL, FALSE),
      ('10000000-0000-0000-0000-000000000052', 'magic_link.expires_in', 'Magic Link Expiry', 'Time until the magic link expires', 'string', '24 hours', 'audit_property', 'expires_in', 52, '2026-03-20T03:54:34.780647', '2026-03-20T03:54:34.780647', NULL, NULL, NULL, NULL, FALSE),
      ('144bd57c-b15d-41c6-9a95-60b0de3eba13', 'event.timestamp', 'Event Timestamp', 'When the event occurred', 'string', '16 Mar 2026 09:30', 'audit_property', 'timestamp', 81, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '16 Mar 2026 09:30', NULL, NULL, NULL, FALSE),
      ('17c0872c-08d7-48e2-abcb-c537dfb50e87', 'inviter.display_name', 'Inviter Name', 'Person who sent the invitation', 'string', 'Admin User', 'computed', 'inviter.display_name', 92, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Admin User', NULL, NULL, NULL, FALSE),
      ('1a92d2b0-55fa-4414-b9d3-16cc2f773dd3', 'invite.role', 'Invite Role', 'Role granted in the invitation', 'string', 'Admin', 'computed', 'invite.role', 90, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Admin', NULL, NULL, NULL, FALSE),
      ('1c0fd84d-c1d0-4ddc-b896-686b2b68530c', 'control.failing_count', 'Failing Controls', 'Controls failing in this workspace', 'integer', '4', 'computed', 'control.failing_count', 61, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '4', NULL, NULL, NULL, FALSE),
      ('290051ca-74ec-4355-ac16-9a6d5930bdac', 'broadcast.body_text', 'Broadcast Body Text', 'Plain text body', 'string', 'Body text here.', 'computed', 'broadcast.body_text', 103, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Preview body content.', NULL, NULL, NULL, FALSE),
      ('31a5777f-3b59-4d29-85a1-5d6dd8e7a1ed', 'datetime.datetime', 'Date & Time', 'Current date and time', 'string', '16 Mar 2026 09:30', 'computed', 'datetime.datetime', 12, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '16 Mar 2026 09:30', NULL, NULL, NULL, FALSE),
      ('36a762a0-6a8a-469e-ac76-83bdfd4caba3', 'platform.tagline', 'Platform Tagline', 'Short tagline shown under logo', 'string', 'Continuous Compliance', 'settings', 'platform.tagline', 21, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Continuous Compliance', NULL, NULL, NULL, FALSE),
      ('4d4167d9-f6f8-4b9a-ae22-538bc03bcdcc', 'action.workspace_url', 'Workspace URL', 'Direct link to workspace', 'url', 'https://app.kreesalis.com/dashboard', 'computed', 'action.workspace_url', 73, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'https://app.kreesalis.com/dashboard', NULL, NULL, NULL, FALSE),
      ('4fdd454a-018f-4c47-9152-fbab87d4bbe1', 'action.reset_url', 'Password Reset URL', 'One-time reset link', 'url', 'https://app.kreesalis.com/reset?token=PREVIEW', 'computed', 'action.reset_url', 70, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'https://app.kreesalis.com/reset?token=PREVIEW', NULL, NULL, NULL, FALSE),
      ('51e8656a-6dd3-49b6-87f8-4aa4370f67f5', 'platform.unsubscribe_url', 'Unsubscribe URL', 'Notification preferences URL', 'url', 'https://app.kreesalis.com/settings/notifications', 'computed', 'platform.unsubscribe_url', 25, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'https://app.kreesalis.com/settings/notifications', NULL, NULL, NULL, FALSE),
      ('6fab2b16-adba-4c90-9ad6-9c0f55b8a77e', 'datetime.date', 'Date', 'Current date (e.g. 16 Mar 2026)', 'string', '16 Mar 2026', 'computed', 'datetime.date', 10, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '16 Mar 2026', NULL, NULL, NULL, FALSE),
      ('73a946ba-bd9b-4750-b2a2-5fc9a5056f57', 'event.browser', 'Event Browser', 'Browser used', 'string', 'Chrome 120', 'audit_property', 'device_info', 83, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Chrome 120', NULL, NULL, NULL, FALSE),
      ('78703968-b743-4fd5-b849-bb6b2e837725', 'broadcast.body_html', 'Broadcast Body HTML', 'HTML body of broadcast', 'string', '<p>Body text here.</p>', 'computed', 'broadcast.body_html', 102, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '<p>Preview body content.</p>', NULL, NULL, NULL, FALSE),
      ('7c8110b0-b544-461e-887b-6fa3aa6fb262', 'invite.expires_at', 'Invite Expiry', 'When the invitation expires', 'string', '30 Mar 2026', 'computed', 'invite.expires_at', 91, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '30 Mar 2026', NULL, NULL, NULL, FALSE),
      ('7c94c1b4-9d13-43e0-a531-b2e888dee77c', 'task.pending_count', 'Pending Tasks', 'Open tasks for this user in this workspace', 'integer', '5', 'computed', 'task.pending_count', 50, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '5', NULL, NULL, NULL, FALSE),
      ('80ff384f-be10-4511-9d0a-1c442801011b', 'platform.logo_url', 'Platform Logo URL', 'URL of the platform logo used in email headers', 'url', 'https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png', 'static', 'logo_url', 2, '2026-03-20T04:59:04.847336', '2026-03-20T04:59:04.847336', NULL, NULL, NULL, 'https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png', FALSE),
      ('83077e50-55fc-41b5-b4a1-438fef0b4732', 'risk.high_count', 'High/Critical Risks', 'Critical or high risks in this workspace', 'integer', '2', 'computed', 'risk.high_count', 63, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '2', NULL, NULL, NULL, FALSE),
      ('8ce2a8ed-750f-43e2-b8de-48603061db74', 'action.verify_url', 'Email Verify URL', 'One-time email verification link', 'url', 'https://app.kreesalis.com/verify?token=PREVIEW', 'computed', 'action.verify_url', 71, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'https://app.kreesalis.com/verify?token=PREVIEW', NULL, NULL, NULL, FALSE),
      ('96dabc25-5cba-45f2-84da-f447d72bf17d', 'action.expires_in', 'Expires In', 'Human-readable expiry duration', 'string', '24 hours', 'computed', 'action.expires_in', 75, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '24 hours', NULL, NULL, NULL, FALSE),
      ('9b8c40c3-3831-4a35-9d10-e268d18e8efb', 'platform.support_email', 'Support Email', 'Support email address shown in notifications', 'string', 'support@kreesalis.com', 'static', NULL, 9999, '2026-03-17T09:01:13.492053', '2026-03-18T09:22:50.021808', NULL, NULL, NULL, 'support@kreesalis.com', TRUE),
      ('a957df75-edfc-48a8-bb48-0ba74e650118', 'datetime.time', 'Time', 'Current time (e.g. 09:30 AM)', 'string', '09:30 AM', 'computed', 'datetime.time', 11, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '09:30 AM', NULL, NULL, NULL, FALSE),
      ('adc9069f-841b-4d16-9b16-bd77ae56c125', 'framework.active_count', 'Active Frameworks', 'Frameworks active in this workspace', 'integer', '3', 'computed', 'framework.active_count', 60, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '3', NULL, NULL, NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000001', 'custom.user_profile.first_name', 'User First Name', 'Recipient first name', 'string', 'Sri', 'custom_query', 'first_name', 900, '2026-03-17T07:23:08.817984', '2026-03-17T07:23:08.817984', NULL, NULL, 'a0000001-0000-0000-0000-000000000001', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000002', 'custom.user_profile.last_name', 'User Last Name', 'Recipient last name', 'string', 'Kumar', 'custom_query', 'last_name', 901, '2026-03-17T07:23:08.817984', '2026-03-17T07:23:08.817984', NULL, NULL, 'a0000001-0000-0000-0000-000000000001', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000003', 'custom.user_profile.display_name', 'User Display Name', 'Recipient display name', 'string', 'Sri K', 'custom_query', 'display_name', 902, '2026-03-17T07:23:08.817984', '2026-03-17T07:23:08.817984', NULL, NULL, 'a0000001-0000-0000-0000-000000000001', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000004', 'custom.user_profile.email', 'User Email', 'Recipient email', 'string', 'sri@example.com', 'custom_query', 'email', 903, '2026-03-17T07:23:08.817984', '2026-03-17T07:23:08.817984', NULL, NULL, 'a0000001-0000-0000-0000-000000000001', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000005', 'custom.user_profile.username', 'User Username', 'Recipient username', 'string', 'sri', 'custom_query', 'username', 904, '2026-03-17T07:23:08.817984', '2026-03-17T07:23:08.817984', NULL, NULL, 'a0000001-0000-0000-0000-000000000001', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000006', 'custom.user_profile.timezone', 'User Timezone', 'Recipient timezone', 'string', 'America/Chicago', 'custom_query', 'timezone', 905, '2026-03-17T07:23:08.817984', '2026-03-17T07:23:08.817984', NULL, NULL, 'a0000001-0000-0000-0000-000000000001', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000010', 'custom.actor_profile.first_name', 'Actor First Name', 'Actor first name', 'string', 'John', 'custom_query', 'first_name', 910, '2026-03-17T07:23:08.845648', '2026-03-17T07:23:08.845648', NULL, NULL, 'a0000001-0000-0000-0000-000000000002', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000011', 'custom.actor_profile.last_name', 'Actor Last Name', 'Actor last name', 'string', 'Admin', 'custom_query', 'last_name', 911, '2026-03-17T07:23:08.845648', '2026-03-17T07:23:08.845648', NULL, NULL, 'a0000001-0000-0000-0000-000000000002', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000012', 'custom.actor_profile.display_name', 'Actor Display Name', 'Actor display name', 'string', 'John Admin', 'custom_query', 'display_name', 912, '2026-03-17T07:23:08.845648', '2026-03-17T07:23:08.845648', NULL, NULL, 'a0000001-0000-0000-0000-000000000002', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000013', 'custom.actor_profile.email', 'Actor Email', 'Actor email', 'string', 'admin@example.com', 'custom_query', 'email', 913, '2026-03-17T07:23:08.845648', '2026-03-17T07:23:08.845648', NULL, NULL, 'a0000001-0000-0000-0000-000000000002', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000014', 'custom.actor_profile.username', 'Actor Username', 'Actor username', 'string', 'admin', 'custom_query', 'username', 914, '2026-03-17T07:23:08.845648', '2026-03-17T07:23:08.845648', NULL, NULL, 'a0000001-0000-0000-0000-000000000002', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000020', 'custom.org_detail.org_name', 'Org Name', 'Organization name', 'string', 'Acme Corp', 'custom_query', 'org_name', 920, '2026-03-17T07:23:08.873429', '2026-03-17T07:23:08.873429', NULL, NULL, 'a0000001-0000-0000-0000-000000000003', NULL, FALSE),
      ('a0a71a1c-a681-49fd-bfd8-74bab218e798', 'custom.org_detail.org_slug', 'Org Slug', 'Organization slug', 'string', 'acme-corp', 'custom_query', 'org_slug', 921, '2026-03-17T07:23:08.873429', '2026-03-17T07:23:08.873429', NULL, NULL, 'a0000001-0000-0000-0000-000000000003', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000022', 'custom.org_detail.org_type_name', 'Org Type', 'Organization type', 'string', 'Enterprise', 'custom_query', 'org_type_name', 922, '2026-03-17T07:23:08.873429', '2026-03-17T07:23:08.873429', NULL, NULL, 'a0000001-0000-0000-0000-000000000003', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000030', 'custom.workspace_detail.workspace_name', 'Workspace Name', 'Workspace name', 'string', 'Production', 'custom_query', 'workspace_name', 930, '2026-03-17T07:23:08.899592', '2026-03-17T07:23:08.899592', NULL, NULL, 'a0000001-0000-0000-0000-000000000004', NULL, FALSE),
      ('05e98e46-e4b6-4edb-b14e-cfd739dd23fb', 'custom.workspace_detail.workspace_slug', 'Workspace Slug', 'Workspace slug', 'string', 'production', 'custom_query', 'workspace_slug', 931, '2026-03-17T07:23:08.899592', '2026-03-17T07:23:08.899592', NULL, NULL, 'a0000001-0000-0000-0000-000000000004', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000032', 'custom.workspace_detail.workspace_type_name', 'Workspace Type', 'Workspace type', 'string', 'Compliance', 'custom_query', 'workspace_type_name', 932, '2026-03-17T07:23:08.899592', '2026-03-17T07:23:08.899592', NULL, NULL, 'a0000001-0000-0000-0000-000000000004', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000033', 'custom.workspace_detail.org_name', 'Workspace Org Name', 'Parent org of workspace', 'string', 'Acme Corp', 'custom_query', 'org_name', 933, '2026-03-17T07:23:08.899592', '2026-03-17T07:23:08.899592', NULL, NULL, 'a0000001-0000-0000-0000-000000000004', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000040', 'custom.task_detail.title', 'Task Title', 'Task title', 'string', 'Review access policies', 'custom_query', 'title', 940, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000041', 'custom.task_detail.description', 'Task Description', 'Task description', 'string', 'Quarterly access review', 'custom_query', 'description', 941, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000042', 'custom.task_detail.status_code', 'Task Status', 'Task status code', 'string', 'in_progress', 'custom_query', 'status_code', 942, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000043', 'custom.task_detail.priority_code', 'Task Priority', 'Task priority', 'string', 'high', 'custom_query', 'priority_code', 943, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000044', 'custom.task_detail.task_type_code', 'Task Type', 'Task type', 'string', 'control_remediation', 'custom_query', 'task_type_code', 944, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000045', 'custom.task_detail.assignee_name', 'Task Assignee Name', 'Assignee display name', 'string', 'Jane Engineer', 'custom_query', 'assignee_name', 945, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000046', 'custom.task_detail.assignee_email', 'Task Assignee Email', 'Assignee email', 'string', 'jane@example.com', 'custom_query', 'assignee_email', 946, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000047', 'custom.task_detail.reporter_name', 'Task Reporter Name', 'Reporter display name', 'string', 'John Admin', 'custom_query', 'reporter_name', 947, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000048', 'custom.task_detail.reporter_email', 'Task Reporter Email', 'Reporter email', 'string', 'admin@example.com', 'custom_query', 'reporter_email', 948, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000049', 'custom.task_detail.org_name', 'Task Org', 'Task org name', 'string', 'Acme Corp', 'custom_query', 'org_name', 949, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-00000000004a', 'custom.task_detail.workspace_name', 'Task Workspace', 'Task workspace name', 'string', 'Production', 'custom_query', 'workspace_name', 950, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-00000000004b', 'custom.task_detail.due_date', 'Task Due Date', 'Task due date', 'string', '2026-04-01', 'custom_query', 'due_date', 951, '2026-03-17T07:23:08.929803', '2026-03-17T07:23:08.929803', NULL, NULL, 'a0000001-0000-0000-0000-000000000005', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000050', 'custom.risk_detail.risk_code', 'Risk Code', 'Risk code', 'string', 'RSK-042', 'custom_query', 'risk_code', 960, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000051', 'custom.risk_detail.title', 'Risk Title', 'Risk title', 'string', 'Unauthorized access', 'custom_query', 'title', 961, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000052', 'custom.risk_detail.description', 'Risk Description', 'Risk description', 'string', 'Data breach risk', 'custom_query', 'description', 962, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000053', 'custom.risk_detail.risk_level_code', 'Risk Level Code', 'Risk level code', 'string', 'high', 'custom_query', 'risk_level_code', 963, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000054', 'custom.risk_detail.risk_level_name', 'Risk Level Name', 'Risk level human name', 'string', 'High', 'custom_query', 'risk_level_name', 964, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000055', 'custom.risk_detail.risk_category_name', 'Risk Category', 'Risk category name', 'string', 'Technology', 'custom_query', 'risk_category_name', 965, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000056', 'custom.risk_detail.risk_status', 'Risk Status', 'Risk status', 'string', 'identified', 'custom_query', 'risk_status', 966, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000057', 'custom.risk_detail.treatment_type_code', 'Risk Treatment', 'Treatment type', 'string', 'mitigate', 'custom_query', 'treatment_type_code', 967, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000058', 'custom.risk_detail.owner_name', 'Risk Owner Name', 'Risk owner display name', 'string', 'Jane Engineer', 'custom_query', 'owner_name', 968, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000059', 'custom.risk_detail.owner_email', 'Risk Owner Email', 'Risk owner email', 'string', 'jane@example.com', 'custom_query', 'owner_email', 969, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-00000000005a', 'custom.risk_detail.org_name', 'Risk Org', 'Risk org name', 'string', 'Acme Corp', 'custom_query', 'org_name', 970, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-00000000005b', 'custom.risk_detail.workspace_name', 'Risk Workspace', 'Risk workspace name', 'string', 'Production', 'custom_query', 'workspace_name', 971, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-00000000005c', 'custom.risk_detail.latest_risk_score', 'Risk Score', 'Latest risk assessment score', 'string', '12', 'custom_query', 'latest_risk_score', 972, '2026-03-17T07:23:08.96148', '2026-03-17T07:23:08.96148', NULL, NULL, 'a0000001-0000-0000-0000-000000000006', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000060', 'custom.control_detail.control_code', 'Control Code', 'Control code', 'string', 'AC-001', 'custom_query', 'control_code', 980, '2026-03-17T07:23:08.99178', '2026-03-17T07:23:08.99178', NULL, NULL, 'a0000001-0000-0000-0000-000000000007', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000061', 'custom.control_detail.control_name', 'Control Name', 'Control name', 'string', 'Access Control Review', 'custom_query', 'control_name', 981, '2026-03-17T07:23:08.99178', '2026-03-17T07:23:08.99178', NULL, NULL, 'a0000001-0000-0000-0000-000000000007', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000062', 'custom.control_detail.description', 'Control Description', 'Control description', 'string', 'Periodic access audit', 'custom_query', 'description', 982, '2026-03-17T07:23:08.99178', '2026-03-17T07:23:08.99178', NULL, NULL, 'a0000001-0000-0000-0000-000000000007', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000063', 'custom.control_detail.guidance', 'Control Guidance', 'Implementation guidance', 'string', 'Review quarterly', 'custom_query', 'guidance', 983, '2026-03-17T07:23:08.99178', '2026-03-17T07:23:08.99178', NULL, NULL, 'a0000001-0000-0000-0000-000000000007', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000064', 'custom.control_detail.category_name', 'Control Category', 'Control category name', 'string', 'Access Control', 'custom_query', 'category_name', 984, '2026-03-17T07:23:08.99178', '2026-03-17T07:23:08.99178', NULL, NULL, 'a0000001-0000-0000-0000-000000000007', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000065', 'custom.control_detail.criticality_name', 'Control Criticality', 'Control criticality level', 'string', 'High', 'custom_query', 'criticality_name', 985, '2026-03-17T07:23:08.99178', '2026-03-17T07:23:08.99178', NULL, NULL, 'a0000001-0000-0000-0000-000000000007', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000066', 'custom.control_detail.framework_name', 'Control Framework', 'Parent framework name', 'string', 'SOC 2', 'custom_query', 'framework_name', 986, '2026-03-17T07:23:08.99178', '2026-03-17T07:23:08.99178', NULL, NULL, 'a0000001-0000-0000-0000-000000000007', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000067', 'custom.control_detail.framework_code', 'Framework Code', 'Parent framework code', 'string', 'soc2-2024', 'custom_query', 'framework_code', 987, '2026-03-17T07:23:08.99178', '2026-03-17T07:23:08.99178', NULL, NULL, 'a0000001-0000-0000-0000-000000000007', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000070', 'custom.framework_detail.framework_code', 'Framework Code', 'Framework code', 'string', 'soc2-2024', 'custom_query', 'framework_code', 990, '2026-03-17T07:23:09.020106', '2026-03-17T07:23:09.020106', NULL, NULL, 'a0000001-0000-0000-0000-000000000008', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000071', 'custom.framework_detail.framework_name', 'Framework Name', 'Framework name', 'string', 'SOC 2', 'custom_query', 'framework_name', 991, '2026-03-17T07:23:09.020106', '2026-03-17T07:23:09.020106', NULL, NULL, 'a0000001-0000-0000-0000-000000000008', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000072', 'custom.framework_detail.description', 'Framework Desc', 'Framework description', 'string', 'Service org controls', 'custom_query', 'description', 992, '2026-03-17T07:23:09.020106', '2026-03-17T07:23:09.020106', NULL, NULL, 'a0000001-0000-0000-0000-000000000008', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000073', 'custom.framework_detail.publisher_name', 'Framework Publisher', 'Publisher name', 'string', 'AICPA', 'custom_query', 'publisher_name', 993, '2026-03-17T07:23:09.020106', '2026-03-17T07:23:09.020106', NULL, NULL, 'a0000001-0000-0000-0000-000000000008', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000074', 'custom.framework_detail.framework_type_name', 'Framework Type', 'Framework type', 'string', 'Security Framework', 'custom_query', 'framework_type_name', 994, '2026-03-17T07:23:09.020106', '2026-03-17T07:23:09.020106', NULL, NULL, 'a0000001-0000-0000-0000-000000000008', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000075', 'custom.framework_detail.framework_category_name', 'Framework Category', 'Framework category', 'string', 'Security', 'custom_query', 'framework_category_name', 995, '2026-03-17T07:23:09.020106', '2026-03-17T07:23:09.020106', NULL, NULL, 'a0000001-0000-0000-0000-000000000008', NULL, FALSE),
      ('bff7e8c3-d47a-4ffc-88ba-14fc9881748c', 'task.overdue_count', 'Overdue Tasks', 'Overdue tasks for this user in this workspace', 'integer', '2', 'computed', 'task.overdue_count', 51, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '2', NULL, NULL, NULL, FALSE),
      ('c0000001-0000-0000-0000-000000000001', 'task_id', 'Task ID', 'UUID of the task from the audit event', 'string', '3e7a1b2c-...', 'computed', 'task_id', 1010, '2026-03-19T12:00:11.970203', '2026-03-19T12:00:11.970203', NULL, NULL, NULL, NULL, FALSE),
      ('c0000001-0000-0000-0000-000000000002', 'risk_id', 'Risk ID', 'UUID of the risk from the audit event', 'string', '5f2b8d1e-...', 'computed', 'risk_id', 1011, '2026-03-19T12:00:11.970203', '2026-03-19T12:00:11.970203', NULL, NULL, NULL, NULL, FALSE),
      ('c0000001-0000-0000-0000-000000000003', 'control_id', 'Control ID', 'UUID of the control from the audit event', 'string', '9a4c3f7d-...', 'computed', 'control_id', 1012, '2026-03-19T12:00:11.970203', '2026-03-19T12:00:11.970203', NULL, NULL, NULL, NULL, FALSE),
      ('c0000001-0000-0000-0000-000000000004', 'framework_id', 'Framework ID', 'UUID of the framework from the audit event', 'string', 'b2e1d5a8-...', 'computed', 'framework_id', 1013, '2026-03-19T12:00:11.970203', '2026-03-19T12:00:11.970203', NULL, NULL, NULL, NULL, FALSE),
      ('c0000001-0000-0000-0000-000000000005', 'org_id', 'Org ID', 'UUID of the organization from the audit event', 'string', 'd4f6c2b1-...', 'computed', 'org_id', 1014, '2026-03-19T12:00:11.970203', '2026-03-19T12:00:11.970203', NULL, NULL, NULL, NULL, FALSE),
      ('c0000001-0000-0000-0000-000000000006', 'workspace_id', 'Workspace ID', 'UUID of the workspace from the audit event', 'string', 'e7a3b9c5-...', 'computed', 'workspace_id', 1015, '2026-03-19T12:00:11.970203', '2026-03-19T12:00:11.970203', NULL, NULL, NULL, NULL, FALSE),
      ('c0000002-0000-0000-0000-000000000001', 'task_url', 'Task URL', 'Direct link to the task page (base_url/tasks/{task_id})', 'string', 'https://app.example.com/tasks/3e7a1b2c-...', 'computed', 'task_url', 1020, '2026-03-19T12:00:12.002171', '2026-03-19T12:00:12.002171', NULL, NULL, NULL, NULL, FALSE),
      ('c0000002-0000-0000-0000-000000000002', 'risk_url', 'Risk URL', 'Direct link to the risk page (base_url/risks/{risk_id})', 'string', 'https://app.example.com/risks/5f2b8d1e-...', 'computed', 'risk_url', 1021, '2026-03-19T12:00:12.002171', '2026-03-19T12:00:12.002171', NULL, NULL, NULL, NULL, FALSE),
      ('c0000002-0000-0000-0000-000000000003', 'control_url', 'Control URL', 'Direct link to the control page (base_url/controls/{control_id})', 'string', 'https://app.example.com/controls/9a4c3f7d-...', 'computed', 'control_url', 1022, '2026-03-19T12:00:12.002171', '2026-03-19T12:00:12.002171', NULL, NULL, NULL, NULL, FALSE),
      ('c0000002-0000-0000-0000-000000000004', 'framework_url', 'Framework URL', 'Direct link to the framework page (base_url/frameworks/{framework_id})', 'string', 'https://app.example.com/frameworks/b2e1d5a8-...', 'computed', 'framework_url', 1023, '2026-03-19T12:00:12.002171', '2026-03-19T12:00:12.002171', NULL, NULL, NULL, NULL, FALSE),
      ('c1a6cdae-1f4a-4a90-8124-c7cfcd7135bf', 'action.secure_account_url', 'Secure Account URL', 'Link to security settings', 'url', 'https://app.kreesalis.com/settings/security', 'computed', 'action.secure_account_url', 74, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'https://app.kreesalis.com/settings/security', NULL, NULL, NULL, FALSE),
      ('c34c277f-3e29-4a0d-a229-adc7cb9ca143', 'platform.company', 'Company Name', 'Legal company name for footers', 'string', 'Kreesalis', 'settings', 'platform.company', 22, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Kreesalis', NULL, NULL, NULL, FALSE),
      ('c43e45be-6e5d-438e-894c-7ea069ec1d4e', 'platform.support_url', 'Support URL', 'Support portal URL', 'url', 'https://kreesalis.com/support', 'settings', 'platform.support_url', 23, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'https://kreesalis.com/support', NULL, NULL, NULL, FALSE),
      ('cc62e24e-719f-4dbe-99ba-8a51a8aeb657', 'broadcast.subject', 'Broadcast Subject', 'Subject line of broadcast', 'string', 'Platform Update', 'computed', 'broadcast.subject', 100, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Platform Update', NULL, NULL, NULL, FALSE),
      ('d44dea64-2f5e-45b8-8222-001b83542876', 'platform.privacy_url', 'Privacy Policy URL', 'Privacy policy URL', 'url', 'https://kreesalis.com/privacy', 'settings', 'platform.privacy_url', 24, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'https://kreesalis.com/privacy', NULL, NULL, NULL, FALSE),
      ('d7af7a0e-9e13-49da-8b6d-2b783733fcc0', 'event.ip_address', 'Event IP', 'IP address of the event', 'string', '203.0.113.1', 'audit_property', 'ip_address', 80, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '203.0.113.1', NULL, NULL, NULL, FALSE),
      ('dfeac69e-ddae-4226-a1b0-816fff8c645c', 'event.device', 'Event Device', 'Device used', 'string', 'MacBook Pro', 'audit_property', 'device_info', 82, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'MacBook Pro', NULL, NULL, NULL, FALSE),
      ('dff2c34c-c8cd-46a0-9add-7e24848cca48', 'risk.open_count', 'Open Risks', 'Open risks in this workspace', 'integer', '7', 'computed', 'risk.open_count', 62, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', '7', NULL, NULL, NULL, FALSE),
      ('e678e501-7681-417e-b957-5d555e36c0ba', 'event.location', 'Event Location', 'Approx location from IP', 'string', 'Mumbai, India', 'audit_property', 'ip_address', 84, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Mumbai, India', NULL, NULL, NULL, FALSE),
      ('efb0dce7-a085-467e-9c0c-f7c940760e12', 'action.accept_url', 'Invitation Accept URL', 'Link to accept an invitation', 'url', 'https://app.kreesalis.com/accept?token=PREVIEW', 'computed', 'action.accept_url', 72, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'https://app.kreesalis.com/accept?token=PREVIEW', NULL, NULL, NULL, FALSE),
      ('f224ae02-b96a-4276-80ba-87efd838fe20', 'broadcast.headline', 'Broadcast Headline', 'H1 headline of broadcast', 'string', 'Important Update', 'computed', 'broadcast.headline', 101, '2026-03-16T11:15:59.162696', '2026-03-16T11:15:59.162696', 'Important Update', NULL, NULL, NULL, FALSE)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, example_value = EXCLUDED.example_value, resolution_source = EXCLUDED.resolution_source, resolution_key = EXCLUDED.resolution_key, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at, preview_default = EXCLUDED.preview_default, resolver_config = EXCLUDED.resolver_config, query_id = EXCLUDED.query_id, static_value = EXCLUDED.static_value, is_user_defined = EXCLUDED.is_user_defined;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.09_dim_tracking_event_types (9 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."09_dim_tracking_event_types" (id, code, name, description, sort_order, created_at, updated_at)
  VALUES
      ('20000000-0000-0000-0000-000000000001', 'queued', 'Queued', 'Notification entered the queue', 1, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('20000000-0000-0000-0000-000000000002', 'sent', 'Sent', 'Notification sent to provider', 2, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('20000000-0000-0000-0000-000000000003', 'delivered', 'Delivered', 'Provider confirmed delivery', 3, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('20000000-0000-0000-0000-000000000004', 'opened', 'Opened', 'Recipient opened the notification', 4, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('20000000-0000-0000-0000-000000000005', 'clicked', 'Clicked', 'Recipient clicked a link', 5, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('20000000-0000-0000-0000-000000000006', 'bounced', 'Bounced', 'Notification bounced', 6, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('20000000-0000-0000-0000-000000000007', 'failed', 'Failed', 'Delivery failed', 7, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('20000000-0000-0000-0000-000000000008', 'dismissed', 'Dismissed', 'Push notification dismissed by user', 8, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('20000000-0000-0000-0000-000000000009', 'unsubscribed', 'Unsubscribed', 'User unsubscribed via notification link', 9, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.09_dim_variable_queries (5 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."09_dim_variable_queries" (id, slug, name, description, sql_template, bind_params, preview_default, is_active, created_at, updated_at)
  VALUES
      ('1b35b9c6-a3d1-48ca-8251-eb5094747e6f', 'framework.active_count', 'Active Framework Count', 'Number of framework versions active in a specific org workspace', 'SELECT COUNT(*)::text FROM "05_grc_library"."03_fct_versions" WHERE workspace_id = $1 AND is_active = TRUE AND is_deleted = FALSE', '["workspace_id"]'::jsonb, '3', TRUE, '2026-03-16T11:15:59.189218+00:00', '2026-03-16T11:15:59.189218+00:00'),
      ('73bde390-c82a-42d7-8e6b-cb86479b0dd0', 'risk.high_count', 'High/Critical Risk Count', 'Number of critical or high severity open risks in a workspace', 'SELECT COUNT(*)::text FROM "06_risk_registry"."02_fct_risks" WHERE org_id = $1 AND workspace_id = $2 AND severity_code IN (''critical'', ''high'') AND status_code NOT IN (''closed'', ''accepted'') AND is_deleted = FALSE', '["org_id", "workspace_id"]'::jsonb, '2', TRUE, '2026-03-16T11:15:59.189218+00:00', '2026-03-16T11:15:59.189218+00:00'),
      ('b545d3f0-0331-4d39-bdf5-b1b6d9e78290', 'risk.open_count', 'Open Risk Count', 'Number of open risks in a specific org workspace', 'SELECT COUNT(*)::text FROM "06_risk_registry"."02_fct_risks" WHERE org_id = $1 AND workspace_id = $2 AND status_code NOT IN (''closed'', ''accepted'') AND is_deleted = FALSE', '["org_id", "workspace_id"]'::jsonb, '7', TRUE, '2026-03-16T11:15:59.189218+00:00', '2026-03-16T11:15:59.189218+00:00'),
      ('c1e38677-cd52-42c4-aae4-e47b4a4640b1', 'task.overdue_count', 'Overdue Task Count', 'Count of tasks past their due date for the user in a specific org workspace', 'SELECT COUNT(*)::text FROM "07_tasks"."02_fct_tasks" WHERE assigned_user_id = $1 AND org_id = $2 AND workspace_id = $3 AND status_code NOT IN (''completed'', ''cancelled'') AND due_date < NOW() AND is_deleted = FALSE', '["user_id", "org_id", "workspace_id"]'::jsonb, '2', TRUE, '2026-03-16T11:15:59.189218+00:00', '2026-03-16T11:15:59.189218+00:00'),
      ('fe6d57fa-3628-4ac2-b9a2-6ee100039075', 'task.pending_count', 'Pending Task Count', 'Count of open/in-progress tasks assigned to the user in a specific org workspace', 'SELECT COUNT(*)::text FROM "07_tasks"."02_fct_tasks" WHERE assigned_user_id = $1 AND org_id = $2 AND workspace_id = $3 AND status_code NOT IN (''completed'', ''cancelled'') AND is_deleted = FALSE', '["user_id", "org_id", "workspace_id"]'::jsonb, '5', TRUE, '2026-03-16T11:15:59.189218+00:00', '2026-03-16T11:15:59.189218+00:00')
  ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sql_template = EXCLUDED.sql_template, bind_params = EXCLUDED.bind_params, preview_default = EXCLUDED.preview_default, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.10_fct_templates (32 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."10_fct_templates" (id, tenant_key, code, name, description, notification_type_code, channel_code, active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by, org_id, static_variables, category_code)
  VALUES
      ('05ce66bd-4de3-4ed7-960e-7968707f13e7', '__system__', 'global_broadcast_push', 'Global Broadcast (Push)', 'Web push notification for platform-wide announcements.', 'global_broadcast', 'web_push', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.963173', '2026-03-19T16:58:13.963173', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('175beacf-bf60-479d-b6c2-c617c63ad58a', 'default', 'Email_vVerification', 'Email Verification', 'Keys are variable codes used in your template (e.g. {{platform.app_name}}). Static values are defaults when dynamic resolution returns nothing.

', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-19T06:25:47.645579', '2026-03-19T06:25:47.645579', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('1a6d32f0-6671-4ee0-bd3e-8b9caea027a3', 'default', 'robot_test_template_1774187045', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:44:07.998946', '2026-03-22T13:44:31.19762', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('1bb27ec4-623e-4271-bbc3-18a6a3f4b33f', 'default', 'robot_test_template_1774185907', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:25:10.060775', '2026-03-22T13:25:32.956762', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('1e421cc5-a30e-4d4e-ad1b-9ffb22f089de', 'default', 'magic_link_login_email', 'Magic Link Login', 'Sends a magic link for passwordless login to K-Control.', 'magic_link_login', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T03:59:06.53042', '2026-03-20T04:00:55.533539', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('20857b4a-9a1d-4289-a8e4-48e073dc0e14', '__system__', 'email_verification_push', 'Email Verification (Push)', 'Web push notification sent to verify email address.', 'email_verification', 'web_push', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.851129', '2026-03-19T16:58:13.851129', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('215527d2-80b1-4c88-bb80-3fdef4ce4cce', '__system__', 'magic_link_login_email', 'Magic Link Login', 'Sends a magic link for passwordless login.', 'magic_link_login', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-20T03:54:34.804901', '2026-03-20T03:54:34.804901', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('3a851847-0d03-4d06-a80f-315ddb3a91f6', 'default', 'robot_test_template_1773988723', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T06:38:45.297784', '2026-03-20T06:39:07.259459', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('3fabf1eb-e2a0-4840-90b6-2c65a5c7f46e', '__system__', 'org_invite_push', 'Organisation Invite (Push)', 'Web push notification when user is invited to an organisation.', 'org_invite_received', 'web_push', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.908043', '2026-03-19T16:58:13.908043', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('50d67440-9d7c-4731-bbcc-efe046435ed1', 'default', 'robot_test_template_1774430945', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T09:29:07.863794', '2026-03-25T09:29:32.739064', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}', NULL),
      ('526384b1-01d6-4692-85cb-8499b1abbbd5', 'default', 'org_invite', 'Organisation Invite', 'Sent when a user is invited to join an organisation.', 'org_invite_received', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('5a84c59c-21d0-4222-9918-490bb199e0f9', 'default', 'workspace_invite', 'Workspace Invite', 'Sent when a user is added to a workspace.', 'workspace_invite_received', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('5b7bab9d-4f36-42c1-bf0c-5e16dbf5bac5', 'default', 'Email_Verification', 'Email Verification', 'Keys are variable codes used in your template (e.g. {{platform.app_name}}). Static values are defaults when dynamic resolution returns nothing.

', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-19T06:21:25.427275', '2026-03-19T06:21:25.427275', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('5e587fc7-93d2-4fa2-9fd8-42926bdeecda', 'default', 'robot_test_template_1774185125', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:12:07.940624', '2026-03-22T13:12:30.48745', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('604ac4e4-e077-43a6-a52a-27b5bbb5d812', '__system__', 'email_verification_otp', 'Email Verification OTP', 'Sends a 6-digit OTP code for email verification during onboarding.', 'email_verification', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-20T03:39:16.958811', '2026-03-20T03:39:16.958811', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('7ad75562-05c7-4e9d-96dd-109dcdad6ed3', 'default', 'robot_test_template_1774185929', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:25:31.357343', '2026-03-22T13:25:53.255678', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('7f463634-6068-422d-9353-36983e8b919e', 'default', 'email_verification', 'Email Verification', 'Sent to verify a user email address after registration.', 'email_verification', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('8007798b-a4c7-4663-bc4a-39771a1b583c', 'default', 'robot_test_template_1773733027', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:37:09.853065', '2026-03-17T07:37:30.354147', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('8166a55f-00bd-402c-a334-eb3cb702201c', '__system__', 'workspace_invite_push', 'Workspace Invite (Push)', 'Web push notification when user is added to a workspace.', 'workspace_invite_received', 'web_push', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.93531', '2026-03-19T16:58:13.93531', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('97ba7258-78b0-4a60-bf6d-9be6a29b5b81', '__system__', 'login_new_device_push', 'New Device Login (Push)', 'Security alert when login is detected from a new device.', 'login_from_new_device', 'web_push', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.880004', '2026-03-19T16:58:13.880004', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('a2334b60-0a9f-4405-83ca-fcbb79075124', 'default', 'login_new_device', 'Login From New Device', 'Security alert when a login is detected from an unrecognised device or location.', 'login_from_new_device', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('a92fcdb4-aa4f-4361-a845-6683d52bdd01', 'default', 'robot_test_template_1774253729', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T08:15:31.307115', '2026-03-23T08:15:51.564957', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('ae6458b1-5689-4bab-bcd0-2fc947cc3683', 'default', 'global_broadcast', 'Global Broadcast', 'General-purpose broadcast template for platform-wide announcements to all users.', 'global_broadcast', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('b040f4bb-9803-4831-aba0-3f221f1235ba', 'default', 'robot_debug_1774186176', 'Debug Template', '', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:29:37.143579', '2026-03-22T13:29:50.532803', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('b3e50c9b-4e1b-4568-822c-df0d6320d309', 'default', 'robot_test_template_1773988688', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T06:38:10.555502', '2026-03-20T06:38:32.288014', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('c02db7ba-9dec-4a4a-bcd5-d359d3c6dcf5', 'default', 'password_reset', 'Password Reset', 'Sent when a user requests a password reset link.', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('c8ced459-89c1-4e30-953d-53e367ae1cc7', 'default', 'robot_test_template_1774185716', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:21:58.46742', '2026-03-22T13:22:20.938059', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('d3938c74-0575-4981-81a9-74572ab50518', 'default', 'robot_test_template_1774406073', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T02:34:35.986415', '2026-03-25T02:34:59.968071', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}', NULL),
      ('dad0f7a3-5c67-4211-8acb-e6e73a008b49', '__system__', 'password_reset_push', 'Password Reset (Push)', 'Web push notification sent when a password reset is requested.', 'password_reset', 'web_push', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.821413', '2026-03-19T16:58:13.821413', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('ed091f63-43a7-48d6-91c4-11d415798d27', 'default', 'otp_verification_email', 'OTP Verification Email', 'Sends a 6-digit OTP code for email verification during onboarding.', 'email_verification', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T03:56:30.428274', '2026-03-20T03:58:24.425429', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('f7e7bf5f-ae4b-4001-936d-2c96d4a49619', 'default', 'robot_test_template_1774247569', 'Updated Robot Template Name', 'Template created by Robot Framework tests', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T06:32:51.495365', '2026-03-23T06:33:11.614043', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('ff82f804-c17d-4bcd-b9cd-3f6263a33789', 'default', 'robot_debug_1774186150', 'Debug Template', '', 'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:29:11.740897', '2026-03-22T13:29:13.320354', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL, NULL, '{}'::jsonb, NULL)
  ON CONFLICT (tenant_key, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, notification_type_code = EXCLUDED.notification_type_code, channel_code = EXCLUDED.channel_code, active_version_id = EXCLUDED.active_version_id, base_template_id = EXCLUDED.base_template_id, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by, org_id = EXCLUDED.org_id, static_variables = EXCLUDED.static_variables, category_code = EXCLUDED.category_code;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.14_dtl_template_versions (42 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."14_dtl_template_versions" (id, template_id, version_number, subject_line, body_html, body_text, body_short, metadata_json, change_notes, is_active, created_at, created_by)
  VALUES
      ('056d1dde-2295-47b3-a8d8-515ca80e8eb3', 'b3e50c9b-4e1b-4568-822c-df0d6320d309', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-20T06:38:23.9665', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('09e93b99-2799-4309-9854-1d6fb03fd2bf', 'c02db7ba-9dec-4a4a-bcd5-d359d3c6dcf5', 1, 'Reset your {{ platform.name }} password', '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><style>
body{margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrapper{width:100%;background:#f4f6f9;padding:32px 0;}
.card{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.header{background:#0f172a;padding:28px 40px;text-align:center;}
.logo{font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;}
.body{padding:40px;color:#1e293b;font-size:15px;line-height:1.7;}
h1{font-size:22px;font-weight:700;margin:0 0 16px;color:#0f172a;}
.btn{display:inline-block;margin:24px 0;padding:14px 32px;background:#2563eb;color:#fff!important;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;}
.notice{background:#f1f5f9;border-left:4px solid #2563eb;border-radius:4px;padding:14px 18px;margin:20px 0;font-size:14px;color:#475569;}
.divider{border:none;border-top:1px solid #e2e8f0;margin:28px 0;}
.meta{font-size:13px;color:#64748b;}
.footer{padding:24px 40px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#94a3b8;}
.footer a{color:#64748b;text-decoration:none;}
</style></head><body><div class="wrapper"><div class="card">
<div class="header"><div class="logo">{{ platform.name }}</div></div>
<div class="body">
<h1>Reset your password</h1>
<p>Hi {{ user.first_name }},</p>
<p>We received a request to reset the password for your <strong>{{ platform.name }}</strong> account (<strong>{{ user.email }}</strong>).</p>
<p style="text-align:center;"><a class="btn" href="{{ action.reset_url }}">Reset My Password</a></p>
<div class="notice">This link expires in <strong>{{ action.expires_in }}</strong>. If you did not request a password reset, you can safely ignore this email.</div>
<hr class="divider"/>
<p class="meta">Request received from IP <strong>{{ event.ip_address }}</strong>. Not you? <a href="{{ platform.support_url }}">Contact support</a>.</p>
</div>
<div class="footer"><p>&copy; {{ platform.year }} {{ platform.company }}. All rights reserved.<br/><a href="{{ platform.privacy_url }}">Privacy Policy</a></p></div>
</div></div></body></html>', 'Hi {{ user.first_name }},

Reset your {{ platform.name }} password: {{ action.reset_url }}

Expires in {{ action.expires_in }}. If this wasn''t you, ignore this email.', 'Reset your {{ platform.name }} password — link expires in {{ action.expires_in }}.', NULL, 'Initial version', TRUE, '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9'),
      ('1022bd6e-3915-4f33-9e43-8e1b332f85ad', 'a2334b60-0a9f-4405-83ca-fcbb79075124', 1, 'New sign-in to your {{ platform.name }} account', '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><style>
body{margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrapper{width:100%;background:#f4f6f9;padding:32px 0;}
.card{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.header{background:#0f172a;padding:28px 40px;text-align:center;}
.logo{font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;}
.body{padding:40px;color:#1e293b;font-size:15px;line-height:1.7;}
h1{font-size:22px;font-weight:700;margin:0 0 16px;color:#0f172a;}
.btn{display:inline-block;margin:24px 0;padding:14px 32px;background:#dc2626;color:#fff!important;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;}
.notice{background:#fef2f2;border-left:4px solid #dc2626;border-radius:4px;padding:14px 18px;margin:20px 0;font-size:14px;color:#7f1d1d;}
.meta-table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;}
.meta-table td{padding:8px 4px;}
.meta-table tr:nth-child(even) td{background:#f8fafc;}
.meta-table .label{color:#64748b;width:130px;}
.footer{padding:24px 40px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#94a3b8;}
.footer a{color:#64748b;text-decoration:none;}
</style></head><body><div class="wrapper"><div class="card">
<div class="header"><div class="logo">{{ platform.name }}</div></div>
<div class="body">
<h1>New sign-in detected</h1>
<p>Hi {{ user.first_name }},</p>
<p>We noticed a new sign-in to your <strong>{{ platform.name }}</strong> account:</p>
<table class="meta-table">
  <tr><td class="label">Time</td><td><strong>{{ event.timestamp }}</strong></td></tr>
  <tr><td class="label">Device</td><td><strong>{{ event.device }}</strong></td></tr>
  <tr><td class="label">Browser</td><td><strong>{{ event.browser }}</strong></td></tr>
  <tr><td class="label">Location</td><td><strong>{{ event.location }}</strong></td></tr>
  <tr><td class="label">IP Address</td><td><strong>{{ event.ip_address }}</strong></td></tr>
</table>
<div class="notice"><strong>Not you?</strong> Change your password immediately and contact support.</div>
<p style="text-align:center;"><a class="btn" href="{{ action.secure_account_url }}">Secure My Account</a></p>
</div>
<div class="footer"><p>&copy; {{ platform.year }} {{ platform.company }}. All rights reserved.<br/><a href="{{ platform.privacy_url }}">Privacy Policy</a></p></div>
</div></div></body></html>', 'Hi {{ user.first_name }},

New sign-in to your {{ platform.name }} account.
Time: {{ event.timestamp }}
Device: {{ event.device }}
Location: {{ event.location }}
IP: {{ event.ip_address }}

Not you? Secure your account: {{ action.secure_account_url }}', 'New sign-in to your account from {{ event.location }}.', NULL, 'Initial version', TRUE, '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9'),
      ('1073e024-0aa3-4251-a7fa-27e5e057cf93', '1e421cc5-a30e-4d4e-ad1b-9ffb22f089de', 1, 'Your Magic Link — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Magic Link Login</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We received a request to sign in to your K-Control account. Click the button below to log in securely without a password.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This link expires in {{ magic_link.expires_in }}.</strong> If you did not request this link, you can safely ignore this email.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ magic_link.url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Sign In with Magic Link</a>
      </div>
      <div style="margin-top:24px;font-size:1em;">
        <span style="font-weight:600;">Best regards,</span><br>
        <span style="color:#295cf6;font-weight:700;">Kreesalis Team</span>
      </div>
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:28px 0;">
      <div style="color:#888;font-size:0.9em;line-height:1.6;margin-bottom:4px;">
        <strong>Disclaimer:</strong> This email may contain confidential or proprietary information intended only for the recipient. If you are not the intended recipient, please delete this email immediately. Unauthorized copying, disclosure, or distribution is prohibited.
      </div>
    </div>
  </div>
</body>
</html>', 'Hi {{ user.first_name }},

We received a request to sign in to your K-Control account.

Click here to sign in: {{ magic_link.url }}

This link expires in {{ magic_link.expires_in }}.

If you did not request this link, you can safely ignore this email.

Best regards,
Kreesalis Team', 'Click to sign in to K-Control. Link expires in {{ magic_link.expires_in }}.', NULL, 'Initial version - styled magic link email matching password reset design', TRUE, '2026-03-20T04:00:55.533539', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('210cc632-82d5-410d-91d5-d44e57349d07', '5e587fc7-93d2-4fa2-9fd8-42926bdeecda', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-22T13:12:22.056267', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('2a68ebd4-f8ec-4d4b-9516-ccf61933cca0', '1bb27ec4-623e-4271-bbc3-18a6a3f4b33f', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-22T13:25:24.257989', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('2c5d5e37-1f11-4126-bb0b-a1616290241a', 'f7e7bf5f-ae4b-4001-936d-2c96d4a49619', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-23T06:33:01.353376', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('30ff9e55-0853-420e-9026-99612e282220', 'a92fcdb4-aa4f-4361-a845-6683d52bdd01', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-23T08:15:41.214681', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('31194a33-26e8-4d16-ba0c-9b123d7a4bae', 'ae6458b1-5689-4bab-bcd0-2fc947cc3683', 1, '{{ broadcast.subject }}', '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><style>
body{margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrapper{width:100%;background:#f4f6f9;padding:32px 0;}
.card{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.header{background:#0f172a;padding:28px 40px;text-align:center;}
.logo{font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;}
.body{padding:40px;color:#1e293b;font-size:15px;line-height:1.7;}
h1{font-size:22px;font-weight:700;margin:0 0 16px;color:#0f172a;}
.divider{border:none;border-top:1px solid #e2e8f0;margin:28px 0;}
.meta{font-size:13px;color:#64748b;}
.footer{padding:24px 40px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#94a3b8;}
.footer a{color:#64748b;text-decoration:none;}
</style></head><body><div class="wrapper"><div class="card">
<div class="header"><div class="logo">{{ platform.name }}</div></div>
<div class="body">
<h1>{{ broadcast.headline }}</h1>
<p>Hi {{ user.first_name }},</p>
{{ broadcast.body_html }}
<hr class="divider"/>
<p class="meta">You are receiving this because you are a member of <strong>{{ platform.name }}</strong>. <a href="{{ platform.unsubscribe_url }}">Manage preferences</a>.</p>
</div>
<div class="footer"><p>&copy; {{ platform.year }} {{ platform.company }}. All rights reserved.<br/><a href="{{ platform.privacy_url }}">Privacy Policy</a> &middot; <a href="{{ platform.unsubscribe_url }}">Unsubscribe</a></p></div>
</div></div></body></html>', 'Hi {{ user.first_name }},

{{ broadcast.body_text }}

-- The {{ platform.name }} Team', '{{ broadcast.headline }}', NULL, 'Initial version', TRUE, '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9'),
      ('37971cd3-17ac-409e-b4e1-157ae226ffab', 'f7e7bf5f-ae4b-4001-936d-2c96d4a49619', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-23T06:33:04.226327', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('3d48e41f-7861-4609-b072-0a36cb532c14', '3a851847-0d03-4d06-a80f-315ddb3a91f6', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-20T06:38:55.97358', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('4585763e-2a1e-4d56-b97e-3458da7940a1', '7f463634-6068-422d-9353-36983e8b919e', 1, 'Verify your {{ platform.name }} email address', '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><style>
body{margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrapper{width:100%;background:#f4f6f9;padding:32px 0;}
.card{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.header{background:#0f172a;padding:28px 40px;text-align:center;}
.logo{font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;}
.body{padding:40px;color:#1e293b;font-size:15px;line-height:1.7;}
h1{font-size:22px;font-weight:700;margin:0 0 16px;color:#0f172a;}
.btn{display:inline-block;margin:24px 0;padding:14px 32px;background:#16a34a;color:#fff!important;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;}
.notice{background:#f1f5f9;border-left:4px solid #16a34a;border-radius:4px;padding:14px 18px;margin:20px 0;font-size:14px;color:#475569;}
.meta{font-size:13px;color:#64748b;}
.footer{padding:24px 40px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#94a3b8;}
.footer a{color:#64748b;text-decoration:none;}
</style></head><body><div class="wrapper"><div class="card">
<div class="header"><div class="logo">{{ platform.name }}</div></div>
<div class="body">
<h1>Welcome to {{ platform.name }}!</h1>
<p>Hi {{ user.first_name }},</p>
<p>Thanks for signing up. Please verify your email address to activate your account.</p>
<p style="text-align:center;"><a class="btn" href="{{ action.verify_url }}">Verify My Email</a></p>
<div class="notice">This link expires in <strong>{{ action.expires_in }}</strong>. If you did not create an account, please ignore this email.</div>
<p class="meta">Can''t click the button? Copy and paste: {{ action.verify_url }}</p>
</div>
<div class="footer"><p>&copy; {{ platform.year }} {{ platform.company }}. All rights reserved.<br/><a href="{{ platform.privacy_url }}">Privacy Policy</a></p></div>
</div></div></body></html>', 'Hi {{ user.first_name }},

Welcome to {{ platform.name }}! Verify your email: {{ action.verify_url }}

Expires in {{ action.expires_in }}.', 'Verify your {{ platform.name }} email to activate your account.', NULL, 'Initial version', TRUE, '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9'),
      ('55d7f8c5-e13a-4ca6-a99c-f54806210187', 'dad0f7a3-5c67-4211-8acb-e6e73a008b49', 1, 'Password Reset Requested', NULL, 'Click to reset your password. This link expires in {{ action.expires_in }}.', 'A password reset link has been sent. Tap to open.', NULL, NULL, TRUE, '2026-03-19T16:58:13.821413', NULL),
      ('570d371b-88c7-4cb6-8dc5-011bb25a4df5', 'ed091f63-43a7-48d6-91c4-11d415798d27', 1, 'Your Verification OTP — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Your Verification OTP</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Please use the OTP below to complete your email verification:</p>
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <div style="display:inline-block;background:#eaf3fb;color:#295cf6;border-radius:10px;padding:18px 48px;font-size:32px;font-weight:600;letter-spacing:6px;">{{ otp_code }}</div>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This OTP expires in 5 minutes.</strong> If you did not request this code, you can safely ignore this email.
      </div>
      <div style="margin-top:24px;font-size:1em;">
        <span style="font-weight:600;">Best regards,</span><br>
        <span style="color:#295cf6;font-weight:700;">Kreesalis Team</span>
      </div>
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:28px 0;">
      <div style="color:#888;font-size:0.9em;line-height:1.6;margin-bottom:4px;">
        <strong>Disclaimer:</strong> This email may contain confidential or proprietary information intended only for the recipient. If you are not the intended recipient, please delete this email immediately. Unauthorized copying, disclosure, or distribution is prohibited.
      </div>
    </div>
  </div>
</body>
</html>', 'Hi {{ user.first_name | default("there") }},

Your verification OTP is: {{ otp_code }}

This OTP expires in 5 minutes.

If you did not request this code, you can safely ignore this email.

Best regards,
Kreesalis Team', 'Your OTP is {{ otp_code }}. Expires in 5 minutes.', NULL, 'Initial version - styled OTP email matching password reset design', TRUE, '2026-03-20T03:58:24.425429', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('5f88991e-c662-4601-b6a8-8084f58008d2', '3fabf1eb-e2a0-4840-90b6-2c65a5c7f46e', 1, 'You have been invited to an organisation', NULL, 'You have been invited to join an organisation on K-Control.', 'You have a new organisation invitation. Tap to view.', NULL, NULL, TRUE, '2026-03-19T16:58:13.908043', NULL),
      ('610ac4ec-ed9a-4231-8d68-b421ed5adbab', 'c8ced459-89c1-4e30-953d-53e367ae1cc7', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-22T13:22:12.619465', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('6d276a23-df1e-4551-a2f2-fcb7e233897b', '20857b4a-9a1d-4289-a8e4-48e073dc0e14', 1, 'Verify Your Email', NULL, 'Click the link to verify your email address.', 'Please verify your email address. Tap to open.', NULL, NULL, TRUE, '2026-03-19T16:58:13.851129', NULL),
      ('74e1f942-1ce8-4084-86cc-4d99c5de5a72', '1a6d32f0-6671-4ee0-bd3e-8b9caea027a3', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-22T13:44:19.297948', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('7704fc72-b12b-4862-a4dd-b5e9714cad0c', 'ff82f804-c17d-4bcd-b9cd-3f6263a33789', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Debug version', TRUE, '2026-03-22T13:29:13.320354', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('79bd9a11-262a-4045-a498-87b98c5b9819', '526384b1-01d6-4692-85cb-8499b1abbbd5', 1, 'You''ve been invited to join {{ org.name }} on {{ platform.name }}', '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><style>
body{margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrapper{width:100%;background:#f4f6f9;padding:32px 0;}
.card{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.header{background:#0f172a;padding:28px 40px;text-align:center;}
.logo{font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;}
.body{padding:40px;color:#1e293b;font-size:15px;line-height:1.7;}
h1{font-size:22px;font-weight:700;margin:0 0 16px;color:#0f172a;}
.btn{display:inline-block;margin:24px 0;padding:14px 32px;background:#7c3aed;color:#fff!important;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;}
.notice{background:#f5f3ff;border-left:4px solid #7c3aed;border-radius:4px;padding:14px 18px;margin:20px 0;font-size:14px;color:#4c1d95;}
.divider{border:none;border-top:1px solid #e2e8f0;margin:28px 0;}
.meta{font-size:13px;color:#64748b;}
.footer{padding:24px 40px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#94a3b8;}
.footer a{color:#64748b;text-decoration:none;}
</style></head><body><div class="wrapper"><div class="card">
<div class="header"><div class="logo">{{ platform.name }}</div></div>
<div class="body">
<h1>You have been invited!</h1>
<p>Hi {{ user.first_name }},</p>
<p><strong>{{ inviter.display_name }}</strong> has invited you to join <strong>{{ org.name }}</strong> on {{ platform.name }} as a <strong>{{ invite.role }}</strong>.</p>
<p style="text-align:center;"><a class="btn" href="{{ action.accept_url }}">Accept Invitation</a></p>
<div class="notice">This invitation expires on <strong>{{ invite.expires_at }}</strong>. If you don''t have a {{ platform.name }} account yet, you''ll be prompted to create one.</div>
<hr class="divider"/>
<p class="meta">Not expecting this? Safely ignore this email or <a href="{{ platform.support_url }}">contact support</a>.</p>
</div>
<div class="footer"><p>&copy; {{ platform.year }} {{ platform.company }}. All rights reserved.<br/><a href="{{ platform.privacy_url }}">Privacy Policy</a></p></div>
</div></div></body></html>', 'Hi {{ user.first_name }},

{{ inviter.display_name }} invited you to join {{ org.name }} on {{ platform.name }} as {{ invite.role }}.

Accept: {{ action.accept_url }}
Expires: {{ invite.expires_at }}', '{{ inviter.display_name }} invited you to {{ org.name }} — expires {{ invite.expires_at }}.', NULL, 'Initial version', TRUE, '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9'),
      ('7a191ac8-4f8a-42d1-af99-5bd97a59b2f2', '1bb27ec4-623e-4271-bbc3-18a6a3f4b33f', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-22T13:25:20.984701', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('7a20a753-d166-491a-bf3b-672c8be7c3b4', '3a851847-0d03-4d06-a80f-315ddb3a91f6', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-20T06:38:58.793467', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('83186604-66a4-4c30-9a3f-e3664608545f', '8007798b-a4c7-4663-bc4a-39771a1b583c', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-17T07:37:22.883013', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('8351ec51-d6bf-4f07-8a7b-61586a74b0f0', '7ad75562-05c7-4e9d-96dd-109dcdad6ed3', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-22T13:25:41.994274', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('8d17ec6b-829b-4faf-af91-0e6f812b350a', '1a6d32f0-6671-4ee0-bd3e-8b9caea027a3', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-22T13:44:22.682204', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('973573db-4797-44d8-ba62-46684434daa8', '8166a55f-00bd-402c-a334-eb3cb702201c', 1, 'You have been added to a workspace', NULL, 'You have been added to a workspace on K-Control.', 'You have been added to a new workspace. Tap to open.', NULL, NULL, TRUE, '2026-03-19T16:58:13.93531', NULL),
      ('9b2d816d-58df-4e53-8307-3869912d8582', '05ce66bd-4de3-4ed7-960e-7968707f13e7', 1, 'K-Control Platform Announcement', NULL, 'There is a new platform announcement from K-Control.', 'A new platform announcement is available.', NULL, NULL, TRUE, '2026-03-19T16:58:13.963173', NULL),
      ('a5e4f0f7-e186-4d51-8aa2-5268979a66c1', 'b040f4bb-9803-4831-aba0-3f221f1235ba', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Debug version', TRUE, '2026-03-22T13:29:50.532803', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('aba0be72-938a-418d-9db2-25aabf1a4338', '50d67440-9d7c-4731-bbcc-efe046435ed1', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-25T09:29:22.524817', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('afa8c69b-b194-4f42-ba21-1727588a2f53', '8007798b-a4c7-4663-bc4a-39771a1b583c', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-17T07:37:20.075162', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('b36264f0-2e5a-4f2d-a985-d6eabbdd9b36', 'b3e50c9b-4e1b-4568-822c-df0d6320d309', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-20T06:38:21.02807', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('b3b4428a-3c2c-4748-a58b-2ec167c031a5', 'd3938c74-0575-4981-81a9-74572ab50518', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-25T02:34:50.892414', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('c37bb95e-a9f4-4aea-ab43-673066a79ecc', 'c8ced459-89c1-4e30-953d-53e367ae1cc7', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-22T13:22:09.430754', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('c8928edf-ddcb-4cc7-a31e-864855dd48d9', '604ac4e4-e077-43a6-a52a-27b5bbb5d812', 1, 'Your Verification OTP — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Your Verification OTP</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Please use the OTP below to complete your email verification:</p>
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <div style="display:inline-block;background:#eaf3fb;color:#295cf6;border-radius:10px;padding:18px 48px;font-size:32px;font-weight:600;letter-spacing:6px;">{{ otp_code }}</div>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This OTP expires in 5 minutes.</strong> If you did not request this code, you can safely ignore this email.
      </div>
      <div style="margin-top:24px;font-size:1em;">
        <span style="font-weight:600;">Best regards,</span><br>
        <span style="color:#295cf6;font-weight:700;">Kreesalis Team</span>
      </div>
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:28px 0;">
      <div style="color:#888;font-size:0.9em;line-height:1.6;margin-bottom:4px;">
        <strong>Disclaimer:</strong> This email may contain confidential or proprietary information intended only for the recipient. If you are not the intended recipient, please delete this email immediately. Unauthorized copying, disclosure, or distribution is prohibited.
      </div>
    </div>
  </div>
</body>
</html>', 'Hi {{ user.first_name | default("there") }},

Your verification OTP is: {{ otp_code }}

This OTP expires in 5 minutes.

If you did not request this code, you can safely ignore this email.

Best regards,
Kreesalis Team', 'Your OTP is {{ otp_code }}. Expires in 5 minutes.', NULL, NULL, TRUE, '2026-03-20T03:39:16.958811', NULL),
      ('c97f70ec-ac82-4edf-a1bc-d4e07578c9f8', '7ad75562-05c7-4e9d-96dd-109dcdad6ed3', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-22T13:25:44.81753', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('d31a263a-3bcd-41b8-8ac9-4bbf071f2f0a', '215527d2-80b1-4c88-bb80-3fdef4ce4cce', 1, 'Your Magic Link — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Magic Link Login</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We received a request to sign in to your K-Control account. Click the button below to log in securely without a password.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This link expires in {{ magic_link.expires_in }}.</strong> If you did not request this link, you can safely ignore this email.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ magic_link.url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Sign In with Magic Link</a>
      </div>
      <div style="margin-top:24px;font-size:1em;">
        <span style="font-weight:600;">Best regards,</span><br>
        <span style="color:#295cf6;font-weight:700;">Kreesalis Team</span>
      </div>
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:28px 0;">
      <div style="color:#888;font-size:0.9em;line-height:1.6;margin-bottom:4px;">
        <strong>Disclaimer:</strong> This email may contain confidential or proprietary information intended only for the recipient. If you are not the intended recipient, please delete this email immediately. Unauthorized copying, disclosure, or distribution is prohibited.
      </div>
    </div>
  </div>
</body>
</html>', 'Hi {{ user.first_name }},

We received a request to sign in to your K-Control account.

Click here to sign in: {{ magic_link.url }}

This link expires in {{ magic_link.expires_in }}.

If you did not request this link, you can safely ignore this email.

Best regards,
Kreesalis Team', 'Click to sign in to K-Control. Link expires in {{ magic_link.expires_in }}.', NULL, NULL, TRUE, '2026-03-20T03:54:34.804901', NULL),
      ('d61dc5de-f549-46c3-a141-7077a70f9726', '97ba7258-78b0-4a60-bf6d-9be6a29b5b81', 1, 'New Device Login Detected', NULL, 'A login was detected from a new device. If this was not you, secure your account immediately.', 'A new login was detected on your account. Tap to review.', NULL, NULL, TRUE, '2026-03-19T16:58:13.880004', NULL),
      ('da7df34e-af38-4525-be97-d6e83db25a7a', '5e587fc7-93d2-4fa2-9fd8-42926bdeecda', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-22T13:12:18.958168', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('e88e6d5f-8383-4f81-a9a0-4b146b2d3589', 'a92fcdb4-aa4f-4361-a845-6683d52bdd01', 2, 'Updated: Hello {{user.display_name}}', '<h1>Updated Hello {{user.display_name}}</h1>', 'Updated Hello {{user.display_name}}', NULL, NULL, 'Second version with updated subject', TRUE, '2026-03-23T08:15:43.84713', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('ec38ba31-0230-48af-b238-842b00522e24', 'd3938c74-0575-4981-81a9-74572ab50518', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-25T02:34:47.545147', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('ee9a3051-0358-4f8c-97b0-ff0b207ff5af', '50d67440-9d7c-4731-bbcc-efe046435ed1', 1, 'Hello {{user.display_name}} from {{platform.name}}', '<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>', 'Hello {{user.display_name}}, Token: {{token}}', 'Token: {{token}}', NULL, 'Initial version from Robot tests', TRUE, '2026-03-25T09:29:19.881933', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8'),
      ('f1e14cc0-2ecc-4e12-a6d7-cc2623f2acca', '5a84c59c-21d0-4222-9918-490bb199e0f9', 1, 'You''ve been added to the {{ workspace.name }} workspace', '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><style>
body{margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrapper{width:100%;background:#f4f6f9;padding:32px 0;}
.card{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.header{background:#0f172a;padding:28px 40px;text-align:center;}
.logo{font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;}
.body{padding:40px;color:#1e293b;font-size:15px;line-height:1.7;}
h1{font-size:22px;font-weight:700;margin:0 0 16px;color:#0f172a;}
.btn{display:inline-block;margin:24px 0;padding:14px 32px;background:#0891b2;color:#fff!important;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;}
.meta{font-size:13px;color:#64748b;}
.footer{padding:24px 40px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#94a3b8;}
.footer a{color:#64748b;text-decoration:none;}
</style></head><body><div class="wrapper"><div class="card">
<div class="header"><div class="logo">{{ platform.name }}</div></div>
<div class="body">
<h1>Workspace access granted</h1>
<p>Hi {{ user.first_name }},</p>
<p>You have been added to the <strong>{{ workspace.name }}</strong> workspace in <strong>{{ org.name }}</strong> by <strong>{{ inviter.display_name }}</strong> with the role <strong>{{ invite.role }}</strong>.</p>
<p style="text-align:center;"><a class="btn" href="{{ action.workspace_url }}">Open Workspace</a></p>
<p class="meta">Believe this is a mistake? Contact your organisation administrator or <a href="{{ platform.support_url }}">our support team</a>.</p>
</div>
<div class="footer"><p>&copy; {{ platform.year }} {{ platform.company }}. All rights reserved.<br/><a href="{{ platform.privacy_url }}">Privacy Policy</a></p></div>
</div></div></body></html>', 'Hi {{ user.first_name }},

You have been added to {{ workspace.name }} in {{ org.name }} as {{ invite.role }}.

Open it: {{ action.workspace_url }}', 'You''ve been added to {{ workspace.name }} in {{ org.name }}.', NULL, 'Initial version', TRUE, '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9')
  ON CONFLICT (template_id, version_number) DO UPDATE SET subject_line = EXCLUDED.subject_line, body_html = EXCLUDED.body_html, body_text = EXCLUDED.body_text, body_short = EXCLUDED.body_short, metadata_json = EXCLUDED.metadata_json, change_notes = EXCLUDED.change_notes, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- Fix FK ordering: set active_version_id AFTER versions exist
DO $$ BEGIN
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '9b2d816d-58df-4e53-8307-3869912d8582' WHERE id = '05ce66bd-4de3-4ed7-960e-7968707f13e7' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '74e1f942-1ce8-4084-86cc-4d99c5de5a72' WHERE id = '1a6d32f0-6671-4ee0-bd3e-8b9caea027a3' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '7a191ac8-4f8a-42d1-af99-5bd97a59b2f2' WHERE id = '1bb27ec4-623e-4271-bbc3-18a6a3f4b33f' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '1073e024-0aa3-4251-a7fa-27e5e057cf93' WHERE id = '1e421cc5-a30e-4d4e-ad1b-9ffb22f089de' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '6d276a23-df1e-4551-a2f2-fcb7e233897b' WHERE id = '20857b4a-9a1d-4289-a8e4-48e073dc0e14' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'd31a263a-3bcd-41b8-8ac9-4bbf071f2f0a' WHERE id = '215527d2-80b1-4c88-bb80-3fdef4ce4cce' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '3d48e41f-7861-4609-b072-0a36cb532c14' WHERE id = '3a851847-0d03-4d06-a80f-315ddb3a91f6' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '5f88991e-c662-4601-b6a8-8084f58008d2' WHERE id = '3fabf1eb-e2a0-4840-90b6-2c65a5c7f46e' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'ee9a3051-0358-4f8c-97b0-ff0b207ff5af' WHERE id = '50d67440-9d7c-4731-bbcc-efe046435ed1' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '79bd9a11-262a-4045-a498-87b98c5b9819' WHERE id = '526384b1-01d6-4692-85cb-8499b1abbbd5' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'f1e14cc0-2ecc-4e12-a6d7-cc2623f2acca' WHERE id = '5a84c59c-21d0-4222-9918-490bb199e0f9' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'da7df34e-af38-4525-be97-d6e83db25a7a' WHERE id = '5e587fc7-93d2-4fa2-9fd8-42926bdeecda' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'c8928edf-ddcb-4cc7-a31e-864855dd48d9' WHERE id = '604ac4e4-e077-43a6-a52a-27b5bbb5d812' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '8351ec51-d6bf-4f07-8a7b-61586a74b0f0' WHERE id = '7ad75562-05c7-4e9d-96dd-109dcdad6ed3' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '4585763e-2a1e-4d56-b97e-3458da7940a1' WHERE id = '7f463634-6068-422d-9353-36983e8b919e' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'afa8c69b-b194-4f42-ba21-1727588a2f53' WHERE id = '8007798b-a4c7-4663-bc4a-39771a1b583c' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '973573db-4797-44d8-ba62-46684434daa8' WHERE id = '8166a55f-00bd-402c-a334-eb3cb702201c' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'd61dc5de-f549-46c3-a141-7077a70f9726' WHERE id = '97ba7258-78b0-4a60-bf6d-9be6a29b5b81' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '1022bd6e-3915-4f33-9e43-8e1b332f85ad' WHERE id = 'a2334b60-0a9f-4405-83ca-fcbb79075124' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '30ff9e55-0853-420e-9026-99612e282220' WHERE id = 'a92fcdb4-aa4f-4361-a845-6683d52bdd01' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '31194a33-26e8-4d16-ba0c-9b123d7a4bae' WHERE id = 'ae6458b1-5689-4bab-bcd0-2fc947cc3683' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'a5e4f0f7-e186-4d51-8aa2-5268979a66c1' WHERE id = 'b040f4bb-9803-4831-aba0-3f221f1235ba' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'b36264f0-2e5a-4f2d-a985-d6eabbdd9b36' WHERE id = 'b3e50c9b-4e1b-4568-822c-df0d6320d309' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '09e93b99-2799-4309-9854-1d6fb03fd2bf' WHERE id = 'c02db7ba-9dec-4a4a-bcd5-d359d3c6dcf5' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'c37bb95e-a9f4-4aea-ab43-673066a79ecc' WHERE id = 'c8ced459-89c1-4e30-953d-53e367ae1cc7' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = 'ec38ba31-0230-48af-b238-842b00522e24' WHERE id = 'd3938c74-0575-4981-81a9-74572ab50518' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '55d7f8c5-e13a-4ca6-a99c-f54806210187' WHERE id = 'dad0f7a3-5c67-4211-8acb-e6e73a008b49' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '570d371b-88c7-4cb6-8dc5-011bb25a4df5' WHERE id = 'ed091f63-43a7-48d6-91c4-11d415798d27' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '2c5d5e37-1f11-4126-bb0b-a1616290241a' WHERE id = 'f7e7bf5f-ae4b-4001-936d-2c96d4a49619' AND active_version_id IS NULL;
  UPDATE "03_notifications"."10_fct_templates" SET active_version_id = '7704fc72-b12b-4862-a4dd-b5e9714cad0c' WHERE id = 'ff82f804-c17d-4bcd-b9cd-3f6263a33789' AND active_version_id IS NULL;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation THEN NULL;
END $$;


-- 03_notifications.15_dtl_template_placeholders (5 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."15_dtl_template_placeholders" (id, template_id, variable_key_code, is_required, default_value, created_at, updated_at)
  VALUES
      ('059dca0a-1ddd-45ff-af71-992942917671', '215527d2-80b1-4c88-bb80-3fdef4ce4cce', 'user.first_name', FALSE, 'there', '2026-03-20T03:54:34.804901', '2026-03-20T03:54:34.804901'),
      ('12f7f95f-3c0b-441f-8c19-8e9d18c2e855', '215527d2-80b1-4c88-bb80-3fdef4ce4cce', 'magic_link.expires_in', FALSE, '24 hours', '2026-03-20T03:54:34.804901', '2026-03-20T03:54:34.804901'),
      ('282866da-5335-47f7-9530-87a510126028', '215527d2-80b1-4c88-bb80-3fdef4ce4cce', 'magic_link.url', TRUE, NULL, '2026-03-20T03:54:34.804901', '2026-03-20T03:54:34.804901'),
      ('43ac8725-ae58-481f-8e83-9109e05e169a', '604ac4e4-e077-43a6-a52a-27b5bbb5d812', 'otp_code', TRUE, NULL, '2026-03-20T03:39:16.958811', '2026-03-20T03:39:16.958811'),
      ('50b1740b-4c16-4334-a934-1318efc648b1', '604ac4e4-e077-43a6-a52a-27b5bbb5d812', 'user.first_name', FALSE, 'there', '2026-03-20T03:39:16.958811', '2026-03-20T03:39:16.958811')
  ON CONFLICT (template_id, variable_key_code) DO UPDATE SET is_required = EXCLUDED.is_required, default_value = EXCLUDED.default_value, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.11_fct_notification_rules (32 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."11_fct_notification_rules" (id, tenant_key, code, name, description, source_event_type, source_event_category, notification_type_code, recipient_strategy, recipient_filter_json, priority_code, delay_seconds, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
  VALUES
      ('11eb8495-8ae3-491d-b37a-a003a2d8d76c', 'default', 'robot_rule_1773658049', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:47:33.091883', '2026-03-16T10:48:07.359208', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('18f0c75e-edae-46bf-8ec3-ebba8e7303e4', 'default', 'robot_rule_1774406123', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T02:35:25.327941', '2026-03-25T02:35:46.149318', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('1ac4c744-37b5-4fef-85e7-891b7112e3cc', 'default', 'robot_rule_1774185979', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:26:21.438877', '2026-03-22T13:26:40.649573', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('24691c00-aea9-4378-8ce2-1812625b5453', 'default', 'robot_rule_1773478150', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:49:10.756612', '2026-03-14T08:49:18.83006', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('273fb676-c284-4668-b543-a8ee99890506', 'default', 'robot_rule_1773574508', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T11:35:08.808133', '2026-03-15T11:35:18.054649', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('30000000-0000-0000-0000-000000000001', 'default', 'rule_password_reset', 'Password Reset Notification', 'Send password reset link/OTP to user', 'password_reset_requested', 'auth', 'password_reset', 'actor', NULL, 'critical', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000002', 'default', 'rule_email_verification', 'Email Verification Notification', 'Send email verification link to user', 'email_verification_requested', 'auth', 'email_verification', 'actor', NULL, 'critical', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000003', 'default', 'rule_password_changed', 'Password Changed Confirmation', 'Confirm password change to user', 'password_changed', 'auth', 'password_changed', 'actor', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000004', 'default', 'rule_email_verified', 'Email Verified Confirmation', 'Confirm email verification to user', 'email_verification_completed', 'auth', 'email_verified', 'actor', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000005', 'default', 'rule_api_key_created', 'API Key Created Alert', 'Alert user when new API key is created', 'api_key_created', 'auth', 'api_key_created', 'actor', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000006', 'default', 'rule_org_invite', 'Organization Invite', 'Notify user of organization invitation', 'invite_created', 'org', 'org_invite_received', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000007', 'default', 'rule_org_member_added', 'Org Member Added', 'Notify org admins when member is added', 'org_member_added', 'org', 'org_member_added', 'org_members', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000008', 'default', 'rule_workspace_member_added', 'Workspace Member Added', 'Notify workspace admins when member is added', 'workspace_member_added', 'workspace', 'workspace_member_added', 'workspace_members', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000009', 'default', 'rule_role_changed', 'Role Changed', 'Notify user when their role changes', 'group_role_assigned', 'access', 'role_changed', 'actor', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000010', 'default', 'campaign_inactivity_7d', 'Inactivity Reminder (7 days)', 'Send reminder to users inactive for 7+ days', '__campaign__', NULL, 'inactivity_reminder', 'all_users', NULL, 'low', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975', NULL, NULL, NULL, NULL),
      ('38fe904f-e2ba-4c20-af67-87c5bdb81cad', 'default', 'robot_rule_1774247624', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T06:33:47.348546', '2026-03-23T06:34:04.696539', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('461b758c-f394-4af8-b589-c2799236d412', 'default', 'robot_rule_1773478311', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:51:51.871451', '2026-03-14T08:51:59.660269', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('66af3cda-1e52-4992-883e-46eab3d16726', 'default', 'robot_rule_1774185764', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:22:47.180143', '2026-03-22T13:23:06.259346', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('6821d950-d8fd-43ed-aec1-d45ebd86e4b9', 'default', 'robot_rule_1774187120', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:45:22.987072', '2026-03-22T13:45:42.501209', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('69fa29c7-b531-42ed-ace6-08f6b816ec5c', 'default', 'robot_rule_1773480999', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T09:36:40.197239', '2026-03-14T09:36:48.083957', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('704c7f68-c70c-43b6-abe8-6781b433d56b', 'default', 'robot_rule_1773574071', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T11:27:51.854521', '2026-03-15T11:28:00.1859', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('75d61718-2662-4725-811d-4c6f8901959f', 'default', 'robot_rule_1773573933', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T11:25:34.239862', '2026-03-15T11:25:43.176511', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('7b3cb240-8c41-454b-ad1a-34bf9ea44102', 'default', 'robot_rule_1774430996', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T09:29:58.601968', '2026-03-25T09:30:17.056132', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('7e4dc482-8e1a-414b-8014-ed5e6061dbd8', 'default', 'robot_rule_1773733072', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:37:54.320718', '2026-03-17T07:38:11.771689', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('8317964d-f64f-4728-802f-535e14ee6b71', 'default', 'robot_rule_1774185174', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:12:57.046509', '2026-03-22T13:13:16.475623', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('9cbc0780-9750-414a-8802-f612230402ad', 'default', 'robot_rule_1773988736', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T06:38:58.939806', '2026-03-20T06:39:18.270401', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('a1f14324-d6cd-4669-8a74-ed653b609543', 'default', 'robot_rule_1773573523', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T11:18:44.082734', '2026-03-15T11:18:52.699843', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('c3fe7e32-d9bb-4379-93c8-aa4ce58df13d', 'default', 'robot_rule_1774185957', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:25:59.970308', '2026-03-22T13:26:20.33479', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('d53d5196-0c82-44d7-aabd-c20d219f05c0', 'default', 'robot_rule_1773481229', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T09:40:30.5937', '2026-03-14T09:40:39.114883', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('dec71fae-7a44-4c8c-b626-072e885d2163', 'default', 'rule_magic_link_login', 'Magic Link Login Notification', 'Send magic link email when user requests passwordless login', 'magic_link_requested', 'auth', 'magic_link_login', 'actor', NULL, 'critical', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-20T03:54:34.828026', '2026-03-20T03:54:34.828026', NULL, NULL, NULL, NULL),
      ('e5e6f980-2b44-4f8a-98d7-e15cf0808b49', 'default', 'robot_rule_1773988770', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T06:39:32.889238', '2026-03-20T06:39:51.282879', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('e9c2f1a6-b435-4d74-bb5c-0ff3bd6f68fd', 'default', 'robot_rule_1774253784', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T08:16:26.84387', '2026-03-23T08:16:44.220996', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL)
  ON CONFLICT (tenant_key, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, source_event_type = EXCLUDED.source_event_type, source_event_category = EXCLUDED.source_event_category, notification_type_code = EXCLUDED.notification_type_code, recipient_strategy = EXCLUDED.recipient_strategy, recipient_filter_json = EXCLUDED.recipient_filter_json, priority_code = EXCLUDED.priority_code, delay_seconds = EXCLUDED.delay_seconds, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.18_lnk_notification_rule_channels (43 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."18_lnk_notification_rule_channels" (id, rule_id, channel_code, template_code, is_active, created_at, updated_at)
  VALUES
      ('0407b9f3-46cb-47eb-954b-f95983f38935', '38fe904f-e2ba-4c20-af67-87c5bdb81cad', 'email', 'robot_test_template_1774247569', TRUE, '2026-03-23T06:34:10.333567', '2026-03-23T06:34:10.333567'),
      ('0df29cfb-cd48-49d9-97c4-1c3a7df34f10', '30000000-0000-0000-0000-000000000002', 'email', 'otp_verification_email', TRUE, '2026-03-20T04:27:43.910015', '2026-03-20T04:27:43.910015'),
      ('0eb02d92-40c6-46ad-9278-89ce5dcef73e', '8317964d-f64f-4728-802f-535e14ee6b71', 'web_push', NULL, TRUE, '2026-03-22T13:13:25.560446', '2026-03-22T13:13:25.560446'),
      ('13334934-1406-4cbd-a2e6-963f94d73ca9', '7e4dc482-8e1a-414b-8014-ed5e6061dbd8', 'email', 'robot_test_template_1773733027', TRUE, '2026-03-17T07:38:14.889228', '2026-03-17T07:38:14.889228'),
      ('137b901c-3bd6-4592-9942-37706018d6f1', 'a1f14324-d6cd-4669-8a74-ed653b609543', 'email', 'robot_test_template_1773573472', TRUE, '2026-03-15T11:18:53.957787', '2026-03-15T11:18:53.957787'),
      ('18e6f3f3-aa5c-4262-8dac-cf5c0d98b3e7', '66af3cda-1e52-4992-883e-46eab3d16726', 'email', 'robot_test_template_1774185716', TRUE, '2026-03-22T13:23:11.753925', '2026-03-22T13:23:11.753925'),
      ('1ba60aa6-c38d-4908-9960-361ecfb1f4de', '30000000-0000-0000-0000-000000000001', 'email', 'password_reset', TRUE, '2026-03-20T04:27:43.910015', '2026-03-20T04:27:43.910015'),
      ('1e603b08-b9ba-471b-9ca8-f364b65f0adf', 'd53d5196-0c82-44d7-aabd-c20d219f05c0', 'web_push', NULL, TRUE, '2026-03-14T09:40:41.627469', '2026-03-14T09:40:41.627469'),
      ('238702ee-5fd7-4faf-b051-1aa5431717fb', '38fe904f-e2ba-4c20-af67-87c5bdb81cad', 'web_push', NULL, TRUE, '2026-03-23T06:34:12.942064', '2026-03-23T06:34:12.942064'),
      ('25e2f826-5fa5-4264-88ff-60db16d8ce92', '704c7f68-c70c-43b6-abe8-6781b433d56b', 'web_push', NULL, TRUE, '2026-03-15T11:28:02.90706', '2026-03-15T11:28:02.90706'),
      ('2ee0b7a3-10f7-4ca5-aef3-0551ea020b2a', 'c3fe7e32-d9bb-4379-93c8-aa4ce58df13d', 'email', 'robot_test_template_1774185907', TRUE, '2026-03-22T13:26:26.034373', '2026-03-22T13:26:26.034373'),
      ('34aca51f-a44e-40c6-bdcf-c5c79370120a', '461b758c-f394-4af8-b589-c2799236d412', 'web_push', NULL, TRUE, '2026-03-14T08:52:01.993274', '2026-03-14T08:52:01.993274'),
      ('3dcbfd9d-1d67-4ae6-9cfc-64d86e9d27d0', '11eb8495-8ae3-491d-b37a-a003a2d8d76c', 'web_push', NULL, TRUE, '2026-03-16T10:48:14.555898', '2026-03-16T10:48:14.555898'),
      ('4448e26d-def6-4739-9b12-fbdfd3deae49', '11eb8495-8ae3-491d-b37a-a003a2d8d76c', 'email', 'robot_test_template_1773657987', TRUE, '2026-03-16T10:48:10.15514', '2026-03-16T10:48:10.15514'),
      ('4583602e-7c61-4294-be08-88cdf40b2434', '8317964d-f64f-4728-802f-535e14ee6b71', 'email', 'robot_test_template_1774185125', TRUE, '2026-03-22T13:13:22.645251', '2026-03-22T13:13:22.645251'),
      ('502bdbe2-3efc-4f52-9f92-5de000b5543b', '273fb676-c284-4668-b543-a8ee99890506', 'email', 'robot_test_template_1773574475', TRUE, '2026-03-15T11:35:19.550702', '2026-03-15T11:35:19.550702'),
      ('52d7c940-e990-4b56-9e21-727e480293c5', '18f0c75e-edae-46bf-8ec3-ebba8e7303e4', 'email', 'robot_test_template_1774406073', TRUE, '2026-03-25T02:35:51.20968', '2026-03-25T02:35:51.20968'),
      ('555068bd-5f2d-4673-aa72-2fd3fb4b5c77', '9cbc0780-9750-414a-8802-f612230402ad', 'email', 'robot_test_template_1773988688', TRUE, '2026-03-20T06:39:21.622621', '2026-03-20T06:39:21.622621'),
      ('578671e9-1505-4b07-ba7a-309abf6df25b', '461b758c-f394-4af8-b589-c2799236d412', 'email', 'robot_test_template_1773478291', TRUE, '2026-03-14T08:52:00.835253', '2026-03-14T08:52:00.835253'),
      ('58c0dea5-e57b-4243-80ef-b0a667de0db5', '69fa29c7-b531-42ed-ace6-08f6b816ec5c', 'web_push', NULL, TRUE, '2026-03-14T09:36:50.422527', '2026-03-14T09:36:50.422527'),
      ('5c22d2bf-be9c-41f0-bc8b-4ce1b0f1b2c3', '66af3cda-1e52-4992-883e-46eab3d16726', 'web_push', NULL, TRUE, '2026-03-22T13:23:14.504132', '2026-03-22T13:23:14.504132'),
      ('5cdf6d04-6e29-436c-a44f-c456446dc4ee', 'e9c2f1a6-b435-4d74-bb5c-0ff3bd6f68fd', 'web_push', NULL, TRUE, '2026-03-23T08:16:52.982289', '2026-03-23T08:16:52.982289'),
      ('64100556-39df-49bf-a1fb-dd7dc2b9d7c8', '7b3cb240-8c41-454b-ad1a-34bf9ea44102', 'web_push', NULL, TRUE, '2026-03-25T09:30:25.058855', '2026-03-25T09:30:25.058855'),
      ('6e85a2a1-f431-4fa0-bd27-19a88026116c', '6821d950-d8fd-43ed-aec1-d45ebd86e4b9', 'email', 'robot_test_template_1774187045', TRUE, '2026-03-22T13:45:48.350246', '2026-03-22T13:45:48.350246'),
      ('80466f66-374a-49b2-a2c7-00a454b03742', 'dec71fae-7a44-4c8c-b626-072e885d2163', 'email', 'magic_link_login_email', TRUE, '2026-03-20T04:27:43.910015', '2026-03-20T04:27:43.910015'),
      ('805ac51f-2a24-4a0f-a90a-c1ea4c8539f6', '75d61718-2662-4725-811d-4c6f8901959f', 'web_push', NULL, TRUE, '2026-03-15T11:25:45.582888', '2026-03-15T11:25:45.582888'),
      ('83a0647b-8f1f-42a7-a82c-bd5191ea2ce1', '6821d950-d8fd-43ed-aec1-d45ebd86e4b9', 'web_push', NULL, TRUE, '2026-03-22T13:45:51.405335', '2026-03-22T13:45:51.405335'),
      ('92ab9337-b0bc-47a7-8494-2d9888ce732b', '69fa29c7-b531-42ed-ace6-08f6b816ec5c', 'email', 'robot_test_template_1773480977', TRUE, '2026-03-14T09:36:49.242976', '2026-03-14T09:36:49.242976'),
      ('97a330cb-6e37-4dca-800a-7f30f5fe7cba', '75d61718-2662-4725-811d-4c6f8901959f', 'email', 'robot_test_template_1773573900', TRUE, '2026-03-15T11:25:44.373362', '2026-03-15T11:25:44.373362'),
      ('a200c2c2-fe10-455c-aa45-22053be9fa38', 'e5e6f980-2b44-4f8a-98d7-e15cf0808b49', 'email', 'robot_test_template_1773988723', TRUE, '2026-03-20T06:39:54.667081', '2026-03-20T06:39:54.667081'),
      ('ad15d89f-d35b-40da-9599-8f037ca58bc2', 'e5e6f980-2b44-4f8a-98d7-e15cf0808b49', 'web_push', NULL, TRUE, '2026-03-20T06:39:57.537595', '2026-03-20T06:39:57.537595'),
      ('cc060c02-06ab-4afc-b432-f43ddd79c949', 'd53d5196-0c82-44d7-aabd-c20d219f05c0', 'email', 'robot_test_template_1773481201', TRUE, '2026-03-14T09:40:40.348086', '2026-03-14T09:40:40.348086'),
      ('cf79268f-d83b-4816-aa2e-318cc3c537ef', '273fb676-c284-4668-b543-a8ee99890506', 'web_push', NULL, TRUE, '2026-03-15T11:35:20.864551', '2026-03-15T11:35:20.864551'),
      ('cfb45647-50e5-41e2-8db0-2d357f4af6e0', '9cbc0780-9750-414a-8802-f612230402ad', 'web_push', NULL, TRUE, '2026-03-20T06:39:24.588555', '2026-03-20T06:39:24.588555'),
      ('d29769fe-f965-4af5-9e1c-95964c486919', '1ac4c744-37b5-4fef-85e7-891b7112e3cc', 'email', 'robot_test_template_1774185929', TRUE, '2026-03-22T13:26:46.305164', '2026-03-22T13:26:46.305164'),
      ('d432b6be-b614-46ad-8c20-6529f85945c2', '704c7f68-c70c-43b6-abe8-6781b433d56b', 'email', 'robot_test_template_1773574043', TRUE, '2026-03-15T11:28:01.4756', '2026-03-15T11:28:01.4756'),
      ('deed7a3a-509a-484e-816d-ba6e3f5d97dc', 'a1f14324-d6cd-4669-8a74-ed653b609543', 'web_push', NULL, TRUE, '2026-03-15T11:18:55.237664', '2026-03-15T11:18:55.237664'),
      ('e5152d3d-9cd5-41bb-b555-59a47ef43a76', 'c3fe7e32-d9bb-4379-93c8-aa4ce58df13d', 'web_push', NULL, TRUE, '2026-03-22T13:26:28.82923', '2026-03-22T13:26:28.82923'),
      ('e69d0441-d7b3-47dc-9e1a-ac8cce56c940', 'e9c2f1a6-b435-4d74-bb5c-0ff3bd6f68fd', 'email', 'robot_test_template_1774253729', TRUE, '2026-03-23T08:16:50.484229', '2026-03-23T08:16:50.484229'),
      ('ed321551-795e-41d0-b3bd-626a886ad7af', '18f0c75e-edae-46bf-8ec3-ebba8e7303e4', 'web_push', NULL, TRUE, '2026-03-25T02:35:54.849511', '2026-03-25T02:35:54.849511'),
      ('f065e79a-4ab4-46f7-83b0-8f00e7ec1a0a', '7e4dc482-8e1a-414b-8014-ed5e6061dbd8', 'web_push', NULL, TRUE, '2026-03-17T07:38:17.358288', '2026-03-17T07:38:17.358288'),
      ('f2c38bfe-aba6-4253-815c-7f518bd69432', '1ac4c744-37b5-4fef-85e7-891b7112e3cc', 'web_push', NULL, TRUE, '2026-03-22T13:26:49.155421', '2026-03-22T13:26:49.155421'),
      ('fe38e416-00e0-491a-9028-e38d001f7b43', '7b3cb240-8c41-454b-ad1a-34bf9ea44102', 'email', 'robot_test_template_1774430945', TRUE, '2026-03-25T09:30:21.057168', '2026-03-25T09:30:21.057168')
  ON CONFLICT (rule_id, channel_code) DO UPDATE SET template_code = EXCLUDED.template_code, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.19_dtl_rule_conditions (22 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."19_dtl_rule_conditions" (id, rule_id, condition_type, field_key, operator, value, value_type, logical_group, sort_order, is_active, created_at, updated_at)
  VALUES
      ('1225deae-e429-4ea5-b9c6-a42aadf1f694', '7b3cb240-8c41-454b-ad1a-34bf9ea44102', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-25T09:30:28.51392', '2026-03-25T09:30:28.51392'),
      ('170e1eb6-e71a-4c77-a3bc-be8a757a9a7c', 'e9c2f1a6-b435-4d74-bb5c-0ff3bd6f68fd', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-23T08:16:53.998983', '2026-03-23T08:16:53.998983'),
      ('3ec53e3a-cb69-49c9-b76a-4eff301844f7', '273fb676-c284-4668-b543-a8ee99890506', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-15T11:35:23.470607', '2026-03-15T11:35:23.470607'),
      ('40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000010', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('4918b551-3a34-4590-abf8-c92ebdc64308', '7e4dc482-8e1a-414b-8014-ed5e6061dbd8', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-17T07:38:21.585638', '2026-03-17T07:38:21.585638'),
      ('5de152d8-ff65-4b4e-b168-557b426551d6', 'd53d5196-0c82-44d7-aabd-c20d219f05c0', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T09:40:44.190212', '2026-03-14T09:40:44.190212'),
      ('62201318-fcb6-4d3f-b87b-19e670c4ad0a', '9cbc0780-9750-414a-8802-f612230402ad', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-20T06:39:29.328472', '2026-03-20T06:39:29.328472'),
      ('774e83a5-3a37-47ed-8a58-44ba826d5445', 'c3fe7e32-d9bb-4379-93c8-aa4ce58df13d', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:26:31.793525', '2026-03-22T13:26:31.793525'),
      ('7a873499-315c-4cd8-9b46-322bb8c92668', '11eb8495-8ae3-491d-b37a-a003a2d8d76c', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-16T10:48:20.640879', '2026-03-16T10:48:20.640879'),
      ('7fefc4f5-c7f7-4c64-bb66-0536795a1da2', '18f0c75e-edae-46bf-8ec3-ebba8e7303e4', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-25T02:36:00.828537', '2026-03-25T02:36:00.828537'),
      ('827835ec-b57b-4187-ada9-e676b268f9cd', '24691c00-aea9-4378-8ce2-1812625b5453', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T08:49:25.125164', '2026-03-14T08:49:25.125164'),
      ('9da7acbd-9423-4b0a-8a31-5c1897c960fb', '75d61718-2662-4725-811d-4c6f8901959f', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-15T11:25:48.166905', '2026-03-15T11:25:48.166905'),
      ('a1242465-42c7-4bb6-b802-f4a8d89d5810', '8317964d-f64f-4728-802f-535e14ee6b71', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:13:28.299643', '2026-03-22T13:13:28.299643'),
      ('a65d411c-8d06-4338-b55a-a4e7889cc4fa', '6821d950-d8fd-43ed-aec1-d45ebd86e4b9', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:45:54.370399', '2026-03-22T13:45:54.370399'),
      ('b13b0259-8305-4b87-887f-e0209eddbd77', 'e5e6f980-2b44-4f8a-98d7-e15cf0808b49', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-20T06:40:02.281506', '2026-03-20T06:40:02.281506'),
      ('b2f1cfe6-4301-4f43-9210-4eec0ed95c3e', '704c7f68-c70c-43b6-abe8-6781b433d56b', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-15T11:28:05.44497', '2026-03-15T11:28:05.44497'),
      ('c024d655-6fee-4630-817a-14cf90c19914', '1ac4c744-37b5-4fef-85e7-891b7112e3cc', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:26:52.021999', '2026-03-22T13:26:52.021999'),
      ('c5ad5ff7-fbed-48ac-a0e8-2a8b3c43df82', '66af3cda-1e52-4992-883e-46eab3d16726', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:23:17.282482', '2026-03-22T13:23:17.282482'),
      ('d8091905-d111-4799-a678-086338717110', '461b758c-f394-4af8-b589-c2799236d412', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T08:52:04.129066', '2026-03-14T08:52:04.129066'),
      ('eab32da3-f873-4647-bf9d-50ec2d365811', 'a1f14324-d6cd-4669-8a74-ed653b609543', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-15T11:18:58.005027', '2026-03-15T11:18:58.005027'),
      ('f44a376a-c7b5-40ca-bed5-cbea5e1dcdb9', '38fe904f-e2ba-4c20-af67-87c5bdb81cad', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-23T06:34:14.80016', '2026-03-23T06:34:14.80016'),
      ('fcf58544-5a37-437b-a6bc-0a13a034aa38', '69fa29c7-b531-42ed-ace6-08f6b816ec5c', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T09:36:52.593814', '2026-03-14T09:36:52.593814')
  ON CONFLICT (id) DO UPDATE SET rule_id = EXCLUDED.rule_id, condition_type = EXCLUDED.condition_type, field_key = EXCLUDED.field_key, operator = EXCLUDED.operator, value = EXCLUDED.value, value_type = EXCLUDED.value_type, logical_group = EXCLUDED.logical_group, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.31_fct_variable_queries (8 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."31_fct_variable_queries" (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_active, is_deleted, created_at, updated_at, created_by, is_system, linked_event_type_codes)
  VALUES
      ('a0000001-0000-0000-0000-000000000001', '__system__', 'user_profile', 'User Profile', 'Full profile of the notification recipient: name, email, username, timezone.', 'SELECT first_name, last_name, display_name, email, username, timezone FROM "03_auth_manage"."50_vw_user_profile" WHERE user_id = $1', '[{"key": "$user_id", "source": "context", "position": 1, "required": true}]'::jsonb, '[{"name": "first_name", "data_type": "string"}, {"name": "last_name", "data_type": "string"}, {"name": "display_name", "data_type": "string"}, {"name": "email", "data_type": "string"}, {"name": "username", "data_type": "string"}, {"name": "timezone", "data_type": "string"}]'::jsonb, 3000, TRUE, FALSE, '2026-03-17T07:23:08.5595', '2026-03-17T07:23:08.5595', NULL, TRUE, ARRAY[]::text[]),
      ('a0000001-0000-0000-0000-000000000002', '__system__', 'actor_profile', 'Actor Profile', 'Full profile of the actor who triggered the audit event: name, email.', 'SELECT first_name, last_name, display_name, email, username FROM "03_auth_manage"."50_vw_user_profile" WHERE user_id = $1', '[{"key": "$actor_id", "source": "context", "position": 1, "required": true}]'::jsonb, '[{"name": "first_name", "data_type": "string"}, {"name": "last_name", "data_type": "string"}, {"name": "display_name", "data_type": "string"}, {"name": "email", "data_type": "string"}, {"name": "username", "data_type": "string"}]'::jsonb, 3000, TRUE, FALSE, '2026-03-17T07:23:08.588247', '2026-03-17T07:23:08.588247', NULL, TRUE, ARRAY[]::text[]),
      ('a0000001-0000-0000-0000-000000000003', '__system__', 'org_detail', 'Organization Detail', 'Organization name, slug, and type from the org_id in event context.', 'SELECT org_name, org_slug, org_type_name FROM "03_auth_manage"."51_vw_org_detail" WHERE org_id = $1', '[{"key": "$org_id", "source": "context", "position": 1, "required": true}]'::jsonb, '[{"name": "org_name", "data_type": "string"}, {"name": "org_slug", "data_type": "string"}, {"name": "org_type_name", "data_type": "string"}]'::jsonb, 3000, TRUE, FALSE, '2026-03-17T07:23:08.617288', '2026-03-17T07:23:08.617288', NULL, TRUE, ARRAY[]::text[]),
      ('a0000001-0000-0000-0000-000000000004', '__system__', 'workspace_detail', 'Workspace Detail', 'Workspace name, slug, type, and parent org name.', 'SELECT workspace_name, workspace_slug, workspace_type_name, org_name FROM "03_auth_manage"."52_vw_workspace_detail" WHERE workspace_id = $1', '[{"key": "$workspace_id", "source": "context", "position": 1, "required": true}]'::jsonb, '[{"name": "workspace_name", "data_type": "string"}, {"name": "workspace_slug", "data_type": "string"}, {"name": "workspace_type_name", "data_type": "string"}, {"name": "org_name", "data_type": "string"}]'::jsonb, 3000, TRUE, FALSE, '2026-03-17T07:23:08.664524', '2026-03-17T07:23:08.664524', NULL, TRUE, ARRAY[]::text[]),
      ('a0000001-0000-0000-0000-000000000005', '__system__', 'task_detail', 'Task Detail', 'Full task context: title, status, priority, assignee, reporter, due date, org, workspace.', 'SELECT title, description, status_code, priority_code, task_type_code, assignee_name, assignee_email, reporter_name, reporter_email, org_name, workspace_name, due_date::text AS due_date FROM "08_tasks"."50_vw_task_notification" WHERE task_id = $1', '[{"key": "$task_id", "source": "audit_property", "position": 1, "required": true}]'::jsonb, '[{"name": "title", "data_type": "string"}, {"name": "description", "data_type": "string"}, {"name": "status_code", "data_type": "string"}, {"name": "priority_code", "data_type": "string"}, {"name": "task_type_code", "data_type": "string"}, {"name": "assignee_name", "data_type": "string"}, {"name": "assignee_email", "data_type": "string"}, {"name": "reporter_name", "data_type": "string"}, {"name": "reporter_email", "data_type": "string"}, {"name": "org_name", "data_type": "string"}, {"name": "workspace_name", "data_type": "string"}, {"name": "due_date", "data_type": "string"}]'::jsonb, 3000, TRUE, FALSE, '2026-03-17T07:23:08.699323', '2026-03-17T07:23:08.699323', NULL, TRUE, ARRAY[]::text[]),
      ('a0000001-0000-0000-0000-000000000006', '__system__', 'risk_detail', 'Risk Detail', 'Full risk context: title, level, category, owner, treatment type, latest score, org, workspace.', 'SELECT risk_code, title, description, risk_level_code, risk_level_name, risk_category_code, risk_category_name, risk_status, treatment_type_code, owner_name, owner_email, org_name, workspace_name, latest_risk_score::text AS latest_risk_score FROM "14_risk_registry"."50_vw_risk_notification" WHERE risk_id = $1', '[{"key": "$risk_id", "source": "audit_property", "position": 1, "required": true}]'::jsonb, '[{"name": "risk_code", "data_type": "string"}, {"name": "title", "data_type": "string"}, {"name": "description", "data_type": "string"}, {"name": "risk_level_code", "data_type": "string"}, {"name": "risk_level_name", "data_type": "string"}, {"name": "risk_category_code", "data_type": "string"}, {"name": "risk_category_name", "data_type": "string"}, {"name": "risk_status", "data_type": "string"}, {"name": "treatment_type_code", "data_type": "string"}, {"name": "owner_name", "data_type": "string"}, {"name": "owner_email", "data_type": "string"}, {"name": "org_name", "data_type": "string"}, {"name": "workspace_name", "data_type": "string"}, {"name": "latest_risk_score", "data_type": "string"}]'::jsonb, 3000, TRUE, FALSE, '2026-03-17T07:23:08.731886', '2026-03-17T07:23:08.731886', NULL, TRUE, ARRAY[]::text[]),
      ('a0000001-0000-0000-0000-000000000007', '__system__', 'control_detail', 'Control Detail', 'Full control context: code, name, category, criticality, guidance, framework name.', 'SELECT control_code, control_name, description, guidance, category_name, criticality_name, control_type, framework_name, framework_code FROM "05_grc_library"."50_vw_control_notification" WHERE control_id = $1', '[{"key": "$control_id", "source": "audit_property", "position": 1, "required": true}]'::jsonb, '[{"name": "control_code", "data_type": "string"}, {"name": "control_name", "data_type": "string"}, {"name": "description", "data_type": "string"}, {"name": "guidance", "data_type": "string"}, {"name": "category_name", "data_type": "string"}, {"name": "criticality_name", "data_type": "string"}, {"name": "control_type", "data_type": "string"}, {"name": "framework_name", "data_type": "string"}, {"name": "framework_code", "data_type": "string"}]'::jsonb, 3000, TRUE, FALSE, '2026-03-17T07:23:08.758485', '2026-03-17T07:23:08.758485', NULL, TRUE, ARRAY[]::text[]),
      ('a0000001-0000-0000-0000-000000000008', '__system__', 'framework_detail', 'Framework Detail', 'Framework name, type, category, publisher for notification context.', 'SELECT framework_code, framework_name, description, publisher_name, framework_type_name, framework_category_name FROM "05_grc_library"."50_vw_framework_notification" WHERE framework_id = $1', '[{"key": "$framework_id", "source": "audit_property", "position": 1, "required": true}]'::jsonb, '[{"name": "framework_code", "data_type": "string"}, {"name": "framework_name", "data_type": "string"}, {"name": "description", "data_type": "string"}, {"name": "publisher_name", "data_type": "string"}, {"name": "framework_type_name", "data_type": "string"}, {"name": "framework_category_name", "data_type": "string"}]'::jsonb, 3000, TRUE, FALSE, '2026-03-17T07:23:08.789186', '2026-03-17T07:23:08.789186', NULL, TRUE, ARRAY[]::text[])
  ON CONFLICT (tenant_key, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sql_template = EXCLUDED.sql_template, bind_params = EXCLUDED.bind_params, result_columns = EXCLUDED.result_columns, timeout_ms = EXCLUDED.timeout_ms, is_active = EXCLUDED.is_active, is_deleted = EXCLUDED.is_deleted, updated_at = EXCLUDED.updated_at, is_system = EXCLUDED.is_system, linked_event_type_codes = EXCLUDED.linked_event_type_codes;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.30_fct_smtp_config (1 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."30_fct_smtp_config" (id, tenant_key, host, port, username, password, from_email, from_name, use_tls, start_tls, is_active, created_at, updated_at, created_by, updated_by)
  VALUES
      ('0cb90124-7b6d-4a24-a825-3a0558f95a33', 'default', 'smtp.gmail.com', 587, 'no-reply@kreesalis.com', 'aedofcfpntibdwak', 'no-reply@kreesalis.com', 'K-Control', FALSE, TRUE, TRUE, '2026-03-16T11:46:05.290906', '2026-03-16T11:53:01.38837', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223')
  ON CONFLICT (tenant_key) DO UPDATE SET host = EXCLUDED.host, port = EXCLUDED.port, username = EXCLUDED.username, password = EXCLUDED.password, from_email = EXCLUDED.from_email, from_name = EXCLUDED.from_name, use_tls = EXCLUDED.use_tls, start_tls = EXCLUDED.start_tls, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: AI
-- Extracted: 2026-03-27T14:17:24.897027
-- ═════════════════════════════════════════════════════════════════════════════

-- 20_ai.02_dim_agent_types (22 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."02_dim_agent_types" (code, name, description, is_active, created_at)
  VALUES
      ('connector_agent', 'Connector Agent', 'Specialist for connector configuration', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('copilot', 'System Copilot', 'Page-aware general assistant for all kcontrol pages', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('dataset_agent', 'Dataset Agent', 'AI-powered dataset record analysis, description generation, and compliance field explanation', TRUE, '2026-03-25T15:38:55.217004+00:00'),
      ('evidence_checker_agent', 'Evidence Checker Agent', 'Evaluates a single acceptance criterion against indexed document chunks', TRUE, '2026-03-17T18:47:13.438762+00:00'),
      ('evidence_lead', 'Evidence Lead Agent', 'Orchestrates evidence evaluation across all acceptance criteria for a task', TRUE, '2026-03-17T18:47:13.438762+00:00'),
      ('framework_agent', 'Framework Agent', 'Specialist for framework library operations', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('framework_builder', 'Framework Builder', 'AI agent for creating GRC frameworks with requirements, controls, and risk mappings', TRUE, '2026-03-18T19:07:45.869967+00:00'),
      ('grc_assistant', 'GRC Assistant', 'Domain specialist for GRC frameworks, controls, risks', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('library_builder', 'Control Library Builder', 'Creates policies and control test libraries', TRUE, '2026-03-18T22:43:41.833657+00:00'),
      ('report_generator', 'Report Generator', 'Generates AI-powered GRC compliance and audit reports', TRUE, '2026-03-18T14:22:13.092823+00:00'),
      ('risk_agent', 'Risk Agent', 'Specialist for risk registry operations', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('role_agent', 'Role Agent', 'Specialist for role and permission management', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('signal_agent', 'Signal Agent', 'Specialist for signal building operations', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('signal_codegen', 'Signal Code Generator (Spec-Driven)', 'Spec-driven iterative Python code generation', TRUE, '2026-03-18T22:43:41.833657+00:00'),
      ('signal_generate', 'Signal Code Generator (Quick)', 'Quick-generate: prompt → compile → test → fix loop', TRUE, '2026-03-18T22:43:41.833657+00:00'),
      ('signal_generator', 'Signal Generator', 'Autonomous code generation for sandbox signals', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('signal_spec', 'Signal Specification Agent', 'Interactive spec generation with feasibility gate', TRUE, '2026-03-18T22:43:41.833657+00:00'),
      ('supervisor', 'Supervisor', 'Root supervisor that routes tasks to team leads', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('task_agent', 'Task Agent', 'Specialist for task management operations', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('test_dataset_gen', 'Test Dataset Generator', 'Shape-preserving AI test dataset generation', TRUE, '2026-03-18T22:43:41.833657+00:00'),
      ('threat_composer', 'Threat Type Composer', 'Semantic threat type composition from signals', TRUE, '2026-03-18T22:43:41.833657+00:00'),
      ('user_agent', 'User Agent', 'Specialist for user and access management', TRUE, '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.03_dim_message_roles (4 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."03_dim_message_roles" (code, name, created_at)
  VALUES
      ('assistant', 'Assistant', '2026-03-17T15:46:41.31265+00:00'),
      ('system', 'System', '2026-03-17T15:46:41.31265+00:00'),
      ('tool', 'Tool', '2026-03-17T15:46:41.31265+00:00'),
      ('user', 'User', '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.04_dim_approval_statuses (6 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."04_dim_approval_statuses" (code, name, is_terminal, created_at)
  VALUES
      ('approved', 'Approved', FALSE, '2026-03-17T15:46:41.31265+00:00'),
      ('cancelled', 'Cancelled', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('executed', 'Executed', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('expired', 'Expired', TRUE, '2026-03-17T15:46:41.31265+00:00'),
      ('pending', 'Pending', FALSE, '2026-03-17T15:46:41.31265+00:00'),
      ('rejected', 'Rejected', TRUE, '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, is_terminal = EXCLUDED.is_terminal;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.05_dim_tool_categories (6 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."05_dim_tool_categories" (code, name, created_at)
  VALUES
      ('action', 'Action', '2026-03-17T21:15:40.103128+00:00'),
      ('hierarchy', 'Hierarchy', '2026-03-17T21:15:40.103128+00:00'),
      ('insight', 'Insight', '2026-03-17T21:15:40.103128+00:00'),
      ('navigation', 'Navigation', '2026-03-17T21:15:40.103128+00:00'),
      ('read', 'Read', '2026-03-17T15:46:41.31265+00:00'),
      ('write', 'Write', '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.06_dim_memory_types (4 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."06_dim_memory_types" (code, name, created_at)
  VALUES
      ('domain_knowledge', 'Domain Knowledge', '2026-03-17T15:46:41.31265+00:00'),
      ('expertise', 'Domain Expertise', '2026-03-17T15:46:41.31265+00:00'),
      ('interaction_pattern', 'Interaction Pattern', '2026-03-17T15:46:41.31265+00:00'),
      ('preference', 'User Preference', '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.07_dim_budget_periods (2 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."07_dim_budget_periods" (code, name, created_at)
  VALUES
      ('daily', 'Daily', '2026-03-17T15:46:41.31265+00:00'),
      ('monthly', 'Monthly', '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.08_dim_guardrail_types (4 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."08_dim_guardrail_types" (code, name, description, created_at)
  VALUES
      ('content_policy', 'Content Policy', 'Block harmful or off-topic content', '2026-03-17T15:46:41.31265+00:00'),
      ('injection_detect', 'Injection Detect', 'Detect prompt injection and jailbreak attempts', '2026-03-17T15:46:41.31265+00:00'),
      ('output_filter', 'Output Filter', 'Sanitize LLM output — strip leaked prompts, internal IDs', '2026-03-17T15:46:41.31265+00:00'),
      ('pii_filter', 'PII Filter', 'Detect and redact personally identifiable information', '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.09_dim_prompt_scopes (3 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."09_dim_prompt_scopes" (code, name, sort_order, created_at)
  VALUES
      ('agent', 'Agent Base Prompt', 1, '2026-03-17T15:46:41.31265+00:00'),
      ('feature', 'Feature Guardrail', 2, '2026-03-17T15:46:41.31265+00:00'),
      ('org', 'Org Overlay', 3, '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.10_dim_agent_relationships (3 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."10_dim_agent_relationships" (code, name, created_at)
  VALUES
      ('delegates_to', 'Delegates To', '2026-03-17T15:46:41.31265+00:00'),
      ('peers_with', 'Peers With', '2026-03-17T15:46:41.31265+00:00'),
      ('reports_to', 'Reports To', '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.11_dim_job_statuses (7 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."11_dim_job_statuses" (code, name, is_terminal, created_at)
  VALUES
      ('cancelled', 'Cancelled', TRUE, '2026-03-17T15:46:59.780213+00:00'),
      ('completed', 'Completed', TRUE, '2026-03-17T15:46:59.780213+00:00'),
      ('failed', 'Failed', TRUE, '2026-03-17T15:46:59.780213+00:00'),
      ('queued', 'Queued', FALSE, '2026-03-17T15:46:59.780213+00:00'),
      ('rate_limited', 'Rate Limited', FALSE, '2026-03-17T15:46:59.780213+00:00'),
      ('retrying', 'Retrying', FALSE, '2026-03-17T15:46:59.780213+00:00'),
      ('running', 'Running', FALSE, '2026-03-17T15:46:59.780213+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, is_terminal = EXCLUDED.is_terminal;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.12_dim_job_priorities (5 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."12_dim_job_priorities" (code, name, sort_order, created_at)
  VALUES
      ('batch', 'Batch', 100, '2026-03-17T15:46:59.780213+00:00'),
      ('critical', 'Critical', 10, '2026-03-17T15:46:59.780213+00:00'),
      ('high', 'High', 20, '2026-03-17T15:46:59.780213+00:00'),
      ('low', 'Low', 80, '2026-03-17T15:46:59.780213+00:00'),
      ('normal', 'Normal', 50, '2026-03-17T15:46:59.780213+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.30_fct_guardrail_configs (2 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."30_fct_guardrail_configs" (id, tenant_key, org_id, guardrail_type_code, is_enabled, config_json, created_at, updated_at)
  VALUES
      ('1e28ed4d-4d2f-4e7b-b364-cadbc2294d6a', 'default', NULL, 'injection_detect', TRUE, '{}'::jsonb, '2026-03-17T16:13:33.196166+00:00', '2026-03-17T16:13:33.196166+00:00'),
      ('dc016dec-d966-4cad-ad83-baf58df1687e', 'default', NULL, 'pii_filter', TRUE, '{"sensitivity": "high"}'::jsonb, '2026-03-17T16:10:47.642784+00:00', '2026-03-17T16:13:32.845728+00:00')
  ON CONFLICT (id) DO UPDATE SET tenant_key = EXCLUDED.tenant_key, org_id = EXCLUDED.org_id, guardrail_type_code = EXCLUDED.guardrail_type_code, is_enabled = EXCLUDED.is_enabled, config_json = EXCLUDED.config_json, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.32_fct_agent_configs (10 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."32_fct_agent_configs" (id, tenant_key, agent_type_code, org_id, provider_base_url, api_key_encrypted, model_id, temperature, max_tokens, is_active, created_at, updated_at, provider_type)
  VALUES
      ('06f45be6-cbfa-43c3-9aee-818fc49e95e1', 'system', 'evidence_lead', NULL, 'https://llm.kreesalis.com/v1', 'ZLffwkrpiJKIks8jfOEfkRKbMxi7O3lsy91KAVZlDdUE0nxWzDa/ietglODowf76GVG6ABI=', 'gpt-5.3-chat', 1.0, 4096, TRUE, '2026-03-17T18:47:36.820398+00:00', '2026-03-17T20:52:39.334513+00:00', 'openai_compatible'),
      ('0ece99cb-3cf5-4c21-8f95-e81354662040', 'system', 'signal_codegen', NULL, 'https://llm.kreesalis.com/v1', NULL, 'gpt-5.3-chat', 1.0, 4096, TRUE, '2026-03-25T17:18:20.227185+00:00', '2026-03-25T17:18:20.227185+00:00', 'openai_compatible'),
      ('23309feb-1ec1-4990-95e9-0589bea65c21', 'default', 'grc_assistant', NULL, 'https://llm.kreesalis.com/v1', 'ud05XGPZ6iLebOKJfKK0aYvKayZb7Y7W+8lx9v56T4J0ua4so8cdktrzy4KkLFXvRDZQFiw=', 'gpt-5.3-chat', 1.0, 2048, TRUE, '2026-03-17T16:10:29.646545+00:00', '2026-03-17T18:52:43.991743+00:00', 'openai_compatible'),
      ('233a65b6-b06a-4f6a-8a98-3e0a4c51bf55', 'system', 'dataset_agent', NULL, 'https://llm.kreesalis.com/v1', NULL, 'gpt-5.3-chat', 0.3, 4096, TRUE, '2026-03-25T15:38:55.252634+00:00', '2026-03-25T15:38:55.252634+00:00', 'openai_compatible'),
      ('23c624aa-dff3-4b7f-93c3-20d46fc72579', 'default', 'signal_generator', NULL, 'https://api.openai.com/v1', NULL, 'gpt-4o', 0.3, 4096, TRUE, '2026-03-17T16:03:11.976886+00:00', '2026-03-17T16:03:11.976886+00:00', 'openai_compatible'),
      ('3367fd34-e3e8-4585-a621-aadbd39cffd4', 'default', 'copilot', NULL, 'https://llm.kreesalis.com/v1', 'ud05XGPZ6iLebOKJfKK0aYvKayZb7Y7W+8lx9v56T4J0ua4so8cdktrzy4KkLFXvRDZQFiw=', 'gpt-5.3-chat', 1.0, 4096, TRUE, '2026-03-17T15:56:12.328005+00:00', '2026-03-18T09:58:04.692966+00:00', 'openai_compatible'),
      ('7c4ac3d1-77f0-4651-adeb-c276969a1bc4', 'system', 'test_dataset_gen', NULL, 'https://llm.kreesalis.com/v1', NULL, 'gpt-5.3-chat', 1.0, 4096, TRUE, '2026-03-25T17:18:20.156626+00:00', '2026-03-25T17:18:20.156626+00:00', 'openai_compatible'),
      ('90717c10-1bad-4a22-8ce9-ec94f6410c33', 'system', 'threat_composer', NULL, 'https://llm.kreesalis.com/v1', NULL, 'gpt-5.3-chat', 1.0, 4096, TRUE, '2026-03-25T18:31:07.873575+00:00', '2026-03-25T18:31:07.873575+00:00', 'openai_compatible'),
      ('9296a800-55ad-43de-a1a3-c42617c4453c', 'system', 'evidence_checker_agent', NULL, 'https://llm.kreesalis.com/v1', 'ZLffwkrpiJKIks8jfOEfkRKbMxi7O3lsy91KAVZlDdUE0nxWzDa/ietglODowf76GVG6ABI=', 'gpt-5.3-chat', 1.0, 4096, TRUE, '2026-03-17T18:47:37.0429+00:00', '2026-03-17T20:52:39.408782+00:00', 'openai_compatible'),
      ('97224385-2fc8-4005-b682-e1541204158d', 'system', 'library_builder', NULL, 'https://llm.kreesalis.com/v1', NULL, 'gpt-5.3-chat', 1.0, 4096, TRUE, '2026-03-25T18:31:07.943544+00:00', '2026-03-25T18:31:07.943544+00:00', 'openai_compatible')
  ON CONFLICT (id) DO UPDATE SET tenant_key = EXCLUDED.tenant_key, agent_type_code = EXCLUDED.agent_type_code, org_id = EXCLUDED.org_id, provider_base_url = EXCLUDED.provider_base_url, api_key_encrypted = EXCLUDED.api_key_encrypted, model_id = EXCLUDED.model_id, temperature = EXCLUDED.temperature, max_tokens = EXCLUDED.max_tokens, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at, provider_type = EXCLUDED.provider_type;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.33_fct_prompt_templates (1 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."33_fct_prompt_templates" (id, tenant_key, scope_code, agent_type_code, feature_code, org_id, prompt_text, version, is_active, created_by, created_at, updated_at)
  VALUES
      ('e614903a-677a-4096-ba15-0d5fc2c17590', 'default', 'agent', 'copilot', NULL, NULL, 'You are K-Control AI Copilot, an enterprise GRC assistant. Help users with compliance frameworks, controls, risks, and evidence management.', 9, TRUE, 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-17T15:56:12.608923+00:00', '2026-03-19T07:37:50.457884+00:00')
  ON CONFLICT (id) DO UPDATE SET tenant_key = EXCLUDED.tenant_key, scope_code = EXCLUDED.scope_code, agent_type_code = EXCLUDED.agent_type_code, feature_code = EXCLUDED.feature_code, org_id = EXCLUDED.org_id, prompt_text = EXCLUDED.prompt_text, version = EXCLUDED.version, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- "20_ai"."34_dtl_prompt_template_properties": 0 rows (empty)

-- 20_ai.35_fct_agent_definitions (11 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."35_fct_agent_definitions" (id, agent_type_code, parent_agent_type_code, capabilities_json, tools_allowed_json, max_delegation_depth, is_active, created_at, updated_at)
  VALUES
      ('085fee0b-f809-4ae0-8063-0a7f10895b61', 'signal_agent', 'signal_generator', '["signal_crud"]'::jsonb, '["list_signals", "create_signal"]'::jsonb, 0, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('0f7e522b-9630-4264-9f36-6cf2899862cd', 'supervisor', NULL, '["route_tasks", "synthesize_results", "manage_budget"]'::jsonb, '[]'::jsonb, 1, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('2fb80bd9-7a5f-4267-98db-02001ec3d064', 'framework_agent', 'grc_assistant', '["framework_crud"]'::jsonb, '["list_frameworks", "get_framework", "create_framework", "update_framework"]'::jsonb, 0, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('5b7f4138-54d0-4651-853e-f5b023175af7', 'grc_assistant', 'supervisor', '["framework_ops", "risk_ops", "task_ops"]'::jsonb, '["list_frameworks", "get_framework", "list_controls"]'::jsonb, 2, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('63445f82-75a4-4a97-805b-667ca0695c4f', 'signal_generator', 'supervisor', '["signal_code_gen", "signal_validation"]'::jsonb, '["list_signals", "list_connectors"]'::jsonb, 2, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('64da9c02-f7f3-475c-99d9-7c76c3642e78', 'connector_agent', 'signal_generator', '["connector_ops"]'::jsonb, '["list_connectors"]'::jsonb, 0, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('690763f6-7bd6-43d4-b556-68fda8ca4599', 'role_agent', 'supervisor', '["role_ops"]'::jsonb, '["list_roles", "list_groups"]'::jsonb, 0, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('99c25f4d-bfb8-466a-a0d8-2be7c91a72c7', 'risk_agent', 'grc_assistant', '["risk_crud"]'::jsonb, '["list_risks", "create_risk", "update_risk"]'::jsonb, 0, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('a120ba82-2645-4ca0-8135-8cc085237f47', 'user_agent', 'supervisor', '["user_ops"]'::jsonb, '["list_users", "list_roles"]'::jsonb, 0, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('a165fc24-0f5f-447e-bde0-29f85e0ca51c', 'copilot', NULL, '["general_assist", "page_context", "memory"]'::jsonb, '[]'::jsonb, 0, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00'),
      ('bf9a4515-f551-4fbb-9871-e9c75a0cf1d7', 'task_agent', 'grc_assistant', '["task_crud"]'::jsonb, '["list_tasks"]'::jsonb, 0, TRUE, '2026-03-17T15:46:41.31265+00:00', '2026-03-17T15:46:41.31265+00:00')
  ON CONFLICT (agent_type_code) DO UPDATE SET parent_agent_type_code = EXCLUDED.parent_agent_type_code, capabilities_json = EXCLUDED.capabilities_json, tools_allowed_json = EXCLUDED.tools_allowed_json, max_delegation_depth = EXCLUDED.max_delegation_depth, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.44_fct_agent_rate_limits (12 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."44_fct_agent_rate_limits" (id, tenant_key, agent_type_code, org_id, max_requests_per_minute, max_tokens_per_minute, max_concurrent_jobs, batch_size, batch_interval_seconds, cooldown_seconds, is_active, created_at, updated_at)
  VALUES
      ('39d9409a-36a3-433f-889f-b9c43b12bd27', '__platform__', 'signal_agent', NULL, 20, 40000, 2, 5, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('3e4d0f1e-d0fd-4a23-b8f6-c5ba3da1afbc', '__platform__', 'framework_agent', NULL, 30, 60000, 3, 10, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('45e32d7c-1328-4d38-a9d0-d560ca23ae1e', '__platform__', 'grc_assistant', NULL, 30, 60000, 3, 5, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('75946490-5bdd-4312-bb6e-18e019074f93', '__platform__', 'copilot', NULL, 60, 90000, 5, 10, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('8306c13a-ef65-430b-91bb-d1fdfdb1a81a', '__platform__', 'supervisor', NULL, 20, 60000, 3, 5, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('989b8436-81b9-447d-8be9-911fc0d00593', 'default', 'evidence_lead', NULL, 60, 1000000, 1, 1, 0, 0, TRUE, '2026-03-17T18:47:13.438762+00:00', '2026-03-17T18:47:13.438762+00:00'),
      ('a28cb76f-9345-4867-a277-4497fba85e3c', '__platform__', 'signal_generator', NULL, 20, 40000, 2, 5, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('adc79c15-7823-4dfc-86c3-a5f5268f5895', '__platform__', 'risk_agent', NULL, 30, 60000, 3, 10, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('af128dd0-edca-463e-93ab-5ecd7dba1d91', '__platform__', 'user_agent', NULL, 20, 40000, 2, 5, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('b47500ea-b36b-42e6-b2e2-e0c181c8fb51', '__platform__', 'role_agent', NULL, 20, 40000, 2, 5, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('dedcac64-dc02-45fa-887d-4c09a3cc22e0', '__platform__', 'connector_agent', NULL, 20, 40000, 2, 5, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00'),
      ('ee806f46-6ab9-4a50-955b-c973c00f6ef8', '__platform__', 'task_agent', NULL, 30, 60000, 3, 10, 60, 30, TRUE, '2026-03-17T15:46:59.780213+00:00', '2026-03-17T15:46:59.780213+00:00')
  ON CONFLICT (id) DO UPDATE SET tenant_key = EXCLUDED.tenant_key, agent_type_code = EXCLUDED.agent_type_code, org_id = EXCLUDED.org_id, max_requests_per_minute = EXCLUDED.max_requests_per_minute, max_tokens_per_minute = EXCLUDED.max_tokens_per_minute, max_concurrent_jobs = EXCLUDED.max_concurrent_jobs, batch_size = EXCLUDED.batch_size, batch_interval_seconds = EXCLUDED.batch_interval_seconds, cooldown_seconds = EXCLUDED.cooldown_seconds, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 20_ai.60_fct_pdf_templates (1 rows)
DO $$ BEGIN
  INSERT INTO "20_ai"."60_fct_pdf_templates" (id, tenant_key, name, description, cover_style, primary_color, secondary_color, header_text, footer_text, prepared_by, doc_ref_prefix, classification_label, applicable_report_types, is_default, shell_file_key, shell_file_name, created_by, created_at, updated_at)
  VALUES
      ('7e662fa0-b0db-481e-9f02-f0e28a1e92fe', 'default', 'Kreesalis Standard', NULL, 'light_minimal', '#0f172a', '#6366f1', NULL, NULL, 'K-Control Platform', NULL, 'INTERNAL USE ONLY', ARRAY['executive_summary']::text[], TRUE, NULL, NULL, 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-25T08:21:43.369514+00:00', '2026-03-25T08:33:23.298038+00:00')
  ON CONFLICT (id) DO UPDATE SET tenant_key = EXCLUDED.tenant_key, name = EXCLUDED.name, description = EXCLUDED.description, cover_style = EXCLUDED.cover_style, primary_color = EXCLUDED.primary_color, secondary_color = EXCLUDED.secondary_color, header_text = EXCLUDED.header_text, footer_text = EXCLUDED.footer_text, prepared_by = EXCLUDED.prepared_by, doc_ref_prefix = EXCLUDED.doc_ref_prefix, classification_label = EXCLUDED.classification_label, applicable_report_types = EXCLUDED.applicable_report_types, is_default = EXCLUDED.is_default, shell_file_key = EXCLUDED.shell_file_key, shell_file_name = EXCLUDED.shell_file_name, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: SANDBOX
-- Extracted: 2026-03-27T14:17:40.225339
-- ═════════════════════════════════════════════════════════════════════════════

-- 15_sandbox.02_dim_connector_categories (10 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."02_dim_connector_categories" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('1aa616dc-08c7-490e-b11f-4ccb00c7b94d', 'project_management', 'Project Management', 'Jira, ServiceNow, Linear', 4, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('4c418765-b709-4752-a5e5-70a92a70a67f', 'source_control', 'Source Control', 'GitHub, GitLab, Bitbucket', 3, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('7912746d-e264-44c5-a308-4e709b4eb702', 'cloud_infrastructure', 'Cloud Infrastructure', 'AWS, Azure, GCP cloud platforms', 1, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('7ed9a5af-28c2-41bf-a11a-953587d769aa', 'custom', 'Custom', 'Custom API or webhook integrations', 10, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('bde0e7df-c557-4a86-add5-73bd00aade38', 'logging_monitoring', 'Logging & Monitoring', 'Datadog, Splunk, Elastic, CloudWatch', 7, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('c1ff90e7-06ed-4689-baf5-e73d63b81ffb', 'database', 'Database', 'PostgreSQL, MySQL, MongoDB', 5, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('dd6ed471-f0ab-45b0-91c3-e17bda468063', 'itsm', 'IT Service Management', 'ServiceNow, PagerDuty', 8, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('de8feceb-88c2-4e34-b60a-b5dfb9fd1631', 'container_orchestration', 'Container Orchestration', 'Kubernetes, Docker, ECS', 6, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('f888f16e-61ce-4a2c-83fb-6c556304a149', 'identity_provider', 'Identity Provider', 'Okta, Azure AD, Google Workspace', 2, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00'),
      ('fde526e4-778f-4f89-8cef-6773c6599bdc', 'communication', 'Communication', 'Slack, Microsoft Teams', 9, TRUE, '2026-03-16T11:40:37.552142+00:00', '2026-03-16T11:40:37.552142+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.03_dim_connector_types (26 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."03_dim_connector_types" (id, code, name, category_code, auth_method, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('00d8fd3c-46e8-4170-b042-b673063d067e', 'aws_iam', 'AWS IAM', 'cloud_infrastructure', 'iam_role', NULL, 1, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('1cb31ec0-a3c5-4c98-8215-ec24fd900ebf', 'custom_webhook', 'Custom Webhook', 'custom', 'api_key', NULL, 26, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('265e3faa-7dd5-4272-8be0-b2c41d9bb7d7', 'google_workspace', 'Google Workspace', 'identity_provider', 'oauth2', NULL, 11, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('2923e24c-04ad-4bf0-a8d9-d2f05ffb21f8', 'azure_policy', 'Azure Policy', 'cloud_infrastructure', 'oauth2', NULL, 6, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('37cedc8a-1e34-40d1-9663-910d28b789c9', 'mysql', 'MySQL', 'database', 'connection_string', NULL, 18, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('3fad97c6-e0c4-486f-9b9f-f36e437385af', 'aws_config', 'AWS Config', 'cloud_infrastructure', 'iam_role', NULL, 3, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('4a1e19b1-d972-4eb7-8de3-d28200612194', 'custom_api', 'Custom API', 'custom', 'api_key', NULL, 25, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('4dedd9b8-2bed-406c-af91-4ed023d49b2b', 'kubernetes', 'Kubernetes', 'container_orchestration', 'certificate', NULL, 20, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('590b36fc-22c7-4d94-ac6a-a862ad48d57a', 'slack', 'Slack', 'communication', 'oauth2', NULL, 24, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('59905cdb-8d3d-4933-80e9-f7e61dcc76dc', 'gcp_iam', 'GCP IAM', 'cloud_infrastructure', 'oauth2', NULL, 8, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('5c72198e-1003-4ac1-8594-0a588b80e628', 'gitlab', 'GitLab', 'source_control', 'api_key', NULL, 13, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('5ef01b47-ed4a-4840-89cb-27fa9ed487ac', 'mongodb', 'MongoDB', 'database', 'connection_string', NULL, 19, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('7d5e4cfe-7cc2-4b5c-847b-944c5d196034', 'aws_s3', 'AWS S3', 'cloud_infrastructure', 'iam_role', NULL, 4, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('838ff7a7-1b4f-4417-b268-50b1a5a93225', 'gcp_audit', 'GCP Audit Log', 'cloud_infrastructure', 'oauth2', NULL, 9, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('8ce125a9-15e3-4f69-84ed-30f1fad69492', 'datadog', 'Datadog', 'logging_monitoring', 'api_key', NULL, 21, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('a2a7c492-3178-4cca-bc09-4dc556d0b774', 'servicenow', 'ServiceNow', 'itsm', 'basic', NULL, 16, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('b8201b9e-b003-44ba-a3c4-4a4e503a42db', 'github', 'GitHub', 'source_control', 'api_key', NULL, 12, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('c2127312-6052-419a-8a7f-d8ba02552f0a', 'azure_ad', 'Azure Active Directory', 'cloud_infrastructure', 'oauth2', NULL, 5, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('c249245d-fac4-40f1-b17e-baf638281031', 'jira', 'Jira', 'project_management', 'api_key', NULL, 15, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('d05a98d7-0732-45b9-8abf-0cd873c4919d', 'bitbucket', 'Bitbucket', 'source_control', 'api_key', NULL, 14, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('dd72ed29-badf-482d-9abe-e74eb4b19535', 'okta', 'Okta', 'identity_provider', 'api_key', NULL, 10, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('e228dd6b-b4a9-440d-a718-9ac947732533', 'postgresql', 'PostgreSQL', 'database', 'connection_string', NULL, 17, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('e8a37f12-41df-4415-a812-00fad16e4dfd', 'azure_monitor', 'Azure Monitor', 'cloud_infrastructure', 'oauth2', NULL, 7, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('f0fefd8c-d4ed-4736-9432-8dc6743c032f', 'elastic', 'Elastic', 'logging_monitoring', 'api_key', NULL, 23, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('fae8e707-a57d-41f7-814b-dd2fc4f5d841', 'aws_cloudtrail', 'AWS CloudTrail', 'cloud_infrastructure', 'iam_role', NULL, 2, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('fc71919f-3ec6-4af9-ae37-1cda15abf2ce', 'splunk', 'Splunk', 'logging_monitoring', 'api_key', NULL, 22, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, category_code = EXCLUDED.category_code, auth_method = EXCLUDED.auth_method, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.04_dim_signal_statuses (5 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."04_dim_signal_statuses" (id, code, name, description, sort_order, is_terminal, created_at)
  VALUES
      ('0403bd2d-6cf4-4b12-9fa5-36f1d1cf7a0d', 'validated', 'Validated', NULL, 3, FALSE, '2026-03-16T11:40:37.671434+00:00'),
      ('32702cb7-1d23-4de1-bfad-cc8727350521', 'testing', 'Testing', NULL, 2, FALSE, '2026-03-16T11:40:37.671434+00:00'),
      ('476493d7-5efc-4ebc-b5ba-f39683bf87b8', 'promoted', 'Promoted', NULL, 4, TRUE, '2026-03-16T11:40:37.671434+00:00'),
      ('b3784b76-4d32-4f64-9767-01ece38fdfb1', 'archived', 'Archived', NULL, 5, TRUE, '2026-03-16T11:40:37.671434+00:00'),
      ('c63d70d8-fbe9-4790-9185-71088ed869aa', 'draft', 'Draft', NULL, 1, FALSE, '2026-03-16T11:40:37.671434+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_terminal = EXCLUDED.is_terminal;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.05_dim_dataset_sources (8 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."05_dim_dataset_sources" (id, code, name, description, sort_order, created_at)
  VALUES
      ('411f7a9c-3d1a-4ce0-9169-58444a19a8a7', 'ai_generated_tests', 'AI-Generated Test Dataset', 'Test dataset auto-generated by Signal Spec Pipeline', 0, '2026-03-18T22:43:41.833657+00:00'),
      ('50f57f92-1e38-4a54-b4bd-b51efc0bceea', 'manual_json', 'Manual JSON', 'Hand-typed JSON in editor', 1, '2026-03-16T11:40:37.722935+00:00'),
      ('7d38f1fb-9c13-435d-b9a2-d85bb057b253', 'manual_upload', 'File Upload', 'Uploaded .json file', 2, '2026-03-16T11:40:37.722935+00:00'),
      ('80be4e84-d39f-42e3-99be-4e5018ca25fb', 'connector_pull', 'Connector Pull', 'Scheduled or on-demand collection', 4, '2026-03-16T11:40:37.722935+00:00'),
      ('8c362137-60d3-4aff-a2cc-15aa0e8633ab', 'template', 'Template', 'Started from a predefined template', 5, '2026-03-16T11:40:37.722935+00:00'),
      ('b00618f9-dad3-4c47-b679-f6b777399af1', 'live_capture', 'Live Capture', 'Data captured during a live session', 3, '2026-03-16T11:40:37.722935+00:00'),
      ('b73edd89-b47b-423d-8750-f108d13324aa', 'global_library', 'Global Library', NULL, 6, '2026-03-25T06:41:57.752322+00:00'),
      ('caf68f9f-eb63-4546-a8e7-ed8926e76d53', 'composite', 'Composite', 'Mixed sources with field-level overrides', 6, '2026-03-16T11:40:37.722935+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.06_dim_execution_statuses (6 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."06_dim_execution_statuses" (id, code, name, is_terminal, sort_order, created_at)
  VALUES
      ('0b105371-4215-407b-b9c9-97b7e2398aae', 'timeout', 'Timeout', TRUE, 5, '2026-03-16T11:40:37.784623+00:00'),
      ('5af1e18c-4cb1-42b1-bf85-a80b5671394e', 'queued', 'Queued', FALSE, 1, '2026-03-16T11:40:37.784623+00:00'),
      ('6929bc6d-82aa-4a53-99d4-c91013e4b2c3', 'failed', 'Failed', TRUE, 4, '2026-03-16T11:40:37.784623+00:00'),
      ('8448bd53-7663-423b-8962-052ee74de7fb', 'cancelled', 'Cancelled', TRUE, 6, '2026-03-16T11:40:37.784623+00:00'),
      ('c00f5635-b43c-4bc6-8471-52bcf57138fc', 'running', 'Running', FALSE, 2, '2026-03-16T11:40:37.784623+00:00'),
      ('c1e0e48f-2be0-4a6e-94cf-da50a9a736bf', 'completed', 'Completed', TRUE, 3, '2026-03-16T11:40:37.784623+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, is_terminal = EXCLUDED.is_terminal, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.07_dim_dataset_templates (7 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."07_dim_dataset_templates" (id, code, connector_type_code, name, description, json_schema, sample_payload, sort_order, is_active, created_at)
  VALUES
      ('43895884-68bd-4c85-82d9-3675f0633dbe', 'okta_users', 'okta', 'Okta Users', 'Okta user directory with MFA and status', '{"users": [{"id": "string", "email": "string", "login": "string", "groups": ["string"], "status": "string", "created": "string", "last_login": "string", "mfa_factors": [{"status": "string", "provider": "string", "factor_type": "string"}]}]}'::jsonb, '{"users": [{"id": "00u1a2b3c4", "email": "alice@acme.com", "login": "alice@acme.com", "groups": ["Everyone", "Engineering"], "status": "ACTIVE", "created": "2024-01-10T00:00:00Z", "last_login": "2026-03-15T09:00:00Z", "mfa_factors": [{"status": "ACTIVE", "provider": "OKTA", "factor_type": "push"}]}, {"id": "00u5e6f7g8", "email": "bob@acme.com", "login": "bob@acme.com", "groups": ["Everyone"], "status": "ACTIVE", "created": "2025-06-15T00:00:00Z", "last_login": "2026-02-01T00:00:00Z", "mfa_factors": []}]}'::jsonb, 0, TRUE, '2026-03-16T11:40:41.473552+00:00'),
      ('4b3eb70f-6be0-4319-8203-416d3cf8d784', 'azure_ad_users', 'azure_ad', 'Azure AD Users', 'Azure Active Directory user directory', '{"users": [{"id": "string", "displayName": "string", "mfaRegistered": "boolean", "accountEnabled": "boolean", "createdDateTime": "string", "assignedLicenses": ["string"], "userPrincipalName": "string", "lastSignInDateTime": "string"}]}'::jsonb, '{"users": [{"id": "abc-123", "displayName": "Alice Smith", "mfaRegistered": true, "accountEnabled": true, "createdDateTime": "2024-03-01T00:00:00Z", "assignedLicenses": ["E5"], "userPrincipalName": "alice@acme.onmicrosoft.com", "lastSignInDateTime": "2026-03-15T10:00:00Z"}, {"id": "def-456", "displayName": "Bob Jones", "mfaRegistered": false, "accountEnabled": true, "createdDateTime": "2025-09-01T00:00:00Z", "assignedLicenses": ["E3"], "userPrincipalName": "bob@acme.onmicrosoft.com", "lastSignInDateTime": "2026-01-15T00:00:00Z"}]}'::jsonb, 0, TRUE, '2026-03-16T11:40:41.473552+00:00'),
      ('6097f8b0-cf09-4e44-974f-48595c306bad', 'k8s_pod_security', 'kubernetes', 'Kubernetes Pod Security', 'Pod security policies and privilege levels', '{"pods": [{"name": "string", "host_pid": "boolean", "namespace": "string", "containers": [{"name": "string", "image": "string", "privileged": "boolean", "run_as_root": "boolean", "capabilities": ["string"], "read_only_root_fs": "boolean"}], "host_network": "boolean", "service_account": "string"}]}'::jsonb, '{"pods": [{"name": "web-server", "host_pid": false, "namespace": "production", "containers": [{"name": "nginx", "image": "nginx:1.25", "privileged": false, "run_as_root": false, "capabilities": [], "read_only_root_fs": true}], "host_network": false, "service_account": "web-sa"}, {"name": "debug-pod", "host_pid": true, "namespace": "default", "containers": [{"name": "debug", "image": "ubuntu:latest", "privileged": true, "run_as_root": true, "capabilities": ["NET_ADMIN", "SYS_PTRACE"], "read_only_root_fs": false}], "host_network": true, "service_account": "default"}]}'::jsonb, 0, TRUE, '2026-03-16T11:40:41.473552+00:00'),
      ('6d7af5bb-a378-4190-b32a-be6ebd905331', 'jira_workflows', 'jira', 'Jira Workflow Compliance', 'Jira project workflow and issue tracking compliance', '{"projects": [{"key": "string", "name": "string", "issues": [{"key": "string", "type": "string", "status": "string", "created": "string", "updated": "string", "assignee": "string", "priority": "string", "reporter": "string", "resolution_time_days": "integer"}]}]}'::jsonb, '{"projects": [{"key": "SEC", "name": "Security", "issues": [{"key": "SEC-101", "type": "Bug", "status": "Open", "created": "2026-03-01T00:00:00Z", "updated": "2026-03-15T00:00:00Z", "assignee": "alice@acme.com", "priority": "Critical", "reporter": "bob@acme.com", "resolution_time_days": null}, {"key": "SEC-100", "type": "Task", "status": "Done", "created": "2026-02-15T00:00:00Z", "updated": "2026-03-05T00:00:00Z", "assignee": "alice@acme.com", "priority": "High", "reporter": "alice@acme.com", "resolution_time_days": 18}]}]}'::jsonb, 0, TRUE, '2026-03-16T11:40:41.473552+00:00'),
      ('83d72ea3-c2d3-4432-bd6a-655ae1ab6e12', 'postgresql_audit_log', 'postgresql', 'PostgreSQL Audit Log', 'pg_audit log entries for access monitoring', '{"audit_entries": [{"user": "string", "database": "string", "statement": "string", "timestamp": "string", "client_addr": "string", "command_tag": "string", "object_name": "string", "object_type": "string"}]}'::jsonb, '{"audit_entries": [{"user": "app_user", "database": "production", "statement": "SELECT * FROM users WHERE role = ''admin''", "timestamp": "2026-03-15T14:30:00Z", "client_addr": "10.0.1.50", "command_tag": "SELECT", "object_name": "users", "object_type": "TABLE"}, {"user": "root", "database": "production", "statement": "DROP TABLE audit_logs", "timestamp": "2026-03-15T14:31:00Z", "client_addr": "192.168.1.1", "command_tag": "DROP", "object_name": "audit_logs", "object_type": "TABLE"}]}'::jsonb, 0, TRUE, '2026-03-16T11:40:41.473552+00:00'),
      ('bf700e40-80e6-4c8e-98c7-ee07846ce85d', 'aws_iam_users', 'aws_iam', 'AWS IAM Users', 'IAM user listing with MFA, access keys, last login', '{"users": [{"arn": "string", "groups": ["string"], "user_id": "string", "username": "string", "last_login": "string", "access_keys": [{"key_id": "string", "status": "string", "created_at": "string"}], "mfa_enabled": "boolean", "password_last_used": "string"}]}'::jsonb, '{"users": [{"arn": "arn:aws:iam::123456:user/admin", "groups": ["Admins"], "user_id": "AIDA123", "username": "admin", "last_login": "2026-03-15T10:30:00Z", "access_keys": [{"key_id": "AKIA123", "status": "Active", "created_at": "2025-01-15T00:00:00Z"}], "mfa_enabled": true, "password_last_used": "2026-03-15T10:30:00Z"}, {"arn": "arn:aws:iam::123456:user/dev-user", "groups": ["Developers"], "user_id": "AIDA456", "username": "dev-user", "last_login": "2026-03-10T08:00:00Z", "access_keys": [{"key_id": "AKIA456", "status": "Active", "created_at": "2024-06-01T00:00:00Z"}], "mfa_enabled": false, "password_last_used": "2026-03-10T08:00:00Z"}]}'::jsonb, 0, TRUE, '2026-03-16T11:40:41.473552+00:00'),
      ('fe5949a9-2bc2-401d-a44c-9c8684ddd440', 'github_branch_protection', 'github', 'GitHub Branch Protection', 'Repository branch protection rules for main/master', '{"repositories": [{"name": "string", "full_name": "string", "default_branch": "string", "branch_protection": {"enabled": "boolean", "enforce_admins": "boolean", "required_reviews": "integer", "dismiss_stale_reviews": "boolean", "required_status_checks": ["string"], "require_code_owner_reviews": "boolean"}}]}'::jsonb, '{"repositories": [{"name": "api-service", "full_name": "acme/api-service", "default_branch": "main", "branch_protection": {"enabled": true, "enforce_admins": false, "required_reviews": 2, "dismiss_stale_reviews": true, "required_status_checks": ["ci/build", "ci/test"], "require_code_owner_reviews": true}}, {"name": "frontend", "full_name": "acme/frontend", "default_branch": "main", "branch_protection": {"enabled": false, "enforce_admins": false, "required_reviews": 0, "dismiss_stale_reviews": false, "required_status_checks": [], "require_code_owner_reviews": false}}]}'::jsonb, 0, TRUE, '2026-03-16T11:40:41.473552+00:00')
  ON CONFLICT (code) DO UPDATE SET connector_type_code = EXCLUDED.connector_type_code, name = EXCLUDED.name, description = EXCLUDED.description, json_schema = EXCLUDED.json_schema, sample_payload = EXCLUDED.sample_payload, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.08_dim_threat_severities (5 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."08_dim_threat_severities" (id, code, name, sort_order, created_at)
  VALUES
      ('17ed1123-a78d-4829-8be2-6d1256de8140', 'info', 'Informational', 1, '2026-03-16T11:40:37.876018+00:00'),
      ('30233fc0-c2cf-450e-832e-92312cc6612b', 'high', 'High', 4, '2026-03-16T11:40:37.876018+00:00'),
      ('7636e876-7b7f-4d4f-85d3-b545da56c566', 'low', 'Low', 2, '2026-03-16T11:40:37.876018+00:00'),
      ('904fcff7-5dd8-4148-9e07-b70e681ecbde', 'critical', 'Critical', 5, '2026-03-16T11:40:37.876018+00:00'),
      ('b42bdaa2-cd52-4d77-b1ef-457360e31ab9', 'medium', 'Medium', 3, '2026-03-16T11:40:37.876018+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.09_dim_policy_action_types (8 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."09_dim_policy_action_types" (id, code, name, description, sort_order, is_active, created_at)
  VALUES
      ('00c5d3dc-176d-49f0-8e25-4d3bf02b9920', 'escalate', 'Escalate', 'Escalate to specified role/user', 4, TRUE, '2026-03-16T11:40:37.928523+00:00'),
      ('327571a2-3fa8-41de-91e6-926438a52e86', 'quarantine', 'Quarantine', 'Isolate resource for investigation', 8, TRUE, '2026-03-16T11:40:37.928523+00:00'),
      ('561200e2-8895-421a-b32f-bf1f9e3d5a26', 'notification', 'Notification', 'Send alert via configured channel', 1, TRUE, '2026-03-16T11:40:37.928523+00:00'),
      ('7db7caac-37b9-4b77-90f6-ae842d6ffb99', 'disable_access', 'Disable Access', 'Revoke user/session access', 7, TRUE, '2026-03-16T11:40:37.928523+00:00'),
      ('881852f5-2545-4033-8b2f-3813a64955dd', 'webhook', 'Webhook', 'Send HTTP POST to external URL', 6, TRUE, '2026-03-16T11:40:37.928523+00:00'),
      ('8b462654-62bf-4b52-b981-5edf8829c3e0', 'create_task', 'Create Task', 'Create remediation task in task manager', 5, TRUE, '2026-03-16T11:40:37.928523+00:00'),
      ('c1f135c3-b5ee-451d-9a73-57e518438e74', 'rca_agent', 'RCA Agent', 'Run root cause analysis agent', 3, TRUE, '2026-03-16T11:40:37.928523+00:00'),
      ('f06f891a-bff0-40e1-8ef2-29a4ff7f96ac', 'evidence_report', 'Evidence Report', 'Generate compliance evidence document', 2, TRUE, '2026-03-16T11:40:37.928523+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.10_dim_library_types (4 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."10_dim_library_types" (id, code, name, description, sort_order, created_at)
  VALUES
      ('1225df70-0e39-4d7c-86b5-f3a57b876d2c', 'compliance', 'Compliance', NULL, 2, '2026-03-16T11:40:37.987413+00:00'),
      ('28a6410e-148e-458e-880c-8b01b51e69f7', 'operational', 'Operational', NULL, 3, '2026-03-16T11:40:37.987413+00:00'),
      ('74ee4caa-fd0f-40f0-886e-ccf26936b67f', 'custom', 'Custom', NULL, 4, '2026-03-16T11:40:37.987413+00:00'),
      ('786ac1b0-228e-470f-912d-4086bb1dd23f', 'asset_security', 'Asset Security', NULL, 1, '2026-03-16T11:40:37.987413+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.11_dim_asset_versions (11 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."11_dim_asset_versions" (id, connector_type_code, version_code, version_label, is_latest, is_active, sort_order, created_at)
  VALUES
      ('3cb501f4-b56e-4b2a-8f88-d1cf6eefdce9', 'aws_iam', 'v2024', 'AWS IAM 2024', FALSE, TRUE, 1, '2026-03-16T11:40:38.041322+00:00'),
      ('7d526882-344c-4493-9531-4afd2073a1fa', 'postgresql', '14', 'PostgreSQL 14', FALSE, TRUE, 1, '2026-03-16T11:40:38.041322+00:00'),
      ('a6b06c90-ef99-4d55-8e15-e9287966f1fc', 'kubernetes', '1.31', 'Kubernetes 1.31', TRUE, TRUE, 4, '2026-03-16T11:40:38.041322+00:00'),
      ('b55b716f-0f65-441e-a712-ed6e0d845d84', 'kubernetes', '1.29', 'Kubernetes 1.29', FALSE, TRUE, 2, '2026-03-16T11:40:38.041322+00:00'),
      ('b7811718-2993-405a-b95f-5b99cd14bb78', 'mysql', '8.4', 'MySQL 8.4', TRUE, TRUE, 2, '2026-03-16T11:40:38.041322+00:00'),
      ('c85ffc16-2c42-4bb4-9c9d-2efba604eab2', 'mysql', '8.0', 'MySQL 8.0', FALSE, TRUE, 1, '2026-03-16T11:40:38.041322+00:00'),
      ('d04304af-e47a-4eaf-9725-06ca97f247d0', 'kubernetes', '1.30', 'Kubernetes 1.30', FALSE, TRUE, 3, '2026-03-16T11:40:38.041322+00:00'),
      ('d0f90d89-6f68-4f46-bcfb-dc6d76153f64', 'kubernetes', '1.28', 'Kubernetes 1.28', FALSE, TRUE, 1, '2026-03-16T11:40:38.041322+00:00'),
      ('e4899db5-5afd-4aa2-ade3-9d099c7be4f7', 'postgresql', '15', 'PostgreSQL 15', FALSE, TRUE, 2, '2026-03-16T11:40:38.041322+00:00'),
      ('f72bae21-f508-48ab-b409-9f4d292d52b1', 'postgresql', '16', 'PostgreSQL 16', TRUE, TRUE, 3, '2026-03-16T11:40:38.041322+00:00'),
      ('fad7c08f-bb6b-4b41-9072-e5f12b7fe5be', 'aws_iam', 'v2025', 'AWS IAM 2025', TRUE, TRUE, 2, '2026-03-16T11:40:38.041322+00:00')
  ON CONFLICT (connector_type_code, version_code) DO UPDATE SET version_label = EXCLUDED.version_label, is_latest = EXCLUDED.is_latest, is_active = EXCLUDED.is_active, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.14_dim_asset_types (14 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."14_dim_asset_types" (id, code, provider_code, name, description, is_active, created_at)
  VALUES
      ('1fa10ab7-2dae-4d43-b75e-858bb8154ca3', 'github_org', 'github', 'GitHub Organization', 'A GitHub organization', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('222f4b31-0683-4ae4-b681-5356d4afbbab', 'github_deploy_key', 'github', 'GitHub Deploy Key', 'SSH deploy key on repository', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('29198884-f5ed-4c9c-929a-f2e9a4c6f886', 'github_team_member', 'github', 'GitHub Team Member', 'Team membership with role', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('3644644f-9ab4-4225-a2d4-dad9e7da9fc6', 'azure_blob_container', 'azure_storage', 'Azure Blob Container', 'A Blob container within a Storage Account', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('54886e86-4837-48f0-81a6-cd52edd8f703', 'github_branch_protection', 'github', 'Branch Protection Rule', 'Branch protection rules for a GitHub repository', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('54e650f5-3b48-4b98-bfe7-d18ab1714a4c', 'github_webhook', 'github', 'GitHub Webhook', 'Repository webhook configuration', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('6fb4b404-3ae3-4208-a809-4ed56b9616f5', 'github_repo', 'github', 'GitHub Repository', 'A repository within a GitHub org', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('8ed1d37c-e05d-4876-b6e7-43636a9d13b7', 'azure_storage_network_rule', 'azure_storage', 'Azure Storage Network Rule', 'Network rules for an Azure Storage Account', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('a396b874-dc6c-44b0-8f0a-8d975a77d27d', 'github_org_member', 'github', 'Organization Member', 'A member of the GitHub organization', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('a8733c73-b34a-4fee-83c5-34ec60812891', 'github_secret', 'github', 'GitHub Secret', 'Organization or repository secret (name only)', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('cdd27225-d6b3-4b1e-80ab-f8643a4ebb83', 'github_team', 'github', 'GitHub Team', 'A team within a GitHub organization', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('d5670833-bbbc-44d8-9570-9841cc757b38', 'github_collaborator', 'github', 'GitHub Outside Collaborator', 'External collaborator with repo access', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('dcc1e80e-d847-4b6e-9b02-1002dce5e7f3', 'azure_storage_account', 'azure_storage', 'Azure Storage Account', 'An Azure Storage Account', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('fcfb747b-629c-457e-ae26-a840704f189f', 'github_action_workflow', 'github', 'GitHub Action Workflow', 'CI/CD workflow definition', TRUE, '2026-03-17T07:19:19.53681+00:00')
  ON CONFLICT (code) DO UPDATE SET provider_code = EXCLUDED.provider_code, name = EXCLUDED.name, description = EXCLUDED.description, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.15_dim_asset_statuses (6 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."15_dim_asset_statuses" (code, name, description, is_terminal)
  VALUES
      ('active', 'Active', 'Asset verified present in last collection', FALSE),
      ('deleted', 'Deleted', 'Asset confirmed absent at provider', TRUE),
      ('discovered', 'Discovered', 'Asset first found by collector', FALSE),
      ('error', 'Error', 'Asset collection encountered an error', FALSE),
      ('modified', 'Modified', 'Asset properties changed since last snapshot', FALSE),
      ('stale', 'Stale', 'Asset not found in last collection run', FALSE)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_terminal = EXCLUDED.is_terminal;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.16_dim_provider_definitions (16 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."16_dim_provider_definitions" (id, code, name, driver_module, default_auth_method, supports_log_collection, supports_steampipe, supports_custom_driver, steampipe_plugin, rate_limit_rpm, config_schema, is_active, is_coming_soon, created_at, updated_at, current_api_version)
  VALUES
      ('08f4acff-93a7-48f4-b0ef-499b4dce7c73', 'gcp_audit', 'GCP Audit Log', 'backend.10_sandbox.18_drivers.gcp_audit.GcpAuditDriver', 'oauth2', TRUE, TRUE, TRUE, 'turbot/gcp', 60, '{"fields": [{"key": "project_id", "type": "text", "label": "GCP Project ID", "order": 1, "required": true, "credential": false, "placeholder": "my-project-123456"}, {"key": "service_account_key_json", "hint": "Required roles: roles/logging.viewer, roles/viewer", "type": "textarea", "label": "Service Account Key (JSON)", "order": 2, "required": true, "credential": true, "placeholder": "{ \"type\": \"service_account\", \"project_id\": \"...\", ... }"}, {"key": "log_filter", "hint": "GCP Logging filter to narrow which audit logs to collect", "type": "text", "label": "Log Filter (optional)", "order": 3, "required": false, "credential": false, "placeholder": "protoPayload.serviceName=iam.googleapis.com"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.596448+00:00', '2026-03-16T12:28:01.596448+00:00', NULL),
      ('15de556b-4f5c-4bb5-ab07-564298109ce6', 'postgresql', 'PostgreSQL', 'backend.10_sandbox.18_drivers.postgresql.PostgreSQLDriver', 'connection_string', FALSE, TRUE, TRUE, 'turbot/postgres', 60, '{"fields": [{"key": "host", "hint": "Hostname or IP address of the PostgreSQL server", "type": "text", "label": "Host", "order": 1, "required": true, "credential": false, "placeholder": "db.mycompany.com"}, {"key": "port", "hint": "Default is 5432", "type": "text", "label": "Port", "order": 2, "required": false, "credential": false, "validation": "^[0-9]{1,5}$", "placeholder": "5432"}, {"key": "database", "type": "text", "label": "Database Name", "order": 3, "required": true, "credential": false, "placeholder": "mydb"}, {"key": "username", "hint": "Use a read-only user — SELECT privileges on relevant schemas", "type": "text", "label": "Username", "order": 4, "required": true, "credential": false, "placeholder": "readonly_user"}, {"key": "password", "type": "password", "label": "Password", "order": 5, "required": true, "credential": true}, {"key": "ssl_mode", "hint": "Recommended: require or verify-full for production", "type": "select", "label": "SSL Mode", "order": 6, "options": ["require", "verify-ca", "verify-full", "prefer", "disable"], "required": false, "credential": false}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.500433+00:00', '2026-03-16T12:28:01.500433+00:00', NULL),
      ('3b27bd44-bc05-4e61-99ab-4c50197dcc8c', 'jira', 'Jira', 'backend.10_sandbox.18_drivers.jira.JiraDriver', 'api_key', FALSE, TRUE, TRUE, 'turbot/jira', 60, '{"fields": [{"key": "base_url", "hint": "Your Jira Cloud or Server URL (no trailing slash)", "type": "text", "label": "Jira Base URL", "order": 1, "required": true, "credential": false, "placeholder": "https://mycompany.atlassian.net"}, {"key": "email", "hint": "Email associated with the API token", "type": "text", "label": "Account Email", "order": 2, "required": true, "credential": false, "placeholder": "admin@mycompany.com"}, {"key": "api_token", "hint": "Created at id.atlassian.com → Security → API Tokens", "type": "password", "label": "API Token", "order": 3, "required": true, "credential": true, "placeholder": "ATATT3xFfGF0..."}, {"key": "project_keys", "hint": "Comma-separated list of Jira project keys to sync. Leave blank to sync all accessible projects.", "type": "text", "label": "Project Keys (optional)", "order": 4, "required": false, "credential": false, "placeholder": "PROJ,INFRA,SEC"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.476464+00:00', '2026-03-16T12:28:01.476464+00:00', NULL),
      ('3f7e7a6a-e124-464e-afa1-8e9843bc2f8e', 'aws_s3', 'AWS S3', 'backend.10_sandbox.18_drivers.aws_s3.AwsS3Driver', 'iam_role', FALSE, TRUE, TRUE, 'turbot/aws', 120, '{"fields": [{"key": "account_id", "type": "text", "label": "AWS Account ID", "order": 1, "required": true, "credential": false, "validation": "^[0-9]{12}$", "placeholder": "123456789012"}, {"key": "region", "type": "select", "label": "Region", "order": 2, "options": ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"], "required": true, "credential": false}, {"key": "bucket_names", "hint": "Comma-separated list. Leave blank to enumerate all accessible buckets.", "type": "text", "label": "Bucket Names (optional)", "order": 3, "required": false, "credential": false, "placeholder": "my-bucket, logs-bucket"}, {"key": "access_key_id", "type": "text", "label": "Access Key ID", "order": 4, "required": false, "credential": true}, {"key": "secret_access_key", "type": "password", "label": "Secret Access Key", "order": 5, "required": false, "credential": true}, {"key": "role_arn", "type": "text", "label": "IAM Role ARN", "order": 6, "required": false, "credential": false, "placeholder": "arn:aws:iam::123456789012:role/KControlReadOnly"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.619054+00:00', '2026-03-16T12:28:01.619054+00:00', NULL),
      ('4c20508e-feeb-40ff-b57d-a6e249e880a3', 'azure_storage', 'Azure Storage', 'backend.10_sandbox.18_drivers.azure_storage.AzureStorageDriver', 'service_principal', TRUE, TRUE, TRUE, 'turbot/azure', 1200, '{"fields": [{"key": "subscription_id", "type": "text", "label": "Subscription ID", "order": 1, "required": true, "credential": false, "validation": "^[0-9a-f-]{36}$", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "tenant_id", "type": "text", "label": "Tenant ID", "order": 2, "required": true, "credential": false, "validation": "^[0-9a-f-]{36}$", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_id", "type": "text", "label": "Client ID", "order": 3, "required": true, "credential": false, "validation": "^[0-9a-f-]{36}$", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_secret", "type": "password", "label": "Client Secret", "order": 4, "required": true, "credential": true}, {"key": "resource_group", "hint": "Leave empty to collect all storage accounts in the subscription", "type": "text", "label": "Resource Group (optional)", "order": 5, "required": false, "credential": false}]}'::jsonb, TRUE, FALSE, '2026-03-16T11:40:50.992924+00:00', '2026-03-16T11:40:50.992924+00:00', '2023-01-01'),
      ('4d32e1a1-6435-4196-a1bc-8274b3f237ab', 'azure_monitor', 'Azure Monitor', 'backend.10_sandbox.18_drivers.azure_monitor.AzureMonitorDriver', 'oauth2', TRUE, TRUE, TRUE, 'turbot/azure', 60, '{"fields": [{"key": "tenant_id", "type": "text", "label": "Tenant ID", "order": 1, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "subscription_id", "type": "text", "label": "Subscription ID", "order": 2, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_id", "hint": "Requires: Monitoring Reader role on the subscription", "type": "text", "label": "Application (Client) ID", "order": 3, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_secret", "type": "password", "label": "Client Secret", "order": 4, "required": true, "credential": true}, {"key": "workspace_id", "hint": "Only required for Log Analytics / KQL query collection", "type": "text", "label": "Log Analytics Workspace ID (optional)", "order": 5, "required": false, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.641263+00:00', '2026-03-16T12:28:01.641263+00:00', NULL),
      ('5d03802f-0374-4740-a533-30a10db48c55', 'aws_iam', 'AWS IAM', 'backend.10_sandbox.18_drivers.aws_iam.AwsIamDriver', 'iam_role', FALSE, TRUE, TRUE, 'turbot/aws', 120, '{"fields": [{"key": "account_id", "hint": "12-digit AWS account number", "type": "text", "label": "AWS Account ID", "order": 1, "required": true, "credential": false, "validation": "^[0-9]{12}$", "placeholder": "123456789012"}, {"key": "region", "hint": "Primary AWS region for API calls", "type": "select", "label": "Default Region", "order": 2, "options": ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ca-central-1", "sa-east-1"], "required": true, "credential": false, "placeholder": "us-east-1"}, {"key": "access_key_id", "hint": "Use an IAM role (preferred) or provide access key. Required if not using instance role.", "type": "text", "label": "Access Key ID", "order": 3, "required": false, "credential": true, "placeholder": "AKIAIOSFODNN7EXAMPLE"}, {"key": "secret_access_key", "hint": "Secret for the access key above. Not required when using IAM instance roles.", "type": "password", "label": "Secret Access Key", "order": 4, "required": false, "credential": true, "placeholder": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"}, {"key": "role_arn", "hint": "If set, the connector will assume this role. Recommended for cross-account access.", "type": "text", "label": "IAM Role ARN (assume role)", "order": 5, "required": false, "credential": false, "placeholder": "arn:aws:iam::123456789012:role/KControlReadOnly"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.348174+00:00', '2026-03-16T12:28:01.348174+00:00', NULL),
      ('5f6a7274-5427-447c-93aa-5c99834f5b4e', 'azure_ad', 'Azure Active Directory', 'backend.10_sandbox.18_drivers.azure_ad.AzureAdDriver', 'oauth2', FALSE, TRUE, TRUE, 'turbot/azuread', 120, '{"fields": [{"key": "tenant_id", "hint": "Found in Azure Portal → Azure Active Directory → Overview → Tenant ID", "type": "text", "label": "Tenant ID (Directory ID)", "order": 1, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_id", "hint": "App registration client ID. Requires: User.Read.All, Group.Read.All, Directory.Read.All", "type": "text", "label": "Application (Client) ID", "order": 2, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_secret", "hint": "Client secret value from app registration (not the secret ID)", "type": "password", "label": "Client Secret", "order": 3, "required": true, "credential": true, "placeholder": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}, {"key": "subscription_id", "hint": "Azure subscription ID — required for Azure Policy / Azure Monitor connectors", "type": "text", "label": "Subscription ID", "order": 4, "required": false, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.398528+00:00', '2026-03-16T12:28:01.398528+00:00', NULL),
      ('a903e73f-ea46-4e88-8d0e-5ed7dddd5594', 'kubernetes', 'Kubernetes', 'backend.10_sandbox.18_drivers.kubernetes.KubernetesDriver', 'certificate', TRUE, TRUE, TRUE, 'turbot/kubernetes', 60, '{"fields": [{"key": "cluster_name", "hint": "A unique name to identify this cluster", "type": "text", "label": "Cluster Name", "order": 1, "required": true, "credential": false, "placeholder": "prod-k8s-cluster"}, {"key": "api_server_url", "hint": "Kubernetes API server endpoint", "type": "text", "label": "API Server URL", "order": 2, "required": true, "credential": false, "placeholder": "https://k8s.mycompany.com:6443"}, {"key": "kubeconfig", "hint": "Paste kubeconfig content. Preferred over service account token.", "type": "textarea", "label": "Kubeconfig (YAML or base64)", "order": 3, "required": false, "credential": true, "placeholder": "apiVersion: v1\nkind: Config\n..."}, {"key": "service_account_token", "hint": "Alternative to kubeconfig. Bearer token for a read-only service account.", "type": "password", "label": "Service Account Token", "order": 4, "required": false, "credential": true}, {"key": "ca_certificate", "hint": "Base64-encoded cluster CA certificate. Required when not embedded in kubeconfig.", "type": "textarea", "label": "CA Certificate (base64)", "order": 5, "required": false, "credential": false}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.523694+00:00', '2026-03-16T12:28:01.523694+00:00', NULL),
      ('ba6c5595-2843-4484-a351-2bd2cd54f997', 'azure_policy', 'Azure Policy', 'backend.10_sandbox.18_drivers.azure_policy.AzurePolicyDriver', 'oauth2', FALSE, TRUE, TRUE, 'turbot/azure', 60, '{"fields": [{"key": "tenant_id", "type": "text", "label": "Tenant ID", "order": 1, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "subscription_id", "type": "text", "label": "Subscription ID", "order": 2, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_id", "hint": "App registration with Policy Insights Reader role", "type": "text", "label": "Application (Client) ID", "order": 3, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_secret", "type": "password", "label": "Client Secret", "order": 4, "required": true, "credential": true}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.571082+00:00', '2026-03-16T12:28:01.571082+00:00', NULL),
      ('c2280b2f-4dc7-486d-9341-1eca9c3c631d', 'gcp_iam', 'GCP IAM', 'backend.10_sandbox.18_drivers.gcp_iam.GcpIamDriver', 'oauth2', FALSE, TRUE, TRUE, 'turbot/gcp', 120, '{"fields": [{"key": "project_id", "hint": "GCP project ID (not the project number)", "type": "text", "label": "GCP Project ID", "order": 1, "required": true, "credential": false, "placeholder": "my-project-123456"}, {"key": "service_account_key_json", "hint": "Paste the full JSON key file content. Required roles: roles/iam.securityReviewer, roles/viewer", "type": "textarea", "label": "Service Account Key (JSON)", "order": 2, "required": true, "credential": true, "placeholder": "{ \"type\": \"service_account\", \"project_id\": \"...\", ... }"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.42308+00:00', '2026-03-16T12:28:01.42308+00:00', NULL),
      ('dab244d5-3263-4efa-9387-bb849250557a', 'gitlab', 'GitLab', 'backend.10_sandbox.18_drivers.gitlab.GitLabDriver', 'api_key', FALSE, TRUE, TRUE, 'turbot/gitlab', 300, '{"fields": [{"key": "group_path", "hint": "Top-level group path (e.g. gitlab.com/<group>). Use nested paths like group/subgroup.", "type": "text", "label": "Group / Namespace", "order": 1, "required": true, "credential": false, "placeholder": "my-group"}, {"key": "personal_access_token", "hint": "Required scopes: read_api, read_user, read_repository", "type": "password", "label": "Personal Access Token", "order": 2, "required": true, "credential": true, "placeholder": "glpat-xxxxxxxxxxxxxxxxxxxx"}, {"key": "base_url", "hint": "Leave blank for gitlab.com. Set only for self-hosted installations.", "type": "text", "label": "GitLab Self-Hosted URL", "order": 3, "required": false, "credential": false, "placeholder": "https://gitlab.example.com"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.3217+00:00', '2026-03-16T12:28:01.3217+00:00', NULL),
      ('daf878db-6caf-409f-957e-7b4650239970', 'okta', 'Okta', 'backend.10_sandbox.18_drivers.okta.OktaDriver', 'api_key', TRUE, TRUE, TRUE, 'turbot/okta', 120, '{"fields": [{"key": "domain", "hint": "Your Okta tenant domain — found in the browser URL when signed in", "type": "text", "label": "Okta Domain", "order": 1, "required": true, "credential": false, "placeholder": "mycompany.okta.com"}, {"key": "api_token", "hint": "Created in Okta Admin → Security → API → Tokens. Must have read-only admin scope.", "type": "password", "label": "API Token", "order": 2, "required": true, "credential": true, "placeholder": "00xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.450549+00:00', '2026-03-16T12:28:01.450549+00:00', NULL),
      ('f422724c-2e2f-4f53-b636-e4a46a1083b5', 'github', 'GitHub', 'backend.10_sandbox.18_drivers.github.GitHubDriver', 'api_key', TRUE, TRUE, TRUE, 'turbot/github', 5000, '{"fields": [{"key": "org_name", "hint": "The GitHub organization slug (shown in the URL: github.com/<org>)", "type": "text", "label": "Organization Name", "order": 1, "required": true, "credential": false, "placeholder": "my-github-org"}, {"key": "personal_access_token", "hint": "Must be a Classic PAT (not fine-grained). Go to GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic). Required scopes: read:org, repo, admin:org, read:user", "type": "password", "label": "Personal Access Token (Classic)", "order": 2, "required": true, "credential": true, "placeholder": "ghp_xxxxxxxxxxxxxxxxxxxx"}, {"key": "base_url", "hint": "Leave blank for github.com. Set only for GitHub Enterprise Server (e.g. https://github.example.com).", "type": "text", "label": "GitHub Enterprise URL", "order": 3, "required": false, "credential": false, "placeholder": "https://github.example.com"}]}'::jsonb, TRUE, FALSE, '2026-03-16T11:40:50.992924+00:00', '2026-03-16T12:28:01.297129+00:00', '2022-11-28'),
      ('f7b98d08-476e-41f3-a211-fc2f0269f54f', 'aws_cloudtrail', 'AWS CloudTrail', 'backend.10_sandbox.18_drivers.aws_cloudtrail.AwsCloudTrailDriver', 'iam_role', TRUE, TRUE, TRUE, 'turbot/aws', 60, '{"fields": [{"key": "account_id", "hint": "12-digit AWS account number", "type": "text", "label": "AWS Account ID", "order": 1, "required": true, "credential": false, "validation": "^[0-9]{12}$", "placeholder": "123456789012"}, {"key": "region", "type": "select", "label": "Region", "order": 2, "options": ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"], "required": true, "credential": false}, {"key": "trail_arn", "hint": "Leave blank to auto-discover all trails in the account", "type": "text", "label": "CloudTrail Trail ARN", "order": 3, "required": false, "credential": false, "placeholder": "arn:aws:cloudtrail:us-east-1:123456789012:trail/my-trail"}, {"key": "access_key_id", "type": "text", "label": "Access Key ID", "order": 4, "required": false, "credential": true, "placeholder": "AKIAIOSFODNN7EXAMPLE"}, {"key": "secret_access_key", "type": "password", "label": "Secret Access Key", "order": 5, "required": false, "credential": true}, {"key": "role_arn", "type": "text", "label": "IAM Role ARN", "order": 6, "required": false, "credential": false, "placeholder": "arn:aws:iam::123456789012:role/KControlReadOnly"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.375487+00:00', '2026-03-16T12:28:01.375487+00:00', NULL),
      ('ffee8c1d-85d5-44b6-87ae-848802cf6255', 'slack', 'Slack', 'backend.10_sandbox.18_drivers.slack.SlackDriver', 'oauth2', FALSE, TRUE, TRUE, 'turbot/slack', 60, '{"fields": [{"key": "workspace_name", "hint": "Your Slack workspace slug (mycompany.slack.com → enter mycompany)", "type": "text", "label": "Slack Workspace Name", "order": 1, "required": true, "credential": false, "placeholder": "mycompany"}, {"key": "bot_token", "hint": "From Slack App → OAuth & Permissions. Required scopes: channels:read, users:read, team:read", "type": "password", "label": "Bot OAuth Token", "order": 2, "required": true, "credential": true, "placeholder": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.546664+00:00', '2026-03-16T12:28:01.546664+00:00', NULL)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, driver_module = EXCLUDED.driver_module, default_auth_method = EXCLUDED.default_auth_method, supports_log_collection = EXCLUDED.supports_log_collection, supports_steampipe = EXCLUDED.supports_steampipe, supports_custom_driver = EXCLUDED.supports_custom_driver, steampipe_plugin = EXCLUDED.steampipe_plugin, rate_limit_rpm = EXCLUDED.rate_limit_rpm, config_schema = EXCLUDED.config_schema, is_active = EXCLUDED.is_active, is_coming_soon = EXCLUDED.is_coming_soon, updated_at = EXCLUDED.updated_at, current_api_version = EXCLUDED.current_api_version;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 15_sandbox.18_dim_asset_access_roles (3 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."18_dim_asset_access_roles" (code, name, description, sort_order)
  VALUES
      ('edit', 'Edit', 'Can modify asset configuration and trigger collection', 3),
      ('use', 'Use', 'Can reference asset data in signals and policies', 2),
      ('view', 'View', 'Can view asset properties and snapshots', 1)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: GRC
-- Extracted: 2026-03-27T14:17:53.876453
-- ═════════════════════════════════════════════════════════════════════════════

-- 05_grc_library.02_dim_framework_types (6 rows)
DO $$ BEGIN
  INSERT INTO "05_grc_library"."02_dim_framework_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('a0010001-0000-0000-0000-000000000000', 'compliance_standard', 'Compliance Standard', 'Regulatory compliance frameworks (SOC 2, PCI DSS, HIPAA)', 1, TRUE, '2026-03-15T18:21:16.403575', '2026-03-15T18:21:16.403575'),
      ('a0010002-0000-0000-0000-000000000000', 'security_framework', 'Security Framework', 'Information security frameworks (ISO 27001, NIST CSF)', 2, TRUE, '2026-03-15T18:21:16.403575', '2026-03-15T18:21:16.403575'),
      ('a0010003-0000-0000-0000-000000000000', 'privacy_regulation', 'Privacy Regulation', 'Data privacy regulations (GDPR, CCPA, LGPD)', 3, TRUE, '2026-03-15T18:21:16.403575', '2026-03-15T18:21:16.403575'),
      ('a0010004-0000-0000-0000-000000000000', 'industry_standard', 'Industry Standard', 'Industry-specific standards (HITRUST, FedRAMP)', 4, TRUE, '2026-03-15T18:21:16.403575', '2026-03-15T18:21:16.403575'),
      ('a0010005-0000-0000-0000-000000000000', 'internal_policy', 'Internal Policy', 'Organisation-defined internal policies', 5, TRUE, '2026-03-15T18:21:16.403575', '2026-03-15T18:21:16.403575'),
      ('a0010006-0000-0000-0000-000000000000', 'custom', 'Custom', 'Custom framework definitions', 6, TRUE, '2026-03-15T18:21:16.403575', '2026-03-15T18:21:16.403575')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 05_grc_library.03_dim_framework_categories (6 rows)
DO $$ BEGIN
  INSERT INTO "05_grc_library"."03_dim_framework_categories" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('a0000001-0000-0000-0000-000000000000', 'compliance', 'Compliance', 'Regulatory and compliance frameworks', 1, TRUE, '2026-03-15T18:21:16.435208', '2026-03-15T18:21:16.435208'),
      ('a0000002-0000-0000-0000-000000000000', 'security', 'Security', 'Information security and cybersecurity frameworks', 2, TRUE, '2026-03-15T18:21:16.435208', '2026-03-15T18:21:16.435208'),
      ('a0000003-0000-0000-0000-000000000000', 'privacy', 'Privacy', 'Data privacy and protection frameworks', 3, TRUE, '2026-03-15T18:21:16.435208', '2026-03-15T18:21:16.435208'),
      ('a0000004-0000-0000-0000-000000000000', 'industry', 'Industry', 'Industry-specific regulatory frameworks', 4, TRUE, '2026-03-15T18:21:16.435208', '2026-03-15T18:21:16.435208'),
      ('a0000005-0000-0000-0000-000000000000', 'operational', 'Operational', 'Operational risk and resilience frameworks', 5, TRUE, '2026-03-15T18:21:16.435208', '2026-03-15T18:21:16.435208'),
      ('a0000006-0000-0000-0000-000000000000', 'custom', 'Custom', 'Organisation-defined custom frameworks', 6, TRUE, '2026-03-15T18:21:16.435208', '2026-03-15T18:21:16.435208')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 05_grc_library.04_dim_control_categories (14 rows)
DO $$ BEGIN
  INSERT INTO "05_grc_library"."04_dim_control_categories" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('b0000001-0000-0000-0000-000000000000', 'access_control', 'Access Control', 'User authentication, authorisation, MFA', 1, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000002-0000-0000-0000-000000000000', 'change_management', 'Change Management', 'Change control, SDLC, release processes', 2, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000003-0000-0000-0000-000000000000', 'incident_response', 'Incident Response', 'Detection, response, and recovery', 3, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000004-0000-0000-0000-000000000000', 'data_protection', 'Data Protection', 'Encryption, DLP, data classification', 4, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000005-0000-0000-0000-000000000000', 'network_security', 'Network Security', 'Firewalls, segmentation, monitoring', 5, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000006-0000-0000-0000-000000000000', 'physical_security', 'Physical Security', 'Facility access, physical controls', 6, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000007-0000-0000-0000-000000000000', 'risk_management', 'Risk Management', 'Risk assessment, treatment, tracking', 7, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000008-0000-0000-0000-000000000000', 'vendor_management', 'Vendor Management', 'Third-party risk and due diligence', 8, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000009-0000-0000-0000-000000000000', 'hr_security', 'HR Security', 'Hiring, offboarding, security training', 9, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000010-0000-0000-0000-000000000000', 'business_continuity', 'Business Continuity', 'BCP, DR, availability', 10, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000011-0000-0000-0000-000000000000', 'cryptography', 'Cryptography', 'Key management, cert rotation', 11, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000012-0000-0000-0000-000000000000', 'logging_monitoring', 'Logging & Monitoring', 'Audit logs, SIEM, alerting', 12, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000013-0000-0000-0000-000000000000', 'asset_management', 'Asset Management', 'Asset inventory, lifecycle, classification', 13, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762'),
      ('b0000014-0000-0000-0000-000000000000', 'compliance', 'Compliance', 'Regulatory compliance checks', 14, TRUE, '2026-03-15T18:21:16.465762', '2026-03-15T18:21:16.465762')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 05_grc_library.05_dim_control_criticalities (4 rows)
DO $$ BEGIN
  INSERT INTO "05_grc_library"."05_dim_control_criticalities" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('c0000001-0000-0000-0000-000000000000', 'critical', 'Critical', 'Must be implemented — breach = immediate exposure', 1, TRUE, '2026-03-15T18:21:16.499194', '2026-03-15T18:21:16.499194'),
      ('c0000002-0000-0000-0000-000000000000', 'high', 'High', 'Should be implemented promptly', 2, TRUE, '2026-03-15T18:21:16.499194', '2026-03-15T18:21:16.499194'),
      ('c0000003-0000-0000-0000-000000000000', 'medium', 'Medium', 'Implement within current compliance cycle', 3, TRUE, '2026-03-15T18:21:16.499194', '2026-03-15T18:21:16.499194'),
      ('c0000004-0000-0000-0000-000000000000', 'low', 'Low', 'Implement at next opportunity', 4, TRUE, '2026-03-15T18:21:16.499194', '2026-03-15T18:21:16.499194')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 05_grc_library.07_dim_test_types (3 rows)
DO $$ BEGIN
  INSERT INTO "05_grc_library"."07_dim_test_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('e0000001-0000-0000-0000-000000000000', 'automated', 'Automated', 'Fully automated test via connector/API', 1, TRUE, '2026-03-15T18:21:16.529778', '2026-03-15T18:21:16.529778'),
      ('e0000002-0000-0000-0000-000000000000', 'manual', 'Manual', 'Requires human review and attestation', 2, TRUE, '2026-03-15T18:21:16.529778', '2026-03-15T18:21:16.529778'),
      ('e0000003-0000-0000-0000-000000000000', 'semi_automated', 'Semi-Automated', 'Automated signal collection + manual interpretation', 3, TRUE, '2026-03-15T18:21:16.529778', '2026-03-15T18:21:16.529778')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 05_grc_library.08_dim_test_result_statuses (5 rows)
DO $$ BEGIN
  INSERT INTO "05_grc_library"."08_dim_test_result_statuses" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('f0000001-0000-0000-0000-000000000000', 'pass', 'Pass', 'Control is operating effectively', 1, TRUE, '2026-03-15T18:21:16.560187', '2026-03-15T18:21:16.560187'),
      ('f0000002-0000-0000-0000-000000000000', 'fail', 'Fail', 'Control failure detected', 2, TRUE, '2026-03-15T18:21:16.560187', '2026-03-15T18:21:16.560187'),
      ('f0000003-0000-0000-0000-000000000000', 'partial', 'Partial', 'Control partially effective', 3, TRUE, '2026-03-15T18:21:16.560187', '2026-03-15T18:21:16.560187'),
      ('f0000004-0000-0000-0000-000000000000', 'unknown', 'Unknown', 'Insufficient evidence to determine result', 4, TRUE, '2026-03-15T18:21:16.560187', '2026-03-15T18:21:16.560187'),
      ('f0000005-0000-0000-0000-000000000000', 'error', 'Error', 'Test execution error', 5, TRUE, '2026-03-15T18:21:16.560187', '2026-03-15T18:21:16.560187')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: AGENT_SANDBOX
-- Extracted: 2026-03-27T14:17:59.211466
-- ═════════════════════════════════════════════════════════════════════════════

-- 25_agent_sandbox.02_dim_agent_statuses (6 rows)
DO $$ BEGIN
  INSERT INTO "25_agent_sandbox"."02_dim_agent_statuses" (id, code, name, description, sort_order, is_terminal, created_at)
  VALUES
      ('63dee137-1ba8-4cdb-aa62-da1288136d38', 'testing', 'Testing', 'Agent is being tested against scenarios', 2, FALSE, '2026-03-22T15:06:59.837043+00:00'),
      ('76655668-c34a-43b6-ba68-f25098a995d3', 'validated', 'Validated', 'Agent has passed all test scenarios', 3, FALSE, '2026-03-22T15:06:59.837043+00:00'),
      ('c0792d57-98bb-4f70-8ad0-b7f45f6a94fa', 'archived', 'Archived', 'Agent is archived and read-only', 6, TRUE, '2026-03-22T15:06:59.837043+00:00'),
      ('eb9560a3-4626-400b-98c8-18539f8171c7', 'published', 'Published', 'Agent is available for production use', 4, FALSE, '2026-03-22T15:06:59.837043+00:00'),
      ('f55eea9e-5f68-43a7-9cc6-db9c685adf2e', 'draft', 'Draft', 'Agent is being developed', 1, FALSE, '2026-03-22T15:06:59.837043+00:00'),
      ('fd09faee-0479-4c7d-9c83-cf3f5dcd9497', 'deprecated', 'Deprecated', 'Agent is no longer recommended', 5, FALSE, '2026-03-22T15:06:59.837043+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_terminal = EXCLUDED.is_terminal;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 25_agent_sandbox.03_dim_tool_types (5 rows)
DO $$ BEGIN
  INSERT INTO "25_agent_sandbox"."03_dim_tool_types" (id, code, name, description, sort_order, is_active, created_at)
  VALUES
      ('1121f29f-98b6-4f64-91c5-b907f914eb0b', 'api_endpoint', 'API Endpoint', 'HTTP API endpoint with JSON schema', 2, TRUE, '2026-03-22T15:06:59.895874+00:00'),
      ('1c7d14b4-7f58-4446-8c79-d76217cc61da', 'db_query', 'Database Query', 'Read-only database query with parameterized input', 5, TRUE, '2026-03-22T15:06:59.895874+00:00'),
      ('6affeeb6-d1fd-429a-ac15-68cf6e94f92e', 'sandbox_signal', 'Sandbox Signal', 'Existing sandbox signal used as a tool', 4, TRUE, '2026-03-22T15:06:59.895874+00:00'),
      ('7dc51dc7-2f0f-4636-9a3f-47cc48be3983', 'python_function', 'Python Function', 'Custom Python function executed in sandbox', 3, TRUE, '2026-03-22T15:06:59.895874+00:00'),
      ('8a91f14e-b271-4df3-b1eb-46042a0ddec8', 'mcp_server', 'MCP Server', 'Model Context Protocol server endpoint', 1, TRUE, '2026-03-22T15:06:59.895874+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 25_agent_sandbox.04_dim_scenario_types (4 rows)
DO $$ BEGIN
  INSERT INTO "25_agent_sandbox"."04_dim_scenario_types" (id, code, name, description, sort_order, created_at)
  VALUES
      ('66ed3199-298c-4c0a-8442-a953b9d30ccd', 'adversarial', 'Adversarial', 'Edge cases and adversarial inputs', 3, '2026-03-22T15:06:59.952806+00:00'),
      ('68ac3dcd-3864-4b3f-8376-e537ff87c81e', 'multi_turn', 'Multi Turn', 'Multi-step conversation test', 2, '2026-03-22T15:06:59.952806+00:00'),
      ('8d82e30c-019c-4a5c-afbb-bd1fcc3c00cf', 'regression', 'Regression', 'Regression tests for known-good behavior', 4, '2026-03-22T15:06:59.952806+00:00'),
      ('b6507dbd-c52a-42c1-a66a-42375450bce8', 'single_turn', 'Single Turn', 'Single input/output test case', 1, '2026-03-22T15:06:59.952806+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 25_agent_sandbox.05_dim_evaluation_methods (5 rows)
DO $$ BEGIN
  INSERT INTO "25_agent_sandbox"."05_dim_evaluation_methods" (id, code, name, description, sort_order, created_at)
  VALUES
      ('1c994a23-0efa-416a-9983-d634a9d9779e', 'similarity', 'Similarity', 'Cosine similarity against reference output', 3, '2026-03-22T15:07:00.010868+00:00'),
      ('23a3f86c-4e36-47d7-aca8-cf5e54edd9c4', 'custom_python', 'Custom Python', 'User-provided evaluation function in sandbox', 5, '2026-03-22T15:07:00.010868+00:00'),
      ('93f6a04d-47f3-41d2-9187-823aa09d5e36', 'regex', 'Regex', 'Regex pattern matching on output', 4, '2026-03-22T15:07:00.010868+00:00'),
      ('dc193319-4442-4526-9bf7-9ba95b451393', 'deterministic', 'Deterministic', 'Exact match or JSON path assertions', 1, '2026-03-22T15:07:00.010868+00:00'),
      ('f2dfe075-6032-439f-a79d-f8fd7ef76fed', 'llm_judge', 'LLM Judge', 'LLM evaluates output against criteria', 2, '2026-03-22T15:07:00.010868+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 25_agent_sandbox.06_dim_execution_statuses (8 rows)
DO $$ BEGIN
  INSERT INTO "25_agent_sandbox"."06_dim_execution_statuses" (id, code, name, description, sort_order, is_terminal, created_at)
  VALUES
      ('57d3878f-afba-45f5-8447-f5eeb8fe5a40', 'queued', 'Queued', 'Run is waiting to be picked up', 1, FALSE, '2026-03-22T15:07:00.065971+00:00'),
      ('5a1ee116-ab84-4692-98c2-f951747db1aa', 'cancelled', 'Cancelled', 'Run was cancelled by user', 8, TRUE, '2026-03-22T15:07:00.065971+00:00'),
      ('80dcf18b-8fc7-4030-88b2-0154c9990d0e', 'running', 'Running', 'Run is actively executing', 2, FALSE, '2026-03-22T15:07:00.065971+00:00'),
      ('93cc8b94-9478-4728-ac1a-387dc490df4d', 'paused', 'Paused', 'Run is paused (checkpoint saved)', 3, FALSE, '2026-03-22T15:07:00.065971+00:00'),
      ('a165ee01-118d-41cf-aaea-72c3bb1c019c', 'awaiting_approval', 'Awaiting Approval', 'Run needs human approval to continue', 4, FALSE, '2026-03-22T15:07:00.065971+00:00'),
      ('b1ad2942-c3e5-42c1-9eb1-df33913d7bbe', 'timeout', 'Timeout', 'Run exceeded time budget', 7, TRUE, '2026-03-22T15:07:00.065971+00:00'),
      ('b7956d06-ddc4-4d12-9d65-0e4b32930939', 'failed', 'Failed', 'Run failed with an error', 6, TRUE, '2026-03-22T15:07:00.065971+00:00'),
      ('e06da486-d19c-4f6f-bd16-a584cc6aabb9', 'completed', 'Completed', 'Run finished successfully', 5, TRUE, '2026-03-22T15:07:00.065971+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_terminal = EXCLUDED.is_terminal;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: TASKS
-- Extracted: 2026-03-27T14:18:03.615382
-- ═════════════════════════════════════════════════════════════════════════════

-- 08_tasks.02_dim_task_types (4 rows)
DO $$ BEGIN
  INSERT INTO "08_tasks"."02_dim_task_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('b1c10001-0000-0000-0000-000000000000', 'evidence_collection', 'Evidence Collection', 'Collect evidence for a control test', 1, TRUE, '2026-03-15T18:17:05.953736', '2026-03-15T18:17:05.953736'),
      ('b1c10002-0000-0000-0000-000000000000', 'control_remediation', 'Control Remediation', 'Fix a failing or non-compliant control', 2, TRUE, '2026-03-15T18:17:05.953736', '2026-03-15T18:17:05.953736'),
      ('b1c10003-0000-0000-0000-000000000000', 'risk_mitigation', 'Risk Mitigation', 'Execute a risk treatment action', 3, TRUE, '2026-03-15T18:17:05.953736', '2026-03-15T18:17:05.953736'),
      ('b1c10004-0000-0000-0000-000000000000', 'general', 'General', 'General compliance or operational task', 4, TRUE, '2026-03-15T18:17:05.953736', '2026-03-15T18:17:05.953736')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 08_tasks.03_dim_task_priorities (4 rows)
DO $$ BEGIN
  INSERT INTO "08_tasks"."03_dim_task_priorities" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('b2c20001-0000-0000-0000-000000000000', 'critical', 'Critical', 'Must be completed immediately', 1, TRUE, '2026-03-15T18:17:05.977974', '2026-03-15T18:17:05.977974'),
      ('b2c20002-0000-0000-0000-000000000000', 'high', 'High', 'Complete within 3 business days', 2, TRUE, '2026-03-15T18:17:05.977974', '2026-03-15T18:17:05.977974'),
      ('b2c20003-0000-0000-0000-000000000000', 'medium', 'Medium', 'Complete within 2 weeks', 3, TRUE, '2026-03-15T18:17:05.977974', '2026-03-15T18:17:05.977974'),
      ('b2c20004-0000-0000-0000-000000000000', 'low', 'Low', 'Complete at next opportunity', 4, TRUE, '2026-03-15T18:17:05.977974', '2026-03-15T18:17:05.977974')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 08_tasks.04_dim_task_statuses (6 rows)
DO $$ BEGIN
  INSERT INTO "08_tasks"."04_dim_task_statuses" (id, code, name, description, is_terminal, sort_order, is_active, created_at, updated_at)
  VALUES
      ('b3c30001-0000-0000-0000-000000000000', 'open', 'Open', 'Task created, not yet started', FALSE, 1, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30002-0000-0000-0000-000000000000', 'in_progress', 'In Progress', 'Actively being worked on', FALSE, 2, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30003-0000-0000-0000-000000000000', 'pending_verification', 'Pending Verification', 'Work done, awaiting review/verification', FALSE, 3, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30004-0000-0000-0000-000000000000', 'resolved', 'Resolved', 'Task completed and verified', TRUE, 4, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30005-0000-0000-0000-000000000000', 'cancelled', 'Cancelled', 'Task cancelled — no longer needed', TRUE, 5, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30006-0000-0000-0000-000000000000', 'overdue', 'Overdue', 'Past due date — system-managed', FALSE, 6, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_terminal = EXCLUDED.is_terminal, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: ISSUES
-- Extracted: 2026-03-27T14:18:06.282371
-- ═════════════════════════════════════════════════════════════════════════════

-- 09_issues.02_dim_issue_statuses (6 rows)
DO $$ BEGIN
  INSERT INTO "09_issues"."02_dim_issue_statuses" (code, name, sort_order, is_active)
  VALUES
      ('accepted', 'Risk Accepted', 6, TRUE),
      ('closed', 'Closed', 5, TRUE),
      ('investigating', 'Investigating', 2, TRUE),
      ('open', 'Open', 1, TRUE),
      ('remediated', 'Remediated', 3, TRUE),
      ('verified', 'Verified', 4, TRUE)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 09_issues.03_dim_issue_severities (5 rows)
DO $$ BEGIN
  INSERT INTO "09_issues"."03_dim_issue_severities" (code, name, sort_order)
  VALUES
      ('critical', 'Critical', 1),
      ('high', 'High', 2),
      ('info', 'Informational', 5),
      ('low', 'Low', 4),
      ('medium', 'Medium', 3)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: FEEDBACK
-- Extracted: 2026-03-27T14:18:07.970146
-- ═════════════════════════════════════════════════════════════════════════════

-- 10_feedback.01_dim_ticket_types (5 rows)
DO $$ BEGIN
  INSERT INTO "10_feedback"."01_dim_ticket_types" (code, name, description, icon_name, sort_order, is_active)
  VALUES
      ('bug_report', 'Bug Report', 'Something is broken or not working as expected', 'Bug', 10, TRUE),
      ('feature_request', 'Feature Request', 'Suggest a new feature or improvement', 'Lightbulb', 20, TRUE),
      ('general_feedback', 'General Feedback', 'General comments, praise, or suggestions', 'MessageSquare', 30, TRUE),
      ('security_concern', 'Security Concern', 'Potential vulnerability or security-related observation', 'ShieldAlert', 50, TRUE),
      ('service_issue', 'Service Issue', 'Degraded performance, outage, or reliability concern', 'AlertTriangle', 40, TRUE)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, icon_name = EXCLUDED.icon_name, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 10_feedback.02_dim_ticket_statuses (7 rows)
DO $$ BEGIN
  INSERT INTO "10_feedback"."02_dim_ticket_statuses" (code, name, description, is_terminal, sort_order)
  VALUES
      ('closed', 'Closed', 'Closed without further action', TRUE, 50),
      ('duplicate', 'Duplicate', 'Same issue already tracked elsewhere', TRUE, 70),
      ('in_progress', 'In Progress', 'Actively being worked on', FALSE, 30),
      ('in_review', 'In Review', 'Being triaged by support team', FALSE, 20),
      ('open', 'Open', 'Newly submitted, awaiting triage', FALSE, 10),
      ('resolved', 'Resolved', 'Issue fixed or request fulfilled', TRUE, 40),
      ('wont_fix', 'Won''t Fix', 'Acknowledged but will not be addressed', TRUE, 60)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_terminal = EXCLUDED.is_terminal, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 10_feedback.03_dim_ticket_priorities (4 rows)
DO $$ BEGIN
  INSERT INTO "10_feedback"."03_dim_ticket_priorities" (code, name, description, numeric_level, sort_order)
  VALUES
      ('critical', 'Critical', 'Platform unusable or security emergency', 3, 40),
      ('high', 'High', 'Significant impact, no easy workaround', 2, 30),
      ('low', 'Low', 'Minor inconvenience, no business impact', 0, 10),
      ('medium', 'Medium', 'Moderate impact, workaround exists', 1, 20)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, numeric_level = EXCLUDED.numeric_level, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: DOCS
-- Extracted: 2026-03-27T14:18:10.729242
-- ═════════════════════════════════════════════════════════════════════════════

-- 11_docs.01_dim_doc_categories (9 rows)
DO $$ BEGIN
  INSERT INTO "11_docs"."01_dim_doc_categories" (code, name, description, sort_order, is_active)
  VALUES
      ('compliance', 'Compliance', 'Compliance evidence, certificates, and attestations', 60, TRUE),
      ('framework_guide', 'Framework Guide', 'Compliance framework reference guides (ISO, SOC 2, etc.)', 30, TRUE),
      ('other', 'Other', 'Miscellaneous documents', 90, TRUE),
      ('policy', 'Policy', 'Organisational policies and governance documents', 10, TRUE),
      ('procedure', 'Procedure', 'Standard operating procedures and runbooks', 20, TRUE),
      ('reference', 'Reference', 'Technical reference and architecture documentation', 50, TRUE),
      ('sandbox', 'Sandbox', 'K-Control Sandbox reference docs and signal libraries', 70, TRUE),
      ('template', 'Template', 'Document templates for evidence, reports, assessments', 40, TRUE),
      ('training', 'Training', 'Training materials and onboarding guides', 80, TRUE)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: ENGAGEMENTS
-- Extracted: 2026-03-27T14:18:11.834056
-- ═════════════════════════════════════════════════════════════════════════════

-- 12_engagements.02_dim_engagement_statuses (5 rows)
DO $$ BEGIN
  INSERT INTO "12_engagements"."02_dim_engagement_statuses" (code, name, description, sort_order, created_at)
  VALUES
      ('active', 'Active', 'Execution and evidence review', 20, '2026-03-26T20:31:11.230754+00:00'),
      ('closed', 'Closed', 'Archived and read-only', 50, '2026-03-26T20:31:11.230754+00:00'),
      ('completed', 'Completed', 'Final report issued', 40, '2026-03-26T20:31:11.230754+00:00'),
      ('review', 'Review', 'Drafting report and remediation', 30, '2026-03-26T20:31:11.230754+00:00'),
      ('setup', 'Setup', 'Initial configuration phase', 10, '2026-03-26T20:31:11.230754+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 12_engagements.03_dim_engagement_property_keys (7 rows)
DO $$ BEGIN
  INSERT INTO "12_engagements"."03_dim_engagement_property_keys" (id, code, name, description, data_type, is_required, sort_order, created_at)
  VALUES
      ('020821f9-1ee3-4fcb-bb21-b1a7c93942d4', 'audit_period_start', 'Audit Period Start', NULL, 'date', FALSE, 40, '2026-03-26T20:31:11.230754+00:00'),
      ('06122236-eee2-4a53-8512-4cad91096bc8', 'report_type', 'Report Type', NULL, 'text', FALSE, 60, '2026-03-26T20:31:11.230754+00:00'),
      ('2df71727-35e2-4cbd-9f86-3b936abc0033', 'audit_period_end', 'Audit Period End', NULL, 'date', FALSE, 50, '2026-03-26T20:31:11.230754+00:00'),
      ('4c406912-c578-4849-aeb9-968f4da723ca', 'auditor_firm', 'Auditor Firm', NULL, 'text', TRUE, 20, '2026-03-26T20:31:11.230754+00:00'),
      ('d2f98158-0d10-4046-a9f1-49339d737323', 'scope_description', 'Scope Description', NULL, 'text', FALSE, 30, '2026-03-26T20:31:11.230754+00:00'),
      ('e6b5f851-8b23-4980-9163-cf993f293aff', 'engagement_name', 'Engagement Name', NULL, 'text', TRUE, 10, '2026-03-26T20:31:11.230754+00:00'),
      ('e7b131b2-4826-4611-8e18-db67cd130eb1', 'lead_grc_sme', 'Lead GRC SME', NULL, 'text', FALSE, 70, '2026-03-26T20:31:11.230754+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 12_engagements.04_dim_request_property_keys (2 rows)
DO $$ BEGIN
  INSERT INTO "12_engagements"."04_dim_request_property_keys" (id, code, name, data_type, is_required, created_at)
  VALUES
      ('4fa25e60-efbe-4f66-aeef-d30ecfe64df7', 'response_notes', 'Notes', 'text', FALSE, '2026-03-26T20:31:11.230754+00:00'),
      ('c7889c35-b34a-41ea-ad87-9c364318486d', 'request_description', 'Description', 'text', TRUE, '2026-03-26T20:31:11.230754+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, data_type = EXCLUDED.data_type, is_required = EXCLUDED.is_required;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: RISK_REGISTRY
-- Extracted: 2026-03-27T14:18:14.517128
-- ═════════════════════════════════════════════════════════════════════════════

-- 14_risk_registry.02_dim_risk_categories (8 rows)
DO $$ BEGIN
  INSERT INTO "14_risk_registry"."02_dim_risk_categories" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('a1b00001-0000-0000-0000-000000000000', 'operational', 'Operational', 'Risks from internal processes, people, systems', 1, TRUE, '2026-03-15T18:21:17.708264', '2026-03-15T18:21:17.708264'),
      ('a1b00002-0000-0000-0000-000000000000', 'strategic', 'Strategic', 'Risks affecting strategic objectives', 2, TRUE, '2026-03-15T18:21:17.708264', '2026-03-15T18:21:17.708264'),
      ('a1b00003-0000-0000-0000-000000000000', 'compliance', 'Compliance', 'Regulatory and legal compliance risks', 3, TRUE, '2026-03-15T18:21:17.708264', '2026-03-15T18:21:17.708264'),
      ('a1b00004-0000-0000-0000-000000000000', 'financial', 'Financial', 'Financial loss or fraud risks', 4, TRUE, '2026-03-15T18:21:17.708264', '2026-03-15T18:21:17.708264'),
      ('a1b00005-0000-0000-0000-000000000000', 'reputational', 'Reputational', 'Brand and reputation damage risks', 5, TRUE, '2026-03-15T18:21:17.708264', '2026-03-15T18:21:17.708264'),
      ('a1b00006-0000-0000-0000-000000000000', 'technology', 'Technology', 'IT infrastructure and cybersecurity risks', 6, TRUE, '2026-03-15T18:21:17.708264', '2026-03-15T18:21:17.708264'),
      ('a1b00007-0000-0000-0000-000000000000', 'legal', 'Legal', 'Legal liability and contract risks', 7, TRUE, '2026-03-15T18:21:17.708264', '2026-03-15T18:21:17.708264'),
      ('a1b00008-0000-0000-0000-000000000000', 'vendor', 'Vendor', 'Third-party and supply chain risks', 8, TRUE, '2026-03-15T18:21:17.708264', '2026-03-15T18:21:17.708264')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 14_risk_registry.03_dim_risk_treatment_types (4 rows)
DO $$ BEGIN
  INSERT INTO "14_risk_registry"."03_dim_risk_treatment_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      ('a2b00001-0000-0000-0000-000000000000', 'mitigate', 'Mitigate', 'Implement controls to reduce likelihood or impact', 1, TRUE, '2026-03-15T18:21:17.73916', '2026-03-15T18:21:17.73916'),
      ('a2b00002-0000-0000-0000-000000000000', 'accept', 'Accept', 'Accept the risk within tolerance levels', 2, TRUE, '2026-03-15T18:21:17.73916', '2026-03-15T18:21:17.73916'),
      ('a2b00003-0000-0000-0000-000000000000', 'transfer', 'Transfer', 'Transfer risk via insurance or contracts', 3, TRUE, '2026-03-15T18:21:17.73916', '2026-03-15T18:21:17.73916'),
      ('a2b00004-0000-0000-0000-000000000000', 'avoid', 'Avoid', 'Eliminate the activity that creates the risk', 4, TRUE, '2026-03-15T18:21:17.73916', '2026-03-15T18:21:17.73916')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 14_risk_registry.04_dim_risk_levels (4 rows)
DO $$ BEGIN
  INSERT INTO "14_risk_registry"."04_dim_risk_levels" (id, code, name, description, score_min, score_max, color_hex, sort_order, is_active, created_at, updated_at)
  VALUES
      ('a3b00001-0000-0000-0000-000000000000', 'critical', 'Critical', 'Score 16-25: immediate action required', 16, 25, '#ef4444', 1, TRUE, '2026-03-15T18:21:17.772237', '2026-03-15T18:21:17.772237'),
      ('a3b00002-0000-0000-0000-000000000000', 'high', 'High', 'Score 11-15: urgent action within 30 days', 11, 15, '#f97316', 2, TRUE, '2026-03-15T18:21:17.772237', '2026-03-15T18:21:17.772237'),
      ('a3b00003-0000-0000-0000-000000000000', 'medium', 'Medium', 'Score 6-10: action within 90 days', 6, 10, '#f59e0b', 3, TRUE, '2026-03-15T18:21:17.772237', '2026-03-15T18:21:17.772237'),
      ('a3b00004-0000-0000-0000-000000000000', 'low', 'Low', 'Score 1-5: monitor and review quarterly', 1, 5, '#10b981', 4, TRUE, '2026-03-15T18:21:17.772237', '2026-03-15T18:21:17.772237')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, score_min = EXCLUDED.score_min, score_max = EXCLUDED.score_max, color_hex = EXCLUDED.color_hex, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: ASSESSMENTS
-- Extracted: 2026-03-27T14:18:17.190588
-- ═════════════════════════════════════════════════════════════════════════════

-- 09_assessments.02_dim_assessment_types (5 rows)
DO $$ BEGIN
  INSERT INTO "09_assessments"."02_dim_assessment_types" (id, code, name, description, icon, sort_order, is_active, created_at, updated_at)
  VALUES
      ('43f98ac0-e546-428a-811c-f1b9a0e128ce', 'internal_audit', 'Internal Audit', 'Routine internal compliance review', NULL, 1, TRUE, '2026-03-18T03:10:26.630416+00:00', '2026-03-18T03:10:26.630416+00:00'),
      ('568e57e1-df2d-400a-9be4-658c6e947a54', 'external_prep', 'External Audit Prep', 'Preparation session before an external audit', NULL, 2, TRUE, '2026-03-18T03:10:26.630416+00:00', '2026-03-18T03:10:26.630416+00:00'),
      ('7d46252c-9954-4f38-bccb-91724d1270a1', 'readiness_review', 'Readiness Review', 'Pre-audit readiness check', NULL, 5, TRUE, '2026-03-18T03:10:26.630416+00:00', '2026-03-18T03:10:26.630416+00:00'),
      ('7d6b47b0-bb68-4f4e-90ba-3b54dcf7e7e6', 'gap_analysis', 'Gap Analysis', 'Identify compliance gaps across controls and frameworks', NULL, 4, TRUE, '2026-03-18T03:10:26.630416+00:00', '2026-03-18T03:10:26.630416+00:00'),
      ('b709a886-e178-416f-a06c-b0e4e56e3e10', 'certification_audit', 'Certification Audit', 'Formal assessment for a compliance certification', NULL, 3, TRUE, '2026-03-18T03:10:26.630416+00:00', '2026-03-18T03:10:26.630416+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, icon = EXCLUDED.icon, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 09_assessments.03_dim_assessment_statuses (5 rows)
DO $$ BEGIN
  INSERT INTO "09_assessments"."03_dim_assessment_statuses" (id, code, name, description, icon, sort_order, is_active, created_at, updated_at)
  VALUES
      ('55d95e4c-1d23-4adf-8d98-146e1845ee70', 'planned', 'Planned', 'Assessment is scheduled but not yet started', NULL, 1, TRUE, '2026-03-18T03:10:26.720029+00:00', '2026-03-18T03:10:26.720029+00:00'),
      ('6e4f429a-6708-4aac-9e09-fc07ab263982', 'cancelled', 'Cancelled', 'Assessment was abandoned', NULL, 5, TRUE, '2026-03-18T03:10:26.720029+00:00', '2026-03-18T03:10:26.720029+00:00'),
      ('8e34d3d5-ac88-46e5-94ff-8dbb984c8029', 'review', 'In Review', 'Findings are being reviewed before finalizing', NULL, 3, TRUE, '2026-03-18T03:10:26.720029+00:00', '2026-03-18T03:10:26.720029+00:00'),
      ('8ed1870d-61f3-4e3e-bbb4-dce2fce099d4', 'completed', 'Completed', 'Assessment is done and findings are locked', NULL, 4, TRUE, '2026-03-18T03:10:26.720029+00:00', '2026-03-18T03:10:26.720029+00:00'),
      ('ac3b151c-cf41-4e96-b985-af058bb000c9', 'in_progress', 'In Progress', 'Assessment is actively being conducted', NULL, 2, TRUE, '2026-03-18T03:10:26.720029+00:00', '2026-03-18T03:10:26.720029+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, icon = EXCLUDED.icon, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 09_assessments.04_dim_finding_severities (5 rows)
DO $$ BEGIN
  INSERT INTO "09_assessments"."04_dim_finding_severities" (id, code, name, description, icon, sort_order, is_active, created_at, updated_at)
  VALUES
      ('19b0a472-d0e3-4b91-9f58-d7a491284659', 'low', 'Low', 'Minor issue, address at convenience', NULL, 4, TRUE, '2026-03-18T03:10:26.808452+00:00', '2026-03-18T03:10:26.808452+00:00'),
      ('68db33b9-fbe6-4c70-943b-3ee12affbb88', 'medium', 'Medium', 'Should be resolved in the next cycle', NULL, 3, TRUE, '2026-03-18T03:10:26.808452+00:00', '2026-03-18T03:10:26.808452+00:00'),
      ('6e2b9d9f-d20b-4c43-8f3e-15717b9dc8d7', 'informational', 'Informational', 'No action required, noted for awareness', NULL, 5, TRUE, '2026-03-18T03:10:26.808452+00:00', '2026-03-18T03:10:26.808452+00:00'),
      ('ec29e95f-2f97-4eaf-bf82-d1ee22864543', 'high', 'High', 'Must be addressed promptly', NULL, 2, TRUE, '2026-03-18T03:10:26.808452+00:00', '2026-03-18T03:10:26.808452+00:00'),
      ('fe5ce2ac-d425-4738-bc8f-e9e66017d779', 'critical', 'Critical', 'Requires immediate remediation', NULL, 1, TRUE, '2026-03-18T03:10:26.808452+00:00', '2026-03-18T03:10:26.808452+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, icon = EXCLUDED.icon, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 09_assessments.05_dim_finding_statuses (5 rows)
DO $$ BEGIN
  INSERT INTO "09_assessments"."05_dim_finding_statuses" (id, code, name, description, icon, sort_order, is_active, created_at, updated_at)
  VALUES
      ('0f03913c-870b-40a8-8ad5-f51bcc31627d', 'verified_closed', 'Verified Closed', 'Remediation verified and finding resolved', NULL, 3, TRUE, '2026-03-18T03:10:26.893085+00:00', '2026-03-18T03:10:26.893085+00:00'),
      ('4fc68793-081d-4866-b476-7f6c8e07ab39', 'accepted', 'Accepted', 'Acknowledged as a known/accepted risk', NULL, 4, TRUE, '2026-03-18T03:10:26.893085+00:00', '2026-03-18T03:10:26.893085+00:00'),
      ('dccca926-42f8-420c-8c52-2dcd44e0875e', 'open', 'Open', 'Finding has been recorded, not yet addressed', NULL, 1, TRUE, '2026-03-18T03:10:26.893085+00:00', '2026-03-18T03:10:26.893085+00:00'),
      ('ee1f04b4-3e6d-4614-96b5-d37fadc5aaf6', 'in_remediation', 'In Remediation', 'Assignee is actively working on a fix', NULL, 2, TRUE, '2026-03-18T03:10:26.893085+00:00', '2026-03-18T03:10:26.893085+00:00'),
      ('f41200b3-a44e-4444-a5e6-ee81aa346894', 'disputed', 'Disputed', 'Finding is being challenged by the assignee', NULL, 5, TRUE, '2026-03-18T03:10:26.893085+00:00', '2026-03-18T03:10:26.893085+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, icon = EXCLUDED.icon, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 09_assessments.06_dim_assessment_property_keys (3 rows)
DO $$ BEGIN
  INSERT INTO "09_assessments"."06_dim_assessment_property_keys" (id, code, name, description, data_type, is_required, sort_order, created_at, updated_at)
  VALUES
      ('43f32ae6-fa41-4065-a63f-4f91cb8d410f', 'name', 'Name', 'Assessment session name', 'text', TRUE, 1, '2026-03-18T03:10:26.978461+00:00', '2026-03-18T03:10:26.978461+00:00'),
      ('6f7360e8-c92e-4ea0-af6f-4564e4e0fa3c', 'description', 'Description', 'What this assessment covers', 'text', FALSE, 2, '2026-03-18T03:10:26.978461+00:00', '2026-03-18T03:10:26.978461+00:00'),
      ('b7a40578-3195-4c8c-b908-df6b87b299dd', 'scope_notes', 'Scope Notes', 'Scope boundaries and exclusions', 'text', FALSE, 3, '2026-03-18T03:10:26.978461+00:00', '2026-03-18T03:10:26.978461+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 09_assessments.07_dim_finding_property_keys (3 rows)
DO $$ BEGIN
  INSERT INTO "09_assessments"."07_dim_finding_property_keys" (id, code, name, description, data_type, is_required, sort_order, created_at, updated_at)
  VALUES
      ('06a0ff33-606d-4474-baae-559fe8a72945', 'description', 'Description', 'Detailed finding notes', 'text', FALSE, 2, '2026-03-18T03:10:27.065867+00:00', '2026-03-18T03:10:27.065867+00:00'),
      ('0bf938d1-5007-4472-99a8-095303255d4e', 'title', 'Title', 'Finding title', 'text', TRUE, 1, '2026-03-18T03:10:27.065867+00:00', '2026-03-18T03:10:27.065867+00:00'),
      ('ce56ae7d-50a0-4925-9201-f5b9bab9b3e3', 'recommendation', 'Recommendation', 'Suggested remediation', 'text', FALSE, 3, '2026-03-18T03:10:27.065867+00:00', '2026-03-18T03:10:27.065867+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, data_type = EXCLUDED.data_type, is_required = EXCLUDED.is_required, sort_order = EXCLUDED.sort_order, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: STEAMPIPE
-- Extracted: 2026-03-27T14:18:22.419997
-- ═════════════════════════════════════════════════════════════════════════════

-- 17_steampipe.02_dim_plugin_types (2 rows)
DO $$ BEGIN
  INSERT INTO "17_steampipe"."02_dim_plugin_types" (code, name, plugin_image, provider_code, version, is_active, created_at)
  VALUES
      ('turbot/azure', 'Steampipe Azure Plugin', 'ghcr.io/turbot/steampipe-plugin-azure', 'azure_storage', 'latest', TRUE, '2026-03-16T11:39:09.783777+00:00'),
      ('turbot/github', 'Steampipe GitHub Plugin', 'ghcr.io/turbot/steampipe-plugin-github', 'github', 'latest', TRUE, '2026-03-16T11:39:09.783777+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, plugin_image = EXCLUDED.plugin_image, provider_code = EXCLUDED.provider_code, version = EXCLUDED.version, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF SEED DATA
-- ═══════════════════════════════════════════════════════════════════════════
