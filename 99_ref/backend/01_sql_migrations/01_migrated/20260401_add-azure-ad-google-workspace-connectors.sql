-- Migration: Add Azure Entra ID and Google Workspace Directory connector support
-- Date: 2026-04-01
-- Description: Seeds provider definitions, asset types, and Steampipe plugin entries
--   for azure_ad (turbot/azuread) and google_workspace (turbot/googledirectory).
--   Azure AD config schema was already partially seeded in 20260326; this migration
--   adds the missing provider definition and asset types for both providers.

-- ============================================================================
-- Azure Entra ID provider definition
-- (config schema was seeded in 20260326_seed-connector-config-schemas.sql
--  but only into 16_dim_provider_definitions if it exists — upsert here to be safe)
-- ============================================================================

INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe,
    steampipe_plugin, rate_limit_rpm, config_schema
) VALUES (
    'azure_ad',
    'Azure Entra ID',
    'backend.10_sandbox.18_drivers.azure_ad.AzureAdDriver',
    'oauth2',
    FALSE,
    TRUE,
    'turbot/azuread',
    120,
    '{"fields": [
        {"key": "tenant_id",     "label": "Tenant ID",     "type": "text",     "required": true,  "credential": false,
         "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "validation": "^[0-9a-f-]{36}$",
         "hint": "Found in Azure Portal → Azure Active Directory → Overview → Tenant ID", "order": 1},
        {"key": "client_id",     "label": "Client ID",     "type": "text",     "required": true,  "credential": false,
         "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "validation": "^[0-9a-f-]{36}$",
         "hint": "Application (client) ID of the registered app in Azure AD", "order": 2},
        {"key": "client_secret", "label": "Client Secret", "type": "password", "required": true,  "credential": true,
         "placeholder": "your-client-secret-value",
         "hint": "Client secret from Azure AD app registration. Requires Directory.Read.All permission.", "order": 3}
    ]}'
) ON CONFLICT (code) DO UPDATE SET
    steampipe_plugin      = EXCLUDED.steampipe_plugin,
    supports_steampipe    = EXCLUDED.supports_steampipe,
    config_schema         = EXCLUDED.config_schema;


-- ============================================================================
-- Google Workspace Directory provider definition
-- ============================================================================

INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe,
    steampipe_plugin, rate_limit_rpm, config_schema
) VALUES (
    'google_workspace',
    'Google Workspace',
    'backend.10_sandbox.18_drivers.google_workspace.GoogleWorkspaceDriver',
    'service_account',
    FALSE,
    TRUE,
    'turbot/googledirectory',
    300,
    '{"fields": [
        {"key": "admin_email",        "label": "Admin Email",              "type": "text",     "required": true,  "credential": false,
         "placeholder": "admin@yourdomain.com",
         "hint": "Email of a Google Workspace super admin used for impersonation via Domain-Wide Delegation.", "order": 1},
        {"key": "customer_id",        "label": "Customer ID",              "type": "text",     "required": false, "credential": false,
         "placeholder": "C01abc123",
         "hint": "Google Workspace customer ID (Admin Console → Account → Profile). Leave blank to auto-detect.", "order": 2},
        {"key": "service_account_key","label": "Service Account Key (JSON)","type": "textarea","required": true,  "credential": true,
         "placeholder": "{\"type\": \"service_account\", \"project_id\": \"...\", ...}",
         "hint": "Full JSON key file content from Google Cloud Console. The service account must have Domain-Wide Delegation enabled.", "order": 3}
    ]}'
) ON CONFLICT (code) DO UPDATE SET
    steampipe_plugin      = EXCLUDED.steampipe_plugin,
    supports_steampipe    = EXCLUDED.supports_steampipe,
    config_schema         = EXCLUDED.config_schema;


-- ============================================================================
-- Asset types for Azure Entra ID
-- ============================================================================

INSERT INTO "15_sandbox"."14_dim_asset_types" (code, provider_code, name, description) VALUES
    ('azuread_user',                      'azure_ad',        'Azure AD User',             'An Azure Active Directory user account'),
    ('azuread_group',                     'azure_ad',        'Azure AD Group',            'An Azure Active Directory security or Microsoft 365 group'),
    ('azuread_conditional_access_policy', 'azure_ad',        'Conditional Access Policy', 'An Azure AD Conditional Access Policy controlling sign-in conditions'),
    ('azuread_service_principal',         'azure_ad',        'Service Principal',         'An Azure AD application or managed identity service principal'),
    ('azuread_directory_role',            'azure_ad',        'Directory Role',            'An Azure AD built-in or custom directory role')
ON CONFLICT (code) DO NOTHING;


-- ============================================================================
-- Asset types for Google Workspace Directory
-- ============================================================================

INSERT INTO "15_sandbox"."14_dim_asset_types" (code, provider_code, name, description) VALUES
    ('googledirectory_user',     'google_workspace', 'Google Workspace User',  'A Google Workspace user account'),
    ('googledirectory_group',    'google_workspace', 'Google Workspace Group', 'A Google Workspace group'),
    ('googledirectory_org_unit', 'google_workspace', 'Org Unit',               'A Google Workspace organizational unit'),
    ('googledirectory_role',     'google_workspace', 'Admin Role',             'A Google Workspace administrator role')
ON CONFLICT (code) DO NOTHING;


-- ============================================================================
-- Steampipe plugin registry entries
-- ============================================================================

INSERT INTO "17_steampipe"."02_dim_plugin_types" (code, name, plugin_image, provider_code, version)
VALUES
    ('turbot/azuread',         'Steampipe Azure AD Plugin',         'ghcr.io/turbot/steampipe-plugin-azuread',         'azure_ad',        'latest'),
    ('turbot/googledirectory', 'Steampipe Google Directory Plugin', 'ghcr.io/turbot/steampipe-plugin-googledirectory', 'google_workspace', 'latest')
ON CONFLICT (code) DO NOTHING;
