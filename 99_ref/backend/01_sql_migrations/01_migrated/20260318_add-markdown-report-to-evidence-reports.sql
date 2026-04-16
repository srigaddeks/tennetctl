-- Add markdown_report column to evidence check reports table
ALTER TABLE "20_ai"."71_fct_evidence_check_reports"
    ADD COLUMN IF NOT EXISTS markdown_report TEXT;
