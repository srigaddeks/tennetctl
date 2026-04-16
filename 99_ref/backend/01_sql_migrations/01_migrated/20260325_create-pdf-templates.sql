-- PDF Report Templates
-- Stored template configurations for customising AI report PDF exports.
-- Templates are tenant-scoped and can be set as default per report type.

CREATE TABLE IF NOT EXISTS "20_ai"."60_fct_pdf_templates" (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key              TEXT NOT NULL,
    name                    TEXT NOT NULL,
    description             TEXT,
    cover_style             TEXT NOT NULL DEFAULT 'dark_navy'
                            CHECK (cover_style IN ('dark_navy', 'light_minimal', 'gradient_accent')),
    primary_color           TEXT NOT NULL DEFAULT '#1e2a45',
    secondary_color         TEXT NOT NULL DEFAULT '#c9a96e',
    header_text             TEXT,
    footer_text             TEXT,
    prepared_by             TEXT,
    doc_ref_prefix          TEXT,
    classification_label    TEXT,
    applicable_report_types TEXT[] NOT NULL DEFAULT '{}',
    is_default              BOOLEAN NOT NULL DEFAULT FALSE,
    shell_file_key          TEXT,
    shell_file_name         TEXT,
    created_by              UUID NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pdf_templates_tenant
    ON "20_ai"."60_fct_pdf_templates"(tenant_key);

CREATE INDEX IF NOT EXISTS idx_pdf_templates_default
    ON "20_ai"."60_fct_pdf_templates"(tenant_key, is_default)
    WHERE is_default = TRUE;

-- Trigger to keep updated_at current
CREATE OR REPLACE FUNCTION "20_ai".fn_pdf_templates_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_pdf_templates_updated_at') THEN
        CREATE TRIGGER trg_pdf_templates_updated_at
            BEFORE UPDATE ON "20_ai"."60_fct_pdf_templates"
            FOR EACH ROW EXECUTE FUNCTION "20_ai".fn_pdf_templates_updated_at();
    END IF;
END $$;
