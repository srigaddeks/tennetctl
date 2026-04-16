-- Migration: Add parent_group_id to user groups for hierarchy support
--
-- Adds a self-referencing parent_group_id FK on 17_fct_user_groups so groups
-- can be nested (e.g. "Engineering" → "Backend Team" → "Auth Squad").
-- Hierarchy is informational/display only; permission inheritance is NOT
-- transitive at this layer (access resolution still walks group→role→permission).
-- Also adds scope_label column for display purposes.

ALTER TABLE "03_auth_manage"."17_fct_user_groups"
    ADD COLUMN IF NOT EXISTS parent_group_id UUID NULL
        REFERENCES "03_auth_manage"."17_fct_user_groups"(id)
        ON DELETE SET NULL;

-- Index for efficient children lookup
CREATE INDEX IF NOT EXISTS idx_user_groups_parent
    ON "03_auth_manage"."17_fct_user_groups" (parent_group_id)
    WHERE parent_group_id IS NOT NULL AND is_deleted = FALSE;
