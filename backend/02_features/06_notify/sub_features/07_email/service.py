"""
Email channel service — render, track, send.

process_queued_email_deliveries(pool, vault, base_tracking_url) polls for queued
email deliveries, renders via jinja2 (using pre-resolved variables stored on the
delivery row), adds pytracking open/click instrumentation, sends via aiosmtplib,
and updates delivery status.
"""

from __future__ import annotations

import asyncio
import datetime
import email.message
import logging
from importlib import import_module
from typing import Any

import aiosmtplib
import jinja2

_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.07_email.repository"
)
_del_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.repository"
)
_tmpl_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.03_templates.repository"
)
_group_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.02_template_groups.repository"
)
_smtp_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.01_smtp_configs.repository"
)

logger = logging.getLogger("tennetctl.notify.email")

# Jinja2 env — non-strict (resolved_variables may not cover every template var)
_jinja_env = jinja2.Environment(undefined=jinja2.Undefined, autoescape=False)


def apply_email_tracking(html_body: str, delivery_id: str, base_tracking_url: str) -> str:
    """
    Wrap all links with click-tracking redirects and add an open-tracking pixel
    at the end of <body>. Uses pytracking Base64 JSON encoding (no encryption).
    """
    from pytracking.html import adapt_html
    import pytracking

    config = pytracking.Configuration(
        base_open_tracking_url=f"{base_tracking_url}/v1/notify/email/track/o/",
        base_click_tracking_url=f"{base_tracking_url}/v1/notify/email/track/c/",
    )
    return adapt_html(
        html_body,
        {"delivery_id": delivery_id},
        click_tracking=True,
        open_tracking=True,
        configuration=config,
    )


async def _get_recipient_email(conn: Any, recipient_user_id: str) -> str:
    """
    Resolve email address for a delivery recipient.
    Looks up "03_iam"."v_users" by user ID.
    Falls back to treating recipient_user_id as a direct email address if '@' present.
    """
    if "@" in recipient_user_id:
        return recipient_user_id

    row = await conn.fetchrow(
        'SELECT email FROM "03_iam"."v_users" WHERE id = $1',
        recipient_user_id,
    )
    if row is None or not row["email"]:
        raise ValueError(
            f"Cannot resolve email for recipient_user_id={recipient_user_id!r}"
        )
    return row["email"]


async def _send_one(
    conn: Any,
    *,
    delivery: dict,
    vault: Any,
    base_tracking_url: str,
) -> None:
    """
    Render + track + send a single email delivery.
    Raises on any failure — caller updates status to 'failed'.
    """
    # 1. Resolve recipient email
    recipient_email = await _get_recipient_email(conn, delivery["recipient_user_id"])

    # 2. Fetch template with bodies
    template = await _tmpl_repo.get_template(conn, template_id=delivery["template_id"])
    if template is None:
        raise ValueError(f"template {delivery['template_id']!r} not found")

    # 3. Find email body (channel_id = 1)
    email_body = next(
        (b for b in (template.get("bodies") or []) if b["channel_id"] == 1),
        None,
    )
    if email_body is None:
        raise ValueError("template has no email body")

    # 4. Render subject + HTML + text using pre-resolved variables
    vars_dict = delivery.get("resolved_variables") or {}
    rendered_subject = _jinja_env.from_string(template["subject"]).render(**vars_dict)
    rendered_html = _jinja_env.from_string(email_body["body_html"]).render(**vars_dict)
    rendered_text: str | None = None
    if email_body.get("body_text"):
        rendered_text = _jinja_env.from_string(email_body["body_text"]).render(**vars_dict)

    # 5. Apply pytracking (open pixel + click wrapping)
    tracked_html = apply_email_tracking(rendered_html, delivery["id"], base_tracking_url)

    # 6. Fetch SMTP config via template group
    group = await _group_repo.get_template_group(conn, group_id=template["group_id"])
    if group is None or not group.get("smtp_config_id"):
        raise ValueError("template group has no smtp_config_id — cannot send email")
    smtp_config = await _smtp_repo.get_smtp_config(conn, config_id=group["smtp_config_id"])
    if smtp_config is None:
        raise ValueError(f"smtp_config {group['smtp_config_id']!r} not found")

    # 7. Fetch SMTP password from vault
    smtp_password = await vault.get(smtp_config["auth_vault_key"])

    # 8. Build MIME message
    msg = email.message.EmailMessage()
    msg["From"] = smtp_config["username"]
    msg["To"] = recipient_email
    msg["Subject"] = rendered_subject
    if template.get("reply_to"):
        msg["Reply-To"] = template["reply_to"]
    msg.set_content(rendered_text or "")
    msg.add_alternative(tracked_html, subtype="html")

    # 9. Send via aiosmtplib
    await aiosmtplib.send(
        msg,
        hostname=smtp_config["host"],
        port=smtp_config["port"],
        username=smtp_config["username"],
        password=smtp_password,
        use_tls=smtp_config["tls"],
        validate_certs=False,
    )

    # 10. Mark delivery as sent
    await _del_repo.update_delivery_status(
        conn,
        delivery_id=delivery["id"],
        status_id=3,  # sent
        delivered_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
    )


async def process_queued_email_deliveries(
    pool: Any,
    vault: Any,
    base_tracking_url: str,
    limit: int = 10,
) -> int:
    """
    Poll + send queued email deliveries. Returns number successfully sent.
    Each delivery is processed in its own connection to isolate failures.
    """
    async with pool.acquire() as conn:
        deliveries = await _repo.poll_and_claim_email_deliveries(conn, limit=limit)

    if not deliveries:
        return 0

    sent = 0
    for delivery in deliveries:
        async with pool.acquire() as conn:
            try:
                await _send_one(
                    conn,
                    delivery=delivery,
                    vault=vault,
                    base_tracking_url=base_tracking_url,
                )
                sent += 1
            except Exception as exc:
                logger.warning(
                    "email send failed delivery=%s: %s", delivery["id"], exc
                )
                await _del_repo.update_delivery_status(
                    conn,
                    delivery_id=delivery["id"],
                    status_id=8,  # failed
                    failure_reason=str(exc)[:500],
                )
    return sent


async def _email_sender_loop(pool: Any, vault: Any, base_tracking_url: str) -> None:
    """Background loop: drain queued email deliveries every 5 seconds when idle."""
    while True:
        try:
            count = await process_queued_email_deliveries(pool, vault, base_tracking_url)
            if count == 0:
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("email sender loop error: %s", exc)
            await asyncio.sleep(5)


def start_email_sender(pool: Any, vault: Any, base_tracking_url: str) -> "asyncio.Task":
    """Start the background email sender task. Call from app lifespan."""
    return asyncio.create_task(_email_sender_loop(pool, vault, base_tracking_url))
