-- ============================================================================
-- Test Executions & Results
-- ============================================================================
-- Records each time a control test is executed, manually or automatically.
-- Results link back to the control via test-control mappings.
-- Evidence (files/links) can be attached via the attachments module.
-- ============================================================================

-- ── Test Executions ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "05_grc_library"."15_fct_test_executions" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    control_test_id     UUID         NOT NULL,
    control_id          UUID,                    -- specific control being tested (nullable for test-only runs)
    tenant_key          TEXT         NOT NULL DEFAULT '__platform__',
    result_status       VARCHAR(30)  NOT NULL DEFAULT 'pending',
    execution_type      VARCHAR(30)  NOT NULL DEFAULT 'manual',
    executed_by         UUID,
    executed_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    notes               TEXT,
    evidence_summary    TEXT,
    score               INTEGER,                 -- optional 0-100 effectiveness score
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    created_by          UUID,
    updated_by          UUID,

    CONSTRAINT pk_15_fct_test_executions         PRIMARY KEY (id),
    CONSTRAINT fk_15_test_exec_test              FOREIGN KEY (control_test_id)
        REFERENCES "05_grc_library"."14_fct_control_tests"(id),
    CONSTRAINT fk_15_test_exec_control           FOREIGN KEY (control_id)
        REFERENCES "05_grc_library"."13_fct_controls"(id),
    CONSTRAINT ck_15_test_exec_result_status     CHECK (result_status IN (
        'pending', 'pass', 'fail', 'partial', 'not_applicable', 'error'
    )),
    CONSTRAINT ck_15_test_exec_type              CHECK (execution_type IN (
        'manual', 'automated', 'scheduled'
    ))
);

CREATE INDEX IF NOT EXISTS idx_15_test_exec_test
    ON "05_grc_library"."15_fct_test_executions" (control_test_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_15_test_exec_control
    ON "05_grc_library"."15_fct_test_executions" (control_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_15_test_exec_status
    ON "05_grc_library"."15_fct_test_executions" (result_status) WHERE is_deleted = FALSE;

-- ── View: Latest execution per test-control pair ────────────────────────────

CREATE OR REPLACE VIEW "05_grc_library"."43_vw_latest_test_execution" AS
SELECT DISTINCT ON (e.control_test_id, e.control_id)
    e.id,
    e.control_test_id,
    e.control_id,
    e.tenant_key,
    e.result_status,
    e.execution_type,
    e.executed_by,
    e.executed_at,
    e.notes,
    e.evidence_summary,
    e.score,
    t.test_code,
    tp.property_value AS test_name
FROM "05_grc_library"."15_fct_test_executions" e
JOIN "05_grc_library"."14_fct_control_tests" t ON t.id = e.control_test_id
LEFT JOIN "05_grc_library"."24_dtl_test_properties" tp
    ON tp.test_id = t.id AND tp.property_key = 'name'
WHERE e.is_deleted = FALSE
ORDER BY e.control_test_id, e.control_id, e.executed_at DESC;
