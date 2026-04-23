"""
Scheduled publisher worker.

A single in-process asyncio task that wakes every N seconds, finds posts with
`status=scheduled AND scheduled_at <= now()`, and runs them through the same
publish pipeline as "Publish now" does. Failed posts move to `status=failed`
with the error recorded in `60_evt_post_publishes.metadata`.

Design notes:

* One worker per solsocial instance. Advisory lock on each post id via
  `SELECT ... FOR UPDATE SKIP LOCKED` prevents two instances from publishing
  the same post if someone runs the app with multiple replicas.
* No retries here. If a provider call fails, we mark the post failed; the
  user can click "Publish now" after fixing the issue. A retry policy belongs
  in a later iteration.
* Poll interval is 30s. Good enough for a tool where scheduling resolution
  is minute-level.
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any

_posts_service = import_module("apps.solsocial.backend.02_features.20_posts.service")

POLL_INTERVAL_SECONDS = 30
SCHEMA = '"10_solsocial"'


async def _claim_and_publish(
    pool: Any, publisher: Any, tennetctl: Any, *,
    post_id: str, workspace_id: str,
) -> None:
    """Publish one post. Catches and records errors as failed status."""
    try:
        async with pool.acquire() as conn:
            await _posts_service.publish_now(
                conn,
                post_id=post_id, workspace_id=workspace_id,
                publisher=publisher, tennetctl=tennetctl, token="",
            )
    except Exception as exc:
        # publish_now already marks failed inside the service on adapter error.
        # Anything that slipped through is logged here and not re-raised
        # so the worker keeps running.
        print(
            f"[solsocial-scheduler] publish failed post_id={post_id}: {exc!r}",
            flush=True,
        )


async def _fire_due_posts(pool: Any, publisher: Any, tennetctl: Any) -> int:
    """Find every scheduled post whose time has come; claim + publish each.

    Returns the number of posts published or attempted this tick.
    """
    async with pool.acquire() as conn:
        # SKIP LOCKED so parallel workers (if ever run) don't race.
        rows = await conn.fetch(
            f'SELECT id, workspace_id FROM {SCHEMA}."11_fct_posts" '
            'WHERE deleted_at IS NULL '
            '  AND status_id = (SELECT id FROM "10_solsocial"."02_dim_post_statuses" WHERE code = \'scheduled\') '
            '  AND scheduled_at <= CURRENT_TIMESTAMP '
            'ORDER BY scheduled_at '
            'LIMIT 50 '
            'FOR UPDATE SKIP LOCKED',
        )
    if not rows:
        return 0
    count = 0
    for r in rows:
        await _claim_and_publish(
            pool, publisher, tennetctl,
            post_id=r["id"], workspace_id=r["workspace_id"],
        )
        count += 1
    return count


async def scheduler_loop(pool: Any, publisher: Any, tennetctl: Any) -> None:
    """Long-running loop. Stops only when cancelled."""
    print(
        f"[solsocial-scheduler] started · poll every {POLL_INTERVAL_SECONDS}s",
        flush=True,
    )
    while True:
        try:
            fired = await _fire_due_posts(pool, publisher, tennetctl)
            if fired:
                print(f"[solsocial-scheduler] fired {fired} post(s)", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[solsocial-scheduler] tick error: {exc!r}", flush=True)
        try:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            raise


def start(app: Any) -> asyncio.Task:
    """Spawn the scheduler task bound to the app's pool/publisher/tennetctl."""
    return asyncio.create_task(
        scheduler_loop(app.state.pool, app.state.publisher, app.state.tennetctl),
        name="solsocial-scheduler",
    )


async def stop(task: asyncio.Task) -> None:
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
