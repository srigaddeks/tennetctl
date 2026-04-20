-- UP ====

-- Catalog Canvas: trace node status dimension and flow run event projections.
--
-- Purpose: Support the read-side canvas renderer with per-node + per-edge status
-- derived from the evt_catalog_flow_run_events table. No write paths; views only.

-- ── Dimension: Trace Node Status ────────────────────────────────────

CREATE TABLE "01_catalog"."05_dim_trace_node_status" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_trace_node_status PRIMARY KEY (id),
    CONSTRAINT uq_dim_trace_node_status_code UNIQUE (code)
);

COMMENT ON TABLE  "01_catalog"."05_dim_trace_node_status" IS 'Node execution status in a flow run trace. Seeded: pending=1, running=2, success=3, failure=4, skipped=5, timed_out=6.';
COMMENT ON COLUMN "01_catalog"."05_dim_trace_node_status".id IS 'SMALLINT PK (static, seeded).';
COMMENT ON COLUMN "01_catalog"."05_dim_trace_node_status".code IS 'Identifier: pending, running, success, failure, skipped, timed_out.';
COMMENT ON COLUMN "01_catalog"."05_dim_trace_node_status".label IS 'Human-readable label.';
COMMENT ON COLUMN "01_catalog"."05_dim_trace_node_status".description IS 'What this status means.';
COMMENT ON COLUMN "01_catalog"."05_dim_trace_node_status".deprecated_at IS 'NULL for active statuses.';

-- ── View: Flow Run Node Status ──────────────────────────────────────

CREATE VIEW "01_catalog"."v_catalog_flow_run_node_status" AS
SELECT DISTINCT ON (flow_run_id, node_instance_id)
    flow_run_id,
    node_instance_id,
    node_key,
    event_kind,
    occurred_at
FROM "01_catalog"."evt_catalog_flow_run_events"
ORDER BY flow_run_id, node_instance_id, occurred_at DESC;

COMMENT ON VIEW "01_catalog"."v_catalog_flow_run_node_status" IS 'Latest status per node instance in a flow run. DISTINCT ON orders by time DESC to get the terminal event.';

-- ── View: Flow Run Edge Traversal ──────────────────────────────────

CREATE VIEW "01_catalog"."v_catalog_flow_run_edge_traversal" AS
SELECT
    e.id AS edge_id,
    e.flow_version_id,
    e.from_node_id,
    e.to_node_id,
    e.edge_kind_id,
    r.flow_run_id,
    (from_node.event_kind IN ('success', 'failure_handled')
     AND to_node.node_instance_id IS NOT NULL) AS traversed,
    from_node.occurred_at AS from_node_event_time,
    to_node.occurred_at AS to_node_event_time
FROM "01_catalog"."dtl_catalog_flow_edges" e
JOIN "01_catalog"."fct_catalog_flow_versions" v ON e.flow_version_id = v.id
JOIN "01_catalog"."fct_catalog_flow_runs" r ON r.version_id = v.id
LEFT JOIN LATERAL (
    SELECT DISTINCT ON (node_instance_id)
        node_instance_id, event_kind, occurred_at
    FROM "01_catalog"."evt_catalog_flow_run_events"
    WHERE flow_run_id = r.id AND node_instance_id = e.from_node_id
    ORDER BY node_instance_id, occurred_at DESC
) from_node ON true
LEFT JOIN LATERAL (
    SELECT DISTINCT ON (node_instance_id)
        node_instance_id, event_kind, occurred_at
    FROM "01_catalog"."evt_catalog_flow_run_events"
    WHERE flow_run_id = r.id AND node_instance_id = e.to_node_id
) to_node ON true;

COMMENT ON VIEW "01_catalog"."v_catalog_flow_run_edge_traversal" IS 'Edge traversal status: traversed=true when from_node reached success/failure_handled AND to_node has any event. Used for trace overlay on canvas.';

-- DOWN ====

DROP VIEW IF EXISTS "01_catalog"."v_catalog_flow_run_edge_traversal" CASCADE;
DROP VIEW IF EXISTS "01_catalog"."v_catalog_flow_run_node_status" CASCADE;
DROP TABLE IF EXISTS "01_catalog"."05_dim_trace_node_status" CASCADE;
