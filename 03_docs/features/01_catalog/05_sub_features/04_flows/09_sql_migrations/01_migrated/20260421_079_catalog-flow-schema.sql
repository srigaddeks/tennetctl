-- UP ====

-- Catalog flow schema: DAG persistence for visual canvas.
-- Flows are DAGs of node instances joined by typed edges.
-- Flows go through draft -> publish -> immutable-version lifecycle (ADR-020).
--
-- Structural split (Pure-EAV rule: no strings/JSONB on fct_*):
--   10_fct_flows         -- identity only (ids + status_id + audit cols)
--   20_dtl_flows         -- slug/name/description (one row per flow)
--   11_fct_flow_versions -- version identity + hash + publish metadata
--   Circular FK (fct_flows.current_version_id -> fct_flow_versions.id)
--   is added at the end after both tables exist.

-- -------------------------------------------------------------------
-- Dimension tables
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "01_catalog"."04_dim_flow_status" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP NULL,
    CONSTRAINT pk_dim_flow_status PRIMARY KEY (id),
    CONSTRAINT uq_dim_flow_status_code UNIQUE (code)
);
COMMENT ON TABLE  "01_catalog"."04_dim_flow_status" IS 'Flow lifecycle status: draft, published, archived.';
COMMENT ON COLUMN "01_catalog"."04_dim_flow_status".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "01_catalog"."04_dim_flow_status".code IS 'Status code (draft | published | archived).';

CREATE TABLE IF NOT EXISTS "01_catalog"."05_dim_flow_edge_kind" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP NULL,
    CONSTRAINT pk_dim_flow_edge_kind PRIMARY KEY (id),
    CONSTRAINT uq_dim_flow_edge_kind_code UNIQUE (code)
);
COMMENT ON TABLE  "01_catalog"."05_dim_flow_edge_kind" IS 'Edge kinds for DAG connections: next | success | failure | true_branch | false_branch.';

CREATE TABLE IF NOT EXISTS "01_catalog"."06_dim_port_type" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP NULL,
    CONSTRAINT pk_dim_port_type PRIMARY KEY (id),
    CONSTRAINT uq_dim_port_type_code UNIQUE (code)
);
COMMENT ON TABLE  "01_catalog"."06_dim_port_type" IS 'Port type system for typed-edge validation.';

-- -------------------------------------------------------------------
-- Fact: flows (identity only - no strings, no JSONB)
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "01_catalog"."10_fct_flows" (
    id                      VARCHAR(36) NOT NULL,
    org_id                  VARCHAR(36) NOT NULL,
    workspace_id            VARCHAR(36) NOT NULL,
    status_id               SMALLINT NOT NULL,
    current_version_id      VARCHAR(36),
    is_active               BOOLEAN NOT NULL DEFAULT true,
    is_test                 BOOLEAN NOT NULL DEFAULT false,
    deleted_at              TIMESTAMP,
    created_by              VARCHAR(36) NOT NULL,
    updated_by              VARCHAR(36) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_flows PRIMARY KEY (id),
    CONSTRAINT fk_fct_flows_status    FOREIGN KEY (status_id)    REFERENCES "01_catalog"."04_dim_flow_status"(id),
    CONSTRAINT fk_fct_flows_org       FOREIGN KEY (org_id)       REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_fct_flows_workspace FOREIGN KEY (workspace_id) REFERENCES "03_iam"."11_fct_workspaces"(id)
);
COMMENT ON TABLE  "01_catalog"."10_fct_flows" IS 'Persistent flow identity. Strings live in 20_dtl_flows.';
COMMENT ON COLUMN "01_catalog"."10_fct_flows".id IS 'UUID v7 primary key.';
COMMENT ON COLUMN "01_catalog"."10_fct_flows".current_version_id IS 'FK to 11_fct_flow_versions; current working version. Circular FK added at end of migration.';

CREATE INDEX IF NOT EXISTS idx_fct_flows_org_status ON "01_catalog"."10_fct_flows"(org_id, status_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_fct_flows_workspace  ON "01_catalog"."10_fct_flows"(workspace_id)      WHERE deleted_at IS NULL;

-- -------------------------------------------------------------------
-- Fact: flow versions
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "01_catalog"."11_fct_flow_versions" (
    id                      VARCHAR(36) NOT NULL,
    flow_id                 VARCHAR(36) NOT NULL,
    org_id                  VARCHAR(36) NOT NULL,
    version_number          INT NOT NULL,
    status_id               SMALLINT NOT NULL,
    dag_hash                CHAR(64),
    published_at            TIMESTAMP,
    published_by_user_id    VARCHAR(36),
    is_active               BOOLEAN NOT NULL DEFAULT true,
    is_test                 BOOLEAN NOT NULL DEFAULT false,
    deleted_at              TIMESTAMP,
    created_by              VARCHAR(36) NOT NULL,
    updated_by              VARCHAR(36) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_flow_versions                 PRIMARY KEY (id),
    CONSTRAINT uq_fct_flow_versions_flow_number     UNIQUE (flow_id, version_number),
    CONSTRAINT fk_fct_flow_versions_flow            FOREIGN KEY (flow_id)              REFERENCES "01_catalog"."10_fct_flows"(id),
    CONSTRAINT fk_fct_flow_versions_status          FOREIGN KEY (status_id)            REFERENCES "01_catalog"."04_dim_flow_status"(id),
    CONSTRAINT fk_fct_flow_versions_org             FOREIGN KEY (org_id)               REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_fct_flow_versions_published_by    FOREIGN KEY (published_by_user_id) REFERENCES "03_iam"."12_fct_users"(id)
);
COMMENT ON TABLE  "01_catalog"."11_fct_flow_versions" IS 'Immutable flow version snapshots. Only one draft per flow (enforced by partial index).';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".version_number IS 'Monotonic sequence (1, 2, 3, ...).';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".dag_hash IS 'SHA256 of canonical DAG (set on publish).';

-- At most one draft per flow
CREATE UNIQUE INDEX IF NOT EXISTS uq_fct_flow_versions_one_draft
    ON "01_catalog"."11_fct_flow_versions"(flow_id)
    WHERE status_id = 1 AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_fct_flow_versions_flow_status   ON "01_catalog"."11_fct_flow_versions"(flow_id, status_id);
CREATE INDEX IF NOT EXISTS idx_fct_flow_versions_published_by  ON "01_catalog"."11_fct_flow_versions"(published_by_user_id);

-- Circular FK from fct_flows.current_version_id to fct_flow_versions.id
ALTER TABLE "01_catalog"."10_fct_flows"
    ADD CONSTRAINT fk_fct_flows_current_version
    FOREIGN KEY (current_version_id) REFERENCES "01_catalog"."11_fct_flow_versions"(id);

-- -------------------------------------------------------------------
-- Detail: flow strings (Pure-EAV split)
-- -------------------------------------------------------------------
-- Fixed-schema dtl (not dim_attr_defs EAV) - one row per flow,
-- carries the human-facing strings. Partial unique on slug scoped
-- to org, honoring soft-delete via local deleted_at mirror.

CREATE TABLE IF NOT EXISTS "01_catalog"."20_dtl_flows" (
    flow_id         VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    slug            TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    deleted_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dtl_flows      PRIMARY KEY (flow_id),
    CONSTRAINT fk_dtl_flows_flow FOREIGN KEY (flow_id) REFERENCES "01_catalog"."10_fct_flows"(id) ON DELETE CASCADE,
    CONSTRAINT fk_dtl_flows_org  FOREIGN KEY (org_id)  REFERENCES "03_iam"."10_fct_orgs"(id)
);
COMMENT ON TABLE  "01_catalog"."20_dtl_flows" IS 'String detail for flows: slug, name, description. One row per flow.';
COMMENT ON COLUMN "01_catalog"."20_dtl_flows".slug IS 'User-supplied flow slug (stable identifier within org).';

CREATE UNIQUE INDEX IF NOT EXISTS uq_dtl_flows_org_slug
    ON "01_catalog"."20_dtl_flows"(org_id, slug)
    WHERE deleted_at IS NULL;

-- DOWN ====

DROP INDEX IF EXISTS "01_catalog".uq_dtl_flows_org_slug;
DROP TABLE IF EXISTS "01_catalog"."20_dtl_flows";

ALTER TABLE "01_catalog"."10_fct_flows" DROP CONSTRAINT IF EXISTS fk_fct_flows_current_version;

DROP INDEX IF EXISTS "01_catalog".idx_fct_flow_versions_published_by;
DROP INDEX IF EXISTS "01_catalog".idx_fct_flow_versions_flow_status;
DROP INDEX IF EXISTS "01_catalog".uq_fct_flow_versions_one_draft;
DROP TABLE IF EXISTS "01_catalog"."11_fct_flow_versions";

DROP INDEX IF EXISTS "01_catalog".idx_fct_flows_workspace;
DROP INDEX IF EXISTS "01_catalog".idx_fct_flows_org_status;
DROP TABLE IF EXISTS "01_catalog"."10_fct_flows";

DROP TABLE IF EXISTS "01_catalog"."06_dim_port_type";
DROP TABLE IF EXISTS "01_catalog"."05_dim_flow_edge_kind";
DROP TABLE IF EXISTS "01_catalog"."04_dim_flow_status";
