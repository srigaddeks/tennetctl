-- =============================================================================
-- Migration: 20260408_seed-comment-mention-template.sql
-- Description: Adds variable keys for mention.author and mention.comment_body
--              (resolved from audit entry properties) used by comment_mention_email.
--              The comment_mention_email template itself was already seeded by
--              20260402_seed-full-environment.sql — this migration is idempotent.
-- =============================================================================

-- UP ==========================================================================

INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, resolution_source, preview_default, sort_order, created_at, updated_at)
VALUES
    ('a0000000-0000-0001-0002-000000000001'::uuid, 'mention.author',
     'Mention Author', 'Display name of the person who wrote the comment',
     'audit_property', 'Alex Johnson', 133, NOW(), NOW()),
    ('a0000000-0000-0001-0002-000000000002'::uuid, 'mention.comment_body',
     'Comment Body', 'Text content of the comment containing the mention',
     'audit_property', 'Please review the latest evidence for CC6.1.', 134, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- DOWN ========================================================================

DELETE FROM "03_notifications"."08_dim_template_variable_keys"
WHERE code IN ('mention.author', 'mention.comment_body');
