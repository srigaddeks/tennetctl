-- UP ====

-- Flow versions: immutable snapshots with draft→publish lifecycle.
-- Each flow has a "current_version_id" pointing to the latest working version.
-- Only one draft per flow (enforced by partial unique index).

-- ── Flow versions fact table ────────────────────────────────────────

-- fct_catalog_flow_versions: immutable version snapshots
CREATE TABLE IF NOT EXISTS "01_catalog"."11_fct_flow_versions" (
    id                      VARCHAR(36) NOT NULL,
    flow_id                 VARCHAR(36) NOT NULL,
    version_number          INT NOT NULL,
    status_id               SMALLINT NOT NULL,
    dag_hash                CHAR(64),
    published_at            TIMESTAMP,
    published_by_user_id    VARCHAR(36),
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at              TIMESTAMP,
    CONSTRAINT pk_fct_flow_versions PRIMARY KEY (id),
    CONSTRAINT uq_fct_flow_versions_flow_number UNIQUE (flow_id, version_number),
    CONSTRAINT fk_fct_flow_versions_flow FOREIGN KEY (flow_id) REFERENCES "01_catalog"."10_fct_flows"(id),
    CONSTRAINT fk_fct_flow_versions_status FOREIGN KEY (status_id) REFERENCES "01_catalog"."04_dim_flow_status"(id),
    CONSTRAINT fk_fct_flow_versions_published_by FOREIGN KEY (published_by_user_id) REFERENCES "03_iam"."12_fct_users"(id)
);
COMMENT ON TABLE  "01_catalog"."11_fct_flow_versions" IS 'Immutable flow version snapshots. Only one draft per flow.';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".id IS 'UUID v7 primary key.';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".flow_id IS 'FK to fct_catalog_flows.';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".version_number IS 'Monotonic sequence (1, 2, 3, ...).';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".status_id IS 'Draft, published, or archived.';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".dag_hash IS 'SHA256 of canonical DAG (set on publish).';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".published_at IS 'Timestamp when version was published (NULL for draft).';
COMMENT ON COLUMN "01_catalog"."11_fct_flow_versions".published_by_user_id IS 'User who published the version.';

-- Partial unique index: enforce at most one draft per flow
CREATE UNIQUE INDEX idx_fct_flow_versions_one_draft
    ON "01_catalog"."11_fct_flow_versions"(flow_id)
    WHERE status_id = 1 AND deleted_at IS NULL;

CREATE INDEX idx_fct_flow_versions_flow_status ON "01_catalog"."11_fct_flow_versions"(flow_id, status_id);
CREATE INDEX idx_fct_flow_versions_published_by ON "01_catalog"."11_fct_flow_versions"(published_by_user_id);

-- ── Views ────────────────────────────────────────────────────────────

-- v_catalog_flows: read model for flow listings
CREATE OR REPLACE VIEW "01_catalog".v_flows AS
SELECT
    f.id,
    f.org_id,
    f.workspace_id,
    f.slug,
    f.name,
    f.description,
    f.current_version_id,
    s.code AS status,
    s.label AS status_label,
    COALESCE(fv.version_number, 0) AS current_version_number,
    COUNT(DISTINCT n.id) FILTER (WHERE fv.deleted_at IS NULL) AS node_count,
    COUNT(DISTINCT e.id) FILTER (WHERE fv.deleted_at IS NULL) AS edge_count,
    f.created_at,
    f.updated_at,
    f.deleted_at
FROM "01_catalog"."10_fct_flows" f
LEFT JOIN "01_catalog"."04_dim_flow_status" s ON f.status_id = s.id
LEFT JOIN "01_catalog"."11_fct_flow_versions" fv ON f.current_version_id = fv.id
LEFT JOIN "01_catalog"."20_dtl_flow_nodes" n ON fv.id = n.flow_version_id
LEFT JOIN "01_catalog"."21_dtl_flow_edges" e ON fv.id = e.flow_version_id
GROUP BY f.id, f.org_id, f.workspace_id, f.slug, f.name, f.description,
         f.current_version_id, s.code, s.label, fv.version_number,
         f.created_at, f.updated_at, f.deleted_at;

COMMENT ON VIEW "01_catalog".v_flows IS 'Read model: flows with resolved status, current version info, and aggregated node/edge counts.';

-- v_catalog_flow_versions: read model for version details
CREATE OR REPLACE VIEW "01_catalog".v_flow_versions AS
SELECT
    fv.id,
    fv.flow_id,
    f.slug AS flow_slug,
    f.name AS flow_name,
    fv.version_number,
    s.code AS status,
    s.label AS status_label,
    fv.dag_hash,
    fv.published_at,
    fv.published_by_user_id,
    COUNT(DISTINCT n.id) AS node_count,
    COUNT(DISTINCT e.id) AS edge_count,
    fv.created_at,
    fv.deleted_at
FROM "01_catalog"."11_fct_flow_versions" fv
JOIN "01_catalog"."10_fct_flows" f ON fv.flow_id = f.id
LEFT JOIN "01_catalog"."04_dim_flow_status" s ON fv.status_id = s.id
LEFT JOIN "01_catalog"."20_dtl_flow_nodes" n ON fv.id = n.flow_version_id
LEFT JOIN "01_catalog"."21_dtl_flow_edges" e ON fv.id = e.flow_version_id
GROUP BY fv.id, fv.flow_id, f.slug, f.name, fv.version_number,
         s.code, s.label, fv.dag_hash, fv.published_at, fv.published_by_user_id,
         fv.created_at, fv.deleted_at;

COMMENT ON VIEW "01_catalog".v_flow_versions IS 'Read model: flow versions with resolved status and aggregated DAG metrics.';

-- DOWN ====

DROP VIEW IF EXISTS "01_catalog".v_flow_versions;
DROP VIEW IF EXISTS "01_catalog".v_flows;

DROP INDEX IF EXISTS "01_catalog".idx_fct_flow_versions_published_by;
DROP INDEX IF EXISTS "01_catalog".idx_fct_flow_versions_flow_status;
DROP INDEX IF EXISTS "01_catalog".idx_fct_flow_versions_one_draft;

DROP TABLE IF EXISTS "01_catalog"."11_fct_flow_versions";
