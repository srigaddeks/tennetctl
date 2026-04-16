-- Promote correct SOC2 and ISO frameworks to sentinel scope
-- and demote the old low-control-count sentinels.
--
-- New sentinels (from dev):
--   7e003527... = SOC2 (72 controls, 7 versions)
--   4c94586e... = ISO/IEC 27001 (71 controls, 3 versions)
--
-- Old sentinels (demoted):
--   08b0e825... = SOC2 (36 controls) → workspace-scoped copy
--   ce7debe9... = ISO/IEC 27001:2022 (40 controls) → workspace-scoped copy

-- Demote old SOC2 sentinel
UPDATE "05_grc_library"."10_fct_frameworks"
SET scope_org_id = NULL,
    scope_workspace_id = NULL,
    is_marketplace_visible = FALSE,
    updated_at = NOW()
WHERE id = '08b0e825-13d8-41e8-9456-ee6e8e60e2df'
  AND scope_org_id = '00000000-0000-0000-0000-000000000010';

-- Demote old ISO sentinel
UPDATE "05_grc_library"."10_fct_frameworks"
SET scope_org_id = NULL,
    scope_workspace_id = NULL,
    is_marketplace_visible = FALSE,
    updated_at = NOW()
WHERE id = 'ce7debe9-796b-48df-a17c-f5e1c91cd012'
  AND scope_org_id = '00000000-0000-0000-0000-000000000010';

-- Promote new SOC2 to sentinel (seed inserts the row, this ensures scope + visibility)
UPDATE "05_grc_library"."10_fct_frameworks"
SET scope_org_id = '00000000-0000-0000-0000-000000000010',
    scope_workspace_id = '00000000-0000-0000-0000-000000000011',
    is_marketplace_visible = TRUE,
    framework_type_code = 'security_framework',
    approval_status = 'approved',
    updated_at = NOW()
WHERE id = '7e003527-4833-4d10-a2b7-b7515a74ac6d';

-- Promote new ISO to sentinel
UPDATE "05_grc_library"."10_fct_frameworks"
SET scope_org_id = '00000000-0000-0000-0000-000000000010',
    scope_workspace_id = '00000000-0000-0000-0000-000000000011',
    is_marketplace_visible = TRUE,
    framework_type_code = 'compliance_standard',
    approval_status = 'approved',
    updated_at = NOW()
WHERE id = '4c94586e-2200-4c4c-8d67-053e945e3525';
