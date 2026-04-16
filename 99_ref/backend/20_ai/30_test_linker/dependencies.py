from __future__ import annotations

from fastapi import Request

from .service import TestLinkerService


def get_test_linker_service(request: Request) -> TestLinkerService:
    return TestLinkerService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )
