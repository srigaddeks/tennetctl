-- UP ====

-- Catalog fct tables: features, sub-features, nodes.
--
-- Note: deviates from the standard fct_* rule of VARCHAR(36) UUID v7 PKs.
-- Catalog entities are system-level (not user data), seeded via manifest
-- upsert, and referenced by other catalog tables. SMALLINT IDENTITY PKs
-- keep the index pages small and make manifest-driven upsert-by-key
-- simpler. User-approved deviation 2026-04-16.

-- ── Features ────────────────────────────────────────────────────────

CREATE TABLE "01_catalog"."10_fct_features" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    key             TEXT NOT NULL,
    number          SMALLINT NOT NULL,
    module_id       SMALLINT NOT NULL,
    deprecated_at   TIMESTAMP,
    tombstoned_at   TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_features PRIMARY KEY (id),
    CONSTRAINT uq_fct_features_key UNIQUE (key),
    CONSTRAINT uq_fct_features_number UNIQUE (number),
    CONSTRAINT uq_fct_features_module_id UNIQUE (module_id),
    CONSTRAINT fk_fct_features_module FOREIGN KEY (module_id)
        REFERENCES "01_catalog"."01_dim_modules"(id)
);
COMMENT ON TABLE  "01_catalog"."10_fct_features" IS 'Features registered from feature.manifest.yaml on boot. One feature per module in v1.';
COMMENT ON COLUMN "01_catalog"."10_fct_features".id IS 'SMALLINT identity (system-level, not UUID).';
COMMENT ON COLUMN "01_catalog"."10_fct_features".key IS 'Stable NCP key, e.g. "iam". Equals module code in v1.';
COMMENT ON COLUMN "01_catalog"."10_fct_features".number IS 'Permanent feature slot (01–99) from CLAUDE.md feature-number table.';
COMMENT ON COLUMN "01_catalog"."10_fct_features".module_id IS 'FK to dim_modules — gates this feature under TENNETCTL_MODULES.';
COMMENT ON COLUMN "01_catalog"."10_fct_features".deprecated_at IS 'Non-null when the feature is deprecated.';
COMMENT ON COLUMN "01_catalog"."10_fct_features".tombstoned_at IS 'Non-null when the feature key is locked from reuse (≥180d after deprecated_at).';
COMMENT ON COLUMN "01_catalog"."10_fct_features".created_at IS 'Catalog upsert timestamp.';
COMMENT ON COLUMN "01_catalog"."10_fct_features".updated_at IS 'Catalog last-update timestamp (set by boot loader).';

-- ── Sub-features ────────────────────────────────────────────────────

CREATE TABLE "01_catalog"."11_fct_sub_features" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    key             TEXT NOT NULL,
    feature_id      SMALLINT NOT NULL,
    number          SMALLINT NOT NULL,
    deprecated_at   TIMESTAMP,
    tombstoned_at   TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_sub_features PRIMARY KEY (id),
    CONSTRAINT uq_fct_sub_features_key UNIQUE (key),
    CONSTRAINT uq_fct_sub_features_feature_number UNIQUE (feature_id, number),
    CONSTRAINT fk_fct_sub_features_feature FOREIGN KEY (feature_id)
        REFERENCES "01_catalog"."10_fct_features"(id)
);
CREATE INDEX idx_fct_sub_features_feature ON "01_catalog"."11_fct_sub_features" (feature_id);
COMMENT ON TABLE  "01_catalog"."11_fct_sub_features" IS 'Sub-features registered from feature.manifest.yaml. Scoped under a feature.';
COMMENT ON COLUMN "01_catalog"."11_fct_sub_features".id IS 'SMALLINT identity.';
COMMENT ON COLUMN "01_catalog"."11_fct_sub_features".key IS 'Stable NCP key, e.g. "iam.orgs". Must begin with parent feature key.';
COMMENT ON COLUMN "01_catalog"."11_fct_sub_features".feature_id IS 'FK to fct_features.';
COMMENT ON COLUMN "01_catalog"."11_fct_sub_features".number IS 'Sub-feature slot (01–99) within its feature.';
COMMENT ON COLUMN "01_catalog"."11_fct_sub_features".deprecated_at IS 'Non-null when the sub-feature is deprecated.';
COMMENT ON COLUMN "01_catalog"."11_fct_sub_features".tombstoned_at IS 'Non-null when the key is locked from reuse.';
COMMENT ON COLUMN "01_catalog"."11_fct_sub_features".created_at IS 'Catalog upsert timestamp.';
COMMENT ON COLUMN "01_catalog"."11_fct_sub_features".updated_at IS 'Catalog last-update timestamp.';

-- ── Nodes ───────────────────────────────────────────────────────────

CREATE TABLE "01_catalog"."12_fct_nodes" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    key             TEXT NOT NULL,
    sub_feature_id  SMALLINT NOT NULL,
    kind_id         SMALLINT NOT NULL,
    handler_path    TEXT NOT NULL,
    version         SMALLINT NOT NULL DEFAULT 1,
    emits_audit     BOOLEAN NOT NULL DEFAULT false,
    timeout_ms      INTEGER NOT NULL DEFAULT 5000,
    retries         SMALLINT NOT NULL DEFAULT 0,
    tx_mode_id      SMALLINT NOT NULL,
    deprecated_at   TIMESTAMP,
    tombstoned_at   TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_nodes PRIMARY KEY (id),
    CONSTRAINT uq_fct_nodes_key UNIQUE (key),
    CONSTRAINT fk_fct_nodes_sub_feature FOREIGN KEY (sub_feature_id)
        REFERENCES "01_catalog"."11_fct_sub_features"(id),
    CONSTRAINT fk_fct_nodes_kind FOREIGN KEY (kind_id)
        REFERENCES "01_catalog"."02_dim_node_kinds"(id),
    CONSTRAINT fk_fct_nodes_tx_mode FOREIGN KEY (tx_mode_id)
        REFERENCES "01_catalog"."03_dim_tx_modes"(id),
    CONSTRAINT chk_fct_nodes_timeout CHECK (timeout_ms BETWEEN 100 AND 600000),
    CONSTRAINT chk_fct_nodes_retries CHECK (retries BETWEEN 0 AND 3),
    CONSTRAINT chk_fct_nodes_version CHECK (version >= 1),
    CONSTRAINT chk_fct_nodes_effect_must_emit_audit CHECK (kind_id <> 2 OR emits_audit = true)
);
CREATE INDEX idx_fct_nodes_sub_feature ON "01_catalog"."12_fct_nodes" (sub_feature_id);
CREATE INDEX idx_fct_nodes_kind ON "01_catalog"."12_fct_nodes" (kind_id);
COMMENT ON TABLE  "01_catalog"."12_fct_nodes" IS 'Nodes registered from feature.manifest.yaml. Handler_path resolves via importlib at runtime.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".id IS 'SMALLINT identity.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".key IS 'Stable NCP key, e.g. "iam.orgs.create". Must begin with parent sub-feature key.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".sub_feature_id IS 'FK to fct_sub_features.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".kind_id IS 'FK to dim_node_kinds (1=request, 2=effect, 3=control).';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".handler_path IS 'Python dotted path to handler class, relative to feature package.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".version IS 'Node semantic version. Bump on breaking Input/Output changes.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".emits_audit IS 'True iff the node emits an audit event (effect nodes must).';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".timeout_ms IS 'Hard wall time before runner cancels (100..600000 ms).';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".retries IS 'Auto-retry count on TransientError (0..3).';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".tx_mode_id IS 'FK to dim_tx_modes (caller | own | none).';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".deprecated_at IS 'Non-null when the node is deprecated.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".tombstoned_at IS 'Non-null when the key is locked from reuse.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".created_at IS 'Catalog upsert timestamp.';
COMMENT ON COLUMN "01_catalog"."12_fct_nodes".updated_at IS 'Catalog last-update timestamp.';

-- DOWN ====

DROP TABLE IF EXISTS "01_catalog"."12_fct_nodes";
DROP TABLE IF EXISTS "01_catalog"."11_fct_sub_features";
DROP TABLE IF EXISTS "01_catalog"."10_fct_features";
