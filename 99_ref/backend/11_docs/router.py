"""FastAPI router for the Document Library API (prefix /api/v1/docs).

Static sub-paths (/categories, /global, /org, /global/upload, /org/upload)
are declared BEFORE parameterised routes (/{doc_id}/...) to prevent FastAPI
from interpreting a literal path segment as a UUID parameter.

GET  /docs/categories        — list categories (auth only, no permission needed)
GET  /docs/global            — list global docs  (docs.view)
GET  /docs/org               — list org docs     (docs.view, requires org_id query param)
POST /docs/global/upload     — upload global doc (docs.manage — super admin only)
POST /docs/org/upload        — upload org doc    (docs.create — org admin)
GET  /docs/{doc_id}/download — presigned URL     (docs.view)
PATCH /docs/{doc_id}         — update metadata   (docs.update)
DELETE /docs/{doc_id}        — soft delete       (docs.delete)
"""
from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Form, Query, Request, UploadFile, status

from .dependencies import get_document_service
from .schemas import (
    DocCategoryResponse,
    DocumentListResponse,
    DocumentResponse,
    PresignedDownloadResponse,
    UpdateDocumentRequest,
    UploadDocumentResponse,
    DocHistoryResponse,
)
from .service import DocumentService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_errors_module = import_module("backend.01_core.errors")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
require_permission = _perm_check_module.require_permission
AuthorizationError = _errors_module.AuthorizationError

router = InstrumentedAPIRouter(prefix="/api/v1/docs", tags=["docs"])


def _get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


async def _require_org_document_upload_access(
    connection,
    *,
    user_id: str,
    org_id: str,
) -> None:
    """Allow uploads for explicit document writers and org admins."""
    try:
        await require_permission(connection, user_id, "docs.create", scope_org_id=org_id)
    except AuthorizationError:
        await require_permission(connection, user_id, "org_management.update", scope_org_id=org_id)


async def _require_global_document_read_access(
    connection,
    *,
    user_id: str,
) -> None:
    """Allow reads for document viewers and global library managers."""
    try:
        await require_permission(connection, user_id, "docs.view")
    except AuthorizationError:
        await require_permission(connection, user_id, "docs.manage")


# ---------------------------------------------------------------------------
# GET /docs/categories — list document categories (auth only, no perm check)
# NOTE: must be before /docs/{doc_id} to prevent routing shadow
# ---------------------------------------------------------------------------

@router.get("/categories", response_model=list[DocCategoryResponse])
async def list_categories(
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
) -> list[DocCategoryResponse]:
    """Return all active document categories for form building."""
    return await service.list_categories()


# ---------------------------------------------------------------------------
# GET /docs/global — list global documents
# NOTE: must be before /docs/{doc_id} to prevent routing shadow
# ---------------------------------------------------------------------------

@router.get("/global", response_model=DocumentListResponse)
async def list_global_docs(
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
    category_code: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, max_length=200, description="Full-text search on title/description"),
    tags: str | None = Query(None, description="Comma-separated tags to filter by"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    include_all: bool = Query(default=False, description="Include invisible docs (requires docs.manage)"),
) -> DocumentListResponse:
    """List all non-deleted global documents. Requires docs.view permission."""
    async with service._database_pool.acquire() as conn:
        await _require_global_document_read_access(conn, user_id=claims.subject)
        include_invisible = False
        if include_all:
            try:
                await require_permission(conn, claims.subject, "docs.manage")
                include_invisible = True
            except Exception:
                pass
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    return await service.list_global_docs(
        tenant_key=claims.tenant_key,
        category_code=category_code,
        search=search,
        tags=tag_list,
        page=page,
        per_page=per_page,
        include_invisible=include_invisible,
    )


# ---------------------------------------------------------------------------
# GET /docs/org — list org documents
# NOTE: must be before /docs/{doc_id} to prevent routing shadow
# ---------------------------------------------------------------------------

@router.get("/org", response_model=DocumentListResponse)
async def list_org_docs(
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organisation UUID"),
    category_code: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, max_length=200, description="Full-text search on title/description"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    include_all: bool = Query(default=False, description="Include invisible docs (requires docs.manage)"),
) -> DocumentListResponse:
    """List non-deleted documents belonging to a specific organisation. Requires docs.view permission."""
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "docs.view", scope_org_id=org_id)
        include_invisible = False
        if include_all:
            try:
                await require_permission(conn, claims.subject, "docs.manage")
                include_invisible = True
            except Exception:
                pass
    return await service.list_org_docs(
        tenant_key=claims.tenant_key,
        org_id=org_id,
        category_code=category_code,
        search=search,
        page=page,
        per_page=per_page,
        include_invisible=include_invisible,
    )


# ---------------------------------------------------------------------------
# POST /docs/global/upload — upload a global document (super admin only)
# NOTE: must be before /docs/{doc_id} to prevent routing shadow
# ---------------------------------------------------------------------------

@router.post("/global/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_global_doc(
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
    file: UploadFile = ...,
    title: str = Form(..., min_length=1, max_length=500),
    category_code: str = Form(...),
    description: str | None = Form(default=None),
    tags: str = Form(default=""),
    version_label: str | None = Form(default=None),
) -> UploadDocumentResponse:
    """Upload a document to the global library. Requires docs.manage permission (super admin only)."""
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "docs.manage")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    return await service.upload_document(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        scope="global",
        org_id=None,
        category_code=category_code,
        title=title,
        description=description,
        tags=tag_list,
        version_label=version_label,
        file=file,
    )


# ---------------------------------------------------------------------------
# POST /docs/org/upload — upload an org-scoped document
# NOTE: must be before /docs/{doc_id} to prevent routing shadow
# ---------------------------------------------------------------------------

@router.post("/org/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_org_doc(
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
    file: UploadFile = ...,
    org_id: str = Form(...),
    title: str = Form(..., min_length=1, max_length=500),
    category_code: str = Form(...),
    description: str | None = Form(default=None),
    tags: str = Form(default=""),
    version_label: str | None = Form(default=None),
) -> UploadDocumentResponse:
    """Upload a document to an org's library. Requires docs.create or org admin access."""
    async with service._database_pool.acquire() as conn:
        await _require_org_document_upload_access(
            conn,
            user_id=claims.subject,
            org_id=org_id,
        )
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    return await service.upload_document(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        scope="org",
        org_id=org_id,
        category_code=category_code,
        title=title,
        description=description,
        tags=tag_list,
        version_label=version_label,
        file=file,
    )


# ---------------------------------------------------------------------------
# GET /docs/{doc_id}/download — generate presigned download URL
# NOTE: must be before /docs/{doc_id} to avoid routing collision
# ---------------------------------------------------------------------------

@router.get("/{doc_id}/download", response_model=PresignedDownloadResponse)
async def get_download_url(
    doc_id: str,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
) -> PresignedDownloadResponse:
    """Generate a presigned download URL valid for 1 hour. Requires docs.view permission."""
    async with service._database_pool.acquire() as conn:
        await _require_global_document_read_access(conn, user_id=claims.subject)
    return await service.get_download_url(
        doc_id=doc_id,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        client_ip=_get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


# ---------------------------------------------------------------------------
# PATCH /docs/{doc_id} — update document metadata
# ---------------------------------------------------------------------------

@router.patch("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: str,
    body: UpdateDocumentRequest,
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
) -> DocumentResponse:
    """Update document title, description, tags, version label, or category. Requires docs.update."""
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "docs.update")
    return await service.update_document(
        doc_id=doc_id,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=body,
    )


# ---------------------------------------------------------------------------
# DELETE /docs/{doc_id} — soft delete a document
# ---------------------------------------------------------------------------

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Soft-delete a document. Requires docs.delete permission."""
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "docs.delete")
    await service.delete_document(
        doc_id=doc_id,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
    )


# ---------------------------------------------------------------------------
# POST /docs/{doc_id}/replace — replace document file content
# ---------------------------------------------------------------------------

@router.post("/{doc_id}/replace", response_model=DocumentResponse)
async def replace_document(
    doc_id: str,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    claims=Depends(get_current_access_claims),
    file: UploadFile = ...,
) -> DocumentResponse:
    """Replace the file content of an existing document. Requires docs.update permission."""
    async with service._database_pool.acquire() as conn:
        # We use docs.update as the permission for replacing content
        await require_permission(conn, claims.subject, "docs.update")
    
    return await service.replace_document(
        doc_id=doc_id,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        file=file,
    )


@router.get("/{doc_id}/history", response_model=DocHistoryResponse)
async def get_document_history(
    doc_id: str,
    claims=Depends(get_current_access_claims),
    service: DocumentService = Depends(get_document_service),
) -> DocHistoryResponse:
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "docs.view")
    return await service.list_history(tenant_key=claims.tenant_key, doc_id=doc_id)


@router.post("/{doc_id}/revert/{event_id}", response_model=DocumentResponse)
async def revert_document(
    doc_id: str,
    event_id: str,
    claims=Depends(get_current_access_claims),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "docs.update")
    return await service.revert_to_version(
        tenant_key=claims.tenant_key,
        doc_id=doc_id,
        event_id=event_id,
        user_id=claims.subject,
    )

