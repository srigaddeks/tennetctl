-- UP ====

-- iam.roles sub-feature: fct_roles + lnk_user_roles + lnk_role_scopes.
-- Depends on: iam.users (fct_users) + iam.orgs (fct_orgs) + iam bootstrap (dim_role_types, dim_scopes).

CREATE TABLE "03_iam"."13_fct_roles" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36),
    role_type_id    SMALLINT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    is_test         BOOLEAN NOT NULL DEFAULT false,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_roles PRIMARY KEY (id),
    CONSTRAINT fk_iam_fct_roles_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_iam_fct_roles_role_type FOREIGN KEY (role_type_id)
        REFERENCES "03_iam"."04_dim_role_types"(id)
);
CREATE INDEX idx_iam_fct_roles_org ON "03_iam"."13_fct_roles" (org_id);
COMMENT ON TABLE  "03_iam"."13_fct_roles" IS 'Roles. org_id NULL = global system role; non-null = org-scoped.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".org_id IS 'Parent org UUID. NULL = global system role.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".role_type_id IS 'FK to dim_role_types (system | custom).';
COMMENT ON COLUMN "03_iam"."13_fct_roles".is_active IS 'Soft-disable flag.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."13_fct_roles".updated_at IS 'Last-update timestamp.';

CREATE TABLE "03_iam"."42_lnk_user_roles" (
    id              VARCHAR(36) NOT NULL,
    user_id         VARCHAR(36) NOT NULL,
    role_id         VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_lnk_user_roles PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_user_roles_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_iam_lnk_user_roles_role FOREIGN KEY (role_id)
        REFERENCES "03_iam"."13_fct_roles"(id),
    CONSTRAINT fk_iam_lnk_user_roles_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT uq_iam_lnk_user_role UNIQUE (user_id, role_id, org_id)
);
CREATE INDEX idx_iam_lnk_user_roles_user ON "03_iam"."42_lnk_user_roles" (user_id);
CREATE INDEX idx_iam_lnk_user_roles_role ON "03_iam"."42_lnk_user_roles" (role_id);
COMMENT ON TABLE  "03_iam"."42_lnk_user_roles" IS 'User-role assignment (scoped to org).';
COMMENT ON COLUMN "03_iam"."42_lnk_user_roles".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."42_lnk_user_roles".user_id IS 'FK to fct_users.';
COMMENT ON COLUMN "03_iam"."42_lnk_user_roles".role_id IS 'FK to fct_roles.';
COMMENT ON COLUMN "03_iam"."42_lnk_user_roles".org_id IS 'FK to fct_orgs — org in which this role is active.';
COMMENT ON COLUMN "03_iam"."42_lnk_user_roles".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."42_lnk_user_roles".created_at IS 'Insert timestamp.';

CREATE TABLE "03_iam"."44_lnk_role_scopes" (
    id              VARCHAR(36) NOT NULL,
    role_id         VARCHAR(36) NOT NULL,
    scope_id        SMALLINT NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_lnk_role_scopes PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_role_scopes_role FOREIGN KEY (role_id)
        REFERENCES "03_iam"."13_fct_roles"(id),
    CONSTRAINT fk_iam_lnk_role_scopes_scope FOREIGN KEY (scope_id)
        REFERENCES "03_iam"."03_dim_scopes"(id),
    CONSTRAINT uq_iam_lnk_role_scope UNIQUE (role_id, scope_id)
);
CREATE INDEX idx_iam_lnk_role_scopes_role ON "03_iam"."44_lnk_role_scopes" (role_id);
COMMENT ON TABLE  "03_iam"."44_lnk_role_scopes" IS 'Role-scope assignment. Scope grant is a property of the role itself (no org_id).';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".role_id IS 'FK to fct_roles.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".scope_id IS 'FK to dim_scopes.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".created_at IS 'Insert timestamp.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."44_lnk_role_scopes";
DROP TABLE IF EXISTS "03_iam"."42_lnk_user_roles";
DROP TABLE IF EXISTS "03_iam"."13_fct_roles";
