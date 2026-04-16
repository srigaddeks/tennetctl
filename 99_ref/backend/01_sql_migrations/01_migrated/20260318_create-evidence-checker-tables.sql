-- ============================================================
-- 20260318_create-evidence-checker-tables.sql
-- AI Evidence Checker — DB tables in "20_ai" schema
-- ============================================================

BEGIN;

-- ── 1. Evidence check jobs (lifecycle tracking) ──────────────────────────────
CREATE TABLE IF NOT EXISTS "20_ai"."70_fct_evidence_check_jobs" (
    id                          UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_key                  VARCHAR     NOT NULL,
    org_id                      UUID        NOT NULL,
    task_id                     UUID        NOT NULL,
    triggered_by_attachment_id  UUID,
    attachment_ids              JSONB       NOT NULL DEFAULT '[]',
    status_code                 VARCHAR     NOT NULL DEFAULT 'queued',
    queue_position              INT,
    estimated_wait_seconds      INT,
    progress_criteria_done      INT         NOT NULL DEFAULT 0,
    progress_criteria_total     INT         NOT NULL DEFAULT 0,
    page_cap                    INT         NOT NULL DEFAULT 10000,
    pages_analyzed              INT         NOT NULL DEFAULT 0,
    error_message               TEXT,
    started_at                  TIMESTAMPTZ,
    completed_at                TIMESTAMPTZ,
    is_deleted                  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_70_evcheck_jobs_task
    ON "20_ai"."70_fct_evidence_check_jobs" (tenant_key, task_id, status_code)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_70_evcheck_jobs_queued
    ON "20_ai"."70_fct_evidence_check_jobs" (tenant_key, status_code, created_at)
    WHERE is_deleted = FALSE AND status_code IN ('queued','ingesting','evaluating');

COMMENT ON TABLE "20_ai"."70_fct_evidence_check_jobs"
    IS 'Tracks lifecycle of each evidence evaluation run on a task';

-- ── 2. Evidence check reports (one per completed run) ───────────────────────
CREATE TABLE IF NOT EXISTS "20_ai"."71_fct_evidence_check_reports" (
    id                   UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_key           VARCHAR     NOT NULL,
    org_id               UUID        NOT NULL,
    task_id              UUID        NOT NULL,
    job_id               UUID        NOT NULL
        REFERENCES "20_ai"."70_fct_evidence_check_jobs"(id),
    version              INT         NOT NULL DEFAULT 1,
    is_active            BOOLEAN     NOT NULL DEFAULT TRUE,
    overall_verdict      VARCHAR     NOT NULL,
    attachment_count     INT         NOT NULL DEFAULT 0,
    total_pages_analyzed INT         NOT NULL DEFAULT 0,
    langfuse_trace_id    VARCHAR,
    tokens_consumed      INT         NOT NULL DEFAULT 0,
    duration_seconds     FLOAT,
    is_deleted           BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, version)
);

CREATE INDEX IF NOT EXISTS idx_71_evcheck_reports_task
    ON "20_ai"."71_fct_evidence_check_reports" (tenant_key, task_id, is_active)
    WHERE is_deleted = FALSE;

COMMENT ON TABLE "20_ai"."71_fct_evidence_check_reports"
    IS 'One report per completed evidence evaluation, versioned per task';

-- ── 3. Criteria results (one row per criterion per report) ──────────────────
CREATE TABLE IF NOT EXISTS "20_ai"."72_fct_evidence_criteria_results" (
    id                     UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    report_id              UUID        NOT NULL
        REFERENCES "20_ai"."71_fct_evidence_check_reports"(id),
    criterion_id           UUID,
    criterion_text         TEXT        NOT NULL,
    verdict                VARCHAR     NOT NULL,
    threshold_met          BOOLEAN,
    justification          TEXT,
    evidence_references    JSONB       NOT NULL DEFAULT '[]',
    conflicting_references JSONB       NOT NULL DEFAULT '[]',
    agent_run_id           UUID,
    langfuse_trace_id      VARCHAR,
    is_deleted             BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_72_evcheck_criteria_report
    ON "20_ai"."72_fct_evidence_criteria_results" (report_id)
    WHERE is_deleted = FALSE;

COMMENT ON COLUMN "20_ai"."72_fct_evidence_criteria_results".evidence_references
    IS 'JSONB array of document excerpts. May contain indirect PII. Max 150 chars per excerpt.';

COMMIT;
