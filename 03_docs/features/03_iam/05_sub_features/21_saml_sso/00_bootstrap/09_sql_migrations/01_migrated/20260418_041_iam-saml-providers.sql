-- UP ====

-- SAML 2.0 SP-initiated SSO: per-org IdP configuration
CREATE TABLE IF NOT EXISTS "03_iam"."31_fct_saml_providers" (
    id             VARCHAR(36)  NOT NULL,
    org_id         VARCHAR(36)  NOT NULL,
    idp_entity_id  TEXT         NOT NULL,
    sso_url        TEXT         NOT NULL,
    x509_cert      TEXT         NOT NULL,
    sp_entity_id   TEXT         NOT NULL,
    enabled        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at     TIMESTAMP,

    CONSTRAINT pk_saml_providers PRIMARY KEY (id),
    CONSTRAINT fk_saml_providers_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs" (id) ON DELETE CASCADE,
    CONSTRAINT uq_saml_providers_org_entity UNIQUE (org_id, idp_entity_id)
);

COMMENT ON TABLE "03_iam"."31_fct_saml_providers" IS 'Per-org SAML 2.0 IdP configurations for SP-initiated SSO';
COMMENT ON COLUMN "03_iam"."31_fct_saml_providers".idp_entity_id IS 'EntityID of the Identity Provider';
COMMENT ON COLUMN "03_iam"."31_fct_saml_providers".sso_url IS 'IdP SSO service URL (redirect or POST binding)';
COMMENT ON COLUMN "03_iam"."31_fct_saml_providers".x509_cert IS 'IdP public x509 certificate (PEM, stripped of headers)';
COMMENT ON COLUMN "03_iam"."31_fct_saml_providers".sp_entity_id IS 'EntityID of this SP (typically the ACS URL base)';

CREATE INDEX IF NOT EXISTS idx_saml_providers_org ON "03_iam"."31_fct_saml_providers" (org_id)
    WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW "03_iam"."v_saml_providers" AS
SELECT
    sp.id,
    sp.org_id,
    o.slug AS org_slug,
    sp.idp_entity_id,
    sp.sso_url,
    sp.x509_cert,
    sp.sp_entity_id,
    sp.enabled,
    sp.created_at,
    sp.updated_at,
    sp.deleted_at
FROM "03_iam"."31_fct_saml_providers" sp
JOIN "03_iam"."10_fct_orgs" o ON o.id = sp.org_id
WHERE sp.deleted_at IS NULL;

COMMENT ON VIEW "03_iam"."v_saml_providers" IS 'Active SAML providers with org slug resolved';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_saml_providers";
DROP TABLE IF EXISTS "03_iam"."31_fct_saml_providers";
