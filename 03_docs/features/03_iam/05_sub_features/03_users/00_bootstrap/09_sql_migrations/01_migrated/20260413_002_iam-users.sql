-- UP ====

-- iam.users sub-feature: fct_users table.
-- Depends on: iam bootstrap (dim_account_types FK). No lnk tables here — those belong to sub-features that hold the foreign entity (orgs owns lnk_user_orgs, roles owns lnk_user_roles, etc.)

CREATE TABLE "03_iam"."12_fct_users" (
    id              VARCHAR(36) NOT NULL,
    account_type_id SMALLINT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    is_test         BOOLEAN NOT NULL DEFAULT false,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_users PRIMARY KEY (id),
    CONSTRAINT fk_iam_fct_users_account_type FOREIGN KEY (account_type_id)
        REFERENCES "03_iam"."02_dim_account_types"(id)
);
CREATE INDEX idx_iam_fct_users_account_type ON "03_iam"."12_fct_users" (account_type_id);
COMMENT ON TABLE  "03_iam"."12_fct_users" IS 'Users — human and service identities. Email / display_name / avatar live in dtl_attrs.';
COMMENT ON COLUMN "03_iam"."12_fct_users".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."12_fct_users".account_type_id IS 'FK to dim_account_types — drives available auth flows.';
COMMENT ON COLUMN "03_iam"."12_fct_users".is_active IS 'Soft-disable flag.';
COMMENT ON COLUMN "03_iam"."12_fct_users".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "03_iam"."12_fct_users".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "03_iam"."12_fct_users".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."12_fct_users".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "03_iam"."12_fct_users".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."12_fct_users".updated_at IS 'Last-update timestamp (set by app).';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."12_fct_users";
