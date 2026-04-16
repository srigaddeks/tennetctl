-- =============================================================================
-- Migration: 20260401_add-org-workspace-entity-types.sql
-- Module:    08_comments, 09_attachments
-- Description: Expand entity_type checklists for org and workspace entities.
--              This allows attachments and comments to be directly associated
--              with an organization or workspace record (audit vector).
-- =============================================================================

-- UP ==========================================================================

-- 1. Attachments Schema
ALTER TABLE "09_attachments"."01_fct_attachments"
  DROP CONSTRAINT IF EXISTS ck_01_fct_attachments_entity_type;

ALTER TABLE "09_attachments"."01_fct_attachments"
  ADD CONSTRAINT ck_01_fct_attachments_entity_type
  CHECK (entity_type IN (
      'task', 'risk', 'control', 'framework', 'evidence_template', 
      'test', 'comment', 'requirement', 'feedback_ticket',
      'org', 'workspace'
  ));

-- 2. Comments Schema
ALTER TABLE "08_comments"."01_fct_comments"
  DROP CONSTRAINT IF EXISTS ck_01_fct_comments_entity_type;

ALTER TABLE "08_comments"."01_fct_comments"
  ADD CONSTRAINT ck_01_fct_comments_entity_type
  CHECK (entity_type IN (
      'task', 'risk', 'control', 'framework', 'engagement', 
      'evidence_template', 'test', 'requirement', 'feedback_ticket',
      'org', 'workspace'
  ));

-- DOWN ========================================================================
-- (Partial rollback — strictly speaking, removing types is dangerous if data exists)
