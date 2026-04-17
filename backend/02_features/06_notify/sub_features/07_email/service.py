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
_suppression_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.16_suppression.repository"
)
_suppression_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.16_suppression.service"
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

    # 1a-pre. Fallback supersession: if another delivery for the same
    # (org_id, template_id, recipient_user_id) reached opened/clicked,
    # this is a losing fallback — skip without sending.
    superseded = await conn.fetchval(
        '''
        SELECT 1 FROM "06_notify"."v_notify_deliveries"
        WHERE org_id = $1 AND template_id = $2 AND recipient_user_id = $3
          AND id <> $4 AND status_code IN ('opened','clicked')
        LIMIT 1
        ''',
        delivery["org_id"], delivery["template_id"], delivery["recipient_user_id"],
        delivery["id"],
    )
    if superseded:
        await conn.execute(
            '''UPDATE "06_notify"."15_fct_notify_deliveries"
               SET status_id = 9,
                   failure_reason = 'superseded_by_primary',
                   attempt_count = attempt_count + 1,
                   next_retry_at = NULL,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = $1''',
            delivery["id"],
        )
        return

    # 1a. Suppression check — short-circuit before any SMTP work.
    suppressed = await _suppression_repo.is_suppressed(
        conn, org_id=delivery["org_id"], email=recipient_email,
    )
    if suppressed:
        reason = await _suppression_repo.get_reason(
            conn, org_id=delivery["org_id"], email=recipient_email,
        )
        _del_repo_local: Any = import_module(
            "backend.02_features.06_notify.sub_features.06_deliveries.repository"
        )
        await conn.execute(
            '''UPDATE "06_notify"."15_fct_notify_deliveries"
               SET status_id = 9,
                   failure_reason = $2,
                   attempt_count = attempt_count + 1,
                   next_retry_at = NULL,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = $1''',
            delivery["id"], f"suppressed:{reason or 'unknown'}",
        )
        # Silence unused-import warning — _del_repo_local is kept so this
        # status update stays consistent with repository semantics on reuse.
        _ = _del_repo_local
        return

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
    # Envelope From: explicit from_email if provided (required for providers
    # where the SMTP username is an API key, e.g. SendGrid/Postmark/Mailgun);
    # optionally prefix with a display name.
    sender_addr = smtp_config.get("from_email") or smtp_config["username"]
    sender_name = smtp_config.get("from_name")
    msg["From"] = f"{sender_name} <{sender_addr}>" if sender_name else sender_addr
    msg["To"] = recipient_email
    msg["Subject"] = rendered_subject
    if template.get("reply_to"):
        msg["Reply-To"] = template["reply_to"]

    # RFC 8058 one-click unsubscribe. Signed token is cookie-less + stable;
    # includes org_id, email, and the template's category for per-category
    # opt-out granularity.
    try:
        signing_key = await _suppression_svc._signing_key_bytes(vault)
        unsub_token = _suppression_svc.make_unsubscribe_token(
            org_id=delivery["org_id"],
            email=recipient_email,
            category_code=template.get("category_code"),
            signing_key=signing_key,
        )
        unsub_url = f"{base_tracking_url}/v1/notify/unsubscribe?token={unsub_token}"
        # mailto: fallback first, then HTTPS per RFC 8058 ordering.
        mailto_domain = (sender_addr.split("@", 1)[1] if "@" in sender_addr else "example.com")
        msg["List-Unsubscribe"] = (
            f"<mailto:unsubscribe@{mailto_domain}>, <{unsub_url}>"
        )
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    except Exception as exc:
        logger.warning(
            "Could not attach List-Unsubscribe header for delivery=%s: %s",
            delivery["id"], exc,
        )

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

    # 10. Mark delivery as sent (increments attempt_count, resets next_retry_at)
    await conn.execute(
        '''
        UPDATE "06_notify"."15_fct_notify_deliveries"
        SET status_id = 3,
            delivered_at = CURRENT_TIMESTAMP,
            next_retry_at = NULL,
            attempt_count = attempt_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        ''',
        delivery["id"],
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
                backoff = _del_repo.backoff_seconds_for_attempt(
                    int(delivery.get("attempt_count") or 0)
                )
                logger.warning(
                    "email send failed delivery=%s attempt=%d backoff=%ds: %s",
                    delivery["id"], delivery.get("attempt_count") or 0, backoff, exc,
                )
                await _del_repo.mark_retryable_error(
                    conn,
                    delivery_id=delivery["id"],
                    reason=str(exc)[:500],
                    backoff_seconds=backoff,
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
