"""social_publisher.capture — routes for POST/GET /v1/social/captures + insights."""
from __future__ import annotations

import datetime as dt
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_schemas: Any = import_module(
    "backend.02_features.07_social_publisher.capture_schemas"
)
_svc: Any = import_module(
    "backend.02_features.07_social_publisher.capture_service"
)
_persona: Any = import_module(
    "backend.02_features.07_social_publisher.persona_service"
)

router = APIRouter()


def _require_auth(request: Request) -> dict:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.UnauthorizedError("authentication required")
    return {
        "user_id": user_id,
        "id": getattr(request.state, "session_id", None) or "",
        "org_id": getattr(request.state, "org_id", None) or "",
        "workspace_id": getattr(request.state, "workspace_id", None),
    }


# ── In-process per-user rate limit for ingest ────────────────────────────────
#
# Sliding-window of 1 minute. Default ceiling of 500 captures/minute per user
# (comfortably above normal browsing, catches runaway scans).
import collections, time as _time

_RATE_WINDOW_S = 60
_RATE_MAX = 500
_rate_log: dict[str, collections.deque] = collections.defaultdict(collections.deque)


def _rate_check(user_id: str, incoming: int) -> None:
    now = _time.monotonic()
    q = _rate_log[user_id]
    while q and now - q[0] > _RATE_WINDOW_S:
        q.popleft()
    if len(q) + incoming > _RATE_MAX:
        raise _errors.AppError(
            "RATE_LIMITED",
            f"Ingest rate limit exceeded ({_RATE_MAX} captures/min per user).",
            status_code=429,
        )
    for _ in range(incoming):
        q.append(now)


# ── Ingest ──────────────────────────────────────────────────────────────────

@router.post("/v1/social/captures")
async def ingest_captures(request: Request):
    session = _require_auth(request)
    raw = await request.json()
    body = _schemas.CaptureBatchIn.model_validate(raw)

    _rate_check(session["user_id"], len(body.captures))

    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await _svc.ingest_batch(
            conn,
            user_id=session["user_id"],
            org_id=session.get("org_id") or "",
            session_id=session["id"],
            workspace_id=session.get("workspace_id"),
            captures_in=[c.model_dump() for c in body.captures],
        )

    return _response.success(_schemas.CaptureBatchOut(**result).model_dump())


# ── List ────────────────────────────────────────────────────────────────────

@router.get("/v1/social/captures")
async def list_captures(
    request: Request,
    platform: str | None = Query(None),
    type: str | None = Query(None),
    org_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
    author_handle: str | None = Query(None, description="Filter by exact author handle"),
    hashtag: str | None = Query(None, description="Filter by a single hashtag (without #)"),
    mention: str | None = Query(None, description="Filter by a single @mention (without @)"),
    q: str | None = Query(None, description="Full-text search across text_excerpt + author_name"),
    from_dt: dt.datetime | None = Query(None, alias="from"),
    to_dt: dt.datetime | None = Query(None, alias="to"),
    is_own: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = _require_auth(request)
    pool = request.app.state.pool

    async with pool.acquire() as conn:
        result = await _svc.list_captures(
            conn,
            user_id=session["user_id"],
            org_id=org_id,
            workspace_id=workspace_id,
            platform=platform,
            capture_type=type,
            author_handle=author_handle,
            hashtag=hashtag,
            mention=mention,
            q=q,
            from_dt=from_dt,
            to_dt=to_dt,
            is_own=is_own,
            limit=limit,
            offset=offset,
        )

    payload = _schemas.CaptureListOut(
        items=[_schemas.CaptureOut(**item) for item in result["items"]],
        total=result["total"],
        limit=limit,
        offset=offset,
    ).model_dump(mode="json")
    return _response.success(payload)


# ── Metric history for a single capture ─────────────────────────────────────

@router.get("/v1/social/captures/{capture_id}/metrics")
async def capture_metric_history(request: Request, capture_id: str):
    session = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        obs = await _svc.metric_history(conn, user_id=session["user_id"], capture_id=capture_id)

    payload = _schemas.MetricHistoryOut(
        capture_id=capture_id,
        observations=[_schemas.MetricObservation(**o) for o in obs],
    ).model_dump(mode="json")
    return _response.success(payload)


# ── Insights: counts / top authors / top hashtags ───────────────────────────

@router.get("/v1/social/insights/counts")
async def insights_counts(request: Request):
    session = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        counts = await _svc.capture_counts(conn, user_id=session["user_id"])
    return _response.success(_schemas.CaptureCountsOut(**counts).model_dump())


@router.get("/v1/social/insights/top-authors")
async def insights_top_authors(
    request: Request,
    platform: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    session = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _svc.top_authors(conn, user_id=session["user_id"], platform=platform, limit=limit)
    items = [_schemas.TopAuthorRow(**r).model_dump(mode="json") for r in rows]
    return _response.success({"items": items})


@router.get("/v1/social/insights/top-hashtags")
async def insights_top_hashtags(
    request: Request,
    platform: str | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    session = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _svc.top_hashtags(conn, user_id=session["user_id"], platform=platform, limit=limit)
    return _response.success({"items": rows})


# ── Persona + AI recommendations ───────────────────────────────────────────

@router.get("/v1/social/persona")
async def get_persona(request: Request):
    session = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        persona = await _persona.build_persona(conn, user_id=session["user_id"])
    return _response.success(persona)


@router.post("/v1/social/recommendations/comments")
async def recommend_comments(request: Request):
    session = _require_auth(request)
    body = await request.json()
    capture_id = body.get("capture_id")
    n = int(body.get("n", 3))
    if not capture_id:
        raise _errors.AppError("INVALID_BODY", "capture_id is required", status_code=400)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await _persona.recommend_comments(
            conn, user_id=session["user_id"], capture_id=capture_id, n=n,
        )
    return _response.success(result)


@router.post("/v1/social/recommendations/posts")
async def recommend_posts(request: Request):
    session = _require_auth(request)
    body = await request.json() if await request.body() else {}
    n = int(body.get("n", 3)) if isinstance(body, dict) else 3
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await _persona.recommend_posts(conn, user_id=session["user_id"], n=n)
    return _response.success(result)


@router.post("/v1/social/recommendations/articles")
async def recommend_articles(request: Request):
    session = _require_auth(request)
    body = await request.json() if await request.body() else {}
    n = int(body.get("n", 5)) if isinstance(body, dict) else 5
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await _persona.recommend_articles(conn, user_id=session["user_id"], n=n)
    return _response.success(result)
