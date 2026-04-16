"""FastAPI dependencies for the global library module."""

from __future__ import annotations

from fastapi import Request

from .service import GlobalLibraryService


def get_global_library_service(request: Request) -> GlobalLibraryService:
    return GlobalLibraryService(database_pool=request.app.state.database_pool)
