-- Add activity_log column to builder sessions
-- Persists SSE feed events (Phase 1/2 streaming + enhance) so they survive navigation
-- Phase 3 creation logs already live in the job queue output_json; this covers streaming phases.

ALTER TABLE "20_ai"."60_fct_builder_sessions"
    ADD COLUMN IF NOT EXISTS activity_log JSONB NOT NULL DEFAULT '[]'::jsonb;

COMMENT ON COLUMN "20_ai"."60_fct_builder_sessions".activity_log
    IS 'Persisted SSE feed events from Phase 1/2 streaming. Array of {event, ...payload} objects.';
