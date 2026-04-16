-- ===========================================================================
-- Migration: Add 'replaced' to document audit event types
-- Date: 2026-04-08
-- Description: Updates the CHECK constraint on 11_docs.04_aud_doc_events
--   to allow the 'replaced' event type.
-- ===========================================================================

-- 1. Drop existing constraint
ALTER TABLE "11_docs"."04_aud_doc_events" 
DROP CONSTRAINT IF EXISTS "04_aud_doc_events_event_type_check";

-- 2. Add updated constraint with 'replaced'
ALTER TABLE "11_docs"."04_aud_doc_events" 
ADD CONSTRAINT "04_aud_doc_events_event_type_check" 
CHECK (event_type IN (
    'uploaded', 'downloaded', 'deleted', 'description_updated',
    'tags_updated', 'title_updated', 'version_updated', 'replaced',
    'reverted', 'virus_scan_completed'
));

-- DOWN ======================================================================
-- ALTER TABLE "11_docs"."04_aud_doc_events" 
-- DROP CONSTRAINT IF EXISTS "04_aud_doc_events_event_type_check";
--
-- ALTER TABLE "11_docs"."04_aud_doc_events" 
-- ADD CONSTRAINT "04_aud_doc_events_event_type_check" 
-- CHECK (event_type IN (
--     'uploaded', 'downloaded', 'deleted', 'description_updated',
--     'tags_updated', 'title_updated', 'version_updated',
--     'virus_scan_completed'
-- ));
