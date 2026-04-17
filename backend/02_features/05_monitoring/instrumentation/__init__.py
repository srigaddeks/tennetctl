"""Auto-instrumentation package.

Exports ``install_all(app, pool, config)`` — the single entry point wired
from ``backend.main.lifespan``. Each submodule (fastapi, asyncpg,
structlog_bridge) can also be installed individually for tests.

Recursion guard: ``_in_monitoring_bridge`` is a ContextVar shared across all
three bridges so that any publish triggered from inside instrumentation
short-circuits instead of looping.
"""

from __future__ import annotations

from contextvars import ContextVar
from importlib import import_module
from typing import Any

_in_monitoring_bridge: ContextVar[bool] = ContextVar(
    "_in_monitoring_bridge", default=False
)


def install_all(app: Any, pool: Any, config: Any) -> None:
    """Install FastAPI middleware + asyncpg hook + structlog bridge."""
    _fastapi: Any = import_module(
        "backend.02_features.05_monitoring.instrumentation.fastapi"
    )
    _asyncpg: Any = import_module(
        "backend.02_features.05_monitoring.instrumentation.asyncpg"
    )
    _bridge: Any = import_module(
        "backend.02_features.05_monitoring.instrumentation.structlog_bridge"
    )

    _fastapi.install(app, config)
    _asyncpg.install(pool)
    _bridge.install()


__all__ = ["install_all", "_in_monitoring_bridge"]
