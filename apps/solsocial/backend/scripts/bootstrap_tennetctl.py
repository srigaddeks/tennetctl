"""
One-time bootstrap: register the `solsocial` SaaS application in tennetctl,
then create its roles and feature flags scoped to that application.

This replaces per-repo SQL seeds for cross-app data. It talks to tennetctl's
public API so it works whether tennetctl runs on the same machine or remote.

Idempotent — safe to re-run. Existing rows (matched by code) are left alone.

Authentication
--------------
Uses the solsocial service API key (bearer `nk_...`). The key path is read
from `SOLSOCIAL_TENNETCTL_KEY_FILE`. Pass `--session-token <token>` to use
a session token for the first run instead (only one-time; needed because
creating applications requires `iam:applications:write` which the API key
must hold, AND because API keys can't mint more API keys — so the first
API key itself must be minted via a session login).

Usage:
    export SOLSOCIAL_TENNETCTL_URL=http://localhost:51734
    export SOLSOCIAL_TENNETCTL_KEY_FILE=./secrets/tennetctl.key
    .venv/bin/python -m apps.solsocial.backend.scripts.bootstrap_tennetctl \
        --org-id <tennetctl-org-uuid>

The org-id identifies the tennetctl org that owns the `solsocial` application
row. Get it from `GET /v1/orgs` on tennetctl.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from importlib import import_module
from typing import Any

import httpx

_config = import_module("apps.solsocial.backend.01_core.config")

APP_CODE = "solsocial"
APP_LABEL = "SolSocial"
APP_DESCRIPTION = "Lightweight Buffer-alternative built on tennetctl."

ROLES: list[dict] = [
    {"code": "solsocial_viewer",    "label": "Viewer",
     "description": "Read-only access to channels, posts, queues, ideas."},
    {"code": "solsocial_author",    "label": "Author",
     "description": "Create + edit drafts; cannot publish directly."},
    {"code": "solsocial_publisher", "label": "Publisher",
     "description": "Full content lifecycle including publishing."},
    {"code": "solsocial_admin",     "label": "Admin",
     "description": "All permissions including channel connect/disconnect."},
]

FLAGS: list[dict] = [
    {"flag_key": "solsocial_publishing_composer",    "value_type": "boolean",
     "default_value": True,  "description": "Post composer UI."},
    {"flag_key": "solsocial_publishing_queue",       "value_type": "boolean",
     "default_value": True,  "description": "Recurring time-slot queue per channel."},
    {"flag_key": "solsocial_publishing_calendar",    "value_type": "boolean",
     "default_value": True,  "description": "Read-view calendar over scheduled posts."},
    {"flag_key": "solsocial_publishing_ideas",       "value_type": "boolean",
     "default_value": True,  "description": "Idea bucket feature."},
    {"flag_key": "solsocial_channels_linkedin",      "value_type": "boolean",
     "default_value": True,  "description": "LinkedIn publishing."},
    {"flag_key": "solsocial_channels_twitter",       "value_type": "boolean",
     "default_value": True,  "description": "Twitter / X publishing."},
    {"flag_key": "solsocial_channels_instagram",     "value_type": "boolean",
     "default_value": True,  "description": "Instagram publishing."},
    {"flag_key": "solsocial_engagement_inbox",       "value_type": "boolean",
     "default_value": False, "description": "v2 — unified inbox."},
    {"flag_key": "solsocial_analytics_performance",  "value_type": "boolean",
     "default_value": False, "description": "v2 — performance analytics."},
    {"flag_key": "solsocial_start_page",             "value_type": "boolean",
     "default_value": False, "description": "v2 — public link-in-bio start page."},
]


async def _ok_envelope(r: httpx.Response) -> dict:
    body = r.json()
    if not body.get("ok"):
        err = body.get("error") or {}
        raise RuntimeError(
            f"tennetctl {r.status_code}: {err.get('code','?')} {err.get('message','?')}"
        )
    return body.get("data") or {}


def _unwrap_items(data: Any) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("items") or data.get("applications") or []
    return []


async def _find_application(client: httpx.AsyncClient, org_id: str) -> str | None:
    r = await client.get(
        "/v1/applications",
        params={"org_id": org_id, "code": APP_CODE, "limit": 10},
    )
    data = await _ok_envelope(r)
    for app in _unwrap_items(data):
        if isinstance(app, dict) and app.get("code") == APP_CODE:
            return app["id"]
    return None


async def _ensure_application(client: httpx.AsyncClient, org_id: str) -> str:
    app_id = await _find_application(client, org_id)
    if app_id:
        print(f"[bootstrap] application {APP_CODE!r} already exists: {app_id}")
        return app_id
    r = await client.post(
        "/v1/applications",
        json={
            "org_id": org_id,
            "code": APP_CODE,
            "label": APP_LABEL,
            "description": APP_DESCRIPTION,
        },
    )
    data = await _ok_envelope(r)
    app_id = data.get("id") or (data.get("application") or {}).get("id")
    if not app_id:
        raise RuntimeError(f"unexpected create response: {data}")
    print(f"[bootstrap] created application {APP_CODE!r}: {app_id}")
    return app_id


async def _ensure_roles(
    client: httpx.AsyncClient, org_id: str, application_id: str,
) -> None:
    r = await client.get(
        "/v1/roles",
        params={"org_id": org_id, "application_id": application_id, "limit": 200},
    )
    data = await _ok_envelope(r)
    existing_codes = {row.get("code") for row in _unwrap_items(data)}
    for spec in ROLES:
        if spec["code"] in existing_codes:
            print(f"[bootstrap] role {spec['code']!r} already exists — skipping")
            continue
        r = await client.post(
            "/v1/roles",
            json={
                "org_id": org_id,
                "application_id": application_id,
                "role_type": "custom",
                "code": spec["code"],
                "label": spec["label"],
                "description": spec["description"],
            },
        )
        data = await _ok_envelope(r)
        print(f"[bootstrap] created role {spec['code']!r}: {data.get('id')}")


async def _ensure_flags(
    client: httpx.AsyncClient, org_id: str, application_id: str,
) -> None:
    r = await client.get(
        "/v1/flags",
        params={"org_id": org_id, "application_id": application_id, "limit": 500},
    )
    data = await _ok_envelope(r)
    existing = {row.get("flag_key") for row in _unwrap_items(data)}
    for spec in FLAGS:
        if spec["flag_key"] in existing:
            print(f"[bootstrap] flag {spec['flag_key']!r} already exists — skipping")
            continue
        r = await client.post(
            "/v1/flags",
            json={
                "scope": "application",
                "org_id": org_id,
                "application_id": application_id,
                "flag_key": spec["flag_key"],
                "value_type": spec["value_type"],
                "default_value": spec["default_value"],
                "description": spec["description"],
            },
        )
        data = await _ok_envelope(r)
        print(f"[bootstrap] created flag {spec['flag_key']!r}: {data.get('id')}")


async def run(org_id: str, override_token: str | None) -> int:
    cfg = _config.load_config()
    token = override_token or cfg.tennetctl_service_api_key
    if not token:
        print(
            "error: no auth token — set SOLSOCIAL_TENNETCTL_KEY_FILE to a file "
            "containing the service API key (nk_...), or pass --session-token "
            "<token> for a one-time bootstrap using a session token.",
            file=sys.stderr,
        )
        return 2

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url=cfg.tennetctl_url, headers=headers, timeout=30,
    ) as client:
        app_id = await _ensure_application(client, org_id)
        await _ensure_roles(client, org_id, app_id)
        await _ensure_flags(client, org_id, app_id)

    print("\n[bootstrap] done.")
    print(f"  application_id = {app_id}")
    print(f"  roles          = {len(ROLES)} ensured")
    print(f"  feature_flags  = {len(FLAGS)} ensured")
    print("\nUse this application_id in SOLSOCIAL_APPLICATION_ID or fetch it via "
          f"GET /v1/applications?org_id={org_id}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register the solsocial app + its roles/flags in tennetctl.",
    )
    parser.add_argument(
        "--org-id", required=True,
        help="Tennetctl org UUID that owns the solsocial application.",
    )
    parser.add_argument(
        "--session-token", default=None,
        help="One-time session bearer token. When omitted, uses the service "
             "API key from SOLSOCIAL_TENNETCTL_KEY_FILE.",
    )
    args = parser.parse_args()
    return asyncio.run(run(args.org_id, args.session_token))


if __name__ == "__main__":
    sys.exit(main())
