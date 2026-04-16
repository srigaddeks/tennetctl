-- Migration: Dual GTM Model Support (Org-led & Auditor-managed)
-- Date: 2026-03-28

-- 1. Workspace Enhancements for Auditor-Managed Model
ALTER TABLE "03_auth_manage"."34_fct_workspaces" 
ADD COLUMN IF NOT EXISTS "is_auditor_managed" BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE "03_auth_manage"."34_fct_workspaces" 
ADD COLUMN IF NOT EXISTS "workspace_type" VARCHAR(30) NOT NULL DEFAULT 'ORG' 
CHECK (workspace_type IN ('ORG', 'AUDITOR_MANAGED'));

-- 2. Control Ownership for Engineer visibility
ALTER TABLE "05_grc_library"."13_fct_controls" 
ADD COLUMN IF NOT EXISTS "control_owner_user_id" UUID;

-- 3. Expanded Task Statuses for Evidence Lifecycle
INSERT INTO "08_tasks"."04_dim_task_statuses" (id, code, name, description, is_terminal, sort_order, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'submitted',          'Submitted',            'Work done, awaiting internal review',     FALSE, 10, TRUE, NOW(), NOW()),
    (gen_random_uuid(), 'internal_review',    'Under Internal Review', 'Under review by Control Owner',           FALSE, 11, TRUE, NOW(), NOW()),
    (gen_random_uuid(), 'internally_approved', 'Internally Approved',  'Approved by GRC Lead, ready for Auditor', FALSE, 12, TRUE, NOW(), NOW()),
    (gen_random_uuid(), 'ready_for_auditor',  'Ready for Auditor',    'Published to active engagement',         FALSE, 13, TRUE, NOW(), NOW()),
    (gen_random_uuid(), 'auditor_reviewing',  'Auditor Reviewing',    'Under review by external auditor',        FALSE, 14, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. Auditor Firms (Firm-level constraint for staff invitations)
CREATE TABLE IF NOT EXISTS "03_auth_manage"."50_fct_auditor_firms" (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(120) NOT NULL,
    domain      VARCHAR(100) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 5. Track Auditor's Firm linkage in Engagement
ALTER TABLE "12_engagements"."11_fct_audit_access_tokens" 
ADD COLUMN IF NOT EXISTS "auditor_firm_id" UUID REFERENCES "03_auth_manage"."50_fct_auditor_firms"(id);
