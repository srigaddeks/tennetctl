-- UP ====

-- DAG detail tables and read-side views for flows.
-- Prereq: 20260421_079 (schemas, fct_flows, fct_flow_versions, dtl_flows).

-- -------------------------------------------------------------------
-- Detail: node instances within a flow version
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "01_catalog"."21_dtl_flow_nodes" (
    id                      VARCHAR(36) NOT NULL,
    flow_version_id         VARCHAR(36) NOT NULL,
    node_key                TEXT NOT NULL,
    instance_label          TEXT NOT NULL,
    config_json             JSONB NOT NULL DEFAULT '{}',
    position_x              INT,
    position_y              INT,
    sort_order              SMALLINT,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dtl_flow_nodes               PRIMARY KEY (id),
    CONSTRAINT uq_dtl_flow_nodes_instance      UNIQUE (flow_version_id, instance_label),
    CONSTRAINT fk_dtl_flow_nodes_version       FOREIGN KEY (flow_version_id) REFERENCES "01_catalog"."11_fct_flow_versions"(id) ON DELETE CASCADE
);
COMMENT ON TABLE  "01_catalog"."21_dtl_flow_nodes" IS 'Node instances within a flow version. node_key references the live registry (no FK).';
COMMENT ON COLUMN "01_catalog"."21_dtl_flow_nodes".node_key IS 'Stable node key from live registry (e.g., iam.auth_required).';
COMMENT ON COLUMN "01_catalog"."21_dtl_flow_nodes".instance_label IS 'User-supplied label for this node instance.';
COMMENT ON COLUMN "01_catalog"."21_dtl_flow_nodes".config_json IS 'Per-instance config validated against node schema.';

CREATE INDEX IF NOT EXISTS idx_dtl_flow_nodes_version ON "01_catalog"."21_dtl_flow_nodes"(flow_version_id);

-- -------------------------------------------------------------------
-- Detail: typed edges between node instances
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "01_catalog"."22_dtl_flow_edges" (
    id                      VARCHAR(36) NOT NULL,
    flow_version_id         VARCHAR(36) NOT NULL,
    from_node_id            VARCHAR(36) NOT NULL,
    from_port_key           TEXT NOT NULL,
    to_node_id              VARCHAR(36) NOT NULL,
    to_port_key             TEXT NOT NULL,
    edge_kind_id            SMALLINT NOT NULL,
    sort_order              SMALLINT,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dtl_flow_edges              PRIMARY KEY (id),
    CONSTRAINT uq_dtl_flow_edges_connection   UNIQUE (flow_version_id, from_node_id, from_port_key, to_node_id, to_port_key),
    CONSTRAINT fk_dtl_flow_edges_version      FOREIGN KEY (flow_version_id) REFERENCES "01_catalog"."11_fct_flow_versions"(id) ON DELETE CASCADE,
    CONSTRAINT fk_dtl_flow_edges_from_node    FOREIGN KEY (from_node_id)    REFERENCES "01_catalog"."21_dtl_flow_nodes"(id) ON DELETE CASCADE,
    CONSTRAINT fk_dtl_flow_edges_to_node      FOREIGN KEY (to_node_id)      REFERENCES "01_catalog"."21_dtl_flow_nodes"(id) ON DELETE CASCADE,
    CONSTRAINT fk_dtl_flow_edges_kind         FOREIGN KEY (edge_kind_id)    REFERENCES "01_catalog"."05_dim_flow_edge_kind"(id)
);
COMMENT ON TABLE  "01_catalog"."22_dtl_flow_edges" IS 'Directed edges connecting node instances. Immutable once version is published.';
COMMENT ON COLUMN "01_catalog"."22_dtl_flow_edges".edge_kind_id IS 'Type of connection: next | success | failure | true_branch | false_branch.';

CREATE INDEX IF NOT EXISTS idx_dtl_flow_edges_version   ON "01_catalog"."22_dtl_flow_edges"(flow_version_id);
CREATE INDEX IF NOT EXISTS idx_dtl_flow_edges_from_node ON "01_catalog"."22_dtl_flow_edges"(from_node_id);
CREATE INDEX IF NOT EXISTS idx_dtl_flow_edges_to_node   ON "01_catalog"."22_dtl_flow_edges"(to_node_id);

-- -------------------------------------------------------------------
-- Views
-- -------------------------------------------------------------------

CREATE OR REPLACE VIEW "01_catalog".v_flows AS
SELECT
    f.id,
    f.org_id,
    f.workspace_id,
    d.slug,
    d.name,
    d.description,
    f.current_version_id,
    f.status_id,
    s.code  AS status,
    s.label AS status_label,
    COALESCE(fv.version_number, 0) AS current_version_number,
    (SELECT COUNT(*) FROM "01_catalog"."21_dtl_flow_nodes" n WHERE n.flow_version_id = fv.id) AS node_count,
    (SELECT COUNT(*) FROM "01_catalog"."22_dtl_flow_edges" e WHERE e.flow_version_id = fv.id) AS edge_count,
    f.is_active,
    f.is_test,
    f.created_by,
    f.updated_by,
    f.created_at,
    f.updated_at,
    f.deleted_at
FROM "01_catalog"."10_fct_flows" f
LEFT JOIN "01_catalog"."20_dtl_flows"        d  ON d.flow_id = f.id
LEFT JOIN "01_catalog"."04_dim_flow_status"  s  ON f.status_id = s.id
LEFT JOIN "01_catalog"."11_fct_flow_versions" fv ON f.current_version_id = fv.id;

COMMENT ON VIEW "01_catalog".v_flows IS 'Read model: flows joined to string detail, status, and current version aggregates.';

CREATE OR REPLACE VIEW "01_catalog".v_flow_versions AS
SELECT
    fv.id,
    fv.flow_id,
    fv.org_id,
    d.slug  AS flow_slug,
    d.name  AS flow_name,
    fv.version_number,
    fv.status_id,
    s.code  AS status,
    s.label AS status_label,
    fv.dag_hash,
    fv.published_at,
    fv.published_by_user_id,
    (SELECT COUNT(*) FROM "01_catalog"."21_dtl_flow_nodes" n WHERE n.flow_version_id = fv.id) AS node_count,
    (SELECT COUNT(*) FROM "01_catalog"."22_dtl_flow_edges" e WHERE e.flow_version_id = fv.id) AS edge_count,
    fv.is_active,
    fv.is_test,
    fv.created_by,
    fv.updated_by,
    fv.created_at,
    fv.updated_at,
    fv.deleted_at
FROM "01_catalog"."11_fct_flow_versions" fv
JOIN       "01_catalog"."10_fct_flows" f ON fv.flow_id = f.id
LEFT JOIN  "01_catalog"."20_dtl_flows" d ON d.flow_id  = f.id
LEFT JOIN  "01_catalog"."04_dim_flow_status" s ON fv.status_id = s.id;

COMMENT ON VIEW "01_catalog".v_flow_versions IS 'Read model: flow versions with resolved status and denormalized flow strings.';

-- DOWN ====

DROP VIEW IF EXISTS "01_catalog".v_flow_versions;
DROP VIEW IF EXISTS "01_catalog".v_flows;

DROP INDEX IF EXISTS "01_catalog".idx_dtl_flow_edges_to_node;
DROP INDEX IF EXISTS "01_catalog".idx_dtl_flow_edges_from_node;
DROP INDEX IF EXISTS "01_catalog".idx_dtl_flow_edges_version;
DROP TABLE IF EXISTS "01_catalog"."22_dtl_flow_edges";

DROP INDEX IF EXISTS "01_catalog".idx_dtl_flow_nodes_version;
DROP TABLE IF EXISTS "01_catalog"."21_dtl_flow_nodes";
