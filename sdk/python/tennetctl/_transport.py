from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .errors import NetworkError, map_error

SESSION_COOKIE = "tnt_session"

RETRY_STATUSES = {502, 503, 504}
RETRY_BACKOFFS = (0.5, 1.0, 2.0)  # seconds; len = max retries after first attempt
MAX_ATTEMPTS = len(RETRY_BACKOFFS) + 1


class Transport:
    """Async HTTP transport: bearer auth, envelope parse, typed errors, retry."""

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        session_token: str | None = None,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._session_token = session_token
        cookies: dict[str, str] | None = None
        if session_token:
            cookies = {SESSION_COOKIE: session_token}
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            cookies=cookies,
        )
        self._owns_client = client is None

    @property
    def session_token(self) -> str | None:
        return self._session_token

    def set_session_token(self, token: str | None) -> None:
        self._session_token = token
        if token:
            self._client.cookies.set(SESSION_COOKIE, token)
        else:
            try:
                self._client.cookies.delete(SESSION_COOKIE)
            except KeyError:
                pass

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        hdrs: dict[str, str] = dict(headers or {})
        if self._api_key:
            hdrs["Authorization"] = f"Bearer {self._api_key}"

        last_exc: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = await self._client.request(
                    method.upper(),
                    path,
                    json=json,
                    params=params,
                    headers=hdrs,
                )
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
                last_exc = exc
                if attempt < MAX_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_BACKOFFS[attempt])
                    continue
                raise NetworkError(str(exc), code="NETWORK", status=None) from exc

            if response.status_code in RETRY_STATUSES and attempt < MAX_ATTEMPTS - 1:
                await asyncio.sleep(RETRY_BACKOFFS[attempt])
                continue

            return self._parse_response(response)

        # should not reach here — loop either returns or raises
        raise NetworkError("retry loop exhausted", code="NETWORK") from last_exc

    def _parse_response(self, response: httpx.Response) -> Any:
        # 204 No Content — no body to parse
        if response.status_code == 204:
            return None

        try:
            envelope = response.json()
        except ValueError:
            envelope = None

        if 200 <= response.status_code < 300:
            if isinstance(envelope, dict) and envelope.get("ok") is True:
                return envelope.get("data")
            # Non-envelope 2xx (e.g., raw JSON from upstream) — return body as-is
            return envelope

        # Error path
        if not isinstance(envelope, dict):
            envelope = {"ok": False, "error": {"code": "HTTP_ERROR", "message": response.text or f"HTTP {response.status_code}"}}
        raise map_error(response.status_code, envelope)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> Transport:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()
