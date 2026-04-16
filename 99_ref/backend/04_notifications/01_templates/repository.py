from __future__ import annotations

from datetime import datetime

import asyncpg
from importlib import import_module

from ..models import TemplatePlaceholderRecord, TemplateRecord, TemplateVersionRecord

SCHEMA = '"03_notifications"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="notification_templates.repository", logger_name="backend.notification_templates.repository.instrumentation")
class TemplateRepository:
    async def list_templates(
        self, connection: asyncpg.Connection, *, tenant_key: str, include_test: bool = False
    ) -> list[TemplateRecord]:
        test_filter = "" if include_test else "AND is_test = FALSE"
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, code, name, description,
                   notification_type_code, channel_code, category_code,
                   active_version_id, base_template_id, org_id,
                   static_variables,
                   is_active, is_disabled, is_deleted, is_system,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."10_fct_templates"
            WHERE tenant_key = $1 AND is_deleted = FALSE {test_filter}
            ORDER BY name
            """,
            tenant_key,
        )
        return [_row_to_template(r) for r in rows]

    async def delete_template(
        self, connection: asyncpg.Connection, template_id: str, deleted_by: str
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_fct_templates"
            SET is_deleted = TRUE, deleted_at = NOW(), deleted_by = $2
            WHERE id = $1 AND is_deleted = FALSE AND is_system = FALSE
            """,
            template_id,
            deleted_by,
        )
        return result != "UPDATE 0"

    async def get_template_by_id(
        self, connection: asyncpg.Connection, template_id: str
    ) -> TemplateRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, code, name, description,
                   notification_type_code, channel_code, category_code,
                   active_version_id, base_template_id, org_id,
                   static_variables,
                   is_active, is_disabled, is_deleted, is_system,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."10_fct_templates"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            template_id,
        )
        return _row_to_template(row) if row else None

    async def get_template_by_code(
        self, connection: asyncpg.Connection, code: str, tenant_key: str
    ) -> TemplateRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, code, name, description,
                   notification_type_code, channel_code, category_code,
                   active_version_id, base_template_id, org_id,
                   static_variables,
                   is_active, is_disabled, is_deleted, is_system,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."10_fct_templates"
            WHERE code = $1 AND tenant_key = $2 AND is_deleted = FALSE
            """,
            code,
            tenant_key,
        )
        return _row_to_template(row) if row else None

    async def get_template_for_type_channel(
        self,
        connection: asyncpg.Connection,
        notification_type_code: str,
        channel_code: str,
        tenant_key: str,
    ) -> TemplateRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, code, name, description,
                   notification_type_code, channel_code, category_code,
                   active_version_id, base_template_id, org_id,
                   static_variables,
                   is_active, is_disabled, is_deleted, is_system,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."10_fct_templates"
            WHERE notification_type_code = $1
              AND channel_code = $2
              AND tenant_key = $3
              AND is_active = TRUE
              AND is_deleted = FALSE
            LIMIT 1
            """,
            notification_type_code,
            channel_code,
            tenant_key,
        )
        return _row_to_template(row) if row else None

    async def create_template(
        self,
        connection: asyncpg.Connection,
        *,
        template_id: str,
        tenant_key: str,
        code: str,
        name: str,
        description: str | None,
        notification_type_code: str,
        channel_code: str,
        base_template_id: str | None,
        org_id: str | None = None,
        static_variables: str | None = None,
        created_by: str,
        now: datetime,
    ) -> TemplateRecord:
        import json as _json
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."10_fct_templates"
                (
                    id, tenant_key, code, name, description,
                    notification_type_code, channel_code,
                    active_version_id, base_template_id, org_id,
                    static_variables,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7,
                NULL, $8, $9,
                $10::jsonb,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $11, $12, $13, $14, NULL, NULL
            )
            RETURNING id, tenant_key, code, name, description,
                      notification_type_code, channel_code, category_code,
                      active_version_id, base_template_id, org_id,
                      static_variables,
                      is_active, is_disabled, is_deleted, is_system,
                      created_at::text, updated_at::text
            """,
            template_id,
            tenant_key,
            code,
            name,
            description or "",
            notification_type_code,
            channel_code,
            base_template_id,
            org_id,
            static_variables or "{}",
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_template(row)

    async def get_template_for_type_channel_with_org(
        self,
        connection: asyncpg.Connection,
        notification_type_code: str,
        channel_code: str,
        tenant_key: str,
        org_id: str | None = None,
    ) -> TemplateRecord | None:
        """Resolve template with org-specific override fallback.

        Priority: org-specific template > platform-wide template.
        """
        if org_id:
            # Try org-specific first
            org_template = await connection.fetchrow(
                f"""
                SELECT id, tenant_key, code, name, description,
                       notification_type_code, channel_code,
                       active_version_id, base_template_id, org_id,
                       static_variables,
                       is_active, is_disabled, is_deleted, is_system,
                       created_at::text, updated_at::text
                FROM {SCHEMA}."10_fct_templates"
                WHERE notification_type_code = $1
                  AND channel_code = $2
                  AND tenant_key = $3
                  AND org_id = $4
                  AND is_active = TRUE
                  AND is_deleted = FALSE
                LIMIT 1
                """,
                notification_type_code,
                channel_code,
                tenant_key,
                org_id,
            )
            if org_template:
                return _row_to_template(org_template)

        # Fall back to platform-wide (org_id IS NULL)
        return await self.get_template_for_type_channel(
            connection, notification_type_code, channel_code, tenant_key
        )

    async def list_templates_with_org(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None = None,
        include_test: bool = False,
    ) -> list[TemplateRecord]:
        """List templates filtered by org_id. If org_id is None, returns all."""
        test_filter = "" if include_test else "AND is_test = FALSE"
        if org_id:
            rows = await connection.fetch(
                f"""
                SELECT id, tenant_key, code, name, description,
                       notification_type_code, channel_code, category_code,
                       active_version_id, base_template_id, org_id,
                       static_variables,
                       is_active, is_disabled, is_deleted, is_system,
                       created_at::text, updated_at::text
                FROM {SCHEMA}."10_fct_templates"
                WHERE tenant_key = $1 AND is_deleted = FALSE {test_filter}
                  AND (org_id = $2 OR org_id IS NULL)
                ORDER BY org_id NULLS LAST, name
                """,
                tenant_key,
                org_id,
            )
        else:
            rows = await connection.fetch(
                f"""
                SELECT id, tenant_key, code, name, description,
                       notification_type_code, channel_code, category_code,
                       active_version_id, base_template_id, org_id,
                       static_variables,
                       is_active, is_disabled, is_deleted, is_system,
                       created_at::text, updated_at::text
                FROM {SCHEMA}."10_fct_templates"
                WHERE tenant_key = $1 AND is_deleted = FALSE {test_filter}
                ORDER BY org_id NULLS LAST, name
                """,
                tenant_key,
            )
        return [_row_to_template(r) for r in rows]

    async def update_template(
        self,
        connection: asyncpg.Connection,
        template_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        is_disabled: bool | None = None,
        active_version_id: str | None = None,
        static_variables: str | None = None,
        updated_by: str,
        now: datetime,
    ) -> TemplateRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if name is not None:
            fields.append(f"name = ${idx}")
            values.append(name)
            idx += 1
        if description is not None:
            fields.append(f"description = ${idx}")
            values.append(description)
            idx += 1
        if is_disabled is not None:
            fields.append(f"is_active = ${idx}")
            values.append(not is_disabled)
            idx += 1
        if active_version_id is not None:
            fields.append(f"active_version_id = ${idx}")
            values.append(active_version_id)
            idx += 1
        if static_variables is not None:
            fields.append(f"static_variables = ${idx}::jsonb")
            values.append(static_variables)
            idx += 1

        values.append(template_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."10_fct_templates"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING id, tenant_key, code, name, description,
                      notification_type_code, channel_code, category_code,
                      active_version_id, base_template_id, org_id,
                      static_variables,
                      is_active, is_disabled, is_deleted, is_system,
                      created_at::text, updated_at::text
            """,
            *values,
        )
        return _row_to_template(row) if row else None

    async def list_versions(
        self, connection: asyncpg.Connection, template_id: str
    ) -> list[TemplateVersionRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, template_id, version_number, subject_line,
                   body_html, body_text, body_short, metadata_json,
                   change_notes, is_active, created_at::text
            FROM {SCHEMA}."14_dtl_template_versions"
            WHERE template_id = $1
            ORDER BY version_number DESC
            """,
            template_id,
        )
        return [_row_to_version(r) for r in rows]

    async def get_version(
        self, connection: asyncpg.Connection, version_id: str
    ) -> TemplateVersionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, template_id, version_number, subject_line,
                   body_html, body_text, body_short, metadata_json,
                   change_notes, is_active, created_at::text
            FROM {SCHEMA}."14_dtl_template_versions"
            WHERE id = $1
            """,
            version_id,
        )
        return _row_to_version(row) if row else None

    async def create_version(
        self,
        connection: asyncpg.Connection,
        *,
        version_id: str,
        template_id: str,
        version_number: int,
        subject_line: str | None,
        body_html: str | None,
        body_text: str | None,
        body_short: str | None,
        metadata_json: str | None,
        change_notes: str | None,
        created_by: str,
        now: datetime,
    ) -> TemplateVersionRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."14_dtl_template_versions"
                (id, template_id, version_number, subject_line,
                 body_html, body_text, body_short, metadata_json,
                 change_notes, is_active, created_at, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE, $10, $11)
            RETURNING id, template_id, version_number, subject_line,
                      body_html, body_text, body_short, metadata_json,
                      change_notes, is_active, created_at::text
            """,
            version_id,
            template_id,
            version_number,
            subject_line,
            body_html,
            body_text,
            body_short,
            metadata_json,
            change_notes,
            now,
            created_by,
        )
        return _row_to_version(row)

    async def get_next_version_number(
        self, connection: asyncpg.Connection, template_id: str
    ) -> int:
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM {SCHEMA}."14_dtl_template_versions"
            WHERE template_id = $1
            """,
            template_id,
        )
        return row["next_version"]

    async def list_placeholders(
        self, connection: asyncpg.Connection, template_id: str
    ) -> list[TemplatePlaceholderRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, template_id, variable_key_code, is_required, default_value
            FROM {SCHEMA}."15_dtl_template_placeholders"
            WHERE template_id = $1
            ORDER BY variable_key_code
            """,
            template_id,
        )
        return [_row_to_placeholder(r) for r in rows]

    async def set_placeholder(
        self,
        connection: asyncpg.Connection,
        *,
        placeholder_id: str,
        template_id: str,
        variable_key_code: str,
        is_required: bool,
        default_value: str | None,
    ) -> TemplatePlaceholderRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."15_dtl_template_placeholders"
                (id, template_id, variable_key_code, is_required, default_value,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            ON CONFLICT (template_id, variable_key_code)
            DO UPDATE SET
                is_required = EXCLUDED.is_required,
                default_value = EXCLUDED.default_value,
                updated_at = NOW()
            RETURNING id, template_id, variable_key_code, is_required, default_value
            """,
            placeholder_id,
            template_id,
            variable_key_code,
            is_required,
            default_value,
        )
        return _row_to_placeholder(row)

    async def delete_placeholder(
        self, connection: asyncpg.Connection, template_id: str, variable_key_code: str
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."15_dtl_template_placeholders"
            WHERE template_id = $1 AND variable_key_code = $2
            """,
            template_id,
            variable_key_code,
        )
        return result != "DELETE 0"

    async def list_variable_keys(self, connection: asyncpg.Connection) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT code, name, description, data_type, example_value
            FROM {SCHEMA}."08_dim_template_variable_keys"
            ORDER BY sort_order, code
            """
        )
        return [dict(r) for r in rows]


def _row_to_template(r) -> TemplateRecord:
    import json as _json
    raw_vars = r["static_variables"]
    if isinstance(raw_vars, str):
        try:
            static_vars = _json.loads(raw_vars)
        except Exception:
            static_vars = {}
    else:
        static_vars = raw_vars or {}
    return TemplateRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        code=r["code"],
        name=r["name"],
        description=r["description"],
        notification_type_code=r["notification_type_code"],
        channel_code=r["channel_code"],
        category_code=r.get("category_code"),
        active_version_id=r["active_version_id"],
        base_template_id=r["base_template_id"],
        org_id=str(r["org_id"]) if r.get("org_id") else None,
        static_variables=static_vars,
        is_active=r["is_active"],
        is_disabled=r["is_disabled"],
        is_deleted=r["is_deleted"],
        is_system=r["is_system"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_version(r) -> TemplateVersionRecord:
    return TemplateVersionRecord(
        id=r["id"],
        template_id=r["template_id"],
        version_number=r["version_number"],
        subject_line=r["subject_line"],
        body_html=r["body_html"],
        body_text=r["body_text"],
        body_short=r["body_short"],
        metadata_json=r["metadata_json"],
        change_notes=r["change_notes"],
        is_active=r["is_active"],
        created_at=r["created_at"],
    )


def _row_to_placeholder(r) -> TemplatePlaceholderRecord:
    return TemplatePlaceholderRecord(
        id=r["id"],
        template_id=r["template_id"],
        variable_key_code=r["variable_key_code"],
        is_required=r["is_required"],
        default_value=r["default_value"],
    )
