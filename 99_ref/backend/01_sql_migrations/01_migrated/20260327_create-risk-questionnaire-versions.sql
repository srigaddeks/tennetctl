-- ─────────────────────────────────────────────────────────────────────────────
-- 38_VRS_RISK_QUESTIONNAIRE_VERSIONS
-- Immutable questionnaire version snapshots
--
-- Scope: Tied to 37_fct_risk_questionnaires (tenant-scoped via parent)
--   - Each published version captures the full content_jsonb structure
--   - Versions are immutable once published — never update content_jsonb
--   - New questions or edits ALWAYS create a new version record
--
-- content_jsonb structure:
--   { "sections": [ { "id", "title", "description", "icon",
--       "questions": [ { "id", "label", "type", "required",
--                        "options": [{"value","label"}],
--                        "helperText", "placeholder", "subsection" } ] } ] }
--
-- Schema: 14_risk_registry
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "14_risk_registry"."38_vrs_risk_questionnaire_versions" (
    id                  UUID         NOT NULL,
    questionnaire_id    UUID         NOT NULL,   -- FK to 37_fct_risk_questionnaires
    version_number      INTEGER      NOT NULL,   -- 1, 2, 3 … monotonically increasing
    version_status      VARCHAR(50)  NOT NULL DEFAULT 'draft',  -- draft, published, archived
    content_jsonb       JSONB        NOT NULL,   -- full section+question tree (immutable after publish)
    version_label       VARCHAR(255) NULL,
    change_notes        TEXT         NULL,
    published_at        TIMESTAMP    NULL,
    published_by        UUID         NULL,
    created_at          TIMESTAMP    NOT NULL,
    updated_at          TIMESTAMP    NOT NULL,
    created_by          UUID         NULL,
    updated_by          UUID         NULL,
    CONSTRAINT pk_38_vrs_risk_questionnaire_versions               PRIMARY KEY (id),
    CONSTRAINT uq_38_vrs_risk_questionnaire_versions_num           UNIQUE (questionnaire_id, version_number),
    CONSTRAINT ck_38_vrs_risk_questionnaire_versions_status        CHECK (version_status IN ('draft', 'published', 'archived')),
    CONSTRAINT fk_38_vrs_risk_questionnaire_versions_questionnaire FOREIGN KEY (questionnaire_id)
        REFERENCES "14_risk_registry"."37_fct_risk_questionnaires" (id) ON DELETE CASCADE
);

-- The active_version_id FK on 37 is deferred — add it now that 38 exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_37_fct_risk_questionnaires_active_version'
    ) THEN
        ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
            ADD CONSTRAINT fk_37_fct_risk_questionnaires_active_version
                FOREIGN KEY (active_version_id)
                REFERENCES "14_risk_registry"."38_vrs_risk_questionnaire_versions" (id)
                ON DELETE SET NULL;
    END IF;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_38_vrs_risk_questionnaire_versions_questionnaire
    ON "14_risk_registry"."38_vrs_risk_questionnaire_versions" (questionnaire_id, version_number DESC);

CREATE INDEX IF NOT EXISTS idx_38_vrs_risk_questionnaire_versions_status
    ON "14_risk_registry"."38_vrs_risk_questionnaire_versions" (version_status);

-- GIN index for JSONB content search
CREATE INDEX IF NOT EXISTS idx_38_vrs_risk_questionnaire_versions_content
    ON "14_risk_registry"."38_vrs_risk_questionnaire_versions" USING GIN (content_jsonb);

COMMENT ON TABLE "14_risk_registry"."38_vrs_risk_questionnaire_versions"
    IS 'Immutable questionnaire version snapshots. content_jsonb is never modified after publish. New edits always create a new version row.';
COMMENT ON COLUMN "14_risk_registry"."38_vrs_risk_questionnaire_versions".content_jsonb
    IS 'Full sections+questions JSON tree. Schema: {sections:[{id,title,description,icon,questions:[{id,label,type,required,options,helperText}]}]}';
COMMENT ON COLUMN "14_risk_registry"."38_vrs_risk_questionnaire_versions".version_number
    IS 'Monotonically increasing version counter per questionnaire. Starts at 1.';
