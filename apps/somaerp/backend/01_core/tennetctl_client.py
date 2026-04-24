"""
TennetctlClient — somaerp's HTTP proxy to tennetctl.

Two auth modes (per apps/somaerp/03_docs/04_integration/00_tennetctl_proxy_pattern.md):

* user_scoped: forwards user session bearer (used by get_me / whoami)
* system_scoped: uses somaerp's own service API key (Bearer nk_...) for
  audit_emit, notify_send, vault_*, flags, etc.

Envelope handling: every tennetctl response is `{ok, data} | {ok, error}`.
`_unwrap` raises TennetctlProxyError on `ok=false` or non-JSON; otherwise
returns `data`. `audit_emit` is fail-open — network errors are swallowed
so audit failures never break the business flow (per spec).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import httpx

_errors = import_module("apps.somaerp.backend.01_core.errors")


class TennetctlClient:
    def __init__(
        self,
        base_url: str,
        *,
        service_api_key: str | None = None,
        application_id: str | None = None,
        org_id: str | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_api_key = service_api_key
        self._application_id = application_id
        self._org_id = org_id
        self._timeout = timeout_s
        self._http: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def application_id(self) -> str | None:
        return self._application_id

    @property
    def org_id(self) -> str | None:
        return self._org_id

    def set_application(self, application_id: str, org_id: str) -> None:
        self._application_id = application_id
        self._org_id = org_id

    async def start(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout, connect=3.0),
        )

    async def stop(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            raise RuntimeError("TennetctlClient not started — call await start() first")
        return self._http

    @staticmethod
    def _bearer(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def _service_headers(self) -> dict:
        if not self._service_api_key:
            raise _errors.SomaerpError(
                "TENNETCTL_SERVICE_API_KEY not set — cannot make service-to-service calls.",
                code="SERVICE_KEY_MISSING",
                status_code=500,
            )
        headers = self._bearer(self._service_api_key)
        if self._application_id:
            headers["x-application-id"] = self._application_id
        return headers

    @staticmethod
    def _unwrap(r: httpx.Response) -> Any:
        try:
            body = r.json()
        except Exception as exc:
            raise _errors.TennetctlProxyError(
                f"tennetctl returned non-JSON ({r.status_code})",
                code="UPSTREAM_NON_JSON",
            ) from exc
        if r.status_code >= 400 or not body.get("ok", False):
            err = body.get("error") or {}
            code = err.get("code") or "UPSTREAM_ERROR"
            msg = err.get("message") or f"tennetctl error {r.status_code}"
            if r.status_code == 401:
                raise _errors.AuthError(msg, code=code)
            if r.status_code == 404:
                raise _errors.NotFoundError(msg, code=code)
            raise _errors.TennetctlProxyError(msg, code=code, status_code=502)
        return body.get("data")

    # ── User-scoped (session bearer) ──────────────────────────────────────

    async def user_scoped(
        self,
        method: str,
        path: str,
        *,
        user_session_cookie: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        r = await self._client().request(
            method.upper(), path,
            headers=self._bearer(user_session_cookie),
            json=json, params=params,
        )
        return self._unwrap(r)

    async def get_me(self, user_session_cookie: str) -> dict:
        """Resolve session bearer → {user, session}. Wraps GET /v1/auth/me."""
        data = await self.user_scoped(
            "GET", "/v1/auth/me", user_session_cookie=user_session_cookie,
        )
        return data or {}

    # ── System-scoped (service API key) ───────────────────────────────────

    async def system_scoped(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        r = await self._client().request(
            method.upper(), path,
            headers=self._service_headers(),
            json=json, params=params,
        )
        return self._unwrap(r)

    async def audit_emit(
        self,
        event_key: str,
        scope: dict,
        payload: dict | None = None,
    ) -> None:
        """Best-effort audit emission. Network failures are swallowed
        (fail-open) — business flow must never break on audit issues."""
        if not self._service_api_key or self._http is None:
            return
        body = {
            "event_key": event_key,
            "outcome": (payload or {}).get("outcome", "success"),
            "metadata": (payload or {}).get("metadata") or {},
            "application_id": self._application_id,
            "actor_user_id": scope.get("user_id"),
            "org_id": scope.get("org_id") or self._org_id,
            "workspace_id": scope.get("workspace_id"),
        }
        try:
            await self._client().post(
                "/v1/audit-events",
                headers=self._service_headers(),
                json=body,
            )
        except Exception:
            # fail-open per spec
            pass

    async def ping(self) -> dict:
        """Hit tennetctl's low-level /health (no auth required)."""
        r = await self._client().get("/health")
        try:
            return r.json()
        except Exception:
            return {"ok": False, "status": r.status_code}
