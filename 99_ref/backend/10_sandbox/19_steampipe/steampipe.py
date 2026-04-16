"""
Steampipe query substrate.

Steampipe is an open-source tool that exposes cloud provider APIs as SQL tables.
This substrate:
1. Generates a Steampipe HCL config file in a temporary directory (never persisted)
2. Runs `steampipe query` as a subprocess
3. Parses the JSON output into QueryResult
4. Cleans up the temp directory immediately after use

Security: Decrypted credentials are written to a temp HCL file that is deleted
after each query. The temp directory is created with mode 0o700. The process
environment does not leak credentials into logs.

Limitations:
- Steampipe must be installed and on PATH (or configured via settings)
- Plugin for the provider must be installed in Steampipe's plugin directory
- Steampipe is NOT suitable for high-frequency collection (startup overhead ~2s)
  Use custom drivers for frequent small collections; Steampipe for ad-hoc queries
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from importlib import import_module as _im

_sp_base = _im("backend.10_sandbox.19_steampipe.base")
CollectedAsset = _sp_base.CollectedAsset
CollectionResult = _sp_base.CollectionResult
ConnectionConfig = _sp_base.ConnectionConfig
ConnectionTestResult = _sp_base.ConnectionTestResult
QueryResult = _sp_base.QueryResult
QuerySubstrate = _sp_base.QuerySubstrate
SubstrateType = _sp_base.SubstrateType

logger = logging.getLogger(__name__)

# Steampipe plugin codes -> HCL connection type
_PLUGIN_CONNECTION_TYPES: dict[str, str] = {
    "github": "github",
    "azure_storage": "azure",
    "postgresql": "postgres",
    "azure_ad": "azuread",
    "google_workspace": "googledirectory",
}

# Providers that this substrate supports
_SUPPORTED_PROVIDERS = {"github", "azure_storage", "postgresql", "azure_ad", "google_workspace"}


class SteampipeSubstrate(QuerySubstrate):
    """
    Query substrate backed by Steampipe.

    This substrate delegates SQL query execution to the Steampipe CLI.
    It is suitable for:
    - Ad-hoc compliance queries ("which repos have branch protection disabled?")
    - Bulk asset discovery during collection runs
    - Policy evaluation via the sandbox execution engine

    It is NOT suitable for:
    - High-frequency polling (Steampipe startup is slow)
    - Real-time data (Steampipe has its own caching layer)
    """

    substrate_type = SubstrateType.STEAMPIPE

    def __init__(
        self,
        binary_path: str | None = None,
        plugin_dir: str | None = None,
        query_timeout_seconds: int = 60,
    ) -> None:
        self._binary = binary_path or shutil.which("steampipe") or "steampipe"
        self._plugin_dir = plugin_dir
        self._timeout = query_timeout_seconds

    def supports_provider(self, provider_code: str) -> bool:
        return provider_code in _SUPPORTED_PROVIDERS

    def supports_query(self) -> bool:
        return True

    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        """Test by running a minimal query against the provider."""
        import time

        start = time.monotonic()
        try:
            # Minimal query to validate credentials
            test_sql = self._get_test_query(config.provider_code)
            result = await self.execute_query(config, test_sql)
            latency_ms = int((time.monotonic() - start) * 1000)
            return ConnectionTestResult(
                success=True,
                message=f"Connected successfully. Query returned {result.row_count} row(s).",
                details={"row_count": result.row_count},
                latency_ms=latency_ms,
            )
        except SteampipeError as e:
            return ConnectionTestResult(
                success=False,
                message=str(e) or f"Steampipe error ({type(e).__name__})",
                details={"error_type": type(e).__name__},
            )
        except Exception as e:
            logger.warning(
                "steampipe_test_connection_failed",
                extra={"provider": config.provider_code, "error": str(e) or repr(e)},
            )
            error_detail = str(e) or repr(e) or type(e).__name__
            return ConnectionTestResult(
                success=False,
                message=f"Connection test failed: {error_detail}",
            )

    async def collect_assets(
        self,
        config: ConnectionConfig,
        asset_types: list[str] | None = None,
        cursor: str | None = None,
    ) -> CollectionResult:
        """Collect assets by running provider-specific SQL queries via Steampipe.

        Reuses a single temp dir for all queries in one collection run,
        avoiding repeated dir creation / symlink / cleanup per asset type.
        """
        queries = self._get_collection_queries(config.provider_code, asset_types)
        all_assets: list[CollectedAsset] = []
        errors: list[str] = []

        # Template variables for SQL queries
        org_name = config.config.get("org_name", "")

        # Create temp dir once for the entire collection run
        steampipe_home = Path.home() / ".steampipe"
        tmpdir = tempfile.mkdtemp(prefix="kcontrol_sp_", dir=tempfile.gettempdir())
        os.chmod(tmpdir, 0o700)

        try:
            # Symlink shared dirs once
            for dirname in ("plugins", "internal", "db"):
                src = steampipe_home / dirname
                dst = Path(tmpdir) / dirname
                if src.exists():
                    os.symlink(src, dst)

            # Write HCL config once
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            hcl_content = self._generate_hcl(config, tmpdir=tmpdir)
            hcl_path = config_dir / "connection.spc"
            hcl_path.write_text(hcl_content, encoding="utf-8")
            os.chmod(hcl_path, 0o600)

            for asset_type_code, sql_template in queries:
                try:
                    sql = sql_template.format(org_name=org_name)
                    rows = await self._run_steampipe_query(tmpdir, sql)
                    result = QueryResult(
                        rows=rows,
                        row_count=len(rows),
                        query_hash=QueryResult.compute_hash(
                            sql, config.connector_instance_id
                        ),
                        executed_at=datetime.now(tz=timezone.utc),
                        substrate_type=SubstrateType.STEAMPIPE,
                    )
                    assets = self._parse_assets(
                        result.rows, asset_type_code, config.provider_code
                    )
                    all_assets.extend(assets)
                except Exception as e:
                    error_msg = f"Failed to collect {asset_type_code}: {e}"
                    logger.warning(
                        "steampipe_collection_query_failed",
                        extra={
                            "asset_type": asset_type_code,
                            "provider": config.provider_code,
                            "error": str(e),
                        },
                    )
                    errors.append(error_msg)
        finally:
            # Clean up — credentials must not persist on disk
            for link_name in ("plugins", "internal", "db"):
                link_path = Path(tmpdir) / link_name
                if link_path.is_symlink():
                    link_path.unlink()
            shutil.rmtree(tmpdir, ignore_errors=True)

        return CollectionResult(
            assets=all_assets,
            errors=errors,
            is_partial=len(errors) > 0 and len(all_assets) > 0,
        )

    async def execute_query(self, config: ConnectionConfig, sql: str) -> QueryResult:
        """Execute a SQL query via Steampipe.

        Creates a temporary copy of the Steampipe install dir with a custom
        HCL config containing credentials from the database. This ensures each
        connector uses its own credentials without polluting the global config.
        """
        query_hash = QueryResult.compute_hash(sql, config.connector_instance_id)

        # Copy the Steampipe install dir so we get plugins, then override config
        steampipe_home = Path.home() / ".steampipe"
        tmpdir = tempfile.mkdtemp(prefix="kcontrol_sp_", dir=tempfile.gettempdir())
        os.chmod(tmpdir, 0o700)

        try:
            # Symlink the plugin dir (large, don't copy)
            plugin_src = steampipe_home / "plugins"
            plugin_dst = Path(tmpdir) / "plugins"
            if plugin_src.exists():
                os.symlink(plugin_src, plugin_dst)

            # Symlink internal dir (database, etc.)
            internal_src = steampipe_home / "internal"
            internal_dst = Path(tmpdir) / "internal"
            if internal_src.exists():
                os.symlink(internal_src, internal_dst)

            # Symlink db dir
            db_src = steampipe_home / "db"
            db_dst = Path(tmpdir) / "db"
            if db_src.exists():
                os.symlink(db_src, db_dst)

            # Write custom config with credentials from DB
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            hcl_content = self._generate_hcl(config, tmpdir=tmpdir)
            hcl_path = config_dir / "connection.spc"
            hcl_path.write_text(hcl_content, encoding="utf-8")
            os.chmod(hcl_path, 0o600)

            rows = await self._run_steampipe_query(tmpdir, sql)
            return QueryResult(
                rows=rows,
                row_count=len(rows),
                query_hash=query_hash,
                executed_at=datetime.now(tz=timezone.utc),
                substrate_type=SubstrateType.STEAMPIPE,
            )
        finally:
            # Clean up — credentials must not persist on disk
            # Remove symlinks first (don't follow into real dirs)
            for link_name in ("plugins", "internal", "db"):
                link_path = Path(tmpdir) / link_name
                if link_path.is_symlink():
                    link_path.unlink()
            shutil.rmtree(tmpdir, ignore_errors=True)

    async def _run_steampipe_query(
        self, install_dir: str, sql: str, extra_env: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """Run steampipe query subprocess and parse JSON output."""
        cmd = [
            self._binary,
            "query",
            "--output",
            "json",
            "--install-dir",
            install_dir,
            sql,
        ]

        env = {
            **os.environ,
            "STEAMPIPE_TELEMETRY": "none",
            "STEAMPIPE_UPDATE_CHECK": "false",
        }
        if extra_env:
            env.update(extra_env)

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                ),
                timeout=self._timeout,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self._timeout
            )
        except asyncio.TimeoutError:
            raise SteampipeError(f"Steampipe query timed out after {self._timeout}s")

        if proc.returncode != 0:
            error_text = stderr.decode(errors="replace").strip()
            # Sanitize — don't leak credentials from error messages
            error_text = self._sanitize_error(error_text)
            if not error_text:
                error_text = f"exit code {proc.returncode} (no stderr output)"
            raise SteampipeError(
                f"Steampipe exited with code {proc.returncode}: {error_text}"
            )

        try:
            data = json.loads(stdout.decode())
            return data if isinstance(data, list) else data.get("rows", [])
        except json.JSONDecodeError as e:
            raise SteampipeError(f"Failed to parse Steampipe JSON output: {e}")

    def _generate_hcl(self, config: ConnectionConfig, tmpdir: str | None = None) -> str:
        """Generate a Steampipe HCL connection config from credentials.

        Uses the plugin name as the connection name (e.g. 'github') so that
        Steampipe's default search path resolves the tables correctly.
        Each collection runs in an isolated temp dir so there's no conflict.

        Args:
            config: ConnectionConfig with decrypted credentials and non-secret config.
            tmpdir: Path to the current temp directory. Required for providers that
                need credentials written to a file (e.g. google_workspace service
                account key). The temp dir is wiped after every query, so the key
                file never persists beyond a single run.

        Returns:
            HCL string for the Steampipe connection block.

        Raises:
            SteampipeError: If the provider is unsupported or tmpdir is missing
                when required.
        """
        connection_type = _PLUGIN_CONNECTION_TYPES.get(
            config.provider_code, config.provider_code
        )
        conn_name = connection_type  # Use plugin name as connection name

        if config.provider_code == "github":
            token = config.credentials.get("personal_access_token", "")
            base_url = config.config.get("base_url", "")
            hcl = f'''connection "{conn_name}" {{
  plugin = "github"
  token  = "{token}"
'''
            if base_url:
                hcl += f'  base_url = "{base_url}"\n'
            hcl += "}\n"
            return hcl

        elif config.provider_code == "azure_storage":
            return f'''connection "{conn_name}" {{
  plugin          = "azure"
  tenant_id       = "{config.config.get("tenant_id", "")}"
  client_id       = "{config.config.get("client_id", "")}"
  client_secret   = "{config.credentials.get("client_secret", "")}"
  subscription_id = "{config.config.get("subscription_id", "")}"
}}
'''
        elif config.provider_code == "azure_ad":
            return f'''connection "{conn_name}" {{
  plugin        = "azuread"
  tenant_id     = "{config.config.get("tenant_id", "")}"
  client_id     = "{config.config.get("client_id", "")}"
  client_secret = "{config.credentials.get("client_secret", "")}"
}}
'''
        elif config.provider_code == "google_workspace":
            if not tmpdir:
                raise SteampipeError(
                    "tmpdir is required for google_workspace HCL generation"
                )
            # Write service account JSON to a temp file — googledirectory plugin
            # requires a file path, not inline JSON. The temp dir is wiped after
            # every query so the key never persists on disk beyond the run.
            sa_key_json = config.credentials.get("service_account_key", "")
            sa_key_path = Path(tmpdir) / "gws_sa_key.json"
            sa_key_path.write_text(sa_key_json, encoding="utf-8")
            os.chmod(sa_key_path, 0o600)
            admin_email = config.config.get("admin_email", "")
            return f'''connection "{conn_name}" {{
  plugin                  = "googledirectory"
  credentials             = "{sa_key_path}"
  impersonated_user_email = "{admin_email}"
}}
'''
        elif config.provider_code == "postgresql":
            host = config.config.get("host", "localhost")
            port = config.config.get("port", 5432)
            dbname = config.config.get("database", "postgres")
            sslmode = config.config.get("sslmode", "require")
            username = config.credentials.get("username", "")
            password = config.credentials.get("password", "")
            return f'''connection "{conn_name}" {{
  plugin     = "postgres"
  host       = "{host}"
  port       = {port}
  db_name    = "{dbname}"
  username   = "{username}"
  password   = "{password}"
  sslmode    = "{sslmode}"
}}
'''
        else:
            raise SteampipeError(
                f"No HCL template for provider: {config.provider_code}"
            )

    def _get_test_query(self, provider_code: str) -> str:
        """Minimal query to validate credentials."""
        if provider_code == "github":
            return "SELECT name_with_owner FROM github_my_repository LIMIT 1"
        elif provider_code == "azure_storage":
            return "SELECT name FROM azure_storage_account LIMIT 1"
        elif provider_code == "azure_ad":
            return "SELECT id, display_name FROM azuread_user LIMIT 1"
        elif provider_code == "google_workspace":
            return "SELECT id, primary_email FROM googledirectory_user LIMIT 1"
        elif provider_code == "postgresql":
            return "SELECT rolname FROM postgres_role LIMIT 1"
        return "SELECT 1"

    def _get_collection_queries(
        self,
        provider_code: str,
        asset_types: list[str] | None,
    ) -> list[tuple[str, str]]:
        """Return (asset_type_code, sql) pairs for a provider."""
        all_queries = _COLLECTION_QUERIES.get(provider_code, [])
        if not asset_types:
            return all_queries
        return [(code, sql) for code, sql in all_queries if code in asset_types]

    def _parse_assets(
        self,
        rows: list[dict[str, Any]],
        asset_type_code: str,
        provider_code: str,
    ) -> list[CollectedAsset]:
        """Convert raw Steampipe rows into CollectedAsset objects."""
        parser = _ASSET_PARSERS.get(asset_type_code)
        if parser:
            return [parser(row) for row in rows if row]
        # Fallback: generic parser for any Steampipe table
        return [_parse_github_generic(row, asset_type_code) for row in rows if row]

    @staticmethod
    def _sanitize_error(msg: str) -> str:
        """Remove potential credential fragments from error messages."""
        import re

        # Remove anything that looks like a secret token (40+ hex chars or base64)
        msg = re.sub(r"[A-Za-z0-9+/]{40,}={0,2}", "[REDACTED]", msg)
        return msg[:2000]  # Truncate


class SteampipeError(Exception):
    """Raised when Steampipe execution fails."""


# ─────────────────────────────────────────────────────────────────────────────
# Provider-specific collection queries
# ─────────────────────────────────────────────────────────────────────────────

_COLLECTION_QUERIES: dict[str, list[tuple[str, str]]] = {
    "github": [
        # Keep the Steampipe GitHub queries on stable columns only.
        # The installed plugin version is fragile for github_team, so team
        # collection is intentionally omitted here until that path is driver-based.
        (
            "github_org",
            """
            SELECT login, name, description, email, created_at, updated_at,
                   default_repo_permission,
                   members_allowed_repository_creation_type,
                   two_factor_requirement_enabled, billing_email,
                   web_commit_signoff_required
            FROM github_my_organization
            LIMIT 1
        """,
        ),
        (
            "github_repo",
            """
            SELECT name_with_owner, name, description, visibility, owner_login,
                   is_archived, is_disabled, is_fork, is_private, is_template,
                   created_at, updated_at, pushed_at
            FROM github_my_repository
        """,
        ),
        (
            "github_org_member",
            """
            SELECT login, role, has_two_factor_enabled, organization, created_at
            FROM github_organization_member
            WHERE organization = '{org_name}'
        """,
        ),
        (
            "github_workflow",
            """
            SELECT name, state, repository_full_name, path, created_at, updated_at
            FROM github_workflow
            WHERE repository_full_name IN (
                SELECT name_with_owner FROM github_my_repository WHERE NOT is_archived
            )
        """,
        ),
    ],
    "azure_ad": [
        (
            "azuread_user",
            """
            SELECT id, display_name, user_principal_name, mail, user_type,
                   account_enabled, given_name, surname, job_title, department,
                   company_name, office_location, usage_location,
                   on_premises_sync_enabled, on_premises_last_sync_date_time,
                   on_premises_sam_account_name,
                   created_date_time, last_password_change_date_time,
                   password_policies, external_user_state,
                   assigned_licenses, assigned_plans, member_of
            FROM azuread_user
            ORDER BY display_name
        """,
        ),
        (
            "azuread_group",
            """
            SELECT id, display_name, description, mail, mail_enabled,
                   security_enabled, group_types, visibility,
                   membership_rule, membership_rule_processing_state,
                   is_assignable_to_role, on_premises_sync_enabled,
                   created_date_time, members, owners
            FROM azuread_group
            ORDER BY display_name
        """,
        ),
        (
            "azuread_conditional_access_policy",
            """
            SELECT id, display_name, state, conditions,
                   grant_controls, session_controls, created_date_time
            FROM azuread_conditional_access_policy
            ORDER BY display_name
        """,
        ),
        (
            "azuread_service_principal",
            """
            SELECT id, display_name, app_id, service_principal_type,
                   account_enabled, created_date_time
            FROM azuread_service_principal
            ORDER BY display_name
        """,
        ),
        (
            "azuread_directory_role",
            """
            SELECT id, display_name, description, role_template_id, members
            FROM azuread_directory_role
            ORDER BY display_name
        """,
        ),
    ],
    "google_workspace": [
        (
            "googledirectory_user",
            """
            SELECT id, primary_email, full_name, is_admin,
                   is_enrolled_in_2sv, suspended, org_unit_path,
                   creation_time, last_login_time
            FROM googledirectory_user
            ORDER BY primary_email
        """,
        ),
        (
            "googledirectory_group",
            """
            SELECT id, email, name, description,
                   admin_created, direct_members_count
            FROM googledirectory_group
            ORDER BY email
        """,
        ),
        (
            "googledirectory_org_unit",
            """
            SELECT org_unit_id, org_unit_path, name,
                   parent_org_unit_path, block_inheritance
            FROM googledirectory_org_unit
            ORDER BY org_unit_path
        """,
        ),
        (
            "googledirectory_role",
            """
            SELECT role_id, role_name, is_system_role, is_super_admin_role
            FROM googledirectory_role
            ORDER BY role_name
        """,
        ),
    ],
    "azure_storage": [
        (
            "azure_storage_account",
            """
            SELECT
                id                    AS external_id,
                name,
                resource_group,
                location,
                sku_name,
                sku_tier,
                kind,
                access_tier,
                enable_blob_encryption,
                enable_file_encryption,
                enable_https_traffic_only,
                allow_blob_public_access,
                minimum_tls_version,
                is_hns_enabled,
                large_file_shares_state,
                creation_time,
                tags
            FROM azure_storage_account
            ORDER BY name
        """,
        ),
        (
            "azure_blob_container",
            """
            SELECT
                id                    AS external_id,
                name,
                storage_account_name,
                resource_group,
                public_access,
                default_encryption_scope,
                deny_encryption_scope_override,
                has_immutability_policy,
                has_legal_hold,
                deleted,
                deleted_time
            FROM azure_storage_container
            ORDER BY storage_account_name, name
        """,
        ),
    ],
    "postgresql": [
        (
            "postgres_role",
            """
            SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb,
                   rolcanlogin, rolreplication, rolbypassrls,
                   rolconnlimit, rolvaliduntil::text, rolpassword
            FROM postgres_role
        """,
        ),
        (
            "postgres_database",
            """
            SELECT name, encoding, lc_collate, lc_ctype,
                   is_template, allow_connections,
                   connection_limit, datdba::text
            FROM postgres_database
        """,
        ),
        (
            "postgres_schema",
            """
            SELECT catalog_name, schema_name, schema_owner,
                   default_character_set_catalog, default_character_set_schema,
                   default_character_set_name, sql_path
            FROM postgres_schema
        """,
        ),
        (
            "postgres_table",
            """
            SELECT table_catalog, table_schema, table_name, table_type,
                   self_referencing_column_name,
                   reference_generation, user_defined_type_catalog,
                   user_defined_type_schema, user_defined_type_name,
                   is_insertable_into, is_typed, commit_action
            FROM postgres_table
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        """,
        ),
        (
            "postgres_stat_activity",
            """
            SELECT pid, datname, usename, application_name,
                   client_addr::text, client_hostname,
                   state, wait_event_type, wait_event,
                   query_start::text, state_change::text,
                   backend_start::text, xact_start::text
            FROM postgres_stat_activity
            WHERE state IS NOT NULL
        """,
        ),
        (
            "postgres_stat_statements",
            """
            SELECT queryid, userid, dbid, query, calls,
                   total_exec_time, mean_exec_time, max_exec_time,
                   rows, shared_blks_hit, shared_blks_read,
                   blk_read_time, blk_write_time
            FROM postgres_stat_statements
            ORDER BY total_exec_time DESC
            LIMIT 100
        """,
        ),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Asset row parsers: convert Steampipe row → CollectedAsset
# ─────────────────────────────────────────────────────────────────────────────


def _flatten_row(
    row: dict[str, Any], exclude: set[str] | None = None
) -> dict[str, str]:
    """Flatten a Steampipe row to string key-value pairs, skipping nulls and internal fields."""
    skip = exclude or set()
    skip.update({"_ctx", "sp_connection_name", "sp_ctx"})
    props: dict[str, str] = {}
    for k, v in row.items():
        if k in skip or v is None:
            continue
        if isinstance(v, dict):
            for nk, nv in v.items():
                if nv is not None and not isinstance(nv, (dict, list)):
                    props[f"{k}_{nk}"] = str(nv)
        elif isinstance(v, list):
            props[k] = ",".join(str(i) for i in v) if v else ""
        else:
            props[k] = str(v)
    return props


def _parse_github_org(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("login") or row.get("name") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="github_org",
        properties=_flatten_row(row, {"login"}),
    )


def _parse_github_repo(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(
        row.get("name_with_owner")
        or row.get("full_name")
        or row.get("name")
        or "unknown"
    )
    org = ext_id.split("/")[0] if "/" in ext_id else None
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="github_repo",
        properties=_flatten_row(row, {"name_with_owner"}),
        parent_external_id=org,
        parent_asset_type_code="github_org",
    )


def _parse_github_branch_protection(row: dict[str, Any]) -> CollectedAsset:
    repo = str(row.get("repository_full_name", ""))
    pattern = str(row.get("pattern", ""))
    ext_id = f"{repo}/{pattern}" if repo and pattern else str(row.get("id", "unknown"))
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="github_branch_protection",
        properties=_flatten_row(row),
        parent_external_id=repo or None,
        parent_asset_type_code="github_repo",
    )


def _parse_azure_storage_account(row: dict[str, Any]) -> CollectedAsset:
    tags = row.get("tags") or {}
    props = {
        k: str(v)
        for k, v in row.items()
        if v is not None and k not in ("external_id", "tags")
    }
    # Flatten tags
    for tag_key, tag_val in tags.items() if isinstance(tags, dict) else []:
        props[f"tag_{tag_key}"] = str(tag_val)
    return CollectedAsset(
        external_id=row["external_id"],
        asset_type_code="azure_storage_account",
        properties=props,
    )


def _parse_azure_blob_container(row: dict[str, Any]) -> CollectedAsset:
    return CollectedAsset(
        external_id=row["external_id"],
        asset_type_code="azure_blob_container",
        properties={
            k: str(v) for k, v in row.items() if v is not None and k != "external_id"
        },
        parent_external_id=row.get("storage_account_name"),
        parent_asset_type_code="azure_storage_account",
    )


def _parse_github_team(row: dict[str, Any]) -> CollectedAsset:
    org = str(row.get("organization", ""))
    slug = str(row.get("slug", row.get("name", "unknown")))
    return CollectedAsset(
        external_id=f"{org}/{slug}" if org else slug,
        asset_type_code="github_team",
        properties=_flatten_row(row),
        parent_external_id=org or None,
        parent_asset_type_code="github_org",
    )


def _parse_github_org_member(row: dict[str, Any]) -> CollectedAsset:
    org = str(row.get("organization", ""))
    login = str(row.get("login", "unknown"))
    return CollectedAsset(
        external_id=f"{org}/{login}" if org else login,
        asset_type_code="github_org_member",
        properties=_flatten_row(row),
        parent_external_id=org or None,
        parent_asset_type_code="github_org",
    )


def _parse_github_generic(row: dict[str, Any], asset_type_code: str) -> CollectedAsset:
    """Generic parser for any GitHub table — uses row ID or first unique column as external_id."""
    ext_id = str(
        row.get("repository_full_name", "")
        + "/"
        + str(row.get("name", row.get("id", "unknown")))
        if row.get("repository_full_name")
        else row.get("name", row.get("id", "unknown"))
    )
    parent = row.get("repository_full_name") or row.get("organization")
    parent_type = (
        "github_repo"
        if row.get("repository_full_name")
        else "github_org"
        if row.get("organization")
        else None
    )
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code=asset_type_code,
        properties=_flatten_row(row),
        parent_external_id=str(parent) if parent else None,
        parent_asset_type_code=parent_type,
    )


def _parse_azuread_user(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("id") or row.get("user_principal_name") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="azuread_user",
        properties=_flatten_row(row, {"id"}),
    )


def _parse_azuread_group(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("id") or row.get("display_name") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="azuread_group",
        properties=_flatten_row(row, {"id"}),
    )


def _parse_azuread_conditional_access_policy(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("id") or row.get("display_name") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="azuread_conditional_access_policy",
        properties=_flatten_row(row, {"id"}),
    )


def _parse_azuread_service_principal(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("id") or row.get("app_id") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="azuread_service_principal",
        properties=_flatten_row(row, {"id"}),
    )


def _parse_azuread_directory_role(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("id") or row.get("display_name") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="azuread_directory_role",
        properties=_flatten_row(row, {"id"}),
    )


def _parse_googledirectory_user(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("id") or row.get("primary_email") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="googledirectory_user",
        properties=_flatten_row(row, {"id"}),
    )


def _parse_googledirectory_group(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("id") or row.get("email") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="googledirectory_group",
        properties=_flatten_row(row, {"id"}),
    )


def _parse_googledirectory_org_unit(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("org_unit_id") or row.get("org_unit_path") or "unknown")
    parent_path = row.get("parent_org_unit_path")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="googledirectory_org_unit",
        properties=_flatten_row(row, {"org_unit_id"}),
        parent_external_id=str(parent_path) if parent_path and parent_path != "/" else None,
        parent_asset_type_code="googledirectory_org_unit" if parent_path and parent_path != "/" else None,
    )


def _parse_googledirectory_role(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("role_id") or row.get("role_name") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="googledirectory_role",
        properties=_flatten_row(row, {"role_id"}),
    )


def _parse_pg_role(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("rolname") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="postgres_role",
        properties=_flatten_row(row, {"rolname"}),
    )


def _parse_pg_database(row: dict[str, Any]) -> CollectedAsset:
    ext_id = str(row.get("name") or row.get("datname") or "unknown")
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="postgres_database",
        properties=_flatten_row(row),
    )


def _parse_pg_schema(row: dict[str, Any]) -> CollectedAsset:
    schema_name = str(row.get("schema_name") or row.get("nspname") or "unknown")
    catalog = str(row.get("catalog_name") or "")
    ext_id = f"{catalog}.{schema_name}" if catalog else schema_name
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="postgres_schema",
        properties=_flatten_row(row),
    )


def _parse_pg_table(row: dict[str, Any]) -> CollectedAsset:
    schema = str(row.get("table_schema") or "public")
    name = str(row.get("table_name") or row.get("name") or "unknown")
    ext_id = f"{schema}.{name}"
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="postgres_table",
        properties=_flatten_row(row),
    )


def _parse_pg_stat_activity(row: dict[str, Any]) -> CollectedAsset:
    pid = str(row.get("pid") or "unknown")
    usename = str(row.get("usename") or "")
    ext_id = f"{usename}_{pid}" if usename else pid
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="postgres_stat_activity",
        properties=_flatten_row(row),
    )


def _parse_pg_stat_statements(row: dict[str, Any]) -> CollectedAsset:
    queryid = str(row.get("queryid") or row.get("query_id") or "unknown")
    userid = str(row.get("userid") or "")
    ext_id = f"{userid}_{queryid}" if userid else queryid
    return CollectedAsset(
        external_id=ext_id,
        asset_type_code="postgres_stat_statements",
        properties=_flatten_row(row),
    )


_ASSET_PARSERS: dict[str, Any] = {
    # GitHub
    "github_org": _parse_github_org,
    "github_repo": _parse_github_repo,
    "github_branch_protection": _parse_github_branch_protection,
    "github_team": _parse_github_team,
    "github_org_member": _parse_github_org_member,
    # Azure Storage
    "azure_storage_account": _parse_azure_storage_account,
    "azure_blob_container": _parse_azure_blob_container,
    # Azure Entra ID
    "azuread_user": _parse_azuread_user,
    "azuread_group": _parse_azuread_group,
    "azuread_conditional_access_policy": _parse_azuread_conditional_access_policy,
    "azuread_service_principal": _parse_azuread_service_principal,
    "azuread_directory_role": _parse_azuread_directory_role,
    # Google Workspace Directory
    "googledirectory_user": _parse_googledirectory_user,
    "googledirectory_group": _parse_googledirectory_group,
    "googledirectory_org_unit": _parse_googledirectory_org_unit,
    "googledirectory_role": _parse_googledirectory_role,
    # PostgreSQL
    "postgres_role": _parse_pg_role,
    "postgres_database": _parse_pg_database,
    "postgres_schema": _parse_pg_schema,
    "postgres_table": _parse_pg_table,
    "postgres_stat_activity": _parse_pg_stat_activity,
    "postgres_stat_statements": _parse_pg_stat_statements,
}
