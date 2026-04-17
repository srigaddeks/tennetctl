-- UP ====

CREATE TABLE IF NOT EXISTS "03_iam"."30_fct_oidc_providers" (
    id                      VARCHAR(36)  NOT NULL,
    org_id                  VARCHAR(36)  NOT NULL REFERENCES "03_iam"."10_fct_orgs"(id) ON DELETE CASCADE,
    slug                    TEXT         NOT NULL,
    issuer                  TEXT         NOT NULL,
    client_id               TEXT         NOT NULL,
    client_secret_vault_key TEXT         NOT NULL,
    scopes                  TEXT         NOT NULL DEFAULT 'openid email profile',
    claim_mapping           JSONB        NOT NULL DEFAULT '{"email":"email","name":"name","sub":"sub"}',
    enabled                 BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at              TIMESTAMP,
    CONSTRAINT "pk_30_fct_oidc_providers" PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS "uq_30_fct_oidc_providers_org_slug"
    ON "03_iam"."30_fct_oidc_providers" (org_id, slug)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS "idx_30_fct_oidc_providers_org_id"
    ON "03_iam"."30_fct_oidc_providers" (org_id)
    WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW "03_iam"."v_oidc_providers" AS
SELECT
    p.id,
    p.org_id,
    p.slug,
    p.issuer,
    p.client_id,
    p.client_secret_vault_key,
    p.scopes,
    p.claim_mapping,
    p.enabled,
    p.created_at,
    p.updated_at,
    o.slug AS org_slug
FROM "03_iam"."30_fct_oidc_providers" p
JOIN "03_iam"."10_fct_orgs" o ON o.id = p.org_id
WHERE p.deleted_at IS NULL;

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_oidc_providers";
DROP TABLE IF EXISTS "03_iam"."30_fct_oidc_providers";
