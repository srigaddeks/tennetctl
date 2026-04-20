"""Action dispatch worker — LISTEN-based + periodic retry scanner."""

import asyncio
import logging
from importlib import import_module
from datetime import datetime, timedelta
import asyncpg

_core_db = import_module("backend.01_core.database")
_core_id = import_module("backend.01_core.id")

logger = logging.getLogger(__name__)


class ActionDispatchWorker:
    """
    Worker that:
    1. Subscribes to Postgres LISTEN monitoring_action_dispatch
    2. Polls every 30s for stale deliveries (pending retry)
    3. Dispatches with bounded concurrency (semaphore=20)
    """

    def __init__(self, pool: asyncpg.Pool, max_concurrent: int = 20):
        self.pool = pool
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.running = False

    async def run(self):
        """Start the worker loop."""
        self.running = True
        conn = await self.pool.acquire()

        try:
            await conn.add_listener("monitoring_action_dispatch", self._on_notify)

            # Start background task for polling
            poll_task = asyncio.create_task(self._poll_loop())

            # Run LISTEN loop
            while self.running:
                try:
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    break

            # Cleanup
            poll_task.cancel()
            try:
                await poll_task
            except asyncio.CancelledError:
                pass

        finally:
            await conn.remove_listener("monitoring_action_dispatch")
            await self.pool.release(conn)

    def _on_notify(self, connection, pid, channel, payload):
        """Handle NOTIFY event from monitoring_action_dispatch."""
        delivery_id = payload
        asyncio.create_task(self._dispatch_delivery(delivery_id))

    async def _poll_loop(self):
        """Periodically scan for pending deliveries to retry."""
        while self.running:
            try:
                await asyncio.sleep(30)  # Poll every 30s
                await self._scan_pending_retries()
            except Exception as e:
                logger.error(f"Polling error: {e}")

    async def _scan_pending_retries(self):
        """Find deliveries pending retry and enqueue them."""
        conn = await self.pool.acquire()

        try:
            # Find deliveries where:
            # - succeeded_at IS NULL (not succeeded)
            # - completed_at IS NULL (not yet completed)
            # - started_at + (backoff delay) <= now
            deliveries = await conn.fetch(
                """
                SELECT d.id, d.template_id, d.attempt, t.retry_policy
                FROM "05_monitoring"."65_evt_monitoring_action_deliveries" d
                JOIN "05_monitoring"."14_fct_monitoring_action_templates" t
                  ON d.template_id = t.id
                WHERE d.succeeded_at IS NULL
                  AND d.completed_at IS NULL
                  AND d.started_at <= CURRENT_TIMESTAMP - INTERVAL '1 minute'
                LIMIT 100
                """
            )

            for delivery in deliveries:
                await self._dispatch_delivery(delivery["id"])

        finally:
            await self.pool.release(conn)

    async def _dispatch_delivery(self, delivery_id: str):
        """Dispatch a single delivery with retry logic."""
        async with self.semaphore:
            conn = await self.pool.acquire()

            try:
                # Fetch delivery + template
                delivery = await conn.fetchrow(
                    """
                    SELECT d.*, t.kind_id, k.code AS kind_code,
                           t.target_url, t.target_address, t.body_template,
                           t.headers_template, t.signing_secret_vault_ref, t.retry_policy
                    FROM "05_monitoring"."65_evt_monitoring_action_deliveries" d
                    JOIN "05_monitoring"."14_fct_monitoring_action_templates" t
                      ON d.template_id = t.id
                    JOIN "05_monitoring"."03_dim_monitoring_action_kind" k
                      ON t.kind_id = k.id
                    WHERE d.id = $1
                    """,
                    delivery_id,
                )

                if not delivery:
                    logger.warning(f"Delivery {delivery_id} not found")
                    return

                # Check if max attempts exceeded
                retry_policy = delivery["retry_policy"] or {}
                max_attempts = retry_policy.get("max_attempts", 3)
                if delivery["attempt"] >= max_attempts:
                    logger.info(f"Delivery {delivery_id} exhausted retries ({max_attempts})")
                    # Mark as completed (permanently failed)
                    await conn.execute(
                        """
                        UPDATE "05_monitoring"."65_evt_monitoring_action_deliveries"
                        SET completed_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        """,
                        delivery_id,
                    )
                    return

                # Render template (simplified; real impl would re-render)
                rendered_body = delivery["body_template"]  # Placeholder
                rendered_headers = delivery["headers_template"] or {}

                # Fetch signing secret from vault if needed
                signing_secret = None
                if delivery["signing_secret_vault_ref"]:
                    # TODO: resolve vault secret
                    pass

                # Call dispatch node
                from importlib import import_module
                dispatch_node = import_module(
                    "backend.02_features.05_monitoring.sub_features.09_action_templates.nodes.dispatch"
                )

                result = await dispatch_node.DispatchNode().handle(
                    {
                        "delivery_id": delivery_id,
                        "template_id": delivery["template_id"],
                        "rendered_body": rendered_body,
                        "rendered_headers": rendered_headers,
                        "signing_secret": signing_secret,
                    },
                    pool=self.pool,
                )

                # Handle retry logic
                if not result.get("success"):
                    # Schedule retry if within max attempts
                    base_seconds = retry_policy.get("base_seconds", 5)
                    max_seconds = retry_policy.get("max_seconds", 300)
                    backoff_seconds = min(
                        base_seconds * (2 ** (delivery["attempt"] - 1)), max_seconds
                    )

                    # Add jitter ±20%
                    import random
                    jitter = backoff_seconds * 0.2 * random.uniform(-1, 1)
                    delay_seconds = max(1, backoff_seconds + jitter)

                    # Create new delivery record for retry
                    next_delivery_id = _core_id.uuid7()
                    await conn.execute(
                        """
                        INSERT INTO "05_monitoring"."65_evt_monitoring_action_deliveries"
                        (id, template_id, alert_event_id, escalation_state_id,
                         attempt, request_payload_hash, started_at)
                        VALUES ($1, $2, $3, $4, $5, $6,
                                CURRENT_TIMESTAMP + INTERVAL '1 second' * $7)
                        """,
                        next_delivery_id,
                        delivery["template_id"],
                        delivery["alert_event_id"],
                        delivery["escalation_state_id"],
                        delivery["attempt"] + 1,
                        delivery["request_payload_hash"],
                        delay_seconds,
                    )

                    logger.info(
                        f"Scheduled retry for delivery {delivery_id}: "
                        f"attempt {delivery['attempt'] + 1} in {delay_seconds:.1f}s"
                    )

            except Exception as e:
                logger.error(f"Error dispatching {delivery_id}: {e}", exc_info=True)

            finally:
                await self.pool.release(conn)


async def start_worker(pool: asyncpg.Pool):
    """Start the action dispatch worker."""
    worker = ActionDispatchWorker(pool)
    await worker.run()
