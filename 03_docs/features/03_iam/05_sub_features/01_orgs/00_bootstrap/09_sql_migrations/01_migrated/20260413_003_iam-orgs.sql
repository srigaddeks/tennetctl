-- UP ====

-- iam.orgs sub-feature: fct_orgs + lnk_user_orgs.
-- Depends on: iam bootstrap + iam.users (for lnk_user_orgs.user_id FK).

CREATE TABLE "03_iam"."10_fct_orgs" (
    id              VARCHAR(36) NOT NULL,
    slug            TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    is_test         BOOLEAN NOT NULL DEFAULT false,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_orgs PRIMARY KEY (id)
);
CREATE UNIQUE INDEX uq_iam_fct_orgs_slug_active
    ON "03_iam"."10_fct_orgs" (slug)
    WHERE deleted_at IS NULL;
COMMENT ON TABLE  "03_iam"."10_fct_orgs" IS 'Organisations — top-level tenant boundary.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".slug IS 'URL-safe identifier. Unique among non-deleted rows.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".is_active IS 'Soft-disable flag.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."10_fct_orgs".updated_at IS 'Last-update timestamp.';

CREATE TABLE "03_iam"."40_lnk_user_orgs" (
    id              VARCHAR(36) NOT NULL,
    user_id         VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_lnk_user_orgs PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_user_orgs_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_iam_lnk_user_orgs_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT uq_iam_lnk_user_org UNIQUE (user_id, org_id)
);
CREATE INDEX idx_iam_lnk_user_orgs_user ON "03_iam"."40_lnk_user_orgs" (user_id);
CREATE INDEX idx_iam_lnk_user_orgs_org ON "03_iam"."40_lnk_user_orgs" (org_id);
COMMENT ON TABLE  "03_iam"."40_lnk_user_orgs" IS 'User-org membership. Immutable row (revoke via delete + new row).';
COMMENT ON COLUMN "03_iam"."40_lnk_user_orgs".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."40_lnk_user_orgs".user_id IS 'FK to fct_users.';
COMMENT ON COLUMN "03_iam"."40_lnk_user_orgs".org_id IS 'FK to fct_orgs. Tenant discriminator.';
COMMENT ON COLUMN "03_iam"."40_lnk_user_orgs".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."40_lnk_user_orgs".created_at IS 'Insert timestamp.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."40_lnk_user_orgs";
DROP TABLE IF EXISTS "03_iam"."10_fct_orgs";
