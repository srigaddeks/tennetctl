-- UP ====

-- Feature 02 (vault) — schema + EAV foundation + fct_vault_entries + view.
-- See ADR-028 for the envelope encryption design.
-- Pure-EAV: description lives in 21_dtl_attrs (not as a business column on fct_).

CREATE SCHEMA IF NOT EXISTS "02_vault";
COMMENT ON SCHEMA "02_vault" IS 'Secret storage with AES-256-GCM envelope encryption. See ADR-028.';

-- ── Entity types (EAV key for vault) ────────────────────────────────

CREATE TABLE "02_vault"."01_dim_entity_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_vault_dim_entity_types PRIMARY KEY (id),
    CONSTRAINT uq_vault_dim_entity_types_code UNIQUE (code)
);
COMMENT ON TABLE  "02_vault"."01_dim_entity_types" IS 'Vault entity categories. Keys EAV attrs in 21_dtl_attrs.';
COMMENT ON COLUMN "02_vault"."01_dim_entity_types".id IS 'Permanent manual ID. Never renumber. Referenced by dtl_attrs.entity_type_id.';
COMMENT ON COLUMN "02_vault"."01_dim_entity_types".code IS 'Entity category code (e.g. secret).';
COMMENT ON COLUMN "02_vault"."01_dim_entity_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "02_vault"."01_dim_entity_types".description IS 'Free-text description.';
COMMENT ON COLUMN "02_vault"."01_dim_entity_types".deprecated_at IS 'Non-null when no longer in use.';

-- ── EAV attribute definitions ───────────────────────────────────────

CREATE TABLE "02_vault"."20_dtl_attr_defs" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    entity_type_id  SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    value_type      TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_vault_dtl_attr_defs PRIMARY KEY (id),
    CONSTRAINT fk_vault_dtl_attr_defs_entity_type FOREIGN KEY (entity_type_id)
        REFERENCES "02_vault"."01_dim_entity_types"(id),
    CONSTRAINT chk_vault_dtl_attr_defs_value_type CHECK (value_type IN ('text','jsonb','smallint')),
    CONSTRAINT uq_vault_dtl_attr_defs_entity_code UNIQUE (entity_type_id, code)
);
COMMENT ON TABLE  "02_vault"."20_dtl_attr_defs" IS 'Registered EAV attribute definitions per vault entity type.';
COMMENT ON COLUMN "02_vault"."20_dtl_attr_defs".id IS 'Auto-generated identity.';
COMMENT ON COLUMN "02_vault"."20_dtl_attr_defs".entity_type_id IS 'Which entity type this attr applies to.';
COMMENT ON COLUMN "02_vault"."20_dtl_attr_defs".code IS 'Attr code (e.g. description).';
COMMENT ON COLUMN "02_vault"."20_dtl_attr_defs".label IS 'Human-readable label.';
COMMENT ON COLUMN "02_vault"."20_dtl_attr_defs".value_type IS 'Which key_* column carries the value: text | jsonb | smallint.';
COMMENT ON COLUMN "02_vault"."20_dtl_attr_defs".description IS 'Free-text description.';
COMMENT ON COLUMN "02_vault"."20_dtl_attr_defs".deprecated_at IS 'Non-null when deprecated.';

-- ── EAV attribute values ────────────────────────────────────────────

CREATE TABLE "02_vault"."21_dtl_attrs" (
    id              VARCHAR(36) NOT NULL,
    entity_type_id  SMALLINT NOT NULL,
    entity_id       VARCHAR(36) NOT NULL,
    attr_def_id     SMALLINT NOT NULL,
    key_text        TEXT,
    key_jsonb       JSONB,
    key_smallint    SMALLINT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_vault_dtl_attrs PRIMARY KEY (id),
    CONSTRAINT fk_vault_dtl_attrs_entity_type FOREIGN KEY (entity_type_id)
        REFERENCES "02_vault"."01_dim_entity_types"(id),
    CONSTRAINT fk_vault_dtl_attrs_attr_def FOREIGN KEY (attr_def_id)
        REFERENCES "02_vault"."20_dtl_attr_defs"(id),
    CONSTRAINT chk_vault_dtl_attrs_one_value CHECK (
        (CASE WHEN key_text     IS NOT NULL THEN 1 ELSE 0 END)
      + (CASE WHEN key_jsonb    IS NOT NULL THEN 1 ELSE 0 END)
      + (CASE WHEN key_smallint IS NOT NULL THEN 1 ELSE 0 END) = 1
    ),
    CONSTRAINT uq_vault_dtl_attrs_entity_attr UNIQUE (entity_type_id, entity_id, attr_def_id)
);
CREATE INDEX idx_vault_dtl_attrs_entity ON "02_vault"."21_dtl_attrs" (entity_type_id, entity_id);
COMMENT ON TABLE  "02_vault"."21_dtl_attrs" IS 'EAV attribute values for vault entities. Append-only (no updated_at); upsert via ON CONFLICT.';
COMMENT ON COLUMN "02_vault"."21_dtl_attrs".id IS 'UUID v7.';
COMMENT ON COLUMN "02_vault"."21_dtl_attrs".entity_type_id IS 'Which dim_entity_types row this attr belongs to.';
COMMENT ON COLUMN "02_vault"."21_dtl_attrs".entity_id IS 'UUID v7 of the vault entity (e.g. fct_vault_entries.id).';
COMMENT ON COLUMN "02_vault"."21_dtl_attrs".attr_def_id IS 'Which attribute definition.';
COMMENT ON COLUMN "02_vault"."21_dtl_attrs".key_text IS 'String value (exactly one key_* non-null).';
COMMENT ON COLUMN "02_vault"."21_dtl_attrs".key_jsonb IS 'JSON value.';
COMMENT ON COLUMN "02_vault"."21_dtl_attrs".key_smallint IS 'Smallint / dim FK value.';
COMMENT ON COLUMN "02_vault"."21_dtl_attrs".created_at IS 'Insert timestamp (append-only).';

-- ── Vault entries (ciphertext + wrapped DEK + nonce) ────────────────

CREATE TABLE "02_vault"."10_fct_vault_entries" (
    id               VARCHAR(36) NOT NULL,
    key              TEXT NOT NULL,
    version          SMALLINT NOT NULL DEFAULT 1,
    ciphertext       BYTEA NOT NULL,
    wrapped_dek      BYTEA NOT NULL,
    nonce            BYTEA NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT true,
    is_test          BOOLEAN NOT NULL DEFAULT false,
    deleted_at       TIMESTAMP,
    rotated_from_id  VARCHAR(36),
    created_by       VARCHAR(36) NOT NULL,
    updated_by       VARCHAR(36) NOT NULL,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_vault_entries PRIMARY KEY (id),
    CONSTRAINT uq_fct_vault_entries_key_version UNIQUE (key, version),
    CONSTRAINT fk_fct_vault_entries_rotated_from FOREIGN KEY (rotated_from_id)
        REFERENCES "02_vault"."10_fct_vault_entries"(id),
    CONSTRAINT chk_fct_vault_entries_nonce_len CHECK (octet_length(nonce) = 12),
    CONSTRAINT chk_fct_vault_entries_ciphertext_len CHECK (octet_length(ciphertext) > 0),
    CONSTRAINT chk_fct_vault_entries_wrapped_dek_len CHECK (octet_length(wrapped_dek) >= 44),
    CONSTRAINT chk_fct_vault_entries_key_shape CHECK (key ~ '^[a-z][a-z0-9._-]{0,127}$'),
    CONSTRAINT chk_fct_vault_entries_version_positive CHECK (version >= 1)
);
CREATE INDEX idx_fct_vault_entries_key_latest
    ON "02_vault"."10_fct_vault_entries" (key, version DESC)
    WHERE deleted_at IS NULL;
COMMENT ON TABLE  "02_vault"."10_fct_vault_entries" IS 'Envelope-encrypted secrets. Pure structural cols — description lives in 21_dtl_attrs. See ADR-028.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".id IS 'UUID v7. Stable per (key, version) tuple.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".key IS 'User-supplied stable identifier (e.g. auth.argon2.pepper). Lowercase dotted; shape enforced by chk.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".version IS 'Monotonic per key. Rotate creates a new row with version=prev+1.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".ciphertext IS 'AES-256-GCM ciphertext of the plaintext value.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".wrapped_dek IS '12-byte wrap_nonce || AESGCM(root_key).encrypt(wrap_nonce, dek). Min 44 bytes (12 nonce + 32 dek + 16 tag).';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".nonce IS '12-byte data nonce used when DEK encrypted the plaintext.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".is_active IS 'Whether this version is active. Rotate sets prev rows inactive is future behaviour; v0.2 leaves all versions active and reads newest.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".is_test IS 'Test-mode marker. Always false in v0.2; reserved for v0.3.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".deleted_at IS 'Soft-delete timestamp. DELETE marks all versions of a key.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".rotated_from_id IS 'FK to the prior version''s row on rotate. NULL for version=1.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".created_by IS 'User id (or ''sys'' for bootstrap) that created this version.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".updated_by IS 'User id that last touched this row (soft-delete).';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".updated_at IS 'Last update timestamp (app-set; no trigger).';

-- ── Flat read view — latest non-deleted version per key, description pivoted ──

CREATE VIEW "02_vault"."v_vault_entries" AS
SELECT
    latest.id,
    latest.key,
    latest.version,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description,
    latest.is_active,
    latest.is_test,
    latest.deleted_at,
    latest.rotated_from_id,
    latest.created_by,
    latest.updated_by,
    latest.created_at,
    latest.updated_at
FROM (
    SELECT DISTINCT ON (key)
        id, key, version, is_active, is_test, deleted_at, rotated_from_id,
        created_by, updated_by, created_at, updated_at
    FROM "02_vault"."10_fct_vault_entries"
    WHERE deleted_at IS NULL
    ORDER BY key, version DESC
) latest
LEFT JOIN "02_vault"."21_dtl_attrs" da
    ON da.entity_type_id = 1 AND da.entity_id = latest.id
LEFT JOIN "02_vault"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    latest.id, latest.key, latest.version, latest.is_active, latest.is_test,
    latest.deleted_at, latest.rotated_from_id, latest.created_by, latest.updated_by,
    latest.created_at, latest.updated_at;

COMMENT ON VIEW "02_vault"."v_vault_entries" IS 'Flat read shape for vault entries — latest non-deleted version per key, description pivoted from dtl_attrs. Metadata only; ciphertext is never exposed via this view.';

-- DOWN ====

DROP VIEW IF EXISTS "02_vault"."v_vault_entries";
DROP TABLE IF EXISTS "02_vault"."10_fct_vault_entries";
DROP TABLE IF EXISTS "02_vault"."21_dtl_attrs";
DROP TABLE IF EXISTS "02_vault"."20_dtl_attr_defs";
DROP TABLE IF EXISTS "02_vault"."01_dim_entity_types";
DROP SCHEMA IF EXISTS "02_vault";
