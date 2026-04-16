"""
PdfTemplateService — CRUD and file-upload logic for PDF report templates.
"""
from __future__ import annotations

from importlib import import_module

import asyncpg

from .models import PdfTemplateRecord
from .repository import PdfTemplateRepository
from .schemas import (
    CreatePdfTemplateRequest,
    PdfTemplateListResponse,
    PdfTemplateResponse,
    UpdatePdfTemplateRequest,
)

_errors_module = import_module("backend.01_core.errors")
_logging_module = import_module("backend.01_core.logging_utils")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_storage_module = import_module("backend.09_attachments.storage")

NotFoundError = _errors_module.NotFoundError
AuthorizationError = _errors_module.AuthorizationError
get_logger = _logging_module.get_logger
require_permission = _perm_check_module.require_permission
get_storage_provider = _storage_module.get_storage_provider

_VIEW_PERM = "reports.view"
_WRITE_PERM = "reports.create"


def _to_response(record: PdfTemplateRecord) -> PdfTemplateResponse:
    return PdfTemplateResponse(
        id=record.id,
        tenant_key=record.tenant_key,
        name=record.name,
        description=record.description,
        cover_style=record.cover_style,
        primary_color=record.primary_color,
        secondary_color=record.secondary_color,
        header_text=record.header_text,
        footer_text=record.footer_text,
        prepared_by=record.prepared_by,
        doc_ref_prefix=record.doc_ref_prefix,
        classification_label=record.classification_label,
        applicable_report_types=record.applicable_report_types,
        is_default=record.is_default,
        shell_file_key=record.shell_file_key,
        shell_file_name=record.shell_file_name,
        created_by=record.created_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


class PdfTemplateService:

    def __init__(self, settings, database_pool: asyncpg.Pool):
        self._settings = settings
        self._pool = database_pool
        self._repo = PdfTemplateRepository()
        self._log = get_logger(__name__)

    async def create_template(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreatePdfTemplateRequest,
    ) -> PdfTemplateResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, _WRITE_PERM)
            if request.is_default:
                await self._repo.unset_defaults_for_types(
                    conn, tenant_key, request.applicable_report_types
                )
            record = await self._repo.create(
                conn,
                tenant_key=tenant_key,
                name=request.name,
                description=request.description,
                cover_style=request.cover_style,
                primary_color=request.primary_color,
                secondary_color=request.secondary_color,
                header_text=request.header_text,
                footer_text=request.footer_text,
                prepared_by=request.prepared_by,
                doc_ref_prefix=request.doc_ref_prefix,
                classification_label=request.classification_label,
                applicable_report_types=request.applicable_report_types,
                is_default=request.is_default,
                created_by=user_id,
            )
        return _to_response(record)

    async def list_templates(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_type: str | None = None,
        is_default: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> PdfTemplateListResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, _VIEW_PERM)
            items, total = await self._repo.list(
                conn,
                tenant_key=tenant_key,
                report_type=report_type,
                is_default=is_default,
                limit=limit,
                offset=offset,
            )
        return PdfTemplateListResponse(items=[_to_response(r) for r in items], total=total)

    async def get_template(
        self,
        *,
        user_id: str,
        tenant_key: str,
        template_id: str,
    ) -> PdfTemplateResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, _VIEW_PERM)
            record = await self._repo.get(conn, template_id, tenant_key)
        if not record:
            raise NotFoundError(f"PDF template {template_id} not found")
        return _to_response(record)

    async def update_template(
        self,
        *,
        user_id: str,
        tenant_key: str,
        template_id: str,
        request: UpdatePdfTemplateRequest,
    ) -> PdfTemplateResponse:
        fields = {
            k: v for k, v in request.model_dump(exclude_unset=True).items()
            if v is not None
        }
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, _WRITE_PERM)
            if fields.get("is_default"):
                types = fields.get("applicable_report_types") or []
                await self._repo.unset_defaults_for_types(
                    conn, tenant_key, types, exclude_id=template_id
                )
            record = await self._repo.update(conn, template_id, tenant_key, fields)
        if not record:
            raise NotFoundError(f"PDF template {template_id} not found")
        return _to_response(record)

    async def set_default(
        self,
        *,
        user_id: str,
        tenant_key: str,
        template_id: str,
    ) -> PdfTemplateResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, _WRITE_PERM)
            record = await self._repo.get(conn, template_id, tenant_key)
            if not record:
                raise NotFoundError(f"PDF template {template_id} not found")
            await self._repo.unset_defaults_for_types(
                conn, tenant_key, record.applicable_report_types, exclude_id=template_id
            )
            updated = await self._repo.update(
                conn, template_id, tenant_key, {"is_default": True}
            )
        return _to_response(updated)

    async def upload_shell_pdf(
        self,
        *,
        user_id: str,
        tenant_key: str,
        template_id: str,
        file_data: bytes,
        filename: str,
    ) -> PdfTemplateResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, _WRITE_PERM)
            record = await self._repo.get(conn, template_id, tenant_key)
            if not record:
                raise NotFoundError(f"PDF template {template_id} not found")

        storage = get_storage_provider(self._settings)
        storage_key = f"pdf-templates/{tenant_key}/{template_id}/shell.pdf"

        # Delete old shell if present
        if record.shell_file_key:
            try:
                await storage.delete(record.shell_file_key)
            except Exception:
                pass

        await storage.upload(
            file_data=file_data,
            storage_key=storage_key,
            content_type="application/pdf",
            metadata={"template_id": template_id, "tenant_key": tenant_key},
        )

        async with self._pool.acquire() as conn:
            updated = await self._repo.set_shell_file(
                conn, template_id, tenant_key, storage_key, filename
            )
        return _to_response(updated)

    async def delete_template(
        self,
        *,
        user_id: str,
        tenant_key: str,
        template_id: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, _WRITE_PERM)
            record = await self._repo.delete(conn, template_id, tenant_key)

        if not record:
            raise NotFoundError(f"PDF template {template_id} not found")

        if record.shell_file_key:
            storage = get_storage_provider(self._settings)
            try:
                await storage.delete(record.shell_file_key)
            except Exception:
                self._log.warning("Failed to delete shell file %s", record.shell_file_key)

    async def get_default_for_type(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_type: str,
    ) -> PdfTemplateResponse | None:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, _VIEW_PERM)
            record = await self._repo.get_default_for_type(conn, tenant_key, report_type)
        return _to_response(record) if record else None
