-- =============================================================================
-- Migration: 20260409_fix-framework-type-codes.sql
-- Description: Fix framework_type_code for the 3 published global library
--              frameworks. All were incorrectly set to 'custom' at creation.
--              Also promotes DPDP to the global sentinel scope so it appears
--              in the Framework Library marketplace alongside ISO and SOC2.
-- =============================================================================

-- UP ==========================================================================

-- Fix type codes + approval status for ISO/IEC 27001:2022 and SOC2 (already sentinel-scoped)
UPDATE "05_grc_library"."10_fct_frameworks"
SET framework_type_code = 'compliance_standard',
    approval_status     = 'approved'
WHERE id = 'ce7debe9-796b-48df-a17c-f5e1c91cd012';  -- ISO/IEC 27001:2022

UPDATE "05_grc_library"."10_fct_frameworks"
SET framework_type_code = 'security_framework',
    approval_status     = 'approved'
WHERE id = '08b0e825-13d8-41e8-9456-ee6e8e60e2df';  -- SOC2

-- Promote DPDP (dpdp_4, 77 controls) to global sentinel scope with correct type + approved
UPDATE "05_grc_library"."10_fct_frameworks"
SET
    framework_type_code     = 'privacy_regulation',
    scope_org_id            = '00000000-0000-0000-0000-000000000010',
    scope_workspace_id      = '00000000-0000-0000-0000-000000000011',
    is_marketplace_visible  = TRUE,
    approval_status         = 'approved'
WHERE id = '490f2f7d-9815-48de-b08f-83a4dcd64d35';  -- DPDP dpdp_4 (Digital Personal Data Protection, 77 controls)

-- DOWN ========================================================================

-- UPDATE "05_grc_library"."10_fct_frameworks"
-- SET framework_type_code = 'custom'
-- WHERE id IN (
--     'ce7debe9-796b-48df-a17c-f5e1c91cd012',
--     '08b0e825-13d8-41e8-9456-ee6e8e60e2df',
--     'bf4ae427-bdbd-469d-9731-2c9ce5f37db4'
-- );
