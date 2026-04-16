from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module

import asyncpg

_constants_module = import_module("backend.04_notifications.constants")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_audit_module = import_module("backend.01_core.audit")

NOTIFICATION_SCHEMA = _constants_module.NOTIFICATION_SCHEMA
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
AuditEntry = _audit_module.AuditEntry

SCHEMA = f'"{NOTIFICATION_SCHEMA}"'
AUTH_SCHEMA = '"03_auth_manage"'

_LOGGER = get_logger("backend.notifications.variable_resolver")


@instrument_class_methods(
    namespace="notifications.variable_resolver",
    logger_name="backend.notifications.variable_resolver.instrumentation",
)
class VariableResolver:
    """Resolves template variables from their configured sources.

    Each variable in 08_dim_template_variable_keys has a resolution_source
    and resolution_key that tells the system exactly where to fetch the value:

    - user_property:  recipient's property from 05_dtl_user_properties
    - actor_property: actor's property from 05_dtl_user_properties
    - user_group:     user group info from 17_fct_user_groups (primary group)
    - tenant:         tenant-level settings from 03_fct_users (tenant_key metadata)
    - org:            field from 29_fct_orgs (looked up via org_id in audit props)
    - workspace:      field from 34_fct_workspaces (looked up via workspace_id)
    - settings:       application settings field
    - audit_property: directly from audit event properties dict
    - computed:       computed at runtime (timestamps, URLs, etc.)
    """

    async def resolve_all(
        self,
        connection: asyncpg.Connection,
        *,
        audit_entry: AuditEntry,
        recipient_user_id: str,
        settings: object | None = None,
        template_id: str | None = None,
    ) -> dict[str, str]:
        """Resolve all template variables needed for a notification.

        If template_id is provided, only resolves variables declared in
        15_dtl_template_placeholders for that template. Otherwise resolves
        all known variable keys.
        """
        # Get the variable keys we need to resolve
        variable_keys = await self._get_required_variables(
            connection, template_id=template_id
        )
        if not variable_keys:
            # No declared placeholders — only pass through safe audit properties
            # (not the full dict, which could contain secrets like otp_code or tokens)
            _SAFE_AUDIT_KEYS = {"target", "method", "action_url", "expires_in", "ip_address"}
            return {k: str(v) for k, v in audit_entry.properties.items() if k in _SAFE_AUDIT_KEYS}

        # Group variables by resolution source for batch fetching
        by_source: dict[str, list[asyncpg.Record]] = {}
        for row in variable_keys:
            source = row["resolution_source"]
            by_source.setdefault(source, []).append(row)

        result: dict[str, str] = {}

        # Always include raw audit properties as fallback
        for key, value in audit_entry.properties.items():
            result[key] = str(value) if value is not None else ""

        # Resolve each source group
        if "user_property" in by_source:
            user_props = await self._resolve_user_properties(
                connection, user_id=recipient_user_id, keys=by_source["user_property"]
            )
            result.update(user_props)

        if "actor_property" in by_source and audit_entry.actor_id:
            actor_props = await self._resolve_user_properties(
                connection,
                user_id=audit_entry.actor_id,
                keys=by_source["actor_property"],
                prefix="actor.",
            )
            result.update(actor_props)

        if "org" in by_source:
            org_id = audit_entry.properties.get("org_id") or (
                audit_entry.entity_id if audit_entry.entity_type == "org" else None
            )
            if org_id:
                org_props = await self._resolve_org_fields(
                    connection, org_id=org_id, keys=by_source["org"]
                )
                result.update(org_props)

        if "workspace" in by_source:
            workspace_id = audit_entry.properties.get("workspace_id") or (
                audit_entry.entity_id
                if audit_entry.entity_type == "workspace"
                else None
            )
            if workspace_id:
                ws_props = await self._resolve_workspace_fields(
                    connection, workspace_id=workspace_id, keys=by_source["workspace"]
                )
                result.update(ws_props)

        if "user_group" in by_source:
            group_props = await self._resolve_user_group_fields(
                connection,
                user_id=recipient_user_id,
                keys=by_source["user_group"],
            )
            result.update(group_props)

        if "tenant" in by_source:
            tenant_key = audit_entry.properties.get("tenant_key") or ""
            if tenant_key:
                tenant_props = await self._resolve_tenant_fields(
                    connection, tenant_key=tenant_key, keys=by_source["tenant"]
                )
                result.update(tenant_props)

        if "settings" in by_source and settings is not None:
            settings_props = self._resolve_settings(
                settings=settings, keys=by_source["settings"]
            )
            result.update(settings_props)

        if "computed" in by_source:
            computed_props = self._resolve_computed(
                audit_entry=audit_entry,
                settings=settings,
                keys=by_source["computed"],
            )
            result.update(computed_props)

        # audit_property source: map resolution_key to audit property
        if "audit_property" in by_source:
            for row in by_source["audit_property"]:
                code = row["code"]
                resolution_key = row["resolution_key"]
                if resolution_key and resolution_key in audit_entry.properties:
                    result[code] = str(audit_entry.properties[resolution_key])

        # static source: return the literal static_value stored in the dim table
        if "static" in by_source:
            for row in by_source["static"]:
                code = row["code"]
                static_val = row.get("static_value")
                if static_val is not None:
                    result[code] = str(static_val)

        # custom_query source: execute user-defined SQL queries
        if "custom_query" in by_source:
            custom_props = await self._resolve_custom_queries(
                connection,
                keys=by_source["custom_query"],
                recipient_user_id=recipient_user_id,
                audit_entry=audit_entry,
            )
            result.update(custom_props)

        # Apply default values for any missing required variables
        for row in variable_keys:
            code = row["code"]
            if code not in result or not result[code]:
                default_value = row.get("default_value")
                if default_value:
                    result[code] = default_value

        # Always inject system context
        result["entity_type"] = audit_entry.entity_type
        result["entity_id"] = audit_entry.entity_id
        result["event_type"] = audit_entry.event_type
        if audit_entry.actor_id:
            result["actor_id"] = audit_entry.actor_id

        return result

    async def _get_required_variables(
        self,
        connection: asyncpg.Connection,
        *,
        template_id: str | None = None,
    ) -> list[asyncpg.Record]:
        """Get variable definitions, optionally filtered to a specific template."""
        if template_id:
            # Only variables declared in the template's placeholders (if any are declared)
            rows = await connection.fetch(
                f"""
                SELECT vk.code, vk.resolution_source, vk.resolution_key,
                       vk.data_type, vk.example_value, vk.query_id,
                       vk.static_value,
                       tp.default_value, tp.is_required
                FROM {SCHEMA}."15_dtl_template_placeholders" tp
                JOIN {SCHEMA}."08_dim_template_variable_keys" vk
                    ON vk.code = tp.variable_key_code
                WHERE tp.template_id = $1
                ORDER BY vk.sort_order
                """,
                template_id,
            )
            # If no placeholders declared for this template, fall through to resolve all
            if rows:
                return rows

        # All known variables
        return await connection.fetch(
            f"""
            SELECT code, resolution_source, resolution_key,
                   data_type, example_value, query_id,
                   static_value,
                   NULL AS default_value, TRUE AS is_required
            FROM {SCHEMA}."08_dim_template_variable_keys"
            ORDER BY sort_order
            """
        )

    async def _resolve_user_properties(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        keys: list[asyncpg.Record],
        prefix: str = "user.",
    ) -> dict[str, str]:
        """Fetch user properties from 05_dtl_user_properties."""
        property_keys = [row["resolution_key"] for row in keys if row["resolution_key"]]
        if not property_keys:
            return {}

        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {AUTH_SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1
              AND property_key = ANY($2)
            """,
            user_id,
            property_keys,
        )

        # Build lookup: property_key -> value
        prop_values = {r["property_key"]: r["property_value"] for r in rows}

        result: dict[str, str] = {}
        for row in keys:
            code = row["code"]  # e.g. "user.display_name" or "actor.display_name"
            resolution_key = row["resolution_key"]  # e.g. "display_name"
            if resolution_key and resolution_key in prop_values:
                result[code] = prop_values[resolution_key] or ""

        return result

    async def _resolve_org_fields(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        keys: list[asyncpg.Record],
    ) -> dict[str, str]:
        """Fetch org fields from 29_fct_orgs."""
        row = await connection.fetchrow(
            f"""
            SELECT name, code AS slug, description,
                   org_type_code, created_at::text, updated_at::text
            FROM {AUTH_SCHEMA}."29_fct_orgs"
            WHERE id = $1
            """,
            org_id,
        )
        if not row:
            return {}

        result: dict[str, str] = {}
        for key_row in keys:
            code = key_row["code"]
            resolution_key = key_row["resolution_key"]
            if resolution_key and resolution_key in dict(row):
                val = row[resolution_key]
                result[code] = str(val) if val is not None else ""

        return result

    async def _resolve_workspace_fields(
        self,
        connection: asyncpg.Connection,
        *,
        workspace_id: str,
        keys: list[asyncpg.Record],
    ) -> dict[str, str]:
        """Fetch workspace fields from 34_fct_workspaces."""
        row = await connection.fetchrow(
            f"""
            SELECT name, code AS slug, description,
                   workspace_type_code, created_at::text, updated_at::text
            FROM {AUTH_SCHEMA}."34_fct_workspaces"
            WHERE id = $1
            """,
            workspace_id,
        )
        if not row:
            return {}

        result: dict[str, str] = {}
        for key_row in keys:
            code = key_row["code"]
            resolution_key = key_row["resolution_key"]
            if resolution_key and resolution_key in dict(row):
                val = row[resolution_key]
                result[code] = str(val) if val is not None else ""

        return result

    async def _resolve_user_group_fields(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        keys: list[asyncpg.Record],
    ) -> dict[str, str]:
        """Fetch user group info via group memberships.

        Resolves the user's primary group (first active membership) from
        18_lnk_group_memberships -> 17_fct_user_groups.
        """
        row = await connection.fetchrow(
            f"""
            SELECT ug.name, ug.code, ug.description,
                   ug.created_at::text, ug.updated_at::text
            FROM {AUTH_SCHEMA}."18_lnk_group_memberships" gm
            JOIN {AUTH_SCHEMA}."17_fct_user_groups" ug ON ug.id = gm.group_id
            WHERE gm.user_id = $1
              AND ug.is_active = TRUE AND ug.is_deleted = FALSE
            ORDER BY gm.created_at ASC
            LIMIT 1
            """,
            user_id,
        )
        if not row:
            return {}

        result: dict[str, str] = {}
        for key_row in keys:
            code = key_row["code"]
            resolution_key = key_row["resolution_key"]
            if resolution_key and resolution_key in dict(row):
                val = row[resolution_key]
                result[code] = str(val) if val is not None else ""

        return result

    async def _resolve_tenant_fields(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        keys: list[asyncpg.Record],
    ) -> dict[str, str]:
        """Resolve tenant-level variables.

        Currently resolves from the tenant_key itself and any tenant-level
        settings stored in the system. Extensible for future tenant metadata tables.
        """
        result: dict[str, str] = {}
        for key_row in keys:
            code = key_row["code"]
            resolution_key = key_row["resolution_key"]

            if resolution_key == "tenant_key":
                result[code] = tenant_key
            elif resolution_key == "user_count":
                # Count active users in tenant
                count = await connection.fetchval(
                    f"""
                    SELECT COUNT(*)
                    FROM {AUTH_SCHEMA}."03_fct_users"
                    WHERE tenant_key = $1 AND is_active = TRUE AND is_deleted = FALSE
                    """,
                    tenant_key,
                )
                result[code] = str(count or 0)
            elif resolution_key == "org_count":
                count = await connection.fetchval(
                    f"""
                    SELECT COUNT(*)
                    FROM {AUTH_SCHEMA}."29_fct_orgs"
                    WHERE tenant_key = $1 AND is_active = TRUE AND is_deleted = FALSE
                    """,
                    tenant_key,
                )
                result[code] = str(count or 0)

        return result

    @staticmethod
    def _resolve_settings(
        *,
        settings: object,
        keys: list[asyncpg.Record],
    ) -> dict[str, str]:
        """Resolve variables from application settings.

        Resolution keys may use dot notation (e.g. ``platform.company``).
        These are mapped to underscore attributes on the Settings object
        (e.g. ``platform_company``) before fallback to direct attribute lookup.
        """
        result: dict[str, str] = {}
        for row in keys:
            code = row["code"]
            resolution_key = row["resolution_key"]
            if not resolution_key:
                continue
            # Try dot→underscore mapping first (e.g. "platform.company" → "platform_company")
            attr_name = resolution_key.replace(".", "_")
            if hasattr(settings, attr_name):
                val = getattr(settings, attr_name)
                result[code] = str(val) if val is not None else ""
            elif hasattr(settings, resolution_key):
                val = getattr(settings, resolution_key)
                result[code] = str(val) if val is not None else ""

        return result

    @staticmethod
    def _resolve_computed(
        *,
        audit_entry: AuditEntry,
        settings: object | None,
        keys: list[asyncpg.Record],
    ) -> dict[str, str]:
        """Resolve computed variables (timestamps, URLs, entity IDs, deep links)."""
        result: dict[str, str] = {}

        base_url = ""
        if settings and hasattr(settings, "notification_tracking_base_url"):
            base_url = getattr(settings, "notification_tracking_base_url") or ""

        entity_type = audit_entry.entity_type or ""
        entity_id   = audit_entry.entity_id   or ""

        def _resolve_id(key: str) -> str:
            """Pick entity ID from properties or entity_id fallback."""
            from_prop = audit_entry.properties.get(key, "")
            if from_prop:
                return from_prop
            if entity_type == key:
                return entity_id
            return ""

        for row in keys:
            code = row["code"]
            resolution_key = row["resolution_key"]

            if resolution_key == "event_timestamp":
                result[code] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )

            elif resolution_key == "unsubscribe_url":
                result[code] = (
                    f"{base_url}/settings/notifications" if base_url
                    else "/settings/notifications"
                )

            # ── entity ID pass-throughs ──────────────────────────────────────
            elif resolution_key == "task_id":
                result[code] = _resolve_id("task")
            elif resolution_key == "risk_id":
                result[code] = _resolve_id("risk")
            elif resolution_key == "control_id":
                result[code] = _resolve_id("control")
            elif resolution_key == "framework_id":
                result[code] = _resolve_id("framework")
            elif resolution_key == "org_id":
                result[code] = (
                    audit_entry.properties.get("org_id", "")
                    or (_resolve_id("org"))
                )
            elif resolution_key == "workspace_id":
                result[code] = (
                    audit_entry.properties.get("workspace_id", "")
                    or (_resolve_id("workspace"))
                )

            # ── deep-link URLs ───────────────────────────────────────────────
            elif resolution_key == "task_url":
                tid = _resolve_id("task")
                result[code] = f"{base_url}/tasks/{tid}" if tid else ""
            elif resolution_key == "risk_url":
                rid = _resolve_id("risk")
                result[code] = f"{base_url}/risks/{rid}" if rid else ""
            elif resolution_key == "control_url":
                cid = _resolve_id("control")
                result[code] = f"{base_url}/controls/{cid}" if cid else ""
            elif resolution_key == "framework_url":
                fid = _resolve_id("framework")
                result[code] = f"{base_url}/frameworks/{fid}" if fid else ""

            # ── action URLs / transactional tokens ───────────────────────────
            # These are pre-computed by the caller and passed as audit properties.
            # The computed resolution_key matches the audit property key directly.
            elif resolution_key in (
                "action.reset_url", "action.verify_url", "action.accept_url",
                "action.secure_account_url", "action.workspace_url",
                "action.expires_in",
            ):
                result[code] = str(audit_entry.properties.get(resolution_key, ""))

            # ── platform settings pass-through ───────────────────────────────
            elif resolution_key in ("platform.unsubscribe_url",):
                result[code] = (
                    f"{base_url}/settings/notifications" if base_url
                    else "/settings/notifications"
                )

        return result

    async def _resolve_custom_queries(
        self,
        connection: asyncpg.Connection,
        *,
        keys: list[asyncpg.Record],
        recipient_user_id: str,
        audit_entry: AuditEntry,
    ) -> dict[str, str]:
        """Execute custom SQL queries and map results to variable codes.

        Groups variable keys by query_id, fetches each query definition,
        builds bind params from context, executes with timeout/read-only,
        and maps result columns to their variable codes.
        """
        import json as _json

        # Group keys by query_id
        by_query: dict[str, list[asyncpg.Record]] = {}
        for row in keys:
            query_id = row.get("query_id")
            if query_id:
                by_query.setdefault(str(query_id), []).append(row)

        if not by_query:
            return {}

        result: dict[str, str] = {}

        # Build context values available for binding.
        # For each entity type, fall back to audit_entry.entity_id when the
        # explicit property key is absent — e.g. a task_created event stores the
        # task UUID as entity_id (entity_type="task") rather than a property.
        entity_type = audit_entry.entity_type or ""
        entity_id   = audit_entry.entity_id   or ""

        def _entity_id_for(key: str) -> str:
            """Return explicit property value, or entity_id when entity_type matches."""
            from_prop = audit_entry.properties.get(key, "")
            if from_prop:
                return from_prop
            if entity_type == key:
                return entity_id
            return ""

        context = {
            "$user_id":      recipient_user_id,
            "$tenant_key":   audit_entry.properties.get("tenant_key", "") or audit_entry.tenant_key or "",
            "$actor_id":     audit_entry.actor_id or "",
            "$org_id":       _entity_id_for("org") or audit_entry.properties.get("org_id", ""),
            "$workspace_id": _entity_id_for("workspace") or audit_entry.properties.get("workspace_id", ""),
            "$framework_id": _entity_id_for("framework") or audit_entry.properties.get("framework_id", ""),
            "$control_id":   _entity_id_for("control") or audit_entry.properties.get("control_id", ""),
            "$task_id":      _entity_id_for("task") or audit_entry.properties.get("task_id", ""),
            "$risk_id":      _entity_id_for("risk") or audit_entry.properties.get("risk_id", ""),
        }

        for query_id, var_keys in by_query.items():
            try:
                # Fetch query definition
                query_row = await connection.fetchrow(
                    f"""SELECT sql_template, bind_params::text, result_columns::text, timeout_ms
                    FROM {SCHEMA}."31_fct_variable_queries"
                    WHERE id = $1 AND is_active = TRUE AND is_deleted = FALSE""",
                    query_id,
                )
                if not query_row:
                    continue

                bind_params = _json.loads(query_row["bind_params"])
                result_columns = _json.loads(query_row["result_columns"])
                timeout_ms = query_row["timeout_ms"]

                # Build ordered positional params
                sorted_params = sorted(bind_params, key=lambda p: p["position"])
                ordered: list = []
                skip = False
                for bp in sorted_params:
                    value = context.get(bp["key"]) or bp.get("default_value")
                    if not value and bp.get("required", False):
                        skip = True
                        break
                    ordered.append(value or None)

                if skip:
                    # Use default values for all columns
                    for col in result_columns:
                        code = f"custom.{var_keys[0]['code'].split('.')[1]}.{col['name']}" if var_keys else ""
                        # Find the matching variable key
                        for vk in var_keys:
                            if vk["resolution_key"] == col["name"]:
                                result[vk["code"]] = col.get("default_value", "")
                    continue

                # Execute with safety guards
                await connection.execute(f"SET LOCAL statement_timeout = '{timeout_ms}'")
                await connection.execute("SET LOCAL default_transaction_read_only = ON")

                rows = await connection.fetch(query_row["sql_template"], *ordered)

                # Reset read-only (we're in a wider transaction)
                await connection.execute("SET LOCAL default_transaction_read_only = OFF")

                if rows:
                    first_row = dict(rows[0])
                    # Map result columns to variable codes
                    for vk in var_keys:
                        col_name = vk["resolution_key"]
                        if col_name and col_name in first_row:
                            val = first_row[col_name]
                            result[vk["code"]] = str(val) if val is not None else ""
                else:
                    # No rows — use default values
                    for col in result_columns:
                        for vk in var_keys:
                            if vk["resolution_key"] == col["name"]:
                                result[vk["code"]] = col.get("default_value", "")

            except Exception as exc:
                _LOGGER.warning("Custom query %s failed: %s", query_id, exc)
                # Fall back to defaults on any error
                try:
                    result_columns = _json.loads(query_row["result_columns"]) if query_row else []
                except Exception:
                    result_columns = []
                for col in result_columns:
                    for vk in var_keys:
                        if vk["resolution_key"] == col.get("name"):
                            result[vk["code"]] = col.get("default_value", "")

        return result
