-- UP ====

-- iam.applications sub-feature: fct_applications.
-- Depends on: iam.orgs (fct_orgs).

CREATE TABLE "03_iam"."15_fct_applications" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    is_test         BOOLEAN NOT NULL DEFAULT false,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_applications PRIMARY KEY (id),
    CONSTRAINT fk_iam_fct_applications_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id)
);
CREATE INDEX idx_iam_fct_applications_org ON "03_iam"."15_fct_applications" (org_id);
COMMENT ON TABLE  "03_iam"."15_fct_applications" IS 'Applications — external products/services using the API with scoped credentials. Always org-scoped.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".org_id IS 'Parent org UUID.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".is_active IS 'Soft-disable flag.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."15_fct_applications".updated_at IS 'Last-update timestamp.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."15_fct_applications";
