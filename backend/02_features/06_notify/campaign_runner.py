"""
Notify campaign runner.

Polls for campaigns with status=scheduled and scheduled_at <= NOW().
For each campaign:
  1. Transitions status: scheduled → running
  2. Resolves the audience (user IDs from 03_iam membership)
  3. For each user: checks notification preferences, creates deliveries
  4. Throttles delivery creation to campaign.throttle_per_minute
  5. Transitions status: running → completed (or failed on error)

Critical category templates fan out to all channels regardless of campaign.channel_id.
Preferences are checked per channel×category — critical bypasses opt-out.

Usage (in app lifespan):
    task = start_campaign_runner(pool)
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
"""

from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Any

_campaign_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.10_campaigns.repository"
)
_campaign_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.10_campaigns.service"
)
_del_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.service"
)
_tmpl_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.03_templates.repository"
)
_var_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.04_variables.repository"
)
_pref_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.09_preferences.service"
)

logger = logging.getLogger("notify.campaign_runner")

_POLL_INTERVAL_S = 60
_CRITICAL_CHANNELS = [1, 2, 3]  # email, webpush, in_app


async def _run_campaign(pool: Any, campaign: dict) -> None:
    """Execute a single campaign end-to-end."""
    campaign_id = campaign["id"]
    org_id = campaign["org_id"]

    async with pool.acquire() as conn:
        # Claim: scheduled → running
        await _campaign_repo.update_campaign_status(
            conn, campaign_id=campaign_id, status_id=_campaign_repo.STATUS_RUNNING
        )
        logger.info("Campaign %s: status → running", campaign_id)

    try:
        async with pool.acquire() as conn:
            template = await _tmpl_repo.get_template(conn, template_id=campaign["template_id"])
            if template is None:
                raise ValueError(f"template {campaign['template_id']!r} not found")

            audience_ids = await _campaign_svc.resolve_audience(
                conn,
                org_id=org_id,
                audience_query=campaign.get("audience_query") or {},
            )

        logger.info(
            "Campaign %s: audience resolved — %d users", campaign_id, len(audience_ids)
        )

        is_critical = template.get("category_code") == "critical"
        channels = _CRITICAL_CHANNELS if is_critical else [campaign["channel_id"]]
        category_id = template.get("category_id") or 1  # default: transactional
        priority_id = template.get("priority_id") or 2  # default: normal

        throttle_per_minute = campaign.get("throttle_per_minute") or 60
        # Sleep between batches to stay within throttle.
        # We send in batches of min(throttle_per_minute, 100); sleep 60s between batches.
        batch_size = min(throttle_per_minute, 100)
        sleep_between_batches = 60.0

        sent = 0
        for i in range(0, len(audience_ids), batch_size):
            batch = audience_ids[i : i + batch_size]

            async with pool.acquire() as conn:
                resolved = await _var_repo.resolve_variables(
                    conn, template_id=template["id"], context={"org_id": org_id}
                )
                for user_id in batch:
                    for channel_id in channels:
                        opted_in = await _pref_service.is_opted_in(
                            conn,
                            user_id=user_id,
                            org_id=org_id,
                            channel_id=channel_id,
                            category_id=category_id,
                        )
                        if not opted_in:
                            continue
                        await _del_service.create_delivery(
                            conn,
                            subscription_id=None,
                            campaign_id=campaign_id,
                            org_id=org_id,
                            template_id=template["id"],
                            recipient_user_id=user_id,
                            channel_id=channel_id,
                            priority_id=priority_id,
                            resolved_variables=resolved,
                        )
                        sent += 1

            if i + batch_size < len(audience_ids):
                # More batches to process — throttle
                logger.debug(
                    "Campaign %s: batch done (%d sent), sleeping %ds",
                    campaign_id, sent, sleep_between_batches,
                )
                await asyncio.sleep(sleep_between_batches)

        async with pool.acquire() as conn:
            await _campaign_repo.update_campaign_status(
                conn, campaign_id=campaign_id, status_id=_campaign_repo.STATUS_COMPLETED
            )
        logger.info("Campaign %s: completed — %d deliveries created", campaign_id, sent)

    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Campaign %s: failed", campaign_id)
        async with pool.acquire() as conn:
            await _campaign_repo.update_campaign_status(
                conn, campaign_id=campaign_id, status_id=_campaign_repo.STATUS_FAILED
            )


async def _runner_loop(pool: Any) -> None:
    """
    Main loop: poll every _POLL_INTERVAL_S seconds for scheduled campaigns.
    Runs each campaign serially (one at a time) to keep DB load predictable.
    """
    logger.info("Notify campaign runner started (poll=%ds)", _POLL_INTERVAL_S)
    while True:
        try:
            async with pool.acquire() as conn:
                due = await _campaign_repo.poll_scheduled_campaigns(conn)
            for campaign in due:
                await _run_campaign(pool, campaign)
        except asyncio.CancelledError:
            logger.info("Notify campaign runner stopped")
            return
        except Exception:
            logger.exception("Campaign runner poll error")

        try:
            await asyncio.sleep(_POLL_INTERVAL_S)
        except asyncio.CancelledError:
            logger.info("Notify campaign runner stopped")
            return


def start_campaign_runner(pool: Any) -> "asyncio.Task[None]":
    """
    Start the campaign runner as an asyncio background task.
    Cancel the returned task on shutdown.
    """
    return asyncio.create_task(_runner_loop(pool), name="notify-campaign-runner")
