-- Add gap_analysis column to evidence criteria results table
-- Stores what specific evidence is missing for NOT_MET / PARTIALLY_MET verdicts
ALTER TABLE "20_ai"."72_fct_evidence_criteria_results"
    ADD COLUMN IF NOT EXISTS gap_analysis TEXT;
