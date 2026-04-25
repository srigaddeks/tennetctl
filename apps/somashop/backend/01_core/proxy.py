"""HTTP proxy clients for tennetctl + somaerp.

somashop has no own DB schema — every read/write hits tennetctl (auth)
or somaerp (products, subscriptions, orders). Both calls use the
caller's bearer token; system-scoped fallbacks use the service API key.
"""

from __future__ import annotations

from typing import Any

import httpx


class ProxyError(RuntimeError):
    def __init__(self, status: int, body: Any) -> None:
        self.status = status
        self.body = body
        super().__init__(f"proxy error {status}: {body}")


class HttpProxy:
    def __init__(self, base_url: str, *, service_api_key: str | None = None,
                 service_session_token: str | None = None,
                 timeout_s: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_api_key = service_api_key
        self._service_session_token = service_session_token
        self._timeout = timeout_s
        self._http: httpx.AsyncClient | None = None

    def set_service_session_token(self, token: str | None) -> None:
        self._service_session_token = token

    @property
    def base_url(self) -> str:
        return self._base_url

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
            raise RuntimeError("HttpProxy not started — call await start() first")
        return self._http

    async def request(
        self,
        method: str,
        path: str,
        *,
        bearer: str | None = None,
        use_service_session: bool = False,
        use_service_key: bool = False,
        json: Any = None,
        params: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        elif use_service_session and self._service_session_token:
            headers["Authorization"] = f"Bearer {self._service_session_token}"
        elif use_service_key and self._service_api_key:
            headers["Authorization"] = f"Bearer {self._service_api_key}"
        if extra_headers:
            headers.update(extra_headers)
        r = await self._client().request(method, path, json=json, params=params, headers=headers)
        try:
            payload = r.json()
        except Exception:
            payload = {"ok": False, "raw": r.text}
        if r.status_code >= 400:
            raise ProxyError(r.status_code, payload)
        return payload
