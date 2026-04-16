-- Add AI approval columns to test_control_mappings (matching risk_control_mappings pattern)
ALTER TABLE "05_grc_library"."30_lnk_test_control_mappings"
ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) NOT NULL DEFAULT 'approved'
    CHECK (approval_status IN ('pending', 'approved', 'rejected')),
ADD COLUMN IF NOT EXISTS ai_confidence NUMERIC(5,2),
ADD COLUMN IF NOT EXISTS ai_rationale TEXT,
ADD COLUMN IF NOT EXISTS link_type VARCHAR(50) NOT NULL DEFAULT 'covers'
    CHECK (link_type IN ('covers', 'partially_covers', 'related'));

-- Index for filtering pending approvals
CREATE INDEX IF NOT EXISTS idx_test_control_mappings_approval
ON "05_grc_library"."30_lnk_test_control_mappings" (approval_status)
WHERE approval_status = 'pending';
