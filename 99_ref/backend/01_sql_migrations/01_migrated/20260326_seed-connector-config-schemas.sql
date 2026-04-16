-- =============================================================================
-- Migration: Seed connector config schemas in 16_dim_provider_definitions
-- Date: 2026-03-26
-- Description: Each connector type (GitHub, GitLab, AWS, Azure, GCP, Okta,
--   Jira, PostgreSQL, Kubernetes, Slack) gets a config_schema JSONB blob that
--   describes exactly which fields the user must fill in to make the integration
--   work.  Fields are split by "credential" flag:
--     credential=true  → stored encrypted in 41_dtl_connector_instance_credentials
--     credential=false → stored plaintext in 40_dtl_connector_instance_properties
--
--   Each field has: key, label, type, required, credential, placeholder, hint,
--   order.  Optional: options (for select), validation (regex).
--
--   Steampipe plugin reference is also set so the collection engine knows which
--   Steampipe plugin to load.
-- =============================================================================

-- GitHub
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'github',
    'GitHub',
    'backend.10_sandbox.18_drivers.github.GitHubDriver',
    'api_key',
    FALSE, TRUE, 'turbot/github',
    300,
    '{
      "fields": [
        {
          "key": "org_name",
          "label": "Organization Name",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "my-github-org",
          "hint": "The GitHub organization slug (shown in the URL: github.com/<org>)",
          "order": 1
        },
        {
          "key": "personal_access_token",
          "label": "Personal Access Token",
          "type": "password",
          "required": true,
          "credential": true,
          "placeholder": "ghp_xxxxxxxxxxxxxxxxxxxx",
          "hint": "Classic PAT — required scopes: read:org, repo, admin:org, read:user",
          "order": 2
        },
        {
          "key": "base_url",
          "label": "GitHub Enterprise URL",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "https://github.example.com",
          "hint": "Leave blank for github.com. Set only for GitHub Enterprise Server.",
          "order": 3
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema        = EXCLUDED.config_schema,
    supports_steampipe   = EXCLUDED.supports_steampipe,
    steampipe_plugin     = EXCLUDED.steampipe_plugin,
    default_auth_method  = EXCLUDED.default_auth_method,
    updated_at           = NOW();

-- GitLab
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'gitlab',
    'GitLab',
    'backend.10_sandbox.18_drivers.gitlab.GitLabDriver',
    'api_key',
    FALSE, TRUE, 'turbot/gitlab',
    300,
    '{
      "fields": [
        {
          "key": "group_path",
          "label": "Group / Namespace",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "my-group",
          "hint": "Top-level group path (e.g. gitlab.com/<group>). Use nested paths like group/subgroup.",
          "order": 1
        },
        {
          "key": "personal_access_token",
          "label": "Personal Access Token",
          "type": "password",
          "required": true,
          "credential": true,
          "placeholder": "glpat-xxxxxxxxxxxxxxxxxxxx",
          "hint": "Required scopes: read_api, read_user, read_repository",
          "order": 2
        },
        {
          "key": "base_url",
          "label": "GitLab Self-Hosted URL",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "https://gitlab.example.com",
          "hint": "Leave blank for gitlab.com. Set only for self-hosted installations.",
          "order": 3
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- AWS IAM
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'aws_iam',
    'AWS IAM',
    'backend.10_sandbox.18_drivers.aws_iam.AwsIamDriver',
    'iam_role',
    FALSE, TRUE, 'turbot/aws',
    120,
    '{
      "fields": [
        {
          "key": "account_id",
          "label": "AWS Account ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "123456789012",
          "hint": "12-digit AWS account number",
          "validation": "^[0-9]{12}$",
          "order": 1
        },
        {
          "key": "region",
          "label": "Default Region",
          "type": "select",
          "required": true,
          "credential": false,
          "placeholder": "us-east-1",
          "hint": "Primary AWS region for API calls",
          "options": [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
            "ca-central-1", "sa-east-1"
          ],
          "order": 2
        },
        {
          "key": "access_key_id",
          "label": "Access Key ID",
          "type": "text",
          "required": false,
          "credential": true,
          "placeholder": "AKIAIOSFODNN7EXAMPLE",
          "hint": "Use an IAM role (preferred) or provide access key. Required if not using instance role.",
          "order": 3
        },
        {
          "key": "secret_access_key",
          "label": "Secret Access Key",
          "type": "password",
          "required": false,
          "credential": true,
          "placeholder": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
          "hint": "Secret for the access key above. Not required when using IAM instance roles.",
          "order": 4
        },
        {
          "key": "role_arn",
          "label": "IAM Role ARN (assume role)",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "arn:aws:iam::123456789012:role/KControlReadOnly",
          "hint": "If set, the connector will assume this role. Recommended for cross-account access.",
          "order": 5
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- AWS CloudTrail
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'aws_cloudtrail',
    'AWS CloudTrail',
    'backend.10_sandbox.18_drivers.aws_cloudtrail.AwsCloudTrailDriver',
    'iam_role',
    TRUE, TRUE, 'turbot/aws',
    60,
    '{
      "fields": [
        {
          "key": "account_id",
          "label": "AWS Account ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "123456789012",
          "hint": "12-digit AWS account number",
          "validation": "^[0-9]{12}$",
          "order": 1
        },
        {
          "key": "region",
          "label": "Region",
          "type": "select",
          "required": true,
          "credential": false,
          "options": ["us-east-1","us-east-2","us-west-1","us-west-2","eu-west-1","eu-central-1","ap-southeast-1","ap-northeast-1"],
          "order": 2
        },
        {
          "key": "trail_arn",
          "label": "CloudTrail Trail ARN",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "arn:aws:cloudtrail:us-east-1:123456789012:trail/my-trail",
          "hint": "Leave blank to auto-discover all trails in the account",
          "order": 3
        },
        {
          "key": "access_key_id",
          "label": "Access Key ID",
          "type": "text",
          "required": false,
          "credential": true,
          "placeholder": "AKIAIOSFODNN7EXAMPLE",
          "order": 4
        },
        {
          "key": "secret_access_key",
          "label": "Secret Access Key",
          "type": "password",
          "required": false,
          "credential": true,
          "order": 5
        },
        {
          "key": "role_arn",
          "label": "IAM Role ARN",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "arn:aws:iam::123456789012:role/KControlReadOnly",
          "order": 6
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- Azure Active Directory
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'azure_ad',
    'Azure Active Directory',
    'backend.10_sandbox.18_drivers.azure_ad.AzureAdDriver',
    'oauth2',
    FALSE, TRUE, 'turbot/azuread',
    120,
    '{
      "fields": [
        {
          "key": "tenant_id",
          "label": "Tenant ID (Directory ID)",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "hint": "Found in Azure Portal → Azure Active Directory → Overview → Tenant ID",
          "order": 1
        },
        {
          "key": "client_id",
          "label": "Application (Client) ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "hint": "App registration client ID. Requires: User.Read.All, Group.Read.All, Directory.Read.All",
          "order": 2
        },
        {
          "key": "client_secret",
          "label": "Client Secret",
          "type": "password",
          "required": true,
          "credential": true,
          "placeholder": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
          "hint": "Client secret value from app registration (not the secret ID)",
          "order": 3
        },
        {
          "key": "subscription_id",
          "label": "Subscription ID",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "hint": "Azure subscription ID — required for Azure Policy / Azure Monitor connectors",
          "order": 4
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- GCP IAM
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'gcp_iam',
    'GCP IAM',
    'backend.10_sandbox.18_drivers.gcp_iam.GcpIamDriver',
    'oauth2',
    FALSE, TRUE, 'turbot/gcp',
    120,
    '{
      "fields": [
        {
          "key": "project_id",
          "label": "GCP Project ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "my-project-123456",
          "hint": "GCP project ID (not the project number)",
          "order": 1
        },
        {
          "key": "service_account_key_json",
          "label": "Service Account Key (JSON)",
          "type": "textarea",
          "required": true,
          "credential": true,
          "placeholder": "{ \"type\": \"service_account\", \"project_id\": \"...\", ... }",
          "hint": "Paste the full JSON key file content. Required roles: roles/iam.securityReviewer, roles/viewer",
          "order": 2
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- Okta
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'okta',
    'Okta',
    'backend.10_sandbox.18_drivers.okta.OktaDriver',
    'api_key',
    TRUE, TRUE, 'turbot/okta',
    120,
    '{
      "fields": [
        {
          "key": "domain",
          "label": "Okta Domain",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "mycompany.okta.com",
          "hint": "Your Okta tenant domain — found in the browser URL when signed in",
          "order": 1
        },
        {
          "key": "api_token",
          "label": "API Token",
          "type": "password",
          "required": true,
          "credential": true,
          "placeholder": "00xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
          "hint": "Created in Okta Admin → Security → API → Tokens. Must have read-only admin scope.",
          "order": 2
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- Jira
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'jira',
    'Jira',
    'backend.10_sandbox.18_drivers.jira.JiraDriver',
    'api_key',
    FALSE, TRUE, 'turbot/jira',
    60,
    '{
      "fields": [
        {
          "key": "base_url",
          "label": "Jira Base URL",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "https://mycompany.atlassian.net",
          "hint": "Your Jira Cloud or Server URL (no trailing slash)",
          "order": 1
        },
        {
          "key": "email",
          "label": "Account Email",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "admin@mycompany.com",
          "hint": "Email associated with the API token",
          "order": 2
        },
        {
          "key": "api_token",
          "label": "API Token",
          "type": "password",
          "required": true,
          "credential": true,
          "placeholder": "ATATT3xFfGF0...",
          "hint": "Created at id.atlassian.com → Security → API Tokens",
          "order": 3
        },
        {
          "key": "project_keys",
          "label": "Project Keys (optional)",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "PROJ,INFRA,SEC",
          "hint": "Comma-separated list of Jira project keys to sync. Leave blank to sync all accessible projects.",
          "order": 4
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- PostgreSQL
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'postgresql',
    'PostgreSQL',
    'backend.10_sandbox.18_drivers.postgresql.PostgreSQLDriver',
    'connection_string',
    FALSE, TRUE, 'turbot/postgres',
    60,
    '{
      "fields": [
        {
          "key": "host",
          "label": "Host",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "db.mycompany.com",
          "hint": "Hostname or IP address of the PostgreSQL server",
          "order": 1
        },
        {
          "key": "port",
          "label": "Port",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "5432",
          "hint": "Default is 5432",
          "validation": "^[0-9]{1,5}$",
          "order": 2
        },
        {
          "key": "database",
          "label": "Database Name",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "mydb",
          "order": 3
        },
        {
          "key": "username",
          "label": "Username",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "readonly_user",
          "hint": "Use a read-only user — SELECT privileges on relevant schemas",
          "order": 4
        },
        {
          "key": "password",
          "label": "Password",
          "type": "password",
          "required": true,
          "credential": true,
          "order": 5
        },
        {
          "key": "ssl_mode",
          "label": "SSL Mode",
          "type": "select",
          "required": false,
          "credential": false,
          "options": ["require", "verify-ca", "verify-full", "prefer", "disable"],
          "hint": "Recommended: require or verify-full for production",
          "order": 6
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- Kubernetes
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'kubernetes',
    'Kubernetes',
    'backend.10_sandbox.18_drivers.kubernetes.KubernetesDriver',
    'certificate',
    TRUE, TRUE, 'turbot/kubernetes',
    60,
    '{
      "fields": [
        {
          "key": "cluster_name",
          "label": "Cluster Name",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "prod-k8s-cluster",
          "hint": "A unique name to identify this cluster",
          "order": 1
        },
        {
          "key": "api_server_url",
          "label": "API Server URL",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "https://k8s.mycompany.com:6443",
          "hint": "Kubernetes API server endpoint",
          "order": 2
        },
        {
          "key": "kubeconfig",
          "label": "Kubeconfig (YAML or base64)",
          "type": "textarea",
          "required": false,
          "credential": true,
          "placeholder": "apiVersion: v1\nkind: Config\n...",
          "hint": "Paste kubeconfig content. Preferred over service account token.",
          "order": 3
        },
        {
          "key": "service_account_token",
          "label": "Service Account Token",
          "type": "password",
          "required": false,
          "credential": true,
          "hint": "Alternative to kubeconfig. Bearer token for a read-only service account.",
          "order": 4
        },
        {
          "key": "ca_certificate",
          "label": "CA Certificate (base64)",
          "type": "textarea",
          "required": false,
          "credential": false,
          "hint": "Base64-encoded cluster CA certificate. Required when not embedded in kubeconfig.",
          "order": 5
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- Slack
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'slack',
    'Slack',
    'backend.10_sandbox.18_drivers.slack.SlackDriver',
    'oauth2',
    FALSE, TRUE, 'turbot/slack',
    60,
    '{
      "fields": [
        {
          "key": "workspace_name",
          "label": "Slack Workspace Name",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "mycompany",
          "hint": "Your Slack workspace slug (mycompany.slack.com → enter mycompany)",
          "order": 1
        },
        {
          "key": "bot_token",
          "label": "Bot OAuth Token",
          "type": "password",
          "required": true,
          "credential": true,
          "placeholder": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx",
          "hint": "From Slack App → OAuth & Permissions. Required scopes: channels:read, users:read, team:read",
          "order": 2
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- Azure Policy
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'azure_policy',
    'Azure Policy',
    'backend.10_sandbox.18_drivers.azure_policy.AzurePolicyDriver',
    'oauth2',
    FALSE, TRUE, 'turbot/azure',
    60,
    '{
      "fields": [
        {
          "key": "tenant_id",
          "label": "Tenant ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "order": 1
        },
        {
          "key": "subscription_id",
          "label": "Subscription ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "order": 2
        },
        {
          "key": "client_id",
          "label": "Application (Client) ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "hint": "App registration with Policy Insights Reader role",
          "order": 3
        },
        {
          "key": "client_secret",
          "label": "Client Secret",
          "type": "password",
          "required": true,
          "credential": true,
          "order": 4
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- GCP Audit Log
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'gcp_audit',
    'GCP Audit Log',
    'backend.10_sandbox.18_drivers.gcp_audit.GcpAuditDriver',
    'oauth2',
    TRUE, TRUE, 'turbot/gcp',
    60,
    '{
      "fields": [
        {
          "key": "project_id",
          "label": "GCP Project ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "my-project-123456",
          "order": 1
        },
        {
          "key": "service_account_key_json",
          "label": "Service Account Key (JSON)",
          "type": "textarea",
          "required": true,
          "credential": true,
          "placeholder": "{ \"type\": \"service_account\", \"project_id\": \"...\", ... }",
          "hint": "Required roles: roles/logging.viewer, roles/viewer",
          "order": 2
        },
        {
          "key": "log_filter",
          "label": "Log Filter (optional)",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "protoPayload.serviceName=iam.googleapis.com",
          "hint": "GCP Logging filter to narrow which audit logs to collect",
          "order": 3
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- AWS S3
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'aws_s3',
    'AWS S3',
    'backend.10_sandbox.18_drivers.aws_s3.AwsS3Driver',
    'iam_role',
    FALSE, TRUE, 'turbot/aws',
    120,
    '{
      "fields": [
        {
          "key": "account_id",
          "label": "AWS Account ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "123456789012",
          "validation": "^[0-9]{12}$",
          "order": 1
        },
        {
          "key": "region",
          "label": "Region",
          "type": "select",
          "required": true,
          "credential": false,
          "options": ["us-east-1","us-east-2","us-west-1","us-west-2","eu-west-1","eu-central-1","ap-southeast-1","ap-northeast-1"],
          "order": 2
        },
        {
          "key": "bucket_names",
          "label": "Bucket Names (optional)",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "my-bucket, logs-bucket",
          "hint": "Comma-separated list. Leave blank to enumerate all accessible buckets.",
          "order": 3
        },
        {
          "key": "access_key_id",
          "label": "Access Key ID",
          "type": "text",
          "required": false,
          "credential": true,
          "order": 4
        },
        {
          "key": "secret_access_key",
          "label": "Secret Access Key",
          "type": "password",
          "required": false,
          "credential": true,
          "order": 5
        },
        {
          "key": "role_arn",
          "label": "IAM Role ARN",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "arn:aws:iam::123456789012:role/KControlReadOnly",
          "order": 6
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();

-- Azure Monitor
INSERT INTO "15_sandbox"."16_dim_provider_definitions" (
    code, name, driver_module, default_auth_method,
    supports_log_collection, supports_steampipe, steampipe_plugin,
    rate_limit_rpm, config_schema
) VALUES (
    'azure_monitor',
    'Azure Monitor',
    'backend.10_sandbox.18_drivers.azure_monitor.AzureMonitorDriver',
    'oauth2',
    TRUE, TRUE, 'turbot/azure',
    60,
    '{
      "fields": [
        {
          "key": "tenant_id",
          "label": "Tenant ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "order": 1
        },
        {
          "key": "subscription_id",
          "label": "Subscription ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "order": 2
        },
        {
          "key": "client_id",
          "label": "Application (Client) ID",
          "type": "text",
          "required": true,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "hint": "Requires: Monitoring Reader role on the subscription",
          "order": 3
        },
        {
          "key": "client_secret",
          "label": "Client Secret",
          "type": "password",
          "required": true,
          "credential": true,
          "order": 4
        },
        {
          "key": "workspace_id",
          "label": "Log Analytics Workspace ID (optional)",
          "type": "text",
          "required": false,
          "credential": false,
          "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
          "hint": "Only required for Log Analytics / KQL query collection",
          "order": 5
        }
      ]
    }'
) ON CONFLICT (code) DO UPDATE SET
    config_schema = EXCLUDED.config_schema,
    supports_steampipe = EXCLUDED.supports_steampipe,
    steampipe_plugin = EXCLUDED.steampipe_plugin,
    updated_at = NOW();
