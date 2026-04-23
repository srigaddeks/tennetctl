"""
OAuth flow routes.

  POST /v1/oauth/{provider}/start     → {authorize_url, state, mode}
  POST /v1/oauth/{provider}/callback  → exchange code, store tokens in
                                        tennetctl vault, create channel

Adapters are resolved per-workspace from tennetctl vault (15_provider_apps
service). Channel access tokens go into tennetctl vault at callback time
and are revealed on-demand at publish time — solsocial stores no credentials.
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

_channels_service = import_module("apps.solsocial.backend.02_features.10_channels.service")
_provider_apps = import_module("apps.solsocial.backend.02_features.15_provider_apps.service")
_providers = import_module("apps.solsocial.backend.02_features.60_oauth.providers")
_authz = import_module("apps.solsocial.backend.01_core.authz")
_response = import_module("apps.solsocial.backend.01_core.response")
_errors = import_module("apps.solsocial.backend.01_core.errors")
_id = import_module("apps.solsocial.backend.01_core.id")

router = APIRouter(tags=["oauth"])


class OAuthStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    redirect_uri: str = Field(min_length=1)


class OAuthCallback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    state: str
    redirect_uri: str


def _is_live(adapter: Any) -> bool:
    return isinstance(adapter, _providers.LinkedInAdapter)


@router.post("/v1/oauth/{provider}/start")
async def oauth_start(request: Request, provider: str, payload: OAuthStart) -> Any:
    if provider not in _providers.SUPPORTED_PROVIDERS:
        raise _errors.ValidationError(f"Unsupported provider: {provider}")
    tennetctl = request.app.state.tennetctl
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.connect")
    adapter = await _provider_apps.resolve_adapter(
        tennetctl,
        workspace_id=identity["workspace_id"], org_id=identity["org_id"],
        provider_code=provider,
    )
    state = _id.uuid7()
    authorize_url = await adapter.start_auth(
        redirect_uri=payload.redirect_uri, state=state,
    )
    return _response.success({
        "authorize_url": authorize_url, "state": state,
        "mode": "live" if _is_live(adapter) else "stub",
    })


@router.post("/v1/oauth/{provider}/callback")
async def oauth_callback(request: Request, provider: str, payload: OAuthCallback) -> Any:
    if provider not in _providers.SUPPORTED_PROVIDERS:
        raise _errors.ValidationError(f"Unsupported provider: {provider}")
    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl

    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.connect")
    adapter = await _provider_apps.resolve_adapter(
        tennetctl,
        workspace_id=identity["workspace_id"], org_id=identity["org_id"],
        provider_code=provider,
    )

    try:
        result = await adapter.exchange_code(
            code=payload.code, redirect_uri=payload.redirect_uri, state=payload.state,
        )
    except Exception as exc:
        raise _errors.UpstreamError(f"{provider} code exchange failed: {exc}") from exc

    external_id = result.get("external_id") or ""
    tokens = result["tokens"]

    # Reconnect-vs-new: if this workspace already has a channel for
    # (provider, external_id), rotate its tokens in place. Otherwise mint
    # a new channel. This lets the user connect multiple distinct accounts
    # of the same provider (each has a different external_id) while
    # re-OAuthing the same account refreshes its tokens.
    async with pool.acquire() as conn:
        existing = await _channels_service.find_by_external_id(
            conn,
            workspace_id=identity["workspace_id"],
            provider_code=provider,
            external_id=external_id,
        ) if external_id else None

    if existing:
        # Rotate tokens in the existing vault entry.
        await tennetctl.vault_rotate(
            existing["vault_key"], {"value": json.dumps(tokens)},
            scope="org", org_id=identity["org_id"],
        )
        channel = existing
        reused = True
    else:
        channel_id = _id.uuid7()
        vault_key = f"solsocial.channel.{channel_id}.tokens"
        await tennetctl.vault_put({
            "key": vault_key,
            "value": json.dumps(tokens),
            "description": f"solsocial {provider} channel tokens",
            "scope": "org", "org_id": identity["org_id"],
        })
        async with pool.acquire() as conn:
            channel = await _channels_service.connect_channel(
                conn,
                channel_id=channel_id,
                org_id=identity["org_id"],
                workspace_id=identity["workspace_id"],
                provider_code=provider,
                handle=result["handle"],
                display_name=result.get("display_name"),
                avatar_url=result.get("avatar_url"),
                external_id=external_id,
                vault_key=vault_key,
                created_by=identity["user_id"],
            )
        reused = False

    await tennetctl.emit_audit(
        event_key="solsocial.channels.reconnected" if reused else "solsocial.channels.connected",
        outcome="success",
        metadata={
            "channel_id": channel["id"], "provider": provider,
            "vault_key": channel["vault_key"],
            "external_id": external_id, "reused": reused,
        },
        actor_user_id=identity["user_id"], org_id=identity["org_id"],
        workspace_id=identity["workspace_id"],
    )
    return _response.success({
        "channel_id": channel["id"], "provider_code": provider, "reused": reused,
    })
