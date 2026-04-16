-- ─────────────────────────────────────────────────────────────────────────────
-- 41_FCT_RISK_QUESTIONNAIRE_RESPONSES
-- User/workspace answers to an assigned questionnaire version
--
-- Scope: Org + workspace scoped (workspace_id can be NULL for org-level answers)
--   - One row per (org_id, workspace_id, questionnaire_version_id)
--   - answers_jsonb: flat map of question_id → answer value(s)
--     e.g. { "q_abc123": "technology", "q_def456": ["gdpr","iso27001"] }
--
-- Version transition: When a new version (v2) becomes active, the service
--   creates a new response row for v2, pre-filling answers from v1 where
--   question IDs match. Old v1 response is kept for audit history.
--
-- Lifecycle:
--   response_status = 'draft'     → in progress, answers saved but not submitted
--   response_status = 'completed' → user submitted; drives AI risk generation
--
-- Table number 41 used (40 reserved for views by convention)
-- Schema: 14_risk_registry
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "14_risk_registry"."41_fct_risk_questionnaire_responses" (
    id                          UUID         NOT NULL,
    tenant_key                  VARCHAR(100) NOT NULL,
    org_id                      UUID         NOT NULL,
    workspace_id                UUID         NULL,            -- NULL = org-level response
    questionnaire_version_id    UUID         NOT NULL,        -- FK to 38_vrs_risk_questionnaire_versions
    response_status             VARCHAR(50)  NOT NULL DEFAULT 'draft',  -- draft, completed
    answers_jsonb               JSONB        NOT NULL DEFAULT '{}',
    completed_at                TIMESTAMP    NULL,
    completed_by                UUID         NULL,
    created_at                  TIMESTAMP    NOT NULL,
    updated_at                  TIMESTAMP    NOT NULL,
    created_by                  UUID         NULL,
    updated_by                  UUID         NULL,
    CONSTRAINT pk_41_fct_risk_questionnaire_responses               PRIMARY KEY (id),
    CONSTRAINT ck_41_fct_risk_questionnaire_responses_status        CHECK (response_status IN ('draft', 'completed')),
    CONSTRAINT fk_41_fct_risk_questionnaire_responses_version       FOREIGN KEY (questionnaire_version_id)
        REFERENCES "14_risk_registry"."38_vrs_risk_questionnaire_versions" (id),
    CONSTRAINT fk_41_fct_risk_questionnaire_responses_org           FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id),
    CONSTRAINT fk_41_fct_risk_questionnaire_responses_workspace     FOREIGN KEY (workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_tenant
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (tenant_key);

CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_org
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (org_id);

CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_workspace
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (workspace_id)
    WHERE workspace_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_version
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (questionnaire_version_id);

-- Composite: lookup current response for a workspace+version
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_lookup
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (tenant_key, org_id, questionnaire_version_id, created_at DESC);

-- GIN for querying specific answers by question_id
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_answers
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" USING GIN (answers_jsonb);

COMMENT ON TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    IS 'Workspace answers to a questionnaire version. One row per org/workspace/version. Old rows kept as audit history across version transitions.';
COMMENT ON COLUMN "14_risk_registry"."41_fct_risk_questionnaire_responses".answers_jsonb
    IS 'Flat map: question_id → answer. String for single/text, array for multi-choice.';
COMMENT ON COLUMN "14_risk_registry"."41_fct_risk_questionnaire_responses".response_status
    IS 'draft = in progress; completed = submitted and drives AI risk generation.';
