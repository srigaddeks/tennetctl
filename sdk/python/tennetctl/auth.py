from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport
    from .client import Tennetctl


class Sessions:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(self) -> list[dict]:
        data = await self._t.request("GET", "/v1/sessions")
        return data if isinstance(data, list) else list(data or [])

    async def get(self, session_id: str) -> dict:
        return await self._t.request("GET", f"/v1/sessions/{session_id}")

    async def update(self, session_id: str, **patch: Any) -> dict:
        return await self._t.request("PATCH", f"/v1/sessions/{session_id}", json=patch)

    async def revoke(self, session_id: str) -> None:
        await self._t.request("DELETE", f"/v1/sessions/{session_id}")


class ApiKeys:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(self) -> list[dict]:
        data = await self._t.request("GET", "/v1/api-keys")
        return data if isinstance(data, list) else list(data or [])

    async def create(self, *, name: str, scopes: list[str], expires_at: str | None = None) -> dict:
        body: dict[str, Any] = {"name": name, "scopes": scopes}
        if expires_at is not None:
            body["expires_at"] = expires_at
        return await self._t.request("POST", "/v1/api-keys", json=body)

    async def revoke(self, key_id: str) -> None:
        await self._t.request("DELETE", f"/v1/api-keys/{key_id}")

    async def rotate(self, key_id: str) -> dict:
        return await self._t.request("POST", f"/v1/api-keys/{key_id}/rotate")


class Auth:
    """Auth namespace — signin, signout, me, sessions, api_keys."""

    def __init__(self, transport: Transport, client: Tennetctl) -> None:
        self._t = transport
        self._c = client
        self.sessions = Sessions(transport)
        self.api_keys = ApiKeys(transport)

    async def signin(self, *, email: str, password: str) -> dict:
        data = await self._t.request(
            "POST",
            "/v1/auth/signin",
            json={"email": email, "password": password},
        )
        token = None
        if isinstance(data, dict):
            # Backend _build_response_payload returns token + user + session
            token = data.get("token") or data.get("session_token")
            if not token and isinstance(data.get("session"), dict):
                token = data["session"].get("token")
        if token:
            self._t.set_session_token(token)
        return data or {}

    async def signout(self) -> None:
        try:
            await self._t.request("POST", "/v1/auth/signout")
        finally:
            self._t.set_session_token(None)

    async def me(self) -> dict:
        return await self._t.request("GET", "/v1/auth/me")

    async def signup(self, *, email: str, password: str, **extra: Any) -> dict:
        body = {"email": email, "password": password, **extra}
        data = await self._t.request("POST", "/v1/auth/signup", json=body)
        token = None
        if isinstance(data, dict):
            token = data.get("token") or data.get("session_token")
            if not token and isinstance(data.get("session"), dict):
                token = data["session"].get("token")
        if token:
            self._t.set_session_token(token)
        return data or {}
