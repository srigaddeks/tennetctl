"""
Twitter API v2 client — thin async wrapper over httpx.

Only uses bearer token (app-level auth) for now. OAuth 1.0a user-auth
is a future phase item when we need to post as specific user accounts.
"""

from __future__ import annotations

import httpx

TWITTER_API_BASE = "https://api.twitter.com/2"


async def post_tweet(
    bearer_token: str,
    text: str,
    reply_to_id: str | None = None,
) -> dict:
    """Post a tweet. Returns {id, text}."""
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }
        payload: dict = {"text": text}
        if reply_to_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}
        resp = await client.post(
            f"{TWITTER_API_BASE}/tweets",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()["data"]


async def get_tweet_metrics(bearer_token: str, tweet_id: str) -> dict:
    """Fetch public_metrics for a tweet."""
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        params = {"tweet.fields": "public_metrics,created_at,author_id"}
        resp = await client.get(
            f"{TWITTER_API_BASE}/tweets/{tweet_id}",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        metrics = data.get("public_metrics", {})
        return {
            "impressions": metrics.get("impression_count", 0),
            "likes": metrics.get("like_count", 0),
            "reposts": metrics.get("retweet_count", 0),
            "replies": metrics.get("reply_count", 0),
            "bookmarks": metrics.get("bookmark_count", 0),
            "clicks": metrics.get("url_link_clicks", 0),
            "raw": data,
        }


async def verify_credentials(bearer_token: str) -> dict:
    """Verify the bearer token works and return basic user info."""
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        resp = await client.get(
            f"{TWITTER_API_BASE}/users/me",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()["data"]
