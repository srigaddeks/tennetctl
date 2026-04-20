-- UP ====

-- Catalog flow schema: DAG persistence for visual canvas.
-- Flows are DAGs of node instances joined by typed edges.
-- Flows go through draft → publish → immutable-version lifecycle (ADR-020).

-- ── Dimension tables ────────────────────────────────────────────────

-- Flow status: draft=1, published=2, archived=3
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

-- Edge kinds: next=1, success=2, failure=3, true_branch=4, false_branch=5
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
COMMENT ON COLUMN "01_catalog"."05_dim_flow_edge_kind".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "01_catalog"."05_dim_flow_edge_kind".code IS 'Edge kind code.';

-- Port types: any=1, string=2, number=3, boolean=4, object=5, array=6, uuid=7, datetime=8, binary=9, error=10
CREATE TABLE IF NOT EXISTS "01_catalog"."06_dim_port_type" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP NULL,
    CONSTRAINT pk_dim_port_type PRIMARY KEY (id),
    CONSTRAINT uq_dim_port_type_code UNIQUE (code)
);
COMMENT ON TABLE  "01_catalog"."06_dim_port_type" IS 'Port type system for typed-edge validation: any | string | number | boolean | object | array | uuid | datetime | binary | error.';
COMMENT ON COLUMN "01_catalog"."06_dim_port_type".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "01_catalog"."06_dim_port_type".code IS 'Port type code.';

-- ── Flow fact table ────────────────────────────────────────────────

-- fct_catalog_flows: the flow is the stable identity; versions are immutable snapshots
CREATE TABLE IF NOT EXISTS "01_catalog"."10_fct_flows" (
    id                      VARCHAR(36) NOT NULL,
    org_id                  VARCHAR(36) NOT NULL,
    workspace_id            VARCHAR(36) NOT NULL,
    slug                    TEXT NOT NULL,
    name                    TEXT NOT NULL,
    description             TEXT,
    current_version_id      VARCHAR(36),
    status_id               SMALLINT NOT NULL,
    is_test                 BOOLEAN NOT NULL DEFAULT false,
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36),
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at              TIMESTAMP,
    CONSTRAINT pk_fct_flows PRIMARY KEY (id),
    CONSTRAINT uq_fct_flows_slug UNIQUE (org_id, slug) WHERE deleted_at IS NULL,
    CONSTRAINT fk_fct_flows_status FOREIGN KEY (status_id) REFERENCES "01_catalog"."04_dim_flow_status"(id),
    CONSTRAINT fk_fct_flows_org FOREIGN KEY (org_id) REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_fct_flows_workspace FOREIGN KEY (workspace_id) REFERENCES "03_iam"."11_fct_workspaces"(id)
);
COMMENT ON TABLE  "01_catalog"."10_fct_flows" IS 'Persistent flow definitions. The flow is the stable identity; versions are immutable snapshots.';
COMMENT ON COLUMN "01_catalog"."10_fct_flows".id IS 'UUID v7 primary key.';
COMMENT ON COLUMN "01_catalog"."10_fct_flows".slug IS 'User-supplied flow slug (stable identifier within org).';
COMMENT ON COLUMN "01_catalog"."10_fct_flows".current_version_id IS 'FK to fct_catalog_flow_versions; current working version.';
COMMENT ON COLUMN "01_catalog"."10_fct_flows".status_id IS 'Draft, published, or archived.';

CREATE INDEX idx_fct_flows_org_status ON "01_catalog"."10_fct_flows"(org_id, status_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_fct_flows_workspace ON "01_catalog"."10_fct_flows"(workspace_id) WHERE deleted_at IS NULL;

-- ── Detail tables ──────────────────────────────────────────────────

-- dtl_catalog_flow_nodes: instance metadata within a flow version
CREATE TABLE IF NOT EXISTS "01_catalog"."20_dtl_flow_nodes" (
    id                      VARCHAR(36) NOT NULL,
    flow_version_id         VARCHAR(36) NOT NULL,
    node_key                TEXT NOT NULL,
    instance_label          TEXT NOT NULL,
    config_json             JSONB NOT NULL DEFAULT '{}',
    position_x              INT,
    position_y              INT,
    sort_order              SMALLINT,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dtl_flow_nodes PRIMARY KEY (id),
    CONSTRAINT uq_dtl_flow_nodes_instance UNIQUE (flow_version_id, instance_label),
    CONSTRAINT fk_dtl_flow_nodes_version FOREIGN KEY (flow_version_id) REFERENCES "01_catalog"."11_fct_flow_versions"(id)
);
COMMENT ON TABLE  "01_catalog"."20_dtl_flow_nodes" IS 'Node instances within a flow version. node_key references live registry (no FK).';
COMMENT ON COLUMN "01_catalog"."20_dtl_flow_nodes".node_key IS 'Stable node key from live registry (e.g., iam.auth_required). Code-first, no FK.';
COMMENT ON COLUMN "01_catalog"."20_dtl_flow_nodes".instance_label IS 'User-supplied label for this node instance (e.g., auth, handler, audit).';
COMMENT ON COLUMN "01_catalog"."20_dtl_flow_nodes".config_json IS 'Per-instance config validated against node schema.';
COMMENT ON COLUMN "01_catalog"."20_dtl_flow_nodes".position_x IS 'Canvas X position (pixels, nullable for auto-layout).';
COMMENT ON COLUMN "01_catalog"."20_dtl_flow_nodes".position_y IS 'Canvas Y position (pixels, nullable for auto-layout).';
COMMENT ON COLUMN "01_catalog"."20_dtl_flow_nodes".sort_order IS 'Rendering order hint.';

CREATE INDEX idx_dtl_flow_nodes_version ON "01_catalog"."20_dtl_flow_nodes"(flow_version_id);

-- dtl_catalog_flow_edges: typed connections between node instances
CREATE TABLE IF NOT EXISTS "01_catalog"."21_dtl_flow_edges" (
    id                      VARCHAR(36) NOT NULL,
    flow_version_id         VARCHAR(36) NOT NULL,
    from_node_id            VARCHAR(36) NOT NULL,
    from_port_key           TEXT NOT NULL,
    to_node_id              VARCHAR(36) NOT NULL,
    to_port_key             TEXT NOT NULL,
    edge_kind_id            SMALLINT NOT NULL,
    sort_order              SMALLINT,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dtl_flow_edges PRIMARY KEY (id),
    CONSTRAINT uq_dtl_flow_edges_connection UNIQUE (flow_version_id, from_node_id, from_port_key, to_node_id, to_port_key),
    CONSTRAINT fk_dtl_flow_edges_version FOREIGN KEY (flow_version_id) REFERENCES "01_catalog"."11_fct_flow_versions"(id),
    CONSTRAINT fk_dtl_flow_edges_from_node FOREIGN KEY (from_node_id) REFERENCES "01_catalog"."20_dtl_flow_nodes"(id),
    CONSTRAINT fk_dtl_flow_edges_to_node FOREIGN KEY (to_node_id) REFERENCES "01_catalog"."20_dtl_flow_nodes"(id),
    CONSTRAINT fk_dtl_flow_edges_kind FOREIGN KEY (edge_kind_id) REFERENCES "01_catalog"."05_dim_flow_edge_kind"(id)
);
COMMENT ON TABLE  "01_catalog"."21_dtl_flow_edges" IS 'Directed edges connecting node instances. Immutable once version is published.';
COMMENT ON COLUMN "01_catalog"."21_dtl_flow_edges".from_port_key IS 'Output port on source node.';
COMMENT ON COLUMN "01_catalog"."21_dtl_flow_edges".to_port_key IS 'Input port on target node.';
COMMENT ON COLUMN "01_catalog"."21_dtl_flow_edges".edge_kind_id IS 'Type of connection: next | success | failure | true_branch | false_branch.';

CREATE INDEX idx_dtl_flow_edges_version ON "01_catalog"."21_dtl_flow_edges"(flow_version_id);
CREATE INDEX idx_dtl_flow_edges_from_node ON "01_catalog"."21_dtl_flow_edges"(from_node_id);
CREATE INDEX idx_dtl_flow_edges_to_node ON "01_catalog"."21_dtl_flow_edges"(to_node_id);

-- DOWN ====

DROP INDEX IF EXISTS "01_catalog".idx_dtl_flow_edges_to_node;
DROP INDEX IF EXISTS "01_catalog".idx_dtl_flow_edges_from_node;
DROP INDEX IF EXISTS "01_catalog".idx_dtl_flow_edges_version;
DROP TABLE IF EXISTS "01_catalog"."21_dtl_flow_edges";

DROP INDEX IF EXISTS "01_catalog".idx_dtl_flow_nodes_version;
DROP TABLE IF EXISTS "01_catalog"."20_dtl_flow_nodes";

DROP INDEX IF EXISTS "01_catalog".idx_fct_flows_workspace;
DROP INDEX IF EXISTS "01_catalog".idx_fct_flows_org_status;
DROP TABLE IF EXISTS "01_catalog"."10_fct_flows";

DROP TABLE IF EXISTS "01_catalog"."06_dim_port_type";
DROP TABLE IF EXISTS "01_catalog"."05_dim_flow_edge_kind";
DROP TABLE IF EXISTS "01_catalog"."04_dim_flow_status";
