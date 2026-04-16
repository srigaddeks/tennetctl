-- ===========================================================================
-- Migration: Expand attachment audit event types
-- Date: 2026-03-17
-- Description: The original constraint on 03_aud_attachment_events only
--   allowed 5 event types.  Two additional types are now used by the service:
--   storage_cleanup_failed and gdpr_data_deleted.
-- ===========================================================================

ALTER TABLE "09_attachments"."03_aud_attachment_events"
    DROP CONSTRAINT IF EXISTS "ck_03_aud_attachment_events_event_type";

ALTER TABLE "09_attachments"."03_aud_attachment_events"
    ADD CONSTRAINT "ck_03_aud_attachment_events_event_type" CHECK (
        event_type IN (
            'uploaded',
            'downloaded',
            'deleted',
            'virus_scan_completed',
            'description_updated',
            'storage_cleanup_failed',
            'gdpr_data_deleted'
        )
    );
