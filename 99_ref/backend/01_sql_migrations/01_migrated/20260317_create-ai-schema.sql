-- ============================================================
-- 20260317_create-ai-schema.sql
-- Enterprise AI Platform schema (20_ai)
-- ============================================================

BEGIN;

-- Schema created in 20260313_a_create-all-schemas.sql

-- ============================================================
-- DIMENSIONS
-- ============================================================

CREATE TABLE "20_ai"."02_dim_agent_types" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."02_dim_agent_types" (code, name, description) VALUES
    ('copilot',           'System Copilot',       'Page-aware general assistant for all kcontrol pages'),
    ('signal_generator',  'Signal Generator',     'Autonomous code generation for sandbox signals'),
    ('grc_assistant',     'GRC Assistant',        'Domain specialist for GRC frameworks, controls, risks'),
    ('framework_agent',   'Framework Agent',      'Specialist for framework library operations'),
    ('risk_agent',        'Risk Agent',           'Specialist for risk registry operations'),
    ('task_agent',        'Task Agent',           'Specialist for task management operations'),
    ('signal_agent',      'Signal Agent',         'Specialist for signal building operations'),
    ('connector_agent',   'Connector Agent',      'Specialist for connector configuration'),
    ('user_agent',        'User Agent',           'Specialist for user and access management'),
    ('role_agent',        'Role Agent',           'Specialist for role and permission management'),
    ('supervisor',        'Supervisor',           'Root supervisor that routes tasks to team leads');


CREATE TABLE "20_ai"."03_dim_message_roles" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."03_dim_message_roles" (code, name) VALUES
    ('user',      'User'),
    ('assistant', 'Assistant'),
    ('system',    'System'),
    ('tool',      'Tool');


CREATE TABLE "20_ai"."04_dim_approval_statuses" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."04_dim_approval_statuses" (code, name, is_terminal) VALUES
    ('pending',   'Pending',   FALSE),
    ('approved',  'Approved',  FALSE),
    ('rejected',  'Rejected',  TRUE),
    ('executed',  'Executed',  TRUE),
    ('expired',   'Expired',   TRUE),
    ('cancelled', 'Cancelled', TRUE);


CREATE TABLE "20_ai"."05_dim_tool_categories" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."05_dim_tool_categories" (code, name) VALUES
    ('read',       'Read'),
    ('write',      'Write'),
    ('insight',    'Insight'),
    ('navigation', 'Navigation'),
    ('hierarchy',  'Hierarchy'),
    ('action',     'Action');


CREATE TABLE "20_ai"."06_dim_memory_types" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."06_dim_memory_types" (code, name) VALUES
    ('preference',         'User Preference'),
    ('expertise',          'Domain Expertise'),
    ('interaction_pattern','Interaction Pattern'),
    ('domain_knowledge',   'Domain Knowledge');


CREATE TABLE "20_ai"."07_dim_budget_periods" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."07_dim_budget_periods" (code, name) VALUES
    ('daily',   'Daily'),
    ('monthly', 'Monthly');


CREATE TABLE "20_ai"."08_dim_guardrail_types" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."08_dim_guardrail_types" (code, name, description) VALUES
    ('pii_filter',      'PII Filter',       'Detect and redact personally identifiable information'),
    ('injection_detect','Injection Detect',  'Detect prompt injection and jailbreak attempts'),
    ('content_policy',  'Content Policy',   'Block harmful or off-topic content'),
    ('output_filter',   'Output Filter',    'Sanitize LLM output — strip leaked prompts, internal IDs');


CREATE TABLE "20_ai"."09_dim_prompt_scopes" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    sort_order  INT          NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."09_dim_prompt_scopes" (code, name, sort_order) VALUES
    ('agent',   'Agent Base Prompt',    1),
    ('feature', 'Feature Guardrail',    2),
    ('org',     'Org Overlay',          3);


CREATE TABLE "20_ai"."10_dim_agent_relationships" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO "20_ai"."10_dim_agent_relationships" (code, name) VALUES
    ('delegates_to', 'Delegates To'),
    ('reports_to',   'Reports To'),
    ('peers_with',   'Peers With');


-- ============================================================
-- FACTS
-- ============================================================

CREATE TABLE "20_ai"."20_fct_conversations" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key      VARCHAR(100) NOT NULL,
    user_id         UUID         NOT NULL,
    org_id          UUID,
    workspace_id    UUID,
    agent_type_code VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    title           VARCHAR(500),
    page_context    JSONB,
    is_archived     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_user     ON "20_ai"."20_fct_conversations"(user_id);
CREATE INDEX idx_conversations_org      ON "20_ai"."20_fct_conversations"(org_id);
CREATE INDEX idx_conversations_tenant   ON "20_ai"."20_fct_conversations"(tenant_key);
CREATE INDEX idx_conversations_agent    ON "20_ai"."20_fct_conversations"(agent_type_code);
CREATE INDEX idx_conversations_updated  ON "20_ai"."20_fct_conversations"(updated_at DESC);


CREATE TABLE "20_ai"."21_fct_messages" (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id   UUID         NOT NULL REFERENCES "20_ai"."20_fct_conversations"(id) ON DELETE CASCADE,
    role_code         VARCHAR(50)  NOT NULL REFERENCES "20_ai"."03_dim_message_roles"(code),
    content           TEXT         NOT NULL,
    token_count       INT,
    model_id          VARCHAR(200),
    parent_message_id UUID         REFERENCES "20_ai"."21_fct_messages"(id),
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON "20_ai"."21_fct_messages"(conversation_id);
CREATE INDEX idx_messages_created      ON "20_ai"."21_fct_messages"(created_at);


CREATE TABLE "20_ai"."22_fct_tool_calls" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID         NOT NULL REFERENCES "20_ai"."21_fct_messages"(id) ON DELETE CASCADE,
    agent_run_id    UUID,
    tool_name       VARCHAR(200) NOT NULL,
    tool_category   VARCHAR(50)  REFERENCES "20_ai"."05_dim_tool_categories"(code),
    input_json      JSONB,
    output_json     JSONB,
    duration_ms     INT,
    approval_id     UUID,
    is_successful   BOOLEAN,
    error_message   TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_calls_message    ON "20_ai"."22_fct_tool_calls"(message_id);
CREATE INDEX idx_tool_calls_run        ON "20_ai"."22_fct_tool_calls"(agent_run_id);
CREATE INDEX idx_tool_calls_tool_name  ON "20_ai"."22_fct_tool_calls"(tool_name);
CREATE INDEX idx_tool_calls_created    ON "20_ai"."22_fct_tool_calls"(created_at);


CREATE TABLE "20_ai"."23_fct_approval_requests" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key      VARCHAR(100) NOT NULL,
    requester_id    UUID         NOT NULL,
    org_id          UUID,
    workspace_id    UUID,
    approver_id     UUID,
    status_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."04_dim_approval_statuses"(code) DEFAULT 'pending',
    tool_name       VARCHAR(200) NOT NULL,
    tool_category   VARCHAR(50)  NOT NULL,
    entity_type     VARCHAR(100),
    operation       VARCHAR(50),
    payload_json    JSONB        NOT NULL,
    diff_json       JSONB,
    rejection_reason TEXT,
    expires_at      TIMESTAMPTZ  NOT NULL,
    approved_at     TIMESTAMPTZ,
    executed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_approvals_requester   ON "20_ai"."23_fct_approval_requests"(requester_id);
CREATE INDEX idx_approvals_approver    ON "20_ai"."23_fct_approval_requests"(approver_id);
CREATE INDEX idx_approvals_status      ON "20_ai"."23_fct_approval_requests"(status_code);
CREATE INDEX idx_approvals_tenant      ON "20_ai"."23_fct_approval_requests"(tenant_key);
CREATE INDEX idx_approvals_created     ON "20_ai"."23_fct_approval_requests"(created_at DESC);
CREATE INDEX idx_approvals_expires     ON "20_ai"."23_fct_approval_requests"(expires_at) WHERE status_code = 'pending';


CREATE TABLE "20_ai"."24_fct_agent_runs" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID         NOT NULL REFERENCES "20_ai"."20_fct_conversations"(id) ON DELETE CASCADE,
    agent_type_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    graph_name          VARCHAR(200),
    status              VARCHAR(50)  NOT NULL DEFAULT 'running',
    input_tokens        INT          NOT NULL DEFAULT 0,
    output_tokens       INT          NOT NULL DEFAULT 0,
    total_tokens        INT          NOT NULL DEFAULT 0,
    cost_usd            NUMERIC(10,6) NOT NULL DEFAULT 0,
    model_id            VARCHAR(200),
    langfuse_trace_id   VARCHAR(500),
    error_message       TEXT,
    started_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_runs_conversation ON "20_ai"."24_fct_agent_runs"(conversation_id);
CREATE INDEX idx_agent_runs_agent_type   ON "20_ai"."24_fct_agent_runs"(agent_type_code);
CREATE INDEX idx_agent_runs_status       ON "20_ai"."24_fct_agent_runs"(status);
CREATE INDEX idx_agent_runs_started      ON "20_ai"."24_fct_agent_runs"(started_at DESC);


CREATE TABLE "20_ai"."25_fct_user_memories" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL,
    tenant_key      VARCHAR(100) NOT NULL,
    memory_type_code VARCHAR(50) NOT NULL REFERENCES "20_ai"."06_dim_memory_types"(code),
    memory_key      VARCHAR(500) NOT NULL,
    memory_value    TEXT         NOT NULL,
    embedding_id    VARCHAR(500),
    confidence      NUMERIC(3,2) NOT NULL DEFAULT 0.80 CHECK (confidence BETWEEN 0 AND 1),
    source          VARCHAR(200),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_memories_user        ON "20_ai"."25_fct_user_memories"(user_id);
CREATE INDEX idx_user_memories_tenant      ON "20_ai"."25_fct_user_memories"(tenant_key);
CREATE INDEX idx_user_memories_type        ON "20_ai"."25_fct_user_memories"(memory_type_code);
CREATE UNIQUE INDEX idx_user_memories_key  ON "20_ai"."25_fct_user_memories"(user_id, memory_key) WHERE is_active;


-- ============================================================
-- KNOWLEDGE GRAPH (GraphRAG)
-- ============================================================

CREATE TABLE "20_ai"."26_lnk_knowledge_edges" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    source_type         VARCHAR(100) NOT NULL,
    source_id           VARCHAR(500) NOT NULL,
    relationship        VARCHAR(100) NOT NULL,
    target_type         VARCHAR(100) NOT NULL,
    target_id           VARCHAR(500) NOT NULL,
    weight              NUMERIC(5,4) NOT NULL DEFAULT 1.0,
    embedding_id        VARCHAR(500),
    last_refreshed_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_knowledge_edges_source   ON "20_ai"."26_lnk_knowledge_edges"(tenant_key, source_type, source_id);
CREATE INDEX idx_knowledge_edges_target   ON "20_ai"."26_lnk_knowledge_edges"(tenant_key, target_type, target_id);
CREATE UNIQUE INDEX idx_knowledge_edges_unique ON "20_ai"."26_lnk_knowledge_edges"(tenant_key, source_type, source_id, relationship, target_type, target_id);


-- ============================================================
-- APPROVAL POLICIES
-- ============================================================

CREATE TABLE "20_ai"."27_lnk_approval_policies" (
    id                      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key              VARCHAR(100) NOT NULL,
    org_id                  UUID,
    tool_name               VARCHAR(200) NOT NULL,
    auto_approve            BOOLEAN      NOT NULL DEFAULT FALSE,
    max_risk_level          VARCHAR(50),
    required_approver_count INT          NOT NULL DEFAULT 1,
    cooldown_seconds        INT          NOT NULL DEFAULT 0,
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_approval_policies_tenant    ON "20_ai"."27_lnk_approval_policies"(tenant_key);
CREATE INDEX idx_approval_policies_tool      ON "20_ai"."27_lnk_approval_policies"(tool_name);
CREATE UNIQUE INDEX idx_approval_policies_org_tool ON "20_ai"."27_lnk_approval_policies"(COALESCE(org_id::text, ''), tool_name);


-- ============================================================
-- BUDGETS
-- ============================================================

CREATE TABLE "20_ai"."28_fct_token_budgets" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key      VARCHAR(100) NOT NULL,
    user_id         UUID         NOT NULL,
    period_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."07_dim_budget_periods"(code),
    max_tokens      BIGINT       NOT NULL DEFAULT 100000,
    max_cost_usd    NUMERIC(10,2) NOT NULL DEFAULT 5.00,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, period_code)
);

CREATE INDEX idx_token_budgets_user   ON "20_ai"."28_fct_token_budgets"(user_id);
CREATE INDEX idx_token_budgets_tenant ON "20_ai"."28_fct_token_budgets"(tenant_key);


CREATE TABLE "20_ai"."29_trx_token_usage" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL,
    tenant_key      VARCHAR(100) NOT NULL,
    agent_run_id    UUID,
    tokens_used     INT          NOT NULL,
    cost_usd        NUMERIC(10,6) NOT NULL DEFAULT 0,
    model_id        VARCHAR(200),
    recorded_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_token_usage_user        ON "20_ai"."29_trx_token_usage"(user_id);
CREATE INDEX idx_token_usage_recorded    ON "20_ai"."29_trx_token_usage"(user_id, recorded_at);
CREATE INDEX idx_token_usage_run         ON "20_ai"."29_trx_token_usage"(agent_run_id);


-- ============================================================
-- GUARDRAILS
-- ============================================================

CREATE TABLE "20_ai"."30_fct_guardrail_configs" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID,
    guardrail_type_code VARCHAR(50)  NOT NULL REFERENCES "20_ai"."08_dim_guardrail_types"(code),
    is_enabled          BOOLEAN      NOT NULL DEFAULT TRUE,
    config_json         JSONB        NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_guardrail_configs ON "20_ai"."30_fct_guardrail_configs"(tenant_key, COALESCE(org_id::text, ''), guardrail_type_code);
CREATE INDEX idx_guardrail_configs_tenant ON "20_ai"."30_fct_guardrail_configs"(tenant_key);
CREATE INDEX idx_guardrail_configs_org    ON "20_ai"."30_fct_guardrail_configs"(org_id);


CREATE TABLE "20_ai"."31_trx_guardrail_events" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id        UUID,
    user_id             UUID         NOT NULL,
    tenant_key          VARCHAR(100) NOT NULL,
    guardrail_type_code VARCHAR(50)  NOT NULL REFERENCES "20_ai"."08_dim_guardrail_types"(code),
    direction           VARCHAR(20)  NOT NULL CHECK (direction IN ('input', 'output')),
    action_taken        VARCHAR(50)  NOT NULL,
    matched_pattern     TEXT,
    severity            VARCHAR(20)  NOT NULL DEFAULT 'medium',
    original_content    TEXT,
    sanitized_content   TEXT,
    occurred_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_guardrail_events_user    ON "20_ai"."31_trx_guardrail_events"(user_id);
CREATE INDEX idx_guardrail_events_tenant  ON "20_ai"."31_trx_guardrail_events"(tenant_key);
CREATE INDEX idx_guardrail_events_type    ON "20_ai"."31_trx_guardrail_events"(guardrail_type_code);
CREATE INDEX idx_guardrail_events_time    ON "20_ai"."31_trx_guardrail_events"(occurred_at DESC);


-- ============================================================
-- AGENT CONFIG (per agent type + per org LLM config)
-- ============================================================

CREATE TABLE "20_ai"."32_fct_agent_configs" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100) NOT NULL,
    agent_type_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    org_id              UUID,
    provider_base_url   VARCHAR(500),
    api_key_encrypted   TEXT,
    model_id            VARCHAR(200) NOT NULL DEFAULT 'gpt-4o',
    temperature         NUMERIC(3,2) NOT NULL DEFAULT 0.30 CHECK (temperature BETWEEN 0 AND 2),
    max_tokens          INT          NOT NULL DEFAULT 4096,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_configs_tenant     ON "20_ai"."32_fct_agent_configs"(tenant_key);
CREATE INDEX idx_agent_configs_agent_type ON "20_ai"."32_fct_agent_configs"(agent_type_code);
-- Global configs have org_id = NULL; org overrides have org_id set
CREATE UNIQUE INDEX idx_agent_configs_unique ON "20_ai"."32_fct_agent_configs"(agent_type_code, COALESCE(org_id::text, ''));


-- ============================================================
-- PROMPT TEMPLATES (3-level chain)
-- ============================================================

CREATE TABLE "20_ai"."33_fct_prompt_templates" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key      VARCHAR(100) NOT NULL,
    scope_code      VARCHAR(50)  NOT NULL REFERENCES "20_ai"."09_dim_prompt_scopes"(code),
    agent_type_code VARCHAR(50)  REFERENCES "20_ai"."02_dim_agent_types"(code),
    feature_code    VARCHAR(100),
    org_id          UUID,
    prompt_text     TEXT         NOT NULL,
    version         INT          NOT NULL DEFAULT 1,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by      UUID,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompt_templates_tenant     ON "20_ai"."33_fct_prompt_templates"(tenant_key);
CREATE INDEX idx_prompt_templates_scope      ON "20_ai"."33_fct_prompt_templates"(scope_code);
CREATE INDEX idx_prompt_templates_agent_type ON "20_ai"."33_fct_prompt_templates"(agent_type_code);
CREATE INDEX idx_prompt_templates_feature    ON "20_ai"."33_fct_prompt_templates"(feature_code);
CREATE INDEX idx_prompt_templates_org        ON "20_ai"."33_fct_prompt_templates"(org_id);


CREATE TABLE "20_ai"."34_dtl_prompt_template_properties" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id     UUID         NOT NULL REFERENCES "20_ai"."33_fct_prompt_templates"(id) ON DELETE CASCADE,
    property_key    VARCHAR(200) NOT NULL,
    property_value  TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_prompt_props_unique ON "20_ai"."34_dtl_prompt_template_properties"(template_id, property_key);


-- ============================================================
-- SWARM (hierarchical multi-agent)
-- ============================================================

CREATE TABLE "20_ai"."35_fct_agent_definitions" (
    id                      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type_code         VARCHAR(50)  NOT NULL UNIQUE REFERENCES "20_ai"."02_dim_agent_types"(code),
    parent_agent_type_code  VARCHAR(50)  REFERENCES "20_ai"."02_dim_agent_types"(code),
    capabilities_json       JSONB        NOT NULL DEFAULT '[]',
    tools_allowed_json      JSONB        NOT NULL DEFAULT '[]',
    max_delegation_depth    INT          NOT NULL DEFAULT 3,
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Seed agent hierarchy: supervisor → team leads → specialists
INSERT INTO "20_ai"."35_fct_agent_definitions" (agent_type_code, parent_agent_type_code, capabilities_json, tools_allowed_json, max_delegation_depth) VALUES
    ('supervisor',        NULL,            '["route_tasks","synthesize_results","manage_budget"]', '[]', 1),
    ('grc_assistant',     'supervisor',    '["framework_ops","risk_ops","task_ops"]', '["list_frameworks","get_framework","list_controls"]', 2),
    ('signal_generator',  'supervisor',    '["signal_code_gen","signal_validation"]', '["list_signals","list_connectors"]', 2),
    ('copilot',           NULL,            '["general_assist","page_context","memory"]', '[]', 0),
    ('framework_agent',   'grc_assistant', '["framework_crud"]', '["list_frameworks","get_framework","create_framework","update_framework"]', 0),
    ('risk_agent',        'grc_assistant', '["risk_crud"]', '["list_risks","create_risk","update_risk"]', 0),
    ('task_agent',        'grc_assistant', '["task_crud"]', '["list_tasks"]', 0),
    ('signal_agent',      'signal_generator', '["signal_crud"]', '["list_signals","create_signal"]', 0),
    ('connector_agent',   'signal_generator', '["connector_ops"]', '["list_connectors"]', 0),
    ('user_agent',        'supervisor',    '["user_ops"]', '["list_users","list_roles"]', 0),
    ('role_agent',        'supervisor',    '["role_ops"]', '["list_roles","list_groups"]', 0);


CREATE TABLE "20_ai"."36_lnk_agent_hierarchy" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_type_code    VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    child_type_code     VARCHAR(50)  NOT NULL REFERENCES "20_ai"."02_dim_agent_types"(code),
    relationship_code   VARCHAR(50)  NOT NULL REFERENCES "20_ai"."10_dim_agent_relationships"(code),
    delegation_rules    JSONB        NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (parent_type_code, child_type_code)
);


CREATE TABLE "20_ai"."37_trx_agent_delegations" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_run_id       UUID         NOT NULL REFERENCES "20_ai"."24_fct_agent_runs"(id),
    child_run_id        UUID         REFERENCES "20_ai"."24_fct_agent_runs"(id),
    delegated_task      TEXT         NOT NULL,
    result_summary      TEXT,
    tokens_used         INT          NOT NULL DEFAULT 0,
    duration_ms         INT,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_delegations_parent ON "20_ai"."37_trx_agent_delegations"(parent_run_id);
CREATE INDEX idx_agent_delegations_child  ON "20_ai"."37_trx_agent_delegations"(child_run_id);


-- ============================================================
-- EAV DETAILS
-- ============================================================

CREATE TABLE "20_ai"."40_dtl_message_properties" (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id  UUID         NOT NULL REFERENCES "20_ai"."21_fct_messages"(id) ON DELETE CASCADE,
    meta_key    VARCHAR(200) NOT NULL,
    meta_value  TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_message_props_unique ON "20_ai"."40_dtl_message_properties"(message_id, meta_key);


CREATE TABLE "20_ai"."41_dtl_approval_properties" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id     UUID         NOT NULL REFERENCES "20_ai"."23_fct_approval_requests"(id) ON DELETE CASCADE,
    meta_key        VARCHAR(200) NOT NULL,
    meta_value      TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_approval_props_unique ON "20_ai"."41_dtl_approval_properties"(approval_id, meta_key);


CREATE TABLE "20_ai"."42_dtl_agent_run_properties" (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      UUID         NOT NULL REFERENCES "20_ai"."24_fct_agent_runs"(id) ON DELETE CASCADE,
    meta_key    VARCHAR(200) NOT NULL,
    meta_value  TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_run_props_unique ON "20_ai"."42_dtl_agent_run_properties"(run_id, meta_key);


CREATE TABLE "20_ai"."43_dtl_tool_call_properties" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_call_id    UUID         NOT NULL REFERENCES "20_ai"."22_fct_tool_calls"(id) ON DELETE CASCADE,
    meta_key        VARCHAR(200) NOT NULL,
    meta_value      TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_tool_call_props_unique ON "20_ai"."43_dtl_tool_call_properties"(tool_call_id, meta_key);


-- ============================================================
-- VIEWS
-- ============================================================

CREATE VIEW "20_ai"."60_vw_conversation_detail" AS
SELECT
    c.id,
    c.tenant_key,
    c.user_id,
    c.org_id,
    c.workspace_id,
    c.agent_type_code,
    at.name                             AS agent_type_name,
    c.title,
    c.page_context,
    c.is_archived,
    c.created_at,
    c.updated_at,
    COUNT(m.id)                         AS message_count,
    MAX(m.created_at)                   AS last_message_at,
    (SELECT content FROM "20_ai"."21_fct_messages"
     WHERE conversation_id = c.id
     ORDER BY created_at DESC LIMIT 1)  AS last_message_preview
FROM "20_ai"."20_fct_conversations" c
LEFT JOIN "20_ai"."02_dim_agent_types" at ON at.code = c.agent_type_code
LEFT JOIN "20_ai"."21_fct_messages" m ON m.conversation_id = c.id
GROUP BY c.id, at.name;


CREATE VIEW "20_ai"."61_vw_approval_queue" AS
SELECT
    ar.id,
    ar.tenant_key,
    ar.requester_id,
    ar.org_id,
    ar.approver_id,
    ar.status_code,
    aps.name                AS status_name,
    ar.tool_name,
    ar.tool_category,
    ar.entity_type,
    ar.operation,
    ar.payload_json,
    ar.diff_json,
    ar.rejection_reason,
    ar.expires_at,
    ar.approved_at,
    ar.executed_at,
    ar.created_at,
    ar.updated_at,
    CASE WHEN ar.expires_at < NOW() AND ar.status_code = 'pending'
         THEN TRUE ELSE FALSE
    END                     AS is_overdue
FROM "20_ai"."23_fct_approval_requests" ar
LEFT JOIN "20_ai"."04_dim_approval_statuses" aps ON aps.code = ar.status_code;


CREATE VIEW "20_ai"."62_vw_agent_run_detail" AS
SELECT
    r.id,
    r.conversation_id,
    r.agent_type_code,
    at.name             AS agent_type_name,
    r.graph_name,
    r.status,
    r.input_tokens,
    r.output_tokens,
    r.total_tokens,
    r.cost_usd,
    r.model_id,
    r.langfuse_trace_id,
    r.error_message,
    r.started_at,
    r.completed_at,
    r.created_at,
    EXTRACT(EPOCH FROM (COALESCE(r.completed_at, NOW()) - r.started_at)) * 1000 AS duration_ms,
    COUNT(tc.id)        AS tool_call_count
FROM "20_ai"."24_fct_agent_runs" r
LEFT JOIN "20_ai"."02_dim_agent_types" at ON at.code = r.agent_type_code
LEFT JOIN "20_ai"."22_fct_tool_calls" tc ON tc.agent_run_id = r.id
GROUP BY r.id, at.name;


CREATE VIEW "20_ai"."63_vw_token_usage_summary" AS
SELECT
    u.user_id,
    u.tenant_key,
    bp.code                         AS period_code,
    bp.name                         AS period_name,
    CASE
        WHEN bp.code = 'daily'   THEN DATE_TRUNC('day',   u.recorded_at)
        WHEN bp.code = 'monthly' THEN DATE_TRUNC('month',  u.recorded_at)
    END                             AS period_start,
    SUM(u.tokens_used)              AS tokens_used,
    SUM(u.cost_usd)                 AS cost_usd,
    b.max_tokens,
    b.max_cost_usd,
    ROUND(SUM(u.tokens_used) * 100.0 / NULLIF(b.max_tokens, 0), 2) AS token_utilization_pct,
    ROUND(SUM(u.cost_usd)   * 100.0 / NULLIF(b.max_cost_usd, 0), 2) AS cost_utilization_pct
FROM "20_ai"."29_trx_token_usage" u
CROSS JOIN "20_ai"."07_dim_budget_periods" bp
LEFT JOIN "20_ai"."28_fct_token_budgets" b ON b.user_id = u.user_id AND b.period_code = bp.code
WHERE
    (bp.code = 'daily'   AND u.recorded_at >= DATE_TRUNC('day',   NOW()))
    OR
    (bp.code = 'monthly' AND u.recorded_at >= DATE_TRUNC('month', NOW()))
GROUP BY u.user_id, u.tenant_key, bp.code, bp.name, period_start, b.max_tokens, b.max_cost_usd;


CREATE VIEW "20_ai"."64_vw_guardrail_summary" AS
SELECT
    ge.tenant_key,
    ge.guardrail_type_code,
    gt.name                     AS guardrail_type_name,
    ge.direction,
    ge.severity,
    COUNT(*)                    AS trigger_count,
    DATE_TRUNC('hour', ge.occurred_at) AS hour_bucket
FROM "20_ai"."31_trx_guardrail_events" ge
LEFT JOIN "20_ai"."08_dim_guardrail_types" gt ON gt.code = ge.guardrail_type_code
GROUP BY ge.tenant_key, ge.guardrail_type_code, gt.name, ge.direction, ge.severity, hour_bucket;


COMMIT;
