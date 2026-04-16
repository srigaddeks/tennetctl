from __future__ import annotations

from collections import deque
from importlib import import_module
import json
import threading
import time

from starlette.datastructures import Headers, MutableHeaders


_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger
_LOGGER = get_logger("backend.rate_limit")


class SlidingWindowRateLimiter:
    """
    In-memory sliding-window rate limiter keyed by client identifier.

    Tracks request timestamps per key within a rolling window. When the
    count exceeds ``max_requests``, further requests are denied until
    older entries fall outside the window.

    Thread-safe via a lock per key bucket.
    """

    def __init__(self, *, max_requests: int, window_seconds: int = 60) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> tuple[bool, int, int]:
        """
        Check if a request from *key* is allowed.

        Returns:
            (allowed, remaining, reset_after_seconds)
        """
        now = time.monotonic()
        cutoff = now - self._window_seconds

        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = deque()
                self._buckets[key] = bucket

            # Trim expired entries
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            remaining = max(0, self._max_requests - len(bucket))
            if len(bucket) >= self._max_requests:
                reset_after = int(bucket[0] - cutoff) + 1 if bucket else self._window_seconds
                return False, 0, reset_after

            bucket.append(now)
            remaining = max(0, self._max_requests - len(bucket))
            return True, remaining, self._window_seconds

    def cleanup(self) -> int:
        """Remove expired entries. Returns number of keys cleaned up."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        removed = 0
        with self._lock:
            empty_keys = []
            for key, bucket in self._buckets.items():
                while bucket and bucket[0] <= cutoff:
                    bucket.popleft()
                if not bucket:
                    empty_keys.append(key)
            for key in empty_keys:
                del self._buckets[key]
                removed += 1
        return removed


def _extract_client_ip(scope: dict) -> str:
    """Extract client IP from ASGI scope, respecting X-Forwarded-For."""
    headers = Headers(scope=scope)
    forwarded_for = headers.get("x-forwarded-for", "")
    if forwarded_for:
        parts = [p.strip() for p in forwarded_for.split(",") if p.strip()]
        if parts:
            return parts[0]
    real_ip = headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    client = scope.get("client")
    if client:
        return client[0]
    return "unknown"


class RateLimitMiddleware:
    """
    ASGI middleware that enforces per-IP rate limiting.

    Adds standard rate-limit headers to every response:
    - X-RateLimit-Limit
    - X-RateLimit-Remaining
    - X-RateLimit-Reset

    Returns 429 Too Many Requests with Retry-After header when exceeded.
    """

    def __init__(
        self,
        app,
        *,
        max_requests: int = 60,
        window_seconds: int = 60,
        exclude_paths: tuple[str, ...] = (),
    ) -> None:
        self.app = app
        self._limiter = SlidingWindowRateLimiter(max_requests=max_requests, window_seconds=window_seconds)
        self._max_requests = max_requests
        self._exclude_paths = exclude_paths

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")
        if any(path == p or path.startswith(p + "/") for p in self._exclude_paths):
            await self.app(scope, receive, send)
            return

        client_ip = _extract_client_ip(scope)
        allowed, remaining, reset_after = self._limiter.is_allowed(client_ip)

        if not allowed:
            _LOGGER.warning(
                "rate_limit_exceeded",
                extra={
                    "action": "rate_limit.check",
                    "outcome": "denied",
                    "client_ip": client_ip,
                    "path": path,
                    "reset_after": reset_after,
                },
            )
            body = json.dumps({
                "error": {
                    "code": "rate_limited",
                    "message": "Too many requests. Please try again later.",
                },
            }).encode()
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", str(reset_after).encode()),
                    (b"x-ratelimit-limit", str(self._max_requests).encode()),
                    (b"x-ratelimit-remaining", b"0"),
                    (b"x-ratelimit-reset", str(reset_after).encode()),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        async def send_with_headers(message) -> None:
            if message["type"] == "http.response.start":
                mutable_headers = MutableHeaders(raw=message["headers"])
                mutable_headers["X-RateLimit-Limit"] = str(self._max_requests)
                mutable_headers["X-RateLimit-Remaining"] = str(remaining)
                mutable_headers["X-RateLimit-Reset"] = str(reset_after)
            await send(message)

        await self.app(scope, receive, send_with_headers)
