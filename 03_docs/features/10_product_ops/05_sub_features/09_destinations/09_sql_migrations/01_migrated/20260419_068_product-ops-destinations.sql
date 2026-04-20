-- UP ====

-- product_ops.destinations — outbound webhooks fan-out (Segment-style CDP).
--
-- Operators register destinations with:
--   - kind: 'webhook' (POST JSON to URL) | 'slack' (POST to Slack incoming webhook)
--   - filter_rule: which events trigger this destination (eligibility AST)
--   - secret: optional HMAC-SHA256 signing key (signature in X-TennetCTL-Signature header)
--   - retry_policy: {max_attempts, backoff_ms} (best-effort; v1 = sync, no retries)
--
-- Fan-out: at the end of POST /v1/track, after audit summary, the service
-- iterates active destinations whose filter matches each event and POSTs
-- asynchronously (httpx.AsyncClient, fire-and-forget on a 2-second timeout).
-- Every attempt logs an evt_destination_deliveries row (success / failure / timeout).

CREATE TABLE "10_product_ops"."10_fct_destinations" (
    id              VARCHAR(36) NOT NULL,
    slug            TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    kind            TEXT NOT NULL,             -- 'webhook' | 'slack' | 'custom'
    url             TEXT NOT NULL,
    secret          TEXT,                      -- HMAC signing key (operator-supplied)
    headers         JSONB NOT NULL DEFAULT '{}'::jsonb,  -- extra headers to send
    -- Which events go to this destination. Empty = all events.
    filter_rule     JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Retry policy (best-effort spec; v1 service does sync no-retry)
    retry_policy    JSONB NOT NULL DEFAULT '{"max_attempts":1,"backoff_ms":1000}'::jsonb,
    -- Operational
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fct_destinations PRIMARY KEY (id),
    CONSTRAINT uq_fct_destinations_workspace_slug UNIQUE (workspace_id, slug),
    CONSTRAINT chk_fct_destinations_kind CHECK (kind IN ('webhook','slack','custom'))
);

CREATE INDEX idx_fct_destinations_workspace_active
    ON "10_product_ops"."10_fct_destinations" (workspace_id, is_active)
    WHERE deleted_at IS NULL;

COMMENT ON TABLE "10_product_ops"."10_fct_destinations" IS 'Outbound destinations for CDP fan-out. filter_rule selects which events get sent; secret signs the request via HMAC-SHA256; deliveries logged in evt_destination_deliveries.';

-- ── Delivery log (append-only) ────────────────────────────────────

CREATE TABLE "10_product_ops"."60_evt_destination_deliveries" (
    id              VARCHAR(36) NOT NULL,
    destination_id  VARCHAR(36) NOT NULL,
    -- Source event that triggered the delivery (nullable for batch/replay deliveries)
    event_id        VARCHAR(36),
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    -- Outcome
    status          TEXT NOT NULL,             -- 'pending' | 'success' | 'failure' | 'timeout' | 'rejected_filter'
    attempt         INTEGER NOT NULL DEFAULT 1,
    response_code   INTEGER,
    response_body   TEXT,                      -- truncated to 1KB
    duration_ms     INTEGER,
    error_message   TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_evt_destination_deliveries PRIMARY KEY (id),
    CONSTRAINT fk_evt_destination_deliveries_destination
        FOREIGN KEY (destination_id) REFERENCES "10_product_ops"."10_fct_destinations"(id),
    CONSTRAINT chk_evt_destination_deliveries_status
        CHECK (status IN ('pending','success','failure','timeout','rejected_filter'))
);

CREATE INDEX idx_evt_destination_deliveries_dest_occurred
    ON "10_product_ops"."60_evt_destination_deliveries" (destination_id, occurred_at DESC);
CREATE INDEX idx_evt_destination_deliveries_status
    ON "10_product_ops"."60_evt_destination_deliveries" (status, occurred_at DESC);

COMMENT ON TABLE "10_product_ops"."60_evt_destination_deliveries" IS 'Append-only delivery log. response_body truncated to 1KB. status taxonomy enables fan-out funnel analysis (sent vs delivered vs filtered).';

-- ── Read view ─────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "10_product_ops".v_destinations AS
SELECT
    d.id,
    d.slug,
    d.name,
    d.description,
    d.org_id,
    d.workspace_id,
    d.kind,
    d.url,
    -- Never expose the secret in the read view
    (d.secret IS NOT NULL) AS has_secret,
    d.headers,
    d.filter_rule,
    d.retry_policy,
    d.is_active,
    (d.deleted_at IS NOT NULL) AS is_deleted,
    d.deleted_at,
    d.created_by,
    d.created_at,
    d.updated_at,
    -- Pre-aggregated stats (last 30 days)
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_destination_deliveries" dd
       WHERE dd.destination_id = d.id
         AND dd.occurred_at >= CURRENT_DATE - INTERVAL '30 day') AS delivery_count_30d,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_destination_deliveries" dd
       WHERE dd.destination_id = d.id AND dd.status = 'success'
         AND dd.occurred_at >= CURRENT_DATE - INTERVAL '30 day') AS success_count_30d,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_destination_deliveries" dd
       WHERE dd.destination_id = d.id AND dd.status IN ('failure','timeout')
         AND dd.occurred_at >= CURRENT_DATE - INTERVAL '30 day') AS failure_count_30d
FROM "10_product_ops"."10_fct_destinations" d;

COMMENT ON VIEW "10_product_ops".v_destinations IS 'Destination read view. Secret never exposed; only has_secret boolean. Pre-aggregates last-30d delivery counts for at-a-glance health.';

-- DOWN ====

DROP VIEW  IF EXISTS "10_product_ops".v_destinations;
DROP TABLE IF EXISTS "10_product_ops"."60_evt_destination_deliveries";
DROP TABLE IF EXISTS "10_product_ops"."10_fct_destinations";
