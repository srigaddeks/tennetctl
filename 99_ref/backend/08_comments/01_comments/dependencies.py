from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.08_comments.01_comments.service")
CommentService = _service_module.CommentService


def get_comment_service(request: Request) -> CommentService:
    return CommentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
