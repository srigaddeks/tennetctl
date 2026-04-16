from __future__ import annotations

import asyncpg

from .models import PdfTemplateRecord

_SCHEMA = '"20_ai"'
_TABLE = f'{_SCHEMA}."60_fct_pdf_templates"'


def _row_to_record(row) -> PdfTemplateRecord:
    return PdfTemplateRecord(
        id=str(row["id"]),
        tenant_key=row["tenant_key"],
        name=row["name"],
        description=row["description"],
        cover_style=row["cover_style"],
        primary_color=row["primary_color"],
        secondary_color=row["secondary_color"],
        header_text=row["header_text"],
        footer_text=row["footer_text"],
        prepared_by=row["prepared_by"],
        doc_ref_prefix=row["doc_ref_prefix"],
        classification_label=row["classification_label"],
        applicable_report_types=list(row["applicable_report_types"] or []),
        is_default=row["is_default"],
        shell_file_key=row["shell_file_key"],
        shell_file_name=row["shell_file_name"],
        created_by=str(row["created_by"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


class PdfTemplateRepository:

    async def create(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        name: str,
        description: str | None,
        cover_style: str,
        primary_color: str,
        secondary_color: str,
        header_text: str | None,
        footer_text: str | None,
        prepared_by: str | None,
        doc_ref_prefix: str | None,
        classification_label: str | None,
        applicable_report_types: list[str],
        is_default: bool,
        created_by: str,
    ) -> PdfTemplateRecord:
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_TABLE} (
                tenant_key, name, description, cover_style,
                primary_color, secondary_color, header_text, footer_text,
                prepared_by, doc_ref_prefix, classification_label,
                applicable_report_types, is_default, created_by
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
            RETURNING *
            """,
            tenant_key, name, description, cover_style,
            primary_color, secondary_color, header_text, footer_text,
            prepared_by, doc_ref_prefix, classification_label,
            applicable_report_types, is_default, created_by,
        )
        return _row_to_record(row)

    async def list(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        report_type: str | None = None,
        is_default: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PdfTemplateRecord], int]:
        filters = ["tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2

        if report_type is not None:
            filters.append(f"(${idx} = ANY(applicable_report_types) OR applicable_report_types = '{{}}')")
            params.append(report_type)
            idx += 1

        if is_default is not None:
            filters.append(f"is_default = ${idx}")
            params.append(is_default)
            idx += 1

        where = " AND ".join(filters)

        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM {_TABLE} WHERE {where}", *params
        )
        rows = await conn.fetch(
            f"SELECT * FROM {_TABLE} WHERE {where} ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx+1}",
            *params, limit, offset,
        )
        return [_row_to_record(r) for r in rows], total

    async def get(
        self,
        conn: asyncpg.Connection,
        template_id: str,
        tenant_key: str,
    ) -> PdfTemplateRecord | None:
        row = await conn.fetchrow(
            f"SELECT * FROM {_TABLE} WHERE id = $1 AND tenant_key = $2",
            template_id, tenant_key,
        )
        return _row_to_record(row) if row else None

    async def get_default_for_type(
        self,
        conn: asyncpg.Connection,
        tenant_key: str,
        report_type: str,
    ) -> PdfTemplateRecord | None:
        # Prefer type-specific default, fall back to global default (empty applicable_report_types)
        row = await conn.fetchrow(
            f"""
            SELECT * FROM {_TABLE}
            WHERE tenant_key = $1 AND is_default = TRUE
              AND ($2 = ANY(applicable_report_types) OR applicable_report_types = '{{}}')
            ORDER BY
                CASE WHEN $2 = ANY(applicable_report_types) THEN 0 ELSE 1 END
            LIMIT 1
            """,
            tenant_key, report_type,
        )
        return _row_to_record(row) if row else None

    async def update(
        self,
        conn: asyncpg.Connection,
        template_id: str,
        tenant_key: str,
        fields: dict,
    ) -> PdfTemplateRecord | None:
        if not fields:
            return await self.get(conn, template_id, tenant_key)

        set_clauses = ", ".join(f"{k} = ${i+3}" for i, k in enumerate(fields))
        values = list(fields.values())
        row = await conn.fetchrow(
            f"""
            UPDATE {_TABLE}
            SET {set_clauses}
            WHERE id = $1 AND tenant_key = $2
            RETURNING *
            """,
            template_id, tenant_key, *values,
        )
        return _row_to_record(row) if row else None

    async def set_shell_file(
        self,
        conn: asyncpg.Connection,
        template_id: str,
        tenant_key: str,
        shell_file_key: str,
        shell_file_name: str,
    ) -> PdfTemplateRecord | None:
        row = await conn.fetchrow(
            f"""
            UPDATE {_TABLE}
            SET shell_file_key = $3, shell_file_name = $4
            WHERE id = $1 AND tenant_key = $2
            RETURNING *
            """,
            template_id, tenant_key, shell_file_key, shell_file_name,
        )
        return _row_to_record(row) if row else None

    async def unset_defaults_for_types(
        self,
        conn: asyncpg.Connection,
        tenant_key: str,
        applicable_report_types: list[str],
        exclude_id: str | None = None,
    ) -> None:
        """Clear is_default on all templates that overlap with the given report types."""
        if not applicable_report_types:
            # Global default — unset all global defaults
            query = f"""
                UPDATE {_TABLE}
                SET is_default = FALSE
                WHERE tenant_key = $1 AND is_default = TRUE
                  AND applicable_report_types = '{{}}'
                  AND ($2::uuid IS NULL OR id != $2)
            """
            await conn.execute(query, tenant_key, exclude_id)
        else:
            query = f"""
                UPDATE {_TABLE}
                SET is_default = FALSE
                WHERE tenant_key = $1 AND is_default = TRUE
                  AND applicable_report_types && $2
                  AND ($3::uuid IS NULL OR id != $3)
            """
            await conn.execute(query, tenant_key, applicable_report_types, exclude_id)

    async def delete(
        self,
        conn: asyncpg.Connection,
        template_id: str,
        tenant_key: str,
    ) -> PdfTemplateRecord | None:
        row = await conn.fetchrow(
            f"DELETE FROM {_TABLE} WHERE id = $1 AND tenant_key = $2 RETURNING *",
            template_id, tenant_key,
        )
        return _row_to_record(row) if row else None
