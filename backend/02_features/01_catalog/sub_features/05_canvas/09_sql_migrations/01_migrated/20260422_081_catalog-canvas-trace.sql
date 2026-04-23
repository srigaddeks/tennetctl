-- UP ====

-- Catalog Canvas trace: flow-run identity and event stream, plus the two
-- read-only views the canvas renderer depends on for per-node + per-edge
-- status overlay.
--
-- Depends on: 079 (fct_flows, fct_flow_versions), 080 (dtl_flow_nodes/edges).

-- -------------------------------------------------------------------
-- Dimensions
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "01_catalog"."07_dim_flow_run_status" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_flow_run_status PRIMARY KEY (id),
    CONSTRAINT uq_dim_flow_run_status_code UNIQUE (code)
);
COMMENT ON TABLE "01_catalog"."07_dim_flow_run_status" IS 'Flow run terminal status. Seeded: running=1, completed=2, failed=3, cancelled=4.';

CREATE TABLE IF NOT EXISTS "01_catalog"."08_dim_trace_node_status" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_trace_node_status PRIMARY KEY (id),
    CONSTRAINT uq_dim_trace_node_status_code UNIQUE (code)
);
COMMENT ON TABLE "01_catalog"."08_dim_trace_node_status" IS 'Canvas trace overlay status per node. Seeded: pending=1, running=2, success=3, failure=4, skipped=5, timed_out=6.';

CREATE TABLE IF NOT EXISTS "01_catalog"."09_dim_flow_run_event_kind" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_flow_run_event_kind PRIMARY KEY (id),
    CONSTRAINT uq_dim_flow_run_event_kind_code UNIQUE (code)
);
COMMENT ON TABLE "01_catalog"."09_dim_flow_run_event_kind" IS 'Event kinds emitted during a flow run. Seeded: started=1, success=2, failure=3, failure_handled=4, skipped=5, timed_out=6, finished=7.';

-- -------------------------------------------------------------------
-- Fact: flow runs (identity + lifecycle timestamps)
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "01_catalog"."12_fct_flow_runs" (
    id                      VARCHAR(36) NOT NULL,
    flow_version_id         VARCHAR(36) NOT NULL,
    org_id                  VARCHAR(36) NOT NULL,
    workspace_id            VARCHAR(36) NOT NULL,
    started_by_user_id      VARCHAR(36),
    status_id               SMALLINT NOT NULL,
    started_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at             TIMESTAMP,
    is_active               BOOLEAN NOT NULL DEFAULT true,
    is_test                 BOOLEAN NOT NULL DEFAULT false,
    deleted_at              TIMESTAMP,
    created_by              VARCHAR(36) NOT NULL,
    updated_by              VARCHAR(36) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_flow_runs              PRIMARY KEY (id),
    CONSTRAINT fk_fct_flow_runs_version      FOREIGN KEY (flow_version_id)    REFERENCES "01_catalog"."11_fct_flow_versions"(id),
    CONSTRAINT fk_fct_flow_runs_org          FOREIGN KEY (org_id)             REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_fct_flow_runs_workspace    FOREIGN KEY (workspace_id)       REFERENCES "03_iam"."11_fct_workspaces"(id),
    CONSTRAINT fk_fct_flow_runs_started_by   FOREIGN KEY (started_by_user_id) REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_fct_flow_runs_status       FOREIGN KEY (status_id)          REFERENCES "01_catalog"."07_dim_flow_run_status"(id)
);
COMMENT ON TABLE "01_catalog"."12_fct_flow_runs" IS 'One row per flow execution. Per-node events in 60_evt_flow_run_events.';

CREATE INDEX IF NOT EXISTS idx_fct_flow_runs_version_started ON "01_catalog"."12_fct_flow_runs"(flow_version_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_fct_flow_runs_org_started     ON "01_catalog"."12_fct_flow_runs"(org_id, started_at DESC);

-- -------------------------------------------------------------------
-- Events: per-node execution events (append-only)
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "01_catalog"."60_evt_flow_run_events" (
    id                  VARCHAR(36) NOT NULL,
    flow_run_id         VARCHAR(36) NOT NULL,
    node_instance_id    VARCHAR(36) NOT NULL,
    node_key            TEXT NOT NULL,
    event_kind_id       SMALLINT NOT NULL,
    org_id              VARCHAR(36) NOT NULL,
    actor_id            VARCHAR(36),
    occurred_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_evt_flow_run_events         PRIMARY KEY (id),
    CONSTRAINT fk_evt_flow_run_events_run     FOREIGN KEY (flow_run_id)      REFERENCES "01_catalog"."12_fct_flow_runs"(id) ON DELETE CASCADE,
    CONSTRAINT fk_evt_flow_run_events_node    FOREIGN KEY (node_instance_id) REFERENCES "01_catalog"."21_dtl_flow_nodes"(id) ON DELETE CASCADE,
    CONSTRAINT fk_evt_flow_run_events_kind    FOREIGN KEY (event_kind_id)    REFERENCES "01_catalog"."09_dim_flow_run_event_kind"(id),
    CONSTRAINT fk_evt_flow_run_events_org     FOREIGN KEY (org_id)           REFERENCES "03_iam"."10_fct_orgs"(id)
);
COMMENT ON TABLE "01_catalog"."60_evt_flow_run_events" IS 'Append-only per-node execution events. One row per node state transition.';

CREATE INDEX IF NOT EXISTS idx_evt_flow_run_events_run_node  ON "01_catalog"."60_evt_flow_run_events"(flow_run_id, node_instance_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_evt_flow_run_events_occurred  ON "01_catalog"."60_evt_flow_run_events"(occurred_at DESC);

-- -------------------------------------------------------------------
-- Views
-- -------------------------------------------------------------------

CREATE OR REPLACE VIEW "01_catalog".v_flow_runs AS
SELECT
    r.id,
    r.flow_version_id,
    r.org_id,
    r.workspace_id,
    r.started_by_user_id,
    r.status_id,
    s.code  AS status,
    s.label AS status_label,
    r.started_at,
    r.finished_at,
    r.is_active,
    r.is_test,
    r.deleted_at,
    r.created_by,
    r.updated_by,
    r.created_at,
    r.updated_at
FROM "01_catalog"."12_fct_flow_runs" r
LEFT JOIN "01_catalog"."07_dim_flow_run_status" s ON r.status_id = s.id;

COMMENT ON VIEW "01_catalog".v_flow_runs IS 'Read model: flow runs with resolved status code.';

CREATE OR REPLACE VIEW "01_catalog".v_catalog_flow_run_node_status AS
SELECT DISTINCT ON (e.flow_run_id, e.node_instance_id)
    e.flow_run_id,
    e.node_instance_id,
    e.node_key,
    k.code AS event_kind,
    e.occurred_at
FROM "01_catalog"."60_evt_flow_run_events" e
LEFT JOIN "01_catalog"."09_dim_flow_run_event_kind" k ON e.event_kind_id = k.id
ORDER BY e.flow_run_id, e.node_instance_id, e.occurred_at DESC;

COMMENT ON VIEW "01_catalog".v_catalog_flow_run_node_status IS 'Latest event per node instance in a flow run (DISTINCT ON by occurred_at DESC).';

CREATE OR REPLACE VIEW "01_catalog".v_catalog_flow_run_edge_traversal AS
SELECT
    e.id                AS edge_id,
    e.flow_version_id,
    e.from_node_id,
    e.to_node_id,
    e.edge_kind_id,
    r.id                AS flow_run_id,
    (fn.event_kind IN ('success', 'failure_handled')
     AND tn.node_instance_id IS NOT NULL) AS traversed,
    fn.occurred_at      AS from_node_event_time,
    tn.occurred_at      AS to_node_event_time
FROM "01_catalog"."22_dtl_flow_edges" e
JOIN  "01_catalog"."11_fct_flow_versions" v ON e.flow_version_id = v.id
JOIN  "01_catalog"."12_fct_flow_runs"      r ON r.flow_version_id = v.id
LEFT JOIN LATERAL (
    SELECT ev.node_instance_id, k.code AS event_kind, ev.occurred_at
    FROM  "01_catalog"."60_evt_flow_run_events" ev
    LEFT JOIN "01_catalog"."09_dim_flow_run_event_kind" k ON ev.event_kind_id = k.id
    WHERE ev.flow_run_id = r.id AND ev.node_instance_id = e.from_node_id
    ORDER BY ev.occurred_at DESC
    LIMIT 1
) fn ON true
LEFT JOIN LATERAL (
    SELECT ev.node_instance_id, k.code AS event_kind, ev.occurred_at
    FROM  "01_catalog"."60_evt_flow_run_events" ev
    LEFT JOIN "01_catalog"."09_dim_flow_run_event_kind" k ON ev.event_kind_id = k.id
    WHERE ev.flow_run_id = r.id AND ev.node_instance_id = e.to_node_id
    ORDER BY ev.occurred_at DESC
    LIMIT 1
) tn ON true;

COMMENT ON VIEW "01_catalog".v_catalog_flow_run_edge_traversal IS 'Edge traversal per run: traversed=true when from_node reached success/failure_handled AND to_node emitted any event.';

-- DOWN ====

DROP VIEW IF EXISTS "01_catalog".v_catalog_flow_run_edge_traversal;
DROP VIEW IF EXISTS "01_catalog".v_catalog_flow_run_node_status;
DROP VIEW IF EXISTS "01_catalog".v_flow_runs;

DROP INDEX IF EXISTS "01_catalog".idx_evt_flow_run_events_occurred;
DROP INDEX IF EXISTS "01_catalog".idx_evt_flow_run_events_run_node;
DROP TABLE IF EXISTS "01_catalog"."60_evt_flow_run_events";

DROP INDEX IF EXISTS "01_catalog".idx_fct_flow_runs_org_started;
DROP INDEX IF EXISTS "01_catalog".idx_fct_flow_runs_version_started;
DROP TABLE IF EXISTS "01_catalog"."12_fct_flow_runs";

DROP TABLE IF EXISTS "01_catalog"."09_dim_flow_run_event_kind";
DROP TABLE IF EXISTS "01_catalog"."08_dim_trace_node_status";
DROP TABLE IF EXISTS "01_catalog"."07_dim_flow_run_status";
