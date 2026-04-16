-- Migration: Add linked_event_type_codes to variable queries
-- Allows a variable query to be tagged with the audit event types it supports,
-- so the notification engine knows which events can supply bind params.

ALTER TABLE "03_notifications"."31_fct_variable_queries"
    ADD COLUMN IF NOT EXISTS linked_event_type_codes TEXT[] NOT NULL DEFAULT '{}';

COMMENT ON COLUMN "03_notifications"."31_fct_variable_queries".linked_event_type_codes
    IS 'Audit event types (e.g. task.created, risk.updated) that this query can be triggered by';
