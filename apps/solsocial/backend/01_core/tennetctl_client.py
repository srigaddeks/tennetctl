"""
TennetCTL proxy client.

Two auth modes, by call type:

  * Service-to-service (audit emit, notify send, vault write, flag evaluation,
    role/flag listings, application lookups) — uses solsocial's own service
    API key (`nk_...` bearer). This is the default for every method except
    `whoami`.

  * End-user identity resolution (`whoami`) — uses the incoming user's session
    token, because `/v1/auth/me` requires session auth (API keys don't set
    session_id).

The service API key is minted in tennetctl via `POST /v1/api-keys`, stored in
a file, and its path is set on `SOLSOCIAL_TENNETCTL_KEY_FILE`. The key must
carry whatever scopes solsocial needs (notify:send, audit:write, vault:write,
flags:read, iam:roles:read, iam:applications:read, etc.).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import httpx

_errors = import_module("apps.solsocial.backend.01_core.errors")


class TennetCTLClient:
    def __init__(
        self,
        base_url: str,
        service_api_key: str | None = None,
        application_id: str | None = None,
        application_code: str | None = None,
        org_id: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_api_key = service_api_key
        self._application_id = application_id
        self._application_code = application_code
        self._org_id = org_id
        self._http: httpx.AsyncClient | None = None

    @property
    def application_id(self) -> str | None:
        return self._application_id

    @property
    def org_id(self) -> str | None:
        return self._org_id

    def set_application(self, application_id: str, org_id: str) -> None:
        """Set resolved application_id + org_id after the boot lookup."""
        self._application_id = application_id
        self._org_id = org_id

    async def start(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(10.0, connect=3.0),
        )

    async def stop(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            raise RuntimeError("TennetCTLClient not started")
        return self._http

    @staticmethod
    def _bearer(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def _service_headers(self) -> dict:
        if not self._service_api_key:
            raise _errors.AppError(
                "SERVICE_KEY_MISSING",
                "SOLSOCIAL_TENNETCTL_KEY_FILE is not set — cannot make "
                "server-to-server calls to tennetctl.",
                500,
            )
        headers = self._bearer(self._service_api_key)
        # Stamp every outbound call with our application_id so tennetctl can
        # attribute audit events, feature flag evaluations, and vault reads
        # to this application. Middleware reads x-application-id when the
        # bearer is an API key (no session-bound application_id).
        if self._application_id:
            headers["x-application-id"] = self._application_id
        return headers

    @staticmethod
    def _raise_for_envelope(r: httpx.Response) -> dict:
        try:
            body = r.json()
        except Exception as exc:
            raise _errors.UpstreamError(
                f"tennetctl returned non-JSON: {r.status_code}"
            ) from exc
        if r.status_code >= 400 or not body.get("ok", False):
            err = body.get("error") or {}
            code = err.get("code", "UPSTREAM_ERROR")
            msg = err.get("message", f"tennetctl error {r.status_code}")
            if r.status_code == 401:
                raise _errors.UnauthorizedError(msg, code=code)
            if r.status_code == 403:
                raise _errors.ForbiddenError(msg, code=code)
            if r.status_code == 404:
                raise _errors.NotFoundError(msg, code=code)
            raise _errors.UpstreamError(msg, code=code, status_code=502)
        return body.get("data") or {}

    # ── end-user identity (session token required) ──────────────────────

    async def whoami(self, user_token: str) -> dict:
        """Resolve bearer session token → {user, session}. Session auth only."""
        r = await self._client().get("/v1/auth/me", headers=self._bearer(user_token))
        return self._raise_for_envelope(r)

    # ── service-to-service (use the API key) ────────────────────────────

    async def notify_send(self, payload: dict) -> dict:
        body = {**payload}
        body.setdefault("application_id", self._application_id)
        r = await self._client().post(
            "/v1/notify/send", headers=self._service_headers(), json=body,
        )
        return self._raise_for_envelope(r)

    async def vault_put(self, payload: dict) -> dict:
        r = await self._client().post(
            "/v1/vault", headers=self._service_headers(), json=payload,
        )
        return self._raise_for_envelope(r)

    async def vault_rotate(
        self, key: str, payload: dict,
        *, scope: str = "org", org_id: str | None = None, workspace_id: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"scope": scope}
        if org_id: params["org_id"] = org_id
        if workspace_id: params["workspace_id"] = workspace_id
        r = await self._client().post(
            f"/v1/vault/{key}/rotate",
            headers=self._service_headers(),
            params=params,
            json=payload,
        )
        return self._raise_for_envelope(r)

    async def vault_delete(self, key: str, *, scope: str, org_id: str) -> None:
        r = await self._client().delete(
            f"/v1/vault/{key}",
            headers=self._service_headers(),
            params={"scope": scope, "org_id": org_id},
        )
        if r.status_code not in (204, 200):
            self._raise_for_envelope(r)

    async def vault_reveal(
        self, key: str, *, scope: str = "org", org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> str:
        """Return the plaintext value for a vault key. Requires
        `vault:reveal:org` on the service API key. Raises NotFoundError if
        the key doesn't exist."""
        r = await self._client().post(
            f"/v1/vault/{key}/reveal",
            headers=self._service_headers(),
            json={"scope": scope, "org_id": org_id, "workspace_id": workspace_id},
        )
        data = self._raise_for_envelope(r)
        return data["value"]

    async def vault_list(
        self, *, scope: str = "org", org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict]:
        """List secret METADATA at a scope. Never returns plaintext."""
        params: dict[str, Any] = {"scope": scope, "limit": 500}
        if org_id: params["org_id"] = org_id
        if workspace_id: params["workspace_id"] = workspace_id
        r = await self._client().get(
            "/v1/vault", headers=self._service_headers(), params=params,
        )
        data = self._raise_for_envelope(r)
        return data if isinstance(data, list) else list(data.get("items") or [])

    async def feature_flag(self, key: str, context: dict | None = None) -> Any:
        ctx = {**(context or {})}
        ctx.setdefault("application_id", self._application_id)
        if self._org_id:
            ctx.setdefault("org_id", self._org_id)
        r = await self._client().post(
            "/v1/evaluate",
            headers=self._service_headers(),
            json={"flag_key": key, "environment": "production", "context": ctx},
        )
        data = self._raise_for_envelope(r)
        return data.get("value")

    async def emit_audit(
        self,
        *,
        event_key: str,
        outcome: str,
        metadata: dict | None = None,
        actor_user_id: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> None:
        """Best-effort audit emission — never raises into the business flow.

        `application_id` is auto-stamped from the client's configured app.
        End-user context (actor_user_id, org_id, workspace_id) must be passed
        explicitly because the API key identifies the service, not the user.
        """
        if not self._service_api_key:
            return
        try:
            await self._client().post(
                "/v1/audit-events",
                headers=self._service_headers(),
                json={
                    "event_key": event_key,
                    "outcome": outcome,
                    "metadata": metadata or {},
                    "application_id": self._application_id,
                    "actor_user_id": actor_user_id,
                    "org_id": org_id or self._org_id,
                    "workspace_id": workspace_id,
                },
            )
        except Exception:
            pass

    async def list_my_roles(self) -> list[dict]:
        """Roles scoped to this app (application_id auto-applied)."""
        if not self._application_id:
            raise _errors.AppError(
                "APPLICATION_UNRESOLVED",
                "application_id not yet resolved — call resolve_application() at boot.",
                500,
            )
        params: dict[str, Any] = {
            "application_id": self._application_id, "limit": 200,
        }
        if self._org_id:
            params["org_id"] = self._org_id
        r = await self._client().get(
            "/v1/roles", headers=self._service_headers(), params=params,
        )
        data = self._raise_for_envelope(r)
        return data if isinstance(data, list) else list(data.get("items") or [])

    async def list_my_flags(self) -> list[dict]:
        """Feature flags scoped to this app (application_id auto-applied)."""
        if not self._application_id:
            raise _errors.AppError(
                "APPLICATION_UNRESOLVED",
                "application_id not yet resolved — call resolve_application() at boot.",
                500,
            )
        params: dict[str, Any] = {
            "application_id": self._application_id, "limit": 500,
        }
        if self._org_id:
            params["org_id"] = self._org_id
        r = await self._client().get(
            "/v1/flags", headers=self._service_headers(), params=params,
        )
        data = self._raise_for_envelope(r)
        return data if isinstance(data, list) else list(data.get("items") or [])

    async def resolve_application(
        self, *, code: str, org_id: str,
    ) -> dict | None:
        """Look up the application by code + org and cache on the client.

        Call once at app startup. After this, every outbound call auto-stamps
        the resolved `application_id` (and `org_id` where applicable).
        """
        r = await self._client().get(
            "/v1/applications",
            headers=self._service_headers(),
            params={"org_id": org_id, "code": code, "limit": 1},
        )
        data = self._raise_for_envelope(r)
        items = data if isinstance(data, list) else (data.get("items") or [])
        app = items[0] if items else None
        if app:
            self.set_application(app["id"], org_id)
        return app
