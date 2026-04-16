-- ═══════════════════════════════════════════════════════════════════════════
-- KCONTROL SYSTEM SEED DATA
-- Generated: 2026-04-02T12:26:08.628890
-- Source DB: kcontrol_dev @ ks-prod-cin-psql-02.postgres.database.azure.com
-- Categories: auth, notifications, ai, sandbox, grc, agent_sandbox, tasks, issues, feedback, docs, engagements, risk_registry, assessments, steampipe
-- 
-- Idempotent: all INSERTs use ON CONFLICT DO UPDATE SET (upsert).
-- Safe to re-run in any environment.
-- ═══════════════════════════════════════════════════════════════════════════

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: AUTH
-- Extracted: 2026-04-02T12:26:08.628909
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

-- 03_auth_manage.12_dim_feature_permission_actions (21 rows)
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
      ('00000000-0000-0000-0000-000000005031', 'review', 'Review', 'Review a submitted item.', 45, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000005032', 'publish', 'Publish', 'Publish item to an external party.', 55, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000005033', 'complete', 'Complete', 'Mark item as fully complete.', 60, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000005034', 'respond', 'Respond', 'Respond to or dispute an item.', 65, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000005035', 'close', 'Close', 'Close, accept, or escalate an item.', 70, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000006001', 'collect', 'Collect', 'Trigger or cancel asset collection runs.', 85, '2026-03-16T11:39:10.95114', '2026-03-16T11:39:10.95114'),
      ('00000000-0000-0000-0000-000000007001', 'manage', 'Manage', 'Full management access including approvals and registry.', 100, '2026-03-22T15:08:27.826789', '2026-03-22T15:08:27.826789'),
      ('00000000-0000-0000-0000-000000008001', 'edit', 'Edit', 'Edit/modify resources', 35, '2026-04-01T02:55:56.676172', '2026-04-01T02:55:56.676172'),
      ('00000000-0000-0000-0000-000000008002', 'admin', 'Admin', 'Full administrative control', 110, '2026-04-01T02:55:56.709662', '2026-04-01T02:55:56.709662'),
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
      ('00000000-0000-0000-0000-000000000402', 'auth_google_login', 'Google Login', 'Availability of Google login when implemented.', 'auth', 'public', 'active', 'all_users', TRUE, FALSE, FALSE, '2026-03-13T00:00:00', '2026-04-01T05:02:23.989821', 'platform', NULL),
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
      ('00000000-0000-0000-0000-000000009000', 'grc_role_management', 'GRC Role Management', 'Manage org-level GRC role assignments (lead, SME, auditor, vendor) and access grants.', 'grc', 'permissioned', 'active', 'org_admin', TRUE, TRUE, TRUE, '2026-04-01T00:00:00', '2026-04-01T00:00:00', 'platform', NULL),
      ('24de0b90-1704-4af2-91b1-9ec3fbbb4b7c', 'robot_flag_1775025823', 'Robot Flag 1775025823 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-04-01T06:43:49.077001', '2026-04-01T06:43:52.182994', 'platform', NULL),
      ('29b3f390-9cf2-4237-9ec7-bae56bb08ac1', 'findings', 'Findings', 'Finding management within assessments', 'grc', 'permissioned', 'active', 'platform_super_admin', TRUE, TRUE, FALSE, '2026-03-18T03:12:15.766767', '2026-03-18T03:12:15.766767', 'platform', NULL),
      ('2d4478ff-762c-42ce-99ce-a1f6f29e1ee5', 'ai_evidence_checker', 'AI Evidence Checker', 'Auto-evaluate task attachments against acceptance criteria using AI multi-agent evaluation', 'grc', 'permissioned', 'general_availability', 'all_users', TRUE, TRUE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', 'workspace', NULL),
      ('30ddfe78-8e2b-4772-94e1-22de0eaa182d', 'notification_broadcasts', 'Notification Broadcasts', 'Notification Broadcasts feature flag', 'admin', 'permissioned', 'active', '100', TRUE, FALSE, FALSE, '2026-03-14T08:44:04.851727', '2026-03-16T10:41:51.538604', 'platform', NULL),
      ('3182a298-ad59-4a0f-a4a3-daab65ce0618', 'robot_flag_1775021270', 'Robot Flag 1775021270 Updated', 'Updated by Robot Framework', 'auth', 'permissioned', 'planned', 'platform_super_admin', FALSE, FALSE, FALSE, '2026-04-01T05:27:53.487258', '2026-04-01T05:27:55.238488', 'platform', NULL),
      ('37a1f448-c15b-4457-879b-8204aa288f08', 'api_key_management', 'API Key Management', 'API key management for programmatic access', 'auth', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-31T06:27:41.364213', '2026-04-01T05:02:54.531058', 'platform', NULL),
      ('39b95e7d-13ff-4eba-a155-faff7118f7bc', 'reports', 'GRC Reports', 'AI-generated compliance and audit reports', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-18T14:23:34.216589', '2026-03-18T14:23:34.216589', 'platform', NULL),
      ('4dec73fd-6f83-49aa-bdd3-558759474f61', 'api_keys', 'API Keys', 'API key management for programmatic access', 'auth', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-30T21:04:26.814192', '2026-03-31T17:06:55.751075', 'platform', NULL),
      ('58148945-4ed2-47a6-875b-d9607bc72325', 'notification_system', 'Notification System', 'Notification System feature flag', 'admin', 'permissioned', 'active', '100', TRUE, FALSE, FALSE, '2026-03-14T08:44:04.68572', '2026-03-16T10:41:29.435077', 'platform', NULL),
      ('644b34f9-3b54-4517-bb0b-612e3a3e6fca', 'assessments', 'Assessments', 'Assessment & Findings module', 'grc', 'permissioned', 'active', 'platform_super_admin', TRUE, TRUE, FALSE, '2026-03-18T03:12:15.766767', '2026-03-18T03:12:15.766767', 'platform', NULL),
      ('654993d9-4cbe-464a-bd00-77b7dcfc337d', 'global_risk_library', 'Global Risk Library', 'Platform-level global risk registry', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, '2026-03-17T09:56:03.279507', '2026-03-17T09:56:03.279507', 'platform', NULL),
      ('99efdb95-b7a6-4a0a-821f-912ee337ca96', 'notification_preferences', 'Notification Preferences', 'Notification Preferences feature flag', 'admin', 'authenticated', 'active', '100', TRUE, FALSE, FALSE, '2026-03-14T08:44:04.921379', '2026-03-16T10:41:44.390144', 'platform', NULL),
      ('b12d6d5d-7032-455b-9059-ab41ca688ecf', 'notification_templates', 'Notification Templates', 'Notification Templates feature flag', 'admin', 'permissioned', 'active', '100', TRUE, FALSE, FALSE, '2026-03-14T08:44:04.78462', '2026-03-16T10:41:09.801996', 'platform', NULL),
      ('d63d053d-5060-4186-b097-8d1e374e559e', 'ai_copilot', 'AI Copilot Platform', 'Enterprise AI copilot, MCP tools, approval workflows, agent swarm', 'admin', 'permissioned', 'active', 'platform_super_admin', TRUE, TRUE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', 'platform', NULL),
      ('de32a051-928d-485b-84e0-fc737eda4106', 'audit_logs_access', 'Org Audit logs', 'Organization level audit logs visibility', 'audit_logs', 'permissioned', 'active', 'platform_super_admin', TRUE, FALSE, FALSE, '2026-03-16T06:08:56.715018', '2026-03-16T10:13:58.896856', 'org', NULL),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9001', 'audit_workspace_auditor_portfolio', 'Audit Workspace Auditor Portfolio', 'Multi-org auditor portfolio view for assigned engagements.', 'access', 'permissioned', 'draft', 'internal', TRUE, FALSE, FALSE, '2026-04-02T06:50:48.046968', '2026-04-02T06:50:48.046968', 'platform', NULL),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9002', 'audit_workspace_engagement_membership', 'Audit Workspace Engagement Membership', 'Engagement membership foundation for auditor workspace visibility and access resolution.', 'access', 'permissioned', 'draft', 'internal', TRUE, FALSE, FALSE, '2026-04-02T06:50:48.046968', '2026-04-02T06:50:48.046968', 'platform', NULL),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9003', 'audit_workspace_control_access', 'Audit Workspace Control Access', 'Allows assigned auditors to view engagement-scoped control metadata.', 'access', 'permissioned', 'draft', 'internal', TRUE, FALSE, FALSE, '2026-04-02T06:54:47.932116', '2026-04-02T06:54:47.932116', 'platform', NULL),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9004', 'audit_workspace_evidence_requests', 'Audit Workspace Evidence Requests', 'Allows auditors to request evidence and internal teams to review those requests.', 'access', 'permissioned', 'draft', 'internal', TRUE, FALSE, FALSE, '2026-04-02T06:54:47.932116', '2026-04-02T06:54:47.932116', 'platform', NULL),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9005', 'audit_workspace_auditor_tasks', 'Audit Workspace Auditor Tasks', 'Allows engagement-scoped auditor task creation and task access.', 'access', 'permissioned', 'draft', 'internal', TRUE, FALSE, FALSE, '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089', 'platform', NULL),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9006', 'audit_workspace_auditor_findings', 'Audit Workspace Auditor Findings', 'Allows engagement-scoped auditor finding workflows when engagement linkage is ready.', 'access', 'permissioned', 'draft', 'internal', TRUE, FALSE, FALSE, '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089', 'platform', NULL)
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, feature_flag_category_code = EXCLUDED.feature_flag_category_code, access_mode = EXCLUDED.access_mode, lifecycle_state = EXCLUDED.lifecycle_state, initial_audience = EXCLUDED.initial_audience, env_dev = EXCLUDED.env_dev, env_staging = EXCLUDED.env_staging, env_prod = EXCLUDED.env_prod, updated_at = EXCLUDED.updated_at, feature_scope = EXCLUDED.feature_scope, product_id = EXCLUDED.product_id;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.15_dim_feature_permissions (191 rows)
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
      ('00000000-0000-0000-0000-000000008001', 'tasks.submit', 'task_management', 'submit', 'Submit Task Evidence', 'Submit task evidence for internal review.', '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000008002', 'tasks.review', 'task_management', 'review', 'Review Task Evidence', 'Review submitted task evidence as control owner.', '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000008003', 'tasks.approve', 'task_management', 'approve', 'Approve Task Evidence', 'Approve reviewed evidence (GRC Lead only).', '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000008004', 'tasks.publish', 'task_management', 'publish', 'Publish Task Evidence', 'Publish approved evidence to the audit engagement.', '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000008005', 'tasks.complete', 'task_management', 'complete', 'Complete Task', 'Mark evidence task as fully complete.', '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000008006', 'findings.respond', 'findings', 'respond', 'Respond to Finding', 'Submit remediation response or dispute a finding.', '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000008007', 'findings.close', 'findings', 'close', 'Close Finding', 'Close, accept, or escalate a finding.', '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384'),
      ('00000000-0000-0000-0000-000000008901', 'controls.edit', 'control_management', 'edit', 'Edit Controls', 'Edit control details and engagement operations', '2026-04-01T02:55:56.743199', '2026-04-01T02:55:56.743199'),
      ('00000000-0000-0000-0000-000000008902', 'controls.admin', 'control_management', 'admin', 'Admin Controls', 'Full administrative control over controls', '2026-04-01T02:55:56.77979', '2026-04-01T02:55:56.77979'),
      ('00000000-0000-0000-0000-000000009001', 'grc_role_management.view', 'grc_role_management', 'view', 'View GRC Team', 'View GRC role assignments and access grants for the org.', '2026-04-01T00:00:00', '2026-04-01T00:00:00'),
      ('00000000-0000-0000-0000-000000009002', 'grc_role_management.assign', 'grc_role_management', 'assign', 'Assign GRC Role', 'Assign a GRC role to a user at the org level.', '2026-04-01T00:00:00', '2026-04-01T00:00:00'),
      ('00000000-0000-0000-0000-000000009003', 'grc_role_management.revoke', 'grc_role_management', 'revoke', 'Revoke GRC Role', 'Revoke a GRC role assignment.', '2026-04-01T00:00:00', '2026-04-01T00:00:00'),
      ('01dfab3e-59e2-4e79-b514-d57b4de19c65', 'notification_system.view', 'notification_system', 'view', 'notification_system view', 'Permission to view notification_system', '2026-03-14T08:44:05.018473', '2026-03-14T08:44:05.018473'),
      ('03728caf-974b-4a70-941b-ddae4a319f4d', 'notification_system.delete', 'notification_system', 'delete', 'notification_system delete', 'Permission to delete notification_system', '2026-03-14T08:44:05.251235', '2026-03-14T08:44:05.251235'),
      ('03dba1fa-5bdf-45a6-aa0a-aa6117fe6285', 'global_risk_library.delete', 'global_risk_library', 'delete', 'Delete Global Risks', 'Delete global risks', '2026-03-17T09:56:03.320987', '2026-03-17T09:56:03.320987'),
      ('08e2ccca-5d32-49e0-b4e5-062fb0177f81', 'notification_broadcasts.delete', 'notification_broadcasts', 'delete', 'notification_broadcasts delete', 'Permission to delete notification_broadcasts', '2026-03-14T08:44:05.762885', '2026-03-14T08:44:05.762885'),
      ('0abe68aa-b4ac-4335-8189-24ab0cb4e460', 'notification_system.create', 'notification_system', 'create', 'notification_system create', 'Permission to create notification_system', '2026-03-14T08:44:05.119831', '2026-03-14T08:44:05.119831'),
      ('10c9c4e1-dc73-4ddd-a86d-944875232bda', 'global_risk_library.create', 'global_risk_library', 'create', 'Create Global Risks', 'Create global risks', '2026-03-17T09:56:03.320987', '2026-03-17T09:56:03.320987'),
      ('11582d29-77d4-49ed-b8a4-ef7a1c3c540f', 'feature_flag_registry.assign', 'feature_flag_registry', 'assign', 'feature_flag_registry.assign', 'feature_flag_registry.assign', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('1350f1fa-7c92-4159-a4a5-e64b3523d1ee', 'api_key_management.view', 'api_key_management', 'view', 'View API Keys', 'View API keys', '2026-03-30T21:06:14.218265', '2026-03-30T21:06:14.218265'),
      ('13fd0ba4-d66e-4223-8f0e-76b0ec002d39', 'notification_system.update', 'notification_system', 'update', 'notification_system update', 'Permission to update notification_system', '2026-03-14T08:44:05.184259', '2026-03-14T08:44:05.184259'),
      ('16757271-2e78-4262-bb10-164de2feb96a', 'api_key_management.update', 'api_key_management', 'update', 'Update API Key', 'Rotate API keys', '2026-03-30T21:06:14.218265', '2026-03-30T21:06:14.218265'),
      ('18e15e8f-21d4-4206-aac9-a7d116129277', 'access_governance_console.create', 'access_governance_console', 'create', 'access_governance_console.create', 'access_governance_console.create', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('20dfe0b5-3990-4bb4-bc02-6f93b8673e36', 'findings.delete', 'findings', 'delete', 'Delete Findings', 'Delete findings', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('2a13ab65-48c6-4044-b30a-94a748abb443', 'api_keys.create', 'api_keys', 'create', 'API Keys Create', 'create permission for API Keys', '2026-03-31T17:06:55.751075', '2026-03-31T17:06:55.751075'),
      ('32c6f06d-fdcd-4a67-9a0c-9f1596978659', 'notification_templates.create', 'notification_templates', 'create', 'notification_templates create', 'Permission to create notification_templates', '2026-03-14T08:44:05.379413', '2026-03-14T08:44:05.379413'),
      ('340ab0cd-3506-4c40-b2f8-87397ffd5d69', 'assessments.create', 'assessments', 'create', 'Create Assessments', 'Create assessment sessions', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('3b6dccb7-0a56-429b-b604-4a71763e5bfe', 'api_keys.update', 'api_keys', 'update', 'API Keys Update', 'update permission for API Keys', '2026-03-31T17:06:55.751075', '2026-03-31T17:06:55.751075'),
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
      ('beb5a4fe-a758-4549-a5ee-8ebe1a516445', 'api_key_management.create', 'api_key_management', 'create', 'Create API Key', 'Create new API keys', '2026-03-30T21:06:14.218265', '2026-03-30T21:06:14.218265'),
      ('c20bad33-1a4a-46fc-9157-9e7ecab76ee4', 'policy_management.assign', 'policy_management', 'assign', 'Policy Management — Assign', 'Permission to assign policy management.', '2026-03-24T11:16:59.147417', '2026-03-24T11:16:59.147417'),
      ('c47e6c29-5556-4b4c-a1b2-14a02fcec5de', 'findings.create', 'findings', 'create', 'Create Findings', 'Create findings in an assessment', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('c5a6b9e9-3a6b-48c8-8bd8-97c5e46d4cbb', 'api_keys.view', 'api_keys', 'view', 'API Keys View', 'view permission for API Keys', '2026-03-31T17:06:55.751075', '2026-03-31T17:06:55.751075'),
      ('cd7ac714-d579-4380-93d4-83e1c6dbc17b', 'ai_copilot.admin', 'ai_copilot', 'assign', 'AI Admin', 'View all users conversations, manage budgets, configure guardrails, kill agents', '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('d0f29e6c-218e-4deb-8d6d-956db7fb12bf', 'ai_copilot.create', 'ai_copilot', 'create', 'Create AI Conversations', 'Start new conversations, archive, manage own history', '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('dc8b435a-6aea-432e-8504-191a78bf53dc', 'notification_broadcasts.update', 'notification_broadcasts', 'update', 'notification_broadcasts update', 'Permission to update notification_broadcasts', '2026-03-14T08:44:05.698225', '2026-03-14T08:44:05.698225'),
      ('e18a4b59-eb37-4df3-9c09-263cf74ea33a', 'findings.view', 'findings', 'view', 'View Findings', 'View finding details and responses', '2026-03-18T03:12:15.808913', '2026-03-18T03:12:15.808913'),
      ('e6be427a-3f30-4fee-af22-cf8cc215da4e', 'workspace_management.delete', 'workspace_management', 'delete', 'workspace_management.delete', 'workspace_management.delete', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('ea89e772-4707-4117-9306-bd047278cb2c', 'notification_templates.update', 'notification_templates', 'update', 'notification_templates update', 'Permission to update notification_templates', '2026-03-14T08:44:05.44338', '2026-03-14T08:44:05.44338'),
      ('ebbeba6f-b172-4038-a2a3-384060a1ec43', 'feature_flag_registry.delete', 'feature_flag_registry', 'delete', 'feature_flag_registry.delete', 'feature_flag_registry.delete', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9011', 'audit_workspace_auditor_portfolio.view', 'audit_workspace_auditor_portfolio', 'view', 'Audit Workspace Auditor Portfolio View', 'View the assigned auditor portfolio across engagements.', '2026-04-02T06:50:48.046968', '2026-04-02T06:50:48.046968'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9012', 'audit_workspace_engagement_membership.view', 'audit_workspace_engagement_membership', 'view', 'Audit Workspace Engagement Membership View', 'View engagement membership-backed auditor workspace data.', '2026-04-02T06:50:48.046968', '2026-04-02T06:50:48.046968'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9013', 'audit_workspace_engagement_membership.update', 'audit_workspace_engagement_membership', 'update', 'Audit Workspace Engagement Membership Update', 'Manage engagement membership-backed auditor workspace access.', '2026-04-02T06:50:48.046968', '2026-04-02T06:50:48.046968'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9021', 'audit_workspace_control_access.view', 'audit_workspace_control_access', 'view', 'Audit Workspace Control Access View', 'View engagement-scoped controls in the auditor workspace.', '2026-04-02T06:54:47.932116', '2026-04-02T06:54:47.932116'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9022', 'audit_workspace_evidence_requests.view', 'audit_workspace_evidence_requests', 'view', 'Audit Workspace Evidence Requests View', 'View auditor evidence requests in the engagement workflow.', '2026-04-02T06:54:47.932116', '2026-04-02T06:54:47.932116'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9023', 'audit_workspace_evidence_requests.create', 'audit_workspace_evidence_requests', 'create', 'Audit Workspace Evidence Requests Create', 'Create engagement-scoped auditor evidence requests.', '2026-04-02T06:54:47.932116', '2026-04-02T06:54:47.932116'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9024', 'audit_workspace_evidence_requests.approve', 'audit_workspace_evidence_requests', 'approve', 'Audit Workspace Evidence Requests Approve', 'Approve or fulfill auditor evidence requests.', '2026-04-02T06:54:47.932116', '2026-04-02T06:54:47.932116'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9025', 'audit_workspace_evidence_requests.revoke', 'audit_workspace_evidence_requests', 'revoke', 'Audit Workspace Evidence Requests Revoke', 'Revoke or dismiss auditor evidence requests.', '2026-04-02T06:54:47.932116', '2026-04-02T06:54:47.932116'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9031', 'audit_workspace_auditor_tasks.view', 'audit_workspace_auditor_tasks', 'view', 'Audit Workspace Auditor Tasks View', 'View engagement-scoped tasks through the auditor workspace.', '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9032', 'audit_workspace_auditor_tasks.create', 'audit_workspace_auditor_tasks', 'create', 'Audit Workspace Auditor Tasks Create', 'Create engagement-scoped auditor tasks.', '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9033', 'audit_workspace_auditor_tasks.assign', 'audit_workspace_auditor_tasks', 'assign', 'Audit Workspace Auditor Tasks Assign', 'Assign engagement-scoped auditor tasks to active engagement participants.', '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9034', 'audit_workspace_auditor_tasks.update', 'audit_workspace_auditor_tasks', 'update', 'Audit Workspace Auditor Tasks Update', 'Update engagement-scoped auditor tasks.', '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9041', 'audit_workspace_auditor_findings.view', 'audit_workspace_auditor_findings', 'view', 'Audit Workspace Auditor Findings View', 'View engagement-scoped auditor findings.', '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9042', 'audit_workspace_auditor_findings.create', 'audit_workspace_auditor_findings', 'create', 'Audit Workspace Auditor Findings Create', 'Create engagement-scoped auditor findings.', '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089'),
      ('ec07be31-5506-4a09-8f9f-7d3d402f9043', 'audit_workspace_auditor_findings.update', 'audit_workspace_auditor_findings', 'update', 'Audit Workspace Auditor Findings Update', 'Update engagement-scoped auditor findings.', '2026-04-02T06:54:47.987089', '2026-04-02T06:54:47.987089'),
      ('edcd40a1-d791-4ca0-9955-4766088115f1', 'ai_copilot.approve', 'ai_copilot', 'approve', 'Approve AI Actions', 'Approve or reject pending write tool approval requests', '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647'),
      ('ee241772-1028-47fe-813c-04377db03e20', 'group_access_assignment.create', 'group_access_assignment', 'create', 'group_access_assignment.create', 'group_access_assignment.create', '2026-03-13T17:32:52.754777', '2026-03-13T17:32:52.754777'),
      ('f70226ef-a1da-4e9c-8115-2388b7436e9a', 'frameworks.approve', 'framework_management', 'approve', 'Approve Frameworks', 'Approve and publish frameworks to the marketplace', '2026-03-18T13:47:14.553559', '2026-03-18T13:47:14.553559'),
      ('fbee9a75-4360-4a59-8f02-130491ce81af', 'api_key_management.revoke', 'api_key_management', 'revoke', 'Revoke API Key', 'Revoke or delete API keys', '2026-03-30T21:06:14.218265', '2026-03-30T21:06:14.218265')
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

-- 03_auth_manage.33_dim_workspace_types (11 rows)
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
      ('00000000-0000-0000-0000-000000001408', 'grc', 'GRC', 'Governance, Risk and Compliance workspace for compliance programs and audit engagements.', 80, FALSE, '2026-03-30T00:00:00', '2026-03-30T00:00:00'),
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

-- 03_auth_manage.16_fct_roles (17 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."16_fct_roles" (id, tenant_key, role_level_code, code, name, description, scope_org_id, scope_workspace_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
  VALUES
      ('00000000-0000-0000-0000-000000000601', 'default', 'super_admin', 'platform_super_admin', 'Platform Super Admin', 'System role for full platform feature governance control.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000002001', 'default', 'platform', 'basic_user', 'Basic User', 'Default role granted to every registered user. Allows onboarding setup.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T00:00:00', '2026-03-14T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004001', 'default', 'org', 'org_admin', 'Org Admin', 'Full administrative control within an organization. Can manage org settings, members, and all workspaces.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.657832', '2026-03-17T06:38:32.657832', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004002', 'default', 'org', 'org_member', 'Org Member', 'Standard organization member. Can view org, interact with all workspaces, but cannot administer the org.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.686831', '2026-03-17T06:38:32.686831', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004003', 'default', 'org', 'org_viewer', 'Org Viewer', 'Read-only organization access. Can view org details but cannot modify anything. No workspace access unless separately granted.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.713382', '2026-03-17T06:38:32.713382', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004011', 'default', 'workspace', 'workspace_admin', 'Workspace Admin', 'Full administrative control within a workspace. Can manage workspace settings and members.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.741419', '2026-03-17T06:38:32.741419', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004012', 'default', 'workspace', 'workspace_contributor', 'Workspace Contributor', 'Can view and contribute to workspace content. Cannot manage members or settings.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.769931', '2026-03-17T06:38:32.769931', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004013', 'default', 'workspace', 'workspace_viewer', 'Workspace Viewer', 'Read-only workspace access. Can view workspace content but cannot modify anything.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.857507', '2026-03-17T06:38:32.857507', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000005100', '__platform__', 'workspace', 'grc_practitioner', 'GRC Practitioner', 'Full GRC compliance program ownership: framework activation, evidence approval, task management, and org posture.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000005101', '__platform__', 'workspace', 'grc_sme', 'GRC SME', 'Compliance specialist: contributes evidence, assigns tasks, views live test results, responds to findings.', NULL, NULL, TRUE, FALSE, TRUE, FALSE, TRUE, TRUE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000005102', '__platform__', 'workspace', 'grc_engineer', 'Engineer', 'Remediation only: completes assigned tasks and submits evidence for controls they own.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000005103', '__platform__', 'workspace', 'grc_ciso', 'CISO / Exec', 'Executive read-only access: posture dashboard, risk register, and framework status.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000005104', '__platform__', 'workspace', 'grc_lead_auditor', 'Lead Auditor', 'External audit lead: engagement-scoped view of controls and published evidence, raises findings, assigns tasks.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000005105', '__platform__', 'workspace', 'grc_staff_auditor', 'Staff Auditor', 'External audit staff: engagement-scoped read and internal annotation, findings go to lead for sign-off.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000005106', '__platform__', 'workspace', 'grc_vendor', 'Vendor', 'Vendor questionnaire access only: no compliance program visibility.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'default', 'platform', 'external_collaborator', 'External Collaborator', 'Limited platform role for external users who authenticate via magic link. Grants read-only access to tasks, comments, and attachments.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T15:38:38.28856', '2026-03-17T15:38:38.28856', NULL, NULL, NULL, NULL),
      ('9441cc00-943f-4469-aef5-7fae7171b2b9', 'default', 'platform', 'super_admin', 'Super Admin', 'Full platform access', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL)
  ON CONFLICT (tenant_key, role_level_code, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, scope_org_id = EXCLUDED.scope_org_id, scope_workspace_id = EXCLUDED.scope_workspace_id, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.17_fct_user_groups (17 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."17_fct_user_groups" (id, tenant_key, role_level_code, code, name, description, scope_org_id, scope_workspace_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by, parent_group_id)
  VALUES
      ('00000000-0000-0000-0000-000000000701', 'default', 'super_admin', 'platform_super_admin', 'Platform Super Admin', 'System group for platform super administrators.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000003001', 'default', 'platform', 'default_users', 'Default Users', 'Every registered user is automatically a member of this group.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T00:00:00', '2026-03-14T00:00:00', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006001', 'default', 'org', 'org_admins', 'Org Admins', 'Organization administrators with full org management permissions', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.936618', '2026-03-31T16:44:30.936618', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006002', 'default', 'org', 'org_members', 'Org Members', 'Standard organization members', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.936618', '2026-03-31T16:44:30.936618', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006003', 'default', 'org', 'org_viewers', 'Org Viewers', 'Read-only organization access', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.936618', '2026-03-31T16:44:30.936618', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006011', 'default', 'workspace', 'workspace_admins', 'Workspace Admins', 'Workspace administrators', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.965891', '2026-03-31T16:44:30.965891', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006012', 'default', 'workspace', 'workspace_contributors', 'Workspace Contributors', 'Workspace contributors who can create and edit', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.965891', '2026-03-31T16:44:30.965891', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006013', 'default', 'workspace', 'workspace_viewers', 'Workspace Viewers', 'Read-only workspace access', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.965891', '2026-03-31T16:44:30.965891', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006100', 'default', 'workspace', 'grc_leads', 'GRC Leads', 'GRC compliance program leads', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.991899', '2026-03-31T16:44:30.991899', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006101', 'default', 'workspace', 'grc_smes', 'GRC SMEs', 'Subject matter experts for compliance', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.991899', '2026-03-31T16:44:30.991899', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006102', 'default', 'workspace', 'grc_engineers', 'Engineers', 'Engineers handling remediation tasks', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.991899', '2026-03-31T16:44:30.991899', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006103', 'default', 'workspace', 'grc_cisos', 'CISO / Execs', 'Executive compliance oversight', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.991899', '2026-03-31T16:44:30.991899', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006104', 'default', 'workspace', 'grc_lead_auditors', 'Lead Auditors', 'External lead auditors', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.991899', '2026-03-31T16:44:30.991899', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006105', 'default', 'workspace', 'grc_staff_auditors', 'Staff Auditors', 'External staff auditors', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.991899', '2026-03-31T16:44:30.991899', NULL, NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000006106', 'default', 'workspace', 'grc_vendors', 'Vendors', 'External vendor questionnaire access', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-31T16:44:30.991899', '2026-03-31T16:44:30.991899', NULL, NULL, NULL, NULL, NULL),
      ('0ed8698f-247b-4d00-9155-d12cb2f0be47', 'default', 'platform', 'platform_admins', 'Platform Admins', 'Platform administrators', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL, NULL),
      ('9e4e4815-0123-4ea0-8f46-e6663ee8ca95', 'default', 'platform', 'external_collaborators', 'External Collaborators', 'System group for all external collaborator users. Automatically enrolled when a user authenticates via magic link for the first time.', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T15:38:38.329908', '2026-03-17T15:38:38.329908', NULL, NULL, NULL, NULL, NULL)
  ON CONFLICT (tenant_key, role_level_code, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, scope_org_id = EXCLUDED.scope_org_id, scope_workspace_id = EXCLUDED.scope_workspace_id, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by, parent_group_id = EXCLUDED.parent_group_id;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.19_lnk_group_role_assignments (17 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (id, group_id, role_id, assignment_status, effective_from, effective_to, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
  VALUES
      ('00000000-0000-0000-0000-000000000801', '00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000601', 'active', '2026-03-13T00:00:00', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T00:00:00', '2026-03-13T00:00:00', NULL, NULL, NULL, NULL),
      ('00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003001', '00000000-0000-0000-0000-000000002001', 'active', '2026-03-14T00:00:00', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-14T00:00:00', '2026-03-14T00:00:00', NULL, NULL, NULL, NULL),
      ('11ff429c-99e5-47f4-83c8-ea4cbba775aa', '00000000-0000-0000-0000-000000006100', '00000000-0000-0000-0000-000000005100', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('173c6d05-1aab-4d5f-b31e-1628101c824f', '00000000-0000-0000-0000-000000006001', '00000000-0000-0000-0000-000000004001', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('18b90535-dba5-45e3-9d86-cecd3f846171', '00000000-0000-0000-0000-000000006102', '00000000-0000-0000-0000-000000005102', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('419e08cb-e673-419a-8ff4-b369eacbeac6', '00000000-0000-0000-0000-000000006101', '00000000-0000-0000-0000-000000005101', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('6f677c64-20ca-4547-b56d-8bbf14a8533f', '00000000-0000-0000-0000-000000006013', '00000000-0000-0000-0000-000000004013', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('8a3e2eaf-7b4b-4525-a53e-15b8b6e025b0', '00000000-0000-0000-0000-000000006012', '00000000-0000-0000-0000-000000004012', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('90d0e129-b60e-4fdb-a56e-8e05a84e29bb', '00000000-0000-0000-0000-000000006106', '00000000-0000-0000-0000-000000005106', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('94b37a30-25bb-4c6a-9f20-c4a55367f4d1', '00000000-0000-0000-0000-000000006011', '00000000-0000-0000-0000-000000004011', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('a0fd5afa-3402-4aed-98ad-90181918cdd9', '00000000-0000-0000-0000-000000006103', '00000000-0000-0000-0000-000000005103', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('af3aa3cc-9d2d-47b9-aac4-c220a6c4ade7', '00000000-0000-0000-0000-000000006105', '00000000-0000-0000-0000-000000005105', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('afeb32b0-fc67-42c2-a418-b6ac64da34f3', '0ed8698f-247b-4d00-9155-d12cb2f0be47', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'active', '2026-03-13T17:33:40.526446', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('c0c87fbc-3e9f-49b7-bbbf-541dbfeaa46e', '9e4e4815-0123-4ea0-8f46-e6663ee8ca95', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'active', '2026-03-17T15:38:38.371545', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T15:38:38.371545', '2026-03-17T15:38:38.371545', NULL, NULL, NULL, NULL),
      ('c1e6a729-5444-4bff-98fa-30c0c5553306', '00000000-0000-0000-0000-000000006104', '00000000-0000-0000-0000-000000005104', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('d57cd7dd-6a4a-4cf8-be67-a3f1df0558df', '00000000-0000-0000-0000-000000006002', '00000000-0000-0000-0000-000000004002', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL),
      ('f792485e-15ff-4ceb-bd17-c266bcc5622b', '00000000-0000-0000-0000-000000006003', '00000000-0000-0000-0000-000000004003', 'active', '2026-03-31T16:44:31.018048', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T16:44:31.018048', '2026-03-31T16:44:31.018048', NULL, NULL, NULL, NULL)
  ON CONFLICT (group_id, role_id) DO UPDATE SET assignment_status = EXCLUDED.assignment_status, effective_from = EXCLUDED.effective_from, effective_to = EXCLUDED.effective_to, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.20_lnk_role_feature_permissions (674 rows)
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
      ('01a4caf6-8cd9-489c-817d-7c283d9ce931', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9041', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('020b793e-fdb0-407d-af2b-e6bf7b556c43', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000555', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:02.904557', '2026-04-01T15:59:02.904557', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('02209401-f8e8-4329-b9d7-877ff3a31a17', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003042', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('024926e6-6998-4240-b733-5805fd6bbee9', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('0258ed1c-f258-46c3-b4f7-c8efcc194431', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001705', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:52.516852', '2026-04-01T15:59:52.516852', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('02920bf8-db3d-4cad-8f61-76ef9cac88ba', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9042', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('02967935-c6b4-44b4-b32b-05bf4816d1d8', '00000000-0000-0000-0000-000000005104', '6732df5a-2522-4447-bd3f-5c33ebd61696', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('0343e633-4113-4a69-a9bf-17c23c985824', '00000000-0000-0000-0000-000000005102', '00000000-0000-0000-0000-000000008001', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('04540b28-2a18-44d8-8f8a-484bcce959c9', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9043', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('047de117-0e0e-4642-a61d-bfb17c0004b9', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000008006', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('050d1daa-3d36-4a8d-922e-cf717a4e4278', '00000000-0000-0000-0000-000000000601', 'bc922db4-d4f5-4a10-83be-cc92b6af097a', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('05487684-13ff-4d84-afa0-3e679bd0cc6d', '00000000-0000-0000-0000-000000000601', '55963948-87ca-47e7-9de7-ddd7f3dc675f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:18:16.315393', '2026-03-17T11:18:16.315393', NULL, NULL, NULL, NULL),
      ('05581a02-7bf1-455b-8048-8bdeb8733662', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000005025', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:45:59.252772', '2026-04-01T06:45:59.252772', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('0567c3bf-492d-43a9-8a82-a3759ab3e933', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000003051', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('05f6076e-ee87-450f-bd64-8407fbecfbcf', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000006021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:55.021773', '2026-04-01T06:51:55.021773', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('06076075-aafc-45a8-8fcc-299f495f6f65', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000509', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('07c61b27-3439-4d52-a979-7f40dad02d46', '00000000-0000-0000-0000-000000005102', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('08394d1a-c83f-40e2-bb48-2aab23c1b6b1', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '73f7950d-7163-4467-837d-b6907dd0abcf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.676368', '2026-03-14T08:45:17.676368', NULL, NULL, NULL, NULL),
      ('0863af5f-c26b-4b9c-a3c1-c11d3767bf40', '00000000-0000-0000-0000-000000005105', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('08f887dd-9895-4551-9a68-bd573218cbc6', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000008902', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.846896', '2026-04-01T02:55:56.846896', NULL, NULL, NULL, NULL),
      ('08f9d1aa-6013-4d7e-9ca7-5a3767e5ef4f', '00000000-0000-0000-0000-000000005101', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('098c9bb5-11b2-4a66-bd74-76992e36b07a', '9441cc00-943f-4469-aef5-7fae7171b2b9', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('0aee4b8d-af42-44d5-a010-ffc684a2533d', '9441cc00-943f-4469-aef5-7fae7171b2b9', '11582d29-77d4-49ed-b8a4-ef7a1c3c540f', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('0b1f0d80-4f5c-407c-86a8-a2b1be850c10', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '96f825f4-8b6d-48ea-914f-15afe230fbc8', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.726112', '2026-03-14T08:45:17.726112', NULL, NULL, NULL, NULL),
      ('0b9a124a-2d16-4c12-a9a4-ce75fb5760ae', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008004', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:23.904423', '2026-04-01T06:49:23.904423', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('0bda704c-434a-42d4-a69c-9962bb00bb51', '00000000-0000-0000-0000-000000005100', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('0c05c774-1ba6-4a54-a96d-58ecd47b3703', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('0c336609-0d75-4acd-94ed-b595413ca1b5', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9011', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('0c67d4db-ad94-41f9-a72c-170acf9f32cd', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('0ce94036-4c85-4cdf-946d-992e749ab545', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('0d522ad8-c100-4f81-bd4b-13a67a5134ef', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050f', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('0d87e5cf-ad3b-4dd6-b2fc-e87ece76d20a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005024', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('0d88cb48-5bb1-4af3-927d-46b82f334644', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001817', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('0d8c3e4a-d373-47a6-9cd0-e737872266ba', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'a59a9d62-3e75-47ae-b485-11b0d6c8669e', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('0d9c736a-e61c-4e8c-854b-35b2475c123b', '00000000-0000-0000-0000-000000005100', '6732df5a-2522-4447-bd3f-5c33ebd61696', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('0db26608-7a66-475a-83d8-28e329973750', '00000000-0000-0000-0000-000000004011', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('0ecdf057-008e-4de8-965e-e6bfba3c22af', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001713', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('0f37b94c-4470-4227-af38-4bc7495aff99', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003043', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:34.438185', '2026-04-01T06:49:34.438185', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('0f93f7c5-5643-4e1d-939b-2d4ff1854cea', '00000000-0000-0000-0000-000000005100', '20dfe0b5-3990-4bb4-bc02-6f93b8673e36', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('10380b0c-844e-4ab1-b7b0-1753922079a1', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000005020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:28.172606', '2026-04-01T06:49:28.172606', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('10b6f2cc-6cae-4f04-93b7-1c58c5ad785c', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003052', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:21.17401', '2026-04-01T06:49:21.17401', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('11e9a2e9-a4fc-4d41-8357-931d1c6c2410', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.991631', '2026-03-14T08:45:15.991631', NULL, NULL, NULL, NULL),
      ('124aeb6b-539c-49df-9db3-ecd8a16a1634', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003032', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('133e67c4-5ba9-4af0-ae0f-30a224b62a8a', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9011', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('13c76cac-a14f-4599-95ca-47b963c50d19', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000005023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:29.933985', '2026-04-01T06:49:29.933985', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('13ebcdc5-ec85-4282-a230-bae43427232d', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('143f4277-45bc-4e92-a2ec-0001ac7e3b9d', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.905989', '2026-03-14T08:45:14.905989', NULL, NULL, NULL, NULL),
      ('155292ee-7f38-492c-9837-ccfdf648655e', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000005024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:30.539934', '2026-04-01T06:49:30.539934', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('156ac245-c214-4ea7-8215-0b709ac274bc', '9441cc00-943f-4469-aef5-7fae7171b2b9', '7f9057c2-d375-4517-98ec-84956a68343b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T13:56:11.417625', '2026-03-16T13:56:11.417625', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1683dd05-021d-419f-9537-071af26c0192', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001714', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.697235', '2026-03-14T08:45:15.697235', NULL, NULL, NULL, NULL),
      ('16d22e6b-924c-471c-867a-52e6b26e0a93', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005021', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('16dbf61f-80dc-41f7-882f-ed00a2a46c5c', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000505', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('173476dc-0d09-4ed0-9a25-283734f814d1', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:55:12.499819', '2026-04-01T06:55:12.499819', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1750ac00-1ecd-43ae-a819-b1033e7987ea', '00000000-0000-0000-0000-000000002001', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('176ca84b-244b-44d8-96da-4b5173be1057', '00000000-0000-0000-0000-000000000601', '03dba1fa-5bdf-45a6-aa0a-aa6117fe6285', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:18:16.315393', '2026-03-17T11:18:16.315393', NULL, NULL, NULL, NULL),
      ('17826f49-01cc-4437-a21e-d08250d09736', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000555', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('17b1a57a-2273-4332-b404-ed82d0bd2fb8', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('18570f2c-3e27-4e84-b48b-bc29a9728eb3', '00000000-0000-0000-0000-000000005104', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('18594423-a90c-4f5e-a3c7-733e9809cac4', '00000000-0000-0000-0000-000000002001', '10c9c4e1-dc73-4ddd-a86d-944875232bda', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:55:20.683695', '2026-04-01T06:55:20.683695', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1896e22e-0663-44de-8f14-99ced0689e86', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9034', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('189d4458-baf3-4752-b6bb-94c2c8cd037c', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000541', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('18ea3618-68d5-4620-bbd2-a41c096bbfb8', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000009001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('19404624-57da-437a-832c-443705ab08ea', '00000000-0000-0000-0000-000000004001', 'a14daddc-fb26-4f71-9e4c-fb60dc2a8c9a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:05.867968', '2026-04-01T06:51:05.867968', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('19998df7-e2d9-4540-b222-b83d2410e743', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008902', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:30.407421', '2026-04-01T06:51:30.407421', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1aeb7c7e-d0ed-4d61-9db0-09459ff03ce4', '00000000-0000-0000-0000-000000002001', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('1b609cfb-00d8-4754-b9a8-2aa1c0b9a770', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9041', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('1b666727-d5d7-4e2a-9ab3-969aba215187', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('1c1af33c-a5d2-4d61-a5a8-ae1dddb76367', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001813', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('1c34216f-405d-42cd-be05-401c6074646a', '65643275-fd73-40ef-b6d8-8069b3b18d52', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-14T01:29:28.118955', '2026-03-14T01:29:29.679819', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', '2026-03-14T01:29:29.679819', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b'),
      ('1c749feb-0d40-4dfd-9ef9-7d2daa08b124', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000504', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('1c972805-2db4-4fba-a735-c4ba44284c92', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003051', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:20.509809', '2026-04-01T06:49:20.509809', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1ce597c7-1625-48bb-a16d-892f97e20242', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000516', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.186953', '2026-03-14T08:45:17.186953', NULL, NULL, NULL, NULL),
      ('1d42d248-eaa3-429c-84be-69e0fce7b87c', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008004', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('1d68a807-56b2-4912-8103-d1c536a38668', '00000000-0000-0000-0000-000000000601', '32c6f06d-fdcd-4a67-9a0c-9f1596978659', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('1daebd63-abae-4de1-8ac9-d0ea2c53f263', '00000000-0000-0000-0000-000000000601', '96f825f4-8b6d-48ea-914f-15afe230fbc8', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('1de083f5-2d94-492a-8ba6-412169c60923', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001701', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.3008', '2026-03-14T08:45:15.3008', NULL, NULL, NULL, NULL),
      ('1de3de25-24cf-48e2-9cf7-3b98b23ef8df', '197ae046-a989-418f-99df-ec17310d73a4', '00000000-0000-0000-0000-000000006022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:44.016031', '2026-03-18T12:03:44.016031', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1e467d85-f417-4600-84c7-3c543639d93e', '00000000-0000-0000-0000-000000004012', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('1e481b01-577e-48f5-a5fc-66c96e4c0864', '197ae046-a989-418f-99df-ec17310d73a4', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:40.82988', '2026-03-18T12:03:40.82988', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('1e8e0ca5-a179-4463-926d-fc76dafc6f59', '9a2f8bd7-f635-4cfe-9bad-8f640f50fe74', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:02:34.87345', '2026-03-18T12:02:34.87345', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', NULL, NULL),
      ('1e9e7fc1-f4e4-4c4a-a333-de908b951f4d', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003033', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('1f05f885-94fe-4012-b62e-739bfacbad91', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9034', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('20066110-3537-45f4-aadd-5cc5cd92588a', '00000000-0000-0000-0000-000000004011', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('201cc15a-4a57-4870-88a1-33379f0f70ba', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003015', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T18:11:13.659325', '2026-03-18T18:11:13.659325', NULL, NULL, NULL, NULL),
      ('2031a183-25d4-4745-9ef3-d5317a3e29d7', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000543', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.10148', '2026-03-17T07:49:17.10148', NULL, NULL, NULL, NULL),
      ('2032fc1c-55ee-497d-bdb6-e67d8530336d', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '32c6f06d-fdcd-4a67-9a0c-9f1596978659', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.577762', '2026-03-14T08:45:17.577762', NULL, NULL, NULL, NULL),
      ('20454244-503b-4090-b865-02962c0cf114', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000008901', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.810308', '2026-04-01T02:55:56.810308', NULL, NULL, NULL, NULL),
      ('2046ded2-7fd5-4b37-9465-ae00ef6f56e4', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('2093b07f-5fe7-4208-a1c0-90958321aa1e', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:49.468188', '2026-04-01T06:54:49.468188', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('20c12ceb-83a5-4e16-9b6f-fe69c510e16c', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000512', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('222c19fe-0f0c-4594-819c-6b90b84f7e65', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000515', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:01.051702', '2026-04-01T06:51:01.051702', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('222d7143-1bd6-40d8-ba77-ada5cef175b7', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003052', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('225d705d-cb31-4345-aeeb-53ed90793ad6', '00000000-0000-0000-0000-000000004001', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:52:03.869945', '2026-04-01T06:52:03.869945', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('22b7a3d8-aa40-4a47-b82c-9eba3c711948', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9021', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('23c3d45a-2af9-4d35-a6eb-d7efea5f2634', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9025', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('2432a954-38b9-4579-9971-7c7e5fc556b4', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003065', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('251dab77-74a4-4074-91e4-ff9eedb8a107', '00000000-0000-0000-0000-000000005103', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('252b2c4a-6647-4655-96b3-4f5c307a81f0', '9441cc00-943f-4469-aef5-7fae7171b2b9', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('25591cfa-862a-4aeb-a185-ecdf3110211d', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9022', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('2675a747-d414-4a59-88b2-c592c0c479a8', '00000000-0000-0000-0000-000000002001', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('26fe35be-46ab-432e-8ccc-a457c3742bc3', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:29.481512', '2026-04-01T06:51:29.481512', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('274317e6-066f-4853-a52c-eff491b16ab0', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('2743e2c1-7b14-44a9-8849-d0ffa8040d5c', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000514', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.082744', '2026-03-14T08:45:17.082744', NULL, NULL, NULL, NULL),
      ('2847bdd1-4870-4efb-bc1b-c18ecdbb66a5', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('28938c9c-ba88-4e17-bb91-5dabaad97da6', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('28d0eb87-1fef-469f-adf2-04e58f1b889e', '00000000-0000-0000-0000-000000002001', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:33.990596', '2026-04-01T06:54:33.990596', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('291ca0d0-406e-4b95-aa47-f29901a6b179', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001712', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('2953498c-8b41-4a6d-9742-7d67af0ea590', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('2961a808-7f1d-4bfd-ac95-5555078eb1b8', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9025', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('2a66ff21-3176-454e-8da0-5434036fcd6a', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9041', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('2aca98c0-f966-4d34-a3c2-c8ba736b6605', '00000000-0000-0000-0000-000000004001', '03dba1fa-5bdf-45a6-aa0a-aa6117fe6285', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:13.109121', '2026-04-01T06:51:13.109121', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('2b57ed09-ad4b-495c-90ff-6e55226fbe15', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9031', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('2b5fa77a-a643-4f1b-b4e5-27a348562f35', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001702', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:51.11084', '2026-04-01T15:59:51.11084', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('2c97e1b8-cb28-4c08-acfa-ce731eacba90', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000008007', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('2efccfab-cf7a-4e92-ab88-78d2bf887ced', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000000514', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-01T18:42:32.767057', '2026-04-01T18:42:32.767057', NULL, NULL, NULL, NULL),
      ('2f017666-3e73-4b7f-b5a3-86cb43b71124', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9032', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('2f5a1f96-512a-41b7-95be-ca95e045ad77', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000552', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:01.410229', '2026-04-01T15:59:01.410229', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('2fb15698-4d81-42d6-a84c-ff77e67e0799', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'b536b3c5-d955-441b-a439-4a57243b049a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:16:43.585605', '2026-03-17T11:16:43.585605', NULL, NULL, NULL, NULL),
      ('2ff9ddfc-927d-47e3-ad88-c190d5bbe340', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.05298', '2026-03-14T08:45:15.05298', NULL, NULL, NULL, NULL),
      ('300987a9-7603-4ade-b2eb-894b10122985', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:28.177957', '2026-04-01T06:51:28.177957', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('3037a44e-5ae3-4779-9cb1-436955fe8f94', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001703', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:51.624248', '2026-04-01T15:59:51.624248', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('3088d634-546d-4344-acf8-6f55f28474df', '00000000-0000-0000-0000-000000004011', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('30c4d300-d4d9-4ffa-aad4-f15b04173664', 'ddf8bcb6-6d66-472c-9b29-4c1c0e3a9d3f', '18e15e8f-21d4-4206-aac9-a7d116129277', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-16T12:34:42.823331', '2026-03-16T12:34:46.025535', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-16T12:34:46.025535', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('30d86fe9-d145-4dda-b202-e4e5aa72dbba', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006020', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('30e320e8-4ee4-40f7-8ec2-faeda204f8df', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000509', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.808768', '2026-03-14T08:45:14.808768', NULL, NULL, NULL, NULL),
      ('3145fb9a-33ae-480b-8ebb-4a32fda49700', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('3148ba8a-3e26-4820-8a6e-d8ef5183997d', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9033', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('31f2b9f1-a8a0-450e-b327-7427428ff571', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003042', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('325be562-5372-494d-be04-b08e2354e2dd', '197ae046-a989-418f-99df-ec17310d73a4', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:42.629382', '2026-03-18T12:03:42.629382', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('329824e0-4fef-40b1-ba5d-37e773c65535', '9441cc00-943f-4469-aef5-7fae7171b2b9', '18e15e8f-21d4-4206-aac9-a7d116129277', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('32b93ad6-ff93-4cbe-863d-fe698f9100d3', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006024', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('32bf7887-709d-4f3a-bbb6-b5bb449111ab', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:13:43.791271', '2026-03-17T07:13:43.791271', NULL, NULL, NULL, NULL),
      ('3310abd1-36f7-4417-9eab-fac2a5b19e4c', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000006020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:53:40.017705', '2026-04-01T06:53:40.017705', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('33f1d3dd-35f0-4588-b9ad-fb64ba651fd4', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003022', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('3431844d-98ac-4b1f-a64e-f7854a2b370a', '00000000-0000-0000-0000-000000004001', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('34a00e7c-b94e-4bd9-994a-c331e12370d3', '00000000-0000-0000-0000-000000004003', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.980336', '2026-03-17T06:38:32.980336', NULL, NULL, NULL, NULL),
      ('354c9e88-5764-429b-bc04-e8b0f116d657', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003011', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('35a45297-ab63-4a13-9573-f6a53774e8c2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003013', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('35beec67-bd00-4222-9fde-0d88b0637887', '00000000-0000-0000-0000-000000005102', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('35cc8c6c-98c3-4fe2-971c-22b135d10877', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003072', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('3619c50b-a16d-4605-8e2d-8779eea82727', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000005023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:45:57.591462', '2026-04-01T06:45:57.591462', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('362efce4-a76c-42e5-867d-f0f16b27ff29', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001812', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('365a41ea-6267-43f7-a8c2-272367383938', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001704', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:52.144683', '2026-04-01T15:59:52.144683', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('36805922-fa6b-4814-9642-a74ef927efca', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.857642', '2026-03-14T08:45:14.857642', NULL, NULL, NULL, NULL),
      ('38a57f4d-6e50-4c32-9742-a0ff8c2b47df', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001712', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('38de9456-895f-4beb-ab6c-6895bc9fbc72', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001819', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.440764', '2026-03-14T08:45:16.440764', NULL, NULL, NULL, NULL),
      ('39ae4e4a-d66a-48a0-a67a-e39b68049964', '00000000-0000-0000-0000-000000004011', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('39bb5090-2401-4f6c-8ad3-eb91aa9d96bf', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001702', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.351665', '2026-03-14T08:45:15.351665', NULL, NULL, NULL, NULL),
      ('3a0c0c77-4db7-4365-8b91-4eacca1c3945', '00000000-0000-0000-0000-000000000601', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('3a8fc603-16fc-43ed-ad36-b716c6d0ede4', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T05:39:05.819391', '2026-03-23T05:39:05.819391', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('3abcceb6-6cdb-4547-83c8-a320260ac4bd', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000005022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:45:56.713093', '2026-04-01T06:45:56.713093', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('3b016596-12de-4a6d-8673-5cd650e2bf0a', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003042', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:34.0493', '2026-04-01T06:49:34.0493', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('3b0196e9-2ac2-4bd5-98fa-7c4453e51995', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001703', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.40121', '2026-03-14T08:45:15.40121', NULL, NULL, NULL, NULL),
      ('3c3b2640-80e5-4f69-90ab-8e22e1182cb3', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001811', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.040519', '2026-03-14T08:45:16.040519', NULL, NULL, NULL, NULL),
      ('3cc7ca55-0370-4a36-8ab5-60f5fbdfe094', '9441cc00-943f-4469-aef5-7fae7171b2b9', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('3deb0f78-13a4-46ee-93d4-d2b4cebe4c3e', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000005020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:45:52.338547', '2026-04-01T06:45:52.338547', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('3e77cb40-6482-4cce-ab10-d886817b75e8', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000507', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('3e86ad2a-edb8-4b94-8975-0215f66111b4', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'dc8b435a-6aea-432e-8504-191a78bf53dc', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.832262', '2026-03-14T08:45:17.832262', NULL, NULL, NULL, NULL),
      ('3ea7ebc0-b278-4598-a19b-6180f8c1b59d', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008006', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:09.201097', '2026-04-01T15:59:09.201097', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('3ecff9a6-f9d8-4670-b3ed-ca81d4cddbdf', '00000000-0000-0000-0000-000000000601', 'ee241772-1028-47fe-813c-04377db03e20', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('3fa7db33-9fc1-49c8-bf2d-18c648cb9711', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('3fe850de-8441-41f2-ad8f-aaa5962a6f32', '00000000-0000-0000-0000-000000000601', '4db67994-51ad-4dde-93b1-3abd1842da4d', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('401a4a84-547c-4d1b-ad38-43fe483ac89b', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000506', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.661671', '2026-03-14T08:45:14.661671', NULL, NULL, NULL, NULL),
      ('401b4297-5d02-4375-8fbb-1765763275c8', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:47:17.872104', '2026-04-01T06:47:17.872104', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4043f0d5-9d5f-486f-bc80-a28a48a71ffa', '00000000-0000-0000-0000-000000000601', '10c9c4e1-dc73-4ddd-a86d-944875232bda', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:18:16.315393', '2026-03-17T11:18:16.315393', NULL, NULL, NULL, NULL),
      ('417ee135-cd89-4df3-be2a-9d8c42f988d5', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('42011043-6e08-448e-9f8d-052f6d7e553d', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001701', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:50.439214', '2026-04-01T15:59:50.439214', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('43374250-1fd0-4d33-89c9-82b8b4375d0b', '00000000-0000-0000-0000-000000005101', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('434b72a5-a453-4bf6-b94f-31914a5e5df7', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'ea89e772-4707-4117-9306-bd047278cb2c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.62828', '2026-03-14T08:45:17.62828', NULL, NULL, NULL, NULL),
      ('435434db-96e3-49b2-ab6e-b342e8e0e8dd', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9043', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('439869fc-5d4a-4480-83ea-432d199151a9', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9033', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('43d52747-e7f8-4f88-996a-ef1f1c508f8a', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003052', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:47:26.687807', '2026-04-01T06:47:32.885064', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T06:47:32.885064', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('43f5b004-719f-4f36-8ee3-d8cb46c5be83', '9441cc00-943f-4469-aef5-7fae7171b2b9', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('444e9a0e-b466-4bdb-919d-422bde185bf8', '00000000-0000-0000-0000-000000002001', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:37.979042', '2026-04-01T06:54:37.979042', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('446fd7ae-f7ff-4fa1-9564-65093318bbe8', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'a722cf91-835e-4616-8caf-f56a8451d70e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('448dcb6c-fb96-4d13-a5a6-d851c8d56279', '00000000-0000-0000-0000-000000000601', '3d7daef7-175b-4aba-959c-e22517a883e8', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('44a8524c-79ae-40bd-ba1f-e73f5aac3b73', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003012', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('44a98042-49df-4e78-b216-a2575d8d53d6', '00000000-0000-0000-0000-000000004012', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('45d8a95c-02b6-4e49-9ca5-7c7cd2830bc0', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006021', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('45f8b1b2-6fa7-4640-9089-e586977fc0e3', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001715', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('46203560-1590-474e-ae53-a0b51c3ec53c', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9033', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('471f8da8-18b5-4803-81b1-6897aeaae39d', '197ae046-a989-418f-99df-ec17310d73a4', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:41.75624', '2026-03-18T12:03:41.75624', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4746637f-beba-4470-8174-c80c2158aa93', '00000000-0000-0000-0000-000000004012', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('4797526a-1803-4de2-a704-173fa9b082ab', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:50.16683', '2026-04-01T06:54:50.16683', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('47e2e008-9e97-4d51-b162-0b533c17fcd2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006023', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('4880e97f-6d43-4255-9d28-1457224be800', '00000000-0000-0000-0000-000000000601', '08e2ccca-5d32-49e0-b4e5-062fb0177f81', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('493b2817-34e1-4830-93a4-37be33f326a7', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001712', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.600161', '2026-03-14T08:45:15.600161', NULL, NULL, NULL, NULL),
      ('49528cff-f300-4738-b44a-d8aa2884b51f', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000005025', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:30.990873', '2026-04-01T06:49:30.990873', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4965e77d-576d-42c8-98e5-4305ea5cec93', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9012', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('49735f94-8456-4a41-a713-657304daf0bd', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9022', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('49c7e3cc-8aa9-47e9-b68e-250133ad540c', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '03728caf-974b-4a70-941b-ddae4a319f4d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.478904', '2026-03-14T08:45:17.478904', NULL, NULL, NULL, NULL),
      ('4a77723a-f31b-4b9a-8b31-777245bcdb11', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003032', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:54:55.268839', '2026-04-01T06:55:03.556758', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T06:55:03.556758', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('4ac19f0c-0963-4ff1-8877-96beafee2e6f', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9043', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('4b1e9cba-8866-45ba-8681-bedeb430abbe', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9023', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('4b756402-7135-490e-bcc1-5478f39f5518', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000005024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:45:58.50033', '2026-04-01T06:45:58.50033', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4bb27e14-4fd9-4c58-8c3e-921143f6a90a', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003033', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:58:59.311501', '2026-04-01T15:58:59.311501', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4bd410c3-2721-4f04-a68e-83ad808f834e', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.55129', '2026-03-14T08:45:15.55129', NULL, NULL, NULL, NULL),
      ('4cbb87f6-c3e4-4ff8-932f-9bddf77e9ee6', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9021', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('4d2966ab-bf92-4be7-b649-f2084355b896', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003032', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:58:57.398346', '2026-04-01T15:58:57.398346', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4d580850-482b-46a8-b676-3896c0bfb768', '00000000-0000-0000-0000-000000004001', 'bc922db4-d4f5-4a10-83be-cc92b6af097a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:58:51.203315', '2026-04-01T15:58:51.203315', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4d833fd8-16c6-4995-ae35-09f9efda82b7', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001815', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('4e46dce9-5e46-4bfc-8a36-4d9ca275ba45', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:53.871386', '2026-04-01T06:54:53.871386', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4ed1c438-2ca9-4b57-acf6-0065f69a33aa', '00000000-0000-0000-0000-000000005105', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('4fc7ab9e-c80e-4be3-ab96-fbe4e0093b86', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:19.520062', '2026-04-01T06:49:19.520062', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('4fe7cec9-0a3a-45d1-936c-265c6f1d7e7a', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003041', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('502a45f8-4cfa-48b5-81ce-21f8717aeafa', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9042', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('5079f4c5-e010-48dd-ae94-fe9e27d3ffb5', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('51b2f36b-ba92-4c5e-a847-c6b17394c68e', '00000000-0000-0000-0000-000000004001', 'a59a9d62-3e75-47ae-b485-11b0d6c8669e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:05.061498', '2026-04-01T06:51:05.061498', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('527e6aca-99be-4291-89eb-ede7290fcdf2', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003013', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:14.797606', '2026-04-01T06:51:14.797606', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('52a1e0d5-b78a-4dfb-85cf-0b75edaa37a1', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000007020', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:52:10.690963', '2026-04-01T15:58:40.614219', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T15:58:40.614219', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('52ae626b-eec0-4807-ba1f-862037d9d436', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050b', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('52d16695-1a01-47a0-a98c-0facc42ff2a9', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003022', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('52d4e127-254b-42bc-8d35-edf16690972c', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000008901', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.810308', '2026-04-01T02:55:56.810308', NULL, NULL, NULL, NULL),
      ('53a0dd58-fc07-4377-bde4-481a74979556', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('53b07488-924a-4575-b4d6-dbfb0de743fa', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000008901', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.810308', '2026-04-01T02:55:56.810308', NULL, NULL, NULL, NULL),
      ('5412527b-9007-49dc-b3b8-3e21d2c898d5', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000006020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:54.571211', '2026-04-01T06:51:54.571211', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('544c7ec9-df7a-485c-b87f-58023cfe633d', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('54522269-b5e6-4e8b-be1e-1a1e94745265', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000512', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.251668', '2026-03-14T08:45:15.251668', NULL, NULL, NULL, NULL),
      ('54928708-210e-44ca-90cb-3bfdf9a95b25', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000514', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:00.277658', '2026-04-01T06:51:00.277658', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('54cf57a7-a747-4686-bbc8-85bf0c6af911', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001704', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.452905', '2026-03-14T08:45:15.452905', NULL, NULL, NULL, NULL),
      ('54f1ec96-8cbe-4efc-a18a-a34493bac428', '00000000-0000-0000-0000-000000000601', 'beb5a4fe-a758-4549-a5ee-8ebe1a516445', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T21:06:14.218265', '2026-03-30T21:06:14.218265', NULL, NULL, NULL, NULL),
      ('557ada15-a685-4199-b2a1-b8073ee533d5', '00000000-0000-0000-0000-000000004001', '6732df5a-2522-4447-bd3f-5c33ebd61696', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:07.508986', '2026-04-01T15:59:07.508986', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('5756b8f5-f3c6-47c6-ba4d-28238d04d8c4', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9022', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('57b4706e-2542-4ed0-8048-698844bfbe0b', '00000000-0000-0000-0000-000000004012', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.036277', '2026-03-17T06:38:33.036277', NULL, NULL, NULL, NULL),
      ('57edc87f-d7eb-4bc9-9eda-01cb03168e35', 'ddf8bcb6-6d66-472c-9b29-4c1c0e3a9d3f', '00000000-0000-0000-0000-000000000512', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-16T12:34:41.608231', '2026-03-16T12:34:46.486669', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-16T12:34:46.486669', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('58126db8-14e0-48ef-9113-2d107394e256', '513b472b-5ae1-45b8-91e3-a1402960b8eb', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-13T17:56:25.542936', '2026-03-13T17:56:27.022539', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', '2026-03-13T17:56:27.022539', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b'),
      ('58407018-cd0c-4e8e-8e5f-0b1919281d95', '00000000-0000-0000-0000-000000005100', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('585699d4-a7fe-44d6-b914-d1196e72c82b', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:58:55.999473', '2026-04-01T15:58:55.999473', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('58968dc4-5797-451a-970b-69a1eb64e95c', '00000000-0000-0000-0000-000000004013', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.06368', '2026-03-17T06:38:33.06368', NULL, NULL, NULL, NULL),
      ('590771dd-379c-401a-9efb-a0e4a8b094ad', '00000000-0000-0000-0000-000000000601', 'f70226ef-a1da-4e9c-8115-2388b7436e9a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T13:47:14.553559', '2026-03-18T13:47:14.553559', NULL, NULL, NULL, NULL),
      ('59821420-e5d8-453c-91ec-08b3079d2a56', 'd4152905-c44d-457b-bcdc-5be936af5ee2', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T05:28:12.68674', '2026-04-01T05:28:14.491889', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T05:28:14.491889', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('5a1c74fa-f8d5-4dc3-9e5e-ba5763888bd4', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9042', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('5a4c298f-4317-4926-a37c-c02f2baaa4ab', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'a14daddc-fb26-4f71-9e4c-fb60dc2a8c9a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('5a5187c9-4b43-4ab4-a679-c89205f40d92', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9042', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('5becdcdd-7705-408a-b0aa-4dbdbd47ecf1', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001814', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.187654', '2026-03-14T08:45:16.187654', NULL, NULL, NULL, NULL),
      ('5ca5d352-f256-4d0e-9913-72a38606b759', '00000000-0000-0000-0000-000000005102', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('5d10bfae-74be-464f-9a30-3ae8e942e521', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000007021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:28.592463', '2026-04-01T06:54:28.592463', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('5d805f47-833e-4304-91ca-6b0a5f59f1b8', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000000513', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-01T18:42:32.767057', '2026-04-01T18:42:32.767057', NULL, NULL, NULL, NULL),
      ('5dcb0fc7-87f9-4974-9f46-e1169e4d7d5d', '00000000-0000-0000-0000-000000004001', '10c9c4e1-dc73-4ddd-a86d-944875232bda', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:11.965057', '2026-04-01T06:51:11.965057', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('5e423a63-e6f6-4816-81cb-bc2e649edd8e', '00000000-0000-0000-0000-000000004001', '20dfe0b5-3990-4bb4-bc02-6f93b8673e36', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:08.102104', '2026-04-01T15:59:08.102104', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('5ecb844c-ec4d-43ca-8fed-905c1d3a319d', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003012', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:14.311088', '2026-04-01T06:51:14.311088', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('5fea0d25-a8e5-425b-a5aa-cf197229a9b2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000543', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('60c5719e-f460-4d67-96c5-7b83750608a8', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000505', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:43.848836', '2026-04-01T15:59:43.848836', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('60d7d27b-89bf-4683-aeab-dc91c96b3268', '00000000-0000-0000-0000-000000005102', '00000000-0000-0000-0000-000000009001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('60f557f2-b0d0-46cc-b07f-a18cd364d4ed', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('619e3e02-9679-4fad-910f-22abd0f47fa2', '00000000-0000-0000-0000-000000000601', '11582d29-77d4-49ed-b8a4-ef7a1c3c540f', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6244e7f1-cf4c-46b4-a923-d75e6ad50154', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9021', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('62c3a05d-cb7e-4176-bf61-650447b385e0', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'e6be427a-3f30-4fee-af22-cf8cc215da4e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.985261', '2026-03-14T08:45:16.985261', NULL, NULL, NULL, NULL),
      ('63b292d7-354a-4ac6-9958-24e0458aa5e5', '00000000-0000-0000-0000-000000000601', '01dfab3e-59e2-4e79-b514-d57b4de19c65', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('64680b2e-c73e-4290-8973-ed3a2e41f7cd', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000421', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-15T07:01:10.571982', '2026-03-15T07:01:10.571982', NULL, NULL, NULL, NULL),
      ('64d2d8e4-73d7-4e5f-a9d6-47656471d48b', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9023', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('65458be8-55c2-4df0-9f31-88cb738654d8', '00000000-0000-0000-0000-000000000601', '97bf4a0a-7afd-47cb-bc1f-974c8d7cb3d6', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-24T11:16:10.615645', '2026-03-24T11:16:10.615645', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('657a048d-76f1-4985-8342-bbc84fd4d15f', '197ae046-a989-418f-99df-ec17310d73a4', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:37.975858', '2026-03-18T12:03:37.975858', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('668efb2a-8c27-45b3-8a1d-1f9cf85d5b1c', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:32.438298', '2026-04-01T06:51:32.438298', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('672d0377-a35d-4629-a885-52ad68347b2e', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000552', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('675cfabe-4dde-4bb8-a9c9-5a43b5074e57', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('67842159-59c5-40f4-9d39-2d9bc86eeeec', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.796016', '2026-03-14T08:45:15.796016', NULL, NULL, NULL, NULL),
      ('67ccaf20-7063-4a8f-9825-28b93a84e2bc', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('67f67bd2-0526-4ac6-87da-119835fabb46', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001702', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('67fcb7ec-904a-4f80-9af6-7b656080bf3c', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9013', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('68c1d703-a3f6-4012-9399-4d1adc12fd29', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000008005', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('696276da-8119-4c2e-b9c1-194d850a48fb', '9441cc00-943f-4469-aef5-7fae7171b2b9', '03dba1fa-5bdf-45a6-aa0a-aa6117fe6285', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:16:43.585605', '2026-03-17T11:16:43.585605', NULL, NULL, NULL, NULL),
      ('69667c37-19f2-42cc-b033-eb011e75c4ab', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000521', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('69c42984-a96a-4bb0-8f62-00b8462b7c95', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000545', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('69f058d6-432d-4871-921e-bde56774f2b1', '00000000-0000-0000-0000-000000000601', '13fd0ba4-d66e-4223-8f0e-76b0ec002d39', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('6b775498-8698-4d7e-bf90-627e5b335a77', '00000000-0000-0000-0000-000000000601', 'a14daddc-fb26-4f71-9e4c-fb60dc2a8c9a', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6c241470-c5ed-4b20-95ec-20d2709089d8', '00000000-0000-0000-0000-000000005104', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('6c257cbc-cb01-48fe-8fb8-ab400f17ed5d', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000009001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('6c262983-ead5-4ae8-b838-934cc03fcf14', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('6cb4f709-6374-4ae8-b4dd-c42182ee0ccc', '00000000-0000-0000-0000-000000000601', '619affe6-e90d-4fac-a1bc-c6364653041a', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-24T11:24:24.306498', '2026-03-24T11:24:24.306498', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6d066ffa-c530-4929-a2dc-963ed58c61fb', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000511', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:06.960883', '2026-04-01T06:51:06.960883', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('6e1a6d6d-98d6-4d91-9b8c-3a9442e39aa6', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:45.93219', '2026-04-01T06:54:45.93219', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('6e8981f9-dd4b-4f67-9bd7-848d155f7b3d', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('6e9693ef-fd88-4c36-b054-f48b64af4b32', '00000000-0000-0000-0000-000000004001', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:52:04.32813', '2026-04-01T06:52:04.32813', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('6ebaaccb-30aa-479e-b9fa-c443ef404e3e', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000006022', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6ec10388-d26b-4c0d-a1fd-e6cd6cc438f2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('6f297ca0-dfcf-481c-bad4-8277dd1770f2', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000009001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('6f2bbec6-b391-4229-afb2-9152fb2cf8c9', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000502', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.454011', '2026-03-14T08:45:14.454011', NULL, NULL, NULL, NULL),
      ('6f339861-9de2-443c-b011-eca088c1f9f5', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001819', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('6f38f20d-d182-4589-b9e9-a226ed023652', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9032', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('6ff668e1-c861-4603-af65-5425e0bd20b2', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001703', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('71e80bd6-59b1-4114-ac1d-ccb96a538576', '9a2f8bd7-f635-4cfe-9bad-8f640f50fe74', '18e15e8f-21d4-4206-aac9-a7d116129277', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:02:32.063695', '2026-03-18T12:02:32.063695', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', NULL, NULL),
      ('723ae2e0-8c1b-4cf1-97f7-ad18db8e229c', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008006', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('725c0583-71d7-4b51-a1ab-dd59ac17be5f', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003023', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7279edb0-f2f7-4267-95c2-a8aa14a33f24', '00000000-0000-0000-0000-000000004001', 'b536b3c5-d955-441b-a439-4a57243b049a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:12.601876', '2026-04-01T06:51:12.601876', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('73afb666-4dff-4438-b4e4-4ff17756f67d', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('73e4d186-bc65-4f03-a71e-0e4780eea316', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003062', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('7447099f-59cb-428a-a0fa-35864dbf29b0', '00000000-0000-0000-0000-000000004001', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:52:03.465486', '2026-04-01T06:52:03.465486', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('74b06dbc-9899-43ce-bc2b-d3f8ab322f38', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('74b8334f-ee3f-473e-a7fa-98941b6b8ecd', '00000000-0000-0000-0000-000000004001', '418d753c-aa97-4551-abb6-b703d54f8f96', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:39.829791', '2026-04-01T06:49:39.829791', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('74eb969e-5445-45a7-8453-b44f388d4879', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000544', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('74f8ceba-4abf-4e94-9216-d5bbff83c3b5', '00000000-0000-0000-0000-000000005103', '00000000-0000-0000-0000-000000009001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('754c8677-0189-432c-bf19-400264862811', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:47:24.691755', '2026-04-01T06:47:24.691755', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('75c4b463-e98f-42d1-8895-d6b16d41e626', '00000000-0000-0000-0000-000000004001', '619affe6-e90d-4fac-a1bc-c6364653041a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:03.320047', '2026-04-01T15:59:03.320047', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('76882253-5961-41b6-8bf6-1db8f7eefa23', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003012', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('76b92c1f-b159-40ba-8cc2-0afbbe77ba5a', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000009003', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:12.01748', '2026-04-01T15:59:12.01748', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('76dbdfb1-fd03-41c8-8f07-7a8a90c2a581', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.892223', '2026-03-14T08:45:15.892223', NULL, NULL, NULL, NULL),
      ('7791f6b2-13a6-4c0d-9dc0-644a0498575f', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000521', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.282463', '2026-03-14T08:45:17.282463', NULL, NULL, NULL, NULL),
      ('77f52b7b-6768-4773-a226-2c40bcfa6e54', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003053', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7815397e-018d-4642-b5be-88858bf80b97', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000503', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('78e936f8-e038-4369-8ce2-49117b180ac5', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9021', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('79720277-b3ef-4057-b561-4ccd9567ed37', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000505', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.610297', '2026-03-14T08:45:14.610297', NULL, NULL, NULL, NULL),
      ('79cf7614-ea4c-4e4a-903b-598680d3f4e3', '9441cc00-943f-4469-aef5-7fae7171b2b9', '55963948-87ca-47e7-9de7-ddd7f3dc675f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:16:43.585605', '2026-03-17T11:16:43.585605', NULL, NULL, NULL, NULL),
      ('7a491ede-b5f0-44aa-9b6c-88a1501df3f6', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005022', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7a6d3ecf-2773-4417-a9a4-7f5830b89524', '00000000-0000-0000-0000-000000000601', '82ea4262-c4f8-4ccb-aa94-466fc3fde999', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('7adebe3a-2493-400c-aea6-fa61a2661196', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000507', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('7b1d3b7b-e839-45a7-908f-f33a2b76442a', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('7bdb09cc-e1c1-4fad-bad6-7b6239a3e2b2', '00000000-0000-0000-0000-000000005100', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('7be0cbc5-07d9-43ba-a7c5-a3b148042e22', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005023', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7d1c50ce-97ea-42f8-b252-4e10e44e5a73', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9011', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('7d588d82-00a5-4b91-88c6-9a4c6adb419f', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003022', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:54:51.272683', '2026-04-01T06:55:04.306722', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T06:55:04.306722', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('7d629857-92b0-4441-a042-de1924257648', '00000000-0000-0000-0000-000000002001', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('7d9ac879-2082-403c-a8b4-1e3dcbf95034', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9024', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('7db00d21-20f2-4612-9590-e0e9ffc154d5', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000005022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:29.310431', '2026-04-01T06:49:29.310431', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('7dc53187-6299-457f-aa6b-a5445f4f8c57', '00000000-0000-0000-0000-000000004001', '5e57eaaf-2427-467a-8170-b0c605c5c61d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:37.015448', '2026-04-01T06:49:37.015448', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('7dc55cf7-da6b-40e7-a9d0-fafeeb19223d', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000508', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('7e08ffdc-c29f-4579-a283-78db630ce7bc', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000007023', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:52:12.540227', '2026-04-01T15:58:42.601091', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T15:58:42.601091', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('7e17c3cb-ac38-415e-8900-2ddf66a69123', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003072', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-17T12:39:05.58981', '2026-03-17T12:39:06.919062', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-03-17T12:39:06.919062', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('7e1ffa4d-6511-4c0d-8ca8-aafd405ed751', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000008902', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.846896', '2026-04-01T02:55:56.846896', NULL, NULL, NULL, NULL),
      ('7e4a8ac1-ee71-44e8-9736-ecd15f50c828', '197ae046-a989-418f-99df-ec17310d73a4', '74f334d2-f078-4752-a2fd-2f4af1e360cf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:43.336014', '2026-03-18T12:03:43.336014', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('7e9bba86-ed66-4090-b12e-739d006c60f2', '00000000-0000-0000-0000-000000005105', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('7ea8e4db-10df-47b7-aba7-0c854e27fa4f', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7eb359a2-f82d-4b0e-9f42-e1ed262e9a89', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003041', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('7f2a22bf-ea6b-4811-8085-028b357fa4dd', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('7f50cf8d-4f25-479e-b8b1-0c881cf6fa7f', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('8030e6ab-3959-4b27-9e3c-d04489f9eca7', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000009001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:11.026978', '2026-04-01T15:59:11.026978', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('81b2ac6a-c72b-4bf4-a071-d7e4a22acd3f', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000505', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('81dd4bfb-5365-4357-a0b2-a5c388e392b1', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003053', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('8295299d-0b7d-4114-8818-dff4176bf00a', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:46.743725', '2026-04-01T06:54:46.743725', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('82b388d9-01e6-423d-9bb9-17afadcade7f', '00000000-0000-0000-0000-000000004001', '4de88a99-cf77-4391-b8c5-97d3dcb9d7f6', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:37.017046', '2026-04-01T06:49:37.017046', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('82b620f6-690f-4565-960b-c1a720df6f99', '00000000-0000-0000-0000-000000000601', 'fbee9a75-4360-4a59-8f02-130491ce81af', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T21:06:14.218265', '2026-03-30T21:06:14.218265', NULL, NULL, NULL, NULL),
      ('82f26804-c5b8-49d8-b541-c0f80b011b9c', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000007020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:26.851992', '2026-04-01T06:54:26.851992', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('8374fdf1-e171-4ec2-9c93-5c556150928b', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('83e9a2d2-2850-420f-aaea-1497c06ec1f4', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('8414d99a-6da5-4245-8a71-e612dc15b0bc', '00000000-0000-0000-0000-000000000601', 'a59a9d62-3e75-47ae-b485-11b0d6c8669e', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('855b7ef4-5d19-4861-86ad-3afd4067a3d9', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:25.905773', '2026-04-01T06:49:25.905773', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('8563bf1f-1600-4258-8f30-c2e432ba0569', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000506', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('85a6cc66-adee-44b6-935d-8790027e1c78', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008003', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:22.483859', '2026-04-01T06:49:22.483859', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('8619ac6a-e0c0-4018-a391-620e4a987e77', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000510', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:06.312162', '2026-04-01T06:51:06.312162', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('863639f8-9d7b-497b-a270-e8b84c05dfba', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('8688bd72-31a1-4d1d-8624-63fe96373154', '9a2f8bd7-f635-4cfe-9bad-8f640f50fe74', '00000000-0000-0000-0000-000000000508', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:02:28.684511', '2026-03-18T12:02:28.684511', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', NULL, NULL),
      ('86bf2bf4-6a3e-4a55-9ecc-f1852a5e49c3', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-00000000050f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:03.881809', '2026-04-01T06:51:03.881809', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('86f6829c-aaf6-4453-846e-22a7198f1531', '00000000-0000-0000-0000-000000004001', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('872ea3c8-720e-4096-bfed-26f0c00f1c43', '00000000-0000-0000-0000-000000000601', '03728caf-974b-4a70-941b-ddae4a319f4d', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('874c8d29-f9c0-4a5d-a0a7-48a46261490d', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003053', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:21.846206', '2026-04-01T06:49:21.846206', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('87aae545-7bfd-4f96-8c5c-5a429ebbd2ec', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000504', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('87ae4314-e151-424d-9c7f-063080f03932', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('8819bc8c-7722-4ec7-85e9-1cff695de852', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '0abe68aa-b4ac-4335-8189-24ab0cb4e460', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.378744', '2026-03-14T08:45:17.378744', NULL, NULL, NULL, NULL),
      ('8946554c-4374-4e63-a1f5-4f19fd8f1ee8', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001818', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('895106d0-8487-4957-a95a-51cecf559469', '00000000-0000-0000-0000-000000005105', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('8a0b6f43-b0f1-49a9-97ed-28985e24d933', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003043', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('8b3523b4-7031-4d83-b50c-e3c3d874acd3', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9024', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('8bff065c-6950-4d6a-be08-5ff829cb4336', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003051', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:47:25.805787', '2026-04-01T06:48:04.900844', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T06:48:04.900844', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('8c7f02f1-b6e3-47f1-9871-7a3309644d63', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008002', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('8cccd01f-fa17-4f43-afa9-aaa7f6f897cd', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003011', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:17.378815', '2026-04-01T06:51:17.378815', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('8d981d02-29da-4c71-9c4c-79858c89d8fd', '00000000-0000-0000-0000-000000004001', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:52:03.159865', '2026-04-01T06:52:03.159865', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('8f029e1b-5e17-44de-9092-8345ed83ec70', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000503', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('8f487648-3672-447e-b8b4-d638c7844d19', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'ebbeba6f-b172-4038-a2a3-384060a1ec43', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.54175', '2026-03-14T08:45:16.54175', NULL, NULL, NULL, NULL),
      ('8f48ab68-fea8-4ce7-92ca-a42043480c2d', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '18e15e8f-21d4-4206-aac9-a7d116129277', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.639546', '2026-03-14T08:45:16.639546', NULL, NULL, NULL, NULL),
      ('8f6665d1-6b87-4e30-b57b-e75dce789fc3', '00000000-0000-0000-0000-000000004001', '97bf4a0a-7afd-47cb-bc1f-974c8d7cb3d6', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:43.51175', '2026-04-01T15:59:43.51175', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('9038b614-5ece-4ad2-932a-eb6e50adc17c', '00000000-0000-0000-0000-000000005100', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('908ec89d-b790-447b-853a-64f6b745ed06', '00000000-0000-0000-0000-000000004012', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('90fc044e-0ff6-4f1f-951a-5ecab4decf8c', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008007', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:08.61849', '2026-04-01T15:59:08.61849', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('9129ef11-382d-4d94-9093-43e6b506f632', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '91dd81b2-8d4a-41ac-94a5-1106d459a0be', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.780541', '2026-03-14T08:45:17.780541', NULL, NULL, NULL, NULL),
      ('91390e3d-bcd9-49d7-a7a4-8aa3aeace828', '00000000-0000-0000-0000-000000002001', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:38.531527', '2026-04-01T06:54:38.531527', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('914aa655-c018-423f-83f6-e897ecda2b77', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('914c63aa-e79e-45ec-90be-ab17f6c62fb3', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:33.807079', '2026-04-01T06:51:33.807079', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('91588361-7ef4-44f4-b808-a339b58ff1a8', '9441cc00-943f-4469-aef5-7fae7171b2b9', '4db67994-51ad-4dde-93b1-3abd1842da4d', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('928eb843-b4c0-470e-a12a-74736de4142b', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000501', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('92b253b6-8003-4b20-8e67-c43d3012f0b4', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003053', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('92db178e-da8d-47bd-8aee-9f0c62036c5a', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9041', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('9379a6e4-02d9-42d6-8ec8-79b364cbe311', '00000000-0000-0000-0000-000000002001', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('93cb6780-2f71-4982-ab20-321653786e19', '00000000-0000-0000-0000-000000000601', '73f7950d-7163-4467-837d-b6907dd0abcf', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('93d980c0-f96a-4545-83b1-f1fc9c457fb4', '9441cc00-943f-4469-aef5-7fae7171b2b9', '10c9c4e1-dc73-4ddd-a86d-944875232bda', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:16:43.585605', '2026-03-17T11:16:43.585605', NULL, NULL, NULL, NULL),
      ('943570ee-bb22-48e8-8e8a-8b69fb45cf58', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001816', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.291281', '2026-03-14T08:45:16.291281', NULL, NULL, NULL, NULL),
      ('943915e6-accd-4234-a677-2103ad1be01c', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000007021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:17:34.637994', '2026-03-22T15:17:34.637994', NULL, NULL, NULL, NULL),
      ('94d808c0-7e3c-4486-85db-c998aeb8c21a', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003052', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('950759e4-c435-4979-91b6-8b69edb13c2f', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9011', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('95303513-713e-4212-adfa-b8f6634f3b11', '9441cc00-943f-4469-aef5-7fae7171b2b9', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('959e4541-f8c0-40fd-b1dc-8f5efe302aea', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('961dd377-496a-4134-bfe0-e91b3d0b0d8c', '00000000-0000-0000-0000-000000000601', '91dd81b2-8d4a-41ac-94a5-1106d459a0be', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('96a17d26-4226-414a-827a-1c0dec81f94a', 'e6a1534a-6e9e-49e8-8452-73daf270db13', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-16T10:42:09.281079', '2026-03-16T10:42:11.897059', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', '2026-03-16T10:42:11.897059', '819f347c-e619-4a43-8755-2c80e5fa572e'),
      ('96c9b108-d195-4357-95a5-d4761efe5d54', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003060', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('97c2c646-6da9-4a87-8eaa-5b4308193cb5', '00000000-0000-0000-0000-000000004001', 'a722cf91-835e-4616-8caf-f56a8451d70e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('98deb589-4a33-428a-befc-978341c8d8d2', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('98f488bb-a6e3-4587-a46f-790f29502019', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003032', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('990edc8a-8796-4b46-aee3-98955809fc4a', '00000000-0000-0000-0000-000000000601', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('9a058b86-a8c7-4453-9b5e-1b9576539682', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000516', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:01.534863', '2026-04-01T06:51:01.534863', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('9a64c1a9-9420-4eb9-9c3f-053932364415', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('9acce471-5023-48df-8450-b59be4556d4d', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('9adec155-4828-4273-987b-f1d52e787dc0', '00000000-0000-0000-0000-000000005102', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('9afe3b0f-dac5-4109-b921-914140dc394b', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003031', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:54.576862', '2026-04-01T06:54:54.576862', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('9b4b939a-f2d9-40e3-b053-0cfbf866dc22', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('9bafc7a3-55fb-42fb-b849-7ab0126511eb', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000513', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.032648', '2026-03-14T08:45:17.032648', NULL, NULL, NULL, NULL),
      ('9c8ab479-4f61-4442-82cb-2a8ef019fb91', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9043', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('9d2803e7-48c8-4f10-be0c-98b1020b65d9', '00000000-0000-0000-0000-000000004001', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('9d347166-c609-4d62-a5c8-a32873a75121', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000506', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:45.199272', '2026-04-01T15:59:45.199272', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('9d7917d1-0ca8-48de-968c-9755e09ff44e', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9012', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('9f4653da-4ff9-42ff-b614-0c5d47977d56', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001705', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('9f92fcb0-5c7a-4ec6-9c3a-9fc5f7162c5f', '00000000-0000-0000-0000-000000005103', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('a0063d32-6aba-4ede-b1d6-c33e357c10c0', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('a0748be9-5baa-4bd5-bbbf-ac4bd2dabeec', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000502', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('a0f4ad05-ae03-4f4e-b01f-a9aabc91b547', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'ee241772-1028-47fe-813c-04377db03e20', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.78465', '2026-03-14T08:45:16.78465', NULL, NULL, NULL, NULL),
      ('a117958e-20df-4f61-af89-414462418da1', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000009002', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('a1533a21-6a33-4264-8af7-5a6d7171e209', '9196f27b-03f9-4cd8-b848-72f0390b16d1', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-13T17:36:39.901092', '2026-03-13T17:36:41.079509', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', '2026-03-13T17:36:41.079509', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b'),
      ('a1939e9a-cb0f-4b29-9a24-1d423f37877b', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000506', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('a1d90362-bc6b-457b-9a53-f5c31e5809f8', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000006022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:52:00.290887', '2026-04-01T06:52:00.290887', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('a1f7e249-4402-4d91-9035-946146c704e2', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008001', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('a1f96d37-bbc4-4049-a98b-48a407b49890', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003031', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('a25d89aa-ec29-4583-84f5-e571d5010e62', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000005021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:28.977698', '2026-04-01T06:49:28.977698', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('a30c8b9d-feb0-4005-8ece-4058210ff2c1', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9012', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('a34fc630-87c6-4a44-bd54-6ad55ceb2977', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9031', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('a3c12ba4-3263-4195-809f-860b879e265b', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000513', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:50:59.603152', '2026-04-01T06:50:59.603152', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('a449e96c-74e2-4045-b295-a2aac3a34d99', '00000000-0000-0000-0000-000000000601', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('a4bd82c1-000c-4162-8d43-6495f75ce91d', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001713', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('a50c622d-102b-4c56-8468-04ee4558e7d2', '9ecdb7d5-c229-477f-a659-b5ac3c995aa6', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:44:18.126232', '2026-04-01T06:44:20.425732', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T06:44:20.425732', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('a5f5f544-2deb-4831-a623-ac376373c6fc', '00000000-0000-0000-0000-000000000601', '0abe68aa-b4ac-4335-8189-24ab0cb4e460', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('a6ab0a61-b31b-40cf-a7ed-1f4c2bf146cf', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001816', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('a6c30d4d-f378-466a-9809-73ad0fb4df1e', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000513', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:48:24.457105', '2026-04-01T06:48:28.701692', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T06:48:28.701692', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('a6cb755f-01b2-4253-b237-592edc019876', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003013', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('a774bd93-3cdf-4b9f-893a-eb09fddfc36b', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '13fd0ba4-d66e-4223-8f0e-76b0ec002d39', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.430391', '2026-03-14T08:45:17.430391', NULL, NULL, NULL, NULL),
      ('a796ab17-ed23-43eb-a2e2-ea1fc1be55dc', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003022', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('a7c84249-a914-440b-820f-175502a6324d', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003041', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:47:19.521237', '2026-04-01T06:47:19.521237', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('a81662e5-f60c-4016-a030-6a66f4e3ef9b', '00000000-0000-0000-0000-000000004001', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:06.99934', '2026-04-01T15:59:06.99934', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('a85a6aaf-8509-4e0a-8b80-b134bf6b1ab3', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000520', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('a8c57297-365f-43f3-9613-a0abbc2f10d0', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000422', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-15T07:01:10.571982', '2026-03-15T07:01:10.571982', NULL, NULL, NULL, NULL),
      ('a8f9c744-e1c8-4a46-9f7a-3f07c96fe623', '9441cc00-943f-4469-aef5-7fae7171b2b9', '6732df5a-2522-4447-bd3f-5c33ebd61696', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('a925ad00-d7fb-497a-a544-dfcc381c457b', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000007021', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:52:11.391377', '2026-04-01T15:58:41.299626', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T15:58:41.299626', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('aa5efc06-dbd2-47b6-95b1-3905ff1a491f', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003011', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:55:13.842713', '2026-04-01T06:55:13.842713', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('abd8bfc2-df26-4673-bb64-ac73aebde638', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003052', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('acb03b9c-ae4e-41e1-b382-a8a0680d467e', '9441cc00-943f-4469-aef5-7fae7171b2b9', '4de88a99-cf77-4391-b8c5-97d3dcb9d7f6', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T14:23:40.475695', '2026-03-18T14:23:40.475695', NULL, NULL, NULL, NULL),
      ('ad097225-838e-47c9-95aa-6e5778c15cc3', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000503', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:58:52.107198', '2026-04-01T15:58:52.107198', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('adb05571-982d-4c95-8d18-232a6851c118', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('ae554d6d-4953-46f5-98bd-cf940a30459f', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000181a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('aeb15a9e-fa4c-4bd9-a4d8-88f5f04ab6d5', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9032', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('aeeb9ea6-c71f-4ccb-88e6-417aae0d7f76', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('af2f65e2-e9be-4057-a759-845a6106367b', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003031', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:58:56.432574', '2026-04-01T15:58:56.432574', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('af35f057-6eee-4d9e-b5be-dc54292bf257', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('af78730a-75b3-4188-99cc-577966d38211', '00000000-0000-0000-0000-000000005103', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('afe10be2-ae2f-424b-931e-a14719d42168', '00000000-0000-0000-0000-000000000601', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b1337512-22d3-4d6d-af3a-6d9f865f8cb6', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003021', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b166b57f-5aff-43aa-864e-b5539ad4594a', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '01dfab3e-59e2-4e79-b514-d57b4de19c65', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.330141', '2026-03-14T08:45:17.330141', NULL, NULL, NULL, NULL),
      ('b1bd6677-5ea9-4a24-ac22-8adff1605601', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000551', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:00.002504', '2026-04-01T15:59:00.002504', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('b24c0383-400a-4a89-843a-3bddbee4e9e0', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000507', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.710907', '2026-03-14T08:45:14.710907', NULL, NULL, NULL, NULL),
      ('b32a7c29-cae3-4ea8-bf59-925ac296af4b', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '3d7daef7-175b-4aba-959c-e22517a883e8', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.737038', '2026-03-14T08:45:16.737038', NULL, NULL, NULL, NULL),
      ('b3b24228-9a7a-4152-8104-2a8964441af7', '00000000-0000-0000-0000-000000000601', '18e15e8f-21d4-4206-aac9-a7d116129277', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b3e47361-bb4d-4248-91bf-0e78a6f202dc', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('b46bd9f2-c7d4-4486-b3cf-cc133754b433', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000501', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.377651', '2026-03-14T08:45:14.377651', NULL, NULL, NULL, NULL),
      ('b4cf536c-75f6-450e-a604-e74d2c7ab01e', '00000000-0000-0000-0000-000000004011', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('b5129834-da24-445e-aeda-db4075718270', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001713', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.648406', '2026-03-14T08:45:15.648406', NULL, NULL, NULL, NULL),
      ('b53e6625-3708-429a-903d-3c1e836ac581', '00000000-0000-0000-0000-000000004001', 'ee241772-1028-47fe-813c-04377db03e20', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:04.280782', '2026-04-01T06:51:04.280782', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('b5819905-62b4-4d5a-b0ae-bac386910f4f', '00000000-0000-0000-0000-000000000601', '7f9057c2-d375-4517-98ec-84956a68343b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T13:56:12.151696', '2026-03-16T13:56:12.151696', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('b5d35711-1d5c-40ed-9d43-a496e65e869f', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000008002', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('b5e19ece-eead-486b-8744-165ea6a51978', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003031', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b66bf781-c7bb-4d89-8e1d-15d01f4dd731', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000553', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('b6996589-393a-4e40-8721-3d7599513eda', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000008001', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('b6f9589e-230f-4fa0-9579-e0700b4761fa', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '64bf9716-617e-426f-b9ca-80b1cbec466c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.688113', '2026-03-14T08:45:16.688113', NULL, NULL, NULL, NULL),
      ('b76a952d-63fc-49b5-9566-c8263b1fc4c8', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003051', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('b7873175-fa84-4327-8e54-71d5b3dcef71', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003053', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:47:28.116559', '2026-04-01T06:47:29.887639', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T06:47:29.887639', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('b79fbbaf-8b83-4945-b5d6-7a80342eb1d9', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'edcd40a1-d791-4ca0-9955-4766088115f1', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('b7ad8973-79c8-4675-9fdc-5ca0fbe30a43', '00000000-0000-0000-0000-000000005105', 'c47e6c29-5556-4b4c-a1b2-14a02fcec5de', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('b8648846-3b9f-4575-b179-d1c29cd3933f', '00000000-0000-0000-0000-000000000601', 'b536b3c5-d955-441b-a439-4a57243b049a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T11:18:16.315393', '2026-03-17T11:18:16.315393', NULL, NULL, NULL, NULL),
      ('b88c4c56-2f65-4cf5-b6c8-85ef45e01f30', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000007022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:17:34.637994', '2026-03-22T15:17:34.637994', NULL, NULL, NULL, NULL),
      ('b9c081bc-08cf-4150-a831-3ee6b270e9b9', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008002', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:25.017212', '2026-04-01T06:49:25.017212', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('baa39e27-2c01-45be-add4-88bf1e582889', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000554', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('bb0c8503-2841-44b0-9c7f-a603b4efe067', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003021', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('bc19bafe-cc6f-41e4-9354-b217618c24c5', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008901', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.810308', '2026-04-01T02:55:56.810308', NULL, NULL, NULL, NULL),
      ('bc26b6fd-71b2-4c88-9b65-cca1a1f1aa4f', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '82ea4262-c4f8-4ccb-aa94-466fc3fde999', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.527659', '2026-03-14T08:45:17.527659', NULL, NULL, NULL, NULL),
      ('bc5e819c-2e1d-4e30-93a8-21e3b376b014', '00000000-0000-0000-0000-000000004001', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('bc8b4b20-497a-4f17-883b-28e397832393', '00000000-0000-0000-0000-000000004001', 'f70226ef-a1da-4e9c-8115-2388b7436e9a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:15.56352', '2026-04-01T06:51:15.56352', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('bd38bff6-0169-4641-9eb2-644281574b54', '00000000-0000-0000-0000-000000000601', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('bdb234a3-912c-48c7-8273-0e50e9a9e07d', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001817', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.342898', '2026-03-14T08:45:16.342898', NULL, NULL, NULL, NULL),
      ('be82b21d-26bb-43f9-8fbd-2eb25fe3c5a9', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000504', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.555031', '2026-03-14T08:45:14.555031', NULL, NULL, NULL, NULL),
      ('bf110d86-2586-4bc7-b594-e041d5002e6a', '9a2f8bd7-f635-4cfe-9bad-8f640f50fe74', '3d7daef7-175b-4aba-959c-e22517a883e8', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:02:37.476175', '2026-03-18T12:02:37.476175', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', '3b4c22e8-3a85-4dad-82a6-989e5c8b2b1f', NULL, NULL),
      ('bfb9527a-2141-4104-b0dc-961f58516e40', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-00000000050c', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('bfc1be43-8504-47d9-95f6-a777b5a48d8e', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000520', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.23547', '2026-03-14T08:45:17.23547', NULL, NULL, NULL, NULL),
      ('c0b542e9-0c3b-41e7-8ac3-5e53679f44ff', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:27.718515', '2026-04-01T06:51:27.718515', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('c114d56d-c647-4a05-9cbb-18badc0e571a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000502', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('c118b9d7-3633-45e1-8d1f-2fbad2129d96', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:38:38.414691', '2026-03-17T15:38:38.414691', NULL, NULL, NULL, NULL),
      ('c1e3757c-45ac-437d-8b4e-1ddc3dad0c4d', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003041', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('c2454cb6-add4-4947-906d-2f23b5f917d3', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003043', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('c30306ac-a15a-4d45-8b48-cb7e8baf3613', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000181a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.489402', '2026-03-14T08:45:16.489402', NULL, NULL, NULL, NULL),
      ('c337b187-0139-48f0-a48d-c8291c40c46c', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003051', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('c344347d-f5b8-4214-b34a-9663b2ebddb6', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000006024', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:52:01.269024', '2026-04-01T06:52:01.269024', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('c43125b5-e96c-4b26-a7fb-4664d0c11026', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001811', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('c51cc84d-94f6-438b-9506-66e170c61e83', '00000000-0000-0000-0000-000000000601', 'c20bad33-1a4a-46fc-9157-9e7ecab76ee4', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-24T11:16:59.147417', '2026-03-24T11:16:59.147417', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('c5e6bab7-e9a0-4227-a550-ba9e229b1cd0', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9033', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('c60d0f40-8577-4224-bdb8-9d6453fb0dfc', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'a14daddc-fb26-4f71-9e4c-fb60dc2a8c9a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.884653', '2026-03-14T08:45:16.884653', NULL, NULL, NULL, NULL),
      ('c61541c9-78a9-4f44-88d6-b4d4dd9cfa87', '00000000-0000-0000-0000-000000004001', 'c20bad33-1a4a-46fc-9157-9e7ecab76ee4', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:44.896966', '2026-04-01T15:59:44.896966', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('c6431346-95bb-4475-b130-4bad724ca133', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000003053', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('c6562c49-5ce6-40ce-9b3f-7584f38fa0d6', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008007', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('c696ad9b-683d-40f0-bae0-35fe1960eb52', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003022', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:28.831238', '2026-04-01T06:51:28.831238', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('c733b6aa-2327-40fe-b1e7-7023237623c1', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:50.103224', '2026-04-01T06:51:50.103224', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('c77dc381-81ba-4550-a472-618273d4c8c1', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('c7d5de05-f251-434e-8ba6-177caa8d7978', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000007022', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-04-01T06:52:11.883689', '2026-04-01T15:58:41.899709', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', '2026-04-01T15:58:41.899709', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('c7f73f41-0d50-4a70-91ad-512e347c5638', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '11582d29-77d4-49ed-b8a4-ef7a1c3c540f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.590111', '2026-03-14T08:45:16.590111', NULL, NULL, NULL, NULL),
      ('c800848f-f956-4fa4-a381-4d71e224191e', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008902', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.846896', '2026-04-01T02:55:56.846896', NULL, NULL, NULL, NULL),
      ('c8c49ac2-47e9-4fde-9f7c-4ec875e46953', '00000000-0000-0000-0000-000000000601', 'ec07be31-5506-4a09-8f9f-7d3d402f9031', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('c90172f7-873d-481d-aaf6-e5e0e8fe4035', '00000000-0000-0000-0000-000000000601', 'ebbeba6f-b172-4038-a2a3-384060a1ec43', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('c9191d1f-920a-4d82-b4f2-0d3cba72532a', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001701', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('c9487ad7-4c9c-419d-adb2-9cc7d57e44b9', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.843525', '2026-03-14T08:45:15.843525', NULL, NULL, NULL, NULL),
      ('c9b8fbc8-efd0-4fde-8ae3-f651b87804cd', '00000000-0000-0000-0000-000000004001', 'ba30a1c3-d974-4d81-8f2d-28bfccb4bf6b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:39.124836', '2026-04-01T06:49:39.124836', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('cb779bd7-bb99-4117-92c2-d93caa8eacbe', '00000000-0000-0000-0000-000000005102', '00000000-0000-0000-0000-000000003052', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('cba041ee-bbb8-452f-bf2f-b22eef577adc', '00000000-0000-0000-0000-000000000601', 'dc8b435a-6aea-432e-8504-191a78bf53dc', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('ccc4cee8-007e-4c02-8ff5-26eef34c606e', '00000000-0000-0000-0000-000000000601', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('cd622f5c-ca67-4136-a2bd-47898faa429f', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000544', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.10148', '2026-03-17T07:49:17.10148', NULL, NULL, NULL, NULL),
      ('cd84343c-1163-42fc-98c0-7172dea00734', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000501', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:58:53.602812', '2026-04-01T15:58:53.602812', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('ceb375b2-2864-47a0-9392-4a1994821f7c', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('cee38c1a-6a1d-4c72-bb66-ed0d0dfa8c9e', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008005', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('cf7e6dc9-3f0e-49f5-9b94-2ff582c42ab1', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'd0f29e6c-218e-4deb-8d6d-956db7fb12bf', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('cf8cea14-407e-446e-bfc6-b2706c390824', '00000000-0000-0000-0000-000000005104', '7e356f13-71b2-4447-95e5-b1d9284f26e1', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('d072b93e-c42d-4c7d-b96b-4f8371c4ecb8', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001815', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.239166', '2026-03-14T08:45:16.239166', NULL, NULL, NULL, NULL),
      ('d08990d3-43a8-436a-8233-8cd0fd11a84e', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003042', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('d1392412-9e3a-499c-8c28-987238e908a9', '6b4c9d58-e91b-4fec-9118-49f792f2e69a', '4c0e311e-01ef-487a-9136-b0be8bf85412', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('d24dc813-25b5-4ddf-a473-6a0aef406f75', '00000000-0000-0000-0000-000000004012', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.036277', '2026-03-17T06:38:33.036277', NULL, NULL, NULL, NULL),
      ('d2bd6701-0a7b-4c0b-835d-bd3e9cd94b19', '00000000-0000-0000-0000-000000004013', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('d3eaf92c-205f-458d-a073-a75eac89ddf6', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:32.767', '2026-04-01T06:49:32.767', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('d3f5dc69-b26c-46fa-ad38-24925a020112', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001715', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.747254', '2026-03-14T08:45:15.747254', NULL, NULL, NULL, NULL),
      ('d440116b-7745-4234-aaaf-24c18a2ba1c7', '00000000-0000-0000-0000-000000000601', '418d753c-aa97-4551-abb6-b703d54f8f96', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-24T11:17:26.475614', '2026-03-24T11:17:26.475614', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('d469ab75-2d37-4605-9c0f-14a146551ef4', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003071', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:51.14382', '2026-04-01T06:51:51.14382', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('d4a6fdd6-400f-459b-bd9f-dbfbb8ec7f2c', '9441cc00-943f-4469-aef5-7fae7171b2b9', '5e57eaaf-2427-467a-8170-b0c605c5c61d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T14:23:40.475695', '2026-03-18T14:23:40.475695', NULL, NULL, NULL, NULL),
      ('d4ff129a-ae5c-48fe-bc01-a95526af0de9', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000511', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('d574390c-8866-4eef-b358-12fe13ab0336', '9441cc00-943f-4469-aef5-7fae7171b2b9', '7764d393-4513-4068-a119-d30230b1da5c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('d59683ed-99f1-4d98-b902-71e5a448aa54', '9441cc00-943f-4469-aef5-7fae7171b2b9', '3d7daef7-175b-4aba-959c-e22517a883e8', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('d5d64ce7-7a17-4816-b857-50e870074611', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9031', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('d63d5616-8c03-4515-856c-d59b6c463fda', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003032', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('d6bee11e-d6ec-4128-84eb-8bbe0ac44463', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001714', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('d6f3af89-8cbf-483d-b089-bf4451b9d1c7', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000008003', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('d77c1c44-44d4-449c-8b9a-1c683e24de6b', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.003882', '2026-03-14T08:45:15.003882', NULL, NULL, NULL, NULL),
      ('d87a6b59-f872-4a31-b6ca-66c2db54d3bf', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000508', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.759542', '2026-03-14T08:45:14.759542', NULL, NULL, NULL, NULL),
      ('d8bee1d7-49e3-4a5a-8f79-96cae7f5a150', '197ae046-a989-418f-99df-ec17310d73a4', 'cd7ac714-d579-4380-93d4-83e1c6dbc17b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T12:03:39.595515', '2026-03-18T12:03:39.595515', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('d8dc73c9-2494-4c7a-a85a-6479ce996045', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005025', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('d962ac5a-bf51-4d76-ac8f-f12fbff2f881', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000001723', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:33.006937', '2026-03-17T06:38:33.006937', NULL, NULL, NULL, NULL),
      ('d96c71b7-655f-4d5e-93a5-9fdc7cdb2cd7', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000553', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:02.005416', '2026-04-01T15:59:02.005416', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('db09d1db-1247-4864-970b-cdc9546ed729', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003042', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:47:20.804497', '2026-04-01T06:47:20.804497', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('db477048-c340-4872-a8e4-0c2595b1b274', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9023', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('db989ffd-9f52-4c1d-95b3-d2e24b6aede2', '9441cc00-943f-4469-aef5-7fae7171b2b9', '20dfe0b5-3990-4bb4-bc02-6f93b8673e36', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T03:12:16.143585', '2026-03-18T03:12:16.143585', NULL, NULL, NULL, NULL),
      ('dbc1ba50-723f-41fe-96e5-7228df00345a', '00000000-0000-0000-0000-000000002001', 'a722cf91-835e-4616-8caf-f56a8451d70e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:54:34.706296', '2026-04-01T06:54:34.706296', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('dbdb0265-924c-4457-8a36-7444ef5d5fbf', '00000000-0000-0000-0000-000000005102', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('dbf1d2ba-4211-4cd3-884a-d8231684b083', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000542', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.10148', '2026-03-17T07:49:17.10148', NULL, NULL, NULL, NULL),
      ('dc82d868-7b35-47c9-9c32-2bf056de1473', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001721', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('dccc23e8-999d-45cf-8d68-fde201cb915d', '00000000-0000-0000-0000-000000002001', '55963948-87ca-47e7-9de7-ddd7f3dc675f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:55:19.57439', '2026-04-01T06:55:19.57439', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('dd83c755-7132-4cad-a05b-19111e6123ae', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000005021', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:45:54.704622', '2026-04-01T06:45:54.704622', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('ddfa45a2-7430-4796-b298-123b811827e5', 'b8cf7f37-cbeb-4adb-9032-2cac106bdbd3', '00000000-0000-0000-0000-000000000509', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, '2026-03-13T17:34:58.261925', '2026-03-13T17:34:59.534442', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', '2026-03-13T17:34:59.534442', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b'),
      ('de57ccee-bbfb-43d8-b935-a157c1b6fd1e', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('de580e78-c27c-4f7b-bb9b-f3b475f5bc21', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000515', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.131499', '2026-03-14T08:45:17.131499', NULL, NULL, NULL, NULL),
      ('def8cd1d-2b8e-4e9a-838f-b2050aeb8731', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001818', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.391916', '2026-03-14T08:45:16.391916', NULL, NULL, NULL, NULL),
      ('e05b83d7-805a-4bde-b266-5a75e017e418', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001725', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('e0cd8b62-f8de-4067-a1c0-5a82af5b24db', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003011', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('e120ee9e-f027-4f8c-9528-793ffaa4abe2', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '4db67994-51ad-4dde-93b1-3abd1842da4d', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.935441', '2026-03-14T08:45:16.935441', NULL, NULL, NULL, NULL),
      ('e1e10b8a-a37d-4c78-96f2-5613a94ec25c', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.10098', '2026-03-14T08:45:15.10098', NULL, NULL, NULL, NULL),
      ('e1eb926c-2159-43e4-af28-fd4f3f16dec5', '00000000-0000-0000-0000-000000004001', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:06.311372', '2026-04-01T15:59:06.311372', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('e230ef4b-8ad0-4e3e-a7cb-d577056f0c98', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001704', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('e2b02110-b240-40ca-9d3d-0a6b3cf959ac', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001715', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('e2bcc890-994b-4493-a4a3-e003f02b216c', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000551', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.853395', '2026-03-17T08:28:44.853395', NULL, NULL, NULL, NULL),
      ('e36487f8-ce10-4e90-b769-e3afa539c8ae', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001705', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.502543', '2026-03-14T08:45:15.502543', NULL, NULL, NULL, NULL),
      ('e39b7092-a3d6-4080-bae1-dc07e7b8cf90', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000001814', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('e4306a9e-4190-4848-ad8e-85f9a802cdfb', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ee241772-1028-47fe-813c-04377db03e20', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('e4334156-d325-411a-b993-7054c1083349', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000554', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:02.426107', '2026-04-01T15:59:02.426107', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('e43f6db1-fa09-44f7-825b-3551b90ae918', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9013', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('e456ffb1-e995-4d2c-ba01-fe235a3e572f', '00000000-0000-0000-0000-000000005105', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('e45cd912-7dba-4c11-b9f0-8d1a2009e824', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003043', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:47:22.205324', '2026-04-01T06:47:22.205324', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('e4c401e5-68f3-4b24-bcd7-bc6b6fe24569', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9032', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('e54fc5c4-dfc9-479e-920a-0e95c78fe31a', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001714', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('e56e1ee8-5cc7-4215-b493-c49cf6b31cc1', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('e69655cf-1c5f-48af-aa16-626d6a118695', '00000000-0000-0000-0000-000000000601', '1350f1fa-7c92-4159-a4a5-e64b3523d1ee', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T21:06:14.218265', '2026-03-30T21:06:14.218265', NULL, NULL, NULL, NULL),
      ('e6bb2360-6cb4-4f9f-ad55-26474ebc370a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000551', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T08:28:44.995841', '2026-03-17T08:28:44.995841', NULL, NULL, NULL, NULL),
      ('e6ca645b-1d27-4a44-ba5f-518651f75c30', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9023', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('e6d18fa6-a1ce-453e-be2a-eabb65da7f8e', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9012', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('e6df65a3-14f0-404f-998a-afddb788621f', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003031', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('e7201346-f90d-4575-b80b-04fca5ed4161', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000007020', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:17:34.637994', '2026-03-22T15:17:34.637994', NULL, NULL, NULL, NULL),
      ('e73ee5b6-3463-437d-a4b9-cacff5fea008', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-00000000050c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.955133', '2026-03-14T08:45:14.955133', NULL, NULL, NULL, NULL),
      ('e7c4bb6f-0c57-4c1f-85f9-01ce849ab3ef', '00000000-0000-0000-0000-000000005100', 'e18a4b59-eb37-4df3-9c09-263cf74ea33a', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('e8545b34-fc09-45c4-bbd2-8707379196d3', '00000000-0000-0000-0000-000000005105', 'ec07be31-5506-4a09-8f9f-7d3d402f9034', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('e8713491-1e3c-4319-9a86-4512b89780dc', '00000000-0000-0000-0000-000000005103', '00000000-0000-0000-0000-000000003010', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('e8a8f248-284c-4575-b3fd-28351ec9af20', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003040', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('e8b72ff0-d264-4c1c-a03b-0c4ce5160035', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ebbeba6f-b172-4038-a2a3-384060a1ec43', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('e8c1927c-a43a-4e3a-ad57-8833b10ac054', '00000000-0000-0000-0000-000000004001', '55963948-87ca-47e7-9de7-ddd7f3dc675f', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:11.360062', '2026-04-01T06:51:11.360062', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('e8cc34ce-7fd0-46bb-bb44-a646d585488f', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000000516', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-01T18:42:32.767057', '2026-04-01T18:42:32.767057', NULL, NULL, NULL, NULL),
      ('e8dba5c9-c6c7-4d38-81d3-2502322207cb', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003072', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:52.459669', '2026-04-01T06:51:52.459669', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('e9785ad0-95d0-4242-aba1-35997cffa77d', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003063', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('e99873c9-7c8a-428a-a43b-b2282d64b580', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000542', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.145386', '2026-03-17T07:49:17.145386', NULL, NULL, NULL, NULL),
      ('eb1559c1-fca2-46f2-b336-c46389763ba4', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001813', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.138522', '2026-03-14T08:45:16.138522', NULL, NULL, NULL, NULL),
      ('eb4d0041-68c1-41a1-9417-629e5f2ae97c', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000009002', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:11.607206', '2026-04-01T15:59:11.607206', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('eb9dee6a-e097-4f49-a372-3692b52547ee', '00000000-0000-0000-0000-000000004012', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:51:44.944647', '2026-03-17T15:51:44.944647', NULL, NULL, NULL, NULL),
      ('ebed9e15-12ef-48b2-abf1-69e83d55d7dd', 'dc05ba16-3cd7-4e32-b219-01b788325f30', 'a59a9d62-3e75-47ae-b485-11b0d6c8669e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.836248', '2026-03-14T08:45:16.836248', NULL, NULL, NULL, NULL),
      ('ec033307-c5fb-465e-90b5-1603b24e233c', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000000541', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:49:17.10148', '2026-03-17T07:49:17.10148', NULL, NULL, NULL, NULL),
      ('ec3c7982-64c2-40e5-a953-dcc02dd55db7', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000007023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T15:17:34.637994', '2026-03-22T15:17:34.637994', NULL, NULL, NULL, NULL),
      ('eccb3a4e-7a2c-4184-804d-532ee4d7140e', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000001711', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.914867', '2026-03-17T06:38:32.914867', NULL, NULL, NULL, NULL),
      ('ed5b84c0-d023-47ce-8819-9022272c75af', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'b9bef6b4-83a0-4cb1-bbe3-ca9413e72967', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T15:55:27.86841', '2026-03-17T15:55:27.86841', NULL, NULL, NULL, NULL),
      ('ed9dcc22-4b96-4da6-89ce-116917fe2d35', '00000000-0000-0000-0000-000000005101', '00000000-0000-0000-0000-000000003051', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('ee414272-abb0-4905-b65f-e461f0eed500', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '08e2ccca-5d32-49e0-b4e5-062fb0177f81', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:17.882259', '2026-03-14T08:45:17.882259', NULL, NULL, NULL, NULL),
      ('ef8dadca-7c8c-4ec5-9252-611b45d9119e', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008005', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:23.157361', '2026-04-01T06:49:23.157361', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('f0b04048-5342-4f91-8e8f-e81b12d4881e', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003015', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:16.001718', '2026-04-01T06:51:16.001718', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('f0b8464f-471f-4583-8e5b-567ac7c31719', '00000000-0000-0000-0000-000000004001', '90547321-261e-4d52-a79c-dc2e6f441e0b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('f1494ce9-fdb7-4c79-a1d6-1954c8f94b5f', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000008902', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.846896', '2026-04-01T02:55:56.846896', NULL, NULL, NULL, NULL),
      ('f18ee741-dbe1-4602-9f1a-5aa6d2046227', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000008901', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:51:30.899251', '2026-04-01T06:51:30.899251', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('f1f47b6b-92cb-4e1c-bcb3-7715c1c023c5', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000005020', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('f204295a-f913-43e0-9c4d-86cb1887aec4', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001724', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.942678', '2026-03-14T08:45:15.942678', NULL, NULL, NULL, NULL),
      ('f239e8cb-dd68-4336-85f5-734b123b75bb', '00000000-0000-0000-0000-000000005105', '00000000-0000-0000-0000-000000009001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('f24b7f6f-0f0e-4f26-824e-239480e2fa6d', '00000000-0000-0000-0000-000000005103', '00000000-0000-0000-0000-000000003050', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('f346f49c-440c-489b-9dcd-6f6a0c13887b', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000003041', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:33.397356', '2026-04-01T06:49:33.397356', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('f3670280-419c-4caf-827b-d68b2f898155', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000009003', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('f3750dd2-11b1-4264-9827-7c2cab68e792', '00000000-0000-0000-0000-000000005104', 'ec07be31-5506-4a09-8f9f-7d3d402f9022', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('f39cf3e8-76cc-4563-a122-0acab6064cf3', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000006023', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:52:00.984328', '2026-04-01T06:52:00.984328', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('f39e85fe-d0e3-4470-8287-d0a57c0a5530', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000511', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.201558', '2026-03-14T08:45:15.201558', NULL, NULL, NULL, NULL),
      ('f4c505db-9903-4cde-8a84-2e16fade3302', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ba30a1c3-d974-4d81-8f2d-28bfccb4bf6b', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T14:23:40.475695', '2026-03-18T14:23:40.475695', NULL, NULL, NULL, NULL),
      ('f4d7157b-8d65-4cf7-bcd7-11f627dea762', '00000000-0000-0000-0000-000000005105', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('f4f20722-42c6-4c71-b009-d2140a123818', '00000000-0000-0000-0000-000000000601', '16757271-2e78-4262-bb10-164de2feb96a', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T21:06:14.218265', '2026-03-30T21:06:14.218265', NULL, NULL, NULL, NULL),
      ('f5363954-b168-4959-979a-ce2ce4d52319', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003033', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('f5af86ca-55b8-4c8a-8428-092b58229719', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'ec07be31-5506-4a09-8f9f-7d3d402f9034', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T06:54:48.012366', '2026-04-02T06:54:48.012366', NULL, NULL, NULL, NULL),
      ('f5b3b922-f4e8-490e-a0b0-ae235cb37e52', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003061', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('f5dd282e-e471-47c9-bc3c-79dc8aa4ae03', '00000000-0000-0000-0000-000000005100', '00000000-0000-0000-0000-000000003023', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('f7f17852-ee66-493a-85fe-f64cd082d878', '00000000-0000-0000-0000-000000005100', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('f84fc570-0690-4513-9353-9239b7cb22f4', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000003064', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-17T06:59:17.888689', '2026-03-17T06:59:17.888689', NULL, NULL, NULL, NULL),
      ('f85fd081-eb7f-48b5-9f78-6a97a8fdb2fc', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000001812', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:16.088398', '2026-03-14T08:45:16.088398', NULL, NULL, NULL, NULL),
      ('f89b2ce3-3d2c-4bc5-9cb7-1d6f92deb46e', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000501', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-13T17:40:34.276156', '2026-03-13T17:40:34.276156', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', 'cdc05df1-7847-4b94-a6f5-68fc5e7f4f2b', NULL, NULL),
      ('f93384f0-45f0-41f4-a23e-fc687d18f557', '00000000-0000-0000-0000-000000004002', '00000000-0000-0000-0000-000000001722', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T06:38:32.94637', '2026-03-17T06:38:32.94637', NULL, NULL, NULL, NULL),
      ('f9d58a8a-a9d7-4d0a-9e42-d479c8549b4c', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000003030', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('fb471f3b-66f5-4a68-af53-9dfd1b1fdfe9', '00000000-0000-0000-0000-000000005104', '340ab0cd-3506-4c40-b2f8-87397ffd5d69', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('fb68d3b6-15b5-49dd-9bab-8e62505dc280', '00000000-0000-0000-0000-000000005104', '00000000-0000-0000-0000-000000003020', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-30T10:56:20.050384', '2026-03-30T10:56:20.050384', NULL, NULL, NULL, NULL),
      ('fb7f1584-d7c9-4728-a10a-9f186cca7ca1', '9441cc00-943f-4469-aef5-7fae7171b2b9', '00000000-0000-0000-0000-000000000510', TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-13T17:33:40.526446', '2026-03-13T17:33:40.526446', '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', NULL, NULL),
      ('fb8ed621-0158-436d-bead-90f4014eff58', '00000000-0000-0000-0000-000000000601', 'e6be427a-3f30-4fee-af22-cf8cc215da4e', TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, '2026-03-17T04:58:15.809888', '2026-03-17T04:58:15.809888', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000601', NULL, NULL),
      ('fb8ff7da-3fcc-4f60-9f54-1d9a1fbcc184', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000510', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:15.152797', '2026-03-14T08:45:15.152797', NULL, NULL, NULL, NULL),
      ('fbaeae83-fd12-4a4e-b031-91fd0bedc6cb', '00000000-0000-0000-0000-000000005106', '00000000-0000-0000-0000-000000009001', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T14:33:53.618157', '2026-03-31T14:33:53.618157', NULL, NULL, NULL, NULL),
      ('fc1c6bb0-bfea-4794-b9c5-3c0dd2eb01b9', '00000000-0000-0000-0000-000000002001', '00000000-0000-0000-0000-000000003070', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:13:43.791271', '2026-03-17T07:13:43.791271', NULL, NULL, NULL, NULL),
      ('fcdce522-b0eb-4723-80f6-a5fb9940919b', '00000000-0000-0000-0000-000000004011', '00000000-0000-0000-0000-000000008901', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T02:55:56.810308', '2026-04-01T02:55:56.810308', NULL, NULL, NULL, NULL),
      ('fd1b7f59-4d69-4e27-bbae-4488060dc74a', '00000000-0000-0000-0000-000000004001', '00000000-0000-0000-0000-000000000507', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T15:59:45.71419', '2026-04-01T15:59:45.71419', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('fd2a7f88-2cfd-4ec5-965d-eb0d14b44218', '00000000-0000-0000-0000-000000000601', 'ea89e772-4707-4117-9306-bd047278cb2c', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:37:27.188718', '2026-03-16T10:37:27.188718', NULL, NULL, NULL, NULL),
      ('fe72f0a8-4180-4575-8d8b-458c38911a59', '00000000-0000-0000-0000-000000004011', 'a722cf91-835e-4616-8caf-f56a8451d70e', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-18T02:17:17.313391', '2026-03-18T02:17:17.313391', NULL, NULL, NULL, NULL),
      ('ff8d4ab9-5521-4f61-987e-71d595ca552a', 'dc05ba16-3cd7-4e32-b219-01b788325f30', '00000000-0000-0000-0000-000000000503', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:45:14.506052', '2026-03-14T08:45:14.506052', NULL, NULL, NULL, NULL)
  ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.50_dim_portal_views (6 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."50_dim_portal_views" (id, code, name, description, color, icon, sort_order, is_active, created_at, default_route, updated_at)
  VALUES
      ('51e85cb2-7bcf-49bf-acd3-edd8ce2fb5b4', 'vendor', 'Staff Auditor', 'Staff Auditor — For Audit Readiness', '#06b6d4', 'Building2', 50, TRUE, '2026-03-16T08:51:00.847272+00:00', '/dashboard', '2026-03-17T05:03:53.976966+00:00'),
      ('6c48838a-5586-45b4-9ea4-a077ee65d5ff', 'auditor', 'External Auditor', 'Read-only compliance view — evidence requests, control testing, findings', '#6366f1', 'Search', 20, TRUE, '2026-03-16T08:51:00.847272+00:00', '/framework_library', '2026-03-17T05:03:53.976966+00:00'),
      ('82063d7a-8c17-4423-9f56-2431b7b2e2b2', 'global', 'Global', 'Unrestricted access — all routes and modules visible', '#ef4444', 'Globe', 1, TRUE, '2026-03-17T09:15:03.010065+00:00', '/dashboards', '2026-03-18T09:11:19.865735+00:00'),
      ('b3971f16-c375-4746-ab63-e513251f2a39', 'engineering', 'Engineering', 'Task-focused view — my tasks, evidence to submit, owned controls, test results', '#10b981', 'Wrench', 30, TRUE, '2026-03-16T08:51:00.847272+00:00', '/audit-workspace/engineering', '2026-03-17T05:03:53.976966+00:00'),
      ('cbb4c715-5331-492a-9075-593e40b99713', 'grc', 'GRC Practitioners', 'Full compliance management — frameworks, controls, risks, tasks, tests', '#2878ff', 'ShieldCheck', 10, TRUE, '2026-03-16T08:51:00.847272+00:00', '/dashboard', '2026-03-18T09:13:29.096388+00:00'),
      ('ecfe55ad-2891-4803-8fbc-b789d070160e', 'executive', 'CISO / Executive', 'Board-level read-only view — security posture, risk summary, framework status', '#f59e0b', 'BarChart3', 40, TRUE, '2026-03-16T08:51:00.847272+00:00', '/audit-workspace/executive', '2026-03-19T05:33:32.781811+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, color = EXCLUDED.color, icon = EXCLUDED.icon, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, default_route = EXCLUDED.default_route, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.51_lnk_role_views (30 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."51_lnk_role_views" (id, role_id, view_code, created_at, created_by)
  VALUES
      ('08a1bf22-e522-4116-a2f8-9825eef03dbe', '00000000-0000-0000-0000-000000000601', 'grc', '2026-03-16T08:51:00.847272+00:00', NULL),
      ('18a81188-d930-434a-bd84-f69c666fc56a', '00000000-0000-0000-0000-000000005100', 'grc', '2026-04-01T15:12:05.280726+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('1fc78b71-d4b4-4aa9-88ad-289eedfb1b2d', '00000000-0000-0000-0000-000000004001', 'vendor', '2026-04-01T16:15:58.811477+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('25d2d9dd-c865-4f12-9a20-4eaa459ac8cc', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'global', '2026-04-01T09:25:01.994915+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('33549fad-4227-47b2-86c1-707d5499b189', '00000000-0000-0000-0000-000000005102', 'engineering', '2026-04-01T15:17:38.063541+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('33c1a9a8-e313-4c35-adf5-d5fcff549aaf', '00000000-0000-0000-0000-000000004002', 'executive', '2026-04-01T16:38:44.008727+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('4516ded5-4493-4417-97ab-3babc7393ee7', '00000000-0000-0000-0000-000000004002', 'vendor', '2026-04-01T16:38:35.007599+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('4c2e5b25-7d43-4682-93d3-7fddc81aff66', '00000000-0000-0000-0000-000000000601', 'global', '2026-03-17T09:15:03.063422+00:00', NULL),
      ('5a187619-9b33-4926-85b6-f661fa036601', '00000000-0000-0000-0000-000000005104', 'auditor', '2026-04-01T15:13:34.533987+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('5bf6fc68-0b23-44f0-9e30-7d651c4036de', '00000000-0000-0000-0000-000000004002', 'grc', '2026-04-01T16:39:04.857053+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('5d876281-31ae-45ba-8d29-93839b43d3c6', '00000000-0000-0000-0000-000000004002', 'auditor', '2026-04-01T16:38:58.618803+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('66a84005-4e98-4dc5-801f-d4cb18b0a133', '00000000-0000-0000-0000-000000004001', 'auditor', '2026-04-01T15:14:13.903062+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('6b20aba8-c081-434c-bfd6-4ba2c4c6bac9', '00000000-0000-0000-0000-000000000601', 'auditor', '2026-04-01T15:15:36.404228+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('6eeb8075-58f6-40e3-aa9f-07517e060a17', '00000000-0000-0000-0000-000000005105', 'auditor', '2026-03-31T12:41:03.670369+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('7271312d-b280-4d86-a23a-271339c8db41', '00000000-0000-0000-0000-000000005103', 'executive', '2026-04-01T16:15:48.504179+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('7b1aa795-dcaf-4175-be95-52dc50e4f92a', '00000000-0000-0000-0000-000000004001', 'executive', '2026-04-01T16:15:43.405577+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('862185da-fd56-4f46-8811-85689e435d78', '00000000-0000-0000-0000-000000000601', 'engineering', '2026-04-01T15:17:16.111093+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('87a126dd-658b-49ce-b5e8-1eb62535b35d', '00000000-0000-0000-0000-000000004001', 'grc', '2026-03-17T07:13:40.298205+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('87cc9979-b5ac-4c1d-a441-060ec7a41a3b', '00000000-0000-0000-0000-000000000601', 'executive', '2026-04-01T16:15:47.011991+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('8a17d220-b09c-468e-b98a-307363a6d97a', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'executive', '2026-04-01T16:15:45.911447+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('9e4fad97-32f3-4513-a223-8bcfb80168ad', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'auditor', '2026-04-01T15:14:21.428623+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('9ea28663-69d9-411b-ac9a-463d692a6efd', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'grc', '2026-03-17T05:19:41.306496+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('b268280f-a811-43b3-849a-1dacffadfd25', '00000000-0000-0000-0000-000000004003', 'grc', '2026-04-01T16:39:06.702258+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('ba4d1c01-6c33-4817-9218-77cac5399d60', '00000000-0000-0000-0000-000000004001', 'engineering', '2026-04-01T15:17:09.901559+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('cfe28b9d-c2ad-41b8-8dcd-54d6dd48f8b2', '00000000-0000-0000-0000-000000004002', 'engineering', '2026-04-01T16:38:52.111888+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('eff95423-a867-4947-acbb-ac3d49635f96', '00000000-0000-0000-0000-000000004001', 'global', '2026-04-01T09:24:50.39611+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('f11204f3-5ca2-4ba7-a555-80721c3a5e94', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'vendor', '2026-03-16T17:38:33.431073+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('f220dad5-addb-471b-8fd4-fb9a315b1c18', '9441cc00-943f-4469-aef5-7fae7171b2b9', 'engineering', '2026-03-17T05:25:30.352749+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('f3422595-3af0-4990-b7ca-c0d6a9337e38', '00000000-0000-0000-0000-000000000601', 'vendor', '2026-04-01T16:16:02.304401+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223'),
      ('f39392aa-975d-4a80-b4f3-48583ac4747b', '00000000-0000-0000-0000-000000005105', 'vendor', '2026-04-01T16:16:08.206917+00:00', 'af88f921-2e07-48aa-a3e5-c556a2b2c223')
  ON CONFLICT (role_id, view_code) DO NOTHING;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_auth_manage.52_dtl_view_routes (39 rows)
DO $$ BEGIN
  INSERT INTO "03_auth_manage"."52_dtl_view_routes" (id, view_code, route_prefix, is_read_only, sort_order, sidebar_label, sidebar_icon, sidebar_section)
  VALUES
      ('00dc2b33-cee8-4bde-bb8d-3a53317c0cfc', 'executive', '/audit-workspace/grc', FALSE, 60, 'Audit Management', NULL, 'Audit Workspace'),
      ('015dec1d-9f46-4a24-ae99-2243ceb6876a', 'auditor', '/reports', FALSE, 60, 'Reports', NULL, NULL),
      ('035e770e-756a-4273-aa6f-3de1697a0f36', 'vendor', '/audit-workspace/auditor', FALSE, 10, 'Auditor Workspace', NULL, 'Audit Workspace'),
      ('0fc879ff-6aae-4ba2-a907-e7821e115719', 'auditor', '/audit-workspace/auditor', FALSE, 60, 'Auditor Workspace', NULL, 'Auditor Workspace'),
      ('12e5c2b1-3c5c-47d3-9901-622736d73166', 'grc', '/policies', FALSE, 70, 'Policies & Docs', 'BookOpen', 'GRC Platform'),
      ('2234ba69-5101-429d-aa69-7752b5333c4e', 'grc', '/frameworks', FALSE, 20, 'Frameworks', 'Library', 'GRC Platform'),
      ('289ea024-118f-4caa-a8d5-92aafbf6ea86', 'engineering', '/controls', TRUE, 30, 'Controls', 'ShieldCheck', 'Controls I Own'),
      ('30227b0d-f9fc-415e-9536-d3f873af77af', 'grc', '/framework_library', FALSE, 110, 'framework library', NULL, NULL),
      ('35e8246f-eecb-4104-b35b-bfeda982b362', 'vendor', '/reports', FALSE, 20, 'Reports', NULL, 'Risk & Governance'),
      ('37843367-f0af-4b2b-a88f-9c83ab776986', 'grc', '/monitoring', FALSE, 130, 'Live Monitoring', NULL, NULL),
      ('3ea4cd7e-2560-4270-bdb1-7f7a0a7a449d', 'auditor', '/tasks', FALSE, 50, 'Tasks', NULL, NULL),
      ('43bc3b9a-9d04-487c-a38d-4bb77dddd84b', 'grc', '/dashboard', FALSE, 10, 'Dashboard', 'LayoutDashboard', 'Navigate'),
      ('47ff80b6-f563-42a4-b453-7b8b81a5b9ba', 'global', '/*', FALSE, 0, NULL, NULL, NULL),
      ('4b12c55c-16c0-467d-89c1-79a9c6cfc193', 'grc', '/reports', FALSE, 120, 'reports', NULL, NULL),
      ('4c5196e8-0af7-4296-af6d-fd4ac74af0e2', 'executive', '/risks', TRUE, 20, 'Risk Summary', 'ShieldAlert', 'Board View'),
      ('5560de8b-26c2-4260-8d80-b2408dd1ec27', 'vendor', '/issues', FALSE, 70, 'Issues', NULL, 'Monitoring'),
      ('5b640935-554f-4b55-a6a7-e5ed7df917b6', 'grc', '/assets', FALSE, 140, 'Asset Inventory', NULL, NULL),
      ('6443af6a-9e10-4ecb-a2d9-ebac58f7ce11', 'executive', '/frameworks', TRUE, 30, 'Frameworks', 'Library', 'Board View'),
      ('6e4dff03-7334-4624-982b-06adbe538855', 'grc', '/feedback', FALSE, 80, 'Feedback & Support', 'MessageSquarePlus', 'Administration'),
      ('72edf00c-1a96-439e-a4bb-fbc54f69370f', 'grc', '/issues', FALSE, 150, 'Issues', NULL, NULL),
      ('828c5a4d-e3f0-41eb-9614-7bbb94ee8f9e', 'engineering', '/tests', TRUE, 40, 'Test Results', 'FlaskConical', 'Controls I Own'),
      ('836132c0-5b67-4c15-a45e-41dd55441f60', 'grc', '/workspaces', FALSE, 70, 'Workspaces', 'Layers', 'Administration'),
      ('8951f8bf-29b6-48a5-9ea9-8348ded7faec', 'vendor', '/controls', FALSE, 40, 'Controls', NULL, 'Compliance'),
      ('90a6516b-f97f-4387-b746-e17f70e02a7f', 'executive', '/policies', TRUE, 30, 'Policies & Docs', 'BookOpen', 'GRC Platform'),
      ('9c86455a-5291-4e5b-ab87-3024f54539ee', 'grc', '/tasks', FALSE, 60, 'Tasks', 'CheckSquare', 'GRC Platform'),
      ('9d3f4a58-3a2b-4dbb-946b-af544d7338e2', 'executive', '/framework_library', FALSE, 50, 'framework library', NULL, NULL),
      ('a3c9e271-ec7c-4599-92b8-6600bc4bdd4b', 'vendor', '/tasks', FALSE, 30, 'Tasks', NULL, 'Compliance'),
      ('a40fd46c-f56d-46a2-9ea4-a136f11c646f', 'grc', '/tests', FALSE, 40, 'Control Tests', 'FlaskConical', 'GRC Platform'),
      ('ae7a3c25-8ba3-409a-9e63-2e7bd87847c1', 'engineering', '/audit-workspace/engineering', FALSE, 50, 'FulFillment', NULL, 'Audit Workspace'),
      ('b375dde9-565c-4486-a4c3-66726713215f', 'grc', '/risks', FALSE, 50, 'Risk Registry', 'ShieldAlert', 'GRC Platform'),
      ('b5711382-9409-42ca-95c4-535ff892dacd', 'grc', '/audit-workspace/grc', FALSE, 160, 'Audit Management', NULL, NULL),
      ('b723bbf0-04ae-473e-b8a9-ae64542804df', 'auditor', '/controls', TRUE, 30, 'Controls', 'ShieldCheck', 'Compliance'),
      ('ce8866a7-c220-4df8-bcd3-7c19d03a6a7f', 'executive', '/audit-workspace/executive', FALSE, 60, 'Compliance Insights', NULL, 'Audit Workspace'),
      ('d41e3b43-c774-4670-b698-bd9842417741', 'vendor', '/frameworks', FALSE, 50, 'Frameworks', NULL, 'Compliance'),
      ('dd819f10-afb5-4fe5-80ea-6070df888e1c', 'grc', '/controls', FALSE, 30, 'Controls', 'ShieldCheck', 'GRC Platform'),
      ('e239cdde-23cf-42ef-9f07-f486f1f1b029', 'auditor', '/frameworks', TRUE, 20, 'Frameworks', 'Library', 'Compliance'),
      ('e713bf6b-edf7-49c9-8fc9-05f985888e73', 'engineering', '/tasks', FALSE, 40, 'My Tasks', NULL, 'Compliance'),
      ('eb42caa6-84a1-4e51-984a-c4ecd81af41b', 'vendor', '/tests', FALSE, 60, 'Control Tests', NULL, 'Monitoring'),
      ('eea82a47-6136-47b8-a023-89ea90abc678', 'auditor', '/framework_library', FALSE, 60, 'framework lirary', NULL, NULL)
  ON CONFLICT (view_code, route_prefix) DO UPDATE SET is_read_only = EXCLUDED.is_read_only, sort_order = EXCLUDED.sort_order, sidebar_label = EXCLUDED.sidebar_label, sidebar_icon = EXCLUDED.sidebar_icon, sidebar_section = EXCLUDED.sidebar_section;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: NOTIFICATIONS
-- Extracted: 2026-04-02T12:26:31.549388
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

-- 03_notifications.04_dim_notification_types (51 rows)
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
      ('c0000000-0000-0000-0000-000000000014', 'platform_maintenance', 'Scheduled Maintenance', 'Scheduled platform maintenance window notification', 'system', FALSE, FALSE, TRUE, NULL, 20, '2026-03-14T09:38:58.376265', '2026-03-14T09:38:58.376265', FALSE),
      ('c0000000-0000-0000-0000-000000000021', 'magic_link_assignee', 'Magic Link (Assignee Portal)', 'Passwordless login link for assignee portal — sent to task assignees for one-click portal access', 'security', TRUE, TRUE, TRUE, NULL, 21, '2026-04-01T10:45:13.564116', '2026-04-01T10:45:13.564116', FALSE),
      ('c0000000-0000-0000-0000-000000000030', 'workspace_invite_grc', 'GRC Workspace Invitation', 'Notification sent when a user is invited to a workspace with a GRC role (auditor, lead, engineer, etc.)', 'engagement', FALSE, FALSE, TRUE, NULL, 30, '2026-03-31T05:27:22.373673', '2026-03-31T05:27:22.373673', FALSE),
      ('c0000000-0000-0000-0000-000000000031', 'engagement_access_granted', 'Engagement Access Granted', 'Notification sent when a user is granted access to a specific audit engagement', 'engagement', FALSE, FALSE, TRUE, NULL, 31, '2026-03-31T05:27:22.974268', '2026-03-31T05:27:22.974268', FALSE),
      ('c0000000-0000-0000-0000-000000000040', 'task_assigned', 'Task Assigned', 'Notification sent when a task is assigned to a user', 'engagement', FALSE, FALSE, TRUE, NULL, 40, '2026-04-02T05:25:01.366354', '2026-04-02T05:25:01.366354', FALSE),
      ('c0000000-0000-0000-0000-000000000041', 'task_status_changed', 'Task Status Changed', 'Notification sent when the status of a task the user owns or follows changes', 'engagement', FALSE, FALSE, TRUE, 300, 41, '2026-04-02T05:25:01.366354', '2026-04-02T05:25:01.366354', FALSE),
      ('c0000000-0000-0000-0000-000000000042', 'task_comment_added', 'Comment Added to Task', 'Notification sent when a new comment is added to a task the user is involved with', 'engagement', FALSE, FALSE, TRUE, 60, 42, '2026-04-02T05:25:01.366354', '2026-04-02T05:25:01.366354', FALSE),
      ('c0000000-0000-0000-0000-000000000043', 'task_feedback_received', 'Task Feedback Received', 'Notification sent when feedback is submitted on a task or control evidence', 'engagement', FALSE, FALSE, TRUE, NULL, 43, '2026-04-02T05:25:01.366354', '2026-04-02T05:25:01.366354', FALSE),
      ('c0000000-0000-0000-0001-000000000001', 'task_reassigned', 'Task Reassigned', 'Sent to the new assignee when a task is reassigned', 'engagement', FALSE, FALSE, TRUE, NULL, 51, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000002', 'task_overdue', 'Task Overdue', 'Sent to the assignee when a task passes its due date without being completed', 'engagement', FALSE, FALSE, TRUE, NULL, 52, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000003', 'task_submitted', 'Task Submitted for Review', 'Sent to reviewers when a task is moved to pending_verification', 'engagement', FALSE, FALSE, TRUE, NULL, 53, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000004', 'task_approved', 'Task Approved', 'Sent to the assignee when their task is approved and published', 'engagement', FALSE, FALSE, TRUE, NULL, 54, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000005', 'task_rejected', 'Task Sent Back', 'Sent to the assignee when their task is rejected and sent back to in_progress', 'engagement', FALSE, FALSE, TRUE, NULL, 55, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000010', 'comment_mention', 'Mentioned in Comment', 'Sent when a user is @-mentioned in a comment', 'engagement', FALSE, FALSE, TRUE, 60, 60, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000011', 'comment_reply', 'Reply to Your Comment', 'Sent when someone replies to your comment', 'engagement', FALSE, FALSE, TRUE, 60, 61, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000020', 'risk_assigned', 'Risk Assigned', 'Sent when a risk is assigned to a user as owner', 'engagement', FALSE, FALSE, TRUE, NULL, 70, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000021', 'risk_review_due', 'Risk Review Due', 'Sent when a risk is approaching its scheduled review date', 'engagement', FALSE, FALSE, TRUE, NULL, 71, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000022', 'risk_status_changed', 'Risk Status Changed', 'Sent to the risk owner when a risk status changes', 'engagement', FALSE, FALSE, TRUE, 300, 72, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000023', 'treatment_plan_assigned', 'Treatment Plan Assigned', 'Sent to the treatment owner when a treatment plan is created and assigned to them', 'engagement', FALSE, FALSE, TRUE, NULL, 73, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000030', 'finding_assigned', 'Finding Assigned', 'Sent when an audit finding is assigned to a user for remediation', 'engagement', FALSE, FALSE, TRUE, NULL, 80, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000031', 'finding_response_needed', 'Finding Response Needed', 'Sent to prompt the assignee to respond to a finding in auditor_review status', 'engagement', FALSE, FALSE, TRUE, NULL, 81, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000032', 'finding_reviewed', 'Finding Reviewed', 'Sent to the finding owner after auditor reviews and closes or escalates a finding', 'engagement', FALSE, FALSE, TRUE, NULL, 82, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000040', 'assessment_completed', 'Assessment Completed', 'Sent when an assessment reaches completed status', 'engagement', FALSE, FALSE, TRUE, NULL, 90, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000050', 'engagement_status_changed', 'Engagement Status Changed', 'Sent to engagement participants when the engagement moves to a new phase', 'engagement', FALSE, FALSE, TRUE, NULL, 100, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000060', 'report_ready', 'Report Ready', 'Sent when an AI-generated report has completed and is ready to view', 'transactional', FALSE, FALSE, TRUE, NULL, 110, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000061', 'report_failed', 'Report Generation Failed', 'Sent when report generation fails so the user can retry', 'transactional', FALSE, FALSE, TRUE, NULL, 111, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000070', 'approval_required', 'Approval Required', 'Sent to the designated approver when an AI agent action requires human approval', 'transactional', TRUE, FALSE, TRUE, NULL, 120, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000071', 'approval_expired', 'Approval Request Expired', 'Sent to the requester when an approval times out without a response', 'transactional', FALSE, FALSE, TRUE, NULL, 121, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000072', 'approval_rejected', 'Approval Rejected', 'Sent to the requester when their AI approval request is rejected by the approver', 'transactional', FALSE, FALSE, TRUE, NULL, 122, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000080', 'ticket_assigned', 'Feedback Ticket Assigned', 'Sent when a feedback/support ticket is assigned to a user', 'transactional', FALSE, FALSE, TRUE, NULL, 130, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE),
      ('c0000000-0000-0000-0001-000000000081', 'ticket_status_changed', 'Ticket Status Changed', 'Sent to the ticket submitter when the status of their ticket changes', 'transactional', FALSE, FALSE, TRUE, 300, 131, '2026-04-02T05:25:02.446556', '2026-04-02T05:25:02.446556', FALSE)
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

-- 03_notifications.07_dim_notification_channel_types (92 rows)
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
      ('f0000000-0000-0000-0000-000000000020', 'platform_maintenance', 'web_push', 'high', TRUE, '2026-03-14T09:38:58.411242', '2026-03-14T09:38:58.411242'),
      ('f0000000-0000-0000-0000-000000000021', 'magic_link_assignee', 'email', 'high', TRUE, '2026-04-01T10:45:13.564116', '2026-04-01T10:45:13.564116'),
      ('f0000000-0000-0000-0000-000000000030', 'workspace_invite_grc', 'email', 'high', TRUE, '2026-03-31T05:27:22.996589', '2026-03-31T05:27:22.996589'),
      ('f0000000-0000-0000-0000-000000000031', 'workspace_invite_grc', 'web_push', 'high', TRUE, '2026-03-31T05:27:22.996589', '2026-03-31T05:27:22.996589'),
      ('f0000000-0000-0000-0000-000000000032', 'engagement_access_granted', 'email', 'high', TRUE, '2026-03-31T05:27:22.996589', '2026-03-31T05:27:22.996589'),
      ('f0000000-0000-0000-0000-000000000033', 'engagement_access_granted', 'web_push', 'high', TRUE, '2026-03-31T05:27:22.996589', '2026-03-31T05:27:22.996589'),
      ('f0000000-0000-0000-0000-000000000040', 'task_assigned', 'email', 'high', TRUE, '2026-04-02T05:25:01.394914', '2026-04-02T05:25:01.394914'),
      ('f0000000-0000-0000-0000-000000000041', 'task_assigned', 'web_push', 'high', TRUE, '2026-04-02T05:25:01.394914', '2026-04-02T05:25:01.394914'),
      ('f0000000-0000-0000-0000-000000000042', 'task_status_changed', 'email', 'normal', TRUE, '2026-04-02T05:25:01.394914', '2026-04-02T05:25:01.394914'),
      ('f0000000-0000-0000-0000-000000000043', 'task_status_changed', 'web_push', 'normal', TRUE, '2026-04-02T05:25:01.394914', '2026-04-02T05:25:01.394914'),
      ('f0000000-0000-0000-0000-000000000044', 'task_comment_added', 'email', 'normal', TRUE, '2026-04-02T05:25:01.394914', '2026-04-02T05:25:01.394914'),
      ('f0000000-0000-0000-0000-000000000045', 'task_comment_added', 'web_push', 'normal', TRUE, '2026-04-02T05:25:01.394914', '2026-04-02T05:25:01.394914'),
      ('f0000000-0000-0000-0000-000000000046', 'task_feedback_received', 'email', 'high', TRUE, '2026-04-02T05:25:01.394914', '2026-04-02T05:25:01.394914'),
      ('f0000000-0000-0000-0000-000000000047', 'task_feedback_received', 'web_push', 'high', TRUE, '2026-04-02T05:25:01.394914', '2026-04-02T05:25:01.394914'),
      ('f0000000-0000-0001-0001-000000000001', 'task_reassigned', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000002', 'task_reassigned', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000003', 'task_overdue', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000004', 'task_overdue', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000005', 'task_submitted', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000006', 'task_submitted', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000007', 'task_approved', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000008', 'task_approved', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000009', 'task_rejected', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000000a', 'task_rejected', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000000b', 'comment_mention', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000000c', 'comment_mention', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000000d', 'comment_reply', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000000e', 'comment_reply', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000000f', 'risk_assigned', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000010', 'risk_assigned', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000011', 'risk_review_due', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000012', 'risk_review_due', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000013', 'risk_status_changed', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000014', 'risk_status_changed', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000015', 'treatment_plan_assigned', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000016', 'treatment_plan_assigned', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000017', 'finding_assigned', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000018', 'finding_assigned', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000019', 'finding_response_needed', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000001a', 'finding_response_needed', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000001b', 'finding_reviewed', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000001c', 'finding_reviewed', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000001d', 'assessment_completed', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000001e', 'assessment_completed', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000001f', 'engagement_status_changed', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000020', 'engagement_status_changed', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000021', 'report_ready', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000022', 'report_ready', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000023', 'report_failed', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000024', 'report_failed', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000025', 'approval_required', 'email', 'critical', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000026', 'approval_required', 'web_push', 'critical', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000027', 'approval_expired', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000028', 'approval_expired', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-000000000029', 'approval_rejected', 'email', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000002a', 'approval_rejected', 'web_push', 'high', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000002b', 'ticket_assigned', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000002c', 'ticket_assigned', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000002d', 'ticket_status_changed', 'email', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709'),
      ('f0000000-0000-0001-0001-00000000002e', 'ticket_status_changed', 'web_push', 'normal', TRUE, '2026-04-02T05:25:02.528709', '2026-04-02T05:25:02.528709')
  ON CONFLICT (notification_type_code, channel_code) DO UPDATE SET priority_code = EXCLUDED.priority_code, is_default = EXCLUDED.is_default, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.08_dim_template_variable_keys (198 rows)
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
      ('a0000000-0000-0000-0030-000000000001', 'invite.grc_role_code', 'GRC Role Code', 'Machine code for the GRC role (e.g. grc_lead_auditor)', 'string', NULL, 'audit_property', NULL, 30, '2026-03-31T05:29:14.806841', '2026-03-31T05:29:14.806841', 'grc_lead_auditor', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0030-000000000002', 'invite.grc_role_label', 'GRC Role Label', 'Human-readable GRC role label (e.g. Lead Auditor)', 'string', NULL, 'audit_property', NULL, 31, '2026-03-31T05:29:14.806841', '2026-03-31T05:29:14.806841', 'Lead Auditor', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0030-000000000003', 'invite.engagement_name', 'Engagement Name', 'Name of the audit engagement this invitation grants access to', 'string', NULL, 'audit_property', NULL, 32, '2026-03-31T05:29:14.806841', '2026-03-31T05:29:14.806841', 'Q4 2025 SOC 2 Audit', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0030-000000000004', 'invite.framework_name', 'Framework Name', 'Framework name scoped to this invitation (e.g. SOC 2 Type II)', 'string', NULL, 'audit_property', NULL, 33, '2026-03-31T05:29:14.806841', '2026-03-31T05:29:14.806841', 'SOC 2 Type II', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0030-000000000005', 'invite.accept_url', 'Invitation Accept URL', 'Full URL for the invitee to click and accept the invitation', 'string', NULL, 'audit_property', NULL, 34, '2026-03-31T05:29:14.806841', '2026-03-31T05:29:14.806841', 'https://app.kcontrol.io/accept-invite?token=x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0030-000000000006', 'invite.expires_in', 'Invitation Expiry', 'Human-readable expiry string (e.g. 72 hours)', 'string', NULL, 'audit_property', NULL, 35, '2026-03-31T05:29:14.806841', '2026-03-31T05:29:14.806841', '72 hours', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0030-000000000007', 'invite.workspace_name', 'Invite Workspace Name', 'Name of the workspace the user is being invited to', 'string', NULL, 'audit_property', NULL, 36, '2026-03-31T05:29:14.806841', '2026-03-31T05:29:14.806841', 'Audit Workspace', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0030-000000000008', 'invite.org_name', 'Invite Org Name', 'Name of the organisation associated with this invitation', 'string', NULL, 'audit_property', NULL, 37, '2026-03-31T05:29:14.806841', '2026-03-31T05:29:14.806841', 'Acme Corp', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000001', 'task.title', 'Task Title', 'Title of the task', 'string', NULL, 'audit_property', NULL, 40, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'Review Q4 Controls Evidence', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000002', 'task.description', 'Task Description', 'Brief description of the task', 'string', NULL, 'audit_property', NULL, 41, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'Please review and upload the required evidence for SOC 2 controls.', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000003', 'task.due_date', 'Task Due Date', 'Due date of the task (human-readable)', 'string', NULL, 'audit_property', NULL, 42, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'April 15, 2026', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000004', 'task.url', 'Task URL', 'Direct URL to the task in K-Control', 'string', NULL, 'audit_property', NULL, 43, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'https://app.kcontrol.io/tasks/x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000005', 'task.status.new', 'Task New Status', 'The new status of the task after the change', 'string', NULL, 'audit_property', NULL, 44, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'In Review', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000006', 'task.status.previous', 'Task Previous Status', 'The previous status before the change', 'string', NULL, 'audit_property', NULL, 45, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'In Progress', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000007', 'task.priority', 'Task Priority', 'Priority level of the task (high, medium, low)', 'string', NULL, 'audit_property', NULL, 46, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'high', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000008', 'comment.body', 'Comment Body', 'The text content of the new comment', 'string', NULL, 'audit_property', NULL, 47, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'Please ensure the evidence covers the full audit period.', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-000000000009', 'comment.author', 'Comment Author', 'Display name of the person who added the comment', 'string', NULL, 'audit_property', NULL, 48, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'Sarah Chen', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-00000000000a', 'feedback.body', 'Feedback Body', 'The text content of the feedback', 'string', NULL, 'audit_property', NULL, 49, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'The evidence provided is incomplete. Please include the full policy document.', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-00000000000b', 'feedback.author', 'Feedback Author', 'Display name of the person who submitted the feedback', 'string', NULL, 'audit_property', NULL, 50, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'Alex Torres', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-00000000000c', 'feedback.type', 'Feedback Type', 'Type of feedback (approved, rejected, needs_revision)', 'string', NULL, 'audit_property', NULL, 51, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'needs_revision', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-00000000000d', 'task.control_name', 'Control Name', 'Name of the compliance control associated with the task', 'string', NULL, 'audit_property', NULL, 52, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'CC6.1 – Logical Access Controls', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0000-0040-00000000000e', 'task.framework', 'Framework', 'Compliance framework associated with this task', 'string', NULL, 'audit_property', NULL, 53, '2026-04-02T05:25:01.425182', '2026-04-02T05:25:01.425182', 'SOC 2 Type II', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000001', 'risk.title', 'Risk Title', 'Title of the risk', 'string', NULL, 'audit_property', NULL, 60, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Unauthorised Data Access', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000002', 'risk.severity', 'Risk Severity', 'Current severity level (critical/high/medium/low)', 'string', NULL, 'audit_property', NULL, 61, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'high', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000003', 'risk.status.new', 'Risk New Status', 'The new status after the transition', 'string', NULL, 'audit_property', NULL, 62, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'treating', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000004', 'risk.status.previous', 'Risk Previous Status', 'The previous status before the transition', 'string', NULL, 'audit_property', NULL, 63, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'assessed', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000005', 'risk.url', 'Risk URL', 'Direct link to the risk in K-Control', 'string', NULL, 'audit_property', NULL, 64, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'https://app.kcontrol.io/risks/x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000006', 'risk.review_date', 'Risk Review Date', 'Scheduled review date for the risk', 'string', NULL, 'audit_property', NULL, 65, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'April 30, 2026', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000007', 'treatment.title', 'Treatment Plan Title', 'Title of the risk treatment plan', 'string', NULL, 'audit_property', NULL, 66, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Implement MFA across all services', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000008', 'treatment.due_date', 'Treatment Due Date', 'Due date for the treatment plan', 'string', NULL, 'audit_property', NULL, 67, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'May 15, 2026', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000009', 'finding.title', 'Finding Title', 'Title of the audit finding', 'string', NULL, 'audit_property', NULL, 70, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Missing encryption at rest', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000000a', 'finding.severity', 'Finding Severity', 'Severity of the finding (critical/high/medium/low)', 'string', NULL, 'audit_property', NULL, 71, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'high', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000000b', 'finding.status.new', 'Finding New Status', 'The new status of the finding', 'string', NULL, 'audit_property', NULL, 72, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'auditor_review', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000000c', 'finding.url', 'Finding URL', 'Direct link to the finding', 'string', NULL, 'audit_property', NULL, 73, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'https://app.kcontrol.io/findings/x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000000d', 'finding.due_date', 'Finding Due Date', 'Due date for remediating the finding', 'string', NULL, 'audit_property', NULL, 74, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'April 20, 2026', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000000e', 'assessment.title', 'Assessment Title', 'Title of the assessment', 'string', NULL, 'audit_property', NULL, 80, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Q1 2026 SOC 2 Readiness Assessment', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000000f', 'assessment.url', 'Assessment URL', 'Direct link to the assessment', 'string', NULL, 'audit_property', NULL, 81, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'https://app.kcontrol.io/assessments/x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000010', 'engagement.title', 'Engagement Title', 'Title of the engagement', 'string', NULL, 'audit_property', NULL, 90, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Q4 2025 SOC 2 Type II Audit', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000011', 'engagement.status.new', 'Engagement New Status', 'The new status of the engagement', 'string', NULL, 'audit_property', NULL, 91, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'active', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000012', 'engagement.status.previous', 'Engagement Prev Status', 'The previous status of the engagement', 'string', NULL, 'audit_property', NULL, 92, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'setup', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000013', 'engagement.url', 'Engagement URL', 'Direct link to the engagement', 'string', NULL, 'audit_property', NULL, 93, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'https://app.kcontrol.io/engagements/x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000014', 'report.title', 'Report Title', 'Human-readable title of the generated report', 'string', NULL, 'audit_property', NULL, 100, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'SOC 2 Framework Compliance Report', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000015', 'report.type_label', 'Report Type Label', 'Human label for the report type', 'string', NULL, 'audit_property', NULL, 101, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Framework Compliance', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000016', 'report.url', 'Report URL', 'Direct link to view the report', 'string', NULL, 'audit_property', NULL, 102, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'https://app.kcontrol.io/reports/x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000017', 'report.error', 'Report Error', 'Error message if report generation failed', 'string', NULL, 'audit_property', NULL, 103, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'LLM rate limit exceeded', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000018', 'approval.title', 'Approval Title', 'Human-readable description of the action requiring approval', 'string', NULL, 'audit_property', NULL, 110, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Deploy compliance report to Slack', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000019', 'approval.agent_name', 'Agent Name', 'Name of the AI agent that triggered the approval', 'string', NULL, 'audit_property', NULL, 111, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Audit Copilot', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000001a', 'approval.action', 'Approval Action', 'Summary of the action to be approved or rejected', 'string', NULL, 'audit_property', NULL, 112, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Post report summary to #compliance channel', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000001b', 'approval.url', 'Approval URL', 'Direct link to the approval request', 'string', NULL, 'audit_property', NULL, 113, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'https://app.kcontrol.io/approvals/x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000001c', 'approval.expires_in', 'Approval Expires In', 'How long until the approval request expires', 'string', NULL, 'audit_property', NULL, 114, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', '24 hours', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000001d', 'ticket.title', 'Ticket Title', 'Title of the feedback/support ticket', 'string', NULL, 'audit_property', NULL, 120, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Dashboard not loading in Firefox', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000001e', 'ticket.status.new', 'Ticket New Status', 'The new status of the ticket', 'string', NULL, 'audit_property', NULL, 121, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'in_progress', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-00000000001f', 'ticket.url', 'Ticket URL', 'Direct link to the ticket', 'string', NULL, 'audit_property', NULL, 122, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'https://app.kcontrol.io/feedback/x', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000020', 'mention.entity_type', 'Mention Entity Type', 'Type of entity the comment is on (task, risk, control, etc)', 'string', NULL, 'audit_property', NULL, 130, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'task', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000021', 'mention.entity_title', 'Mention Entity Title', 'Title of the entity the comment is on', 'string', NULL, 'audit_property', NULL, 131, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'Review CC6.1 Evidence', NULL, NULL, NULL, FALSE),
      ('a0000000-0000-0001-0001-000000000022', 'mention.entity_url', 'Mention Entity URL', 'URL of the entity the comment is on', 'string', NULL, 'audit_property', NULL, 132, '2026-04-02T05:25:02.59766', '2026-04-02T05:25:02.59766', 'https://app.kcontrol.io/tasks/x', NULL, NULL, NULL, FALSE),
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
      ('b0000001-0000-0000-0000-000000000021', 'custom.org_detail.org_slug', 'Org Slug', 'Organization slug', 'string', 'acme-corp', 'custom_query', 'org_slug', 921, '2026-03-17T07:23:08.873429', '2026-03-17T07:23:08.873429', NULL, NULL, 'a0000001-0000-0000-0000-000000000003', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000022', 'custom.org_detail.org_type_name', 'Org Type', 'Organization type', 'string', 'Enterprise', 'custom_query', 'org_type_name', 922, '2026-03-17T07:23:08.873429', '2026-03-17T07:23:08.873429', NULL, NULL, 'a0000001-0000-0000-0000-000000000003', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000030', 'custom.workspace_detail.workspace_name', 'Workspace Name', 'Workspace name', 'string', 'Production', 'custom_query', 'workspace_name', 930, '2026-03-17T07:23:08.899592', '2026-03-17T07:23:08.899592', NULL, NULL, 'a0000001-0000-0000-0000-000000000004', NULL, FALSE),
      ('b0000001-0000-0000-0000-000000000031', 'custom.workspace_detail.workspace_slug', 'Workspace Slug', 'Workspace slug', 'string', 'production', 'custom_query', 'workspace_slug', 931, '2026-03-17T07:23:08.899592', '2026-03-17T07:23:08.899592', NULL, NULL, 'a0000001-0000-0000-0000-000000000004', NULL, FALSE),
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

-- 03_notifications.10_fct_templates (62 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."10_fct_templates" (id, tenant_key, code, name, description, notification_type_code, channel_code, active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by, org_id, static_variables, category_code)
  VALUES
      ('05ce66bd-4de3-4ed7-960e-7968707f13e7', 'default', 'global_broadcast_push', 'Global Broadcast (Push)', 'Web push notification for platform-wide announcements.', 'global_broadcast', 'web_push', '9b2d816d-58df-4e53-8307-3869912d8582', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.963173', '2026-03-19T16:58:13.963173', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('1e421cc5-a30e-4d4e-ad1b-9ffb22f089de', 'default', 'magic_link_login_email', 'Magic Link Login', 'Sends a magic link for passwordless login to K-Control.', 'magic_link_login', 'email', '1073e024-0aa3-4251-a7fa-27e5e057cf93', NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T03:59:06.53042', '2026-03-20T04:00:55.533539', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('20857b4a-9a1d-4289-a8e4-48e073dc0e14', 'default', 'email_verification_push', 'Email Verification (Push)', 'Web push notification sent to verify email address.', 'email_verification', 'web_push', '6d276a23-df1e-4551-a2f2-fcb7e233897b', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.851129', '2026-03-19T16:58:13.851129', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('215527d2-80b1-4c88-bb80-3fdef4ce4cce', '__system__', 'magic_link_login_email', 'Magic Link Login', 'Sends a magic link for passwordless login.', 'magic_link_login', 'email', 'd31a263a-3bcd-41b8-8ac9-4bbf071f2f0a', NULL, TRUE, FALSE, TRUE, FALSE, TRUE, FALSE, '2026-03-20T03:54:34.804901', '2026-03-20T03:54:34.804901', NULL, NULL, '2026-04-02T05:37:20.649162', NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('3fabf1eb-e2a0-4840-90b6-2c65a5c7f46e', 'default', 'org_invite_push', 'Organisation Invite (Push)', 'Web push notification when user is invited to an organisation.', 'org_invite_received', 'web_push', '5f88991e-c662-4601-b6a8-8084f58008d2', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.908043', '2026-03-19T16:58:13.908043', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('526384b1-01d6-4692-85cb-8499b1abbbd5', 'default', 'org_invite', 'Organisation Invite', 'Sent when a user is invited to join an organisation.', 'org_invite_received', 'email', '79bd9a11-262a-4045-a498-87b98c5b9819', NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('5a84c59c-21d0-4222-9918-490bb199e0f9', 'default', 'workspace_invite', 'Workspace Invite', 'Sent when a user is added to a workspace.', 'workspace_invite_received', 'email', 'f1e14cc0-2ecc-4e12-a6d7-cc2623f2acca', NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('604ac4e4-e077-43a6-a52a-27b5bbb5d812', 'default', 'email_verification_otp', 'Email Verification OTP', 'Sends a 6-digit OTP code for email verification during onboarding.', 'email_verification', 'email', '5168135d-38b5-4e9b-88e7-b84fad17dbab', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-20T03:39:16.958811', '2026-04-02T05:25:00.748102', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('7f463634-6068-422d-9353-36983e8b919e', 'default', 'email_verification', 'Email Verification', 'Sent to verify a user email address after registration.', 'email_verification', 'email', '4585763e-2a1e-4d56-b97e-3458da7940a1', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('8166a55f-00bd-402c-a334-eb3cb702201c', 'default', 'workspace_invite_push', 'Workspace Invite (Push)', 'Web push notification when user is added to a workspace.', 'workspace_invite_received', 'web_push', '973573db-4797-44d8-ba62-46684434daa8', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.93531', '2026-03-19T16:58:13.93531', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('97ba7258-78b0-4a60-bf6d-9be6a29b5b81', 'default', 'login_new_device_push', 'New Device Login (Push)', 'Security alert when login is detected from a new device.', 'login_from_new_device', 'web_push', 'd61dc5de-f549-46c3-a141-7077a70f9726', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.880004', '2026-03-19T16:58:13.880004', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('a2334b60-0a9f-4405-83ca-fcbb79075124', 'default', 'login_new_device', 'Login From New Device', 'Security alert when a login is detected from an unrecognised device or location.', 'login_from_new_device', 'email', '1022bd6e-3915-4f33-9e43-8e1b332f85ad', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('ae6458b1-5689-4bab-bcd0-2fc947cc3683', 'default', 'global_broadcast', 'Global Broadcast', 'General-purpose broadcast template for platform-wide announcements to all users.', 'global_broadcast', 'email', '31194a33-26e8-4d16-ba0c-9b123d7a4bae', NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('c02db7ba-9dec-4a4a-bcd5-d359d3c6dcf5', 'default', 'password_reset', 'Password Reset', 'Sent when a user requests a password reset link.', 'password_reset', 'email', '09e93b99-2799-4309-9854-1d6fb03fd2bf', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-16T11:07:36.838409', '2026-03-16T11:07:36.838409', 'b8896539-d8c0-4386-907e-0f343abcbdc9', NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('dad0f7a3-5c67-4211-8acb-e6e73a008b49', 'default', 'password_reset_push', 'Password Reset (Push)', 'Web push notification sent when a password reset is requested.', 'password_reset', 'web_push', '55d7f8c5-e13a-4ca6-a99c-f54806210187', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-19T16:58:13.821413', '2026-03-19T16:58:13.821413', NULL, NULL, NULL, NULL, NULL, '{}'::jsonb, NULL),
      ('e1000000-0000-0000-0000-000000000001', 'default', 'workspace_invite_email', 'Workspace Invitation Email', 'Sent when a user is invited to join a workspace', 'workspace_invite_received', 'email', 'e1000000-0000-0000-0000-000000000003', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T05:29:14.833143', '2026-04-02T05:25:00.533824', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e1000000-0000-0000-0000-000000000010', 'default', 'workspace_invite_grc_email', 'GRC Workspace Invitation Email', 'Sent when a user is invited to a workspace with a GRC role (auditor, lead, etc.)', 'workspace_invite_grc', 'email', 'e1000000-0000-0000-0000-000000000012', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T05:29:14.833143', '2026-04-02T05:25:00.673287', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e1000000-0000-0000-0000-000000000020', 'default', 'engagement_access_granted_email', 'Engagement Access Granted Email', 'Sent when an auditor is granted access to a specific audit engagement', 'engagement_access_granted', 'email', 'e1000000-0000-0000-0000-000000000022', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-31T05:29:14.833143', '2026-04-02T05:25:00.721459', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e2000000-0000-0000-0000-000000000001', 'default', 'magic_link_assignee_email', 'Magic Link — Assignee Portal', 'Passwordless login link sent to task assignees for one-click portal access', 'magic_link_assignee', 'email', 'e2000000-0000-0000-0000-000000000002', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-01T10:45:13.564116', '2026-04-01T10:45:13.564116', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000001', 'default', 'password_reset_email', 'Password Reset Email', 'Sent when a user requests a password reset link', 'password_reset', 'email', 'e3000000-0000-0000-0000-000000000002', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000010', 'default', 'password_changed_email', 'Password Changed Email', 'Sent to confirm a user''s password was successfully changed', 'password_changed', 'email', 'e3000000-0000-0000-0000-000000000011', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000020', 'default', 'login_new_device_email', 'Login From New Device Email', 'Security alert sent when a user logs in from an unrecognised device or location', 'login_from_new_device', 'email', 'e3000000-0000-0000-0000-000000000021', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000030', 'default', 'api_key_created_email', 'API Key Created Email', 'Sent when a new API key is created for the user''s account', 'api_key_created', 'email', 'e3000000-0000-0000-0000-000000000031', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000040', 'default', 'email_verified_email', 'Email Verified Confirmation', 'Sent to confirm that the user''s email address has been successfully verified', 'email_verified', 'email', 'e3000000-0000-0000-0000-000000000041', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000050', 'default', 'org_invite_email', 'Organisation Invitation Email', 'Sent when a user is invited to join an organisation', 'org_invite_received', 'email', 'e3000000-0000-0000-0000-000000000051', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000060', 'default', 'org_member_added_email', 'Organisation Member Added Email', 'Sent to confirm a user has joined an organisation', 'org_member_added', 'email', 'e3000000-0000-0000-0000-000000000061', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000070', 'default', 'org_member_removed_email', 'Organisation Member Removed Email', 'Sent to notify a user that they have been removed from an organisation', 'org_member_removed', 'email', 'e3000000-0000-0000-0000-000000000071', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000080', 'default', 'workspace_member_added_email', 'Workspace Member Added Email', 'Sent to confirm a user has been added to a workspace', 'workspace_member_added', 'email', 'e3000000-0000-0000-0000-000000000081', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-000000000090', 'default', 'workspace_member_removed_email', 'Workspace Member Removed Email', 'Sent to notify a user that they have been removed from a workspace', 'workspace_member_removed', 'email', 'e3000000-0000-0000-0000-000000000091', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-0000000000a0', 'default', 'role_changed_email', 'Role Changed Email', 'Sent when a user''s role or permissions are changed', 'role_changed', 'email', 'e3000000-0000-0000-0000-0000000000a1', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-0000000000b0', 'default', 'inactivity_reminder_email', 'Inactivity Reminder Email', 'Sent to re-engage users who have been inactive for a configurable period', 'inactivity_reminder', 'email', 'e3000000-0000-0000-0000-0000000000b1', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-0000000000c0', 'default', 'platform_release_email', 'Platform Release Email', 'Sent to announce a new platform release to users', 'platform_release', 'email', 'e3000000-0000-0000-0000-0000000000c1', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-0000000000d0', 'default', 'platform_incident_email', 'Platform Incident Email', 'Sent to notify users of a platform incident or service disruption', 'platform_incident', 'email', 'e3000000-0000-0000-0000-0000000000d1', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e3000000-0000-0000-0000-0000000000e0', 'default', 'platform_maintenance_email', 'Platform Maintenance Email', 'Sent to notify users of planned platform maintenance windows', 'platform_maintenance', 'email', 'e3000000-0000-0000-0000-0000000000e1', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.106718', '2026-04-02T05:25:01.106718', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e4000000-0000-0000-0000-000000000001', 'default', 'task_assigned_email', 'Task Assigned Email', 'Sent when a compliance task is assigned to a user', 'task_assigned', 'email', 'e4000000-0000-0000-0000-000000000002', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.465256', '2026-04-02T05:25:01.465256', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e4000000-0000-0000-0000-000000000010', 'default', 'task_status_changed_email', 'Task Status Changed Email', 'Sent when the status of a task changes', 'task_status_changed', 'email', 'e4000000-0000-0000-0000-000000000011', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.465256', '2026-04-02T05:25:01.465256', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e4000000-0000-0000-0000-000000000020', 'default', 'task_comment_added_email', 'Task Comment Added Email', 'Sent when a new comment is added to a task the user is involved with', 'task_comment_added', 'email', 'e4000000-0000-0000-0000-000000000021', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.465256', '2026-04-02T05:25:01.465256', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e4000000-0000-0000-0000-000000000030', 'default', 'task_feedback_received_email', 'Task Feedback Received Email', 'Sent when feedback is submitted on a task or control evidence', 'task_feedback_received', 'email', 'e4000000-0000-0000-0000-000000000031', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:25:01.465256', '2026-04-02T05:25:01.465256', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000001', 'default', 'task_reassigned_email', 'Task Reassigned Email', 'Sent to the new assignee when a task is reassigned to them.', 'task_reassigned', 'email', '8bd414f8-b0d6-4140-b4a7-7f13327d79bb', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000002', 'default', 'task_overdue_email', 'Task Overdue Email', 'Sent to the assignee when a task passes its due date without being completed.', 'task_overdue', 'email', 'b38168bb-7d46-40fd-a11d-21452527b4c3', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000003', 'default', 'task_submitted_email', 'Task Submitted for Review Email', 'Sent to reviewers when a task is moved to pending_verification status.', 'task_submitted', 'email', 'b78d3e38-39ea-4121-8b3a-7acb53d22f74', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000004', 'default', 'task_approved_email', 'Task Approved Email', 'Sent to the assignee when their task is approved and published.', 'task_approved', 'email', '5db54288-768c-46ed-b462-d29d7a3a2baf', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000005', 'default', 'task_rejected_email', 'Task Sent Back Email', 'Sent to the assignee when their task is rejected and sent back for revision.', 'task_rejected', 'email', '588fc527-acca-4ec7-810a-d837af13f465', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000010', 'default', 'comment_mention_email', 'Mentioned in Comment Email', 'Sent when a user is @-mentioned in a comment.', 'comment_mention', 'email', '1d93913d-c620-44fc-863e-57124369e872', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000011', 'default', 'comment_reply_email', 'Reply to Your Comment Email', 'Sent when someone replies to your comment.', 'comment_reply', 'email', '6a21320c-3ac0-413c-ba22-f485bb9ca31f', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000020', 'default', 'risk_assigned_email', 'Risk Assigned Email', 'Sent when a risk is assigned to a user as owner.', 'risk_assigned', 'email', 'e17ab86d-b88e-48ff-bd72-e3bbba51bb3f', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000021', 'default', 'risk_review_due_email', 'Risk Review Due Email', 'Sent when a risk is approaching its scheduled review date.', 'risk_review_due', 'email', '0ba0d825-bf4e-4638-b64b-b4a9f5b6f354', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000022', 'default', 'risk_status_changed_email', 'Risk Status Changed Email', 'Sent to the risk owner when a risk status changes.', 'risk_status_changed', 'email', '111b1080-5079-40f6-952a-6f77dd387081', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000023', 'default', 'treatment_plan_assigned_email', 'Treatment Plan Assigned Email', 'Sent to the treatment owner when a treatment plan is created and assigned.', 'treatment_plan_assigned', 'email', '6fa33635-6d7a-4464-b244-f66bffaffe64', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000030', 'default', 'finding_assigned_email', 'Finding Assigned Email', 'Sent when an audit finding is assigned to a user for remediation.', 'finding_assigned', 'email', '480cd303-f638-4c8f-95da-2b702402fbcc', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000031', 'default', 'finding_response_needed_email', 'Finding Response Needed Email', 'Sent to prompt the assignee to respond to a finding in auditor_review status.', 'finding_response_needed', 'email', 'cac34588-1ba3-4222-8116-a47aa9336131', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000032', 'default', 'finding_reviewed_email', 'Finding Reviewed Email', 'Sent to the finding owner after an auditor reviews and closes or escalates a finding.', 'finding_reviewed', 'email', 'e48e14b4-22d8-4d0c-b5e3-f18929dacab8', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:40.953733', '2026-04-02T05:33:40.953733', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000040', 'default', 'assessment_completed_email', 'Assessment Completed Email', 'Sent when an assessment reaches completed status.', 'assessment_completed', 'email', 'ceb347ef-696e-428a-904a-56e1e4bbdb6a', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000050', 'default', 'engagement_status_changed_email', 'Engagement Status Changed Email', 'Sent to engagement participants when the engagement moves to a new phase.', 'engagement_status_changed', 'email', '3a4caf06-1f98-4235-bf47-7000f390c8ce', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000060', 'default', 'report_ready_email', 'Report Ready Email', 'Sent when an AI-generated report has completed and is ready to view.', 'report_ready', 'email', 'a97728b4-4252-4ff6-8d8b-02a657cf6738', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000061', 'default', 'report_failed_email', 'Report Failed Email', 'Sent when report generation fails so the user can retry.', 'report_failed', 'email', 'd9a69b23-96a9-4b3a-bf5e-9c41f52ab2fa', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000070', 'default', 'approval_required_email', 'Approval Required Email', 'Sent to the designated approver when an AI agent action requires human approval.', 'approval_required', 'email', 'bdd463cb-ca6f-44ed-bf43-48b2e77cf776', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000071', 'default', 'approval_expired_email', 'Approval Request Expired Email', 'Sent to the requester when an approval times out without a response.', 'approval_expired', 'email', '9b9c7052-bb08-4e38-bb7b-81b270ac8e28', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000072', 'default', 'approval_rejected_email', 'Approval Rejected Email', 'Sent to the requester when their AI approval request is rejected by the approver.', 'approval_rejected', 'email', '9532de61-9776-4bcb-9c83-fa184936422f', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000080', 'default', 'ticket_assigned_email', 'Feedback Ticket Assigned Email', 'Sent when a feedback/support ticket is assigned to a user.', 'ticket_assigned', 'email', '7a788be3-f3f6-48f5-bb9b-7f42a4434ff9', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('e5000000-0000-0000-0001-000000000081', 'default', 'ticket_status_changed_email', 'Ticket Status Changed Email', 'Sent to the ticket submitter when the status of their ticket changes.', 'ticket_status_changed', 'email', '6f8439a8-c390-4c6f-8f25-79fce67cf2d5', NULL, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-04-02T05:33:48.690335', '2026-04-02T05:33:48.690335', NULL, NULL, NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL),
      ('ed091f63-43a7-48d6-91c4-11d415798d27', 'default', 'otp_verification_email', 'OTP Verification Email', 'Sends a 6-digit OTP code for email verification during onboarding.', 'email_verification', 'email', '570d371b-88c7-4cb6-8dc5-011bb25a4df5', NULL, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T03:56:30.428274', '2026-03-20T03:58:24.425429', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL, NULL, '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb, NULL)
  ON CONFLICT (tenant_key, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, notification_type_code = EXCLUDED.notification_type_code, channel_code = EXCLUDED.channel_code, active_version_id = EXCLUDED.active_version_id, base_template_id = EXCLUDED.base_template_id, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by, org_id = EXCLUDED.org_id, static_variables = EXCLUDED.static_variables, category_code = EXCLUDED.category_code;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.14_dtl_template_versions (67 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."14_dtl_template_versions" (id, template_id, version_number, subject_line, body_html, body_text, body_short, metadata_json, change_notes, is_active, created_at, created_by)
  VALUES
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
      ('0ba0d825-bf4e-4638-b64b-b4a9f5b6f354', 'e5000000-0000-0000-0001-000000000021', 1, 'Risk Review Due: {{ risk.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Risk Review Due</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Risk Review Due Soon</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">A risk you own is scheduled for review soon. Please assess the current risk status and update the treatment plan if necessary.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Review Reminder</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ risk.title | default(''Untitled Risk'') }}</p>
            {% if risk.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Severity: <strong>{{ risk.severity }}</strong></p>{% endif %}
            {% if risk.status %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Current Status: {{ risk.status }}</p>{% endif %}
            {% if risk.review_date %}<p style="margin:0;font-size:13px;color:#92400e;font-weight:600;">Review due: {{ risk.review_date }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ risk.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Review Risk</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this scheduled reminder because you are the risk owner in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Risk Review Due Soon

Hi {{ user.first_name | default(''there'') }},

A risk you own is scheduled for review soon. Please assess the current status and update the treatment plan if necessary.

REVIEW REMINDER
Title: {{ risk.title | default(''Untitled Risk'') }}
{% if risk.severity %}Severity: {{ risk.severity }}{% endif %}
{% if risk.status %}Current Status: {{ risk.status }}{% endif %}
{% if risk.review_date %}Review due: {{ risk.review_date }}{% endif %}

Review the risk: {{ risk.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this scheduled reminder because you are the risk owner.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
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
      ('111b1080-5079-40f6-952a-6f77dd387081', 'e5000000-0000-0000-0001-000000000022', 1, 'Risk Status Updated: {{ risk.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Risk Status Updated</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Risk Status Updated</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">The status of a risk you own has been updated.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Status Change</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ risk.title | default(''Untitled Risk'') }}</p>
            {% if risk.status.previous and risk.status.new %}
            <p style="margin:0 0 4px;font-size:13px;color:#64748b;">
              <span style="color:#64748b;">{{ risk.status.previous }}</span>
              <span style="color:#94a3b8;margin:0 6px;">→</span>
              <strong style="color:#1e293b;">{{ risk.status.new }}</strong>
            </p>
            {% elif risk.status.new %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">New status: <strong>{{ risk.status.new }}</strong></p>{% endif %}
            {% if risk.severity %}<p style="margin:0;font-size:13px;color:#64748b;">Severity: {{ risk.severity }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ risk.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Risk</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are the owner of this risk in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Risk Status Updated

Hi {{ user.first_name | default(''there'') }},

The status of a risk you own has been updated.

STATUS CHANGE
Title: {{ risk.title | default(''Untitled Risk'') }}
{% if risk.status.previous and risk.status.new %}{{ risk.status.previous }} → {{ risk.status.new }}{% elif risk.status.new %}New status: {{ risk.status.new }}{% endif %}
{% if risk.severity %}Severity: {{ risk.severity }}{% endif %}

View the risk: {{ risk.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you are the owner of this risk.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('179057a7-8563-4bba-aa03-a720c856ec2e', '604ac4e4-e077-43a6-a52a-27b5bbb5d812', 2, 'Your Verification Code — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Email Verification</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Use the verification code below to complete your email verification. This code expires in <strong>5 minutes</strong>.</p>
      </div>
      <div style="text-align:center;margin:28px 0;">
        <div style="display:inline-block;background:#eaf3fb;color:#295cf6;border-radius:10px;padding:18px 48px;font-size:2em;font-weight:700;letter-spacing:0.15em;">{{ otp_code }}</div>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This code expires in 5 minutes.</strong> If you did not request this code, you can safely ignore this email.
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

Your K-Control verification code is:

{{ otp_code }}

This code expires in 5 minutes. If you did not request this, ignore this email.

Best regards,
Kreesalis Team', 'Your verification code: {{ otp_code }}', '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', TRUE, '2026-04-02T05:24:17.675032', NULL),
      ('1d93913d-c620-44fc-863e-57124369e872', 'e5000000-0000-0000-0001-000000000010', 1, '{{ comment.author | default(''Someone'') }} mentioned you in a comment', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>You Were Mentioned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">You Were Mentioned</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;"><strong>{{ comment.author | default(''A team member'') }}</strong> mentioned you in a comment{% if task.title %} on <strong>{{ task.title }}</strong>{% endif %}.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Comment</p>
            <p style="margin:0;font-size:15px;color:#1e293b;line-height:1.6;font-style:italic;">"{{ comment.body | default('''') }}"</p>
            {% if comment.author %}<p style="margin:8px 0 0;font-size:13px;color:#64748b;">— {{ comment.author }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Comment</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you were @-mentioned. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'You Were Mentioned

Hi {{ user.first_name | default(''there'') }},

{{ comment.author | default(''A team member'') }} mentioned you in a comment{% if task.title %} on {{ task.title }}{% endif %}.

COMMENT
"{{ comment.body | default('''') }}"
{% if comment.author %}— {{ comment.author }}{% endif %}

View the comment: {{ task.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you were @-mentioned. To manage your notification preferences, visit your account settings.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
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
      ('3a4caf06-1f98-4235-bf47-7000f390c8ce', 'e5000000-0000-0000-0001-000000000050', 1, 'Engagement Update: {{ engagement.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Engagement Update</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Engagement Phase Updated</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An engagement you are participating in has moved to a new phase.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Phase Update</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ engagement.title | default(''Untitled Engagement'') }}</p>
            {% if engagement.status.previous and engagement.status.new %}
            <p style="margin:0 0 4px;font-size:13px;color:#64748b;">
              <span style="color:#64748b;">{{ engagement.status.previous }}</span>
              <span style="color:#94a3b8;margin:0 6px;">→</span>
              <strong style="color:#1e293b;">{{ engagement.status.new }}</strong>
            </p>
            {% elif engagement.status.new %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">New phase: <strong>{{ engagement.status.new }}</strong></p>{% endif %}
            {% if engagement.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Target completion: <strong>{{ engagement.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ engagement.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Engagement</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are a participant in this engagement in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Engagement Phase Updated

Hi {{ user.first_name | default(''there'') }},

An engagement you are participating in has moved to a new phase.

PHASE UPDATE
Title: {{ engagement.title | default(''Untitled Engagement'') }}
{% if engagement.status.previous and engagement.status.new %}{{ engagement.status.previous }} → {{ engagement.status.new }}{% elif engagement.status.new %}New phase: {{ engagement.status.new }}{% endif %}
{% if engagement.due_date %}Target completion: {{ engagement.due_date }}{% endif %}

View the engagement: {{ engagement.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you are a participant in this engagement.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
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
      ('480cd303-f638-4c8f-95da-2b702402fbcc', 'e5000000-0000-0000-0001-000000000030', 1, 'Audit Finding Assigned: {{ finding.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Finding Assigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Audit Finding Assigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An audit finding has been assigned to you for remediation. Please review the finding and provide a response within the required timeframe.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Finding Details</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ finding.title | default(''Untitled Finding'') }}</p>
            {% if finding.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Severity: <strong>{{ finding.severity }}</strong></p>{% endif %}
            {% if finding.status %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Status: {{ finding.status }}</p>{% endif %}
            {% if finding.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Response due: <strong>{{ finding.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if finding.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ finding.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ finding.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Finding</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you were assigned to remediate this finding in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Audit Finding Assigned to You

Hi {{ user.first_name | default(''there'') }},

An audit finding has been assigned to you for remediation.

FINDING DETAILS
Title: {{ finding.title | default(''Untitled Finding'') }}
{% if finding.severity %}Severity: {{ finding.severity }}{% endif %}
{% if finding.status %}Status: {{ finding.status }}{% endif %}
{% if finding.due_date %}Response due: {{ finding.due_date }}{% endif %}
{% if finding.description %}
{{ finding.description }}
{% endif %}

View the finding: {{ finding.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you were assigned to remediate this finding.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('5168135d-38b5-4e9b-88e7-b84fad17dbab', '604ac4e4-e077-43a6-a52a-27b5bbb5d812', 3, 'Your Verification Code — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Email Verification</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Use the verification code below to complete your email verification. This code expires in <strong>5 minutes</strong>.</p>
      </div>
      <div style="text-align:center;margin:28px 0;">
        <div style="display:inline-block;background:#eaf3fb;color:#295cf6;border-radius:10px;padding:18px 48px;font-size:2em;font-weight:700;letter-spacing:0.15em;">{{ otp_code }}</div>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This code expires in 5 minutes.</strong> If you did not request this code, you can safely ignore this email.
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

Your K-Control verification code is:

{{ otp_code }}

This code expires in 5 minutes. If you did not request this, ignore this email.

Best regards,
Kreesalis Team', 'Your verification code: {{ otp_code }}', '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', TRUE, '2026-04-02T05:25:00.748102', NULL),
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
      ('588fc527-acca-4ec7-810a-d837af13f465', 'e5000000-0000-0000-0001-000000000005', 1, 'Task Sent Back for Revision: {{ task.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Sent Back</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Sent Back for Revision</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Your task has been reviewed and sent back for revision. Please review the feedback below and update your submission.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Needs Revision</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default(''Untitled Task'') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
            {% if task.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Due: <strong>{{ task.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if feedback.body %}
        <div style="background:#f8fafc;border-radius:6px;padding:16px 20px;margin:0 0 24px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;">Reviewer Feedback</p>
          <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">{{ feedback.body }}</p>
          {% if feedback.author %}<p style="margin:8px 0 0;font-size:12px;color:#94a3b8;">— {{ feedback.author }}</p>{% endif %}
        </div>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Update Task</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because your task submission was returned for revision in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Task Sent Back for Revision

Hi {{ user.first_name | default(''there'') }},

Your task has been reviewed and sent back for revision. Please review the feedback and update your submission.

NEEDS REVISION
Title: {{ task.title | default(''Untitled Task'') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}
{% if task.due_date %}Due: {{ task.due_date }}{% endif %}

{% if feedback.body %}
REVIEWER FEEDBACK
{{ feedback.body }}
{% if feedback.author %}— {{ feedback.author }}{% endif %}
{% endif %}

Update the task: {{ task.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This notification was sent because your task submission was returned for revision.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('5db54288-768c-46ed-b462-d29d7a3a2baf', 'e5000000-0000-0000-0001-000000000004', 1, 'Task Approved: {{ task.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Approved</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Approved</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Great news — your task has been reviewed and approved. The evidence has been accepted and the task is now published.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border-left:4px solid #22c55e;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#166534;text-transform:uppercase;letter-spacing:0.05em;">Approved</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default(''Untitled Task'') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Task</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because your task was reviewed and approved in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Task Approved

Hi {{ user.first_name | default(''there'') }},

Great news — your task has been reviewed and approved. The evidence has been accepted and the task is now published.

APPROVED
Title: {{ task.title | default(''Untitled Task'') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}

View the task: {{ task.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This notification was sent because your task was reviewed and approved.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('5f88991e-c662-4601-b6a8-8084f58008d2', '3fabf1eb-e2a0-4840-90b6-2c65a5c7f46e', 1, 'You have been invited to an organisation', NULL, 'You have been invited to join an organisation on K-Control.', 'You have a new organisation invitation. Tap to view.', NULL, NULL, TRUE, '2026-03-19T16:58:13.908043', NULL),
      ('6a21320c-3ac0-413c-ba22-f485bb9ca31f', 'e5000000-0000-0000-0001-000000000011', 1, '{{ comment.author | default(''Someone'') }} replied to your comment', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>New Reply</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">New Reply to Your Comment</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;"><strong>{{ comment.author | default(''A team member'') }}</strong> replied to your comment{% if task.title %} on <strong>{{ task.title }}</strong>{% endif %}.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Reply</p>
            <p style="margin:0;font-size:15px;color:#1e293b;line-height:1.6;font-style:italic;">"{{ comment.body | default('''') }}"</p>
            {% if comment.author %}<p style="margin:8px 0 0;font-size:13px;color:#64748b;">— {{ comment.author }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Conversation</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because someone replied to your comment. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'New Reply to Your Comment

Hi {{ user.first_name | default(''there'') }},

{{ comment.author | default(''A team member'') }} replied to your comment{% if task.title %} on {{ task.title }}{% endif %}.

REPLY
"{{ comment.body | default('''') }}"
{% if comment.author %}— {{ comment.author }}{% endif %}

View the conversation: {{ task.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because someone replied to your comment.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('6d276a23-df1e-4551-a2f2-fcb7e233897b', '20857b4a-9a1d-4289-a8e4-48e073dc0e14', 1, 'Verify Your Email', NULL, 'Click the link to verify your email address.', 'Please verify your email address. Tap to open.', NULL, NULL, TRUE, '2026-03-19T16:58:13.851129', NULL),
      ('6f8439a8-c390-4c6f-8f25-79fce67cf2d5', 'e5000000-0000-0000-0001-000000000081', 1, 'Update on Your Ticket: {{ ticket.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ticket Updated</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Your Ticket Has Been Updated</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">There has been an update to your support ticket. Please review the latest status below.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Status Update</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ ticket.title | default(''Untitled Ticket'') }}</p>
            {% if ticket.status.previous and ticket.status.new %}
            <p style="margin:0 0 4px;font-size:13px;color:#64748b;">
              <span style="color:#64748b;">{{ ticket.status.previous }}</span>
              <span style="color:#94a3b8;margin:0 6px;">→</span>
              <strong style="color:#1e293b;">{{ ticket.status.new }}</strong>
            </p>
            {% elif ticket.status.new %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Status: <strong>{{ ticket.status.new }}</strong></p>{% endif %}
            {% if ticket.assignee %}<p style="margin:0;font-size:13px;color:#64748b;">Assigned to: {{ ticket.assignee }}</p>{% endif %}
          </td></tr>
        </table>
        {% if comment.body %}
        <div style="background:#f8fafc;border-radius:6px;padding:16px 20px;margin:0 0 24px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;">Update Note</p>
          <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">{{ comment.body }}</p>
          {% if comment.author %}<p style="margin:8px 0 0;font-size:12px;color:#94a3b8;">— {{ comment.author }}</p>{% endif %}
        </div>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ ticket.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Ticket</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you submitted this ticket in {{ platform.name | default(''K-Control'') }}. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Your Ticket Has Been Updated

Hi {{ user.first_name | default(''there'') }},

There has been an update to your support ticket.

STATUS UPDATE
Title: {{ ticket.title | default(''Untitled Ticket'') }}
{% if ticket.status.previous and ticket.status.new %}{{ ticket.status.previous }} → {{ ticket.status.new }}{% elif ticket.status.new %}Status: {{ ticket.status.new }}{% endif %}
{% if ticket.assignee %}Assigned to: {{ ticket.assignee }}{% endif %}

{% if comment.body %}
UPDATE NOTE
{{ comment.body }}
{% if comment.author %}— {{ comment.author }}{% endif %}
{% endif %}

View the ticket: {{ ticket.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you submitted this ticket.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
      ('6fa33635-6d7a-4464-b244-f66bffaffe64', 'e5000000-0000-0000-0001-000000000023', 1, 'Treatment Plan Assigned: {{ risk.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Treatment Plan Assigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Treatment Plan Assigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">You have been assigned as the owner of a risk treatment plan. Please review the treatment details and begin implementing the required controls.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Treatment Plan</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ treatment.title | default(''Treatment Plan'') }}</p>
            <p style="margin:0 0 4px;font-size:13px;color:#64748b;">Risk: {{ risk.title | default(''Untitled Risk'') }}</p>
            {% if risk.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Risk Severity: <strong>{{ risk.severity }}</strong></p>{% endif %}
            {% if treatment.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Target date: <strong>{{ treatment.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if treatment.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ treatment.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ risk.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Treatment Plan</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you were assigned as the treatment owner in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Treatment Plan Assigned to You

Hi {{ user.first_name | default(''there'') }},

You have been assigned as the owner of a risk treatment plan.

TREATMENT PLAN
Title: {{ treatment.title | default(''Treatment Plan'') }}
Risk: {{ risk.title | default(''Untitled Risk'') }}
{% if risk.severity %}Risk Severity: {{ risk.severity }}{% endif %}
{% if treatment.due_date %}Target date: {{ treatment.due_date }}{% endif %}
{% if treatment.description %}
{{ treatment.description }}
{% endif %}

View the treatment plan: {{ risk.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you were assigned as the treatment owner.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
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
      ('7a788be3-f3f6-48f5-bb9b-7f42a4434ff9', 'e5000000-0000-0000-0001-000000000080', 1, 'Support Ticket Assigned: {{ ticket.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ticket Assigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Support Ticket Assigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">A support ticket has been assigned to you. Please review the details and respond to the submitter.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Ticket Details</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ ticket.title | default(''Untitled Ticket'') }}</p>
            {% if ticket.type %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Type: {{ ticket.type }}</p>{% endif %}
            {% if ticket.priority %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Priority: <strong>{{ ticket.priority }}</strong></p>{% endif %}
            {% if ticket.submitted_by %}<p style="margin:0;font-size:13px;color:#64748b;">Submitted by: {{ ticket.submitted_by }}</p>{% endif %}
          </td></tr>
        </table>
        {% if ticket.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ ticket.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ ticket.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Ticket</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because a support ticket was assigned to you in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Support Ticket Assigned to You

Hi {{ user.first_name | default(''there'') }},

A support ticket has been assigned to you. Please review the details and respond to the submitter.

TICKET DETAILS
Title: {{ ticket.title | default(''Untitled Ticket'') }}
{% if ticket.type %}Type: {{ ticket.type }}{% endif %}
{% if ticket.priority %}Priority: {{ ticket.priority }}{% endif %}
{% if ticket.submitted_by %}Submitted by: {{ ticket.submitted_by }}{% endif %}
{% if ticket.description %}
{{ ticket.description }}
{% endif %}

View the ticket: {{ ticket.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because a support ticket was assigned to you.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
      ('8bd414f8-b0d6-4140-b4a7-7f13327d79bb', 'e5000000-0000-0000-0001-000000000001', 1, 'Task Reassigned: {{ task.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Reassigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Reassigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">A task has been reassigned to you. Please review the details below and take action before the due date.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Task Details</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default(''Untitled Task'') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
            {% if task.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Due: <strong>{{ task.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if task.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ task.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Task</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because a task was assigned to your account. If you believe this is an error, please contact <a href="mailto:{{ platform.support_email | default(''support@kcontrol.io'') }}" style="color:#295cf6;text-decoration:none;">{{ platform.support_email | default(''support@kcontrol.io'') }}</a>.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Task Reassigned to You

Hi {{ user.first_name | default(''there'') }},

A task has been reassigned to you. Please review the details and take action before the due date.

TASK DETAILS
Title: {{ task.title | default(''Untitled Task'') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}
{% if task.due_date %}Due: {{ task.due_date }}{% endif %}
{% if task.description %}
{{ task.description }}
{% endif %}

View the task: {{ task.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This notification was sent because a task was assigned to your account.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('9532de61-9776-4bcb-9c83-fa184936422f', 'e5000000-0000-0000-0001-000000000072', 1, 'Approval Rejected', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Approval Rejected</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Approval Rejected</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Your AI agent approval request has been rejected. The agent has been paused. Review the reason below and adjust the configuration before resubmitting.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Rejected</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ approval.action | default(''AI Agent Action'') }}</p>
            {% if approval.agent %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Agent: {{ approval.agent }}</p>{% endif %}
            {% if approval.rejected_by %}<p style="margin:0;font-size:13px;color:#64748b;">Rejected by: {{ approval.rejected_by }}</p>{% endif %}
          </td></tr>
        </table>
        {% if approval.rejection_reason %}
        <div style="background:#f8fafc;border-radius:6px;padding:16px 20px;margin:0 0 24px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;">Reason</p>
          <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">{{ approval.rejection_reason }}</p>
        </div>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ approval.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Agent</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because your AI agent approval request was rejected in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Approval Rejected

Hi {{ user.first_name | default(''there'') }},

Your AI agent approval request has been rejected. The agent has been paused.

REJECTED
Action: {{ approval.action | default(''AI Agent Action'') }}
{% if approval.agent %}Agent: {{ approval.agent }}{% endif %}
{% if approval.rejected_by %}Rejected by: {{ approval.rejected_by }}{% endif %}

{% if approval.rejection_reason %}
REASON
{{ approval.rejection_reason }}
{% endif %}

View the agent: {{ approval.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This notification was sent because your AI agent approval request was rejected.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
      ('973573db-4797-44d8-ba62-46684434daa8', '8166a55f-00bd-402c-a334-eb3cb702201c', 1, 'You have been added to a workspace', NULL, 'You have been added to a workspace on K-Control.', 'You have been added to a new workspace. Tap to open.', NULL, NULL, TRUE, '2026-03-19T16:58:13.93531', NULL),
      ('9b2d816d-58df-4e53-8307-3869912d8582', '05ce66bd-4de3-4ed7-960e-7968707f13e7', 1, 'K-Control Platform Announcement', NULL, 'There is a new platform announcement from K-Control.', 'A new platform announcement is available.', NULL, NULL, TRUE, '2026-03-19T16:58:13.963173', NULL),
      ('9b9c7052-bb08-4e38-bb7b-81b270ac8e28', 'e5000000-0000-0000-0001-000000000071', 1, 'Approval Request Expired', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Approval Expired</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#f59e0b;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Approval Request Expired</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An approval request for your AI agent action expired before a response was received. The agent has been paused. You can submit a new approval request from the agents dashboard.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Expired Request</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ approval.action | default(''AI Agent Action'') }}</p>
            {% if approval.agent %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Agent: {{ approval.agent }}</p>{% endif %}
            {% if approval.expires_at %}<p style="margin:0;font-size:13px;color:#64748b;">Expired at: {{ approval.expires_at }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ approval.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Agent Dashboard</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because an approval request you initiated expired in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Approval Request Expired

Hi {{ user.first_name | default(''there'') }},

An approval request for your AI agent action expired before a response was received. The agent has been paused.

EXPIRED REQUEST
Action: {{ approval.action | default(''AI Agent Action'') }}
{% if approval.agent %}Agent: {{ approval.agent }}{% endif %}
{% if approval.expires_at %}Expired at: {{ approval.expires_at }}{% endif %}

View Agent Dashboard: {{ approval.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This notification was sent because an approval request you initiated expired.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
      ('a97728b4-4252-4ff6-8d8b-02a657cf6738', 'e5000000-0000-0000-0001-000000000060', 1, 'Your Report Is Ready: {{ report.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Report Ready</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Your Report Is Ready</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Your AI-generated report has been completed and is ready for review.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border-left:4px solid #22c55e;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#166534;text-transform:uppercase;letter-spacing:0.05em;">Report Completed</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ report.title | default(''Untitled Report'') }}</p>
            {% if report.type %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Type: {{ report.type }}</p>{% endif %}
            {% if report.completed_at %}<p style="margin:0;font-size:13px;color:#64748b;">Generated: {{ report.completed_at }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ report.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Report</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because a report you requested is now ready in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Your Report Is Ready

Hi {{ user.first_name | default(''there'') }},

Your AI-generated report has been completed and is ready for review.

REPORT COMPLETED
Title: {{ report.title | default(''Untitled Report'') }}
{% if report.type %}Type: {{ report.type }}{% endif %}
{% if report.completed_at %}Generated: {{ report.completed_at }}{% endif %}

View the report: {{ report.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This notification was sent because a report you requested is now ready.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
      ('b38168bb-7d46-40fd-a11d-21452527b4c3', 'e5000000-0000-0000-0001-000000000002', 1, 'Overdue Task: {{ task.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Overdue</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#dc2626;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Is Overdue</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">The following task has passed its due date and still requires your attention. Please complete or update it as soon as possible.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fef2f2;border-left:4px solid #dc2626;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#991b1b;text-transform:uppercase;letter-spacing:0.05em;">Overdue Task</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default(''Untitled Task'') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
            {% if task.due_date %}<p style="margin:0;font-size:13px;color:#dc2626;font-weight:600;">Was due: {{ task.due_date }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Complete Task Now</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This is an automated overdue reminder from {{ platform.name | default(''K-Control'') }}. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Task Is Overdue

Hi {{ user.first_name | default(''there'') }},

The following task has passed its due date and still requires your attention.

OVERDUE TASK
Title: {{ task.title | default(''Untitled Task'') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}
{% if task.due_date %}Was due: {{ task.due_date }}{% endif %}

Complete the task: {{ task.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This is an automated overdue reminder from {{ platform.name | default(''K-Control'') }}.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('b78d3e38-39ea-4121-8b3a-7acb53d22f74', 'e5000000-0000-0000-0001-000000000003', 1, 'Task Ready for Review: {{ task.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Ready for Review</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Awaiting Your Review</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">A task has been submitted for review and is pending your approval. Please review the evidence and either approve or send it back for revision.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Pending Review</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default(''Untitled Task'') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
            {% if task.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Due: <strong>{{ task.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Review Task</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You are receiving this because you are a reviewer for this task. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Task Awaiting Your Review

Hi {{ user.first_name | default(''there'') }},

A task has been submitted for review and is pending your approval.

PENDING REVIEW
Title: {{ task.title | default(''Untitled Task'') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}
{% if task.due_date %}Due: {{ task.due_date }}{% endif %}

Review the task: {{ task.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You are receiving this because you are a reviewer for this task.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('bdd463cb-ca6f-44ed-bf43-48b2e77cf776', 'e5000000-0000-0000-0001-000000000070', 1, 'Your Approval Is Required', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Approval Required</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Your Approval Is Required</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An AI agent is requesting your approval before proceeding. Please review the proposed action and approve or reject it.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Pending Approval</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ approval.action | default(''AI Agent Action'') }}</p>
            {% if approval.agent %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Agent: {{ approval.agent }}</p>{% endif %}
            {% if approval.context %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Context: {{ approval.context }}</p>{% endif %}
            {% if approval.expires_at %}<p style="margin:0;font-size:13px;color:#92400e;font-weight:600;">Expires: {{ approval.expires_at }}</p>{% endif %}
          </td></tr>
        </table>
        {% if approval.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ approval.description }}</p>
        {% endif %}
        <p style="margin:0 0 16px;font-size:14px;color:#475569;">This request will expire if no action is taken before the deadline.</p>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ approval.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Review &amp; Approve</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are the designated approver for this AI agent action in {{ platform.name | default(''K-Control'') }}. This is a mandatory notification.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Your Approval Is Required

Hi {{ user.first_name | default(''there'') }},

An AI agent is requesting your approval before proceeding. Please review the proposed action and approve or reject it.

PENDING APPROVAL
Action: {{ approval.action | default(''AI Agent Action'') }}
{% if approval.agent %}Agent: {{ approval.agent }}{% endif %}
{% if approval.context %}Context: {{ approval.context }}{% endif %}
{% if approval.expires_at %}Expires: {{ approval.expires_at }}{% endif %}

{% if approval.description %}
{{ approval.description }}
{% endif %}

This request will expire if no action is taken before the deadline.

Review & Approve: {{ approval.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you are the designated approver for this AI agent action. This is a mandatory notification.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
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
      ('cac34588-1ba3-4222-8116-a47aa9336131', 'e5000000-0000-0000-0001-000000000031', 1, 'Response Required: {{ finding.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Response Required</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Your Response Is Required</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An audit finding assigned to you is now under auditor review and requires your formal response. Please provide your response as soon as possible.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Response Required</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ finding.title | default(''Untitled Finding'') }}</p>
            {% if finding.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Severity: <strong>{{ finding.severity }}</strong></p>{% endif %}
            {% if finding.due_date %}<p style="margin:0;font-size:13px;color:#92400e;font-weight:600;">Response due: {{ finding.due_date }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ finding.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Respond to Finding</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This is a reminder that your formal response is required for an audit finding in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Your Response Is Required

Hi {{ user.first_name | default(''there'') }},

An audit finding assigned to you is now under auditor review and requires your formal response.

RESPONSE REQUIRED
Title: {{ finding.title | default(''Untitled Finding'') }}
{% if finding.severity %}Severity: {{ finding.severity }}{% endif %}
{% if finding.due_date %}Response due: {{ finding.due_date }}{% endif %}

Respond to the finding: {{ finding.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This is a reminder that your formal response is required for an audit finding.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('ceb347ef-696e-428a-904a-56e1e4bbdb6a', 'e5000000-0000-0000-0001-000000000040', 1, 'Assessment Completed: {{ assessment.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Assessment Completed</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Assessment Completed</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An assessment has been completed. The results are now available for review.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border-left:4px solid #22c55e;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#166534;text-transform:uppercase;letter-spacing:0.05em;">Completed</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ assessment.title | default(''Untitled Assessment'') }}</p>
            {% if assessment.type %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Type: {{ assessment.type }}</p>{% endif %}
            {% if assessment.score %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Score: <strong>{{ assessment.score }}</strong></p>{% endif %}
            {% if assessment.completed_at %}<p style="margin:0;font-size:13px;color:#64748b;">Completed: {{ assessment.completed_at }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ assessment.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Results</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are a participant in this assessment in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Assessment Completed

Hi {{ user.first_name | default(''there'') }},

An assessment has been completed. The results are now available for review.

COMPLETED
Title: {{ assessment.title | default(''Untitled Assessment'') }}
{% if assessment.type %}Type: {{ assessment.type }}{% endif %}
{% if assessment.score %}Score: {{ assessment.score }}{% endif %}
{% if assessment.completed_at %}Completed: {{ assessment.completed_at }}{% endif %}

View the results: {{ assessment.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you are a participant in this assessment.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
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
      ('d9a69b23-96a9-4b3a-bf5e-9c41f52ab2fa', 'e5000000-0000-0000-0001-000000000061', 1, 'Report Generation Failed: {{ report.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Report Failed</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#dc2626;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Report Generation Failed</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Unfortunately, your report could not be generated. You can retry from the reports page.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fef2f2;border-left:4px solid #dc2626;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#991b1b;text-transform:uppercase;letter-spacing:0.05em;">Failed</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ report.title | default(''Untitled Report'') }}</p>
            {% if report.type %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Type: {{ report.type }}</p>{% endif %}
            {% if report.error %}<p style="margin:0;font-size:13px;color:#dc2626;">Error: {{ report.error }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ report.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Retry Report</a>
          </td></tr>
        </table>
        <p style="margin:0 0 20px;font-size:14px;color:#64748b;line-height:1.6;">If this problem persists, please contact <a href="mailto:{{ platform.support_email | default(''support@kcontrol.io'') }}" style="color:#295cf6;text-decoration:none;">{{ platform.support_email | default(''support@kcontrol.io'') }}</a>.</p>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because a report you requested failed to generate in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Report Generation Failed

Hi {{ user.first_name | default(''there'') }},

Unfortunately, your report could not be generated. You can retry from the reports page.

FAILED
Title: {{ report.title | default(''Untitled Report'') }}
{% if report.type %}Type: {{ report.type }}{% endif %}
{% if report.error %}Error: {{ report.error }}{% endif %}

Retry the report: {{ report.url | default(''#'') }}

If this problem persists, please contact {{ platform.support_email | default(''support@kcontrol.io'') }}.

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
This notification was sent because a report you requested failed to generate.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:48.690335', NULL),
      ('e1000000-0000-0000-0000-000000000002', 'e1000000-0000-0000-0000-000000000001', 1, 'You have been invited to join {{ workspace.name | default("a workspace") }}', '<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Workspace Invitation</title>
  <style>
    body { margin:0; padding:0; background:#f4f4f5; font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',sans-serif; }
    .wrapper { max-width:600px; margin:40px auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08); }
    .header { background:#0f172a; padding:32px 40px; text-align:center; }
    .header h1 { margin:0; color:#fff; font-size:22px; font-weight:600; }
    .header p  { margin:6px 0 0; color:#94a3b8; font-size:13px; }
    .body  { padding:40px; }
    .body h2   { margin:0 0 12px; font-size:18px; font-weight:600; color:#0f172a; }
    .body p    { margin:0 0 16px; font-size:15px; color:#475569; line-height:1.6; }
    .cta  { display:block; margin:28px auto 0; padding:14px 32px; background:#0f172a; color:#fff; text-decoration:none; border-radius:6px; font-size:15px; font-weight:600; text-align:center; width:fit-content; }
    .meta { margin:28px 0 0; padding:20px; background:#f8fafc; border-radius:6px; border-left:3px solid #e2e8f0; }
    .meta p { margin:0; font-size:13px; color:#64748b; line-height:1.5; }
    .footer { padding:24px 40px; border-top:1px solid #e2e8f0; text-align:center; }
    .footer p { margin:0; font-size:12px; color:#94a3b8; }
    .footer a { color:#64748b; text-decoration:none; }
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>K-Control</h1>
    <p>Governance, Risk &amp; Compliance Platform</p>
  </div>
  <div class="body">
    <h2>You''ve been invited</h2>
    <p>Hi {{ user.display_name | default(''there'') }},</p>
    <p>
      <strong>{{ actor.display_name | default(''A team member'') }}</strong> has invited you to join
      the workspace <strong>{{ invite.workspace_name | default(''a workspace'') }}</strong>
      {% if invite.org_name %} at <strong>{{ invite.org_name }}</strong>{% endif %}.
    </p>
    <p>Click the button below to accept your invitation and get started.</p>
    <a href="{{ invite.accept_url }}" class="cta">Accept Invitation</a>
    <div class="meta">
      <p>This invitation expires in <strong>{{ invite.expires_in | default(''72 hours'') }}</strong>.
      If you were not expecting this invitation, you can safely ignore this email.</p>
    </div>
  </div>
  <div class="footer"><p>K-Control &mdash; <a href="{{ unsubscribe_url }}">Unsubscribe</a></p></div>
</div>
</body>
</html>', 'You''ve been invited to join {{ invite.workspace_name | default(''a workspace'') }}{% if invite.org_name %} at {{ invite.org_name }}{% endif %}.

{{ actor.display_name | default(''A team member'') }} has invited you.

Accept here: {{ invite.accept_url }}

Expires in {{ invite.expires_in | default(''72 hours'') }}. If unexpected, ignore this email.', 'Invited to {{ invite.workspace_name | default("a workspace") }}', '{}', 'Initial version', TRUE, '2026-03-31T05:29:14.833143', NULL),
      ('e1000000-0000-0000-0000-000000000003', 'e1000000-0000-0000-0000-000000000001', 2, 'You''ve been invited to join {{ invite.workspace_name | default("a workspace") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Workspace Invitation</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ actor.display_name | default("A team member") }}</strong> has invited you to join the workspace <strong>{{ invite.workspace_name | default("a workspace") }}</strong>{% if invite.org_name %} at <strong>{{ invite.org_name }}</strong>{% endif %}. Click the button below to accept your invitation and get started.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This invitation expires in {{ invite.expires_in | default("72 hours") }}.</strong> If you were not expecting this invitation, you can safely ignore this email.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ invite.accept_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Accept Invitation</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

{{ actor.display_name | default("A team member") }} has invited you to join {{ invite.workspace_name | default("a workspace") }}{% if invite.org_name %} at {{ invite.org_name }}{% endif %}.

Accept here: {{ invite.accept_url }}

This invitation expires in {{ invite.expires_in | default("72 hours") }}. If unexpected, ignore this email.

Best regards,
Kreesalis Team', 'Invited to {{ invite.workspace_name | default("a workspace") }}', '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', TRUE, '2026-04-02T05:24:17.59302', NULL),
      ('e1000000-0000-0000-0000-000000000011', 'e1000000-0000-0000-0000-000000000010', 1, 'GRC Access: {{ invite.grc_role_label | default("GRC Role") }} on {{ invite.workspace_name | default("K-Control") }}', '<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>GRC Access Invitation</title>
  <style>
    body { margin:0; padding:0; background:#f4f4f5; font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',sans-serif; }
    .wrapper { max-width:600px; margin:40px auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08); }
    .header { background:#0f172a; padding:32px 40px; text-align:center; }
    .header h1 { margin:0; color:#fff; font-size:22px; font-weight:600; }
    .header .badge { display:inline-block; margin:10px 0 0; padding:4px 14px; background:#1e3a5f; color:#93c5fd; border-radius:20px; font-size:12px; font-weight:600; letter-spacing:.5px; text-transform:uppercase; }
    .body { padding:40px; }
    .body h2 { margin:0 0 12px; font-size:18px; font-weight:600; color:#0f172a; }
    .body p  { margin:0 0 16px; font-size:15px; color:#475569; line-height:1.6; }
    .role-card { margin:24px 0; padding:20px 24px; background:#f0f9ff; border-radius:8px; border:1px solid #bae6fd; }
    .role-card .role-title { font-size:13px; font-weight:600; color:#0369a1; text-transform:uppercase; letter-spacing:.5px; margin:0 0 4px; }
    .role-card .role-name  { font-size:18px; font-weight:700; color:#0c4a6e; margin:0 0 12px; }
    .scope-list { margin:0; padding:0; list-style:none; }
    .scope-list li { padding:7px 0; border-bottom:1px solid #e0f2fe; font-size:14px; color:#0369a1; display:flex; gap:8px; }
    .scope-list li:last-child { border-bottom:none; }
    .scope-list .lbl { color:#64748b; font-size:13px; min-width:100px; }
    .cta { display:block; margin:28px auto 0; padding:14px 32px; background:#0f172a; color:#fff; text-decoration:none; border-radius:6px; font-size:15px; font-weight:600; text-align:center; width:fit-content; }
    .meta { margin:28px 0 0; padding:20px; background:#f8fafc; border-radius:6px; border-left:3px solid #e2e8f0; }
    .meta p { margin:0; font-size:13px; color:#64748b; line-height:1.5; }
    .footer { padding:24px 40px; border-top:1px solid #e2e8f0; text-align:center; }
    .footer p { margin:0; font-size:12px; color:#94a3b8; }
    .footer a { color:#64748b; text-decoration:none; }
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>K-Control</h1>
    <div class="badge">GRC Access</div>
  </div>
  <div class="body">
    <h2>You''ve been assigned a GRC role</h2>
    <p>Hi {{ user.display_name | default(''there'') }},</p>
    <p>
      <strong>{{ actor.display_name | default(''A team member'') }}</strong> has invited you to
      <strong>{{ invite.workspace_name | default(''a GRC workspace'') }}</strong>
      {% if invite.org_name %}({{ invite.org_name }}){% endif %}
      with the following access:
    </p>
    <div class="role-card">
      <div class="role-title">Assigned Role</div>
      <div class="role-name">{{ invite.grc_role_label | default(''GRC Member'') }}</div>
      <ul class="scope-list">
        {% if invite.workspace_name %}<li><span class="lbl">Workspace</span>{{ invite.workspace_name }}</li>{% endif %}
        {% if invite.framework_name %}<li><span class="lbl">Framework</span>{{ invite.framework_name }}</li>{% endif %}
        {% if invite.engagement_name %}<li><span class="lbl">Engagement</span>{{ invite.engagement_name }}</li>{% endif %}
      </ul>
    </div>
    <p>Click below to accept and access the platform.</p>
    <a href="{{ invite.accept_url }}" class="cta">Accept &amp; Access Platform</a>
    <div class="meta">
      <p>This invitation expires in <strong>{{ invite.expires_in | default(''72 hours'') }}</strong>.
      If unexpected, you can safely ignore this email.</p>
    </div>
  </div>
  <div class="footer"><p>K-Control &mdash; <a href="{{ unsubscribe_url }}">Unsubscribe</a></p></div>
</div>
</body>
</html>', 'You''ve been assigned a GRC role on {{ invite.workspace_name | default(''a workspace'') }}{% if invite.org_name %} ({{ invite.org_name }}){% endif %}.

Role: {{ invite.grc_role_label | default(''GRC Member'') }}
{% if invite.framework_name %}Framework:  {{ invite.framework_name }}
{% endif %}{% if invite.engagement_name %}Engagement: {{ invite.engagement_name }}
{% endif %}
Accept here: {{ invite.accept_url }}

Expires in {{ invite.expires_in | default(''72 hours'') }}.', 'GRC role: {{ invite.grc_role_label | default("GRC Member") }} on {{ invite.workspace_name | default("K-Control") }}', '{}', 'Initial version', TRUE, '2026-03-31T05:29:14.833143', NULL),
      ('e1000000-0000-0000-0000-000000000012', 'e1000000-0000-0000-0000-000000000010', 2, 'GRC Access: {{ invite.grc_role_label | default("GRC Role") }} on {{ invite.workspace_name | default("K-Control") }}', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">GRC Role Assignment</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ actor.display_name | default("A team member") }}</strong> has invited you to <strong>{{ invite.workspace_name | default("a GRC workspace") }}</strong>{% if invite.org_name %} ({{ invite.org_name }}){% endif %} with the following access:</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Assigned Role</div>
        <div style="font-size:1.2em;font-weight:700;color:#0c4a6e;margin-bottom:12px;">{{ invite.grc_role_label | default("GRC Member") }}</div>
        {% if invite.workspace_name %}<div style="display:flex;padding:6px 0;border-top:1px solid #e0f2fe;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Workspace</span><span style="color:#0369a1;font-weight:500;">{{ invite.workspace_name }}</span></div>{% endif %}
        {% if invite.framework_name %}<div style="display:flex;padding:6px 0;border-top:1px solid #e0f2fe;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Framework</span><span style="color:#0369a1;font-weight:500;">{{ invite.framework_name }}</span></div>{% endif %}
        {% if invite.engagement_name %}<div style="display:flex;padding:6px 0;border-top:1px solid #e0f2fe;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Engagement</span><span style="color:#0369a1;font-weight:500;">{{ invite.engagement_name }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This invitation expires in {{ invite.expires_in | default("72 hours") }}.</strong> If you were not expecting this, you can safely ignore this email.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ invite.accept_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Accept &amp; Access Platform</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

{{ actor.display_name | default("A team member") }} has assigned you a GRC role on {{ invite.workspace_name | default("a workspace") }}{% if invite.org_name %} ({{ invite.org_name }}){% endif %}.

Role: {{ invite.grc_role_label | default("GRC Member") }}
{% if invite.framework_name %}Framework:  {{ invite.framework_name }}
{% endif %}{% if invite.engagement_name %}Engagement: {{ invite.engagement_name }}
{% endif %}
Accept here: {{ invite.accept_url }}

This invitation expires in {{ invite.expires_in | default("72 hours") }}.

Best regards,
Kreesalis Team', 'GRC role: {{ invite.grc_role_label | default("GRC Member") }} on {{ invite.workspace_name | default("K-Control") }}', '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', TRUE, '2026-04-02T05:24:17.621799', NULL),
      ('e1000000-0000-0000-0000-000000000021', 'e1000000-0000-0000-0000-000000000020', 1, 'Engagement Access: {{ invite.engagement_name | default("Audit Engagement") }} — {{ invite.org_name | default("K-Control") }}', '<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Engagement Access Granted</title>
  <style>
    body { margin:0; padding:0; background:#f4f4f5; font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',sans-serif; }
    .wrapper { max-width:600px; margin:40px auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08); }
    .header { background:#14532d; padding:32px 40px; text-align:center; }
    .header h1 { margin:0; color:#fff; font-size:22px; font-weight:600; }
    .header .badge { display:inline-block; margin:10px 0 0; padding:4px 14px; background:#166534; color:#86efac; border-radius:20px; font-size:12px; font-weight:600; letter-spacing:.5px; text-transform:uppercase; }
    .body { padding:40px; }
    .body h2 { margin:0 0 12px; font-size:18px; font-weight:600; color:#0f172a; }
    .body p  { margin:0 0 16px; font-size:15px; color:#475569; line-height:1.6; }
    .eng-card { margin:24px 0; padding:20px 24px; background:#f0fdf4; border-radius:8px; border:1px solid #bbf7d0; }
    .eng-card .eng-title { font-size:13px; font-weight:600; color:#15803d; text-transform:uppercase; letter-spacing:.5px; margin:0 0 4px; }
    .eng-card .eng-name  { font-size:18px; font-weight:700; color:#14532d; margin:0 0 12px; }
    .detail-row { display:flex; gap:8px; padding:6px 0; border-bottom:1px solid #dcfce7; font-size:14px; }
    .detail-row:last-child { border-bottom:none; }
    .detail-row .lbl { color:#64748b; font-size:13px; min-width:110px; }
    .detail-row .val { color:#166534; font-weight:500; }
    .cta { display:block; margin:28px auto 0; padding:14px 32px; background:#14532d; color:#fff; text-decoration:none; border-radius:6px; font-size:15px; font-weight:600; text-align:center; width:fit-content; }
    .meta { margin:28px 0 0; padding:20px; background:#f8fafc; border-radius:6px; border-left:3px solid #e2e8f0; }
    .meta p { margin:0; font-size:13px; color:#64748b; line-height:1.5; }
    .footer { padding:24px 40px; border-top:1px solid #e2e8f0; text-align:center; }
    .footer p { margin:0; font-size:12px; color:#94a3b8; }
    .footer a { color:#64748b; text-decoration:none; }
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>K-Control</h1>
    <div class="badge">Audit Access</div>
  </div>
  <div class="body">
    <h2>Engagement access granted</h2>
    <p>Hi {{ user.display_name | default(''there'') }},</p>
    <p>You have been granted access to an audit engagement on K-Control.
    {% if invite.org_name %}This engagement is managed by <strong>{{ invite.org_name }}</strong>.{% endif %}</p>
    <div class="eng-card">
      <div class="eng-title">Audit Engagement</div>
      <div class="eng-name">{{ invite.engagement_name | default(''Audit Engagement'') }}</div>
      {% if invite.framework_name %}
      <div class="detail-row"><span class="lbl">Framework</span><span class="val">{{ invite.framework_name }}</span></div>
      {% endif %}
      {% if invite.grc_role_label %}
      <div class="detail-row"><span class="lbl">Your Role</span><span class="val">{{ invite.grc_role_label }}</span></div>
      {% endif %}
    </div>
    <p>Log in to K-Control to view the engagement and begin your audit work.</p>
    <a href="{{ invite.accept_url }}" class="cta">Go to K-Control</a>
    <div class="meta">
      <p>Your access remains active until the engagement is closed or your access is revoked.
      Contact the engagement lead with any questions.</p>
    </div>
  </div>
  <div class="footer"><p>K-Control &mdash; <a href="{{ unsubscribe_url }}">Unsubscribe</a></p></div>
</div>
</body>
</html>', 'Engagement access granted on K-Control.
{% if invite.org_name %}Organisation: {{ invite.org_name }}
{% endif %}
Engagement: {{ invite.engagement_name | default(''Audit Engagement'') }}
{% if invite.framework_name %}Framework:  {{ invite.framework_name }}
{% endif %}{% if invite.grc_role_label %}Your Role:  {{ invite.grc_role_label }}
{% endif %}
Log in here: {{ invite.accept_url }}

Access remains active until the engagement is closed or revoked.', 'Access: {{ invite.engagement_name | default("Audit Engagement") }}', '{}', 'Initial version', TRUE, '2026-03-31T05:29:14.833143', NULL),
      ('e1000000-0000-0000-0000-000000000022', 'e1000000-0000-0000-0000-000000000020', 2, 'Engagement Access: {{ invite.engagement_name | default("Audit Engagement") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Audit Engagement Access</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>You have been granted access to an audit engagement on K-Control.{% if invite.org_name %} This engagement is managed by <strong>{{ invite.org_name }}</strong>.{% endif %}</p>
      </div>
      <div style="background:#f0fdf4;padding:18px 20px;border-radius:8px;border:1px solid #bbf7d0;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#15803d;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Audit Engagement</div>
        <div style="font-size:1.2em;font-weight:700;color:#14532d;margin-bottom:12px;">{{ invite.engagement_name | default("Audit Engagement") }}</div>
        {% if invite.framework_name %}<div style="display:flex;padding:6px 0;border-top:1px solid #dcfce7;font-size:0.9em;"><span style="color:#64748b;min-width:110px;">Framework</span><span style="color:#166534;font-weight:500;">{{ invite.framework_name }}</span></div>{% endif %}
        {% if invite.grc_role_label %}<div style="display:flex;padding:6px 0;border-top:1px solid #dcfce7;font-size:0.9em;"><span style="color:#64748b;min-width:110px;">Your Role</span><span style="color:#166534;font-weight:500;">{{ invite.grc_role_label }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>Your access remains active</strong> until the engagement is closed or your access is revoked. Contact the engagement lead with any questions.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ invite.accept_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to K-Control</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

You have been granted access to an audit engagement on K-Control.
{% if invite.org_name %}Organisation: {{ invite.org_name }}
{% endif %}
Engagement: {{ invite.engagement_name | default("Audit Engagement") }}
{% if invite.framework_name %}Framework:   {{ invite.framework_name }}
{% endif %}{% if invite.grc_role_label %}Your Role:   {{ invite.grc_role_label }}
{% endif %}
Log in here: {{ invite.accept_url }}

Access remains active until the engagement is closed or revoked.

Best regards,
Kreesalis Team', 'Access: {{ invite.engagement_name | default("Audit Engagement") }}', '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', TRUE, '2026-04-02T05:24:17.64982', NULL),
      ('e17ab86d-b88e-48ff-bd72-e3bbba51bb3f', 'e5000000-0000-0000-0001-000000000020', 1, 'Risk Assigned to You: {{ risk.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Risk Assigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Risk Assigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">You have been assigned as the owner of a risk. Please review the risk details and ensure appropriate treatment plans are in place.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Risk Details</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ risk.title | default(''Untitled Risk'') }}</p>
            {% if risk.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Severity: <strong>{{ risk.severity }}</strong></p>{% endif %}
            {% if risk.status %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Status: {{ risk.status }}</p>{% endif %}
            {% if risk.review_date %}<p style="margin:0;font-size:13px;color:#64748b;">Next review: <strong>{{ risk.review_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if risk.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ risk.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ risk.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Risk</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you were assigned as the risk owner in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Risk Assigned to You

Hi {{ user.first_name | default(''there'') }},

You have been assigned as the owner of a risk. Please review the details and ensure appropriate treatment plans are in place.

RISK DETAILS
Title: {{ risk.title | default(''Untitled Risk'') }}
{% if risk.severity %}Severity: {{ risk.severity }}{% endif %}
{% if risk.status %}Status: {{ risk.status }}{% endif %}
{% if risk.review_date %}Next review: {{ risk.review_date }}{% endif %}
{% if risk.description %}
{{ risk.description }}
{% endif %}

View the risk: {{ risk.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you were assigned as the risk owner.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
      ('e2000000-0000-0000-0000-000000000002', 'e2000000-0000-0000-0000-000000000001', 1, 'Your Task Portal Access Link — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Task Portal Access</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>You have been assigned a task on K-Control. Click the button below to access your task portal without a password.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This link expires in {{ magic_link.expires_in }}.</strong> If you did not expect this email, you can safely ignore it.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ magic_link.url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Open Task Portal</a>
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

You have been assigned a task on K-Control.

Click here to access your task portal: {{ magic_link.url }}

This link expires in {{ magic_link.expires_in }}.

If you did not expect this email, you can safely ignore it.

Best regards,
Kreesalis Team', 'Task portal: {{ magic_link.url }}', '{}', 'Initial version', TRUE, '2026-04-01T10:45:13.564116', NULL),
      ('e3000000-0000-0000-0000-000000000002', 'e3000000-0000-0000-0000-000000000001', 1, 'Reset your K-Control password', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Password Reset</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We received a request to reset your K-Control password. Click the button below to choose a new password.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This link expires in {{ reset.expires_in | default("30 minutes") }}.</strong> If you did not request a password reset, you can safely ignore this email — your password will not change.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ reset.url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Reset Password</a>
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

We received a request to reset your K-Control password.

Click here to reset your password: {{ reset.url }}

This link expires in {{ reset.expires_in | default("30 minutes") }}. If you did not request this, ignore this email — your password will not change.

Best regards,
Kreesalis Team', 'Reset your K-Control password: {{ reset.url }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000011', 'e3000000-0000-0000-0000-000000000010', 1, 'Your K-Control password was changed', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Password Changed</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Your K-Control account password was successfully changed on <strong>{{ event.occurred_at | default("just now") }}</strong>.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>If you did not make this change</strong>, please reset your password immediately and contact support. Your account security may be at risk.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ reset.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Reset Password</a>
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

Your K-Control password was successfully changed on {{ event.occurred_at | default("just now") }}.

If you did not make this change, please reset your password immediately: {{ reset.url }}

Best regards,
Kreesalis Team', 'Your K-Control password was changed', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000021', 'e3000000-0000-0000-0000-000000000020', 1, 'New sign-in to your K-Control account', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">New Device Sign-In</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We detected a sign-in to your K-Control account from a new device or location.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Sign-In Details</div>
        {% if event.occurred_at %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Time</span><span style="color:#0c4a6e;font-weight:500;">{{ event.occurred_at }}</span></div>{% endif %}
        {% if event.ip_address %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">IP Address</span><span style="color:#0c4a6e;font-weight:500;">{{ event.ip_address }}</span></div>{% endif %}
        {% if event.user_agent %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Device</span><span style="color:#0c4a6e;font-weight:500;">{{ event.user_agent }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>If this wasn''t you</strong>, please reset your password immediately and contact our support team. Your account may be compromised.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ reset.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Secure My Account</a>
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

We detected a sign-in to your K-Control account from a new device or location.
{% if event.occurred_at %}Time:       {{ event.occurred_at }}
{% endif %}{% if event.ip_address %}IP Address: {{ event.ip_address }}
{% endif %}{% if event.user_agent %}Device:     {{ event.user_agent }}
{% endif %}
If this wasn''t you, please reset your password immediately: {{ reset.url }}

Best regards,
Kreesalis Team', 'New sign-in to your K-Control account', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000031', 'e3000000-0000-0000-0000-000000000030', 1, 'New API key created — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">API Key Created</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>A new API key has been created for your K-Control account.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Key Details</div>
        {% if api_key.name %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Key Name</span><span style="color:#0c4a6e;font-weight:500;">{{ api_key.name }}</span></div>{% endif %}
        {% if api_key.prefix %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Prefix</span><span style="color:#0c4a6e;font-weight:500;font-family:monospace;">{{ api_key.prefix }}...</span></div>{% endif %}
        {% if event.occurred_at %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Created</span><span style="color:#0c4a6e;font-weight:500;">{{ event.occurred_at }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>If you did not create this key</strong>, please revoke it immediately in your account settings and contact our support team.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ settings.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Manage API Keys</a>
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

A new API key has been created for your K-Control account.
{% if api_key.name %}Key Name: {{ api_key.name }}
{% endif %}{% if api_key.prefix %}Prefix:   {{ api_key.prefix }}...
{% endif %}{% if event.occurred_at %}Created:  {{ event.occurred_at }}
{% endif %}
If you did not create this key, revoke it immediately in your account settings.

Best regards,
Kreesalis Team', 'New API key created: {{ api_key.name | default("API Key") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000041', 'e3000000-0000-0000-0000-000000000040', 1, 'Your email address has been verified — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Email Verified</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Your email address has been successfully verified. Your K-Control account is fully active and ready to use.</p>
      </div>
      <div style="background:#f0fdf4;padding:14px 18px;border-radius:8px;border-left:4px solid #22c55e;margin:14px 0;">
        <strong>Verification complete.</strong> You can now access all features of the platform.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ dashboard.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to Dashboard</a>
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

Your K-Control email address has been successfully verified. Your account is fully active.

Go to your dashboard: {{ dashboard.url }}

Best regards,
Kreesalis Team', 'Email verified — your K-Control account is active', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000051', 'e3000000-0000-0000-0000-000000000050', 1, 'You''ve been invited to join {{ invite.org_name | default("an organisation") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Organisation Invitation</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ actor.display_name | default("A team member") }}</strong> has invited you to join <strong>{{ invite.org_name | default("an organisation") }}</strong> on K-Control.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This invitation expires in {{ invite.expires_in | default("72 hours") }}.</strong> If you were not expecting this, you can safely ignore this email.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ invite.accept_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Accept Invitation</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

{{ actor.display_name | default("A team member") }} has invited you to join {{ invite.org_name | default("an organisation") }} on K-Control.

Accept here: {{ invite.accept_url }}

This invitation expires in {{ invite.expires_in | default("72 hours") }}. If unexpected, ignore this email.

Best regards,
Kreesalis Team', 'Invited to {{ invite.org_name | default("an organisation") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000061', 'e3000000-0000-0000-0000-000000000060', 1, 'Welcome to {{ org.name | default("your organisation") }} on K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Organisation Access Granted</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>You have been added to <strong>{{ org.name | default("your organisation") }}</strong> on K-Control with the role <strong>{{ member.role | default("member") }}</strong>.</p>
      </div>
      <div style="background:#f0fdf4;padding:14px 18px;border-radius:8px;border-left:4px solid #22c55e;margin:14px 0;">
        <strong>You now have access</strong> to the organisation''s workspaces, resources, and team collaboration tools.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ dashboard.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to Dashboard</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

You have been added to {{ org.name | default("your organisation") }} on K-Control with the role {{ member.role | default("member") }}.

Go to your dashboard: {{ dashboard.url }}

Best regards,
Kreesalis Team', 'Welcome to {{ org.name | default("your organisation") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000071', 'e3000000-0000-0000-0000-000000000070', 1, 'Your access to {{ org.name | default("an organisation") }} has been removed — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Organisation Access Removed</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>Your membership in <strong>{{ org.name | default("your organisation") }}</strong> on K-Control has been removed.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>You no longer have access</strong> to this organisation''s workspaces or resources. If you believe this is an error, please contact your organisation administrator.
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
</html>', 'Hi {{ user.display_name | default("there") }},

Your membership in {{ org.name | default("your organisation") }} on K-Control has been removed.

You no longer have access to this organisation''s workspaces or resources. If this is an error, contact your organisation administrator.

Best regards,
Kreesalis Team', 'Access removed from {{ org.name | default("an organisation") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000081', 'e3000000-0000-0000-0000-000000000080', 1, 'You''ve been added to {{ workspace.name | default("a workspace") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Workspace Access Granted</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>You have been added to the workspace <strong>{{ workspace.name | default("a workspace") }}</strong>{% if org.name %} at <strong>{{ org.name }}</strong>{% endif %} with the role <strong>{{ member.role | default("member") }}</strong>.</p>
      </div>
      <div style="background:#f0fdf4;padding:14px 18px;border-radius:8px;border-left:4px solid #22c55e;margin:14px 0;">
        <strong>You now have access</strong> to this workspace and its resources.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ workspace.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to Workspace</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

You have been added to the workspace {{ workspace.name | default("a workspace") }}{% if org.name %} at {{ org.name }}{% endif %} with the role {{ member.role | default("member") }}.

Go to workspace: {{ workspace.url }}

Best regards,
Kreesalis Team', 'Added to {{ workspace.name | default("a workspace") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-000000000091', 'e3000000-0000-0000-0000-000000000090', 1, 'Your access to {{ workspace.name | default("a workspace") }} has been removed — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Workspace Access Removed</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>Your membership in the workspace <strong>{{ workspace.name | default("a workspace") }}</strong>{% if org.name %} at <strong>{{ org.name }}</strong>{% endif %} has been removed.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>You no longer have access</strong> to this workspace. If you believe this is an error, contact your workspace administrator.
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
</html>', 'Hi {{ user.display_name | default("there") }},

Your membership in the workspace {{ workspace.name | default("a workspace") }}{% if org.name %} at {{ org.name }}{% endif %} has been removed.

If this is an error, contact your workspace administrator.

Best regards,
Kreesalis Team', 'Access removed from {{ workspace.name | default("a workspace") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-0000000000a1', 'e3000000-0000-0000-0000-0000000000a0', 1, 'Your role on K-Control has been updated', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Role Updated</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>Your role in <strong>{{ org.name | default("your organisation") }}</strong> has been updated by <strong>{{ actor.display_name | default("an administrator") }}</strong>.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Role Change</div>
        {% if role.previous %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Previous</span><span style="color:#64748b;font-weight:500;text-decoration:line-through;">{{ role.previous }}</span></div>{% endif %}
        {% if role.new %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">New Role</span><span style="color:#0c4a6e;font-weight:700;">{{ role.new }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        Your permissions have been updated accordingly. If you have questions about this change, contact your administrator.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ dashboard.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to Dashboard</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

Your role in {{ org.name | default("your organisation") }} has been updated by {{ actor.display_name | default("an administrator") }}.
{% if role.previous %}Previous role: {{ role.previous }}
{% endif %}{% if role.new %}New role:      {{ role.new }}
{% endif %}
If you have questions, contact your administrator.

Best regards,
Kreesalis Team', 'Your role was updated to {{ role.new | default("a new role") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-0000000000b1', 'e3000000-0000-0000-0000-0000000000b0', 1, 'We miss you — come back to K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">We Miss You</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>You haven''t logged into K-Control in a while. Your team and workspaces are waiting for you.</p>
      </div>
      <div style="background:#f0f9ff;padding:14px 18px;border-radius:8px;border-left:4px solid #295cf6;margin:14px 0;">
        Log back in to stay up to date with your compliance controls, audit progress, and team activity.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ dashboard.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Return to K-Control</a>
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

You haven''t logged into K-Control in a while. Your team and workspaces are waiting for you.

Return to K-Control: {{ dashboard.url }}

Best regards,
Kreesalis Team', 'Come back to K-Control', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-0000000000c1', 'e3000000-0000-0000-0000-0000000000c0', 1, 'K-Control {{ release.version | default("update") }} is now live', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">{{ release.title | default("New Release") }}</h2>
      {% if release.version %}<p style="color:#295cf6;font-size:0.9em;margin:4px 0 0 0;font-weight:600;">{{ release.version }}</p>{% endif %}
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>{{ release.summary | default("We have released a new version of K-Control with improvements and new features.") }}</p>
      </div>
      {% if release.changelog_url %}
      <div style="background:#f0f9ff;padding:14px 18px;border-radius:8px;border-left:4px solid #295cf6;margin:14px 0;">
        Read the full changelog for details on what''s new in this release.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ release.changelog_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Read Changelog</a>
      </div>
      {% endif %}
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

{{ release.title | default("New Release") }}{% if release.version %} ({{ release.version }}){% endif %}

{{ release.summary | default("We have released a new version of K-Control.") }}
{% if release.changelog_url %}
Read the full changelog: {{ release.changelog_url }}
{% endif %}
Best regards,
Kreesalis Team', '{{ release.title | default("New release") }}{% if release.version %} ({{ release.version }}){% endif %}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-0000000000d1', 'e3000000-0000-0000-0000-0000000000d0', 1, '[{{ incident.severity | default("Incident") | upper }}] {{ incident.title | default("Platform Incident") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#dc2626;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Platform Incident</h2>
      {% if incident.severity %}<p style="color:#dc2626;font-size:0.9em;margin:4px 0 0 0;font-weight:700;text-transform:uppercase;">{{ incident.severity }}</p>{% endif %}
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We are currently investigating an incident that may affect the K-Control platform.</p>
      </div>
      <div style="background:#fef2f2;padding:18px 20px;border-radius:8px;border:1px solid #fecaca;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">{{ incident.title | default("Platform Incident") }}</div>
        <div style="font-size:0.95em;color:#7f1d1d;line-height:1.6;">{{ incident.description | default("We are investigating the issue and will provide updates.") }}</div>
        {% if incident.affected_components %}<div style="margin-top:10px;font-size:0.88em;color:#dc2626;"><strong>Affected:</strong> {{ incident.affected_components }}</div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        Our team is actively working to resolve this issue. We will send updates as the situation progresses.
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

[{{ incident.severity | default("INCIDENT") | upper }}] {{ incident.title | default("Platform Incident") }}

{{ incident.description | default("We are investigating an incident affecting the K-Control platform.") }}
{% if incident.affected_components %}Affected: {{ incident.affected_components }}
{% endif %}
Our team is actively working to resolve this. We will send updates as the situation progresses.

Best regards,
Kreesalis Team', '[{{ incident.severity | upper }}] {{ incident.title | default("Platform Incident") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e3000000-0000-0000-0000-0000000000e1', 'e3000000-0000-0000-0000-0000000000e0', 1, 'Scheduled Maintenance — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#f59e0b;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Scheduled Maintenance</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>K-Control is scheduled for planned maintenance. During this window, the platform may be unavailable or experience degraded performance.</p>
      </div>
      <div style="background:#fffbeb;padding:18px 20px;border-radius:8px;border:1px solid #fde68a;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#b45309;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Maintenance Window</div>
        {% if maintenance.starts_at %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Starts</span><span style="color:#92400e;font-weight:500;">{{ maintenance.starts_at }}</span></div>{% endif %}
        {% if maintenance.ends_at %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Ends</span><span style="color:#92400e;font-weight:500;">{{ maintenance.ends_at }}</span></div>{% endif %}
        {% if maintenance.duration %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Duration</span><span style="color:#92400e;font-weight:500;">{{ maintenance.duration }}</span></div>{% endif %}
        {% if maintenance.description %}
        <div style="margin-top:10px;font-size:0.9em;color:#7f1d1d;line-height:1.5;">{{ maintenance.description }}</div>
        {% endif %}
      </div>
      <div style="background:#f5f7fa;padding:14px 18px;border-radius:8px;border-left:4px solid #94a3b8;margin:14px 0;">
        We apologise for any inconvenience. If you have questions, contact our support team.
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

K-Control is scheduled for planned maintenance. The platform may be unavailable during this window.
{% if maintenance.starts_at %}Starts:   {{ maintenance.starts_at }}
{% endif %}{% if maintenance.ends_at %}Ends:     {{ maintenance.ends_at }}
{% endif %}{% if maintenance.duration %}Duration: {{ maintenance.duration }}
{% endif %}{% if maintenance.description %}
{{ maintenance.description }}
{% endif %}
We apologise for any inconvenience.

Best regards,
Kreesalis Team', 'Scheduled maintenance: {% if maintenance.starts_at %}{{ maintenance.starts_at }}{% else %}upcoming{% endif %}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.106718', NULL),
      ('e4000000-0000-0000-0000-000000000002', 'e4000000-0000-0000-0000-000000000001', 1, 'Task assigned: {{ task.title | default("New Task") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Task Assigned</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ actor.display_name | default("A team member") }}</strong> has assigned a task to you on K-Control.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Task Details</div>
        <div style="font-size:1.1em;font-weight:700;color:#0c4a6e;margin-bottom:10px;">{{ task.title | default("New Task") }}</div>
        {% if task.description %}<div style="font-size:0.9em;color:#475569;line-height:1.5;margin-bottom:10px;">{{ task.description }}</div>{% endif %}
        {% if task.control_name %}<div style="display:flex;padding:5px 0;border-top:1px solid #e0f2fe;font-size:0.88em;"><span style="color:#64748b;min-width:90px;">Control</span><span style="color:#0369a1;font-weight:500;">{{ task.control_name }}</span></div>{% endif %}
        {% if task.framework %}<div style="display:flex;padding:5px 0;border-top:1px solid #e0f2fe;font-size:0.88em;"><span style="color:#64748b;min-width:90px;">Framework</span><span style="color:#0369a1;font-weight:500;">{{ task.framework }}</span></div>{% endif %}
        {% if task.priority %}<div style="display:flex;padding:5px 0;border-top:1px solid #e0f2fe;font-size:0.88em;"><span style="color:#64748b;min-width:90px;">Priority</span><span style="color:#0369a1;font-weight:500;text-transform:capitalize;">{{ task.priority }}</span></div>{% endif %}
      </div>
      {% if task.due_date %}
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>Due date: {{ task.due_date }}.</strong> Please complete this task before the due date.
      </div>
      {% endif %}
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ task.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">View Task</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

{{ actor.display_name | default("A team member") }} has assigned a task to you on K-Control.

Task: {{ task.title | default("New Task") }}
{% if task.description %}{{ task.description }}
{% endif %}{% if task.control_name %}Control:   {{ task.control_name }}
{% endif %}{% if task.framework %}Framework: {{ task.framework }}
{% endif %}{% if task.priority %}Priority:  {{ task.priority }}
{% endif %}{% if task.due_date %}Due Date:  {{ task.due_date }}
{% endif %}
View task: {{ task.url }}

Best regards,
Kreesalis Team', 'Task assigned: {{ task.title | default("New Task") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.465256', NULL),
      ('e4000000-0000-0000-0000-000000000011', 'e4000000-0000-0000-0000-000000000010', 1, 'Task status updated: {{ task.title | default("Task") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Task Status Updated</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>The status of a task you are involved with has been updated by <strong>{{ actor.display_name | default("a team member") }}</strong>.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Status Change</div>
        <div style="font-size:1.05em;font-weight:600;color:#0c4a6e;margin-bottom:10px;">{{ task.title | default("Task") }}</div>
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;">
          {% if task.status.previous %}<span style="background:#e2e8f0;color:#475569;padding:4px 12px;border-radius:20px;font-size:0.85em;font-weight:500;">{{ task.status.previous }}</span>
          <span style="color:#64748b;font-size:1.2em;">→</span>{% endif %}
          <span style="background:#dbeafe;color:#1d4ed8;padding:4px 12px;border-radius:20px;font-size:0.85em;font-weight:600;">{{ task.status.new | default("Updated") }}</span>
        </div>
        {% if task.control_name %}<div style="display:flex;padding:5px 0;border-top:1px solid #e0f2fe;margin-top:8px;font-size:0.88em;"><span style="color:#64748b;min-width:90px;">Control</span><span style="color:#0369a1;font-weight:500;">{{ task.control_name }}</span></div>{% endif %}
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ task.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">View Task</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

{{ actor.display_name | default("A team member") }} updated the status of a task you are involved with.

Task: {{ task.title | default("Task") }}
{% if task.status.previous %}Previous: {{ task.status.previous }}
{% endif %}New Status: {{ task.status.new | default("Updated") }}
{% if task.control_name %}Control:  {{ task.control_name }}
{% endif %}
View task: {{ task.url }}

Best regards,
Kreesalis Team', '{{ task.title | default("Task") }}: status changed to {{ task.status.new | default("updated") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.465256', NULL),
      ('e4000000-0000-0000-0000-000000000021', 'e4000000-0000-0000-0000-000000000020', 1, 'New comment on: {{ task.title | default("Task") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">New Comment</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ comment.author | default("A team member") }}</strong> added a comment to <strong>{{ task.title | default("a task") }}</strong> you are involved with.</p>
      </div>
      <div style="background:#f8fafc;padding:18px 20px;border-radius:8px;border-left:4px solid #295cf6;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">{{ comment.author | default("Comment") }}</div>
        <div style="font-size:0.95em;color:#1e293b;line-height:1.6;font-style:italic;">"{{ comment.body | default("See the task for the full comment.") }}"</div>
      </div>
      {% if task.control_name %}
      <div style="background:#fffbeb;padding:12px 16px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;font-size:0.9em;">
        <strong>Control:</strong> {{ task.control_name }}{% if task.framework %} · {{ task.framework }}{% endif %}
      </div>
      {% endif %}
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ task.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">View Task</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

{{ comment.author | default("A team member") }} added a comment to {{ task.title | default("a task") }}:

"{{ comment.body | default("See the task for the full comment.") }}"

{% if task.control_name %}Control: {{ task.control_name }}{% if task.framework %} · {{ task.framework }}{% endif %}
{% endif %}
View task: {{ task.url }}

Best regards,
Kreesalis Team', '{{ comment.author | default("New comment") }} on {{ task.title | default("task") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.465256', NULL),
      ('e4000000-0000-0000-0000-000000000031', 'e4000000-0000-0000-0000-000000000030', 1, 'Feedback received on: {{ task.title | default("Task") }} — K-Control', '<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Feedback Received</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ feedback.author | default("A reviewer") }}</strong> has submitted feedback on <strong>{{ task.title | default("a task") }}</strong>.</p>
      </div>
      {% if feedback.type %}
      <div style="text-align:center;margin:10px 0;">
        {% if feedback.type == ''approved'' %}
        <span style="display:inline-block;background:#dcfce7;color:#166534;padding:6px 18px;border-radius:20px;font-size:0.88em;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Approved</span>
        {% elif feedback.type == ''rejected'' %}
        <span style="display:inline-block;background:#fee2e2;color:#991b1b;padding:6px 18px;border-radius:20px;font-size:0.88em;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Rejected</span>
        {% else %}
        <span style="display:inline-block;background:#fffbeb;color:#92400e;padding:6px 18px;border-radius:20px;font-size:0.88em;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Needs Revision</span>
        {% endif %}
      </div>
      {% endif %}
      <div style="background:#f8fafc;padding:18px 20px;border-radius:8px;border-left:4px solid #295cf6;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Feedback from {{ feedback.author | default("Reviewer") }}</div>
        <div style="font-size:0.95em;color:#1e293b;line-height:1.6;font-style:italic;">"{{ feedback.body | default("See the task for the full feedback.") }}"</div>
      </div>
      {% if task.control_name %}
      <div style="background:#fffbeb;padding:12px 16px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;font-size:0.9em;">
        <strong>Control:</strong> {{ task.control_name }}{% if task.framework %} · {{ task.framework }}{% endif %}
      </div>
      {% endif %}
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ task.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">View Task</a>
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
</html>', 'Hi {{ user.display_name | default("there") }},

{{ feedback.author | default("A reviewer") }} submitted feedback on {{ task.title | default("a task") }}:
{% if feedback.type %}Outcome: {{ feedback.type | upper }}
{% endif %}
"{{ feedback.body | default("See the task for the full feedback.") }}"

{% if task.control_name %}Control: {{ task.control_name }}{% if task.framework %} · {{ task.framework }}{% endif %}
{% endif %}
View task: {{ task.url }}

Best regards,
Kreesalis Team', 'Feedback on {{ task.title | default("task") }}: {{ feedback.type | default("review") }}', '{}', 'Initial version', TRUE, '2026-04-02T05:25:01.465256', NULL),
      ('e48e14b4-22d8-4d0c-b5e3-f18929dacab8', 'e5000000-0000-0000-0001-000000000032', 1, 'Finding Reviewed: {{ finding.title }}', '<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Finding Reviewed</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,''Segoe UI'',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default(''https://assets.kcontrol.io/logo.png'') }}" alt="{{ platform.name | default(''K-Control'') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Audit Finding Reviewed</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default(''there'') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">The auditor has reviewed your finding. Please check the updated status and any reviewer notes below.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Auditor Decision</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ finding.title | default(''Untitled Finding'') }}</p>
            {% if finding.status.new %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">New status: <strong>{{ finding.status.new }}</strong></p>{% endif %}
            {% if finding.severity %}<p style="margin:0;font-size:13px;color:#64748b;">Severity: {{ finding.severity }}</p>{% endif %}
          </td></tr>
        </table>
        {% if comment.body %}
        <div style="background:#f8fafc;border-radius:6px;padding:16px 20px;margin:0 0 24px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;">Auditor Notes</p>
          <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">{{ comment.body }}</p>
          {% if comment.author %}<p style="margin:8px 0 0;font-size:12px;color:#94a3b8;">— {{ comment.author }}</p>{% endif %}
        </div>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ finding.url | default(''#'') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Finding</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default(''Kreesalis'') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are the owner of this finding in {{ platform.name | default(''K-Control'') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>', 'Audit Finding Reviewed

Hi {{ user.first_name | default(''there'') }},

The auditor has reviewed your finding. Please check the updated status and any reviewer notes.

AUDITOR DECISION
Title: {{ finding.title | default(''Untitled Finding'') }}
{% if finding.status.new %}New status: {{ finding.status.new }}{% endif %}
{% if finding.severity %}Severity: {{ finding.severity }}{% endif %}

{% if comment.body %}
AUDITOR NOTES
{{ comment.body }}
{% if comment.author %}— {{ comment.author }}{% endif %}
{% endif %}

View the finding: {{ finding.url | default(''#'') }}

Best regards,
{{ platform.name | default(''Kreesalis'') }} Team

---
You received this because you are the owner of this finding.', NULL, '[]', NULL, TRUE, '2026-04-02T05:33:40.953733', NULL),
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

-- 03_notifications.11_fct_notification_rules (79 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."11_fct_notification_rules" (id, tenant_key, code, name, description, source_event_type, source_event_category, notification_type_code, recipient_strategy, recipient_filter_json, priority_code, delay_seconds, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
  VALUES
      ('0611c619-330b-4afa-b8af-14cc9c1d2f21', 'default', 'robot_rule_1774935524', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T05:38:44.976818', '2026-03-31T05:38:49.251994', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('11eb8495-8ae3-491d-b37a-a003a2d8d76c', 'default', 'robot_rule_1773658049', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-16T10:47:33.091883', '2026-03-16T10:48:07.359208', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('137da862-0695-49de-ba16-0470027ac754', 'default', 'robot_rule_1775021581', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T05:33:02.511952', '2026-04-01T05:33:14.438595', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('18f0c75e-edae-46bf-8ec3-ebba8e7303e4', 'default', 'robot_rule_1774406123', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T02:35:25.327941', '2026-03-25T02:35:46.149318', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('196ccffe-cf09-41f0-8edc-3084657078de', 'default', 'robot_rule_1774804744', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-29T17:19:06.472132', '2026-03-29T17:19:25.376202', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
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
      ('30000000-0000-0000-0000-000000000020', 'default', 'rule_workspace_invite', 'Workspace Invitation', 'Notify invitee when a workspace invitation is created', 'invite_created', 'auth', 'workspace_invite_received', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T05:27:23.073653', '2026-03-31T05:27:23.073653', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000021', 'default', 'rule_workspace_invite_grc', 'GRC Workspace Invitation', 'Notify invitee when a workspace invitation with a GRC role is created', 'invite_created', 'auth', 'workspace_invite_grc', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T05:27:25.681052', '2026-03-31T05:27:25.681052', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000022', 'default', 'rule_engagement_access_granted', 'Engagement Access Granted', 'Notify user when audit engagement access is provisioned', 'engagement_access_provisioned', 'auth', 'engagement_access_granted', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T05:27:25.703243', '2026-03-31T05:27:25.703243', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000030', 'default', 'rule_task_assigned', 'Task Assigned', 'Notify the assignee when a task is assigned to them', 'task_assigned', 'grc', 'task_assigned', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:25:01.499743', '2026-04-02T05:25:01.499743', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000031', 'default', 'rule_task_status_changed', 'Task Status Changed', 'Notify task participants when task status changes', 'task_status_changed', 'grc', 'task_status_changed', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:25:01.499743', '2026-04-02T05:25:01.499743', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000032', 'default', 'rule_task_comment_added', 'Comment Added to Task', 'Notify task participants when a comment is added', 'task_comment_added', 'grc', 'task_comment_added', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:25:01.499743', '2026-04-02T05:25:01.499743', NULL, NULL, NULL, NULL),
      ('30000000-0000-0000-0000-000000000033', 'default', 'rule_task_feedback_received', 'Task Feedback Received', 'Notify task owner when feedback is submitted on their task', 'task_feedback_received', 'grc', 'task_feedback_received', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:25:01.499743', '2026-04-02T05:25:01.499743', NULL, NULL, NULL, NULL),
      ('38fe904f-e2ba-4c20-af67-87c5bdb81cad', 'default', 'robot_rule_1774247624', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T06:33:47.348546', '2026-03-23T06:34:04.696539', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('461b758c-f394-4af8-b589-c2799236d412', 'default', 'robot_rule_1773478311', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T08:51:51.871451', '2026-03-14T08:51:59.660269', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('57b4d3f7-d6c8-434d-a95a-9520ba64467a', 'default', 'robot_rule_1774889033', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T16:43:55.059099', '2026-03-30T16:44:07.943025', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('5c79c659-4623-453f-b888-810a67b9d921', 'default', 'robot_rule_1774943450', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T07:50:51.405433', '2026-03-31T07:50:55.886509', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('612d26d9-a3ce-4ca0-ad38-8a5c07baad23', 'default', 'robot_rule_1774955206', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T11:06:48.383047', '2026-03-31T11:07:00.040866', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('66af3cda-1e52-4992-883e-46eab3d16726', 'default', 'robot_rule_1774185764', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:22:47.180143', '2026-03-22T13:23:06.259346', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('6821d950-d8fd-43ed-aec1-d45ebd86e4b9', 'default', 'robot_rule_1774187120', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:45:22.987072', '2026-03-22T13:45:42.501209', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('69fa29c7-b531-42ed-ace6-08f6b816ec5c', 'default', 'robot_rule_1773480999', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T09:36:40.197239', '2026-03-14T09:36:48.083957', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('704c7f68-c70c-43b6-abe8-6781b433d56b', 'default', 'robot_rule_1773574071', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T11:27:51.854521', '2026-03-15T11:28:00.1859', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('75d61718-2662-4725-811d-4c6f8901959f', 'default', 'robot_rule_1773573933', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T11:25:34.239862', '2026-03-15T11:25:43.176511', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('7b3cb240-8c41-454b-ad1a-34bf9ea44102', 'default', 'robot_rule_1774430996', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-25T09:29:58.601968', '2026-03-25T09:30:17.056132', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('7e4dc482-8e1a-414b-8014-ed5e6061dbd8', 'default', 'robot_rule_1773733072', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-17T07:37:54.320718', '2026-03-17T07:38:11.771689', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('8317964d-f64f-4728-802f-535e14ee6b71', 'default', 'robot_rule_1774185174', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:12:57.046509', '2026-03-22T13:13:16.475623', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('8329ddc1-4401-4879-a1ed-6b844168fd08', 'default', 'robot_rule_1775026170', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-01T06:49:32.137859', '2026-04-01T06:49:45.99786', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('8b392270-9ef0-4768-bc07-597302a1e816', 'default', 'robot_rule_1774939421', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T06:43:41.9886', '2026-03-31T06:43:46.807503', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('91ce9f99-91a0-4790-aa07-25d03e1fce4f', 'default', 'robot_rule_1774942061', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T07:27:41.575278', '2026-03-31T07:27:45.761368', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('9243f0b0-5820-4e06-9fc5-7fe8431336ff', 'default', 'robot_rule_1774952454', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T10:20:56.415972', '2026-03-31T10:21:08.027164', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('9c045d77-c253-4c22-a0dd-dec9083e6266', 'default', 'robot_rule_1774906428', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T21:33:48.914121', '2026-03-30T21:33:52.015758', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('9cbc0780-9750-414a-8802-f612230402ad', 'default', 'robot_rule_1773988736', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T06:38:58.939806', '2026-03-20T06:39:18.270401', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('9fa6d81b-6262-42b8-a8e7-e546cd045fc8', 'default', 'robot_rule_1774958737', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-31T12:05:39.699832', '2026-03-31T12:05:52.024517', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('a1f14324-d6cd-4669-8a74-ed653b609543', 'default', 'robot_rule_1773573523', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-15T11:18:44.082734', '2026-03-15T11:18:52.699843', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('b5000000-0000-0000-0001-000000000001', 'default', 'rule_task_reassigned', 'Task Reassigned', 'Notify the new assignee when a task is reassigned to them', 'task_reassigned', 'grc', 'task_reassigned', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000002', 'default', 'rule_task_overdue', 'Task Overdue', 'Notify the assignee when a task passes its due date', 'task_overdue', 'grc', 'task_overdue', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000003', 'default', 'rule_task_submitted', 'Task Submitted for Review', 'Notify the reviewer when a task is submitted', 'task_submitted', 'grc', 'task_submitted', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000004', 'default', 'rule_task_approved', 'Task Approved', 'Notify the assignee when their task is approved', 'task_approved', 'grc', 'task_approved', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000005', 'default', 'rule_task_rejected', 'Task Sent Back', 'Notify the assignee when their task is sent back for rework', 'task_rejected', 'grc', 'task_rejected', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000010', 'default', 'rule_comment_mention', 'Mentioned in Comment', 'Notify a user when they are mentioned in a comment', 'comment_mention', 'grc', 'comment_mention', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000011', 'default', 'rule_comment_reply', 'Reply to Comment', 'Notify a user when someone replies to their comment', 'comment_reply', 'grc', 'comment_reply', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000020', 'default', 'rule_risk_assigned', 'Risk Assigned', 'Notify the owner when a risk is assigned to them', 'risk_assigned', 'grc', 'risk_assigned', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000021', 'default', 'rule_risk_review_due', 'Risk Review Due', 'Notify the owner when a risk review is approaching', 'risk_review_due', 'grc', 'risk_review_due', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000022', 'default', 'rule_risk_status_changed', 'Risk Status Changed', 'Notify relevant parties when a risk status changes', 'risk_status_changed', 'grc', 'risk_status_changed', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000023', 'default', 'rule_treatment_plan_assigned', 'Treatment Plan Assigned', 'Notify the owner when a risk treatment plan is assigned', 'treatment_plan_assigned', 'grc', 'treatment_plan_assigned', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000030', 'default', 'rule_finding_assigned', 'Finding Assigned', 'Notify the owner when a finding is assigned to them', 'finding_assigned', 'grc', 'finding_assigned', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000031', 'default', 'rule_finding_response_needed', 'Finding Response Needed', 'Notify the owner when a finding requires a response', 'finding_response_needed', 'grc', 'finding_response_needed', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0001-000000000032', 'default', 'rule_finding_reviewed', 'Finding Reviewed', 'Notify the owner when their finding response is reviewed', 'finding_reviewed', 'grc', 'finding_reviewed', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:53.424545', '2026-04-02T05:39:53.424545', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000001', 'default', 'rule_assessment_completed', 'Assessment Completed', 'Notify relevant parties when an assessment is completed', 'assessment_completed', 'grc', 'assessment_completed', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000002', 'default', 'rule_engagement_status_changed', 'Engagement Status Changed', 'Notify relevant parties when an engagement status changes', 'engagement_status_changed', 'grc', 'engagement_status_changed', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000003', 'default', 'rule_report_ready', 'Report Ready', 'Notify the requester when a report is ready to download', 'report_ready', 'grc', 'report_ready', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000004', 'default', 'rule_report_failed', 'Report Generation Failed', 'Notify the requester when report generation fails', 'report_failed', 'grc', 'report_failed', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000005', 'default', 'rule_approval_required', 'Approval Required', 'Notify the approver when an item requires their approval', 'approval_required', 'grc', 'approval_required', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000006', 'default', 'rule_approval_expired', 'Approval Request Expired', 'Notify the requester when an approval request expires', 'approval_expired', 'grc', 'approval_expired', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000007', 'default', 'rule_approval_rejected', 'Approval Rejected', 'Notify the requester when their approval request is rejected', 'approval_rejected', 'grc', 'approval_rejected', 'specific_users', NULL, 'high', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000008', 'default', 'rule_ticket_assigned', 'Feedback Ticket Assigned', 'Notify the assignee when a feedback ticket is assigned to them', 'ticket_assigned', 'grc', 'ticket_assigned', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('b5000000-0000-0000-0002-000000000009', 'default', 'rule_ticket_status_changed', 'Ticket Status Changed', 'Notify the submitter when their ticket status changes', 'ticket_status_changed', 'grc', 'ticket_status_changed', 'specific_users', NULL, 'normal', 0, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-04-02T05:39:59.441022', '2026-04-02T05:39:59.441022', NULL, NULL, NULL, NULL),
      ('c3fe7e32-d9bb-4379-93c8-aa4ce58df13d', 'default', 'robot_rule_1774185957', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-22T13:25:59.970308', '2026-03-22T13:26:20.33479', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('c5bb0ad7-251e-4d30-99e7-d5f524936e41', 'default', 'robot_rule_1774872905', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T12:15:05.411041', '2026-03-30T12:15:09.602834', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('cebd843b-447e-49cf-9fc7-e3accbac744f', 'default', 'robot_rule_1774873411', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T12:23:33.329364', '2026-03-30T12:23:45.939403', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL),
      ('d325733f-c786-4102-815b-54fcaa7a6fe5', 'default', 'robot_rule_1774871418', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T11:50:18.481463', '2026-03-30T11:50:21.786196', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('d53d5196-0c82-44d7-aabd-c20d219f05c0', 'default', 'robot_rule_1773481229', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-14T09:40:30.5937', '2026-03-14T09:40:39.114883', '819f347c-e619-4a43-8755-2c80e5fa572e', '819f347c-e619-4a43-8755-2c80e5fa572e', NULL, NULL),
      ('dec71fae-7a44-4c8c-b626-072e885d2163', 'default', 'rule_magic_link_login', 'Magic Link Login Notification', 'Send magic link email when user requests passwordless login', 'magic_link_requested', 'auth', 'magic_link_login', 'actor', NULL, 'critical', 0, TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, '2026-03-20T03:54:34.828026', '2026-03-20T03:54:34.828026', NULL, NULL, NULL, NULL),
      ('e5e6f980-2b44-4f8a-98d7-e15cf0808b49', 'default', 'robot_rule_1773988770', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-20T06:39:32.889238', '2026-03-20T06:39:51.282879', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('e69d5c3d-0003-4334-9501-ec83e2bc91ad', 'default', 'robot_rule_1774905543', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T21:19:04.370223', '2026-03-30T21:19:07.787241', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('e9c2f1a6-b435-4d74-bb5c-0ff3bd6f68fd', 'default', 'robot_rule_1774253784', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-23T08:16:26.84387', '2026-03-23T08:16:44.220996', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', 'ba28b1db-4232-4f23-8a1b-b01df31e40a8', NULL, NULL),
      ('fcf4d3be-27c7-4f89-b8ed-c79e307029a9', 'default', 'robot_rule_1774869970', 'Updated Robot Rule', 'Rule created by Robot Framework tests', 'login_succeeded', 'auth', 'login_from_new_device', 'actor', NULL, 'high', 30, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, '2026-03-30T11:26:12.574885', '2026-03-30T11:26:25.476092', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', 'af88f921-2e07-48aa-a3e5-c556a2b2c223', NULL, NULL)
  ON CONFLICT (tenant_key, code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, source_event_type = EXCLUDED.source_event_type, source_event_category = EXCLUDED.source_event_category, notification_type_code = EXCLUDED.notification_type_code, recipient_strategy = EXCLUDED.recipient_strategy, recipient_filter_json = EXCLUDED.recipient_filter_json, priority_code = EXCLUDED.priority_code, delay_seconds = EXCLUDED.delay_seconds, is_active = EXCLUDED.is_active, is_disabled = EXCLUDED.is_disabled, is_deleted = EXCLUDED.is_deleted, is_test = EXCLUDED.is_test, is_system = EXCLUDED.is_system, is_locked = EXCLUDED.is_locked, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by, deleted_at = EXCLUDED.deleted_at, deleted_by = EXCLUDED.deleted_by;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.18_lnk_notification_rule_channels (107 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."18_lnk_notification_rule_channels" (id, rule_id, channel_code, template_code, is_active, created_at, updated_at)
  VALUES
      ('000657ec-7316-4cc3-b698-864ca6368316', '57b4d3f7-d6c8-434d-a95a-9520ba64467a', 'email', 'robot_test_template_1774889001', TRUE, '2026-03-30T16:44:09.692182', '2026-03-30T16:44:09.692182'),
      ('0407b9f3-46cb-47eb-954b-f95983f38935', '38fe904f-e2ba-4c20-af67-87c5bdb81cad', 'email', 'robot_test_template_1774247569', TRUE, '2026-03-23T06:34:10.333567', '2026-03-23T06:34:10.333567'),
      ('0df29cfb-cd48-49d9-97c4-1c3a7df34f10', '30000000-0000-0000-0000-000000000002', 'email', 'otp_verification_email', TRUE, '2026-03-20T04:27:43.910015', '2026-03-20T04:27:43.910015'),
      ('0eb02d92-40c6-46ad-9278-89ce5dcef73e', '8317964d-f64f-4728-802f-535e14ee6b71', 'web_push', NULL, TRUE, '2026-03-22T13:13:25.560446', '2026-03-22T13:13:25.560446'),
      ('13334934-1406-4cbd-a2e6-963f94d73ca9', '7e4dc482-8e1a-414b-8014-ed5e6061dbd8', 'email', 'robot_test_template_1773733027', TRUE, '2026-03-17T07:38:14.889228', '2026-03-17T07:38:14.889228'),
      ('137b901c-3bd6-4592-9942-37706018d6f1', 'a1f14324-d6cd-4669-8a74-ed653b609543', 'email', 'robot_test_template_1773573472', TRUE, '2026-03-15T11:18:53.957787', '2026-03-15T11:18:53.957787'),
      ('1669e403-6660-41fd-b14c-16b4d1001bbc', 'e69d5c3d-0003-4334-9501-ec83e2bc91ad', 'email', 'robot_test_template_1774905536', TRUE, '2026-03-30T21:19:09.14385', '2026-03-30T21:19:09.14385'),
      ('176805f4-a1b7-471a-b604-b621e4489e8e', '5c79c659-4623-453f-b888-810a67b9d921', 'web_push', NULL, TRUE, '2026-03-31T07:50:57.574833', '2026-03-31T07:50:57.574833'),
      ('18e6f3f3-aa5c-4262-8dac-cf5c0d98b3e7', '66af3cda-1e52-4992-883e-46eab3d16726', 'email', 'robot_test_template_1774185716', TRUE, '2026-03-22T13:23:11.753925', '2026-03-22T13:23:11.753925'),
      ('1ba60aa6-c38d-4908-9960-361ecfb1f4de', '30000000-0000-0000-0000-000000000001', 'email', 'password_reset', TRUE, '2026-03-20T04:27:43.910015', '2026-03-20T04:27:43.910015'),
      ('1d9559b3-bdce-4bb3-9e41-ca59d15c7771', '9fa6d81b-6262-42b8-a8e7-e546cd045fc8', 'web_push', NULL, TRUE, '2026-03-31T12:05:55.51345', '2026-03-31T12:05:55.51345'),
      ('1e603b08-b9ba-471b-9ca8-f364b65f0adf', 'd53d5196-0c82-44d7-aabd-c20d219f05c0', 'web_push', NULL, TRUE, '2026-03-14T09:40:41.627469', '2026-03-14T09:40:41.627469'),
      ('238702ee-5fd7-4faf-b051-1aa5431717fb', '38fe904f-e2ba-4c20-af67-87c5bdb81cad', 'web_push', NULL, TRUE, '2026-03-23T06:34:12.942064', '2026-03-23T06:34:12.942064'),
      ('25e2f826-5fa5-4264-88ff-60db16d8ce92', '704c7f68-c70c-43b6-abe8-6781b433d56b', 'web_push', NULL, TRUE, '2026-03-15T11:28:02.90706', '2026-03-15T11:28:02.90706'),
      ('2b3efa79-9821-4d4f-9ed9-8de74dbe89e6', '9fa6d81b-6262-42b8-a8e7-e546cd045fc8', 'email', 'robot_test_template_1774958707', TRUE, '2026-03-31T12:05:53.737782', '2026-03-31T12:05:53.737782'),
      ('2ee0b7a3-10f7-4ca5-aef3-0551ea020b2a', 'c3fe7e32-d9bb-4379-93c8-aa4ce58df13d', 'email', 'robot_test_template_1774185907', TRUE, '2026-03-22T13:26:26.034373', '2026-03-22T13:26:26.034373'),
      ('2feb5d8b-0b17-413c-a303-014704d0378a', 'd325733f-c786-4102-815b-54fcaa7a6fe5', 'email', 'robot_test_template_1774871409', TRUE, '2026-03-30T11:50:22.254709', '2026-03-30T11:50:22.254709'),
      ('30e4ad50-d85e-410e-b933-ae4be50d7f3d', '0611c619-330b-4afa-b8af-14cc9c1d2f21', 'web_push', NULL, TRUE, '2026-03-31T05:38:51.933339', '2026-03-31T05:38:51.933339'),
      ('320b17af-5d51-4f2e-8db9-c6144868a8cf', 'e69d5c3d-0003-4334-9501-ec83e2bc91ad', 'web_push', NULL, TRUE, '2026-03-30T21:19:09.728349', '2026-03-30T21:19:09.728349'),
      ('34aca51f-a44e-40c6-bdcf-c5c79370120a', '461b758c-f394-4af8-b589-c2799236d412', 'web_push', NULL, TRUE, '2026-03-14T08:52:01.993274', '2026-03-14T08:52:01.993274'),
      ('3dcbfd9d-1d67-4ae6-9cfc-64d86e9d27d0', '11eb8495-8ae3-491d-b37a-a003a2d8d76c', 'web_push', NULL, TRUE, '2026-03-16T10:48:14.555898', '2026-03-16T10:48:14.555898'),
      ('3fe2647e-649c-42e9-80c4-db2ef20b29ce', '9c045d77-c253-4c22-a0dd-dec9083e6266', 'web_push', NULL, TRUE, '2026-03-30T21:33:53.677997', '2026-03-30T21:33:53.677997'),
      ('4448e26d-def6-4739-9b12-fbdfd3deae49', '11eb8495-8ae3-491d-b37a-a003a2d8d76c', 'email', 'robot_test_template_1773657987', TRUE, '2026-03-16T10:48:10.15514', '2026-03-16T10:48:10.15514'),
      ('4583602e-7c61-4294-be08-88cdf40b2434', '8317964d-f64f-4728-802f-535e14ee6b71', 'email', 'robot_test_template_1774185125', TRUE, '2026-03-22T13:13:22.645251', '2026-03-22T13:13:22.645251'),
      ('502bdbe2-3efc-4f52-9f92-5de000b5543b', '273fb676-c284-4668-b543-a8ee99890506', 'email', 'robot_test_template_1773574475', TRUE, '2026-03-15T11:35:19.550702', '2026-03-15T11:35:19.550702'),
      ('52d7c940-e990-4b56-9e21-727e480293c5', '18f0c75e-edae-46bf-8ec3-ebba8e7303e4', 'email', 'robot_test_template_1774406073', TRUE, '2026-03-25T02:35:51.20968', '2026-03-25T02:35:51.20968'),
      ('54a9de85-ee56-4094-bbb0-6194032fbb36', '196ccffe-cf09-41f0-8edc-3084657078de', 'email', 'robot_test_template_1774804695', TRUE, '2026-03-29T17:19:29.372953', '2026-03-29T17:19:29.372953'),
      ('555068bd-5f2d-4673-aa72-2fd3fb4b5c77', '9cbc0780-9750-414a-8802-f612230402ad', 'email', 'robot_test_template_1773988688', TRUE, '2026-03-20T06:39:21.622621', '2026-03-20T06:39:21.622621'),
      ('578671e9-1505-4b07-ba7a-309abf6df25b', '461b758c-f394-4af8-b589-c2799236d412', 'email', 'robot_test_template_1773478291', TRUE, '2026-03-14T08:52:00.835253', '2026-03-14T08:52:00.835253'),
      ('5838770d-ca1b-4662-b4bf-9e8a3ffaadac', '137da862-0695-49de-ba16-0470027ac754', 'web_push', NULL, TRUE, '2026-04-01T05:33:17.931107', '2026-04-01T05:33:17.931107'),
      ('58c0dea5-e57b-4243-80ef-b0a667de0db5', '69fa29c7-b531-42ed-ace6-08f6b816ec5c', 'web_push', NULL, TRUE, '2026-03-14T09:36:50.422527', '2026-03-14T09:36:50.422527'),
      ('5c22d2bf-be9c-41f0-bc8b-4ce1b0f1b2c3', '66af3cda-1e52-4992-883e-46eab3d16726', 'web_push', NULL, TRUE, '2026-03-22T13:23:14.504132', '2026-03-22T13:23:14.504132'),
      ('5cdf6d04-6e29-436c-a44f-c456446dc4ee', 'e9c2f1a6-b435-4d74-bb5c-0ff3bd6f68fd', 'web_push', NULL, TRUE, '2026-03-23T08:16:52.982289', '2026-03-23T08:16:52.982289'),
      ('623ecf6c-4a29-4efd-abf3-20dd910bd27c', '57b4d3f7-d6c8-434d-a95a-9520ba64467a', 'web_push', NULL, TRUE, '2026-03-30T16:44:11.5938', '2026-03-30T16:44:11.5938'),
      ('64100556-39df-49bf-a1fb-dd7dc2b9d7c8', '7b3cb240-8c41-454b-ad1a-34bf9ea44102', 'web_push', NULL, TRUE, '2026-03-25T09:30:25.058855', '2026-03-25T09:30:25.058855'),
      ('648a05d3-ac22-4533-a0e5-de99545eaf0e', 'fcf4d3be-27c7-4f89-b8ed-c79e307029a9', 'web_push', NULL, TRUE, '2026-03-30T11:26:29.057214', '2026-03-30T11:26:29.057214'),
      ('65acae6e-eacc-42ee-a1ab-69ad3a7f9cc3', 'fcf4d3be-27c7-4f89-b8ed-c79e307029a9', 'email', 'robot_test_template_1774869936', TRUE, '2026-03-30T11:26:27.240672', '2026-03-30T11:26:27.240672'),
      ('6e85a2a1-f431-4fa0-bd27-19a88026116c', '6821d950-d8fd-43ed-aec1-d45ebd86e4b9', 'email', 'robot_test_template_1774187045', TRUE, '2026-03-22T13:45:48.350246', '2026-03-22T13:45:48.350246'),
      ('6f3f4586-ef7d-4dc6-9ded-c7e2f959633e', '8329ddc1-4401-4879-a1ed-6b844168fd08', 'email', 'robot_test_template_1775026140', TRUE, '2026-04-01T06:49:48.289295', '2026-04-01T06:49:48.289295'),
      ('7bf61f2e-de68-4bb6-937c-b2e381fef0b1', '5c79c659-4623-453f-b888-810a67b9d921', 'email', 'robot_test_template_1774943437', TRUE, '2026-03-31T07:50:56.680821', '2026-03-31T07:50:56.680821'),
      ('80466f66-374a-49b2-a2c7-00a454b03742', 'dec71fae-7a44-4c8c-b626-072e885d2163', 'email', 'magic_link_login_email', TRUE, '2026-03-20T04:27:43.910015', '2026-03-20T04:27:43.910015'),
      ('805ac51f-2a24-4a0f-a90a-c1ea4c8539f6', '75d61718-2662-4725-811d-4c6f8901959f', 'web_push', NULL, TRUE, '2026-03-15T11:25:45.582888', '2026-03-15T11:25:45.582888'),
      ('82156aa3-6117-4c8d-a37d-acb38022d2c7', '196ccffe-cf09-41f0-8edc-3084657078de', 'web_push', NULL, TRUE, '2026-03-29T17:19:32.378565', '2026-03-29T17:19:32.378565'),
      ('83a0647b-8f1f-42a7-a82c-bd5191ea2ce1', '6821d950-d8fd-43ed-aec1-d45ebd86e4b9', 'web_push', NULL, TRUE, '2026-03-22T13:45:51.405335', '2026-03-22T13:45:51.405335'),
      ('86e44713-8609-4aef-9034-d258a272e9ab', '137da862-0695-49de-ba16-0470027ac754', 'email', 'robot_test_template_1775021551', TRUE, '2026-04-01T05:33:16.123408', '2026-04-01T05:33:16.123408'),
      ('8afdf4dd-4872-4d2c-8ab6-e25326ff6a2e', 'cebd843b-447e-49cf-9fc7-e3accbac744f', 'email', 'robot_test_template_1774873384', TRUE, '2026-03-30T12:23:47.841491', '2026-03-30T12:23:47.841491'),
      ('8db9b850-ae88-42e2-916a-dc4ebc53b5b3', '8b392270-9ef0-4768-bc07-597302a1e816', 'email', 'robot_test_template_1774939411', TRUE, '2026-03-31T06:43:47.441019', '2026-03-31T06:43:47.441019'),
      ('8e2a14e1-7761-438c-bfe2-0e3966667bf4', 'd325733f-c786-4102-815b-54fcaa7a6fe5', 'web_push', NULL, TRUE, '2026-03-30T11:50:22.827992', '2026-03-30T11:50:22.827992'),
      ('92ab9337-b0bc-47a7-8494-2d9888ce732b', '69fa29c7-b531-42ed-ace6-08f6b816ec5c', 'email', 'robot_test_template_1773480977', TRUE, '2026-03-14T09:36:49.242976', '2026-03-14T09:36:49.242976'),
      ('97a330cb-6e37-4dca-800a-7f30f5fe7cba', '75d61718-2662-4725-811d-4c6f8901959f', 'email', 'robot_test_template_1773573900', TRUE, '2026-03-15T11:25:44.373362', '2026-03-15T11:25:44.373362'),
      ('994b3a29-5b5b-48af-9d99-a1fb83788c84', '8329ddc1-4401-4879-a1ed-6b844168fd08', 'web_push', NULL, TRUE, '2026-04-01T06:49:50.302086', '2026-04-01T06:49:50.302086'),
      ('a200c2c2-fe10-455c-aa45-22053be9fa38', 'e5e6f980-2b44-4f8a-98d7-e15cf0808b49', 'email', 'robot_test_template_1773988723', TRUE, '2026-03-20T06:39:54.667081', '2026-03-20T06:39:54.667081'),
      ('a90b37f2-92ea-4776-840d-0ab626db1633', '91ce9f99-91a0-4790-aa07-25d03e1fce4f', 'web_push', NULL, TRUE, '2026-03-31T07:27:47.237433', '2026-03-31T07:27:47.237433'),
      ('ad15d89f-d35b-40da-9599-8f037ca58bc2', 'e5e6f980-2b44-4f8a-98d7-e15cf0808b49', 'web_push', NULL, TRUE, '2026-03-20T06:39:57.537595', '2026-03-20T06:39:57.537595'),
      ('ad62d145-36b1-4a35-9f69-4a460f023f45', '8b392270-9ef0-4768-bc07-597302a1e816', 'web_push', NULL, TRUE, '2026-03-31T06:43:48.041203', '2026-03-31T06:43:48.041203'),
      ('afe57ba3-13b5-4dcc-9a50-b5726dee6172', '9c045d77-c253-4c22-a0dd-dec9083e6266', 'email', 'robot_test_template_1774906421', TRUE, '2026-03-30T21:33:53.198934', '2026-03-30T21:33:53.198934'),
      ('b0000000-0000-0000-0020-000000000001', '30000000-0000-0000-0000-000000000020', 'email', 'workspace_invite_email', TRUE, '2026-03-31T05:29:14.925152', '2026-03-31T05:29:14.925152'),
      ('b0000000-0000-0000-0021-000000000001', '30000000-0000-0000-0000-000000000021', 'email', 'workspace_invite_grc_email', TRUE, '2026-03-31T05:29:14.925152', '2026-03-31T05:29:14.925152'),
      ('b0000000-0000-0000-0022-000000000001', '30000000-0000-0000-0000-000000000022', 'email', 'engagement_access_granted_email', TRUE, '2026-03-31T05:29:14.925152', '2026-03-31T05:29:14.925152'),
      ('b0000000-0000-0000-0030-000000000001', '30000000-0000-0000-0000-000000000030', 'email', 'task_assigned_email', TRUE, '2026-04-02T05:25:01.757746', '2026-04-02T05:25:01.757746'),
      ('b0000000-0000-0000-0031-000000000001', '30000000-0000-0000-0000-000000000031', 'email', 'task_status_changed_email', TRUE, '2026-04-02T05:25:01.757746', '2026-04-02T05:25:01.757746'),
      ('b0000000-0000-0000-0032-000000000001', '30000000-0000-0000-0000-000000000032', 'email', 'task_comment_added_email', TRUE, '2026-04-02T05:25:01.757746', '2026-04-02T05:25:01.757746'),
      ('b0000000-0000-0000-0033-000000000001', '30000000-0000-0000-0000-000000000033', 'email', 'task_feedback_received_email', TRUE, '2026-04-02T05:25:01.757746', '2026-04-02T05:25:01.757746'),
      ('b3b24959-c5cf-40df-8e28-b5e07e2a3069', '9243f0b0-5820-4e06-9fc5-7fe8431336ff', 'web_push', NULL, TRUE, '2026-03-31T10:21:11.40258', '2026-03-31T10:21:11.40258'),
      ('b5000000-0000-0000-0001-00000000b001', 'b5000000-0000-0000-0001-000000000001', 'email', 'task_reassigned_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b002', 'b5000000-0000-0000-0001-000000000002', 'email', 'task_overdue_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b003', 'b5000000-0000-0000-0001-000000000003', 'email', 'task_submitted_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b004', 'b5000000-0000-0000-0001-000000000004', 'email', 'task_approved_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b005', 'b5000000-0000-0000-0001-000000000005', 'email', 'task_rejected_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b010', 'b5000000-0000-0000-0001-000000000010', 'email', 'comment_mention_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b011', 'b5000000-0000-0000-0001-000000000011', 'email', 'comment_reply_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b020', 'b5000000-0000-0000-0001-000000000020', 'email', 'risk_assigned_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b021', 'b5000000-0000-0000-0001-000000000021', 'email', 'risk_review_due_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b022', 'b5000000-0000-0000-0001-000000000022', 'email', 'risk_status_changed_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b023', 'b5000000-0000-0000-0001-000000000023', 'email', 'treatment_plan_assigned_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b030', 'b5000000-0000-0000-0001-000000000030', 'email', 'finding_assigned_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b031', 'b5000000-0000-0000-0001-000000000031', 'email', 'finding_response_needed_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0001-00000000b032', 'b5000000-0000-0000-0001-000000000032', 'email', 'finding_reviewed_email', TRUE, '2026-04-02T05:39:53.452547', '2026-04-02T05:39:53.452547'),
      ('b5000000-0000-0000-0002-00000000b001', 'b5000000-0000-0000-0002-000000000001', 'email', 'assessment_completed_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b5000000-0000-0000-0002-00000000b002', 'b5000000-0000-0000-0002-000000000002', 'email', 'engagement_status_changed_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b5000000-0000-0000-0002-00000000b003', 'b5000000-0000-0000-0002-000000000003', 'email', 'report_ready_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b5000000-0000-0000-0002-00000000b004', 'b5000000-0000-0000-0002-000000000004', 'email', 'report_failed_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b5000000-0000-0000-0002-00000000b005', 'b5000000-0000-0000-0002-000000000005', 'email', 'approval_required_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b5000000-0000-0000-0002-00000000b006', 'b5000000-0000-0000-0002-000000000006', 'email', 'approval_expired_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b5000000-0000-0000-0002-00000000b007', 'b5000000-0000-0000-0002-000000000007', 'email', 'approval_rejected_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b5000000-0000-0000-0002-00000000b008', 'b5000000-0000-0000-0002-000000000008', 'email', 'ticket_assigned_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b5000000-0000-0000-0002-00000000b009', 'b5000000-0000-0000-0002-000000000009', 'email', 'ticket_status_changed_email', TRUE, '2026-04-02T05:39:59.470529', '2026-04-02T05:39:59.470529'),
      ('b6424174-ad28-4baf-aa4d-c81f7b3fe860', '612d26d9-a3ce-4ca0-ad38-8a5c07baad23', 'web_push', NULL, TRUE, '2026-03-31T11:07:03.244986', '2026-03-31T11:07:03.244986'),
      ('cc060c02-06ab-4afc-b432-f43ddd79c949', 'd53d5196-0c82-44d7-aabd-c20d219f05c0', 'email', 'robot_test_template_1773481201', TRUE, '2026-03-14T09:40:40.348086', '2026-03-14T09:40:40.348086'),
      ('cea8d9d4-138a-4972-b38e-5ccb4f261103', '91ce9f99-91a0-4790-aa07-25d03e1fce4f', 'email', 'robot_test_template_1774942051', TRUE, '2026-03-31T07:27:46.55716', '2026-03-31T07:27:46.55716'),
      ('cf79268f-d83b-4816-aa2e-318cc3c537ef', '273fb676-c284-4668-b543-a8ee99890506', 'web_push', NULL, TRUE, '2026-03-15T11:35:20.864551', '2026-03-15T11:35:20.864551'),
      ('cfb45647-50e5-41e2-8db0-2d357f4af6e0', '9cbc0780-9750-414a-8802-f612230402ad', 'web_push', NULL, TRUE, '2026-03-20T06:39:24.588555', '2026-03-20T06:39:24.588555'),
      ('d29769fe-f965-4af5-9e1c-95964c486919', '1ac4c744-37b5-4fef-85e7-891b7112e3cc', 'email', 'robot_test_template_1774185929', TRUE, '2026-03-22T13:26:46.305164', '2026-03-22T13:26:46.305164'),
      ('d2b2dcf1-612e-4be7-a69f-ccaf37d34b57', 'c5bb0ad7-251e-4d30-99e7-d5f524936e41', 'email', 'robot_test_template_1774872896', TRUE, '2026-03-30T12:15:10.153044', '2026-03-30T12:15:10.153044'),
      ('d2e30df5-da29-4bbc-bdb9-aba83b3e35f3', '0611c619-330b-4afa-b8af-14cc9c1d2f21', 'email', 'robot_test_template_1774935512', TRUE, '2026-03-31T05:38:51.291913', '2026-03-31T05:38:51.291913'),
      ('d432b6be-b614-46ad-8c20-6529f85945c2', '704c7f68-c70c-43b6-abe8-6781b433d56b', 'email', 'robot_test_template_1773574043', TRUE, '2026-03-15T11:28:01.4756', '2026-03-15T11:28:01.4756'),
      ('deed7a3a-509a-484e-816d-ba6e3f5d97dc', 'a1f14324-d6cd-4669-8a74-ed653b609543', 'web_push', NULL, TRUE, '2026-03-15T11:18:55.237664', '2026-03-15T11:18:55.237664'),
      ('e5152d3d-9cd5-41bb-b555-59a47ef43a76', 'c3fe7e32-d9bb-4379-93c8-aa4ce58df13d', 'web_push', NULL, TRUE, '2026-03-22T13:26:28.82923', '2026-03-22T13:26:28.82923'),
      ('e69d0441-d7b3-47dc-9e1a-ac8cce56c940', 'e9c2f1a6-b435-4d74-bb5c-0ff3bd6f68fd', 'email', 'robot_test_template_1774253729', TRUE, '2026-03-23T08:16:50.484229', '2026-03-23T08:16:50.484229'),
      ('e7b850e0-7c23-4368-87e0-50f657f70d1c', '612d26d9-a3ce-4ca0-ad38-8a5c07baad23', 'email', 'robot_test_template_1774955177', TRUE, '2026-03-31T11:07:01.632098', '2026-03-31T11:07:01.632098'),
      ('e7dc2046-82d8-417d-80ec-55a3e5b21007', 'cebd843b-447e-49cf-9fc7-e3accbac744f', 'web_push', NULL, TRUE, '2026-03-30T12:23:49.639333', '2026-03-30T12:23:49.639333'),
      ('ed321551-795e-41d0-b3bd-626a886ad7af', '18f0c75e-edae-46bf-8ec3-ebba8e7303e4', 'web_push', NULL, TRUE, '2026-03-25T02:35:54.849511', '2026-03-25T02:35:54.849511'),
      ('ef269ab6-ab72-4748-99df-1598ef6904b0', 'c5bb0ad7-251e-4d30-99e7-d5f524936e41', 'web_push', NULL, TRUE, '2026-03-30T12:15:10.724948', '2026-03-30T12:15:10.724948'),
      ('f065e79a-4ab4-46f7-83b0-8f00e7ec1a0a', '7e4dc482-8e1a-414b-8014-ed5e6061dbd8', 'web_push', NULL, TRUE, '2026-03-17T07:38:17.358288', '2026-03-17T07:38:17.358288'),
      ('f247340f-482b-49cd-86ed-0871596a656b', '9243f0b0-5820-4e06-9fc5-7fe8431336ff', 'email', 'robot_test_template_1774952425', TRUE, '2026-03-31T10:21:09.668897', '2026-03-31T10:21:09.668897'),
      ('f2c38bfe-aba6-4253-815c-7f518bd69432', '1ac4c744-37b5-4fef-85e7-891b7112e3cc', 'web_push', NULL, TRUE, '2026-03-22T13:26:49.155421', '2026-03-22T13:26:49.155421'),
      ('fe38e416-00e0-491a-9028-e38d001f7b43', '7b3cb240-8c41-454b-ad1a-34bf9ea44102', 'email', 'robot_test_template_1774430945', TRUE, '2026-03-25T09:30:21.057168', '2026-03-25T09:30:21.057168')
  ON CONFLICT (rule_id, channel_code) DO UPDATE SET template_code = EXCLUDED.template_code, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- 03_notifications.19_dtl_rule_conditions (39 rows)
DO $$ BEGIN
  INSERT INTO "03_notifications"."19_dtl_rule_conditions" (id, rule_id, condition_type, field_key, operator, value, value_type, logical_group, sort_order, is_active, created_at, updated_at)
  VALUES
      ('02302653-1080-4485-9667-e1fe67d026ec', '137da862-0695-49de-ba16-0470027ac754', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-04-01T05:33:21.195322', '2026-04-01T05:33:21.195322'),
      ('07c2d26a-3478-43db-9f7d-736c6f6971c3', '9fa6d81b-6262-42b8-a8e7-e546cd045fc8', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-31T12:05:58.941332', '2026-03-31T12:05:58.941332'),
      ('1225deae-e429-4ea5-b9c6-a42aadf1f694', '7b3cb240-8c41-454b-ad1a-34bf9ea44102', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-25T09:30:28.51392', '2026-03-25T09:30:28.51392'),
      ('14ff4305-8dcd-4329-afcf-7ead4e70279c', '5c79c659-4623-453f-b888-810a67b9d921', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-31T07:50:59.12868', '2026-03-31T07:50:59.12868'),
      ('170e1eb6-e71a-4c77-a3bc-be8a757a9a7c', 'e9c2f1a6-b435-4d74-bb5c-0ff3bd6f68fd', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-23T08:16:53.998983', '2026-03-23T08:16:53.998983'),
      ('192563f4-af78-4585-87f5-ca9113447fca', '91ce9f99-91a0-4790-aa07-25d03e1fce4f', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-31T07:27:48.491521', '2026-03-31T07:27:48.491521'),
      ('2be457d1-f46f-4dea-8d8e-6482c183606b', '0611c619-330b-4afa-b8af-14cc9c1d2f21', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-31T05:38:53.509237', '2026-03-31T05:38:53.509237'),
      ('2fdaf3c9-e058-41c0-a716-43742764a4bd', '612d26d9-a3ce-4ca0-ad38-8a5c07baad23', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-31T11:07:06.54312', '2026-03-31T11:07:06.54312'),
      ('38a2c45c-86d1-4c58-90b2-35a68cbe6697', '57b4d3f7-d6c8-434d-a95a-9520ba64467a', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-30T16:44:15.687395', '2026-03-30T16:44:15.687395'),
      ('3ec53e3a-cb69-49c9-b76a-4eff301844f7', '273fb676-c284-4668-b543-a8ee99890506', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-15T11:35:23.470607', '2026-03-15T11:35:23.470607'),
      ('40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000010', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T08:26:29.738975', '2026-03-14T08:26:29.738975'),
      ('47748272-18de-423a-9cb8-40c2934271ec', '196ccffe-cf09-41f0-8edc-3084657078de', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-29T17:19:36.991388', '2026-03-29T17:19:36.991388'),
      ('4918b551-3a34-4590-abf8-c92ebdc64308', '7e4dc482-8e1a-414b-8014-ed5e6061dbd8', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-17T07:38:21.585638', '2026-03-17T07:38:21.585638'),
      ('497b3412-a383-4cb9-bae7-a85801f1ee3a', '9c045d77-c253-4c22-a0dd-dec9083e6266', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-30T21:33:54.052122', '2026-03-30T21:33:54.052122'),
      ('5de152d8-ff65-4b4e-b168-557b426551d6', 'd53d5196-0c82-44d7-aabd-c20d219f05c0', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T09:40:44.190212', '2026-03-14T09:40:44.190212'),
      ('62201318-fcb6-4d3f-b87b-19e670c4ad0a', '9cbc0780-9750-414a-8802-f612230402ad', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-20T06:39:29.328472', '2026-03-20T06:39:29.328472'),
      ('64a763c3-97f0-4ce4-ae15-69979b4f6190', 'd325733f-c786-4102-815b-54fcaa7a6fe5', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-30T11:50:23.806257', '2026-03-30T11:50:23.806257'),
      ('774e83a5-3a37-47ed-8a58-44ba826d5445', 'c3fe7e32-d9bb-4379-93c8-aa4ce58df13d', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:26:31.793525', '2026-03-22T13:26:31.793525'),
      ('7a873499-315c-4cd8-9b46-322bb8c92668', '11eb8495-8ae3-491d-b37a-a003a2d8d76c', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-16T10:48:20.640879', '2026-03-16T10:48:20.640879'),
      ('7fefc4f5-c7f7-4c64-bb66-0536795a1da2', '18f0c75e-edae-46bf-8ec3-ebba8e7303e4', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-25T02:36:00.828537', '2026-03-25T02:36:00.828537'),
      ('827835ec-b57b-4187-ada9-e676b268f9cd', '24691c00-aea9-4378-8ce2-1812625b5453', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T08:49:25.125164', '2026-03-14T08:49:25.125164'),
      ('976e0c6d-de61-40ae-afab-405cb61cdea1', 'cebd843b-447e-49cf-9fc7-e3accbac744f', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-30T12:23:53.636984', '2026-03-30T12:23:53.636984'),
      ('9bd00351-4e1d-44ec-a3ac-4f0c044a00a7', '8329ddc1-4401-4879-a1ed-6b844168fd08', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-04-01T06:49:54.193741', '2026-04-01T06:49:54.193741'),
      ('9da7acbd-9423-4b0a-8a31-5c1897c960fb', '75d61718-2662-4725-811d-4c6f8901959f', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-15T11:25:48.166905', '2026-03-15T11:25:48.166905'),
      ('a1242465-42c7-4bb6-b802-f4a8d89d5810', '8317964d-f64f-4728-802f-535e14ee6b71', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:13:28.299643', '2026-03-22T13:13:28.299643'),
      ('a22537eb-7a49-4dd1-9d50-1c7dfc55f606', 'e69d5c3d-0003-4334-9501-ec83e2bc91ad', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-30T21:19:10.164362', '2026-03-30T21:19:10.164362'),
      ('a65d411c-8d06-4338-b55a-a4e7889cc4fa', '6821d950-d8fd-43ed-aec1-d45ebd86e4b9', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:45:54.370399', '2026-03-22T13:45:54.370399'),
      ('b13b0259-8305-4b87-887f-e0209eddbd77', 'e5e6f980-2b44-4f8a-98d7-e15cf0808b49', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-20T06:40:02.281506', '2026-03-20T06:40:02.281506'),
      ('b2f1cfe6-4301-4f43-9210-4eec0ed95c3e', '704c7f68-c70c-43b6-abe8-6781b433d56b', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-15T11:28:05.44497', '2026-03-15T11:28:05.44497'),
      ('be44259b-44d5-40d3-91f9-7fd9813bf855', '9243f0b0-5820-4e06-9fc5-7fe8431336ff', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-31T10:21:14.659038', '2026-03-31T10:21:14.659038'),
      ('c024d655-6fee-4630-817a-14cf90c19914', '1ac4c744-37b5-4fef-85e7-891b7112e3cc', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:26:52.021999', '2026-03-22T13:26:52.021999'),
      ('c5ad5ff7-fbed-48ac-a0e8-2a8b3c43df82', '66af3cda-1e52-4992-883e-46eab3d16726', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-22T13:23:17.282482', '2026-03-22T13:23:17.282482'),
      ('d517755e-44f8-4616-9494-69b8b31c8e36', 'c5bb0ad7-251e-4d30-99e7-d5f524936e41', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-30T12:15:11.93706', '2026-03-30T12:15:11.93706'),
      ('d567119f-5435-4574-b1aa-02b0a6e06345', '8b392270-9ef0-4768-bc07-597302a1e816', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-31T06:43:49.209967', '2026-03-31T06:43:49.209967'),
      ('d8091905-d111-4799-a678-086338717110', '461b758c-f394-4af8-b589-c2799236d412', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-14T08:52:04.129066', '2026-03-14T08:52:04.129066'),
      ('da748eac-56c5-4c51-8eec-1b94c9a3aaba', 'fcf4d3be-27c7-4f89-b8ed-c79e307029a9', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, '2026-03-30T11:26:32.788642', '2026-03-30T11:26:32.788642'),
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
-- Extracted: 2026-04-02T12:26:44.826091
-- ═════════════════════════════════════════════════════════════════════════════

-- 20_ai.02_dim_agent_types (23 rows)
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
      ('test_linker', 'Test Linker', 'AI agent that links control tests to controls', TRUE, '2026-03-31T12:01:52.554329+00:00'),
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
-- Extracted: 2026-04-02T12:26:57.484679
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
      ('00d8fd3c-46e8-4170-b042-b673063d067e', 'aws_iam', 'AWS IAM', 'cloud_infrastructure', 'iam_role', NULL, 1, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('1cb31ec0-a3c5-4c98-8215-ec24fd900ebf', 'custom_webhook', 'Custom Webhook', 'custom', 'api_key', NULL, 26, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('265e3faa-7dd5-4272-8be0-b2c41d9bb7d7', 'google_workspace', 'Google Workspace', 'identity_provider', 'oauth2', NULL, 11, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('2923e24c-04ad-4bf0-a8d9-d2f05ffb21f8', 'azure_policy', 'Azure Policy', 'cloud_infrastructure', 'oauth2', NULL, 6, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('37cedc8a-1e34-40d1-9663-910d28b789c9', 'mysql', 'MySQL', 'database', 'connection_string', NULL, 18, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('3fad97c6-e0c4-486f-9b9f-f36e437385af', 'aws_config', 'AWS Config', 'cloud_infrastructure', 'iam_role', NULL, 3, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('4a1e19b1-d972-4eb7-8de3-d28200612194', 'custom_api', 'Custom API', 'custom', 'api_key', NULL, 25, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('4dedd9b8-2bed-406c-af91-4ed023d49b2b', 'kubernetes', 'Kubernetes', 'container_orchestration', 'certificate', NULL, 20, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('590b36fc-22c7-4d94-ac6a-a862ad48d57a', 'slack', 'Slack', 'communication', 'oauth2', NULL, 24, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('59905cdb-8d3d-4933-80e9-f7e61dcc76dc', 'gcp_iam', 'GCP IAM', 'cloud_infrastructure', 'oauth2', NULL, 8, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('5c72198e-1003-4ac1-8594-0a588b80e628', 'gitlab', 'GitLab', 'source_control', 'api_key', NULL, 13, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('5ef01b47-ed4a-4840-89cb-27fa9ed487ac', 'mongodb', 'MongoDB', 'database', 'connection_string', NULL, 19, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('7d5e4cfe-7cc2-4b5c-847b-944c5d196034', 'aws_s3', 'AWS S3', 'cloud_infrastructure', 'iam_role', NULL, 4, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('838ff7a7-1b4f-4417-b268-50b1a5a93225', 'gcp_audit', 'GCP Audit Log', 'cloud_infrastructure', 'oauth2', NULL, 9, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('8ce125a9-15e3-4f69-84ed-30f1fad69492', 'datadog', 'Datadog', 'logging_monitoring', 'api_key', NULL, 21, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('a2a7c492-3178-4cca-bc09-4dc556d0b774', 'servicenow', 'ServiceNow', 'itsm', 'basic', NULL, 16, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('b8201b9e-b003-44ba-a3c4-4a4e503a42db', 'github', 'GitHub', 'source_control', 'api_key', NULL, 12, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('c2127312-6052-419a-8a7f-d8ba02552f0a', 'azure_ad', 'Azure Active Directory', 'cloud_infrastructure', 'oauth2', NULL, 5, TRUE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('c249245d-fac4-40f1-b17e-baf638281031', 'jira', 'Jira', 'project_management', 'api_key', NULL, 15, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('d05a98d7-0732-45b9-8abf-0cd873c4919d', 'bitbucket', 'Bitbucket', 'source_control', 'api_key', NULL, 14, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('dd72ed29-badf-482d-9abe-e74eb4b19535', 'okta', 'Okta', 'identity_provider', 'api_key', NULL, 10, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('e228dd6b-b4a9-440d-a718-9ac947732533', 'postgresql', 'PostgreSQL', 'database', 'connection_string', NULL, 17, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('e8a37f12-41df-4415-a812-00fad16e4dfd', 'azure_monitor', 'Azure Monitor', 'cloud_infrastructure', 'oauth2', NULL, 7, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('f0fefd8c-d4ed-4736-9432-8dc6743c032f', 'elastic', 'Elastic', 'logging_monitoring', 'api_key', NULL, 23, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('fae8e707-a57d-41f7-814b-dd2fc4f5d841', 'aws_cloudtrail', 'AWS CloudTrail', 'cloud_infrastructure', 'iam_role', NULL, 2, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00'),
      ('fc71919f-3ec6-4af9-ae37-1cda15abf2ce', 'splunk', 'Splunk', 'logging_monitoring', 'api_key', NULL, 22, FALSE, '2026-03-16T11:40:37.613791+00:00', '2026-03-16T11:40:37.613791+00:00')
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

-- 15_sandbox.14_dim_asset_types (23 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."14_dim_asset_types" (id, code, provider_code, name, description, is_active, created_at)
  VALUES
      ('189cd88e-5e9e-44c9-b94f-bfcf569f9e8b', 'googledirectory_role', 'google_workspace', 'Admin Role', 'A Google Workspace administrator role', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('1fa10ab7-2dae-4d43-b75e-858bb8154ca3', 'github_org', 'github', 'GitHub Organization', 'A GitHub organization', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('222f4b31-0683-4ae4-b681-5356d4afbbab', 'github_deploy_key', 'github', 'GitHub Deploy Key', 'SSH deploy key on repository', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('239c1692-8428-4cfe-a246-ab974ed2c999', 'googledirectory_user', 'google_workspace', 'Google Workspace User', 'A Google Workspace user account', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('24e70b17-f21b-4a4a-b2c2-99cc91f2c342', 'azuread_group', 'azure_ad', 'Azure AD Group', 'An Azure Active Directory security or Microsoft 365 group', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('29198884-f5ed-4c9c-929a-f2e9a4c6f886', 'github_team_member', 'github', 'GitHub Team Member', 'Team membership with role', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('3644644f-9ab4-4225-a2d4-dad9e7da9fc6', 'azure_blob_container', 'azure_storage', 'Azure Blob Container', 'A Blob container within a Storage Account', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('3a91d957-a9e2-4a54-bc39-f9a3a0cfff34', 'azuread_conditional_access_policy', 'azure_ad', 'Conditional Access Policy', 'An Azure AD Conditional Access Policy controlling sign-in conditions', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('419b226b-519d-4f6d-a011-f00840d2c1c6', 'googledirectory_org_unit', 'google_workspace', 'Org Unit', 'A Google Workspace organizational unit', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('54886e86-4837-48f0-81a6-cd52edd8f703', 'github_branch_protection', 'github', 'Branch Protection Rule', 'Branch protection rules for a GitHub repository', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('54e650f5-3b48-4b98-bfe7-d18ab1714a4c', 'github_webhook', 'github', 'GitHub Webhook', 'Repository webhook configuration', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('63c0cd0e-f43b-4390-aaa5-2ac35a8d3243', 'azuread_directory_role', 'azure_ad', 'Directory Role', 'An Azure AD built-in or custom directory role', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('6fb4b404-3ae3-4208-a809-4ed56b9616f5', 'github_repo', 'github', 'GitHub Repository', 'A repository within a GitHub org', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('8ed1d37c-e05d-4876-b6e7-43636a9d13b7', 'azure_storage_network_rule', 'azure_storage', 'Azure Storage Network Rule', 'Network rules for an Azure Storage Account', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('8f8dce00-4d50-45ba-95b0-d690b065dbd4', 'googledirectory_group', 'google_workspace', 'Google Workspace Group', 'A Google Workspace group', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('a396b874-dc6c-44b0-8f0a-8d975a77d27d', 'github_org_member', 'github', 'Organization Member', 'A member of the GitHub organization', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('a8733c73-b34a-4fee-83c5-34ec60812891', 'github_secret', 'github', 'GitHub Secret', 'Organization or repository secret (name only)', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('c237817b-273a-47f1-85a3-c3259b98970a', 'azuread_service_principal', 'azure_ad', 'Service Principal', 'An Azure AD application or managed identity service principal', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('cdd27225-d6b3-4b1e-80ab-f8643a4ebb83', 'github_team', 'github', 'GitHub Team', 'A team within a GitHub organization', TRUE, '2026-03-16T11:40:51.016943+00:00'),
      ('d5670833-bbbc-44d8-9570-9841cc757b38', 'github_collaborator', 'github', 'GitHub Outside Collaborator', 'External collaborator with repo access', TRUE, '2026-03-17T07:19:19.53681+00:00'),
      ('d686dd96-b785-49d2-9e52-d017a3855471', 'azuread_user', 'azure_ad', 'Azure AD User', 'An Azure Active Directory user account', TRUE, '2026-04-01T06:21:33.175552+00:00'),
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

-- 15_sandbox.16_dim_provider_definitions (17 rows)
DO $$ BEGIN
  INSERT INTO "15_sandbox"."16_dim_provider_definitions" (id, code, name, driver_module, default_auth_method, supports_log_collection, supports_steampipe, supports_custom_driver, steampipe_plugin, rate_limit_rpm, config_schema, is_active, is_coming_soon, created_at, updated_at, current_api_version)
  VALUES
      ('08f4acff-93a7-48f4-b0ef-499b4dce7c73', 'gcp_audit', 'GCP Audit Log', 'backend.10_sandbox.18_drivers.gcp_audit.GcpAuditDriver', 'oauth2', TRUE, TRUE, TRUE, 'turbot/gcp', 60, '{"fields": [{"key": "project_id", "type": "text", "label": "GCP Project ID", "order": 1, "required": true, "credential": false, "placeholder": "my-project-123456"}, {"key": "service_account_key_json", "hint": "Required roles: roles/logging.viewer, roles/viewer", "type": "textarea", "label": "Service Account Key (JSON)", "order": 2, "required": true, "credential": true, "placeholder": "{ \"type\": \"service_account\", \"project_id\": \"...\", ... }"}, {"key": "log_filter", "hint": "GCP Logging filter to narrow which audit logs to collect", "type": "text", "label": "Log Filter (optional)", "order": 3, "required": false, "credential": false, "placeholder": "protoPayload.serviceName=iam.googleapis.com"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.596448+00:00', '2026-03-16T12:28:01.596448+00:00', NULL),
      ('15de556b-4f5c-4bb5-ab07-564298109ce6', 'postgresql', 'PostgreSQL', 'backend.10_sandbox.18_drivers.postgresql.PostgreSQLDriver', 'connection_string', FALSE, TRUE, TRUE, 'turbot/postgres', 60, '{"fields": [{"key": "host", "hint": "Hostname or IP address of the PostgreSQL server", "type": "text", "label": "Host", "order": 1, "required": true, "credential": false, "placeholder": "db.mycompany.com"}, {"key": "port", "hint": "Default is 5432", "type": "text", "label": "Port", "order": 2, "required": false, "credential": false, "validation": "^[0-9]{1,5}$", "placeholder": "5432"}, {"key": "database", "type": "text", "label": "Database Name", "order": 3, "required": true, "credential": false, "placeholder": "mydb"}, {"key": "username", "hint": "Use a read-only user — SELECT privileges on relevant schemas", "type": "text", "label": "Username", "order": 4, "required": true, "credential": false, "placeholder": "readonly_user"}, {"key": "password", "type": "password", "label": "Password", "order": 5, "required": true, "credential": true}, {"key": "ssl_mode", "hint": "Recommended: require or verify-full for production", "type": "select", "label": "SSL Mode", "order": 6, "options": ["require", "verify-ca", "verify-full", "prefer", "disable"], "required": false, "credential": false}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.500433+00:00', '2026-03-16T12:28:01.500433+00:00', NULL),
      ('3b27bd44-bc05-4e61-99ab-4c50197dcc8c', 'jira', 'Jira', 'backend.10_sandbox.18_drivers.jira.JiraDriver', 'api_key', FALSE, TRUE, TRUE, 'turbot/jira', 60, '{"fields": [{"key": "base_url", "hint": "Your Jira Cloud or Server URL (no trailing slash)", "type": "text", "label": "Jira Base URL", "order": 1, "required": true, "credential": false, "placeholder": "https://mycompany.atlassian.net"}, {"key": "email", "hint": "Email associated with the API token", "type": "text", "label": "Account Email", "order": 2, "required": true, "credential": false, "placeholder": "admin@mycompany.com"}, {"key": "api_token", "hint": "Created at id.atlassian.com → Security → API Tokens", "type": "password", "label": "API Token", "order": 3, "required": true, "credential": true, "placeholder": "ATATT3xFfGF0..."}, {"key": "project_keys", "hint": "Comma-separated list of Jira project keys to sync. Leave blank to sync all accessible projects.", "type": "text", "label": "Project Keys (optional)", "order": 4, "required": false, "credential": false, "placeholder": "PROJ,INFRA,SEC"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.476464+00:00', '2026-03-16T12:28:01.476464+00:00', NULL),
      ('3f7e7a6a-e124-464e-afa1-8e9843bc2f8e', 'aws_s3', 'AWS S3', 'backend.10_sandbox.18_drivers.aws_s3.AwsS3Driver', 'iam_role', FALSE, TRUE, TRUE, 'turbot/aws', 120, '{"fields": [{"key": "account_id", "type": "text", "label": "AWS Account ID", "order": 1, "required": true, "credential": false, "validation": "^[0-9]{12}$", "placeholder": "123456789012"}, {"key": "region", "type": "select", "label": "Region", "order": 2, "options": ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"], "required": true, "credential": false}, {"key": "bucket_names", "hint": "Comma-separated list. Leave blank to enumerate all accessible buckets.", "type": "text", "label": "Bucket Names (optional)", "order": 3, "required": false, "credential": false, "placeholder": "my-bucket, logs-bucket"}, {"key": "access_key_id", "type": "text", "label": "Access Key ID", "order": 4, "required": false, "credential": true}, {"key": "secret_access_key", "type": "password", "label": "Secret Access Key", "order": 5, "required": false, "credential": true}, {"key": "role_arn", "type": "text", "label": "IAM Role ARN", "order": 6, "required": false, "credential": false, "placeholder": "arn:aws:iam::123456789012:role/KControlReadOnly"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.619054+00:00', '2026-03-16T12:28:01.619054+00:00', NULL),
      ('435b5d13-72a8-4510-9bb1-8a633048a2cd', 'google_workspace', 'Google Workspace', 'backend.10_sandbox.18_drivers.google_workspace.GoogleWorkspaceDriver', 'service_account', FALSE, TRUE, TRUE, 'turbot/googledirectory', 300, '{"fields": [{"key": "admin_email", "hint": "Email of a Google Workspace super admin used for impersonation via Domain-Wide Delegation.", "type": "text", "label": "Admin Email", "order": 1, "required": true, "credential": false, "placeholder": "admin@yourdomain.com"}, {"key": "customer_id", "hint": "Google Workspace customer ID (Admin Console → Account → Profile). Leave blank to auto-detect.", "type": "text", "label": "Customer ID", "order": 2, "required": false, "credential": false, "placeholder": "C01abc123"}, {"key": "service_account_key", "hint": "Full JSON key file content from Google Cloud Console. The service account must have Domain-Wide Delegation enabled.", "type": "textarea", "label": "Service Account Key (JSON)", "order": 3, "required": true, "credential": true, "placeholder": "{\"type\": \"service_account\", \"project_id\": \"...\", ...}"}]}'::jsonb, TRUE, FALSE, '2026-04-01T06:21:33.175552+00:00', '2026-04-01T06:21:33.175552+00:00', NULL),
      ('4c20508e-feeb-40ff-b57d-a6e249e880a3', 'azure_storage', 'Azure Storage', 'backend.10_sandbox.18_drivers.azure_storage.AzureStorageDriver', 'service_principal', TRUE, TRUE, TRUE, 'turbot/azure', 1200, '{"fields": [{"key": "subscription_id", "type": "text", "label": "Subscription ID", "order": 1, "required": true, "credential": false, "validation": "^[0-9a-f-]{36}$", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "tenant_id", "type": "text", "label": "Tenant ID", "order": 2, "required": true, "credential": false, "validation": "^[0-9a-f-]{36}$", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_id", "type": "text", "label": "Client ID", "order": 3, "required": true, "credential": false, "validation": "^[0-9a-f-]{36}$", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_secret", "type": "password", "label": "Client Secret", "order": 4, "required": true, "credential": true}, {"key": "resource_group", "hint": "Leave empty to collect all storage accounts in the subscription", "type": "text", "label": "Resource Group (optional)", "order": 5, "required": false, "credential": false}]}'::jsonb, TRUE, FALSE, '2026-03-16T11:40:50.992924+00:00', '2026-03-16T11:40:50.992924+00:00', '2023-01-01'),
      ('4d32e1a1-6435-4196-a1bc-8274b3f237ab', 'azure_monitor', 'Azure Monitor', 'backend.10_sandbox.18_drivers.azure_monitor.AzureMonitorDriver', 'oauth2', TRUE, TRUE, TRUE, 'turbot/azure', 60, '{"fields": [{"key": "tenant_id", "type": "text", "label": "Tenant ID", "order": 1, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "subscription_id", "type": "text", "label": "Subscription ID", "order": 2, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_id", "hint": "Requires: Monitoring Reader role on the subscription", "type": "text", "label": "Application (Client) ID", "order": 3, "required": true, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_secret", "type": "password", "label": "Client Secret", "order": 4, "required": true, "credential": true}, {"key": "workspace_id", "hint": "Only required for Log Analytics / KQL query collection", "type": "text", "label": "Log Analytics Workspace ID (optional)", "order": 5, "required": false, "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.641263+00:00', '2026-03-16T12:28:01.641263+00:00', NULL),
      ('5d03802f-0374-4740-a533-30a10db48c55', 'aws_iam', 'AWS IAM', 'backend.10_sandbox.18_drivers.aws_iam.AwsIamDriver', 'iam_role', FALSE, TRUE, TRUE, 'turbot/aws', 120, '{"fields": [{"key": "account_id", "hint": "12-digit AWS account number", "type": "text", "label": "AWS Account ID", "order": 1, "required": true, "credential": false, "validation": "^[0-9]{12}$", "placeholder": "123456789012"}, {"key": "region", "hint": "Primary AWS region for API calls", "type": "select", "label": "Default Region", "order": 2, "options": ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ca-central-1", "sa-east-1"], "required": true, "credential": false, "placeholder": "us-east-1"}, {"key": "access_key_id", "hint": "Use an IAM role (preferred) or provide access key. Required if not using instance role.", "type": "text", "label": "Access Key ID", "order": 3, "required": false, "credential": true, "placeholder": "AKIAIOSFODNN7EXAMPLE"}, {"key": "secret_access_key", "hint": "Secret for the access key above. Not required when using IAM instance roles.", "type": "password", "label": "Secret Access Key", "order": 4, "required": false, "credential": true, "placeholder": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"}, {"key": "role_arn", "hint": "If set, the connector will assume this role. Recommended for cross-account access.", "type": "text", "label": "IAM Role ARN (assume role)", "order": 5, "required": false, "credential": false, "placeholder": "arn:aws:iam::123456789012:role/KControlReadOnly"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.348174+00:00', '2026-03-16T12:28:01.348174+00:00', NULL),
      ('5f6a7274-5427-447c-93aa-5c99834f5b4e', 'azure_ad', 'Azure Active Directory', 'backend.10_sandbox.18_drivers.azure_ad.AzureAdDriver', 'oauth2', FALSE, TRUE, TRUE, 'turbot/azuread', 120, '{"fields": [{"key": "tenant_id", "hint": "Found in Azure Portal → Azure Active Directory → Overview → Tenant ID", "type": "text", "label": "Tenant ID", "order": 1, "required": true, "credential": false, "validation": "^[0-9a-f-]{36}$", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_id", "hint": "Application (client) ID of the registered app in Azure AD", "type": "text", "label": "Client ID", "order": 2, "required": true, "credential": false, "validation": "^[0-9a-f-]{36}$", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}, {"key": "client_secret", "hint": "Client secret from Azure AD app registration. Requires Directory.Read.All permission.", "type": "password", "label": "Client Secret", "order": 3, "required": true, "credential": true, "placeholder": "your-client-secret-value"}]}'::jsonb, TRUE, FALSE, '2026-03-16T12:28:01.398528+00:00', '2026-03-16T12:28:01.398528+00:00', NULL),
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
-- Extracted: 2026-04-02T12:27:07.382829
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
-- Extracted: 2026-04-02T12:27:11.585667
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
-- Extracted: 2026-04-02T12:27:15.114599
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

-- 08_tasks.04_dim_task_statuses (13 rows)
DO $$ BEGIN
  INSERT INTO "08_tasks"."04_dim_task_statuses" (id, code, name, description, is_terminal, sort_order, is_active, created_at, updated_at)
  VALUES
      ('19c60583-b343-403e-a06f-05584a67fee8', 'internally_approved', 'Internally Approved', 'Approved by GRC Lead, ready for Auditor', FALSE, 12, TRUE, '2026-03-30T06:51:19.303941', '2026-03-30T06:51:19.303941'),
      ('251227ad-ce25-4c62-b5c1-d21046b1d433', 'ready_for_auditor', 'Ready for Auditor', 'Published to active engagement', FALSE, 13, TRUE, '2026-03-30T06:51:19.303941', '2026-03-30T06:51:19.303941'),
      ('3eae348b-1d97-45b7-aceb-924a9798629b', 'auditor_reviewing', 'Auditor Reviewing', 'Under review by external auditor', FALSE, 14, TRUE, '2026-03-30T06:51:19.303941', '2026-03-30T06:51:19.303941'),
      ('9d5a0b3c-eb64-4cd3-94c7-e044d75e6277', 'internal_review', 'Under Internal Review', 'Under review by Control Owner', FALSE, 11, TRUE, '2026-03-30T06:51:19.303941', '2026-03-30T06:51:19.303941'),
      ('b05b2611-99a8-4fc0-a4ef-c4bb61599468', 'submitted', 'Submitted', 'Work done, awaiting internal review', FALSE, 10, TRUE, '2026-03-30T06:51:19.303941', '2026-03-30T06:51:19.303941'),
      ('b3c30001-0000-0000-0000-000000000000', 'open', 'Open', 'Task created, not yet started', FALSE, 1, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30002-0000-0000-0000-000000000000', 'in_progress', 'In Progress', 'Actively being worked on', FALSE, 2, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30003-0000-0000-0000-000000000000', 'pending_verification', 'Pending Verification', 'Work done, awaiting review/verification', FALSE, 3, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30004-0000-0000-0000-000000000000', 'resolved', 'Resolved', 'Task completed and verified', TRUE, 4, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30005-0000-0000-0000-000000000000', 'cancelled', 'Cancelled', 'Task cancelled — no longer needed', TRUE, 5, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30006-0000-0000-0000-000000000000', 'overdue', 'Overdue', 'Past due date — system-managed', FALSE, 6, TRUE, '2026-03-15T18:17:06.002267', '2026-03-15T18:17:06.002267'),
      ('b3c30007-0000-0000-0000-000000000000', 'in_review', 'Under Review', 'Evidence submitted and under internal review by control owner or GRC Lead. Not yet visible to external auditors.', FALSE, 7, TRUE, '2026-03-30T10:56:47.359266', '2026-03-30T10:56:47.359266'),
      ('b3c30008-0000-0000-0000-000000000000', 'published', 'Ready for Auditor', 'Evidence approved by GRC Lead. Visible to external auditors in the engagement. Internal label: Published.', FALSE, 8, TRUE, '2026-03-30T10:56:47.359266', '2026-03-30T10:56:47.359266')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, is_terminal = EXCLUDED.is_terminal, sort_order = EXCLUDED.sort_order, is_active = EXCLUDED.is_active, updated_at = EXCLUDED.updated_at;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═════════════════════════════════════════════════════════════════════════════
-- SEED: ISSUES
-- Extracted: 2026-04-02T12:27:17.203068
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
-- Extracted: 2026-04-02T12:27:18.595060
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
-- Extracted: 2026-04-02T12:27:20.670925
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
-- Extracted: 2026-04-02T12:27:21.353658
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

-- 12_engagements.03_dim_engagement_property_keys (8 rows)
DO $$ BEGIN
  INSERT INTO "12_engagements"."03_dim_engagement_property_keys" (id, code, name, description, data_type, is_required, sort_order, created_at)
  VALUES
      ('020821f9-1ee3-4fcb-bb21-b1a7c93942d4', 'audit_period_start', 'Audit Period Start', NULL, 'date', FALSE, 40, '2026-03-26T20:31:11.230754+00:00'),
      ('06122236-eee2-4a53-8512-4cad91096bc8', 'report_type', 'Report Type', NULL, 'text', FALSE, 60, '2026-03-26T20:31:11.230754+00:00'),
      ('2df71727-35e2-4cbd-9f86-3b936abc0033', 'audit_period_end', 'Audit Period End', NULL, 'date', FALSE, 50, '2026-03-26T20:31:11.230754+00:00'),
      ('4c406912-c578-4849-aeb9-968f4da723ca', 'auditor_firm', 'Auditor Firm', NULL, 'text', TRUE, 20, '2026-03-26T20:31:11.230754+00:00'),
      ('7dccc6ba-293e-417d-b3a8-fd8357a01368', 'engagement_type', 'Engagement Type', 'readiness or audit', 'text', FALSE, 100, '2026-03-31T19:59:56.913135+00:00'),
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
-- Extracted: 2026-04-02T12:27:23.409588
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
-- Extracted: 2026-04-02T12:27:25.473334
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

-- 09_assessments.05_dim_finding_statuses (9 rows)
DO $$ BEGIN
  INSERT INTO "09_assessments"."05_dim_finding_statuses" (id, code, name, description, icon, sort_order, is_active, created_at, updated_at)
  VALUES
      ('068a21f2-29c8-4f59-943d-0c066784e077', 'escalated', 'Escalated', 'Finding escalated for further review. May re-enter auditor_review after escalation action.', NULL, 9, TRUE, '2026-03-30T10:56:47.454337+00:00', '2026-03-30T10:56:47.454337+00:00'),
      ('0f03913c-870b-40a8-8ad5-f51bcc31627d', 'verified_closed', 'Verified Closed', 'Remediation verified and finding resolved', NULL, 3, TRUE, '2026-03-18T03:10:26.893085+00:00', '2026-03-18T03:10:26.893085+00:00'),
      ('4fc68793-081d-4866-b476-7f6c8e07ab39', 'accepted', 'Accepted', 'Acknowledged as a known/accepted risk', NULL, 4, TRUE, '2026-03-18T03:10:26.893085+00:00', '2026-03-18T03:10:26.893085+00:00'),
      ('563fe830-2660-459a-9d5f-d96bb5c5cf01', 'auditor_review', 'Auditor Review', 'Auditor is reviewing the org response before closing or escalating the finding.', NULL, 8, TRUE, '2026-03-30T10:56:47.454337+00:00', '2026-03-30T10:56:47.454337+00:00'),
      ('63d526db-9610-469c-b07c-ea07c5c8c473', 'acknowledged', 'Acknowledged', 'Org has acknowledged the finding. Formal review has begun but remediation has not started.', NULL, 6, TRUE, '2026-03-30T10:56:47.454337+00:00', '2026-03-30T10:56:47.454337+00:00'),
      ('b0e9bb4e-9ee0-42de-b98f-41d12917342b', 'responded', 'Responded', 'Org has submitted a remediation response or formal dispute for auditor review.', NULL, 7, TRUE, '2026-03-30T10:56:47.454337+00:00', '2026-03-30T10:56:47.454337+00:00'),
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
-- Extracted: 2026-04-02T12:27:29.679616
-- ═════════════════════════════════════════════════════════════════════════════

-- 17_steampipe.02_dim_plugin_types (4 rows)
DO $$ BEGIN
  INSERT INTO "17_steampipe"."02_dim_plugin_types" (code, name, plugin_image, provider_code, version, is_active, created_at)
  VALUES
      ('turbot/azure', 'Steampipe Azure Plugin', 'ghcr.io/turbot/steampipe-plugin-azure', 'azure_storage', 'latest', TRUE, '2026-03-16T11:39:09.783777+00:00'),
      ('turbot/azuread', 'Steampipe Azure AD Plugin', 'ghcr.io/turbot/steampipe-plugin-azuread', 'azure_ad', 'latest', TRUE, '2026-04-01T06:21:33.175552+00:00'),
      ('turbot/github', 'Steampipe GitHub Plugin', 'ghcr.io/turbot/steampipe-plugin-github', 'github', 'latest', TRUE, '2026-03-16T11:39:09.783777+00:00'),
      ('turbot/googledirectory', 'Steampipe Google Directory Plugin', 'ghcr.io/turbot/steampipe-plugin-googledirectory', 'google_workspace', 'latest', TRUE, '2026-04-01T06:21:33.175552+00:00')
  ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, plugin_image = EXCLUDED.plugin_image, provider_code = EXCLUDED.provider_code, version = EXCLUDED.version, is_active = EXCLUDED.is_active;
EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;
END $$;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF SEED DATA
-- ═══════════════════════════════════════════════════════════════════════════
