-- UP ====

-- Node Catalog Protocol v1 schema + EAV foundation.
-- See: 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
-- See: 03_docs/00_main/08_decisions/027_node_catalog_and_runner.md

CREATE SCHEMA IF NOT EXISTS "01_catalog";
COMMENT ON SCHEMA "01_catalog" IS 'Node Catalog Protocol v1 — mirrors feature.manifest.yaml entries on boot.';

-- ── Entity types (EAV key) ──────────────────────────────────────────

CREATE TABLE "01_catalog"."04_dim_entity_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_entity_types PRIMARY KEY (id),
    CONSTRAINT uq_dim_entity_types_code UNIQUE (code)
);
COMMENT ON TABLE  "01_catalog"."04_dim_entity_types" IS 'Entity categories in the catalog (feature, sub_feature, node, flow, flow_node). Keys every EAV attribute.';
COMMENT ON COLUMN "01_catalog"."04_dim_entity_types".id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "01_catalog"."04_dim_entity_types".code IS 'Stable code (feature, sub_feature, node, flow, flow_node).';
COMMENT ON COLUMN "01_catalog"."04_dim_entity_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "01_catalog"."04_dim_entity_types".description IS 'Free-text description.';
COMMENT ON COLUMN "01_catalog"."04_dim_entity_types".deprecated_at IS 'Non-null when no longer in use.';

-- ── EAV attribute definitions ───────────────────────────────────────

CREATE TABLE "01_catalog"."20_dtl_attr_defs" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    entity_type_id  SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    value_type      TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dtl_attr_defs PRIMARY KEY (id),
    CONSTRAINT fk_dtl_attr_defs_entity_type FOREIGN KEY (entity_type_id)
        REFERENCES "01_catalog"."04_dim_entity_types"(id),
    CONSTRAINT chk_dtl_attr_defs_value_type CHECK (value_type IN ('text','jsonb','smallint')),
    CONSTRAINT uq_dtl_attr_defs_entity_code UNIQUE (entity_type_id, code)
);
COMMENT ON TABLE  "01_catalog"."20_dtl_attr_defs" IS 'Registered EAV attribute definitions per entity type.';
COMMENT ON COLUMN "01_catalog"."20_dtl_attr_defs".id IS 'Auto-generated SMALLINT identity.';
COMMENT ON COLUMN "01_catalog"."20_dtl_attr_defs".entity_type_id IS 'Which entity type (feature/sub_feature/node/...) this attribute applies to.';
COMMENT ON COLUMN "01_catalog"."20_dtl_attr_defs".code IS 'Attribute code (e.g. label, description, tags, icon).';
COMMENT ON COLUMN "01_catalog"."20_dtl_attr_defs".label IS 'Human-readable label for the attribute.';
COMMENT ON COLUMN "01_catalog"."20_dtl_attr_defs".value_type IS 'Which value column carries the value: text | jsonb | smallint.';
COMMENT ON COLUMN "01_catalog"."20_dtl_attr_defs".description IS 'Free-text description.';
COMMENT ON COLUMN "01_catalog"."20_dtl_attr_defs".deprecated_at IS 'Non-null when no longer in use.';

-- ── EAV attribute values ────────────────────────────────────────────

CREATE TABLE "01_catalog"."21_dtl_attrs" (
    id              VARCHAR(36) NOT NULL,
    entity_type_id  SMALLINT NOT NULL,
    entity_id       SMALLINT NOT NULL,
    attr_def_id     SMALLINT NOT NULL,
    key_text        TEXT,
    key_jsonb       JSONB,
    key_smallint    SMALLINT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dtl_attrs PRIMARY KEY (id),
    CONSTRAINT fk_dtl_attrs_entity_type FOREIGN KEY (entity_type_id)
        REFERENCES "01_catalog"."04_dim_entity_types"(id),
    CONSTRAINT fk_dtl_attrs_attr_def FOREIGN KEY (attr_def_id)
        REFERENCES "01_catalog"."20_dtl_attr_defs"(id),
    CONSTRAINT chk_dtl_attrs_one_value CHECK (
        (CASE WHEN key_text     IS NOT NULL THEN 1 ELSE 0 END)
      + (CASE WHEN key_jsonb    IS NOT NULL THEN 1 ELSE 0 END)
      + (CASE WHEN key_smallint IS NOT NULL THEN 1 ELSE 0 END) = 1
    ),
    CONSTRAINT uq_dtl_attrs_entity_attr UNIQUE (entity_type_id, entity_id, attr_def_id)
);
CREATE INDEX idx_dtl_attrs_entity ON "01_catalog"."21_dtl_attrs" (entity_type_id, entity_id);
COMMENT ON TABLE  "01_catalog"."21_dtl_attrs" IS 'EAV attribute values keyed by (entity_type, entity_id, attr_def). Append-only — no updated_at.';
COMMENT ON COLUMN "01_catalog"."21_dtl_attrs".id IS 'UUID v7.';
COMMENT ON COLUMN "01_catalog"."21_dtl_attrs".entity_type_id IS 'Which dim_entity_types row this attr belongs to.';
COMMENT ON COLUMN "01_catalog"."21_dtl_attrs".entity_id IS 'ID of the entity in its fct_* table (SMALLINT to match catalog fct PKs).';
COMMENT ON COLUMN "01_catalog"."21_dtl_attrs".attr_def_id IS 'Which attribute definition this row instantiates.';
COMMENT ON COLUMN "01_catalog"."21_dtl_attrs".key_text IS 'String value (exactly one of key_* is non-null).';
COMMENT ON COLUMN "01_catalog"."21_dtl_attrs".key_jsonb IS 'JSON value (exactly one of key_* is non-null).';
COMMENT ON COLUMN "01_catalog"."21_dtl_attrs".key_smallint IS 'Smallint value / dim FK (exactly one of key_* is non-null).';
COMMENT ON COLUMN "01_catalog"."21_dtl_attrs".created_at IS 'Insert timestamp (append-only).';

-- DOWN ====

DROP TABLE IF EXISTS "01_catalog"."21_dtl_attrs";
DROP TABLE IF EXISTS "01_catalog"."20_dtl_attr_defs";
DROP TABLE IF EXISTS "01_catalog"."04_dim_entity_types";
DROP SCHEMA IF EXISTS "01_catalog";
