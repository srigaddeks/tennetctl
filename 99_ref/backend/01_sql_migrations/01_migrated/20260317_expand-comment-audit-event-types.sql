-- ===========================================================================
-- Migration: Expand comment audit event_type constraint
-- Date: 2026-03-17
-- Description: Adds mark_read and comment_gdpr_data_deleted to the allowed
--   event_type values in 08_comments.04_aud_comment_events.
-- ===========================================================================

ALTER TABLE "08_comments"."04_aud_comment_events"
    DROP CONSTRAINT IF EXISTS "ck_04_aud_event_type";

ALTER TABLE "08_comments"."04_aud_comment_events"
    ADD CONSTRAINT "ck_04_aud_event_type" CHECK (event_type IN (
        'created', 'edited', 'deleted',
        'pinned', 'unpinned',
        'resolved', 'unresolved',
        'reaction_added', 'reaction_removed',
        'mark_read',
        'comment_gdpr_data_deleted'
    ));
