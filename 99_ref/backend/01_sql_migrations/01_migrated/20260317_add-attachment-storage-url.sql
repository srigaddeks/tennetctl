-- ===========================================================================
-- Migration: Add storage_url column to attachments
-- Date: 2026-03-17
-- Description: Stores the canonical blob URL (e.g., Azure Blob URL) directly
--   in Postgres so callers can retrieve the URL without generating a new
--   presigned URL for each request. For Azure the URL is:
--     https://{account}.blob.core.windows.net/{container}/{storage_key}
-- ===========================================================================

ALTER TABLE "09_attachments"."01_fct_attachments"
    ADD COLUMN IF NOT EXISTS storage_url TEXT;

COMMENT ON COLUMN "09_attachments"."01_fct_attachments".storage_url IS
    'Canonical object storage URL. For Azure: https://<account>.blob.core.windows.net/<container>/<key>. NULL for pre-existing rows or non-URL-based providers.';
