-- ═══════════════════════════════════════════════════════════════════════════════
-- Issues — Findings from failed control tests
-- Separate from tasks/risks. Auto-created when control tests fail.
-- ═══════════════════════════════════════════════════════════════════════════════

-- Schema created in 20260313_a_create-all-schemas.sql

-- ---------------------------------------------------------------------------
-- Dimension: issue statuses
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "09_issues"."02_dim_issue_statuses" (
    code        VARCHAR(30)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_02_dim_issue_statuses PRIMARY KEY (code)
);

INSERT INTO "09_issues"."02_dim_issue_statuses" (code, name, sort_order) VALUES
    ('open',          'Open',          1),
    ('investigating', 'Investigating', 2),
    ('remediated',    'Remediated',    3),
    ('verified',      'Verified',      4),
    ('closed',        'Closed',        5),
    ('accepted',      'Risk Accepted', 6)
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Dimension: issue severities
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "09_issues"."03_dim_issue_severities" (
    code        VARCHAR(20)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    CONSTRAINT pk_03_dim_issue_severities PRIMARY KEY (code)
);

INSERT INTO "09_issues"."03_dim_issue_severities" (code, name, sort_order) VALUES
    ('critical', 'Critical', 1),
    ('high',     'High',     2),
    ('medium',   'Medium',   3),
    ('low',      'Low',      4),
    ('info',     'Informational', 5)
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 10_fct_issues — Core issues fact table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "09_issues"."10_fct_issues" (
    id                   UUID          NOT NULL DEFAULT gen_random_uuid(),
    tenant_key           VARCHAR(50)   NOT NULL DEFAULT 'default',
    org_id               UUID          NOT NULL,
    workspace_id         UUID          NULL,

    -- What failed
    promoted_test_id     UUID          NULL,     -- which promoted test failed
    control_test_id      UUID          NULL,     -- GRC control test
    execution_id         UUID          NULL,     -- specific execution that triggered this
    connector_id         UUID          NULL,     -- which connector/asset

    -- Classification
    status_code          VARCHAR(30)   NOT NULL DEFAULT 'open',
    severity_code        VARCHAR(20)   NOT NULL DEFAULT 'high',
    issue_code           VARCHAR(100)  NOT NULL, -- unique per org, e.g. "ISS-2026-001"

    -- Execution result snapshot
    test_code            VARCHAR(200)  NULL,
    test_name            VARCHAR(500)  NULL,
    result_summary       TEXT          NULL,     -- "3 critical issues found"
    result_details       JSONB         NULL,     -- full details array from execution
    connector_type_code  VARCHAR(50)   NULL,

    -- Remediation tracking
    assigned_to          UUID          NULL,
    remediated_at        TIMESTAMPTZ   NULL,
    remediated_by        UUID          NULL,
    remediation_notes    TEXT          NULL,
    verified_at          TIMESTAMPTZ   NULL,
    verified_by          UUID          NULL,

    -- Lifecycle
    is_active            BOOLEAN       NOT NULL DEFAULT TRUE,
    is_deleted           BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    created_by           UUID          NULL,
    closed_at            TIMESTAMPTZ   NULL,

    CONSTRAINT pk_10_fct_issues          PRIMARY KEY (id),
    CONSTRAINT uq_10_fct_issues_code     UNIQUE (org_id, issue_code),
    CONSTRAINT fk_10_fct_issues_status   FOREIGN KEY (status_code)
        REFERENCES "09_issues"."02_dim_issue_statuses" (code),
    CONSTRAINT fk_10_fct_issues_severity FOREIGN KEY (severity_code)
        REFERENCES "09_issues"."03_dim_issue_severities" (code)
);

CREATE INDEX IF NOT EXISTS idx_10_issues_org
    ON "09_issues"."10_fct_issues" (org_id, status_code)
    WHERE is_active AND NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_10_issues_test
    ON "09_issues"."10_fct_issues" (promoted_test_id)
    WHERE is_active AND NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_10_issues_connector
    ON "09_issues"."10_fct_issues" (connector_id)
    WHERE connector_id IS NOT NULL AND is_active AND NOT is_deleted;

-- ---------------------------------------------------------------------------
-- Sequence for issue codes (ISS-2026-001, ISS-2026-002, ...)
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS "09_issues"."issue_code_seq" START 1;
