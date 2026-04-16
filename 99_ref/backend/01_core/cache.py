from __future__ import annotations

import json
from importlib import import_module
from typing import Any

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
start_operation_span = _telemetry_module.start_operation_span

_LOGGER = get_logger("backend.cache")


class CacheManager:
    """Redis/Valkey-backed cache with JSON serialization and pattern invalidation."""

    def __init__(self, *, url: str, key_prefix: str = "kcontrol:", default_ttl: int = 300) -> None:
        import redis.asyncio as aioredis

        self._client = aioredis.from_url(url, decode_responses=True)
        self._prefix = key_prefix
        self._default_ttl = default_ttl

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> str | None:
        with start_operation_span("cache.get", attributes={"cache.key": key}):
            try:
                value = await self._client.get(self._key(key))
                if value is not None:
                    _LOGGER.debug("cache_hit", extra={"cache_key": key})
                else:
                    _LOGGER.debug("cache_miss", extra={"cache_key": key})
                return value
            except Exception:
                _LOGGER.warning("cache_get_failed", extra={"cache_key": key})
                return None

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        with start_operation_span("cache.set", attributes={"cache.key": key, "cache.ttl": ttl}):
            try:
                await self._client.set(self._key(key), value, ex=ttl)
                _LOGGER.debug("cache_set", extra={"cache_key": key, "cache_ttl": ttl})
            except Exception:
                _LOGGER.warning("cache_set_failed", extra={"cache_key": key})

    async def get_json(self, key: str) -> Any | None:
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    async def set_json(self, key: str, data: Any, ttl_seconds: int | None = None) -> None:
        await self.set(key, json.dumps(data, default=str), ttl_seconds)

    async def delete(self, *keys: str) -> None:
        if not keys:
            return
        full_keys = [self._key(k) for k in keys]
        with start_operation_span("cache.delete", attributes={"cache.key_count": len(full_keys)}):
            try:
                await self._client.delete(*full_keys)
                _LOGGER.info("cache_invalidate", extra={"cache_keys": list(keys)})
            except Exception:
                _LOGGER.warning("cache_delete_failed", extra={"cache_keys": list(keys)})

    async def delete_pattern(self, pattern: str) -> None:
        full_pattern = self._key(pattern)
        with start_operation_span("cache.delete_pattern", attributes={"cache.pattern": pattern}):
            try:
                cursor = None
                while cursor != 0:
                    cursor, found_keys = await self._client.scan(
                        cursor=cursor or 0, match=full_pattern, count=100,
                    )
                    if found_keys:
                        await self._client.delete(*found_keys)
                        _LOGGER.info("cache_invalidate_pattern", extra={"cache_pattern": pattern, "keys_removed": len(found_keys)})
            except Exception:
                _LOGGER.warning("cache_delete_pattern_failed", extra={"cache_pattern": pattern})

    async def close(self) -> None:
        try:
            await self._client.aclose()
        except Exception:
            _LOGGER.warning("cache_close_failed")


class NullCacheManager(CacheManager):
    """No-op cache for when Redis is not configured. All reads miss, all writes are silent."""

    def __init__(self) -> None:
        self._prefix = ""
        self._default_ttl = 0

    async def get(self, key: str) -> str | None:
        return None

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        pass

    async def get_json(self, key: str) -> Any | None:
        return None

    async def set_json(self, key: str, data: Any, ttl_seconds: int | None = None) -> None:
        pass

    async def delete(self, *keys: str) -> None:
        pass

    async def delete_pattern(self, pattern: str) -> None:
        pass

    async def close(self) -> None:
        pass
