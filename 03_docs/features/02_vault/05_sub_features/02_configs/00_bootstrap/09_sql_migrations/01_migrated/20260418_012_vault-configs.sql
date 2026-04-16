-- UP ====

-- Vault sub-feature 02 — configs.
-- Plaintext, typed, scoped application configuration values. Stored alongside
-- envelope-encrypted secrets in 02_vault schema; share dim_scopes + EAV stack.
--
-- Ships:
-- 1. dim_value_types (boolean/string/number/json) — same pattern as featureflags.
-- 2. New entity_type 'config' + description attr_def in the shared EAV stack.
-- 3. fct_vault_configs table with (scope, org_id, workspace_id, key) uniqueness.
-- 4. v_vault_configs view joining scope, value_type, description.
--
-- Configs are NOT versioned (unlike secrets). UPDATE is in-place; audit captures
-- history. Values are stored as JSONB regardless of declared type; the type drives
-- UI rendering + validation, not the physical storage.

-- ── 1. dim_value_types ─────────────────────────────────────────────

CREATE TABLE "02_vault"."03_dim_value_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_vault_dim_value_types PRIMARY KEY (id),
    CONSTRAINT uq_vault_dim_value_types_code UNIQUE (code)
);
COMMENT ON TABLE  "02_vault"."03_dim_value_types" IS 'Config value types. UI uses this to render + validate inputs. Storage is always JSONB.';
COMMENT ON COLUMN "02_vault"."03_dim_value_types".id IS 'Permanent manual id.';
COMMENT ON COLUMN "02_vault"."03_dim_value_types".code IS 'Value type code (boolean, string, number, json).';
COMMENT ON COLUMN "02_vault"."03_dim_value_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "02_vault"."03_dim_value_types".description IS 'Free-text description.';
COMMENT ON COLUMN "02_vault"."03_dim_value_types".deprecated_at IS 'Non-null when deprecated.';

INSERT INTO "02_vault"."03_dim_value_types" (id, code, label, description) VALUES
    (1, 'boolean', 'Boolean', 'true / false'),
    (2, 'string',  'String',  'Free-text value'),
    (3, 'number',  'Number',  'Integer or float'),
    (4, 'json',    'JSON',    'Arbitrary JSON object or array')
ON CONFLICT (id) DO NOTHING;

-- ── 2. Extend EAV stack for 'config' entity ────────────────────────

INSERT INTO "02_vault"."01_dim_entity_types" (id, code, label, description) VALUES
    (2, 'config', 'Config', 'Plaintext configuration value (fct_vault_configs row)')
ON CONFLICT (id) DO NOTHING;

INSERT INTO "02_vault"."20_dtl_attr_defs" (entity_type_id, code, label, value_type, description)
VALUES (2, 'description', 'Description', 'text', 'Free-text description of the config''s purpose')
ON CONFLICT (entity_type_id, code) DO NOTHING;

-- ── 3. fct_vault_configs ───────────────────────────────────────────

CREATE TABLE "02_vault"."11_fct_vault_configs" (
    id            VARCHAR(36) NOT NULL,
    key           TEXT NOT NULL,
    value_type_id SMALLINT NOT NULL,
    value_jsonb   JSONB NOT NULL,
    scope_id      SMALLINT NOT NULL DEFAULT 1,
    org_id        VARCHAR(36),
    workspace_id  VARCHAR(36),
    is_active     BOOLEAN NOT NULL DEFAULT true,
    is_test       BOOLEAN NOT NULL DEFAULT false,
    deleted_at    TIMESTAMP,
    created_by    VARCHAR(36) NOT NULL,
    updated_by    VARCHAR(36) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_vault_configs PRIMARY KEY (id),
    CONSTRAINT fk_fct_vault_configs_value_type
        FOREIGN KEY (value_type_id) REFERENCES "02_vault"."03_dim_value_types"(id),
    CONSTRAINT fk_fct_vault_configs_scope
        FOREIGN KEY (scope_id) REFERENCES "02_vault"."02_dim_scopes"(id),
    CONSTRAINT chk_fct_vault_configs_scope_shape CHECK (
        (scope_id = 1 AND org_id IS NULL     AND workspace_id IS NULL)
     OR (scope_id = 2 AND org_id IS NOT NULL AND workspace_id IS NULL)
     OR (scope_id = 3 AND org_id IS NOT NULL AND workspace_id IS NOT NULL)
    ),
    CONSTRAINT chk_fct_vault_configs_key_shape
        CHECK (key ~ '^[a-z][a-z0-9._-]{0,127}$')
);

COMMENT ON TABLE  "02_vault"."11_fct_vault_configs" IS 'Plaintext config values. Value stored as JSONB; value_type_id drives UI rendering + validation. Not versioned.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".id IS 'UUID v7.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".key IS 'User-supplied stable identifier (lowercase dotted).';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".value_type_id IS 'FK dim_value_types; boolean/string/number/json.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".value_jsonb IS 'The actual config value — stored as JSONB regardless of declared type.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".scope_id IS 'FK dim_scopes; 1=global, 2=org, 3=workspace.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".org_id IS 'Required for scope=org/workspace.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".workspace_id IS 'Required for scope=workspace.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".is_active IS 'Whether this config is active. Set false to disable without deleting.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".is_test IS 'Test-mode marker.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".created_by IS 'User id that created this row.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".updated_by IS 'User id that last updated this row.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "02_vault"."11_fct_vault_configs".updated_at IS 'Last update timestamp (app-set).';

-- Unique live (scope, key) — partial index excludes soft-deleted so a key can be
-- reused after a true delete, unlike secrets.
CREATE UNIQUE INDEX uq_fct_vault_configs_scope_key_live
    ON "02_vault"."11_fct_vault_configs" (
        scope_id,
        COALESCE(org_id,       '00000000-0000-0000-0000-000000000000'),
        COALESCE(workspace_id, '00000000-0000-0000-0000-000000000000'),
        key
    )
    WHERE deleted_at IS NULL;

-- ── 4. v_vault_configs view ────────────────────────────────────────

CREATE VIEW "02_vault"."v_vault_configs" AS
SELECT
    c.id,
    c.key,
    c.value_type_id,
    vt.code AS value_type,
    c.value_jsonb,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description,
    c.scope_id,
    ds.code AS scope,
    c.org_id,
    c.workspace_id,
    c.is_active,
    c.is_test,
    c.deleted_at,
    c.created_by,
    c.updated_by,
    c.created_at,
    c.updated_at
FROM "02_vault"."11_fct_vault_configs" c
JOIN "02_vault"."02_dim_scopes" ds        ON ds.id = c.scope_id
JOIN "02_vault"."03_dim_value_types" vt   ON vt.id = c.value_type_id
LEFT JOIN "02_vault"."21_dtl_attrs" da
    ON da.entity_type_id = 2 AND da.entity_id = c.id
LEFT JOIN "02_vault"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
WHERE c.deleted_at IS NULL
GROUP BY
    c.id, c.key, c.value_type_id, vt.code, c.value_jsonb,
    c.scope_id, ds.code, c.org_id, c.workspace_id,
    c.is_active, c.is_test, c.deleted_at,
    c.created_by, c.updated_by, c.created_at, c.updated_at;

COMMENT ON VIEW "02_vault"."v_vault_configs" IS 'Flat read shape for configs — scope code, value_type code, description pivoted from dtl_attrs.';

-- DOWN ====

DROP VIEW IF EXISTS "02_vault"."v_vault_configs";

-- Clean the dtl_attrs that belong to configs (entity_type_id=2) — they'd orphan
-- once the rows + attr_def vanish.
DELETE FROM "02_vault"."21_dtl_attrs" WHERE entity_type_id = 2;

DROP INDEX IF EXISTS "02_vault".uq_fct_vault_configs_scope_key_live;
DROP TABLE IF EXISTS "02_vault"."11_fct_vault_configs";

DELETE FROM "02_vault"."20_dtl_attr_defs" WHERE entity_type_id = 2;
DELETE FROM "02_vault"."01_dim_entity_types" WHERE id = 2;

DROP TABLE IF EXISTS "02_vault"."03_dim_value_types";
