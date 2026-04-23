"""
Per-provider OAuth + publish adapters.

Three concrete adapters + one stub fallback. The adapter factory
`build_for_workspace(...)` is called per-request from the OAuth routes; this
module itself doesn't know about tennetctl vault — the resolver in
15_provider_apps/service.py fetches the client_id/client_secret per workspace
and hands them to the adapter constructor.

Protocol shapes (every adapter returns these):

    start_auth(redirect_uri, state)     → authorize URL (str)
    exchange_code(code, redirect_uri)   → {
        "tokens":       {access_token, refresh_token?, token_type, expires_at, scope?},
        "external_id":  provider's stable user id (for reconnect dedup),
        "handle":       display handle (e.g. @username),
        "display_name": human name,
        "avatar_url":   optional picture URL,
    }
    publish(tokens, channel, post)      → {external_post_id, external_url}
"""

from __future__ import annotations

import time
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx


SUPPORTED_PROVIDERS = ("linkedin", "twitter", "instagram")


class ProviderAdapter(Protocol):
    provider_code: str

    async def start_auth(self, *, redirect_uri: str, state: str) -> str: ...
    async def exchange_code(self, *, code: str, redirect_uri: str, state: str = "") -> dict: ...
    async def publish(self, *, tokens: dict, channel: dict, post: dict) -> dict: ...


# ── Stub ───────────────────────────────────────────────────────────────────

class StubAdapter:
    """Synthetic adapter. Used when provider creds aren't configured."""

    def __init__(self, provider_code: str) -> None:
        self.provider_code = provider_code

    async def start_auth(self, *, redirect_uri: str, state: str) -> str:
        return (
            f"{redirect_uri}?provider={self.provider_code}"
            f"&state={state}&code=stub_code_{state[:8]}"
        )

    async def exchange_code(self, *, code: str, redirect_uri: str, state: str = "") -> dict:
        suffix = code[-6:] if len(code) >= 6 else code
        return {
            "tokens": {
                "access_token": f"stub_{self.provider_code}_at_{suffix}",
                "refresh_token": f"stub_{self.provider_code}_rt_{suffix}",
                "token_type": "Bearer",
                "expires_at": int(time.time()) + 3600,
            },
            "external_id": f"stub_{self.provider_code}_{suffix}",
            "handle": f"@stub_{self.provider_code}_{suffix}",
            "display_name": f"Stub {self.provider_code.title()} User",
            "avatar_url": None,
        }

    async def publish(self, *, tokens: dict, channel: dict, post: dict) -> dict:
        post_id = post["id"]
        return {
            "external_post_id": f"stub_{self.provider_code}_post_{post_id[-8:]}",
            "external_url": f"https://{self.provider_code}.example/stub/{post_id[-8:]}",
        }


# ── LinkedIn ───────────────────────────────────────────────────────────────
#
# OIDC identity + Share on LinkedIn. Scopes:
#   openid profile email    (Sign In with LinkedIn using OpenID Connect)
#   w_member_social         (Share on LinkedIn)

_LINKEDIN_AUTHORIZE = "https://www.linkedin.com/oauth/v2/authorization"
_LINKEDIN_TOKEN     = "https://www.linkedin.com/oauth/v2/accessToken"
_LINKEDIN_USERINFO  = "https://api.linkedin.com/v2/userinfo"
_LINKEDIN_POSTS     = "https://api.linkedin.com/rest/posts"
_LINKEDIN_SCOPES    = "openid profile email w_member_social"
_LINKEDIN_API_VER   = "202409"


class LinkedInAdapter:
    provider_code = "linkedin"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def start_auth(self, *, redirect_uri: str, state: str) -> str:
        q = urlencode({
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": _LINKEDIN_SCOPES,
        })
        return f"{_LINKEDIN_AUTHORIZE}?{q}"

    async def exchange_code(self, *, code: str, redirect_uri: str, state: str = "") -> dict:
        _ = state
        async with httpx.AsyncClient(timeout=20) as http:
            tok_r = await http.post(
                _LINKEDIN_TOKEN,
                data={
                    "grant_type": "authorization_code",
                    "code": code, "redirect_uri": redirect_uri,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            tok_r.raise_for_status()
            tok = tok_r.json()
            prof_r = await http.get(
                _LINKEDIN_USERINFO,
                headers={"Authorization": f"Bearer {tok['access_token']}"},
            )
            prof_r.raise_for_status()
            prof = prof_r.json()

        external_id = prof.get("sub") or ""
        given = (prof.get("given_name") or "").strip()
        family = (prof.get("family_name") or "").strip()
        display = (f"{given} {family}".strip()) or prof.get("name") or prof.get("email") or "LinkedIn user"
        email = prof.get("email")
        handle = f"@{email.split('@')[0]}" if email else (prof.get("name") or external_id)

        return {
            "tokens": {
                "access_token": tok["access_token"],
                "refresh_token": tok.get("refresh_token"),
                "token_type": tok.get("token_type", "Bearer"),
                "expires_at": int(time.time()) + int(tok.get("expires_in", 3600)),
                "scope": tok.get("scope") or _LINKEDIN_SCOPES,
            },
            "external_id": external_id,
            "handle": handle,
            "display_name": display,
            "avatar_url": prof.get("picture"),
        }

    async def publish(self, *, tokens: dict, channel: dict, post: dict) -> dict:
        access_token = tokens.get("access_token")
        if not access_token:
            raise RuntimeError("LinkedIn channel has no access_token")
        author_urn = f"urn:li:person:{channel['external_id']}"
        body = post.get("body") or ""
        link = post.get("link")

        payload: dict[str, Any] = {
            "author": author_urn,
            "commentary": body,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if link:
            payload["content"] = {
                "article": {"source": link, "title": body.split("\n")[0][:100] or link},
            }

        async with httpx.AsyncClient(timeout=30) as http:
            r = await http.post(
                _LINKEDIN_POSTS, json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "LinkedIn-Version": _LINKEDIN_API_VER,
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Content-Type": "application/json",
                },
            )
        if r.status_code >= 400:
            raise RuntimeError(f"LinkedIn publish failed ({r.status_code}): {r.text[:500]}")

        urn = r.headers.get("x-restli-id") or r.headers.get("X-RestLi-Id") or ""
        external_url = f"https://www.linkedin.com/feed/update/{urn}/" if urn else None
        return {"external_post_id": urn, "external_url": external_url}


# ── Twitter / X ────────────────────────────────────────────────────────────
#
# OAuth 2.0 confidential client (uses Basic auth for token exchange, no PKCE
# required since we can keep client_secret server-side).
#
# Scopes: tweet.read tweet.write users.read offline.access
# Requires at minimum Basic tier ($200/mo) to be useful — free tier caps
# to 500 posts/month across the ENTIRE app. The adapter itself is tier-agnostic.

_TWITTER_AUTHORIZE = "https://twitter.com/i/oauth2/authorize"
_TWITTER_TOKEN     = "https://api.twitter.com/2/oauth2/token"
_TWITTER_USERINFO  = "https://api.twitter.com/2/users/me"
_TWITTER_TWEETS    = "https://api.twitter.com/2/tweets"
_TWITTER_SCOPES    = "tweet.read tweet.write users.read offline.access"


class TwitterAdapter:
    provider_code = "twitter"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def start_auth(self, *, redirect_uri: str, state: str) -> str:
        # `challenge` is required by Twitter's OAuth 2 even for confidential
        # clients. We pass a dummy "plain" challenge because we use Basic
        # auth at token time instead of verifying the code_verifier.
        # Twitter accepts `code_challenge_method=plain` with matching
        # `code_challenge` and `code_verifier`.
        q = urlencode({
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": _TWITTER_SCOPES,
            "code_challenge": state,           # echo state as the (plain) challenge
            "code_challenge_method": "plain",
        })
        return f"{_TWITTER_AUTHORIZE}?{q}"

    async def exchange_code(self, *, code: str, redirect_uri: str, state: str = "") -> dict:
        import base64
        basic = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()
        # code_verifier must equal the code_challenge we set in start_auth
        # (we used the state value as the plain challenge).
        async with httpx.AsyncClient(timeout=20) as http:
            tok_r = await http.post(
                _TWITTER_TOKEN,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": state,
                },
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            tok_r.raise_for_status()
            tok = tok_r.json()
            prof_r = await http.get(
                _TWITTER_USERINFO,
                headers={"Authorization": f"Bearer {tok['access_token']}"},
                params={"user.fields": "profile_image_url,username,name"},
            )
            prof_r.raise_for_status()
            prof = prof_r.json().get("data") or {}

        return {
            "tokens": {
                "access_token": tok["access_token"],
                "refresh_token": tok.get("refresh_token"),
                "token_type": tok.get("token_type", "bearer"),
                "expires_at": int(time.time()) + int(tok.get("expires_in", 7200)),
                "scope": tok.get("scope") or _TWITTER_SCOPES,
            },
            "external_id": prof.get("id") or "",
            "handle": f"@{prof.get('username')}" if prof.get("username") else (prof.get("id") or ""),
            "display_name": prof.get("name") or prof.get("username") or "Twitter user",
            "avatar_url": prof.get("profile_image_url"),
        }

    async def publish(self, *, tokens: dict, channel: dict, post: dict) -> dict:
        access_token = tokens.get("access_token")
        if not access_token:
            raise RuntimeError("Twitter channel has no access_token")
        body = (post.get("body") or "").strip()
        if post.get("link"):
            # Twitter unfurls URLs in the tweet body automatically.
            body = f"{body}\n{post['link']}" if body else post["link"]
        if not body:
            raise RuntimeError("Empty tweet body")
        async with httpx.AsyncClient(timeout=30) as http:
            r = await http.post(
                _TWITTER_TWEETS, json={"text": body},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
        if r.status_code >= 400:
            raise RuntimeError(f"Twitter publish failed ({r.status_code}): {r.text[:500]}")
        data = r.json().get("data") or {}
        tweet_id = data.get("id") or ""
        username = channel.get("handle", "").lstrip("@") or "i"
        external_url = f"https://twitter.com/{username}/status/{tweet_id}" if tweet_id else None
        return {"external_post_id": tweet_id, "external_url": external_url}


# ── Instagram (Graph API, Business accounts only) ──────────────────────────
#
# Instagram requires Facebook Login for Business + an Instagram Business
# account linked to a Facebook Page. Minimum scopes: instagram_basic,
# instagram_content_publish, pages_show_list, business_management.
#
# Publishing is a TWO-STEP flow:
#   1. POST /{ig-user-id}/media  {image_url | video_url, caption}  → creates a container
#   2. POST /{ig-user-id}/media_publish {creation_id}              → publishes
#
# Text-only posts are NOT supported by Instagram's API. Every published post
# must have at least one image or video URL. For solsocial v1 we require
# `post.media[0].url` on publish — the adapter raises if absent.

_IG_APP_VERSION     = "v21.0"
_IG_AUTHORIZE       = f"https://www.facebook.com/{_IG_APP_VERSION}/dialog/oauth"
_IG_TOKEN           = f"https://graph.facebook.com/{_IG_APP_VERSION}/oauth/access_token"
_IG_ME_ACCOUNTS     = f"https://graph.facebook.com/{_IG_APP_VERSION}/me/accounts"
_IG_SCOPES          = "instagram_basic,instagram_content_publish,pages_show_list,business_management"


class InstagramAdapter:
    provider_code = "instagram"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def start_auth(self, *, redirect_uri: str, state: str) -> str:
        q = urlencode({
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": _IG_SCOPES,
            "response_type": "code",
        })
        return f"{_IG_AUTHORIZE}?{q}"

    async def exchange_code(self, *, code: str, redirect_uri: str, state: str = "") -> dict:
        _ = state
        async with httpx.AsyncClient(timeout=20) as http:
            tok_r = await http.get(
                _IG_TOKEN,
                params={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            tok_r.raise_for_status()
            tok = tok_r.json()
            access_token = tok["access_token"]

            # List the user's Pages; each page may have a linked IG Business account.
            pages_r = await http.get(
                _IG_ME_ACCOUNTS,
                params={
                    "access_token": access_token,
                    "fields": "id,name,access_token,instagram_business_account{id,username,name,profile_picture_url}",
                },
            )
            pages_r.raise_for_status()
            pages = pages_r.json().get("data") or []

        # Pick the first page with a linked IG business account. A future
        # iteration can let the user pick if multiple are present.
        target = next(
            (p for p in pages if p.get("instagram_business_account")), None,
        )
        if target is None:
            raise RuntimeError(
                "No Instagram Business account found. Convert your IG account "
                "to Business or Creator, link it to a Facebook Page, and retry."
            )
        ig_info = target["instagram_business_account"]
        page_token = target["access_token"]

        return {
            "tokens": {
                "access_token": page_token,          # page token used for publishing
                "user_access_token": access_token,   # kept for refresh / diagnostic
                "ig_user_id": ig_info["id"],
                "page_id": target["id"],
                "token_type": tok.get("token_type", "bearer"),
                "expires_at": int(time.time()) + int(tok.get("expires_in", 60 * 60 * 24 * 60)),
                "scope": _IG_SCOPES,
            },
            "external_id": ig_info["id"],
            "handle": f"@{ig_info.get('username')}" if ig_info.get("username") else ig_info["id"],
            "display_name": ig_info.get("name") or ig_info.get("username") or "Instagram account",
            "avatar_url": ig_info.get("profile_picture_url"),
        }

    async def publish(self, *, tokens: dict, channel: dict, post: dict) -> dict:
        access_token = tokens.get("access_token")
        ig_user_id   = tokens.get("ig_user_id")
        if not access_token or not ig_user_id:
            raise RuntimeError("Instagram channel missing page access_token / ig_user_id")

        media = post.get("media") or []
        image_url = next(
            (m.get("url") for m in media if m.get("type") == "image"), None,
        )
        video_url = next(
            (m.get("url") for m in media if m.get("type") == "video"), None,
        )
        if not image_url and not video_url:
            raise RuntimeError(
                "Instagram requires at least one image or video URL. "
                "Attach media to the post before publishing."
            )

        caption = (post.get("body") or "").strip()

        async with httpx.AsyncClient(timeout=60) as http:
            # Step 1: create the media container.
            container_params: dict[str, Any] = {
                "access_token": access_token,
                "caption": caption,
            }
            if image_url:
                container_params["image_url"] = image_url
            else:
                container_params["media_type"] = "VIDEO"
                container_params["video_url"] = video_url

            c_r = await http.post(
                f"https://graph.facebook.com/{_IG_APP_VERSION}/{ig_user_id}/media",
                data=container_params,
            )
            if c_r.status_code >= 400:
                raise RuntimeError(f"Instagram container failed ({c_r.status_code}): {c_r.text[:500]}")
            container_id = c_r.json().get("id")
            if not container_id:
                raise RuntimeError(f"Instagram container had no id: {c_r.text[:300]}")

            # Step 2: publish the container.
            p_r = await http.post(
                f"https://graph.facebook.com/{_IG_APP_VERSION}/{ig_user_id}/media_publish",
                data={"creation_id": container_id, "access_token": access_token},
            )
            if p_r.status_code >= 400:
                raise RuntimeError(f"Instagram publish failed ({p_r.status_code}): {p_r.text[:500]}")
            published = p_r.json()

        media_id = published.get("id") or ""
        handle = channel.get("handle", "").lstrip("@") or ""
        external_url = f"https://www.instagram.com/{handle}/" if handle else None
        return {"external_post_id": media_id, "external_url": external_url}


# ── Publisher (resolver-based) ─────────────────────────────────────────────

class Publisher:
    """Resolves per-workspace adapters + fetches tokens from tennetctl vault
    at publish time (channel row carries the vault_key; never the plaintext)."""

    def __init__(self, adapters_resolver: Any) -> None:
        self._resolve = adapters_resolver

    async def publish(self, *, tennetctl: Any, token: str, channel: dict, post: dict) -> dict:
        provider = channel["provider_code"]
        adapter = await self._resolve(
            tennetctl,
            workspace_id=channel["workspace_id"],
            org_id=channel["org_id"],
            provider_code=provider,
        )
        tokens: dict = {}
        vault_key = channel.get("vault_key")
        # Any live adapter (Linked/Twitter/Instagram) needs real tokens.
        if vault_key and isinstance(adapter, (LinkedInAdapter, TwitterAdapter, InstagramAdapter)):
            import json as _json
            plaintext = await tennetctl.vault_reveal(
                vault_key, scope="org", org_id=channel["org_id"],
            )
            try:
                tokens = _json.loads(plaintext)
            except _json.JSONDecodeError:
                tokens = {}
        return await adapter.publish(tokens=tokens, channel=channel, post=post)
