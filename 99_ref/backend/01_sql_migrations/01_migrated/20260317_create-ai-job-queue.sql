-- ============================================================
-- 20260317_create-ai-job-queue.sql
-- AI Background Job Queue — per-agent queues, rate limiting, batch execution
-- ============================================================

BEGIN;

-- ============================================================
-- DIMENSIONS (extend 20_ai)
-- ============================================================

CREATE TABLE "20_ai"."11_dim_job_statuses" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."11_dim_job_statuses" (code, name, is_terminal) VALUES
    ('queued',     'Queued',     FALSE),
    ('running',    'Running',    FALSE),
    ('completed',  'Completed',  TRUE),
    ('failed',     'Failed',     TRUE),
    ('cancelled',  'Cancelled',  TRUE),
    ('rate_limited','Rate Limited', FALSE),
    ('retrying',   'Retrying',   FALSE);


CREATE TABLE "20_ai"."12_dim_job_priorities" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    sort_order  INT          NOT NULL DEFAULT 50,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."12_dim_job_priorities" (code, name, sort_order) VALUES
    ('critical', 'Critical', 10),
    ('high',     'High',     20),
    ('normal',   'Normal',   50),
    ('low',      'Low',      80),
    ('batch',    'Batch',    100);


-- ============================================================
-- RATE LIMIT CONFIGS (per agent type + per org)
-- Controls how many tokens/minute, jobs/minute this agent type can use
-- ============================================================

CREATE TABLE "20_ai"."44_fct_agent_rate_limits" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    agent_type_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    org_id              UUID,
    -- Per-minute limits
    max_requests_per_minute  INT     NOT NULL DEFAULT 60,
    max_tokens_per_minute    BIGINT  NOT NULL DEFAULT 90000,
    -- Concurrent execution limits
    max_concurrent_jobs      INT     NOT NULL DEFAULT 5,
    -- Batch config
    batch_size               INT     NOT NULL DEFAULT 10,
    batch_interval_seconds   INT     NOT NULL DEFAULT 60,
    -- Cool-down after hitting limit
    cooldown_seconds         INT     NOT NULL DEFAULT 30,
    is_active               BOOLEAN  NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_rate_limits_unique ON "20_ai"."44_fct_agent_rate_limits"(agent_type_code, COALESCE(org_id::text, ''));
CREATE INDEX idx_rate_limits_tenant ON "20_ai"."44_fct_agent_rate_limits"(tenant_key);

-- Default global rate limits per agent type (org_id = NULL = global default)
INSERT INTO "20_ai"."44_fct_agent_rate_limits"
    (id, tenant_key, agent_type_code, org_id, max_requests_per_minute, max_tokens_per_minute, max_concurrent_jobs, batch_size, batch_interval_seconds)
VALUES
    (gen_random_uuid(), '__platform__', 'copilot',          NULL, 60, 90000,  5, 10, 60),
    (gen_random_uuid(), '__platform__', 'supervisor',        NULL, 20, 60000,  3, 5,  60),
    (gen_random_uuid(), '__platform__', 'grc_assistant',     NULL, 30, 60000,  3, 5,  60),
    (gen_random_uuid(), '__platform__', 'signal_generator',  NULL, 20, 40000,  2, 5,  60),
    (gen_random_uuid(), '__platform__', 'framework_agent',   NULL, 30, 60000,  3, 10, 60),
    (gen_random_uuid(), '__platform__', 'risk_agent',        NULL, 30, 60000,  3, 10, 60),
    (gen_random_uuid(), '__platform__', 'task_agent',        NULL, 30, 60000,  3, 10, 60),
    (gen_random_uuid(), '__platform__', 'signal_agent',      NULL, 20, 40000,  2, 5,  60),
    (gen_random_uuid(), '__platform__', 'connector_agent',   NULL, 20, 40000,  2, 5,  60),
    (gen_random_uuid(), '__platform__', 'user_agent',        NULL, 20, 40000,  2, 5,  60),
    (gen_random_uuid(), '__platform__', 'role_agent',        NULL, 20, 40000,  2, 5,  60);


-- ============================================================
-- JOB QUEUE
-- The core per-agent background job queue
-- ============================================================

CREATE TABLE "20_ai"."45_fct_job_queue" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    user_id             UUID         NOT NULL,
    org_id              UUID,
    workspace_id        UUID,
    agent_type_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    priority_code       VARCHAR(50)  NOT NULL REFERENCES "20_ai"."12_dim_job_priorities"(code) DEFAULT 'normal',
    status_code         VARCHAR(50)  NOT NULL REFERENCES "20_ai"."11_dim_job_statuses"(code) DEFAULT 'queued',
    -- Job payload
    job_type            VARCHAR(200) NOT NULL,   -- e.g. "run_agent", "batch_signal_analysis"
    input_json          JSONB        NOT NULL DEFAULT '{}',
    -- Result
    output_json         JSONB,
    error_message       TEXT,
    -- Scheduling
    scheduled_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    -- Rate limit tracking
    estimated_tokens    INT          NOT NULL DEFAULT 0,
    actual_tokens       INT,
    -- Retry
    max_retries         INT          NOT NULL DEFAULT 3,
    retry_count         INT          NOT NULL DEFAULT 0,
    next_retry_at       TIMESTAMPTZ,
    -- Related entities
    conversation_id     UUID         REFERENCES "20_ai"."20_fct_conversations"(id),
    agent_run_id        UUID         REFERENCES "20_ai"."24_fct_agent_runs"(id),
    -- Batch grouping
    batch_id            UUID,
    -- Metadata
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Core queue index: pick next job to run (ordered by priority + scheduled_at)
CREATE INDEX idx_job_queue_next ON "20_ai"."45_fct_job_queue"
    (agent_type_code, status_code, priority_code, scheduled_at)
    WHERE status_code IN ('queued', 'rate_limited', 'retrying');

CREATE INDEX idx_job_queue_user      ON "20_ai"."45_fct_job_queue"(user_id);
CREATE INDEX idx_job_queue_tenant    ON "20_ai"."45_fct_job_queue"(tenant_key);
CREATE INDEX idx_job_queue_batch     ON "20_ai"."45_fct_job_queue"(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX idx_job_queue_conv      ON "20_ai"."45_fct_job_queue"(conversation_id) WHERE conversation_id IS NOT NULL;
CREATE INDEX idx_job_queue_scheduled ON "20_ai"."45_fct_job_queue"(scheduled_at) WHERE status_code NOT IN ('completed','failed','cancelled');
CREATE INDEX idx_job_queue_updated   ON "20_ai"."45_fct_job_queue"(updated_at DESC);


-- ============================================================
-- RATE LIMIT SLIDING WINDOW LEDGER
-- Tracks tokens used per agent_type per minute window for enforcement
-- ============================================================

CREATE TABLE "20_ai"."46_trx_rate_limit_windows" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID,
    agent_type_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    window_start        TIMESTAMPTZ  NOT NULL,   -- truncated to minute
    requests_count      INT          NOT NULL DEFAULT 0,
    tokens_count        BIGINT       NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_rate_window_unique ON "20_ai"."46_trx_rate_limit_windows"
    (tenant_key, COALESCE(org_id::text,''), agent_type_code, window_start);
CREATE INDEX idx_rate_window_agent_time ON "20_ai"."46_trx_rate_limit_windows"(agent_type_code, window_start DESC);


-- ============================================================
-- BATCH GROUPS
-- Group related jobs into a named batch for tracking
-- ============================================================

CREATE TABLE "20_ai"."47_fct_job_batches" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    user_id             UUID         NOT NULL,
    org_id              UUID,
    agent_type_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    name                VARCHAR(500),
    description         TEXT,
    total_jobs          INT          NOT NULL DEFAULT 0,
    completed_jobs      INT          NOT NULL DEFAULT 0,
    failed_jobs         INT          NOT NULL DEFAULT 0,
    estimated_tokens    BIGINT       NOT NULL DEFAULT 0,
    actual_tokens       BIGINT       NOT NULL DEFAULT 0,
    status_code         VARCHAR(50)  NOT NULL DEFAULT 'queued',
    scheduled_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_job_batches_user     ON "20_ai"."47_fct_job_batches"(user_id);
CREATE INDEX idx_job_batches_tenant   ON "20_ai"."47_fct_job_batches"(tenant_key);
CREATE INDEX idx_job_batches_status   ON "20_ai"."47_fct_job_batches"(status_code);
CREATE INDEX idx_job_batches_agent    ON "20_ai"."47_fct_job_batches"(agent_type_code);


-- ============================================================
-- VIEWS — Per-agent queue dashboards
-- ============================================================

-- Overall queue depth per agent type
CREATE VIEW "20_ai"."65_vw_queue_depth" AS
SELECT
    jq.agent_type_code,
    at.name                         AS agent_type_name,
    jq.tenant_key,
    jq.status_code,
    js.name                         AS status_name,
    jq.priority_code,
    COUNT(*)                        AS job_count,
    SUM(jq.estimated_tokens)        AS estimated_tokens,
    MIN(jq.scheduled_at)            AS oldest_job_at,
    MAX(jq.created_at)              AS newest_job_at
FROM "20_ai"."45_fct_job_queue" jq
LEFT JOIN "20_ai"."02_dim_agent_types" at ON at.code = jq.agent_type_code
LEFT JOIN "20_ai"."11_dim_job_statuses" js ON js.code = jq.status_code
GROUP BY jq.agent_type_code, at.name, jq.tenant_key, jq.status_code, js.name, jq.priority_code;


-- Active rate limit windows (last 5 minutes)
CREATE VIEW "20_ai"."66_vw_rate_limit_status" AS
SELECT
    w.tenant_key,
    w.org_id,
    w.agent_type_code,
    at.name                                 AS agent_type_name,
    w.window_start,
    w.requests_count,
    w.tokens_count,
    rl.max_requests_per_minute,
    rl.max_tokens_per_minute,
    rl.max_concurrent_jobs,
    ROUND(w.requests_count * 100.0 / NULLIF(rl.max_requests_per_minute, 0), 1) AS request_utilization_pct,
    ROUND(w.tokens_count   * 100.0 / NULLIF(rl.max_tokens_per_minute, 0), 1)   AS token_utilization_pct,
    CASE WHEN w.requests_count >= rl.max_requests_per_minute
              OR w.tokens_count >= rl.max_tokens_per_minute
         THEN TRUE ELSE FALSE
    END                                     AS is_at_limit
FROM "20_ai"."46_trx_rate_limit_windows" w
LEFT JOIN "20_ai"."02_dim_agent_types" at ON at.code = w.agent_type_code
LEFT JOIN "20_ai"."44_fct_agent_rate_limits" rl
       ON rl.agent_type_code = w.agent_type_code
      AND COALESCE(rl.org_id::text, '') = COALESCE(w.org_id::text, '')
WHERE w.window_start >= NOW() - INTERVAL '5 minutes';


-- Per-user queue view: all my jobs across agent types
CREATE VIEW "20_ai"."67_vw_user_job_queue" AS
SELECT
    jq.id,
    jq.user_id,
    jq.tenant_key,
    jq.org_id,
    jq.agent_type_code,
    at.name             AS agent_type_name,
    jq.priority_code,
    jp.name             AS priority_name,
    jq.status_code,
    js.name             AS status_name,
    jq.job_type,
    jq.estimated_tokens,
    jq.actual_tokens,
    jq.retry_count,
    jq.max_retries,
    jq.scheduled_at,
    jq.started_at,
    jq.completed_at,
    jq.batch_id,
    jq.conversation_id,
    jq.error_message,
    jq.created_at,
    jq.updated_at,
    CASE
        WHEN jq.status_code IN ('completed','failed','cancelled') THEN NULL
        WHEN jq.scheduled_at <= NOW() THEN 0
        ELSE EXTRACT(EPOCH FROM (jq.scheduled_at - NOW()))::INT
    END                 AS seconds_until_start,
    -- Position in queue for this agent type (among queued/rate_limited/retrying)
    ROW_NUMBER() OVER (
        PARTITION BY jq.agent_type_code, jq.status_code
        ORDER BY jq.priority_code, jq.scheduled_at
    )                   AS queue_position
FROM "20_ai"."45_fct_job_queue" jq
LEFT JOIN "20_ai"."02_dim_agent_types" at ON at.code = jq.agent_type_code
LEFT JOIN "20_ai"."12_dim_job_priorities" jp ON jp.code = jq.priority_code
LEFT JOIN "20_ai"."11_dim_job_statuses" js ON js.code = jq.status_code;


-- Batch progress view
CREATE VIEW "20_ai"."68_vw_batch_progress" AS
SELECT
    b.id,
    b.tenant_key,
    b.user_id,
    b.org_id,
    b.agent_type_code,
    at.name                             AS agent_type_name,
    b.name,
    b.description,
    b.total_jobs,
    b.completed_jobs,
    b.failed_jobs,
    (b.total_jobs - b.completed_jobs - b.failed_jobs) AS pending_jobs,
    b.estimated_tokens,
    b.actual_tokens,
    b.status_code,
    b.scheduled_at,
    b.started_at,
    b.completed_at,
    b.created_at,
    ROUND(b.completed_jobs * 100.0 / NULLIF(b.total_jobs, 0), 1) AS completion_pct,
    EXTRACT(EPOCH FROM (COALESCE(b.completed_at, NOW()) - b.started_at))::INT AS elapsed_seconds
FROM "20_ai"."47_fct_job_batches" b
LEFT JOIN "20_ai"."02_dim_agent_types" at ON at.code = b.agent_type_code;


-- Admin view: full queue across all tenants, ordered for processing
CREATE VIEW "20_ai"."69_vw_queue_processing_order" AS
SELECT
    jq.id,
    jq.tenant_key,
    jq.user_id,
    jq.org_id,
    jq.agent_type_code,
    jq.priority_code,
    jp.sort_order                       AS priority_sort,
    jq.status_code,
    jq.job_type,
    jq.estimated_tokens,
    jq.scheduled_at,
    jq.retry_count,
    jq.batch_id,
    rl.max_concurrent_jobs,
    -- Running count for this agent type
    (SELECT COUNT(*) FROM "20_ai"."45_fct_job_queue" jq2
     WHERE jq2.agent_type_code = jq.agent_type_code
       AND jq2.status_code = 'running')  AS currently_running,
    -- Is rate limit window full?
    EXISTS (
        SELECT 1 FROM "20_ai"."66_vw_rate_limit_status" rls
        WHERE rls.agent_type_code = jq.agent_type_code
          AND rls.is_at_limit = TRUE
          AND rls.window_start >= DATE_TRUNC('minute', NOW())
    )                                   AS is_rate_limited
FROM "20_ai"."45_fct_job_queue" jq
LEFT JOIN "20_ai"."12_dim_job_priorities" jp ON jp.code = jq.priority_code
LEFT JOIN "20_ai"."44_fct_agent_rate_limits" rl
       ON rl.agent_type_code = jq.agent_type_code
      AND rl.org_id IS NULL
WHERE jq.status_code IN ('queued', 'rate_limited', 'retrying')
  AND jq.scheduled_at <= NOW()
ORDER BY jp.sort_order ASC, jq.scheduled_at ASC;

COMMIT;
