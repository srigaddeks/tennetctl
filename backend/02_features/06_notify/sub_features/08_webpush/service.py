"""
notify.webpush — service layer.

VAPID keys are bootstrapped once into vault at startup:
  notify.vapid.private_key  — PEM private key (signs push JWTs)
  notify.vapid.public_key   — base64url uncompressed P-256 point (sent to browsers)

Sending uses pywebpush.webpush_async() which accepts the PEM private key directly
and derives the VAPID `aud` claim from each subscription's endpoint URL.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from dataclasses import replace
from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.08_webpush.repository"
)
_secrets_svc: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.service"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")
_vault_client_mod: Any = import_module("backend.02_features.02_vault.client")

logger = logging.getLogger("tennetctl.notify.webpush")

_VAPID_PRIVATE_KEY = "notify.vapid.private_key"
_VAPID_PUBLIC_KEY = "notify.vapid.public_key"
_VAPID_CLAIMS_SUB = "mailto:admin@tennetctl.local"


async def ensure_vapid_keys(pool: Any, vault: Any) -> str:
    """Bootstrap VAPID keys into vault if not already present.

    Returns the base64url-encoded uncompressed P-256 public key.
    Idempotent: subsequent calls return the existing key without touching the vault.
    """
    try:
        return await vault.get(_VAPID_PUBLIC_KEY)
    except _vault_client_mod.VaultSecretNotFound:
        pass

    # Generate a new VAPID key pair
    from py_vapid import Vapid
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    vapid = Vapid()
    vapid.generate_keys()
    priv_pem = vapid.private_pem().decode("ascii")
    pub_bytes = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode("ascii")

    # Bootstrap-style NodeContext (setup category skips normal authz checks)
    ctx = _catalog_ctx.NodeContext(
        user_id="sys",
        session_id="bootstrap",
        org_id=None,
        workspace_id=None,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="setup",
        extras={"pool": pool, "vault": vault},
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx, conn=conn)
            await _secrets_svc.create_secret(
                pool, conn, ctx,
                vault_client=vault,
                key=_VAPID_PRIVATE_KEY,
                value=priv_pem,
                description="VAPID private key for web push notifications (PEM).",
                scope="global",
            )
            await _secrets_svc.create_secret(
                pool, conn, ctx,
                vault_client=vault,
                key=_VAPID_PUBLIC_KEY,
                value=pub_b64,
                description="VAPID public key for web push notifications (base64url uncompressed P-256).",
                scope="global",
            )

    logger.info("VAPID keys bootstrapped into vault.")
    return pub_b64


async def _send_one(conn: Any, delivery: dict, vault: Any) -> None:
    """Send a single webpush delivery to all active subscriptions for the recipient."""
    from pywebpush import webpush_async, WebPushException

    delivery_id = delivery["id"]
    recipient_user_id = delivery["recipient_user_id"]

    # Fallback supersession: another delivery for this (org,template,user)
    # already reached opened/clicked — skip this channel.
    superseded = await conn.fetchval(
        '''
        SELECT 1 FROM "06_notify"."v_notify_deliveries"
        WHERE org_id = $1 AND template_id = $2 AND recipient_user_id = $3
          AND id <> $4 AND status_code IN ('opened','clicked')
        LIMIT 1
        ''',
        delivery["org_id"], delivery["template_id"], recipient_user_id, delivery_id,
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
            delivery_id,
        )
        return

    # Resolve all active browser subscriptions for this user
    subs = await _repo.get_user_webpush_subscriptions(conn, user_id=recipient_user_id)
    if not subs:
        await _repo.mark_delivery_failed(
            conn, delivery_id=delivery_id, reason="no_webpush_subscriptions"
        )
        return

    # Build notification payload from resolved variables + deep_link
    resolved_vars = delivery.get("resolved_variables") or {}
    title = resolved_vars.get("subject") or resolved_vars.get("title") or "Notification"
    body = resolved_vars.get("body") or resolved_vars.get("message") or ""
    url = delivery.get("deep_link") or resolved_vars.get("url") or "/"
    payload = json.dumps({
        "title": title,
        "body": body,
        "delivery_id": delivery_id,
        "url": url,
    })

    # Load VAPID private key (PEM) from vault
    priv_pem = await vault.get(_VAPID_PRIVATE_KEY)

    errors: list[str] = []
    for sub in subs:
        sub_info = {
            "endpoint": sub["endpoint"],
            "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
        }
        try:
            resp = await webpush_async(
                subscription_info=sub_info,
                data=payload,
                vapid_private_key=priv_pem,
                vapid_claims={"sub": _VAPID_CLAIMS_SUB},
                ttl=86400,
                content_encoding="aes128gcm",
            )
            if hasattr(resp, "status") and resp.status >= 400:
                errors.append(f"sub={sub['id'][:8]} HTTP {resp.status}")
        except WebPushException as exc:
            errors.append(f"sub={sub['id'][:8]} push_err={exc}")
        except Exception as exc:
            errors.append(f"sub={sub['id'][:8]} err={exc}")

    if errors:
        _del_repo: Any = import_module(
            "backend.02_features.06_notify.sub_features.06_deliveries.repository"
        )
        backoff = _del_repo.backoff_seconds_for_attempt(
            int(delivery.get("attempt_count") or 0)
        )
        await _del_repo.mark_retryable_error(
            conn,
            delivery_id=delivery_id,
            reason="; ".join(errors[:3])[:500],
            backoff_seconds=backoff,
        )
    else:
        await _repo.mark_delivery_sent(conn, delivery_id=delivery_id)


async def process_queued_webpush_deliveries(
    pool: Any, vault: Any, limit: int = 10
) -> int:
    """Poll and send up to `limit` queued webpush deliveries. Returns count processed."""
    async with pool.acquire() as conn:
        deliveries = await _repo.poll_and_claim_webpush_deliveries(conn, limit=limit)

    count = 0
    for delivery in deliveries:
        async with pool.acquire() as conn:
            try:
                await _send_one(conn, delivery, vault)
                count += 1
            except Exception as exc:
                logger.exception(
                    "webpush send error delivery=%s: %s", delivery["id"], exc
                )
                try:
                    _del_repo: Any = import_module(
                        "backend.02_features.06_notify.sub_features.06_deliveries.repository"
                    )
                    backoff = _del_repo.backoff_seconds_for_attempt(
                        int(delivery.get("attempt_count") or 0)
                    )
                    await _del_repo.mark_retryable_error(
                        conn,
                        delivery_id=delivery["id"],
                        reason=str(exc)[:500],
                        backoff_seconds=backoff,
                    )
                except Exception:
                    pass
    return count


async def _webpush_sender_loop(pool: Any, vault: Any) -> None:
    while True:
        try:
            processed = await process_queued_webpush_deliveries(pool, vault)
            if processed == 0:
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("webpush sender loop error: %s", exc)
            await asyncio.sleep(10)


def start_webpush_sender(pool: Any, vault: Any) -> asyncio.Task:
    """Start the webpush background sender as an asyncio Task."""
    return asyncio.create_task(_webpush_sender_loop(pool, vault))
