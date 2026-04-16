-- Task Builder sessions table — mirrors framework builder session pattern
-- for async task generation with history, job tracking, and activity logging.

CREATE TABLE IF NOT EXISTS "20_ai"."65_fct_task_builder_sessions" (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key              TEXT        NOT NULL,
    user_id                 UUID        NOT NULL,
    status                  TEXT        NOT NULL DEFAULT 'idle',
        -- idle | generating | reviewing | applying | complete | failed

    -- Scope
    framework_id            UUID        NOT NULL,
    scope_org_id            UUID,
    scope_workspace_id      UUID,

    -- Inputs
    user_context            TEXT        DEFAULT '',
    attachment_ids          JSONB       DEFAULT '[]'::jsonb,
    control_ids             JSONB,          -- NULL = all controls

    -- AI output (preview)
    proposed_tasks          JSONB,          -- list of TaskGroupResponse dicts

    -- Apply result
    apply_result            JSONB,          -- {created: int, skipped: int}

    -- Background job
    job_id                  UUID,           -- FK to 45_fct_job_queue
    error_message           TEXT,

    -- Activity log (persisted SSE events for progress feed)
    activity_log            JSONB       DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    created_by              UUID        NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_task_builder_sessions_user
    ON "20_ai"."65_fct_task_builder_sessions" (tenant_key, user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_task_builder_sessions_framework
    ON "20_ai"."65_fct_task_builder_sessions" (framework_id);

CREATE INDEX IF NOT EXISTS idx_task_builder_sessions_job
    ON "20_ai"."65_fct_task_builder_sessions" (job_id)
    WHERE job_id IS NOT NULL;

-- Seed agent type for job queue FK
INSERT INTO "20_ai"."02_dim_agent_types" (code, name, description)
VALUES ('task_builder', 'Task Builder', 'AI-powered task generation for framework controls')
ON CONFLICT (code) DO NOTHING;
