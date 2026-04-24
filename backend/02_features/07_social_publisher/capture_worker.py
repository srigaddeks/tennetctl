"""
social_publisher.capture_worker — background tasks for the capture feature.

Tasks:
  • retention_prune: nightly, delete captures past their per-type TTL.

Runs as a single asyncio task started at app lifespan. Cadence is conservative:
prune once per hour (cheap — uses indexed `observed_at` range delete).
"""
from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Any

logger = logging.getLogger("tennetctl.social.capture_worker")

_repo: Any = import_module(
    "backend.02_features.07_social_publisher.capture_repository"
)

_PRUNE_INTERVAL_S = 3600  # 1 hour
_DEFAULT_RETENTION_DAYS = 365


async def _prune_once(pool: Any) -> None:
    try:
        async with pool.acquire() as conn:
            deleted = await _repo.prune_expired(conn, default_days=_DEFAULT_RETENTION_DAYS)
        if deleted:
            logger.info("social.capture.prune: deleted %d rows past retention", deleted)
    except Exception as e:
        logger.warning("social.capture.prune failed: %s", e)


async def run(pool: Any) -> None:
    """Long-running loop. Cancel-safe."""
    # Small jitter on startup so multi-pod deployments don't all prune at once
    await asyncio.sleep(30)
    while True:
        await _prune_once(pool)
        await asyncio.sleep(_PRUNE_INTERVAL_S)


def start_worker(pool: Any) -> asyncio.Task:
    return asyncio.create_task(run(pool))
