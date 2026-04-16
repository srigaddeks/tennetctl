-- UP ====

-- iam.workspaces sub-feature: fct_workspaces + lnk_user_workspaces.
-- Depends on: iam.users (fct_users) + iam.orgs (fct_orgs).

CREATE TABLE "03_iam"."11_fct_workspaces" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    slug            TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    is_test         BOOLEAN NOT NULL DEFAULT false,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_workspaces PRIMARY KEY (id),
    CONSTRAINT fk_iam_fct_workspaces_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id)
);
CREATE UNIQUE INDEX uq_iam_fct_workspaces_slug_org_active
    ON "03_iam"."11_fct_workspaces" (org_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_iam_fct_workspaces_org ON "03_iam"."11_fct_workspaces" (org_id);
COMMENT ON TABLE  "03_iam"."11_fct_workspaces" IS 'Workspaces — scoped containers within an org.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".org_id IS 'Parent org UUID.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".slug IS 'URL-safe identifier. Unique within (org_id) among non-deleted rows.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".is_active IS 'Soft-disable flag.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."11_fct_workspaces".updated_at IS 'Last-update timestamp.';

CREATE TABLE "03_iam"."41_lnk_user_workspaces" (
    id              VARCHAR(36) NOT NULL,
    user_id         VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_lnk_user_workspaces PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_user_workspaces_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_iam_lnk_user_workspaces_workspace FOREIGN KEY (workspace_id)
        REFERENCES "03_iam"."11_fct_workspaces"(id),
    CONSTRAINT fk_iam_lnk_user_workspaces_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT uq_iam_lnk_user_workspace UNIQUE (user_id, workspace_id)
);
CREATE INDEX idx_iam_lnk_user_workspaces_user ON "03_iam"."41_lnk_user_workspaces" (user_id);
CREATE INDEX idx_iam_lnk_user_workspaces_workspace ON "03_iam"."41_lnk_user_workspaces" (workspace_id);
COMMENT ON TABLE  "03_iam"."41_lnk_user_workspaces" IS 'User-workspace membership (within an org).';
COMMENT ON COLUMN "03_iam"."41_lnk_user_workspaces".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."41_lnk_user_workspaces".user_id IS 'FK to fct_users.';
COMMENT ON COLUMN "03_iam"."41_lnk_user_workspaces".workspace_id IS 'FK to fct_workspaces.';
COMMENT ON COLUMN "03_iam"."41_lnk_user_workspaces".org_id IS 'FK to fct_orgs (tenant discriminator).';
COMMENT ON COLUMN "03_iam"."41_lnk_user_workspaces".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."41_lnk_user_workspaces".created_at IS 'Insert timestamp.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."41_lnk_user_workspaces";
DROP TABLE IF EXISTS "03_iam"."11_fct_workspaces";
