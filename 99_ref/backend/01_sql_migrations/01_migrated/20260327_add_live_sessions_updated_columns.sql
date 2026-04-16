-- Add missing updated_at and updated_by columns to live_sessions table
-- This is needed because the repository code expects these columns to exist

ALTER TABLE "15_sandbox"."28_fct_live_sessions"
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NULL;

ALTER TABLE "15_sandbox"."28_fct_live_sessions"
    ADD COLUMN IF NOT EXISTS updated_by UUID NULL;
