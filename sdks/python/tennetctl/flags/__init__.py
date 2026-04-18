"""
tennetctl.flags — Python SDK for feature flag evaluation.

Usage:
    from tennetctl.flags import Client

    client = Client(base_url="http://localhost:51734", api_key="nk_...", environment="prod")
    is_on = client.evaluate("new_checkout_flow", user_id="u-123", org_id="o-456")
    variant = client.evaluate("homepage_variant", user_id="u-123", default="control")
    bulk = client.evaluate_bulk(["flag_a", "flag_b"], user_id="u-123")
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import Any, Literal

import httpx

Environment = Literal["dev", "staging", "prod", "test"]


@dataclass(frozen=True, slots=True)
class EvalResult:
    value: Any
    reason: str
    flag_id: str | None = None
    flag_scope: str | None = None
    rule_id: str | None = None
    override_id: str | None = None


@dataclass(slots=True)
class _CacheEntry:
    result: EvalResult
    expires_at: float


def _cache_key(flag_key: str, env: str, ctx: dict[str, Any]) -> str:
    canon = json.dumps([flag_key, env, ctx], sort_keys=True, default=str)
    return hashlib.sha256(canon.encode()).hexdigest()[:32]


class Client:
    """Synchronous feature flag evaluation client.

    Uses httpx with a small in-process SWR cache (60s TTL by default) so
    repeated evaluations for the same context are near-zero-latency.
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        environment: Environment = "prod",
        cache_ttl_seconds: float = 60.0,
        timeout_seconds: float = 3.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._environment = environment
        self._cache_ttl = cache_ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}
        self._cache_lock = threading.Lock()
        headers: dict[str, str] = {"content-type": "application/json"}
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(timeout=timeout_seconds, headers=headers)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def evaluate(
        self,
        flag_key: str,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        application_id: str | None = None,
        attrs: dict[str, Any] | None = None,
        default: Any = None,
        environment: Environment | None = None,
    ) -> Any:
        """Evaluate a single flag. Returns the resolved value or `default`
        on flag_not_found / network error."""
        result = self.evaluate_detailed(
            flag_key,
            user_id=user_id,
            org_id=org_id,
            workspace_id=workspace_id,
            application_id=application_id,
            attrs=attrs,
            environment=environment,
        )
        if result is None or result.reason == "flag_not_found":
            return default
        return result.value

    def evaluate_detailed(
        self,
        flag_key: str,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        application_id: str | None = None,
        attrs: dict[str, Any] | None = None,
        environment: Environment | None = None,
    ) -> EvalResult | None:
        """Evaluate and return the full result including reason/rule_id.
        Returns None on network error."""
        env = environment or self._environment
        ctx = {
            "user_id": user_id,
            "org_id": org_id,
            "workspace_id": workspace_id,
            "application_id": application_id,
            "attrs": attrs or {},
        }
        key = _cache_key(flag_key, env, ctx)

        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is not None and entry.expires_at > time.monotonic():
                return entry.result

        try:
            resp = self._client.post(
                f"{self._base_url}/v1/evaluate",
                json={
                    "flag_key": flag_key,
                    "environment": env,
                    "context": ctx,
                },
            )
            resp.raise_for_status()
            payload = resp.json()
            if not payload.get("ok"):
                return None
            data = payload["data"]
            result = EvalResult(
                value=data.get("value"),
                reason=data.get("reason", "unknown"),
                flag_id=data.get("flag_id"),
                flag_scope=data.get("flag_scope"),
                rule_id=data.get("rule_id"),
                override_id=data.get("override_id"),
            )
        except (httpx.HTTPError, ValueError, KeyError):
            return None

        with self._cache_lock:
            self._cache[key] = _CacheEntry(
                result=result,
                expires_at=time.monotonic() + self._cache_ttl,
            )
        return result

    def evaluate_bulk(
        self,
        flag_keys: list[str],
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        application_id: str | None = None,
        attrs: dict[str, Any] | None = None,
        environment: Environment | None = None,
    ) -> dict[str, Any]:
        """Evaluate many flags against the same context. Returns {flag_key: value}."""
        return {
            k: self.evaluate(
                k,
                user_id=user_id,
                org_id=org_id,
                workspace_id=workspace_id,
                application_id=application_id,
                attrs=attrs,
                environment=environment,
            )
            for k in flag_keys
        }

    def invalidate_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()


class AsyncClient:
    """Async flag evaluation client — mirror of Client, uses httpx.AsyncClient."""

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        environment: Environment = "prod",
        cache_ttl_seconds: float = 60.0,
        timeout_seconds: float = 3.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._environment = environment
        self._cache_ttl = cache_ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}
        self._cache_lock = asyncio.Lock()
        headers: dict[str, str] = {"content-type": "application/json"}
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(timeout=timeout_seconds, headers=headers)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def evaluate(
        self,
        flag_key: str,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        application_id: str | None = None,
        attrs: dict[str, Any] | None = None,
        default: Any = None,
        environment: Environment | None = None,
    ) -> Any:
        result = await self.evaluate_detailed(
            flag_key,
            user_id=user_id,
            org_id=org_id,
            workspace_id=workspace_id,
            application_id=application_id,
            attrs=attrs,
            environment=environment,
        )
        if result is None or result.reason == "flag_not_found":
            return default
        return result.value

    async def evaluate_detailed(
        self,
        flag_key: str,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        application_id: str | None = None,
        attrs: dict[str, Any] | None = None,
        environment: Environment | None = None,
    ) -> EvalResult | None:
        env = environment or self._environment
        ctx = {
            "user_id": user_id,
            "org_id": org_id,
            "workspace_id": workspace_id,
            "application_id": application_id,
            "attrs": attrs or {},
        }
        key = _cache_key(flag_key, env, ctx)

        async with self._cache_lock:
            entry = self._cache.get(key)
            if entry is not None and entry.expires_at > time.monotonic():
                return entry.result

        try:
            resp = await self._client.post(
                f"{self._base_url}/v1/evaluate",
                json={
                    "flag_key": flag_key,
                    "environment": env,
                    "context": ctx,
                },
            )
            resp.raise_for_status()
            payload = resp.json()
            if not payload.get("ok"):
                return None
            data = payload["data"]
            result = EvalResult(
                value=data.get("value"),
                reason=data.get("reason", "unknown"),
                flag_id=data.get("flag_id"),
                flag_scope=data.get("flag_scope"),
                rule_id=data.get("rule_id"),
                override_id=data.get("override_id"),
            )
        except (httpx.HTTPError, ValueError, KeyError):
            return None

        async with self._cache_lock:
            self._cache[key] = _CacheEntry(
                result=result,
                expires_at=time.monotonic() + self._cache_ttl,
            )
        return result


__all__ = ["Client", "AsyncClient", "EvalResult", "Environment"]
