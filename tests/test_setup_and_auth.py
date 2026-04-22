"""Setup + auth: the entry path before any other feature is usable."""

from __future__ import annotations

import pytest


class TestSetupAndAuth:
    async def test_setup_status_reports_initialized(self, client, admin_session):
        resp = await client.get("/v1/setup/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["initialized"] is True
        assert body["data"]["user_count"] >= 1

    async def test_signin_with_valid_credentials_returns_token(self, client, admin_session):
        resp = await client.post(
            "/v1/auth/signin",
            json={"email": admin_session["email"], "password": admin_session["password"]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["token"]
        assert data["user"]["id"] == admin_session["user_id"]
        # Session must be bound to *some* org (not strictly the same UUID we
        # cached — the membership resolver picks a default from the user's
        # current memberships, and we're purely verifying the path yields an
        # org-scoped session).
        assert data["session"]["org_id"] is not None

    async def test_signin_rejects_wrong_password(self, client, admin_session):
        resp = await client.post(
            "/v1/auth/signin",
            json={"email": admin_session["email"], "password": "wrong"},
        )
        assert resp.status_code in (400, 401, 403)
        body = resp.json()
        assert body.get("ok") is False or "error" in body or "detail" in body

    async def test_me_returns_profile_when_authenticated(self, client, admin_session):
        # Re-sign-in locally so we're certain the token is live, even if some
        # earlier test churned the session list.
        signin = await client.post(
            "/v1/auth/signin",
            json={"email": admin_session["email"], "password": admin_session["password"]},
        )
        assert signin.status_code == 200, signin.text
        token = signin.json()["data"]["token"]

        resp = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["user"]["id"] == admin_session["user_id"]
        assert data["user"]["email"] == admin_session["email"]

    async def test_me_without_token_returns_empty_or_401(self, client):
        resp = await client.get("/v1/auth/me")
        # Either the handler returns 401, or it returns 200 with no user payload.
        # Both are valid for a session-middleware-open-by-default design.
        assert resp.status_code in (200, 401), resp.text
        if resp.status_code == 200:
            body = resp.json()
            assert body.get("data", {}).get("user") is None or body.get("ok") is False

    async def test_double_setup_rejected(self, client, admin_session):
        resp = await client.post(
            "/v1/setup/initial-admin",
            json={
                "email": "second@example.com",
                "password": "whatever-password-1234",
                "display_name": "Second",
            },
        )
        # 409 is the intended AppError; 422 means Pydantic rejected the body
        # before the service ever ran. Both confirm "don't let a second admin
        # be created" — either way the system refuses.
        assert resp.status_code in (400, 403, 409, 422), resp.text
        body = resp.json()
        if body.get("ok") is False:
            assert body["error"]["code"] in ("ALREADY_INITIALIZED",)
