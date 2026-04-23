"""
social_publisher — background scheduler worker.

Polls every 30 seconds for posts that are scheduled and due.
Runs as an asyncio task started from main.py lifespan.
"""

from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Any

_service: Any = import_module("backend.02_features.07_social_publisher.service")
_repo: Any = import_module("backend.02_features.07_social_publisher.repository")

logger = logging.getLogger("tennetctl.social_publisher.worker")

_POLL_INTERVAL = 30  # seconds


async def run_scheduler_loop(pool: Any, vault_client: Any) -> None:
    """Main scheduler loop — finds due posts and publishes them.

    Runs forever; cancelled cleanly by asyncio task cancellation on shutdown.
    Errors on individual posts never crash the loop.
    """
    logger.info("Social publisher scheduler started (poll interval: %ds)", _POLL_INTERVAL)

    while True:
        try:
            await _tick(pool, vault_client)
        except asyncio.CancelledError:
            logger.info("Social publisher scheduler stopping.")
            raise
        except Exception:
            logger.exception("Social publisher scheduler tick failed — will retry")

        await asyncio.sleep(_POLL_INTERVAL)


async def _tick(pool: Any, vault_client: Any) -> None:
    """Single scheduler tick — publish all due posts."""
    async with pool.acquire() as conn:
        due_posts = await _repo.get_due_posts(conn)

    if not due_posts:
        return

    logger.info("Social publisher: found %d due post(s)", len(due_posts))

    for post in due_posts:
        post_id = post["id"]
        try:
            # Use a minimal ctx — scheduler has no user session
            ctx = _SchedulerCtx(org_id=post["org_id"])
            await _service.publish_post_now(pool, vault_client, ctx, post_id)
            logger.info("Social publisher: published post %s", post_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Social publisher: failed to publish post %s: %s", post_id, e)
            # Mark as failed so it's not retried endlessly
            try:
                async with pool.acquire() as conn:
                    await _repo.update_post_status(
                        conn,
                        post_id=post_id,
                        status_id=_service._STATUS_FAILED,
                        error_message=str(e)[:500],
                    )
            except Exception:
                logger.exception("Social publisher: could not mark post %s as failed", post_id)


class _SchedulerCtx:
    """Minimal context for the scheduler — no user session."""

    def __init__(self, org_id: str) -> None:
        self.user_id = "scheduler"
        self.session_id = None
        self.org_id = org_id
        self.workspace_id = None
        self.audit_category = "system"
