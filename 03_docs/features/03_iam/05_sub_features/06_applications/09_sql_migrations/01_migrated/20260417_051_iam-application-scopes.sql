-- UP ====

-- iam.applications — lnk_application_scopes (M:N between applications and dim_scopes).
-- Enforces REPLACE semantics at the service layer (delete + insert in a single tx);
-- the UNIQUE (application_id, scope_id) constraint guards against double-grants.

CREATE TABLE "03_iam"."45_lnk_application_scopes" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    application_id  VARCHAR(36) NOT NULL,
    scope_id        SMALLINT    NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_lnk_application_scopes PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_application_scopes_app
        FOREIGN KEY (application_id)
        REFERENCES "03_iam"."15_fct_applications"(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_iam_lnk_application_scopes_scope
        FOREIGN KEY (scope_id)
        REFERENCES "03_iam"."03_dim_scopes"(id),
    CONSTRAINT fk_iam_lnk_application_scopes_org
        FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT uq_iam_lnk_application_scope UNIQUE (application_id, scope_id)
);

CREATE INDEX idx_iam_lnk_application_scopes_app
    ON "03_iam"."45_lnk_application_scopes" (application_id);

COMMENT ON TABLE  "03_iam"."45_lnk_application_scopes" IS 'Application-scope assignment. REPLACE semantics via service layer (atomic delete + insert).';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".org_id IS 'FK to fct_orgs (tenant discriminator, mirrors parent application).';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".application_id IS 'FK to fct_applications.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".scope_id IS 'FK to dim_scopes.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".created_at IS 'Insert timestamp.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."45_lnk_application_scopes";
