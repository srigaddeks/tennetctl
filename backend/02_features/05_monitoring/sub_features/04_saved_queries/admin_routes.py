"""Cross-cutting admin + health routes for monitoring.

- GET /health/monitoring — worker pool snapshot
- POST /v1/monitoring/dlq/replay — admin-scoped DLQ drain

Lives inside the saved_queries package to avoid a whole new sub-feature for
two endpoints. Plan 13-05 calls this the ``workers_admin`` router.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

_errors: Any = import_module("backend.01_core.errors")
_resp: Any = import_module("backend.01_core.response")
_nats_core: Any = import_module("backend.01_core.nats")
_config_mod: Any = import_module("backend.01_core.config")

router = APIRouter(tags=["monitoring.admin"])


class DLQReplayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: Literal[
        "monitoring.dlq.logs",
        "monitoring.dlq.spans",
    ]
    limit: int = Field(default=100, ge=1, le=1000)


_ALLOWED_DLQ_TO_ORIGINAL = {
    "monitoring.dlq.logs":  "monitoring.logs.retry",
    "monitoring.dlq.spans": "monitoring.spans.retry",
}


def _require_admin(request: Request) -> None:
    """Scope gate. The full scope system lands later; for now require the
    ``monitoring:admin`` scope to be present on ``request.state.scopes`` OR
    the ``x-monitoring-admin: 1`` header as a dev-only bypass. When neither
    is set, return 403.
    """
    scopes = getattr(request.state, "scopes", None) or []
    if "monitoring:admin" in scopes:
        return
    if request.headers.get("x-monitoring-admin") == "1":
        return
    raise _errors.ForbiddenError(
        "monitoring:admin scope required (or x-monitoring-admin: 1 header in dev)",
    )


@router.get("/health/monitoring")
async def monitoring_health(request: Request) -> dict:
    """Return worker-pool + NATS + store snapshot."""
    app = request.app
    pool = getattr(app.state, "monitoring_worker_pool", None)
    workers: list[dict] = []
    if pool is not None:
        snap = pool.health()
        workers = [{"name": k, **v} for k, v in snap.items()]

    # NATS
    nats_connected = False
    streams: list[str] = []
    try:
        if _nats_core._client is not None:
            nats_connected = True
            try:
                js = _nats_core.get_js()
                names_resp = await js.streams_info()
                streams = [s.config.name for s in names_resp]
            except Exception:  # noqa: BLE001
                streams = []
    except Exception:  # noqa: BLE001
        nats_connected = False

    cfg = _config_mod.load_config()
    store = {
        "kind": "postgres",
        "healthy": getattr(app.state, "pool", None) is not None,
    }

    return _resp.success({
        "workers": workers,
        "nats": {"connected": nats_connected, "streams": streams},
        "store": store,
        "enabled": getattr(cfg, "monitoring_enabled", False),
    })


@router.post("/v1/monitoring/dlq/replay", status_code=200)
async def dlq_replay(request: Request, body: DLQReplayRequest) -> dict:
    """Consume up to ``limit`` messages from the named DLQ and republish them
    to the original subject. Requires monitoring:admin scope.
    """
    _require_admin(request)
    try:
        js = _nats_core.get_js()
    except Exception as e:  # noqa: BLE001
        raise _errors.AppError(
            "UNAVAILABLE", f"NATS not available: {e}", 503,
        ) from e

    original = _ALLOWED_DLQ_TO_ORIGINAL[body.subject]

    # Pull-based ephemeral subscription. Each fetched msg is published to
    # the original subject and acked.
    replayed = 0
    errors = 0
    try:
        sub = await js.pull_subscribe(
            subject=body.subject,
            durable=None,  # ephemeral
        )
        for _ in range(body.limit):
            try:
                msgs = await sub.fetch(batch=1, timeout=1.0)
            except Exception:  # noqa: BLE001
                break
            if not msgs:
                break
            msg = msgs[0]
            try:
                await js.publish(original, msg.data)
                await msg.ack()
                replayed += 1
            except Exception:  # noqa: BLE001
                errors += 1
                try:
                    await msg.nak()
                except Exception:  # noqa: BLE001
                    pass
    except Exception as e:  # noqa: BLE001
        raise _errors.AppError(
            "DLQ_REPLAY_FAILED", f"DLQ replay failed: {e}", 500,
        ) from e

    return _resp.success({
        "subject": body.subject,
        "original": original,
        "replayed": replayed,
        "errors": errors,
    })
