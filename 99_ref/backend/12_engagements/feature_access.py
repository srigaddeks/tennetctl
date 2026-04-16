from __future__ import annotations

from importlib import import_module

import asyncpg

_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")

load_settings = _settings_module.load_settings
ServiceUnavailableError = _errors_module.ServiceUnavailableError


def _flag_env_column(environment: str) -> str:
    env = (environment or "").strip().lower()
    if env in {"local", "development", "dev", "test"}:
        return "env_dev"
    if env == "staging":
        return "env_staging"
    return "env_prod"


async def is_feature_flag_enabled(connection: asyncpg.Connection, *, flag_code: str) -> bool:
    settings = load_settings()
    env_column = _flag_env_column(settings.environment)
    row = await connection.fetchrow(
        f"""
        SELECT {env_column} AS enabled
        FROM "03_auth_manage"."14_dim_feature_flags"
        WHERE code = $1
        """,
        flag_code,
    )
    if not row:
        return False
    return bool(row["enabled"])


async def require_feature_flag_enabled(connection: asyncpg.Connection, *, flag_code: str, message: str) -> None:
    enabled = await is_feature_flag_enabled(connection, flag_code=flag_code)
    if not enabled:
        raise ServiceUnavailableError(message)
