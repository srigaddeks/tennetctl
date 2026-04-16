-- Add feedback_ticket to comments and attachments entity type constraints
-- Also add requirement to attachments entity type constraint

ALTER TABLE "08_comments"."01_fct_comments"
  DROP CONSTRAINT IF EXISTS ck_01_fct_comments_entity_type;
ALTER TABLE "08_comments"."01_fct_comments"
  ADD CONSTRAINT ck_01_fct_comments_entity_type
  CHECK (entity_type IN ('task','risk','control','framework','evidence_template','test','requirement','feedback_ticket'));

ALTER TABLE "09_attachments"."01_fct_attachments"
  DROP CONSTRAINT IF EXISTS ck_01_fct_attachments_entity_type;
ALTER TABLE "09_attachments"."01_fct_attachments"
  ADD CONSTRAINT ck_01_fct_attachments_entity_type
  CHECK (entity_type IN ('task','risk','control','framework','evidence_template','test','comment','requirement','feedback_ticket'));
