-- ─────────────────────────────────────────────────────────────────────────
-- INVITATION SYSTEM  (43, 44)
-- Enterprise-grade user invitation with scope-based auto-enrollment.
-- ─────────────────────────────────────────────────────────────────────────

-- ── Dimension: Invite Statuses ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."43_dim_invite_statuses" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_43_dim_invite_statuses      PRIMARY KEY (id),
    CONSTRAINT uq_43_dim_invite_statuses_code UNIQUE (code)
);

-- ── Transaction: Invitations ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."44_trx_invitations" (
    id                UUID          NOT NULL,
    tenant_key        VARCHAR(100)  NOT NULL,
    invite_token_hash VARCHAR(128)  NOT NULL,
    email             VARCHAR(255)  NOT NULL,
    scope             VARCHAR(20)   NOT NULL,
    org_id            UUID          NULL,
    workspace_id      UUID          NULL,
    role              VARCHAR(50)   NULL,
    status_id         UUID          NOT NULL,
    invited_by        UUID          NOT NULL,
    expires_at        TIMESTAMP     NOT NULL,
    accepted_at       TIMESTAMP     NULL,
    accepted_by       UUID          NULL,
    revoked_at        TIMESTAMP     NULL,
    revoked_by        UUID          NULL,
    created_at        TIMESTAMP     NOT NULL,
    updated_at        TIMESTAMP     NOT NULL,
    CONSTRAINT pk_44_trx_invitations PRIMARY KEY (id),
    CONSTRAINT uq_44_trx_invitations_token_hash UNIQUE (invite_token_hash),
    CONSTRAINT fk_44_trx_invitations_status_id_43_dim_invite_statuses
        FOREIGN KEY (status_id)
        REFERENCES "03_auth_manage"."43_dim_invite_statuses" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_44_trx_invitations_invited_by_03_fct_users
        FOREIGN KEY (invited_by)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_44_trx_invitations_accepted_by_03_fct_users
        FOREIGN KEY (accepted_by)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_44_trx_invitations_revoked_by_03_fct_users
        FOREIGN KEY (revoked_by)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT ck_44_trx_invitations_scope
        CHECK (scope IN ('platform', 'organization', 'workspace')),
    CONSTRAINT ck_44_trx_invitations_platform_scope
        CHECK (scope <> 'platform' OR (org_id IS NULL AND workspace_id IS NULL)),
    CONSTRAINT ck_44_trx_invitations_org_scope
        CHECK (scope <> 'organization' OR (org_id IS NOT NULL AND workspace_id IS NULL)),
    CONSTRAINT ck_44_trx_invitations_workspace_scope
        CHECK (scope <> 'workspace' OR (org_id IS NOT NULL AND workspace_id IS NOT NULL))
);

-- ─────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_44_trx_invitations_tenant_email_status
    ON "03_auth_manage"."44_trx_invitations" (tenant_key, email, status_id);

CREATE INDEX IF NOT EXISTS idx_44_trx_invitations_tenant_status_created
    ON "03_auth_manage"."44_trx_invitations" (tenant_key, status_id, created_at);

CREATE INDEX IF NOT EXISTS idx_44_trx_invitations_expires_at
    ON "03_auth_manage"."44_trx_invitations" (expires_at)
    WHERE accepted_at IS NULL AND revoked_at IS NULL;

-- ─────────────────────────────────────────────────────────────────────────
-- SEED DATA: Invite Statuses
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."43_dim_invite_statuses" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001001', 'pending', 'Pending', 'Invitation sent and awaiting response.', 10, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."43_dim_invite_statuses" WHERE code = 'pending');

INSERT INTO "03_auth_manage"."43_dim_invite_statuses" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001002', 'accepted', 'Accepted', 'Invitation accepted by the invitee.', 20, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."43_dim_invite_statuses" WHERE code = 'accepted');

INSERT INTO "03_auth_manage"."43_dim_invite_statuses" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001003', 'revoked', 'Revoked', 'Invitation revoked by the inviter.', 30, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."43_dim_invite_statuses" WHERE code = 'revoked');

INSERT INTO "03_auth_manage"."43_dim_invite_statuses" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001004', 'expired', 'Expired', 'Invitation expired before acceptance.', 40, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."43_dim_invite_statuses" WHERE code = 'expired');

INSERT INTO "03_auth_manage"."43_dim_invite_statuses" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001005', 'declined', 'Declined', 'Invitation declined by the invitee.', 50, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."43_dim_invite_statuses" WHERE code = 'declined');

-- ─────────────────────────────────────────────────────────────────────────
-- SEED DATA: Feature Flag + Permissions for invitation_management
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000408', 'invitation_management', 'Invitation Management', 'User invitation creation and lifecycle management.', 'admin', 'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'invitation_management');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000513', 'invitation_management.view', 'invitation_management', 'view', 'View Invitations', 'View invitation list and statistics.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000514', 'invitation_management.create', 'invitation_management', 'create', 'Create Invitations', 'Create and send user invitations.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000515', 'invitation_management.update', 'invitation_management', 'update', 'Update Invitations', 'Update invitation details.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.update');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000516', 'invitation_management.revoke', 'invitation_management', 'revoke', 'Revoke Invitations', 'Revoke pending invitations.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.revoke');

-- Grant invitation permissions to platform_super_admin role
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-00000000090c', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000513',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000513');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-00000000090d', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000514',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000514');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-00000000090e', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000515',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000515');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-00000000090f', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000516',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000516');

-- ─────────────────────────────────────────────────────────────────────────
-- COMMENTS
-- ─────────────────────────────────────────────────────────────────────────

COMMENT ON TABLE "03_auth_manage"."43_dim_invite_statuses" IS 'Dimension table for invitation lifecycle statuses.';
COMMENT ON TABLE "03_auth_manage"."44_trx_invitations" IS 'Transaction table for user invitations with scope-based auto-enrollment.';
COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".id IS 'Application-assigned invitation identifier.';
COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".invite_token_hash IS 'SHA-256 hash of the invite token. Token is only returned on creation.';
COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".scope IS 'Invitation scope: platform, organization, or workspace.';
COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".role IS 'Role to assign when invitation is accepted (org or workspace role).';
COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".expires_at IS 'Configurable deadline after which the invitation cannot be accepted.';
