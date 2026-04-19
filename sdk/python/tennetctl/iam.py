from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport


class _ReadResource:
    """Read-only resource wrapper for IAM list/get endpoints."""

    def __init__(self, transport: Transport, path: str) -> None:
        self._t = transport
        self._path = path  # e.g. "/v1/users"

    async def list(self, **filters: Any) -> list[dict]:
        params = {k: v for k, v in filters.items() if v is not None}
        data = await self._t.request("GET", self._path, params=params or None)
        return data if isinstance(data, list) else list(data or [])

    async def get(self, item_id: str) -> dict:
        return await self._t.request("GET", f"{self._path}/{item_id}")


class IAM:
    """Read-only helpers for IAM resources. Mutation goes through admin UI / direct endpoints."""

    def __init__(self, transport: Transport) -> None:
        self.users = _ReadResource(transport, "/v1/users")
        self.orgs = _ReadResource(transport, "/v1/orgs")
        self.workspaces = _ReadResource(transport, "/v1/workspaces")
        self.roles = _ReadResource(transport, "/v1/roles")
        self.groups = _ReadResource(transport, "/v1/groups")
