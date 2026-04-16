-- Framework Builder Sessions
-- Persists builder session state (proposed hierarchy, controls, risks) across logout
-- Lives in the 20_ai schema alongside other AI infrastructure

CREATE TABLE IF NOT EXISTS "20_ai"."60_fct_builder_sessions" (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key              TEXT NOT NULL,
    user_id                 UUID NOT NULL,
    session_type            TEXT NOT NULL DEFAULT 'create',   -- 'create' | 'enhance'
    status                  TEXT NOT NULL DEFAULT 'idle',
        -- idle | phase1_streaming | phase1_review
        -- | phase2_streaming | phase2_review
        -- | creating | complete | failed
    -- For enhance mode: the framework being enhanced
    framework_id            UUID REFERENCES "05_grc_library"."10_fct_frameworks"(id) ON DELETE SET NULL,
    -- Setup inputs
    framework_name          TEXT,
    framework_type_code     TEXT,
    framework_category_code TEXT,
    user_context            TEXT,
    attachment_ids          JSONB NOT NULL DEFAULT '[]',
    node_overrides          JSONB NOT NULL DEFAULT '{}',
    -- Proposal outputs (written after each phase completes so user can resume)
    proposed_hierarchy      JSONB,       -- Phase 1: requirement tree
    proposed_controls       JSONB,       -- Phase 2: controls per requirement
    proposed_risks          JSONB,       -- Phase 2: new risk proposals
    proposed_risk_mappings  JSONB,       -- Phase 2: control→risk link proposals
    enhance_diff            JSONB,       -- Enhance mode: full diff payload
    accepted_changes        JSONB,       -- Enhance mode: user-accepted subset
    -- Phase 3 background job
    job_id                  UUID,        -- FK to 20_ai.45_fct_job_queue
    -- Result
    result_framework_id     UUID REFERENCES "05_grc_library"."10_fct_frameworks"(id) ON DELETE SET NULL,
    error_message           TEXT,
    -- Timestamps
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by              UUID NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_builder_sessions_user
    ON "20_ai"."60_fct_builder_sessions" (tenant_key, user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_builder_sessions_status
    ON "20_ai"."60_fct_builder_sessions" (status) WHERE status NOT IN ('complete', 'failed');
