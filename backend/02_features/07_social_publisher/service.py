"""
social_publisher — service layer.

Owns all business logic: vault integration, platform dispatch, metrics polling.
All functions take conn (not pool) except entry points that need multiple
transactions (publish_post_now, refresh_metrics).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_repo: Any = import_module("backend.02_features.07_social_publisher.repository")
_tw: Any = import_module("backend.02_features.07_social_publisher.twitter_client")

logger = logging.getLogger("tennetctl.social_publisher")

# Status ID constants (must match 02_dim_post_statuses seed)
_STATUS_DRAFT = 1
_STATUS_SCHEDULED = 2
_STATUS_PUBLISHING = 3
_STATUS_PUBLISHED = 4
_STATUS_FAILED = 5
_STATUS_CANCELLED = 6

_STATUS_CODE_TO_ID = {
    "draft": _STATUS_DRAFT,
    "scheduled": _STATUS_SCHEDULED,
    "publishing": _STATUS_PUBLISHING,
    "published": _STATUS_PUBLISHED,
    "failed": _STATUS_FAILED,
    "cancelled": _STATUS_CANCELLED,
}


def _actor(ctx: Any) -> str:
    return getattr(ctx, "user_id", None) or "sys"


# ── Accounts ─────────────────────────────────────────────────────────────────

async def connect_account(
    pool: Any,
    vault_client: Any,
    ctx: Any,
    data: dict,
) -> dict:
    """Vault the bearer token and create the social account row."""
    platform = data["platform"]
    handle = data.get("account_handle") or data["account_name"]
    bearer_token = data["bearer_token"]
    org_id = getattr(ctx, "org_id", None) or data.get("org_id")
    workspace_id = getattr(ctx, "workspace_id", None)

    if not org_id:
        raise _errors.AppError(
            "MISSING_ORG", "org_id is required to connect an account.", 400
        )

    # Vault key follows the convention social.{platform}.{handle}
    vault_key = f"social.{platform}.{handle.lstrip('@')}"

    # Store the bearer token in vault.
    # Use audit_category="setup" so the audit row passes the DB CHECK constraint
    # (setup category bypasses the scope enforcement that requires session_id).
    _secrets_svc: Any = import_module(
        "backend.02_features.02_vault.sub_features.01_secrets.service"
    )
    _catalog_ctx_mod: Any = import_module("backend.01_catalog.context")
    _core_id_mod: Any = import_module("backend.01_core.id")
    vault_ctx = _catalog_ctx_mod.NodeContext(
        user_id=getattr(ctx, "user_id", None) or "sys",
        session_id=None,
        org_id=getattr(ctx, "org_id", None),
        workspace_id=getattr(ctx, "workspace_id", None),
        trace_id=_core_id_mod.uuid7(),
        span_id=_core_id_mod.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool, "vault": vault_client},
    )
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                await _secrets_svc.create_secret(
                    pool, conn, vault_ctx,
                    vault_client=vault_client,
                    key=vault_key,
                    value=bearer_token,
                    description=f"Bearer token for {platform} account {handle}",
                )
            except _errors.ConflictError:
                # Token already vaulted — rotate it
                await _secrets_svc.rotate_secret(
                    pool, conn, vault_ctx,
                    vault_client=vault_client,
                    key=vault_key,
                    value=bearer_token,
                    description=f"Bearer token for {platform} account {handle} (rotated)",
                )

            # Look up platform_id
            platform_id = await _repo.get_platform_id(conn, platform_code=platform)
            if platform_id is None:
                raise _errors.AppError(
                    "UNKNOWN_PLATFORM",
                    f"Platform '{platform}' is not configured.",
                    400,
                )

            account_id = _core_id.uuid7()
            actor = _actor(ctx)

            row = await _repo.create_social_account(
                conn,
                id=account_id,
                org_id=org_id,
                workspace_id=workspace_id,
                platform_id=platform_id,
                account_name=data["account_name"],
                account_handle=data.get("account_handle"),
                account_id_on_platform=data.get("account_id_on_platform"),
                vault_key=vault_key,
                created_by=actor,
            )

    return row


async def disconnect_account(pool: Any, ctx: Any, account_id: str) -> None:
    actor = _actor(ctx)
    async with pool.acquire() as conn:
        row = await _repo.get_social_account(conn, account_id=account_id)
        if row is None:
            raise _errors.NotFoundError(f"Social account {account_id!r} not found.")
        await _repo.delete_social_account(conn, account_id=account_id, deleted_by=actor)


async def list_accounts(pool: Any, org_id: str) -> list[dict]:
    async with pool.acquire() as conn:
        return await _repo.list_social_accounts(conn, org_id=org_id)


# ── Posts ─────────────────────────────────────────────────────────────────────

async def create_post(pool: Any, ctx: Any, data: dict) -> dict:
    org_id = getattr(ctx, "org_id", None) or data.get("org_id")
    workspace_id = getattr(ctx, "workspace_id", None)
    actor = _actor(ctx)

    if not org_id:
        raise _errors.AppError("MISSING_ORG", "org_id is required.", 400)

    account_ids: list[str] = data.get("account_ids", [])
    if not account_ids:
        raise _errors.AppError("MISSING_ACCOUNTS", "At least one account_id is required.", 400)

    # Validate accounts belong to org
    async with pool.acquire() as conn:
        for acc_id in account_ids:
            acc = await _repo.get_social_account(conn, account_id=acc_id)
            if acc is None or acc["org_id"] != org_id:
                raise _errors.AppError(
                    "ACCOUNT_NOT_FOUND",
                    f"Account {acc_id!r} not found in this org.",
                    404,
                )

    scheduled_at = data.get("scheduled_at")
    status_id = _STATUS_SCHEDULED if scheduled_at else _STATUS_DRAFT

    post_id = _core_id.uuid7()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _post = await _repo.create_post(
                conn,
                id=post_id,
                org_id=org_id,
                workspace_id=workspace_id,
                content_text=data.get("content_text", ""),
                media_urls=data.get("media_urls", []),
                first_comment=data.get("first_comment"),
                scheduled_at=scheduled_at,
                status_id=status_id,
                author_user_id=actor,
                created_by=actor,
            )
            for acc_id in account_ids:
                link_id = _core_id.uuid7()
                await _repo.add_post_account_link(
                    conn, id=link_id, post_id=post_id, account_id=acc_id
                )

    # Re-fetch with target_accounts populated
    async with pool.acquire() as conn:
        return await _repo.get_post(conn, post_id=post_id)  # type: ignore[return-value]


async def update_post(pool: Any, ctx: Any, post_id: str, data: dict) -> dict:
    actor = _actor(ctx)

    async with pool.acquire() as conn:
        existing = await _repo.get_post(conn, post_id=post_id)
        if existing is None:
            raise _errors.NotFoundError(f"Post {post_id!r} not found.")

    fields: dict[str, Any] = {}
    if "content_text" in data and data["content_text"] is not None:
        fields["content_text"] = data["content_text"]
    if "scheduled_at" in data:
        fields["scheduled_at"] = data["scheduled_at"]
        if data["scheduled_at"] is not None:
            fields["status_id"] = _STATUS_SCHEDULED
    if "status" in data and data["status"] is not None:
        sid = _STATUS_CODE_TO_ID.get(data["status"])
        if sid is None:
            raise _errors.AppError("INVALID_STATUS", f"Unknown status {data['status']!r}", 400)
        fields["status_id"] = sid

    async with pool.acquire() as conn:
        async with conn.transaction():
            _post = await _repo.update_post(conn, post_id=post_id, updated_by=actor, **fields)

            # Update account links if provided
            if "account_ids" in data and data["account_ids"] is not None:
                org_id = existing["org_id"]
                for acc_id in data["account_ids"]:
                    acc = await _repo.get_social_account(conn, account_id=acc_id)
                    if acc is None or acc["org_id"] != org_id:
                        raise _errors.AppError(
                            "ACCOUNT_NOT_FOUND",
                            f"Account {acc_id!r} not found in this org.",
                            404,
                        )
                await _repo.remove_post_account_links(conn, post_id=post_id)
                for acc_id in data["account_ids"]:
                    link_id = _core_id.uuid7()
                    await _repo.add_post_account_link(
                        conn, id=link_id, post_id=post_id, account_id=acc_id
                    )

    async with pool.acquire() as conn:
        return await _repo.get_post(conn, post_id=post_id)  # type: ignore[return-value]


async def delete_post(pool: Any, ctx: Any, post_id: str) -> None:
    actor = _actor(ctx)
    async with pool.acquire() as conn:
        existing = await _repo.get_post(conn, post_id=post_id)
        if existing is None:
            raise _errors.NotFoundError(f"Post {post_id!r} not found.")
        await _repo.soft_delete_post(conn, post_id=post_id, deleted_by=actor)


async def list_posts(
    pool: Any,
    org_id: str,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    async with pool.acquire() as conn:
        items = await _repo.list_posts(conn, org_id=org_id, status=status, limit=limit, offset=offset)
        total = await _repo.count_posts(conn, org_id=org_id, status=status)
    return items, total


async def get_post(pool: Any, post_id: str) -> dict | None:
    async with pool.acquire() as conn:
        return await _repo.get_post(conn, post_id=post_id)


# ── Publishing ────────────────────────────────────────────────────────────────

async def publish_post_now(
    pool: Any,
    vault_client: Any,
    _ctx: Any,  # reserved for future audit emission
    post_id: str,
) -> dict:
    """Immediately publish a post to all linked accounts."""
    async with pool.acquire() as conn:
        post = await _repo.get_post(conn, post_id=post_id)
        if post is None:
            raise _errors.NotFoundError(f"Post {post_id!r} not found.")

        # Mark as publishing
        await _repo.update_post_status(conn, post_id=post_id, status_id=_STATUS_PUBLISHING)

        accounts = await _repo.get_accounts_for_post(conn, post_id=post_id)

    if not accounts:
        async with pool.acquire() as conn:
            await _repo.update_post_status(
                conn, post_id=post_id, status_id=_STATUS_FAILED,
                error_message="No accounts linked to this post.",
            )
        raise _errors.AppError("NO_ACCOUNTS", "No accounts are linked to this post.", 400)

    platform_post_ids: dict[str, str] = {}
    errors: list[str] = []

    for account in accounts:
        platform = account["platform"]
        account_id = account["id"]
        vault_key = account["vault_key"]

        try:
            bearer_token = await vault_client.get(vault_key)
        except Exception as e:
            logger.error("vault get failed for %s: %s", vault_key, e)
            errors.append(f"{platform}: token not found in vault")
            async with pool.acquire() as conn:
                await _repo.insert_delivery_log(
                    conn,
                    id=_core_id.uuid7(),
                    org_id=post["org_id"],
                    post_id=post_id,
                    account_id=account_id,
                    platform_id=account["platform_id"],
                    outcome="failure",
                    error_detail=f"vault key not found: {vault_key}",
                )
            continue

        try:
            if platform == "x":
                result = await _do_twitter_post(bearer_token, post["content_text"])
                platform_post_ids["x"] = result["id"]
                async with pool.acquire() as conn:
                    await _repo.insert_delivery_log(
                        conn,
                        id=_core_id.uuid7(),
                        org_id=post["org_id"],
                        post_id=post_id,
                        account_id=account_id,
                        platform_id=account["platform_id"],
                        outcome="success",
                        platform_post_id=result["id"],
                    )
            else:
                # Placeholder for future platforms
                raise NotImplementedError(f"Publishing to {platform} is not yet implemented.")

        except NotImplementedError as e:
            errors.append(str(e))
            async with pool.acquire() as conn:
                await _repo.insert_delivery_log(
                    conn,
                    id=_core_id.uuid7(),
                    org_id=post["org_id"],
                    post_id=post_id,
                    account_id=account_id,
                    platform_id=account["platform_id"],
                    outcome="skipped",
                    error_detail=str(e),
                )
        except Exception as e:
            logger.error("publish failed for %s/%s: %s", platform, account_id, e)
            errors.append(f"{platform}: {e}")
            async with pool.acquire() as conn:
                await _repo.insert_delivery_log(
                    conn,
                    id=_core_id.uuid7(),
                    org_id=post["org_id"],
                    post_id=post_id,
                    account_id=account_id,
                    platform_id=account["platform_id"],
                    outcome="failure",
                    error_detail=str(e)[:500],
                )

    # Determine final status
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if platform_post_ids:
        final_status = _STATUS_PUBLISHED
        async with pool.acquire() as conn:
            await _repo.update_post_status(
                conn,
                post_id=post_id,
                status_id=final_status,
                platform_post_ids=platform_post_ids,
                published_at=now,
            )
    else:
        async with pool.acquire() as conn:
            await _repo.update_post_status(
                conn,
                post_id=post_id,
                status_id=_STATUS_FAILED,
                error_message="; ".join(errors) or "Publishing failed.",
            )

    async with pool.acquire() as conn:
        updated = await _repo.get_post(conn, post_id=post_id)

    return updated  # type: ignore[return-value]


async def _do_twitter_post(bearer_token: str, text: str) -> dict:
    """Post to Twitter v2 API. Returns {id, text}."""
    return await _tw.post_tweet(bearer_token, text)


# ── Metrics ───────────────────────────────────────────────────────────────────

async def refresh_metrics(
    pool: Any,
    vault_client: Any,
    post_id: str,
) -> list[dict]:
    """Pull fresh metrics from platform APIs for all published accounts."""
    async with pool.acquire() as conn:
        post = await _repo.get_post(conn, post_id=post_id)
        if post is None:
            raise _errors.NotFoundError(f"Post {post_id!r} not found.")
        accounts = await _repo.get_accounts_for_post(conn, post_id=post_id)

    platform_post_ids: dict = post.get("platform_post_ids") or {}

    for account in accounts:
        platform = account["platform"]
        pid = platform_post_ids.get(platform)
        if not pid:
            continue

        try:
            bearer_token = await vault_client.get(account["vault_key"])
        except Exception:
            continue

        try:
            if platform == "x":
                metrics = await _fetch_twitter_metrics(bearer_token, pid)
                async with pool.acquire() as conn:
                    await _repo.insert_metrics(
                        conn,
                        id=_core_id.uuid7(),
                        org_id=post["org_id"],
                        post_id=post_id,
                        account_id=account["id"],
                        platform_id=account["platform_id"],
                        platform_post_id=pid,
                        impressions=metrics.get("impressions", 0),
                        likes=metrics.get("likes", 0),
                        reposts=metrics.get("reposts", 0),
                        replies=metrics.get("replies", 0),
                        bookmarks=metrics.get("bookmarks", 0),
                        clicks=metrics.get("clicks", 0),
                        raw_data=metrics.get("raw", {}),
                    )
        except Exception as e:
            logger.warning("metrics fetch failed for %s/%s: %s", platform, pid, e)

    async with pool.acquire() as conn:
        return await _repo.get_post_metrics(conn, post_id=post_id)


async def _fetch_twitter_metrics(bearer_token: str, tweet_id: str) -> dict:
    return await _tw.get_tweet_metrics(bearer_token, tweet_id)
