-- ===========================================================================
-- Migration: Create agent sandbox schema
-- Date: 2026-03-22
-- Description: Agent Sandbox — build, test, and deploy autonomous AI agents
--              from the UI with all agent code stored in the database.
--
--   Chain: Tools → Agent Definitions → Test Scenarios → Agent Runs → Promotion
--
--   Agents are declarative Python graphs stored in DB EAV, executed via a
--   controlled interpreter with budget enforcement, approval gates, and
--   full execution trace recording.
--
-- Row-Level Security (RLS) notes:
--   All fact tables carry tenant_key.  If RLS is enabled in a future phase,
--   policies should filter by tenant_key using a current_setting session var.
-- ===========================================================================

-- Schema created in 20260313_a_create-all-schemas.sql

-- ─────────────────────────────────────────────────────────────────────────────
-- SHARED TRIGGER FUNCTION — auto-update updated_at
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION "25_agent_sandbox".fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ═══════════════════════════════════════════════════════════════════════════════
-- DIMENSION TABLES (02-06)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 02_dim_agent_statuses — agent lifecycle states
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."02_dim_agent_statuses" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_02_dim_agent_statuses       PRIMARY KEY (id),
    CONSTRAINT uq_02_dim_agent_statuses_code  UNIQUE (code)
);

INSERT INTO "25_agent_sandbox"."02_dim_agent_statuses" (code, name, description, sort_order, is_terminal) VALUES
    ('draft',       'Draft',       'Agent is being developed',                     1, FALSE),
    ('testing',     'Testing',     'Agent is being tested against scenarios',       2, FALSE),
    ('validated',   'Validated',   'Agent has passed all test scenarios',           3, FALSE),
    ('published',   'Published',   'Agent is available for production use',         4, FALSE),
    ('deprecated',  'Deprecated',  'Agent is no longer recommended',               5, FALSE),
    ('archived',    'Archived',    'Agent is archived and read-only',              6, TRUE)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 03_dim_tool_types — types of tools agents can use
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."03_dim_tool_types" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_03_dim_tool_types       PRIMARY KEY (id),
    CONSTRAINT uq_03_dim_tool_types_code  UNIQUE (code)
);

INSERT INTO "25_agent_sandbox"."03_dim_tool_types" (code, name, description, sort_order) VALUES
    ('mcp_server',       'MCP Server',        'Model Context Protocol server endpoint',               1),
    ('api_endpoint',     'API Endpoint',      'HTTP API endpoint with JSON schema',                   2),
    ('python_function',  'Python Function',   'Custom Python function executed in sandbox',            3),
    ('sandbox_signal',   'Sandbox Signal',    'Existing sandbox signal used as a tool',                4),
    ('db_query',         'Database Query',    'Read-only database query with parameterized input',     5)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 04_dim_scenario_types — test scenario categories
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."04_dim_scenario_types" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_04_dim_scenario_types       PRIMARY KEY (id),
    CONSTRAINT uq_04_dim_scenario_types_code  UNIQUE (code)
);

INSERT INTO "25_agent_sandbox"."04_dim_scenario_types" (code, name, description, sort_order) VALUES
    ('single_turn',   'Single Turn',   'Single input/output test case',                  1),
    ('multi_turn',    'Multi Turn',    'Multi-step conversation test',                   2),
    ('adversarial',   'Adversarial',   'Edge cases and adversarial inputs',              3),
    ('regression',    'Regression',    'Regression tests for known-good behavior',       4)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 05_dim_evaluation_methods — how test results are judged
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."05_dim_evaluation_methods" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_05_dim_evaluation_methods       PRIMARY KEY (id),
    CONSTRAINT uq_05_dim_evaluation_methods_code  UNIQUE (code)
);

INSERT INTO "25_agent_sandbox"."05_dim_evaluation_methods" (code, name, description, sort_order) VALUES
    ('deterministic',   'Deterministic',   'Exact match or JSON path assertions',                 1),
    ('llm_judge',       'LLM Judge',       'LLM evaluates output against criteria',                2),
    ('similarity',      'Similarity',      'Cosine similarity against reference output',           3),
    ('regex',           'Regex',           'Regex pattern matching on output',                     4),
    ('custom_python',   'Custom Python',   'User-provided evaluation function in sandbox',         5)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 06_dim_execution_statuses — run lifecycle states
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."06_dim_execution_statuses" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_06_dim_execution_statuses       PRIMARY KEY (id),
    CONSTRAINT uq_06_dim_execution_statuses_code  UNIQUE (code)
);

INSERT INTO "25_agent_sandbox"."06_dim_execution_statuses" (code, name, description, sort_order, is_terminal) VALUES
    ('queued',              'Queued',              'Run is waiting to be picked up',          1, FALSE),
    ('running',             'Running',             'Run is actively executing',               2, FALSE),
    ('paused',              'Paused',              'Run is paused (checkpoint saved)',         3, FALSE),
    ('awaiting_approval',   'Awaiting Approval',   'Run needs human approval to continue',    4, FALSE),
    ('completed',           'Completed',           'Run finished successfully',               5, TRUE),
    ('failed',              'Failed',              'Run failed with an error',                6, TRUE),
    ('timeout',             'Timeout',             'Run exceeded time budget',                7, TRUE),
    ('cancelled',           'Cancelled',           'Run was cancelled by user',               8, TRUE)
ON CONFLICT (code) DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════════════
-- FACT TABLES (20-24)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 20_fct_agents — core agent definitions (versioned, org-scoped)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."20_fct_agents" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    workspace_id        UUID,
    agent_code          VARCHAR(100) NOT NULL,
    version_number      INT          NOT NULL DEFAULT 1,
    agent_status_code   VARCHAR(50)  NOT NULL DEFAULT 'draft',
    -- Structural fields (not EAV)
    graph_type          VARCHAR(50)  NOT NULL DEFAULT 'sequential',
    llm_model_id        VARCHAR(200),
    temperature         NUMERIC(3,2) NOT NULL DEFAULT 0.30,
    max_iterations      INT          NOT NULL DEFAULT 20,
    max_tokens_budget   INT          NOT NULL DEFAULT 50000,
    max_tool_calls      INT          NOT NULL DEFAULT 100,
    max_duration_ms     INT          NOT NULL DEFAULT 300000,
    max_cost_usd        NUMERIC(10,6) NOT NULL DEFAULT 1.000000,
    requires_approval   BOOLEAN      NOT NULL DEFAULT FALSE,
    python_hash         VARCHAR(64),
    -- Standard columns
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID,
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID,

    CONSTRAINT pk_20_fct_agents           PRIMARY KEY (id),
    CONSTRAINT uq_20_fct_agents_version   UNIQUE (org_id, agent_code, version_number),
    CONSTRAINT fk_20_fct_agents_status    FOREIGN KEY (agent_status_code)
        REFERENCES "25_agent_sandbox"."02_dim_agent_statuses" (code),
    CONSTRAINT ck_20_fct_agents_graph     CHECK (graph_type IN ('sequential', 'branching', 'cyclic')),
    CONSTRAINT ck_20_fct_agents_temp      CHECK (temperature >= 0.00 AND temperature <= 2.00),
    CONSTRAINT ck_20_fct_agents_iter      CHECK (max_iterations >= 1 AND max_iterations <= 1000),
    CONSTRAINT ck_20_fct_agents_tokens    CHECK (max_tokens_budget >= 100 AND max_tokens_budget <= 10000000),
    CONSTRAINT ck_20_fct_agents_tools     CHECK (max_tool_calls >= 0 AND max_tool_calls <= 10000),
    CONSTRAINT ck_20_fct_agents_dur       CHECK (max_duration_ms >= 1000 AND max_duration_ms <= 3600000),
    CONSTRAINT ck_20_fct_agents_cost      CHECK (max_cost_usd >= 0 AND max_cost_usd <= 1000),
    CONSTRAINT ck_20_fct_agents_del       CHECK (
        (is_deleted = FALSE) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_20_fct_agents_org
    ON "25_agent_sandbox"."20_fct_agents" (org_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS ix_20_fct_agents_org_ws
    ON "25_agent_sandbox"."20_fct_agents" (org_id, workspace_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS ix_20_fct_agents_code
    ON "25_agent_sandbox"."20_fct_agents" (org_id, agent_code) WHERE is_deleted = FALSE;

CREATE TRIGGER trg_20_fct_agents_updated_at
    BEFORE UPDATE ON "25_agent_sandbox"."20_fct_agents"
    FOR EACH ROW EXECUTE FUNCTION "25_agent_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 21_fct_agent_tools — registered tools (org-scoped, not versioned)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."21_fct_agent_tools" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    tool_code           VARCHAR(100) NOT NULL,
    tool_type_code      VARCHAR(50)  NOT NULL,
    -- Structural fields
    input_schema        JSONB        NOT NULL DEFAULT '{}',
    output_schema       JSONB        NOT NULL DEFAULT '{}',
    endpoint_url        TEXT,
    mcp_server_url      TEXT,
    python_source       TEXT,
    signal_id           UUID,
    requires_approval   BOOLEAN      NOT NULL DEFAULT FALSE,
    is_destructive      BOOLEAN      NOT NULL DEFAULT FALSE,
    timeout_ms          INT          NOT NULL DEFAULT 30000,
    -- Standard columns
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID,
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID,

    CONSTRAINT pk_21_fct_agent_tools          PRIMARY KEY (id),
    CONSTRAINT uq_21_fct_agent_tools_code     UNIQUE (org_id, tool_code),
    CONSTRAINT fk_21_fct_agent_tools_type     FOREIGN KEY (tool_type_code)
        REFERENCES "25_agent_sandbox"."03_dim_tool_types" (code),
    CONSTRAINT ck_21_fct_agent_tools_timeout  CHECK (timeout_ms >= 1000 AND timeout_ms <= 300000),
    CONSTRAINT ck_21_fct_agent_tools_del      CHECK (
        (is_deleted = FALSE) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_21_fct_agent_tools_org
    ON "25_agent_sandbox"."21_fct_agent_tools" (org_id) WHERE is_deleted = FALSE;

CREATE TRIGGER trg_21_fct_agent_tools_updated_at
    BEFORE UPDATE ON "25_agent_sandbox"."21_fct_agent_tools"
    FOR EACH ROW EXECUTE FUNCTION "25_agent_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 22_fct_test_scenarios — test scenario definitions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."22_fct_test_scenarios" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    workspace_id        UUID,
    scenario_code       VARCHAR(100) NOT NULL,
    scenario_type_code  VARCHAR(50)  NOT NULL DEFAULT 'single_turn',
    agent_id            UUID,
    -- Standard columns
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID,
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID,

    CONSTRAINT pk_22_fct_test_scenarios           PRIMARY KEY (id),
    CONSTRAINT uq_22_fct_test_scenarios_code      UNIQUE (org_id, scenario_code),
    CONSTRAINT fk_22_fct_test_scenarios_type      FOREIGN KEY (scenario_type_code)
        REFERENCES "25_agent_sandbox"."04_dim_scenario_types" (code),
    CONSTRAINT fk_22_fct_test_scenarios_agent     FOREIGN KEY (agent_id)
        REFERENCES "25_agent_sandbox"."20_fct_agents" (id),
    CONSTRAINT ck_22_fct_test_scenarios_del       CHECK (
        (is_deleted = FALSE) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_22_fct_test_scenarios_org
    ON "25_agent_sandbox"."22_fct_test_scenarios" (org_id) WHERE is_deleted = FALSE;

CREATE TRIGGER trg_22_fct_test_scenarios_updated_at
    BEFORE UPDATE ON "25_agent_sandbox"."22_fct_test_scenarios"
    FOR EACH ROW EXECUTE FUNCTION "25_agent_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 23_fct_test_cases — individual test cases within scenarios
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."23_fct_test_cases" (
    id                      UUID         NOT NULL DEFAULT gen_random_uuid(),
    scenario_id             UUID         NOT NULL,
    case_index              INT          NOT NULL DEFAULT 0,
    input_messages          JSONB        NOT NULL DEFAULT '[]',
    initial_context         JSONB        NOT NULL DEFAULT '{}',
    expected_behavior       JSONB        NOT NULL DEFAULT '{}',
    evaluation_method_code  VARCHAR(50)  NOT NULL DEFAULT 'deterministic',
    evaluation_config       JSONB        NOT NULL DEFAULT '{}',
    -- Standard columns
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID,

    CONSTRAINT pk_23_fct_test_cases          PRIMARY KEY (id),
    CONSTRAINT fk_23_fct_test_cases_scenario FOREIGN KEY (scenario_id)
        REFERENCES "25_agent_sandbox"."22_fct_test_scenarios" (id) ON DELETE CASCADE,
    CONSTRAINT fk_23_fct_test_cases_eval     FOREIGN KEY (evaluation_method_code)
        REFERENCES "25_agent_sandbox"."05_dim_evaluation_methods" (code)
);

CREATE INDEX IF NOT EXISTS ix_23_fct_test_cases_scenario
    ON "25_agent_sandbox"."23_fct_test_cases" (scenario_id);

CREATE TRIGGER trg_23_fct_test_cases_updated_at
    BEFORE UPDATE ON "25_agent_sandbox"."23_fct_test_cases"
    FOR EACH ROW EXECUTE FUNCTION "25_agent_sandbox".fn_update_timestamp();


-- ═══════════════════════════════════════════════════════════════════════════════
-- DETAIL / EAV TABLES (40-43)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 40_dtl_agent_properties — name, description, graph_source, system_prompt, tags
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."40_dtl_agent_properties" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    agent_id        UUID         NOT NULL,
    property_key    VARCHAR(80)  NOT NULL,
    property_value  TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_by      UUID,

    CONSTRAINT pk_40_dtl_agent_properties       PRIMARY KEY (id),
    CONSTRAINT uq_40_dtl_agent_properties_key   UNIQUE (agent_id, property_key),
    CONSTRAINT fk_40_dtl_agent_properties_agent FOREIGN KEY (agent_id)
        REFERENCES "25_agent_sandbox"."20_fct_agents" (id) ON DELETE CASCADE
);

CREATE TRIGGER trg_40_dtl_agent_properties_updated_at
    BEFORE UPDATE ON "25_agent_sandbox"."40_dtl_agent_properties"
    FOR EACH ROW EXECUTE FUNCTION "25_agent_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 41_dtl_tool_properties — name, description, config, docs
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."41_dtl_tool_properties" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    tool_id         UUID         NOT NULL,
    property_key    VARCHAR(80)  NOT NULL,
    property_value  TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_by      UUID,

    CONSTRAINT pk_41_dtl_tool_properties       PRIMARY KEY (id),
    CONSTRAINT uq_41_dtl_tool_properties_key   UNIQUE (tool_id, property_key),
    CONSTRAINT fk_41_dtl_tool_properties_tool  FOREIGN KEY (tool_id)
        REFERENCES "25_agent_sandbox"."21_fct_agent_tools" (id) ON DELETE CASCADE
);

CREATE TRIGGER trg_41_dtl_tool_properties_updated_at
    BEFORE UPDATE ON "25_agent_sandbox"."41_dtl_tool_properties"
    FOR EACH ROW EXECUTE FUNCTION "25_agent_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 42_dtl_scenario_properties — name, description, setup_instructions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."42_dtl_scenario_properties" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    scenario_id     UUID         NOT NULL,
    property_key    VARCHAR(80)  NOT NULL,
    property_value  TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_by      UUID,

    CONSTRAINT pk_42_dtl_scenario_properties         PRIMARY KEY (id),
    CONSTRAINT uq_42_dtl_scenario_properties_key     UNIQUE (scenario_id, property_key),
    CONSTRAINT fk_42_dtl_scenario_properties_scen    FOREIGN KEY (scenario_id)
        REFERENCES "25_agent_sandbox"."22_fct_test_scenarios" (id) ON DELETE CASCADE
);

CREATE TRIGGER trg_42_dtl_scenario_properties_updated_at
    BEFORE UPDATE ON "25_agent_sandbox"."42_dtl_scenario_properties"
    FOR EACH ROW EXECUTE FUNCTION "25_agent_sandbox".fn_update_timestamp();


-- ═══════════════════════════════════════════════════════════════════════════════
-- LINK TABLES (50)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 50_lnk_agent_tool_bindings — which tools an agent version can use
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."50_lnk_agent_tool_bindings" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    agent_id    UUID         NOT NULL,
    tool_id     UUID         NOT NULL,
    sort_order  INT          NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by  UUID,

    CONSTRAINT pk_50_lnk_agent_tool_bindings       PRIMARY KEY (id),
    CONSTRAINT uq_50_lnk_agent_tool_bindings_pair  UNIQUE (agent_id, tool_id),
    CONSTRAINT fk_50_lnk_agent_tool_agent          FOREIGN KEY (agent_id)
        REFERENCES "25_agent_sandbox"."20_fct_agents" (id) ON DELETE CASCADE,
    CONSTRAINT fk_50_lnk_agent_tool_tool           FOREIGN KEY (tool_id)
        REFERENCES "25_agent_sandbox"."21_fct_agent_tools" (id) ON DELETE CASCADE
);


-- ═══════════════════════════════════════════════════════════════════════════════
-- TRANSACTION TABLES (70-75) — immutable execution records
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 70_fct_agent_runs — top-level execution records
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."70_fct_agent_runs" (
    id                      UUID         NOT NULL DEFAULT gen_random_uuid(),
    tenant_key              VARCHAR(100) NOT NULL,
    org_id                  UUID         NOT NULL,
    workspace_id            UUID,
    agent_id                UUID         NOT NULL,
    execution_status_code   VARCHAR(50)  NOT NULL DEFAULT 'queued',
    -- Input
    input_messages          JSONB        NOT NULL DEFAULT '[]',
    initial_context         JSONB        NOT NULL DEFAULT '{}',
    -- Budget tracking
    tokens_used             INT          NOT NULL DEFAULT 0,
    tool_calls_made         INT          NOT NULL DEFAULT 0,
    llm_calls_made          INT          NOT NULL DEFAULT 0,
    cost_usd                NUMERIC(10,6) NOT NULL DEFAULT 0,
    iterations_used         INT          NOT NULL DEFAULT 0,
    -- Result
    output_messages         JSONB,
    final_state             JSONB,
    error_message           TEXT,
    -- Timing
    started_at              TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ,
    execution_time_ms       INT,
    -- Tracing
    langfuse_trace_id       VARCHAR(200),
    job_queue_id            UUID,
    test_run_id             UUID,
    -- Snapshot
    graph_source_snapshot   TEXT,
    agent_code_snapshot     VARCHAR(100),
    version_snapshot        INT,
    -- Standard
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID,

    CONSTRAINT pk_70_fct_agent_runs       PRIMARY KEY (id),
    CONSTRAINT fk_70_fct_agent_runs_agent FOREIGN KEY (agent_id)
        REFERENCES "25_agent_sandbox"."20_fct_agents" (id),
    CONSTRAINT fk_70_fct_agent_runs_status FOREIGN KEY (execution_status_code)
        REFERENCES "25_agent_sandbox"."06_dim_execution_statuses" (code)
);

CREATE INDEX IF NOT EXISTS ix_70_fct_agent_runs_org
    ON "25_agent_sandbox"."70_fct_agent_runs" (org_id);
CREATE INDEX IF NOT EXISTS ix_70_fct_agent_runs_agent
    ON "25_agent_sandbox"."70_fct_agent_runs" (agent_id);
CREATE INDEX IF NOT EXISTS ix_70_fct_agent_runs_created
    ON "25_agent_sandbox"."70_fct_agent_runs" (created_at DESC);

-- Prevent UPDATE on immutable transaction table
CREATE OR REPLACE FUNCTION "25_agent_sandbox".fn_prevent_update_70()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow status transitions and budget updates only
    IF OLD.execution_status_code IN ('completed', 'failed', 'timeout', 'cancelled') THEN
        RAISE EXCEPTION 'Cannot update a terminal agent run record';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_70_prevent_terminal_update
    BEFORE UPDATE ON "25_agent_sandbox"."70_fct_agent_runs"
    FOR EACH ROW EXECUTE FUNCTION "25_agent_sandbox".fn_prevent_update_70();


-- ---------------------------------------------------------------------------
-- 71_dtl_agent_run_steps — per-node execution steps within a run
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."71_dtl_agent_run_steps" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    agent_run_id    UUID         NOT NULL,
    step_index      INT          NOT NULL,
    node_name       VARCHAR(200) NOT NULL,
    step_type       VARCHAR(50)  NOT NULL,
    input_json      JSONB,
    output_json     JSONB,
    transition      VARCHAR(200),
    tokens_used     INT          NOT NULL DEFAULT 0,
    cost_usd        NUMERIC(10,6) NOT NULL DEFAULT 0,
    duration_ms     INT,
    error_message   TEXT,
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,

    CONSTRAINT pk_71_dtl_agent_run_steps       PRIMARY KEY (id),
    CONSTRAINT fk_71_dtl_run_steps_run         FOREIGN KEY (agent_run_id)
        REFERENCES "25_agent_sandbox"."70_fct_agent_runs" (id) ON DELETE CASCADE,
    CONSTRAINT ck_71_dtl_run_steps_type        CHECK (step_type IN ('llm_call', 'tool_call', 'conditional', 'human_input', 'handler'))
);

CREATE INDEX IF NOT EXISTS ix_71_dtl_agent_run_steps_run
    ON "25_agent_sandbox"."71_dtl_agent_run_steps" (agent_run_id, step_index);


-- ---------------------------------------------------------------------------
-- 72_dtl_agent_run_tool_calls — tool calls made during a run step
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."72_dtl_agent_run_tool_calls" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    run_step_id     UUID         NOT NULL,
    tool_code       VARCHAR(100) NOT NULL,
    tool_type_code  VARCHAR(50)  NOT NULL,
    input_json      JSONB,
    output_json     JSONB,
    duration_ms     INT,
    error_message   TEXT,
    approval_status VARCHAR(50),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_72_dtl_agent_run_tool_calls       PRIMARY KEY (id),
    CONSTRAINT fk_72_dtl_run_tool_calls_step        FOREIGN KEY (run_step_id)
        REFERENCES "25_agent_sandbox"."71_dtl_agent_run_steps" (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_72_dtl_tool_calls_step
    ON "25_agent_sandbox"."72_dtl_agent_run_tool_calls" (run_step_id);


-- ---------------------------------------------------------------------------
-- 73_dtl_agent_run_llm_calls — LLM calls made during a run step
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."73_dtl_agent_run_llm_calls" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    run_step_id     UUID         NOT NULL,
    model_id        VARCHAR(200),
    system_prompt   TEXT,
    user_prompt     TEXT,
    response_text   TEXT,
    input_tokens    INT          NOT NULL DEFAULT 0,
    output_tokens   INT          NOT NULL DEFAULT 0,
    total_tokens    INT          NOT NULL DEFAULT 0,
    cost_usd        NUMERIC(10,6) NOT NULL DEFAULT 0,
    duration_ms     INT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_73_dtl_agent_run_llm_calls       PRIMARY KEY (id),
    CONSTRAINT fk_73_dtl_run_llm_calls_step        FOREIGN KEY (run_step_id)
        REFERENCES "25_agent_sandbox"."71_dtl_agent_run_steps" (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_73_dtl_llm_calls_step
    ON "25_agent_sandbox"."73_dtl_agent_run_llm_calls" (run_step_id);


-- ---------------------------------------------------------------------------
-- 74_trx_test_run_results — test scenario execution aggregates
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."74_trx_test_run_results" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    tenant_key      VARCHAR(100) NOT NULL,
    org_id          UUID         NOT NULL,
    scenario_id     UUID         NOT NULL,
    agent_id        UUID         NOT NULL,
    total_cases     INT          NOT NULL DEFAULT 0,
    passed          INT          NOT NULL DEFAULT 0,
    failed          INT          NOT NULL DEFAULT 0,
    errored         INT          NOT NULL DEFAULT 0,
    pass_rate       NUMERIC(5,4) NOT NULL DEFAULT 0,
    total_tokens    INT          NOT NULL DEFAULT 0,
    total_cost_usd  NUMERIC(10,6) NOT NULL DEFAULT 0,
    total_duration_ms INT        NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID,

    CONSTRAINT pk_74_trx_test_run_results         PRIMARY KEY (id),
    CONSTRAINT fk_74_trx_test_run_scenario        FOREIGN KEY (scenario_id)
        REFERENCES "25_agent_sandbox"."22_fct_test_scenarios" (id),
    CONSTRAINT fk_74_trx_test_run_agent           FOREIGN KEY (agent_id)
        REFERENCES "25_agent_sandbox"."20_fct_agents" (id)
);

CREATE INDEX IF NOT EXISTS ix_74_trx_test_run_results_org
    ON "25_agent_sandbox"."74_trx_test_run_results" (org_id, created_at DESC);


-- ---------------------------------------------------------------------------
-- 75_dtl_test_case_results — per-case results within a test run
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "25_agent_sandbox"."75_dtl_test_case_results" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    test_run_id     UUID         NOT NULL,
    test_case_id    UUID         NOT NULL,
    agent_run_id    UUID,
    passed          BOOLEAN      NOT NULL DEFAULT FALSE,
    score           NUMERIC(5,4),
    reason          TEXT,
    evaluation_output JSONB,
    execution_time_ms INT        NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_75_dtl_test_case_results       PRIMARY KEY (id),
    CONSTRAINT fk_75_dtl_case_results_run        FOREIGN KEY (test_run_id)
        REFERENCES "25_agent_sandbox"."74_trx_test_run_results" (id) ON DELETE CASCADE,
    CONSTRAINT fk_75_dtl_case_results_case       FOREIGN KEY (test_case_id)
        REFERENCES "25_agent_sandbox"."23_fct_test_cases" (id),
    CONSTRAINT fk_75_dtl_case_results_agent_run  FOREIGN KEY (agent_run_id)
        REFERENCES "25_agent_sandbox"."70_fct_agent_runs" (id)
);

CREATE INDEX IF NOT EXISTS ix_75_dtl_case_results_run
    ON "25_agent_sandbox"."75_dtl_test_case_results" (test_run_id);


-- ═══════════════════════════════════════════════════════════════════════════════
-- VIEWS (80-82)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 80_vw_agent_detail — agents with EAV name/description joined
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "25_agent_sandbox"."80_vw_agent_detail" AS
SELECT
    a.id,
    a.tenant_key,
    a.org_id,
    a.workspace_id,
    a.agent_code,
    a.version_number,
    a.agent_status_code,
    s.name AS agent_status_name,
    a.graph_type,
    a.llm_model_id,
    a.temperature,
    a.max_iterations,
    a.max_tokens_budget,
    a.max_tool_calls,
    a.max_duration_ms,
    a.max_cost_usd,
    a.requires_approval,
    a.python_hash,
    a.is_active,
    a.is_deleted,
    a.created_at,
    a.updated_at,
    a.created_by,
    (SELECT p.property_value FROM "25_agent_sandbox"."40_dtl_agent_properties" p
     WHERE p.agent_id = a.id AND p.property_key = 'name') AS name,
    (SELECT p.property_value FROM "25_agent_sandbox"."40_dtl_agent_properties" p
     WHERE p.agent_id = a.id AND p.property_key = 'description') AS description
FROM "25_agent_sandbox"."20_fct_agents" a
LEFT JOIN "25_agent_sandbox"."02_dim_agent_statuses" s ON s.code = a.agent_status_code
WHERE a.is_deleted = FALSE;


-- ---------------------------------------------------------------------------
-- 81_vw_agent_run_detail — runs with agent info joined
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "25_agent_sandbox"."81_vw_agent_run_detail" AS
SELECT
    r.id,
    r.tenant_key,
    r.org_id,
    r.workspace_id,
    r.agent_id,
    r.execution_status_code,
    es.name AS execution_status_name,
    r.input_messages,
    r.initial_context,
    r.tokens_used,
    r.tool_calls_made,
    r.llm_calls_made,
    r.cost_usd,
    r.iterations_used,
    r.output_messages,
    r.final_state,
    r.error_message,
    r.started_at,
    r.completed_at,
    r.execution_time_ms,
    r.langfuse_trace_id,
    r.test_run_id,
    r.agent_code_snapshot,
    r.version_snapshot,
    r.created_at,
    r.created_by,
    (SELECT p.property_value FROM "25_agent_sandbox"."40_dtl_agent_properties" p
     WHERE p.agent_id = r.agent_id AND p.property_key = 'name') AS agent_name
FROM "25_agent_sandbox"."70_fct_agent_runs" r
LEFT JOIN "25_agent_sandbox"."06_dim_execution_statuses" es ON es.code = r.execution_status_code;


-- ---------------------------------------------------------------------------
-- 82_vw_test_run_summary — test runs with pass/fail counts
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "25_agent_sandbox"."82_vw_test_run_summary" AS
SELECT
    tr.id,
    tr.tenant_key,
    tr.org_id,
    tr.scenario_id,
    tr.agent_id,
    tr.total_cases,
    tr.passed,
    tr.failed,
    tr.errored,
    tr.pass_rate,
    tr.total_tokens,
    tr.total_cost_usd,
    tr.total_duration_ms,
    tr.created_at,
    tr.created_by,
    (SELECT p.property_value FROM "25_agent_sandbox"."42_dtl_scenario_properties" p
     WHERE p.scenario_id = tr.scenario_id AND p.property_key = 'name') AS scenario_name,
    (SELECT p.property_value FROM "25_agent_sandbox"."40_dtl_agent_properties" p
     WHERE p.agent_id = tr.agent_id AND p.property_key = 'name') AS agent_name
FROM "25_agent_sandbox"."74_trx_test_run_results" tr;
