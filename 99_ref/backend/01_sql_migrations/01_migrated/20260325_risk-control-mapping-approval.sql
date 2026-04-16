-- Add approval workflow columns to risk-control mappings
-- Mappings created via AI bulk-link start as 'pending'; manually created mappings are 'approved'

ALTER TABLE "14_risk_registry"."30_lnk_risk_control_mappings"
    ADD COLUMN IF NOT EXISTS approval_status  VARCHAR(20)  NOT NULL DEFAULT 'approved'
        CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    ADD COLUMN IF NOT EXISTS approved_by      UUID,
    ADD COLUMN IF NOT EXISTS approved_at      TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS rejection_reason TEXT,
    ADD COLUMN IF NOT EXISTS ai_confidence    NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS ai_rationale     TEXT;

-- Index for quickly fetching pending mappings per org/workspace
CREATE INDEX IF NOT EXISTS idx_risk_ctrl_map_pending
    ON "14_risk_registry"."30_lnk_risk_control_mappings" (approval_status)
    WHERE approval_status = 'pending';
