-- Add is_visible column to documents for admin-controlled visibility
-- Super admins toggle this to control whether end users can see a document

ALTER TABLE "11_docs"."02_fct_documents"
  ADD COLUMN IF NOT EXISTS is_visible BOOLEAN NOT NULL DEFAULT false;
