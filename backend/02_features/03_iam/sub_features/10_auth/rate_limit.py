"""
iam.auth — IP-based rate limiter for unauthenticated endpoints (Plan 38-01).

Postgres-native fixed-window counter. Intentionally simple: UPSERT on
(endpoint, ip, window_start) with atomic increment; window_start is
`date_trunc`-equivalent via floor(epoch/window). Decoupled from the caller's
transaction — uses a fresh pool connection so the counter commits even if the
auth request rolls back.

Valkey-first path (INCR + EXPIRE on authrl:{endpoint}:{ip}:{bucket}) is
deferred until Valkey is wired into app.state; see plan 38-01 boundaries.
The FastAPI dependency is the only public surface — endpoints apply it via
Depends(auth_rate_limit("endpoint", max=N, window=S)).

Denied requests emit `iam.auth.rate_limited` fire-and-forget on a detached
connection so the audit write lands even when the HTTP response is 429.
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import Request

_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")


_TABLE = '"03_iam"."60_evt_auth_rate_limit_window"'


def _client_ip(request: Request) -> str:
    """Extract the best-effort client IP.

    Prefers X-Forwarded-For's first hop when present (trusted proxy deployment).
    Falls back to the direct socket peer. Returns the literal string "unknown"
    when neither is available — we still rate-limit that bucket so a
    misconfigured proxy doesn't open the floodgates.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def _increment_window(
    pool: Any,
    *,
    endpoint: str,
    ip: str,
    window_seconds: int,
) -> int:
    """Bump the counter for the current window and return the post-increment count."""
    async with pool.acquire() as fresh:
        row = await fresh.fetchrow(
            f"""
            INSERT INTO {_TABLE} (endpoint, ip, window_start, count, first_seen_at, last_seen_at)
            VALUES (
                $1, $2,
                date_trunc('second', CURRENT_TIMESTAMP)
                    - make_interval(secs =>
                        EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::bigint % $3
                    ),
                1,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (endpoint, ip, window_start) DO UPDATE
                SET count = {_TABLE}.count + 1,
                    last_seen_at = CURRENT_TIMESTAMP
            RETURNING count
            """,
            endpoint, ip, window_seconds,
        )
        return int(row["count"]) if row else 1


async def _emit_rate_limited_audit(
    pool: Any,
    request: Request,
    *,
    endpoint: str,
    ip: str,
    max_requests: int,
    window_seconds: int,
    count: int,
) -> None:
    """Fire-and-forget audit emit on a detached connection."""
    try:
        ctx = _catalog_ctx.NodeContext(
            user_id=getattr(request.state, "user_id", None),
            session_id=getattr(request.state, "session_id", None),
            org_id=getattr(request.state, "org_id", None),
            workspace_id=getattr(request.state, "workspace_id", None),
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
            audit_category="security",
            extras={"pool": pool},
        )
        await _catalog.run_node(
            pool, "audit.events.emit",
            replace(ctx, conn=None),
            {
                "event_key": "iam.auth.rate_limited",
                "outcome": "failure",
                "metadata": {
                    "endpoint": endpoint,
                    "ip": ip,
                    "window_seconds": window_seconds,
                    "max_requests": max_requests,
                    "count": count,
                },
            },
        )
    except Exception:
        pass  # never fail the 429 response on an audit glitch


def auth_rate_limit(endpoint: str, *, max_requests: int, window_seconds: int):
    """Return a FastAPI dependency that enforces (endpoint, ip, window) rate limits.

    Usage:
        @router.post(
            "/signin",
            dependencies=[Depends(auth_rate_limit("auth.signin", max_requests=10, window_seconds=60))],
        )

    Raises 429 with {code: RATE_LIMITED, retry_after: N} when the bucket is full.
    """
    async def _dep(request: Request) -> None:
        pool = request.app.state.pool
        ip = _client_ip(request)
        count = await _increment_window(
            pool, endpoint=endpoint, ip=ip, window_seconds=window_seconds,
        )
        if count > max_requests:
            # Retry-after is the worst-case wait — a full window — since the
            # exact seconds-to-window-rollover would require re-reading
            # window_start and subtracting. A conservative ceiling is safer
            # for clients than lying about a precise reset time.
            retry_after = window_seconds
            await _emit_rate_limited_audit(
                pool, request,
                endpoint=endpoint, ip=ip,
                max_requests=max_requests, window_seconds=window_seconds,
                count=count,
            )
            # AppError envelope is {code, message}; clients parse retry_after
            # from the suffix of the message (no extras field on AppError).
            raise _errors.AppError(
                "RATE_LIMITED",
                f"Too many {endpoint} requests from this IP. Retry after {retry_after}s.",
                status_code=429,
            )
    return _dep
