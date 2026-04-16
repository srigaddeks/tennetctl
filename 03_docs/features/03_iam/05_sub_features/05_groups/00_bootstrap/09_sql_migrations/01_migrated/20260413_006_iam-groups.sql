-- UP ====

-- iam.groups sub-feature: fct_groups + lnk_user_groups.
-- Depends on: iam.users (fct_users) + iam.orgs (fct_orgs).

CREATE TABLE "03_iam"."14_fct_groups" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    is_test         BOOLEAN NOT NULL DEFAULT false,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_groups PRIMARY KEY (id),
    CONSTRAINT fk_iam_fct_groups_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id)
);
CREATE INDEX idx_iam_fct_groups_org ON "03_iam"."14_fct_groups" (org_id);
COMMENT ON TABLE  "03_iam"."14_fct_groups" IS 'Groups — user collections for bulk role assignment. Always org-scoped.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".org_id IS 'Parent org UUID.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".is_active IS 'Soft-disable flag.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."14_fct_groups".updated_at IS 'Last-update timestamp.';

CREATE TABLE "03_iam"."43_lnk_user_groups" (
    id              VARCHAR(36) NOT NULL,
    user_id         VARCHAR(36) NOT NULL,
    group_id        VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_lnk_user_groups PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_user_groups_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_iam_lnk_user_groups_group FOREIGN KEY (group_id)
        REFERENCES "03_iam"."14_fct_groups"(id),
    CONSTRAINT fk_iam_lnk_user_groups_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT uq_iam_lnk_user_group UNIQUE (user_id, group_id, org_id)
);
CREATE INDEX idx_iam_lnk_user_groups_user ON "03_iam"."43_lnk_user_groups" (user_id);
CREATE INDEX idx_iam_lnk_user_groups_group ON "03_iam"."43_lnk_user_groups" (group_id);
COMMENT ON TABLE  "03_iam"."43_lnk_user_groups" IS 'User-group membership.';
COMMENT ON COLUMN "03_iam"."43_lnk_user_groups".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."43_lnk_user_groups".user_id IS 'FK to fct_users.';
COMMENT ON COLUMN "03_iam"."43_lnk_user_groups".group_id IS 'FK to fct_groups.';
COMMENT ON COLUMN "03_iam"."43_lnk_user_groups".org_id IS 'FK to fct_orgs (tenant discriminator).';
COMMENT ON COLUMN "03_iam"."43_lnk_user_groups".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."43_lnk_user_groups".created_at IS 'Insert timestamp.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."43_lnk_user_groups";
DROP TABLE IF EXISTS "03_iam"."14_fct_groups";
