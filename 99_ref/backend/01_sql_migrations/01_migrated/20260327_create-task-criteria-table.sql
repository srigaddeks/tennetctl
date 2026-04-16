-- ─────────────────────────────────────────────────────────────────────────────
-- Task Criteria: structured acceptance criteria for evidence checking
-- Replaces newline-delimited EAV property with structured rows
-- Used by: evidence_lead_agent.py (_load_criteria)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "08_tasks"."12_fct_task_criteria" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    tenant_key      VARCHAR      NOT NULL,
    org_id          UUID         NULL,
    task_id         UUID         NOT NULL,
    criterion_text  TEXT         NOT NULL,
    threshold       TEXT         NULL,
    sort_order      INTEGER      NOT NULL DEFAULT 0,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_12_fct_task_criteria      PRIMARY KEY (id),
    CONSTRAINT fk_12_fct_task_criteria_task FOREIGN KEY (task_id)
        REFERENCES "08_tasks"."10_fct_tasks" (id)
);

CREATE INDEX IF NOT EXISTS idx_12_fct_task_criteria_task
    ON "08_tasks"."12_fct_task_criteria" (task_id)
    WHERE is_deleted = FALSE;
