-- =============================================================================
-- Migration:   20260409_024_kbio_api_keys.sql
-- Module:      10_kbio
-- Sub-feature: 00_bootstrap
-- Sequence:    024
-- Depends on:  023 (10_kbio/00_bootstrap seed policies)
-- Description: Workspace API keys for SDK authentication. Replaces the
--              hardcoded X-Internal-Service-Token with per-workspace keys.
--              Adds dim_api_key_statuses, entity type, fct_api_keys, EAV
--              attr defs, and v_api_keys view.
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- 09_dim_api_key_statuses — Lifecycle states for API keys
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."09_dim_api_key_statuses" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_api_key_statuses       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_api_key_statuses_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."09_dim_api_key_statuses" IS
    'Lifecycle states for workspace API keys. active = key can authenticate; '
    'revoked = key permanently disabled by admin; expired = key past its TTL.';
COMMENT ON COLUMN "10_kbio"."09_dim_api_key_statuses".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."09_dim_api_key_statuses".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."09_dim_api_key_statuses".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."09_dim_api_key_statuses".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."09_dim_api_key_statuses".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."09_dim_api_key_statuses" (code, label, description) VALUES
    ('active',   'Active',   'API key is live and can authenticate ingest requests.'),
    ('revoked',  'Revoked',  'API key permanently disabled by an administrator.'),
    ('expired',  'Expired',  'API key has passed its configured expiry timestamp.');

GRANT SELECT ON "10_kbio"."09_dim_api_key_statuses" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."09_dim_api_key_statuses" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- Register entity type: kbio_api_key  (id=7, after kbio_predefined_policy=6)
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."06_dim_entity_types" (code, label, description) VALUES
    ('kbio_api_key', 'kBio API Key', 'A workspace-scoped API key used to authenticate SDK ingest requests.');

-- ---------------------------------------------------------------------------
-- 16_fct_api_keys — Workspace API key identity
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."16_fct_api_keys" (
    id              VARCHAR(36)   NOT NULL,
    org_id          VARCHAR(36)   NOT NULL,
    workspace_id    VARCHAR(36)   NOT NULL,
    key_prefix      VARCHAR(8)    NOT NULL,
    key_hash        VARCHAR(128)  NOT NULL,
    status_id       SMALLINT      NOT NULL DEFAULT 1,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    is_test         BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36)   NOT NULL,
    updated_by      VARCHAR(36)   NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kbio_fct_api_keys             PRIMARY KEY (id),
    CONSTRAINT uq_kbio_fct_api_keys_key_hash    UNIQUE (key_hash),
    CONSTRAINT fk_kbio_fct_api_keys_status      FOREIGN KEY (status_id)
                                                 REFERENCES "10_kbio"."09_dim_api_key_statuses" (id)
);

CREATE INDEX idx_kbio_fct_api_keys_org_ws   ON "10_kbio"."16_fct_api_keys" (org_id, workspace_id);
CREATE INDEX idx_kbio_fct_api_keys_key_hash ON "10_kbio"."16_fct_api_keys" (key_hash);

COMMENT ON TABLE  "10_kbio"."16_fct_api_keys" IS
    'Workspace-scoped API keys for SDK authentication. One row per key. '
    'org_id, workspace_id, key_prefix, and key_hash are scope/routing columns '
    'required for sub-millisecond auth validation on every ingest request — '
    'they are not business data stored outside EAV for convenience.';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".id              IS 'UUID v7 primary key.';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".org_id          IS 'Organisation that owns this key. Logical FK to 03_iam orgs (no cross-schema FK).';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".workspace_id    IS 'Workspace this key is scoped to. Logical FK to 03_iam workspaces.';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".key_prefix      IS 'First 8 characters of the raw key, for display (e.g. "kb_a3f2...").';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".key_hash        IS 'SHA-256 hex digest of the full raw API key. Only the hash is stored.';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".status_id       IS 'FK → 09_dim_api_key_statuses. Lifecycle state (active, revoked, expired).';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".is_active       IS 'FALSE when the key is disabled (complements status for quick filtering).';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".is_test         IS 'TRUE for test/sandbox keys. Excluded from production analytics.';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".deleted_at      IS 'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".created_by      IS 'UUID of the actor that created this key.';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".updated_by      IS 'UUID of the actor that last updated this key.';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".created_at      IS 'Row creation timestamp (UTC).';
COMMENT ON COLUMN "10_kbio"."16_fct_api_keys".updated_at      IS 'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "10_kbio"."16_fct_api_keys" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "10_kbio"."16_fct_api_keys" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- EAV attribute definitions for kbio_api_key (entity_type_id resolved by code)
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."07_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('kbio_api_key', 'name',         'Key Name',        'Human-readable label for this API key.',                  'key_text'),
    ('kbio_api_key', 'description',  'Key Description', 'Optional description of the key purpose.',                'key_text'),
    ('kbio_api_key', 'last_used_at', 'Last Used At',    'ISO-8601 timestamp of the last successful authentication.', 'key_text'),
    ('kbio_api_key', 'rate_limit',   'Rate Limit',      'Maximum requests per minute allowed for this key.',       'key_text'),
    ('kbio_api_key', 'permissions',  'Permissions',     'JSON array of permission scopes granted to this key.',    'key_jsonb'),
    ('kbio_api_key', 'expires_at',   'Expiry',          'ISO-8601 timestamp after which the key is no longer valid.', 'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "10_kbio"."06_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- v_api_keys — Read view with dim codes resolved and EAV pivoted
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "10_kbio".v_api_keys AS
SELECT
    k.id,
    k.org_id,
    k.workspace_id,
    k.key_prefix,
    k.key_hash,
    k.status_id,
    st.code                                                                        AS status,
    k.is_active,
    (k.deleted_at IS NOT NULL)                                                     AS is_deleted,
    -- EAV pivots (entity_type_id resolved for kbio_api_key)
    MAX(CASE WHEN ad.code = 'name'         THEN a.key_text  END)                   AS name,
    MAX(CASE WHEN ad.code = 'description'  THEN a.key_text  END)                   AS description,
    MAX(CASE WHEN ad.code = 'last_used_at' THEN a.key_text  END)                   AS last_used_at,
    MAX(CASE WHEN ad.code = 'rate_limit'   THEN a.key_text  END)                   AS rate_limit,
    (array_agg(a.key_jsonb) FILTER (WHERE ad.code = 'permissions' AND a.key_jsonb IS NOT NULL))[1] AS permissions,
    MAX(CASE WHEN ad.code = 'expires_at'   THEN a.key_text  END)                   AS expires_at,
    k.created_by,
    k.updated_by,
    k.created_at,
    k.updated_at
FROM "10_kbio"."16_fct_api_keys" k
LEFT JOIN "10_kbio"."09_dim_api_key_statuses" st ON st.id = k.status_id
LEFT JOIN "10_kbio"."20_dtl_attrs" a
       ON a.entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_api_key')
      AND a.entity_id = k.id
LEFT JOIN "10_kbio"."07_dim_attr_defs" ad ON ad.id = a.attr_def_id
GROUP BY
    k.id, k.org_id, k.workspace_id, k.key_prefix, k.key_hash,
    k.status_id, st.code,
    k.is_active, k.deleted_at,
    k.created_by, k.updated_by, k.created_at, k.updated_at;

COMMENT ON VIEW "10_kbio".v_api_keys IS
    'Workspace API keys with status dim code resolved and EAV attrs pivoted. '
    'Pivots: name, description, last_used_at, rate_limit, permissions, expires_at.';

GRANT SELECT ON "10_kbio".v_api_keys TO tennetctl_read;
GRANT SELECT ON "10_kbio".v_api_keys TO tennetctl_write;

-- DOWN =======================================================================

DROP VIEW  IF EXISTS "10_kbio".v_api_keys;
DROP TABLE IF EXISTS "10_kbio"."16_fct_api_keys";

-- Remove EAV attr defs for kbio_api_key
DELETE FROM "10_kbio"."07_dim_attr_defs"
WHERE entity_type_id = (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_api_key');

-- Remove entity type
DELETE FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_api_key';

DROP TABLE IF EXISTS "10_kbio"."09_dim_api_key_statuses";
