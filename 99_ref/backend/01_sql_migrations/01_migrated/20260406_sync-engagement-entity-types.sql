-- =============================================================================
-- Migration: 20260406_sync-engagement-entity-types.sql
-- Module:    08_comments, 09_attachments
-- Description: Ensure 'engagement' and other missing entity types are enabled
--              across comments and attachments schema constraints.
--              FIX: Added 'comment' to valid types for 08_comments too.
-- =============================================================================

-- 1. Attachments Schema: Sync 'engagement', 'org', 'workspace', 'comment'
ALTER TABLE "09_attachments"."01_fct_attachments"
  DROP CONSTRAINT IF EXISTS ck_01_fct_attachments_entity_type,
  DROP CONSTRAINT IF EXISTS chk_01_fct_attachments_entity_type;

ALTER TABLE "09_attachments"."01_fct_attachments"
  ADD CONSTRAINT ck_01_fct_attachments_entity_type
  CHECK (entity_type IN (
      'task', 'risk', 'control', 'framework', 'engagement', 'evidence_template', 
      'test', 'comment', 'requirement', 'feedback_ticket',
      'org', 'workspace'
  ));

-- 2. Comments Schema (Facts): Sync 'engagement', 'org', 'workspace', 'comment'
ALTER TABLE "08_comments"."01_fct_comments"
  DROP CONSTRAINT IF EXISTS ck_01_fct_comments_entity_type,
  DROP CONSTRAINT IF EXISTS chk_01_fct_comments_entity_type;

ALTER TABLE "08_comments"."01_fct_comments"
  ADD CONSTRAINT ck_01_fct_comments_entity_type
  CHECK (entity_type IN (
      'task', 'risk', 'control', 'framework', 'engagement', 
      'evidence_template', 'test', 'requirement', 'feedback_ticket',
      'org', 'workspace', 'comment'
  ));

-- 3. Comments Schema (Views): Sync 'engagement', 'org', 'workspace', 'comment'
ALTER TABLE "08_comments"."05_trx_comment_views"
  DROP CONSTRAINT IF EXISTS ck_05_trx_comment_views_entity_type,
  DROP CONSTRAINT IF EXISTS chk_05_trx_comment_views_entity_type;

ALTER TABLE "08_comments"."05_trx_comment_views"
  ADD CONSTRAINT ck_05_trx_comment_views_entity_type
  CHECK (entity_type IN (
      'task', 'risk', 'control', 'framework', 'engagement', 
      'evidence_template', 'test', 'requirement', 'feedback_ticket',
      'org', 'workspace', 'comment'
  ));
