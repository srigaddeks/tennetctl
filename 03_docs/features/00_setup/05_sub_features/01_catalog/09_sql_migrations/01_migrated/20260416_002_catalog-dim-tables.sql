-- UP ====

-- Catalog dim tables: modules, node kinds, tx modes.

-- ── Modules ─────────────────────────────────────────────────────────

CREATE TABLE "01_catalog"."01_dim_modules" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    always_on       BOOLEAN NOT NULL DEFAULT false,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_modules PRIMARY KEY (id),
    CONSTRAINT uq_dim_modules_code UNIQUE (code)
);
COMMENT ON TABLE  "01_catalog"."01_dim_modules" IS 'Modules gated by the TENNETCTL_MODULES env var.';
COMMENT ON COLUMN "01_catalog"."01_dim_modules".id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "01_catalog"."01_dim_modules".code IS 'Module code (core, iam, audit, monitoring, vault, notify, billing, llmops).';
COMMENT ON COLUMN "01_catalog"."01_dim_modules".label IS 'Human-readable label.';
COMMENT ON COLUMN "01_catalog"."01_dim_modules".description IS 'Free-text description.';
COMMENT ON COLUMN "01_catalog"."01_dim_modules".always_on IS 'True for core/iam/audit — cannot be disabled by env var.';
COMMENT ON COLUMN "01_catalog"."01_dim_modules".deprecated_at IS 'Non-null when module is deprecated.';

-- ── Node kinds ──────────────────────────────────────────────────────

CREATE TABLE "01_catalog"."02_dim_node_kinds" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_node_kinds PRIMARY KEY (id),
    CONSTRAINT uq_dim_node_kinds_code UNIQUE (code)
);
COMMENT ON TABLE  "01_catalog"."02_dim_node_kinds" IS 'Node kinds: request (gateway-compiled), effect (runtime), control (flow-only).';
COMMENT ON COLUMN "01_catalog"."02_dim_node_kinds".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "01_catalog"."02_dim_node_kinds".code IS 'Kind code (request | effect | control).';
COMMENT ON COLUMN "01_catalog"."02_dim_node_kinds".label IS 'Human-readable label.';
COMMENT ON COLUMN "01_catalog"."02_dim_node_kinds".description IS 'Free-text description.';
COMMENT ON COLUMN "01_catalog"."02_dim_node_kinds".deprecated_at IS 'Non-null when kind is deprecated.';

-- ── Transaction modes ───────────────────────────────────────────────

CREATE TABLE "01_catalog"."03_dim_tx_modes" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_tx_modes PRIMARY KEY (id),
    CONSTRAINT uq_dim_tx_modes_code UNIQUE (code)
);
COMMENT ON TABLE  "01_catalog"."03_dim_tx_modes" IS 'Node runner transaction modes: caller | own | none.';
COMMENT ON COLUMN "01_catalog"."03_dim_tx_modes".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "01_catalog"."03_dim_tx_modes".code IS 'Mode code (caller | own | none).';
COMMENT ON COLUMN "01_catalog"."03_dim_tx_modes".label IS 'Human-readable label.';
COMMENT ON COLUMN "01_catalog"."03_dim_tx_modes".description IS 'Free-text description.';
COMMENT ON COLUMN "01_catalog"."03_dim_tx_modes".deprecated_at IS 'Non-null when mode is deprecated.';

-- DOWN ====

DROP TABLE IF EXISTS "01_catalog"."03_dim_tx_modes";
DROP TABLE IF EXISTS "01_catalog"."02_dim_node_kinds";
DROP TABLE IF EXISTS "01_catalog"."01_dim_modules";
