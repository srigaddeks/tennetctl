-- Migration: Disable connector types that have no working Steampipe integration
-- Date: 2026-04-01
-- Description: Sets is_active = FALSE for all connector types except the three
--   that are fully wired end-to-end through the Steampipe substrate:
--     - github         (turbot/github)
--     - azure_ad       (turbot/azuread)
--     - google_workspace (turbot/googledirectory)
--
--   All other connector types remain in the database for future activation.
--   To re-enable a connector, set is_active = TRUE once the Steampipe substrate
--   wiring (HCL template, test query, collection queries, parsers) is complete.

UPDATE "15_sandbox"."03_dim_connector_types"
SET    is_active = FALSE
WHERE  code NOT IN ('github', 'azure_ad', 'google_workspace');
