-- UP ====

-- SCIM 2.0 per-org bearer tokens
CREATE TABLE IF NOT EXISTS "03_iam"."32_fct_scim_tokens" (
    id           VARCHAR(36)  NOT NULL,
    org_id       VARCHAR(36)  NOT NULL,
    label        TEXT         NOT NULL DEFAULT '',
    token_hash   VARCHAR(64)  NOT NULL,
    last_used_at TIMESTAMP,
    revoked_at   TIMESTAMP,
    created_by   VARCHAR(36)  NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_scim_tokens PRIMARY KEY (id),
    CONSTRAINT fk_scim_tokens_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs" (id) ON DELETE CASCADE,
    CONSTRAINT uq_scim_token_hash UNIQUE (token_hash)
);

COMMENT ON TABLE "03_iam"."32_fct_scim_tokens" IS 'Per-org SCIM 2.0 bearer tokens (stored as SHA256 hex hash)';
COMMENT ON COLUMN "03_iam"."32_fct_scim_tokens".token_hash IS 'SHA256 hex of the raw bearer token — never store raw token';
COMMENT ON COLUMN "03_iam"."32_fct_scim_tokens".revoked_at IS 'Set when token is revoked; NULL = active';

CREATE INDEX IF NOT EXISTS idx_scim_tokens_org ON "03_iam"."32_fct_scim_tokens" (org_id)
    WHERE revoked_at IS NULL;

-- SCIM external ID attr def (entity_type_id=3 = users)
INSERT INTO "03_iam"."20_dtl_attr_defs"
    (id, entity_type_id, code, label, value_type, description, deprecated_at)
OVERRIDING SYSTEM VALUE
VALUES
    (50, 3, 'scim_external_id', 'SCIM External ID', 'text', 'externalId from SCIM provisioner (Okta, Azure AD)', NULL)
ON CONFLICT DO NOTHING;

-- DOWN ====

DELETE FROM "03_iam"."20_dtl_attr_defs" WHERE id = 50;
DROP TABLE IF EXISTS "03_iam"."32_fct_scim_tokens";
