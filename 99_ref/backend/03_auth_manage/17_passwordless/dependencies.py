from __future__ import annotations

from fastapi import Request

from .service import PasswordlessService


def get_passwordless_service(request: Request) -> PasswordlessService:
    return PasswordlessService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
